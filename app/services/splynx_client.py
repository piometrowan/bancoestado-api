"""
Cliente para integración con Splynx API v2.0
Busca clientes por RUT y obtiene sus facturas
"""

import requests
import logging
import time
import hashlib
import hmac
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SplynxClient:
    """Cliente para interactuar con la API de Splynx"""
    
    def __init__(self):
        from config.settings import settings
        config = settings.get_splynx_config()
        
        self.base_url = config["base_url"]
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        self.rut_fields = config["rut_fields"]
        self.default_category = config["default_category"]
        self.default_tax = config["default_tax"]
        
        self.session = requests.Session()
        self.session.timeout = config["timeout"]
        
    def _generate_signature(self, nonce: int) -> str:
        """
        Generar firma HMAC-SHA256 para autenticación según documentación Splynx:
        $signature = strtoupper(hash_hmac('sha256', $nonce . $api_key, $api_secret));
        """
        # Concatenar nonce + api_key (como en PHP)
        message = f"{nonce}{self.api_key}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest().upper()
        logger.debug(f"Generated signature: nonce={nonce}, message='{message}', signature={signature}")
        return signature
    
    def _get_auth_headers(self, use_basic_auth=False) -> Dict[str, str]:
        """
        Generar headers de autenticación para Splynx
        """
        if use_basic_auth:
            # Intentar autenticación básica como alternativa (requiere Unsecure access habilitado)
            import base64
            credentials = f"{self.api_key}:{self.api_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            return {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        else:
            # Autenticación por firma según documentación Splynx (método 1 - líneas 41-42)
            # $nonce = round(microtime(true) * 100);
            # $signature = strtoupper(hash_hmac('sha256', $nonce . $api_key, $api_secret));
            nonce = int(round(time.time() * 100))
            signature = self._generate_signature(nonce)
            
            # Construir auth_data array como en PHP (líneas 44-48)
            auth_data = {
                'key': self.api_key,
                'signature': signature,
                'nonce': nonce
            }
            
            # http_build_query como en PHP (línea 49)
            auth_string = f"key={auth_data['key']}&signature={auth_data['signature']}&nonce={auth_data['nonce']}"
            
            logger.debug(f"Nonce: {nonce}, Signature: {signature}")
            logger.debug(f"Auth string: {auth_string}")
            
            return {
                "Authorization": f"Splynx-EA ({auth_string})",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, use_basic_auth=False) -> Dict[str, Any]:
        """Realizar petición HTTP a Splynx API con manejo de errores según documentación"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_auth_headers(use_basic_auth)
        
        try:
            logger.info(f"Splynx API {method} request to: {url}")
            logger.debug(f"Headers: {headers.get('Authorization', 'No auth')[:50]}...")
            if params:
                logger.debug(f"Params: {params}")
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            )
            
            logger.info(f"Splynx API response: {response.status_code}")
            
            if response.status_code in [200, 201, 202]:
                return response.json()
            elif response.status_code == 204:
                return {"success": True, "message": "No content"}
            elif response.status_code == 401:
                logger.error("Authentication failed (401) - Invalid API credentials")
                return {
                    "error": {
                        "code": 401,
                        "internal_code": "UNAUTHORIZED",
                        "message": "API key o secret inválidos. Verifica credenciales en Splynx."
                    }
                }
            elif response.status_code == 403:
                logger.error(f"Forbidden access (403): {response.text}")
                return {
                    "error": {
                        "code": 403,
                        "internal_code": "FORBIDDEN", 
                        "message": "No tienes permisos para acceder a este recurso"
                    }
                }
            elif response.status_code == 404:
                logger.warning(f"Resource not found (404): {url}")
                return {
                    "error": {
                        "code": 404,
                        "internal_code": "NOT_FOUND",
                        "message": "Recurso no encontrado"
                    }
                }
            elif response.status_code == 405:
                logger.error(f"Method not allowed (405): {method} {url}")
                return {
                    "error": {
                        "code": 405,
                        "internal_code": "METHOD_NOT_ALLOWED",
                        "message": "Método no permitido para este endpoint"
                    }
                }
            elif response.status_code == 500:
                logger.error(f"Internal server error (500): {response.text}")
                return {
                    "error": {
                        "code": 500,
                        "internal_code": "SERVER_ERROR",
                        "message": "Error interno del servidor Splynx"
                    }
                }
            else:
                # Intentar parsear error JSON de Splynx si está disponible
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        logger.error(f"Splynx API error: {error_data['error']}")
                        return error_data
                except:
                    pass
                    
                logger.error(f"Splynx API error {response.status_code}: {response.text}")
                return {
                    "error": {
                        "code": response.status_code,
                        "internal_code": "UNKNOWN_ERROR",
                        "message": f"Error HTTP {response.status_code}",
                        "details": response.text
                    }
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout en petición a Splynx: {url}")
            return {
                "error": {
                    "code": 408,
                    "internal_code": "REQUEST_TIMEOUT", 
                    "message": "Timeout de conexión con Splynx"
                }
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión a Splynx: {e}")
            return {
                "error": {
                    "code": 503,
                    "internal_code": "CONNECTION_ERROR",
                    "message": "Error de conexión con Splynx",
                    "details": str(e)
                }
            }
    
    def search_customer_by_rut(self, rut: str) -> Optional[Dict[str, Any]]:
        """
        Buscar cliente en Splynx por RUT usando el formato correcto según la documentación API
        """
        try:
            logger.info(f"Buscando cliente con RUT: {rut}")
            
            # Probar una búsqueda simple primero
            search_params = {
                "main_attributes[login]": rut,
                "limit": 1
            }
            result = self._make_request("GET", "/admin/customers/customer", params=search_params)
            
            # Si hay error de autenticación, fallar inmediatamente sin reintentos
            if result and result.get("error") and result["error"].get("code") == 401:
                logger.error("Error de autenticación - No se pueden realizar búsquedas")
                return None
            
            if result and not result.get("error") and isinstance(result, list) and len(result) > 0:
                customer = result[0]
                logger.info(f"Cliente encontrado por login: ID {customer.get('id')}")
                return customer
            
            # Solo continuar si no hay error de autenticación
            if not result or not result.get("error"):
                # Buscar por login con LIKE
                search_params = {
                    "main_attributes[login][0]": "LIKE",
                    "main_attributes[login][1]": rut,
                    "limit": 1
                }
                result = self._make_request("GET", "/admin/customers/customer", params=search_params)
                
                if result and not result.get("error") and isinstance(result, list) and len(result) > 0:
                    customer = result[0]
                    logger.info(f"Cliente encontrado por login con LIKE: ID {customer.get('id')}")
                    return customer
            
            logger.warning(f"Cliente con RUT {rut} no encontrado")
            return None
            
        except Exception as e:
            logger.error(f"Error buscando cliente por RUT {rut}: {e}")
            return None
    
    def get_customer_invoices(self, customer_id: int) -> List[Dict[str, Any]]:
        """Obtener facturas de un cliente por su ID usando el endpoint correcto según documentación"""
        try:
            logger.info(f"Obteniendo facturas del cliente ID: {customer_id}")
            
            # Según la documentación, usar parámetros de búsqueda estructurados
            search_params = {
                "main_attributes[customer_id]": customer_id,
                "limit": 100,  # Aumentar límite para obtener más facturas
                "order[date_created]": "DESC"  # Facturas más recientes primero
            }
            
            result = self._make_request("GET", "/admin/finance/invoices", params=search_params)
            
            if result and not result.get("error"):
                if isinstance(result, list):
                    # Filtrar solo facturas no pagadas o pendientes
                    unpaid_invoices = [
                        invoice for invoice in result 
                        if invoice.get('status') in ['not_paid', 'pending']
                    ]
                    logger.info(f"Encontradas {len(result)} facturas totales, {len(unpaid_invoices)} pendientes para cliente {customer_id}")
                    return unpaid_invoices if unpaid_invoices else result
                else:
                    logger.warning(f"Respuesta inesperada de facturas: {type(result)}")
                    return []
            else:
                logger.warning(f"No se pudieron obtener facturas para cliente {customer_id}: {result}")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo facturas del cliente {customer_id}: {e}")
            return []
    
    def get_customer_by_rut(self, rut: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información completa del cliente y sus facturas por RUT
        Esta es la función principal que se usa desde el servicio
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
            else:
                customer['invoices'] = []
            
            logger.info(f"Datos completos obtenidos para cliente {customer.get('name', 'Sin nombre')}")
            return customer
            
        except Exception as e:
            logger.error(f"Error obteniendo cliente completo por RUT {rut}: {e}")
            return None
    
    def register_payment(self, customer_id: int, amount: float, description: str, invoice_id: str = None) -> Dict[str, Any]:
        """
        Registrar pago en Splynx creando una transacción tipo debit (ingreso)
        """
        try:
            logger.info(f"Registrando pago en Splynx - Cliente: {customer_id}, Monto: {amount}")
            
            # Usar configuración centralizada para transacciones
            transaction_data = {
                "type": "debit",  # debit = ingreso (pago recibido)
                "customer_id": customer_id,
                "quantity": 1,
                "price": amount,
                "tax_percent": self.default_tax,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "category": self.default_category,
                "description": f"Pago BancoEstado: {description}",
                "source": "manual"
            }
            
            # Si hay ID de factura específica, agregarla
            if invoice_id and invoice_id.isdigit():
                transaction_data["payment_id"] = int(invoice_id)
            
            result = self._make_request("POST", "/admin/finance/transactions", data=transaction_data)
            
            if result and not result.get("error"):
                transaction_id = result.get("id")
                logger.info(f"Pago registrado exitosamente - Transaction ID: {transaction_id}")
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "message": "Pago registrado en Splynx"
                }
            else:
                logger.error(f"Error registrando pago en Splynx: {result}")
                return {
                    "success": False,
                    "message": "Error registrando pago en Splynx",
                    "details": result
                }
                
        except Exception as e:
            logger.error(f"Excepción registrando pago en Splynx: {e}")
            return {
                "success": False,
                "message": "Error interno registrando pago",
                "details": str(e)
            }
    
    def process_payment_by_rut(self, rut: str, factura_id: str, amount: float, description: str) -> Dict[str, Any]:
        """
        Procesar pago completo: buscar cliente por RUT y registrar pago
        """
        try:
            logger.info(f"Procesando pago completo - RUT: {rut}, Factura: {factura_id}, Monto: {amount}")
            
            # 1. Buscar cliente por RUT
            customer = self.search_customer_by_rut(rut)
            if not customer:
                return {
                    "success": False,
                    "message": "Cliente no encontrado",
                    "codigo_error": "3"
                }
            
            customer_id = customer.get('id')
            if not customer_id:
                return {
                    "success": False,
                    "message": "ID de cliente inválido",
                    "codigo_error": "3"
                }
            
            # 2. Validar que el cliente tenga facturas pendientes
            customer_with_invoices = self.get_customer_by_rut(rut)
            if not customer_with_invoices or not customer_with_invoices.get('invoices'):
                return {
                    "success": False,
                    "message": "Cliente no tiene facturas",
                    "codigo_error": "5"
                }
            
            # 3. Buscar factura específica si se proporciona
            target_invoice = None
            if factura_id and factura_id != "Sin facturas":
                for invoice in customer_with_invoices['invoices']:
                    if str(invoice.get('id')) == str(factura_id):
                        target_invoice = invoice
                        break
                
                if not target_invoice:
                    # Si no se encuentra la factura específica, usar la primera pendiente
                    target_invoice = customer_with_invoices['invoices'][0]
            else:
                # Usar la primera factura disponible
                target_invoice = customer_with_invoices['invoices'][0]
            
            # 4. Validar monto si hay factura específica
            invoice_amount = float(target_invoice.get('total', 0))
            if invoice_amount > 0 and abs(amount - invoice_amount) > 0.01:
                logger.warning(f"Monto no coincide - Esperado: {invoice_amount}, Recibido: {amount}")
                # Continuar con el monto recibido (BancoEstado puede enviar monto diferente)
            
            # 5. Registrar el pago en Splynx
            payment_result = self.register_payment(
                customer_id=customer_id,
                amount=amount,
                description=description,
                invoice_id=str(target_invoice.get('id', ''))
            )
            
            if payment_result['success']:
                return {
                    "success": True,
                    "customer_id": str(customer_id),
                    "transaction_id": payment_result.get('transaction_id'),
                    "invoice_id": str(target_invoice.get('id', '')),
                    "amount": amount,
                    "message": "Pago procesado exitosamente"
                }
            else:
                return {
                    "success": False,
                    "message": payment_result['message'],
                    "codigo_error": "500"
                }
                
        except Exception as e:
            logger.error(f"Error procesando pago completo: {e}")
            return {
                "success": False,
                "message": "Error interno procesando pago",
                "codigo_error": "500"
            }

    def test_connection(self) -> Dict[str, Any]:
        """Probar la conexión con Splynx API - Una sola request"""
        try:
            logger.info("Probando conexión con Splynx API")
            result = self._make_request("GET", "/admin/customers/customer", params={"limit": 1})
            
            if result and not result.get("error"):
                return {"success": True, "message": "Conexión exitosa con Splynx"}
            elif result and result.get("error") and result["error"].get("code") == 401:
                return {
                    "success": False, 
                    "message": "Error de autenticación: API key o secret inválidos",
                    "details": "Verifica credenciales en Splynx y permisos del API key"
                }
            else:
                return {"success": False, "message": "Error de conexión", "details": result}
                
        except Exception as e:
            logger.error(f"Error probando conexión Splynx: {e}")
            return {"success": False, "message": "Error de conexión", "details": str(e)}