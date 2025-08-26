from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from app.models.banco_estado import (
    ConsultarClienteRequest, 
    RegistrarPagoRequest, 
    BancoEstadoResponse
)
from app.services.banco_estado_internal import BancoEstadoInternalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banco-estado", tags=["BancoEstado"])

@router.post("/consultar-cliente", response_model=BancoEstadoResponse)
async def consultar_cliente(request: ConsultarClienteRequest):
    """
    Consultar Cliente - Replica the consultarCliente PHP function
    
    Obtener datos de una factura o última factura de un cliente
    
    Args:
        request: ConsultarClienteRequest with rut_cliente
        
    Returns:
        BancoEstadoResponse with client information or error details
    """
    try:
        logger.info(f"Received consultar_cliente request for RUT: {request.rut_cliente}")
        
        # Call the internal service (no external dependency)
        response = BancoEstadoInternalService.consultar_cliente(request.rut_cliente)
        
        if response.success:
            logger.info(f"Successfully consulted client {request.rut_cliente}")
            return response
        else:
            logger.warning(f"Client consultation failed for {request.rut_cliente}: {response.error}")
            return response
            
    except Exception as e:
        logger.error(f"Unexpected error in consultar_cliente: {str(e)}")
        return BancoEstadoResponse(
            success=False,
            error={"codigo_error": "500", "descripcion_error": f"Internal server error: {str(e)}"},
            raw_xml=None
        )

@router.post("/registrar-pago", response_model=BancoEstadoResponse)
async def registrar_pago(request: RegistrarPagoRequest):
    """
    Registrar Pago - Replica the registrarPago PHP function
    
    Pagar factura y activar un cliente
    
    Args:
        request: RegistrarPagoRequest with payment details
        
    Returns:
        BancoEstadoResponse with payment confirmation or error details
    """
    try:
        logger.info(f"Received registrar_pago request for RUT: {request.rut_cliente}, Invoice: {request.factura}")
        
        # Call the internal service (no external dependency)
        response = BancoEstadoInternalService.registrar_pago(
            rut_cliente=request.rut_cliente,
            factura=request.factura,
            monto=request.monto,
            descripcion=request.descripcion,
            pasarela=request.pasarela,
            transaccion=request.transaccion
        )
        
        if response.success:
            logger.info(f"Successfully registered payment for client {request.rut_cliente}")
            return response
        else:
            logger.warning(f"Payment registration failed for {request.rut_cliente}: {response.error}")
            return response
            
    except Exception as e:
        logger.error(f"Unexpected error in registrar_pago: {str(e)}")
        return BancoEstadoResponse(
            success=False,
            error={"codigo_error": "500", "descripcion_error": f"Internal server error: {str(e)}"},
            raw_xml=None
        )

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running
    """
    return {"status": "healthy", "service": "BancoEstado API"}

@router.get("/test-splynx")
async def test_splynx_connection():
    """
    Test endpoint para verificar conexión con Splynx
    """
    try:
        from app.services.splynx_client import SplynxClient
        
        splynx = SplynxClient()
        result = splynx.test_connection()
        
        return {
            "service": "Splynx Connection Test",
            "timestamp": "2025-08-25",
            "splynx_api": "https://crm.metrowan.cl/api/2.0",
            "connection": result
        }
        
    except Exception as e:
        logger.error(f"Error testing Splynx connection: {e}")
        return {
            "service": "Splynx Connection Test",
            "timestamp": "2025-08-25",
            "connection": {
                "success": False,
                "message": "Error de conexión",
                "details": str(e)
            }
        }

@router.get("/debug-splynx/{rut}")
async def debug_splynx_search(rut: str):
    """
    Debug endpoint para probar diferentes métodos de búsqueda en Splynx
    """
    try:
        from app.services.splynx_client import SplynxClient
        
        splynx = SplynxClient()
        
        # Probar diferentes endpoints de búsqueda
        results = {}
        
        # 1. Test básico de conexión
        results["connection_test"] = splynx.test_connection()
        
        # 2. Listar primeros clientes
        try:
            first_customers = splynx._make_request("GET", "/admin/customers/customer", params={"limit": 3})
            results["first_customers"] = first_customers
        except:
            results["first_customers"] = {"error": "No se pudo obtener lista"}
        
        # 3. Búsqueda específica por RUT
        try:
            customer_result = splynx.search_customer_by_rut(rut)
            results["customer_search"] = customer_result or "No encontrado"
        except Exception as e:
            results["customer_search"] = {"error": str(e)}
        
        return {
            "rut_buscado": rut,
            "debug_results": results,
            "note": "Revisa los logs del servidor para más detalles"
        }
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return {
            "error": "Error en debug",
            "details": str(e)
        }