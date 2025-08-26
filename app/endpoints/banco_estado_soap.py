"""
Endpoints SOAP compatibles con el WSDL de BancoEstado
Implementa consultarCliente y registrarPago
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
import logging
from typing import Dict, Any

from ..services.banco_estado_soap_service import BancoEstadoSOAPService

logger = logging.getLogger(__name__)
router = APIRouter()

# Instancia del servicio
soap_service = BancoEstadoSOAPService()

@router.post("/consultarCliente", response_class=PlainTextResponse)
async def consultar_cliente(request: Request):
    """
    Endpoint SOAP para consultar cliente por RUT
    Compatible con consultarClienteRequest del WSDL
    
    Acepta:
    - SOAP XML con rutCliente
    - Form data con rutCliente 
    - JSON con rutCliente
    - Query param rutCliente
    """
    try:
        rut_cliente = None
        
        # Obtener RUT de diferentes fuentes posibles
        content_type = request.headers.get("content-type", "").lower()
        
        if "xml" in content_type or "soap" in content_type:
            # Request SOAP XML
            body = await request.body()
            body_text = body.decode('utf-8')
            
            # Extraer rutCliente del XML SOAP (método simple)
            import re
            rut_match = re.search(r'<rutCliente[^>]*>([^<]+)</rutCliente>', body_text)
            if rut_match:
                rut_cliente = rut_match.group(1)
            
            logger.info(f"SOAP Request recibido: {body_text[:200]}...")
            
        elif "form" in content_type:
            # Form data
            form = await request.form()
            rut_cliente = form.get("rutCliente")
            
        elif "json" in content_type:
            # JSON data
            json_data = await request.json()
            rut_cliente = json_data.get("rutCliente")
            
        # Si no se encontró en el body, buscar en query params
        if not rut_cliente:
            rut_cliente = request.query_params.get("rutCliente")
        
        if not rut_cliente:
            logger.error("RUT del cliente no proporcionado")
            return """{"success": false, "codigo_error": "1", "mensaje": "RUT del cliente es requerido"}"""
        
        # Llamar al servicio
        result = soap_service.consultar_cliente(rut_cliente)
        
        logger.info(f"Consulta cliente {rut_cliente} completada")
        return result
        
    except Exception as e:
        logger.error(f"Error en consultarCliente: {str(e)}")
        return f'{{"success": false, "codigo_error": "500", "mensaje": "Error interno: {str(e)}"}}'

@router.post("/registrarPago", response_class=PlainTextResponse)
async def registrar_pago(request: Request):
    """
    Endpoint SOAP para registrar pago
    Compatible con registrarPagoRequest del WSDL
    
    Acepta los parámetros:
    - rutCliente: RUT del cliente
    - factura: ID de la factura
    - monto: Monto del pago
    - descripcion: Descripción del pago
    - pasarela: Pasarela utilizada
    - transaccion: ID de transacción
    """
    try:
        # Inicializar parámetros
        params = {
            "rutCliente": None,
            "factura": None, 
            "monto": None,
            "descripcion": None,
            "pasarela": None,
            "transaccion": None
        }
        
        content_type = request.headers.get("content-type", "").lower()
        
        if "xml" in content_type or "soap" in content_type:
            # Request SOAP XML
            body = await request.body()
            body_text = body.decode('utf-8')
            
            # Extraer parámetros del XML SOAP
            import re
            for param in params.keys():
                pattern = f'<{param}[^>]*>([^<]+)</{param}>'
                match = re.search(pattern, body_text)
                if match:
                    params[param] = match.group(1)
            
            logger.info(f"SOAP registrarPago recibido: {body_text[:300]}...")
            
        elif "form" in content_type:
            # Form data
            form = await request.form()
            for param in params.keys():
                params[param] = form.get(param)
                
        elif "json" in content_type:
            # JSON data
            json_data = await request.json()
            for param in params.keys():
                params[param] = json_data.get(param)
        
        # Si no se encontró en el body, buscar en query params
        for param in params.keys():
            if not params[param]:
                params[param] = request.query_params.get(param)
        
        # Validar parámetros requeridos
        required_params = ["rutCliente", "factura", "monto", "descripcion", "pasarela", "transaccion"]
        missing_params = [p for p in required_params if not params[p]]
        
        if missing_params:
            error_msg = f"Parámetros requeridos faltantes: {', '.join(missing_params)}"
            logger.error(error_msg)
            return f'{{"success": false, "codigo_error": "1", "mensaje": "{error_msg}"}}'
        
        # Convertir monto a float
        try:
            monto = float(params["monto"])
        except (ValueError, TypeError):
            logger.error(f"Monto inválido: {params['monto']}")
            return '{"success": false, "codigo_error": "2", "mensaje": "Monto debe ser un número válido"}'
        
        # Llamar al servicio
        result = soap_service.registrar_pago(
            rut_cliente=params["rutCliente"],
            factura=params["factura"],
            monto=monto,
            descripcion=params["descripcion"],
            pasarela=params["pasarela"],
            transaccion=params["transaccion"]
        )
        
        logger.info(f"Pago registrado para {params['rutCliente']} - Transacción: {params['transaccion']}")
        return result
        
    except Exception as e:
        logger.error(f"Error en registrarPago: {str(e)}")
        return f'{{"success": false, "codigo_error": "500", "mensaje": "Error interno: {str(e)}"}}'

@router.get("/wsdl", response_class=PlainTextResponse)
async def get_wsdl():
    """
    Endpoint para servir el WSDL (opcional, para compatibilidad)
    """
    wsdl_content = '''<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
             xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
             xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" 
             xmlns:tns="ws/" 
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" 
             xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" 
             xmlns="http://schemas.xmlsoap.org/wsdl/" 
             targetNamespace="ws/">
    <message name="consultarClienteRequest">
        <part name="rutCliente" type="xsd:string"/>
    </message>
    <message name="consultarClienteResponse">
        <part name="return" type="xsd:string"/>
    </message>
    <message name="registrarPagoRequest">
        <part name="rutCliente" type="xsd:string"/>
        <part name="factura" type="xsd:string"/>
        <part name="monto" type="xsd:float"/>
        <part name="descripcion" type="xsd:string"/>
        <part name="pasarela" type="xsd:string"/>
        <part name="transaccion" type="xsd:string"/>
    </message>
    <message name="registrarPagoResponse">
        <part name="return" type="xsd:string"/>
    </message>
    <portType name="BancoEstadoPortType">
        <operation name="consultarCliente">
            <input message="tns:consultarClienteRequest"/>
            <output message="tns:consultarClienteResponse"/>
        </operation>
        <operation name="registrarPago">
            <input message="tns:registrarPagoRequest"/>
            <output message="tns:registrarPagoResponse"/>
        </operation>
    </portType>
</definitions>'''
    
    return wsdl_content

@router.get("/test-connection")
async def test_connection():
    """Endpoint para probar la conexión con Splynx"""
    return soap_service.test_connection()

@router.get("/payment-methods")
async def get_payment_methods():
    """Endpoint para obtener los métodos de pago disponibles"""
    return soap_service.get_payment_methods()

# Endpoints de prueba para desarrollo
@router.get("/test-consulta/{rut}")
async def test_consulta_cliente(rut: str):
    """Endpoint de prueba para consultar cliente"""
    result = soap_service.consultar_cliente(rut)
    import json
    return json.loads(result)

@router.post("/test-pago")
async def test_registrar_pago(
    rut_cliente: str,
    factura: str,
    monto: float,
    descripcion: str = "Pago de prueba",
    pasarela: str = "BancoEstado",
    transaccion: str = "TEST123"
):
    """Endpoint de prueba para registrar pago"""
    result = soap_service.registrar_pago(
        rut_cliente=rut_cliente,
        factura=factura, 
        monto=monto,
        descripcion=descripcion,
        pasarela=pasarela,
        transaccion=transaccion
    )
    import json
    return json.loads(result)