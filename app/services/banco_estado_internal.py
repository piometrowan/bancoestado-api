"""
Servicio interno de BancoEstado
Reemplaza la dependencia de accesoclientes.mitplay.cl
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.banco_estado import (
    BancoEstadoResponse,
    ClienteInfo,
    PagoResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

class BancoEstadoInternalService:
    """
    Servicio interno que reemplaza accesoclientes.mitplay.cl
    Proporciona la misma funcionalidad sin depender del servidor externo
    """
    
    @staticmethod
    def consultar_cliente(rut_cliente: str) -> BancoEstadoResponse:
        """
        Consultar cliente - funcionalidad interna
        """
        try:
            logger.info(f"Internal consultarCliente called with RUT: {rut_cliente}")
            
            cliente_data = BancoEstadoInternalService._get_client_data(rut_cliente)
            
            if cliente_data:
                # Convertir a ClienteInfo
                cliente_info = ClienteInfo(
                    id_cliente=cliente_data['id_cliente'],
                    rut_cliente=cliente_data['rut_cliente'],
                    nombre=cliente_data['nombre'],
                    estado=cliente_data['estado'],
                    facturas=[cliente_data['ultima_factura']]
                )
                
                return BancoEstadoResponse(
                    success=True,
                    data=cliente_info.dict(),
                    raw_xml=BancoEstadoInternalService._generate_client_xml(cliente_data)
                )
            else:
                error_info = ErrorResponse(
                    codigo_error="3",
                    descripcion_error="Cliente no encontrado"
                )
                
                return BancoEstadoResponse(
                    success=False,
                    error=error_info.dict(),
                    raw_xml=BancoEstadoInternalService._generate_error_xml("3", "Cliente no encontrado")
                )
                
        except Exception as e:
            logger.error(f"Error in internal consultarCliente for RUT {rut_cliente}: {str(e)}")
            return BancoEstadoResponse(
                success=False,
                error={"codigo_error": "500", "descripcion_error": str(e)},
                raw_xml=BancoEstadoInternalService._generate_error_xml("500", "Error interno del servidor")
            )
    
    @staticmethod
    def registrar_pago(
        rut_cliente: str, 
        factura: str, 
        monto: float, 
        descripcion: str,
        pasarela: str = "", 
        transaccion: str = ""
    ) -> BancoEstadoResponse:
        """
        Registrar pago - funcionalidad interna
        """
        try:
            logger.info(f"Internal registrarPago called with RUT: {rut_cliente}, Factura: {factura}, Monto: {monto}")
            
            payment_result = BancoEstadoInternalService._process_payment(
                rut_cliente, factura, monto, descripcion, pasarela, transaccion
            )
            
            if payment_result['success']:
                pago_info = PagoResponse(
                    id_cliente=payment_result['id_cliente'],
                    rut_cliente=rut_cliente,
                    fecha_envio=datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00"),
                    estado="aceptado",
                    mensaje="Pago registrado correctamente"
                )
                
                return BancoEstadoResponse(
                    success=True,
                    data=pago_info.dict(),
                    raw_xml=BancoEstadoInternalService._generate_payment_xml(payment_result, rut_cliente)
                )
            else:
                error_info = ErrorResponse(
                    codigo_error=payment_result['codigo_error'],
                    descripcion_error=payment_result['descripcion_error']
                )
                
                return BancoEstadoResponse(
                    success=False,
                    error=error_info.dict(),
                    raw_xml=BancoEstadoInternalService._generate_error_xml(
                        payment_result['codigo_error'], 
                        payment_result['descripcion_error']
                    )
                )
                
        except Exception as e:
            logger.error(f"Error in internal registrarPago for RUT {rut_cliente}: {str(e)}")
            return BancoEstadoResponse(
                success=False,
                error={"codigo_error": "500", "descripcion_error": str(e)},
                raw_xml=BancoEstadoInternalService._generate_error_xml("500", f"Error interno del servidor: {str(e)}")
            )
    
    @staticmethod
    def _get_client_data(rut_cliente: str) -> Optional[Dict[str, Any]]:
        """
        Obtener datos del cliente desde Splynx
        """
        try:
            from app.services.splynx_client import SplynxClient
            
            splynx = SplynxClient()
            customer_data = splynx.get_customer_by_rut(rut_cliente)
            
            if not customer_data:
                logger.warning(f"Cliente con RUT {rut_cliente} no encontrado en Splynx")
                return None
            
            # Convertir datos de Splynx al formato esperado
            facturas_splynx = customer_data.get('invoices', [])
            facturas_formatted = []
            
            for factura in facturas_splynx[:5]:  # Máximo 5 facturas más recientes
                facturas_formatted.append({
                    "id": factura.get('id', 'N/A'),
                    "monto": float(factura.get('total', 0)),
                    "vencimiento": factura.get('due_date', 'N/A'),
                    "estado": BancoEstadoInternalService._get_invoice_status(factura.get('status', ''))
                })
            
            # Tomar la factura más reciente para compatibilidad
            ultima_factura = facturas_formatted[0] if facturas_formatted else {
                "id": "Sin facturas",
                "monto": 0.0,
                "vencimiento": "N/A",
                "estado": "sin_facturas"
            }
            
            return {
                "id_cliente": str(customer_data.get('id', '')),
                "rut_cliente": rut_cliente,
                "nombre": customer_data.get('name', 'Cliente Splynx'),
                "estado": BancoEstadoInternalService._get_customer_status(customer_data.get('status', '')),
                "todas_facturas": facturas_formatted,
                "ultima_factura": ultima_factura
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del cliente {rut_cliente} desde Splynx: {e}")
            return None
    
    @staticmethod
    def _get_customer_status(splynx_status: str) -> str:
        """Convertir estado de Splynx a formato BancoEstado"""
        status_map = {
            'active': 'activo',
            'new': 'nuevo',
            'blocked': 'bloqueado',
            'disabled': 'inactivo'
        }
        return status_map.get(splynx_status.lower(), 'desconocido')
    
    @staticmethod
    def _get_invoice_status(splynx_status: str) -> str:
        """Convertir estado de factura de Splynx a formato BancoEstado"""
        status_map = {
            'unpaid': 'pendiente',
            'paid': 'pagado',
            'overdue': 'vencida',
            'new': 'nueva'
        }
        return status_map.get(splynx_status.lower(), 'pendiente')
    
    @staticmethod
    def _process_payment(
        rut_cliente: str, 
        factura: str, 
        monto: float, 
        descripcion: str, 
        pasarela: str, 
        transaccion: str
    ) -> Dict[str, Any]:
        """
        Procesar pago - AQUÍ IMPLEMENTAS TU LÓGICA DE PAGOS REAL
        """
        try:
            # Validar cliente existe
            cliente_data = BancoEstadoInternalService._get_client_data(rut_cliente)
            if not cliente_data:
                return {
                    "success": False,
                    "codigo_error": "3",
                    "descripcion_error": "Cliente no encontrado"
                }
            
            # Validar monto
            if monto <= 0:
                return {
                    "success": False,
                    "codigo_error": "4",
                    "descripcion_error": "Monto inválido"
                }
            
            # IMPLEMENTAR LÓGICA REAL CON SPLYNX:
            # 1. Buscar cliente por RUT en Splynx
            # 2. Validar factura
            # 3. Registrar pago como transacción
            # 4. Devolver confirmación
            
            logger.info(f"Processing payment in Splynx for RUT={rut_cliente}, Amount={monto}, Invoice={factura}")
            
            try:
                from app.services.splynx_client import SplynxClient
                
                splynx = SplynxClient()
                payment_result = splynx.process_payment_by_rut(
                    rut=rut_cliente,
                    factura_id=factura,
                    amount=monto,
                    description=descripcion
                )
                
                if payment_result['success']:
                    return {
                        "success": True,
                        "id_cliente": payment_result['customer_id'],
                        "transaction_id": payment_result.get('transaction_id', ''),
                        "invoice_id": payment_result.get('invoice_id', factura)
                    }
                else:
                    return {
                        "success": False,
                        "codigo_error": payment_result.get('codigo_error', '500'),
                        "descripcion_error": payment_result.get('message', 'Error procesando pago')
                    }
                    
            except Exception as e:
                logger.error(f"Exception in Splynx payment processing: {e}")
                return {
                    "success": False,
                    "codigo_error": "500",
                    "descripcion_error": f"Error interno procesando pago: {str(e)}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "codigo_error": "500",
                "descripcion_error": str(e)
            }
    
    @staticmethod
    def _generate_client_xml(cliente_data: Dict[str, Any]) -> str:
        """Generar XML de respuesta para consultarCliente (igual al PHP original)"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<RESPUESTA>
    <ID_CLIENTE>{cliente_data['id_cliente']}</ID_CLIENTE>
    <RUT_CLIENTE>{cliente_data['rut_cliente']}</RUT_CLIENTE>
    <CLIENTE>
        <NOMBRE>{cliente_data['nombre']}</NOMBRE>
        <ESTADO>{cliente_data['estado']}</ESTADO>
        <FACTURAS>
            <FACTURA>
                <ID_FACTURA>{cliente_data['ultima_factura']['id']}</ID_FACTURA>
                <MONTO>{cliente_data['ultima_factura']['monto']}</MONTO>
                <VENCIMIENTO>{cliente_data['ultima_factura']['vencimiento']}</VENCIMIENTO>
                <ESTADO>{cliente_data['ultima_factura']['estado']}</ESTADO>
            </FACTURA>
        </FACTURAS>
    </CLIENTE>
</RESPUESTA>"""
    
    @staticmethod
    def _generate_payment_xml(payment_result: Dict[str, Any], rut_cliente: str) -> str:
        """Generar XML de respuesta para registrarPago (igual al PHP original)"""
        fecha_envio = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00")
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<RESPUESTA>
    <ID_CLIENTE>{payment_result['id_cliente']}</ID_CLIENTE>
    <RUT_CLIENTE>{rut_cliente}</RUT_CLIENTE>
    <FECHA_ENVIO>{fecha_envio}</FECHA_ENVIO>
    <ESTADO>aceptado</ESTADO>
    <MENSAJE>Pago registrado correctamente</MENSAJE>
</RESPUESTA>"""
    
    @staticmethod
    def _generate_error_xml(codigo_error: str, descripcion_error: str) -> str:
        """Generar XML de error (igual al PHP original)"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<RESPUESTA>
    <CLIENTE/>
    <ERRORES>
        <CODIGO_ERROR>{codigo_error}</CODIGO_ERROR>
        <DESCRIPCION_ERROR>{descripcion_error}</DESCRIPCION_ERROR>
    </ERRORES>
</RESPUESTA>"""