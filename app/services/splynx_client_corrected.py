"""
Cliente corregido para integración con Splynx API v2.0
Basado en la implementación funcional del proyecto ms-nxchile-mcp-server
"""

import time
from datetime import datetime
import hmac
import hashlib
import urllib
import requests
import urllib.parse
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SplynxClient:
    """Cliente para interactuar con la API de Splynx usando la implementación correcta"""
    
    def __init__(self):
        from config.settings import settings
        config = settings.get_splynx_config()
        
        self.base_url = config["base_url"]
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        self.timeout = config["timeout"]
        
        logger.info(f"SplynxClient inicializado con URL: {self.base_url}")

    def _generate_headers(self):
        """Generar headers de autenticación usando el método correcto de Splynx-EA"""
        t_now = datetime.now()
        nonce = round((time.mktime(t_now.timetuple()) + t_now.microsecond / 1000000.0) * 100)
        st = f"{nonce}{self.api_key}"
        signature = hmac.new(
            bytes(self.api_secret.encode('latin-1')), 
            bytes(st.encode('latin-1')),
            hashlib.sha256
        ).hexdigest()
        
        auth_data = {
            'key': self.api_key,
            'signature': signature.upper(),
            'nonce': nonce,
        }
        auth_string = urllib.parse.urlencode(auth_data)
        headers = {"Authorization": f"Splynx-EA ({auth_string})"}
        
        logger.debug(f"Headers generados para nonce: {nonce}")
        return headers

    def get(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Realizar petición GET a Splynx API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._generate_headers()
        
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"

        try:
            logger.info(f"GET request: {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("Error de autenticación (401)")
                return {"error": {"code": 401, "message": "Credenciales inválidas"}}
            elif response.status_code == 403:
                logger.error("Acceso prohibido (403)")
                return {"error": {"code": 403, "message": "Sin permisos para este recurso"}}
            elif response.status_code == 404:
                logger.error("Recurso no encontrado (404)")
                return {"error": {"code": 404, "message": "Endpoint no encontrado"}}
            else:
                logger.error(f"Error HTTP {response.status_code}: {response.text}")
                return {"error": {"code": response.status_code, "message": response.text}}
                
        except requests.exceptions.Timeout:
            logger.error("Timeout en petición a Splynx")
            return {"error": {"code": 408, "message": "Timeout de conexión"}}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión: {str(e)}")
            return {"error": {"code": 503, "message": f"Error de conexión: {str(e)}"}}

    def post(self, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Realizar petición POST a Splynx API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._generate_headers()
        
        try:
            logger.info(f"POST request: {url}")
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Error HTTP {response.status_code}: {response.text}")
                return {"error": {"code": response.status_code, "message": response.text}}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en POST: {str(e)}")
            return {"error": {"code": 503, "message": f"Error de conexión: {str(e)}"}}

    def search_customer_by_rut(self, rut: str) -> Optional[Dict[str, Any]]:
        """
        Buscar cliente en Splynx por RUT usando 2 pasos:
        1. Buscar por RUT para obtener ID
        2. Obtener datos completos por ID (incluyendo facturas)
        """
        try:
            logger.info(f"Paso 1: Buscando ID del cliente con RUT: {rut}")
            
            # PASO 1: Buscar por RUT para obtener solo el ID
            customer_id = self._find_customer_id_by_rut(rut)
            
            if not customer_id:
                logger.warning(f"Cliente con RUT {rut} no encontrado")
                return None
            
            logger.info(f"Paso 2: Obteniendo datos completos para Customer ID: {customer_id}")
            
            # PASO 2: Obtener datos completos del cliente por ID
            customer_data = self.get(f"/admin/customers/customer/{customer_id}")
            
            if customer_data and not customer_data.get("error"):
                logger.info(f"Cliente completo obtenido: {customer_data.get('name')}")
                return customer_data
            else:
                logger.error(f"Error obteniendo datos completos del cliente {customer_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error buscando cliente por RUT {rut}: {e}")
            return None
    
    def _find_customer_id_by_rut(self, rut: str) -> Optional[int]:
        """
        Buscar solo el ID del cliente por RUT usando diferentes métodos
        """
        try:
            # Método 1: Búsqueda por login exacto
            result = self.get("/admin/customers/customer", {
                "main_attributes[login]": rut,
                "limit": 1
            })
            
            if isinstance(result, list) and len(result) > 0:
                customer_id = result[0].get('id')
                logger.info(f"ID encontrado por login exacto: {customer_id}")
                return customer_id
            
            # Método 2: Búsqueda con LIKE en login
            result = self.get("/admin/customers/customer", {
                "main_attributes[login][0]": "LIKE",
                "main_attributes[login][1]": f"%{rut}%",
                "limit": 1
            })
            
            if isinstance(result, list) and len(result) > 0:
                customer_id = result[0].get('id')
                logger.info(f"ID encontrado con LIKE en login: {customer_id}")
                return customer_id
            
            # Método 3: Búsqueda en nombre
            result = self.get("/admin/customers/customer", {
                "main_attributes[name][0]": "LIKE", 
                "main_attributes[name][1]": f"%{rut}%",
                "limit": 1
            })
            
            if isinstance(result, list) and len(result) > 0:
                customer_id = result[0].get('id')
                logger.info(f"ID encontrado en nombre: {customer_id}")
                return customer_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando ID por RUT {rut}: {e}")
            return None

    def get_customer_invoices(self, customer_id: int) -> List[Dict[str, Any]]:
        """Obtener facturas de un cliente por su ID"""
        try:
            logger.info(f"Obteniendo facturas del cliente ID: {customer_id}")
            
            result = self.get("/admin/finance/invoices", {
                "main_attributes[customer_id]": customer_id,
                "limit": 50,
                "order[date_created]": "DESC"
            })
            
            if isinstance(result, list):
                # Filtrar facturas no pagadas si es posible
                unpaid_invoices = [
                    invoice for invoice in result 
                    if invoice.get('status') in ['not_paid', 'pending', 'new']
                ]
                logger.info(f"Encontradas {len(result)} facturas totales, {len(unpaid_invoices)} pendientes")
                return unpaid_invoices if unpaid_invoices else result
            else:
                error_msg = result.get("error", {}).get("message", "Error desconocido") if result else "Sin respuesta"
                logger.warning(f"No se pudieron obtener facturas para cliente {customer_id}: {error_msg}")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo facturas del cliente {customer_id}: {e}")
            return []

    def get_customer_by_rut(self, rut: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información completa del cliente y sus facturas por RUT
        Esta es la función principal que debe usar la API de BancoEstado
        """
        try:
            # 1. Buscar el cliente por RUT
            customer = self.search_customer_by_rut(rut)
            if not customer:
                logger.warning(f"Cliente con RUT {rut} no encontrado")
                return None
            
            # 2. Obtener las facturas del cliente
            customer_id = customer.get('id')
            if customer_id:
                invoices = self.get_customer_invoices(customer_id)
                customer['invoices'] = invoices
                logger.info(f"Cliente encontrado con {len(invoices)} facturas")
            else:
                customer['invoices'] = []
            
            return customer
            
        except Exception as e:
            logger.error(f"Error obteniendo cliente completo por RUT {rut}: {e}")
            return None

    def test_connection(self) -> Dict[str, Any]:
        """Probar la conexión con Splynx API"""
        try:
            logger.info("Probando conexión con Splynx API")
            result = self.get("/admin/customers/customer", {"limit": 1})
            
            # Si result es una lista (respuesta exitosa)
            if isinstance(result, list):
                return {
                    "success": True, 
                    "message": "Conexión exitosa con Splynx",
                    "customers_found": len(result)
                }
            # Si result es un dict con error
            elif isinstance(result, dict) and result.get("error"):
                error = result["error"]
                return {
                    "success": False, 
                    "message": f"Error {error.get('code')}: {error.get('message')}",
                    "details": result
                }
            # Si no hay respuesta
            else:
                return {"success": False, "message": "Sin respuesta del servidor"}
                
        except Exception as e:
            logger.error(f"Error probando conexión Splynx: {e}")
            return {"success": False, "message": f"Error de conexión: {str(e)}"}