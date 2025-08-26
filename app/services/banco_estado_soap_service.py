"""
Servicio para la API SOAP de BancoEstado
Compatible con el WSDL original del CRM
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from .splynx_client_corrected import SplynxClient
from .splynx_database import SplynxDatabase

logger = logging.getLogger(__name__)

class BancoEstadoSOAPService:
    """Servicio que implementa los métodos SOAP compatibles con el WSDL original"""
    
    def __init__(self):
        self.splynx_client = SplynxClient()
        self.splynx_db = SplynxDatabase()
    
    def consultar_cliente(self, rut_cliente: str) -> str:
        """
        Consultar cliente por RUT - Compatible con consultarClienteRequest
        Retorna string JSON igual que el CRM original
        
        Args:
            rut_cliente (str): RUT del cliente a consultar
            
        Returns:
            str: JSON string con los datos del cliente y su última factura
        """
        try:
            logger.info(f"Consultando cliente con RUT: {rut_cliente}")
            
            # Limpiar el RUT
            rut_limpio = rut_cliente.strip().replace(" ", "")
            
            # Buscar cliente en base de datos usando stored procedure (como ms-nxchile)
            customer_db = self.splynx_db.buscar_cliente_por_rut(rut_limpio)
            
            if customer_db:
                # Si encontramos en BD, mapear los campos correctos
                customer_id = customer_db.get('id_cliente')
                
                if customer_id:
                    # Normalizar los datos de BD para que coincidan con formato API
                    customer = {
                        'id': customer_id,
                        'name': customer_db.get('nombre_cliente', ''),
                        'login': customer_db.get('rut_cliente', rut_limpio),
                        'email': '',  # No viene en stored procedure
                        'status': customer_db.get('status', 'new'),
                        'phone': customer_db.get('phone', ''),
                        'street_1': customer_db.get('street_1', ''),
                        'city': '',  # No viene en stored procedure
                        'category': customer_db.get('category', 'person'),
                        'mrr_total': '0.0000'  # No viene en stored procedure
                    }
                    
                    # Agregar facturas desde la BD
                    invoices_db = self.splynx_db.obtener_facturas_cliente(customer_id)
                    customer['invoices'] = invoices_db
                    
                    logger.info(f"Cliente encontrado en BD: {customer['name']} (ID: {customer_id})")
                else:
                    logger.warning(f"Customer ID no encontrado en BD para RUT {rut_limpio}")
                    customer = None
            else:
                # Fallback al método original API si no hay en BD
                customer = self.splynx_client.get_customer_by_rut(rut_limpio)
            
            if not customer:
                # Respuesta cuando no se encuentra el cliente
                response = {
                    "success": False,
                    "codigo_error": "3",
                    "mensaje": "Cliente no encontrado",
                    "rut": rut_cliente,
                    "cliente": None,
                    "facturas": []
                }
                logger.warning(f"Cliente no encontrado: {rut_cliente}")
                return json.dumps(response, ensure_ascii=False)
            
            # Datos del cliente encontrado
            cliente_data = {
                "id": str(customer.get('id', '')),
                "nombre": customer.get('name', ''),
                "rut": customer.get('login', rut_cliente),
                "email": customer.get('email', ''),
                "estado": customer.get('status', ''),
                "direccion": customer.get('street_1', ''),
                "ciudad": customer.get('city', ''),
                "telefono": customer.get('phone', ''),
                "fecha_registro": customer.get('date_add', ''),
                "tipo_facturacion": customer.get('billing_type', ''),
                "balance": str(customer.get('mrr_total', '0.0000'))
            }
            
            # Procesar facturas
            invoices = customer.get('invoices', [])
            facturas_data = []
            ultima_factura_pendiente = None
            
            for invoice in invoices:
                factura = {
                    "id": str(invoice.get('id', '')),
                    "total": str(invoice.get('total', '0')),
                    "estado": invoice.get('status', ''),
                    "fecha_creacion": invoice.get('date_created', ''),
                    "fecha_vencimiento": invoice.get('date_to_pay', ''),
                    "periodo_desde": invoice.get('date_from', ''),
                    "periodo_hasta": invoice.get('date_to', '')
                }
                facturas_data.append(factura)
                
                # Buscar la última factura pendiente
                estado = invoice.get('status', '').lower()
                if estado in ['not_paid', 'pending', 'new', 'unpaid'] and not ultima_factura_pendiente:
                    ultima_factura_pendiente = factura
            
            # Respuesta exitosa compatible con el formato original
            response = {
                "success": True,
                "codigo_error": "0",
                "mensaje": "Cliente encontrado exitosamente",
                "rut": rut_cliente,
                "cliente": cliente_data,
                "facturas": facturas_data,
                "total_facturas": len(facturas_data),
                "ultima_factura_pendiente": ultima_factura_pendiente,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Cliente encontrado: {cliente_data['nombre']} (ID: {cliente_data['id']})")
            return json.dumps(response, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error consultando cliente {rut_cliente}: {str(e)}")
            
            # Respuesta de error
            error_response = {
                "success": False,
                "codigo_error": "500",
                "mensaje": f"Error interno del servidor: {str(e)}",
                "rut": rut_cliente,
                "cliente": None,
                "facturas": []
            }
            return json.dumps(error_response, ensure_ascii=False)
    
    def registrar_pago(self, rut_cliente: str, factura: str, monto: float, 
                      descripcion: str, pasarela: str, transaccion: str) -> str:
        """
        Registrar pago en Splynx - Compatible con registrarPagoRequest
        
        Args:
            rut_cliente (str): RUT del cliente
            factura (str): ID de la factura
            monto (float): Monto del pago
            descripcion (str): Descripción del pago
            pasarela (str): Pasarela de pago utilizada
            transaccion (str): ID de transacción
            
        Returns:
            str: JSON string con el resultado del registro
        """
        try:
            logger.info(f"Registrando pago - RUT: {rut_cliente}, Factura: {factura}, Monto: {monto}")
            
            # Limpiar el RUT
            rut_limpio = rut_cliente.strip().replace(" ", "")
            
            # 1. Buscar el cliente usando BD primero (como ms-nxchile)
            customer_db = self.splynx_db.buscar_cliente_por_rut(rut_limpio)
            if customer_db:
                customer = {'id': customer_db.get('id_cliente')}
            else:
                # Fallback a API si no está en BD
                customer = self.splynx_client.search_customer_by_rut(rut_limpio)
            if not customer:
                response = {
                    "success": False,
                    "codigo_error": "3",
                    "mensaje": "Cliente no encontrado",
                    "rut": rut_cliente,
                    "transaccion_id": None
                }
                logger.warning(f"Cliente no encontrado para pago: {rut_cliente}")
                return json.dumps(response, ensure_ascii=False)
            
            customer_id = customer.get('id')
            
            # 2. Preparar datos del pago según documentación Splynx
            payment_data = {
                "customer_id": customer_id,
                "invoice_id": int(factura) if factura and factura.isdigit() else None,
                "payment_type": "24",  # Tipo de pago Banco Estado Mitplay como especificaste
                "receipt_number": transaccion,  # Número de transacción como receipt
                "date": datetime.now().strftime("%Y-%m-%d"),
                "amount": str(monto),
                "comment": f"Pago BancoEstado - {descripcion} - Pasarela: {pasarela} - RUT: {rut_cliente}",
                "field_1": rut_cliente,  # RUT en field_1
                "field_2": factura,      # ID factura en field_2
                "field_3": pasarela,     # Pasarela en field_3
                "field_4": transaccion,  # Transacción en field_4
                "field_5": "BancoEstado", # Identificador del sistema
                "note": f"Pago procesado automáticamente via API BancoEstado",
                "memo": f"Transacción: {transaccion} - Descripción: {descripcion}"
            }
            
            # 3. Registrar el pago en Splynx
            result = self.splynx_client.post("/admin/finance/payments", payment_data)
            
            if result and not result.get("error"):
                # Pago registrado exitosamente
                payment_id = result.get("id") if isinstance(result, dict) else None
                
                response = {
                    "success": True,
                    "codigo_error": "0",
                    "mensaje": "Pago registrado exitosamente",
                    "rut": rut_cliente,
                    "factura_id": factura,
                    "monto": monto,
                    "transaccion_id": transaccion,
                    "payment_id": str(payment_id) if payment_id else None,
                    "customer_id": str(customer_id),
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Pago registrado exitosamente - Payment ID: {payment_id}")
                return json.dumps(response, ensure_ascii=False)
            
            else:
                # Error al registrar el pago
                error_msg = "Error desconocido"
                if result and result.get("error"):
                    error_details = result["error"]
                    error_msg = error_details.get("message", "Error en Splynx")
                
                response = {
                    "success": False,
                    "codigo_error": "500",
                    "mensaje": f"Error registrando pago: {error_msg}",
                    "rut": rut_cliente,
                    "transaccion_id": transaccion,
                    "detalles": result
                }
                
                logger.error(f"Error registrando pago en Splynx: {result}")
                return json.dumps(response, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error registrando pago {rut_cliente}: {str(e)}")
            
            # Respuesta de error
            error_response = {
                "success": False,
                "codigo_error": "500",
                "mensaje": f"Error interno del servidor: {str(e)}",
                "rut": rut_cliente,
                "transaccion_id": transaccion
            }
            return json.dumps(error_response, ensure_ascii=False)
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """Obtener los métodos de pago disponibles en Splynx"""
        try:
            methods = self.splynx_client.get("/admin/finance/payment-methods")
            return {"success": True, "payment_methods": methods}
        except Exception as e:
            logger.error(f"Error obteniendo métodos de pago: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """Probar la conexión con Splynx usando BD y API"""
        try:
            # Probar conexión BD primero
            db_test = self.splynx_db.test_connection()
            api_test = self.splynx_client.test_connection()
            
            return {
                "success": db_test.get("success") and api_test.get("success"),
                "database": db_test,
                "api": api_test,
                "message": "BD y API funcionando" if db_test.get("success") and api_test.get("success") else "Hay problemas de conexión"
            }
        except Exception as e:
            logger.error(f"Error probando conexiones: {str(e)}")
            return {
                "success": False,
                "message": f"Error probando conexiones: {str(e)}"
            }