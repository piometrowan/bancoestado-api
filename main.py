from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import logging
import uvicorn
from config.settings import settings
from app.endpoints.banco_estado import router as banco_estado_router
from app.endpoints.banco_estado_soap import router as soap_router
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info("REST API: /banco-estado/ (for Splynx)")
    logger.info("No external dependencies - fully self-contained")
    yield
    # Shutdown
    logger.info("Shutting down BancoEstado Unified API")

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    API BancoEstado - REST para Splynx
    
    API REST endpoints:
    - POST /banco-estado/consultar-cliente
    - POST /banco-estado/registrar-pago  
    - GET /banco-estado/health
    
    NOTA: Requiere conexión a base de datos real para funcionar.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for Splynx integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(banco_estado_router)
app.include_router(soap_router)

# Ruta exacta para reemplazar el PHP original
@app.api_route("/bancoestado/web/index.php", methods=["GET", "POST"])
async def banco_estado_php_endpoint(request: Request):
    """
    Endpoint que replica exactamente la ruta del PHP original
    GET: Devuelve WSDL
    POST: Procesa solicitudes SOAP
    """
    if request.method == "GET":
        # Verificar si se solicita WSDL
        query_params = dict(request.query_params)
        if "wsdl" in query_params or "wsdl" in str(request.url).lower():
            return Response(
                content=_generate_wsdl(),
                media_type="text/xml",
                headers={"Content-Type": "text/xml; charset=utf-8"}
            )
        else:
            return {"message": "BancoEstado SOAP Service", "status": "active"}
    
    elif request.method == "POST":
        # Procesar solicitud SOAP
        body = await request.body()
        content_type = request.headers.get("content-type", "")
        
        if "soap" in content_type.lower() or "xml" in content_type.lower():
            return await _process_soap_request(body.decode())
        else:
            return {"error": "Content-Type debe ser application/soap+xml o text/xml"}

def _generate_wsdl() -> str:
    """Generar WSDL básico para compatibilidad"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://bancoestado.local/"
             targetNamespace="http://bancoestado.local/">
    
    <message name="consultarClienteRequest">
        <part name="rut_cliente" type="xsd:string"/>
    </message>
    <message name="consultarClienteResponse">
        <part name="return" type="xsd:string"/>
    </message>
    
    <portType name="BancoEstadoPortType">
        <operation name="consultarCliente">
            <input message="tns:consultarClienteRequest"/>
            <output message="tns:consultarClienteResponse"/>
        </operation>
    </portType>
    
    <binding name="BancoEstadoBinding" type="tns:BancoEstadoPortType">
        <soap:binding transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="consultarCliente">
            <soap:operation soapAction="consultarCliente"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
    </binding>
    
    <service name="BancoEstadoService">
        <port name="BancoEstadoPort" binding="tns:BancoEstadoBinding">
            <soap:address location="http://localhost:8000/bancoestado/web/index.php"/>
        </port>
    </service>
</definitions>'''

async def _process_soap_request(soap_body: str) -> Response:
    """Procesar solicitud SOAP y devolver XML"""
    try:
        # Extraer operación del SOAP body
        if "consultarCliente" in soap_body:
            # Extraer RUT del XML SOAP
            import re
            rut_match = re.search(r'<rut_cliente[^>]*>([^<]+)</rut_cliente>', soap_body)
            if rut_match:
                rut = rut_match.group(1)
                from app.services.banco_estado_internal import BancoEstadoInternalService
                result = BancoEstadoInternalService.consultar_cliente(rut)
                return Response(
                    content=result.raw_xml,
                    media_type="text/xml",
                    headers={"Content-Type": "text/xml; charset=utf-8"}
                )
        
        # Si no se puede procesar
        error_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<RESPUESTA>
    <ERRORES>
        <CODIGO_ERROR>400</CODIGO_ERROR>
        <DESCRIPCION_ERROR>Solicitud SOAP no válida</DESCRIPCION_ERROR>
    </ERRORES>
</RESPUESTA>'''
        return Response(
            content=error_xml,
            media_type="text/xml",
            headers={"Content-Type": "text/xml; charset=utf-8"}
        )
        
    except Exception as e:
        error_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<RESPUESTA>
    <ERRORES>
        <CODIGO_ERROR>500</CODIGO_ERROR>
        <DESCRIPCION_ERROR>Error interno: {str(e)}</DESCRIPCION_ERROR>
    </ERRORES>
</RESPUESTA>'''
        return Response(
            content=error_xml,
            media_type="text/xml",
            headers={"Content-Type": "text/xml; charset=utf-8"}
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "BancoEstado API - REST para Splynx",
        "version": settings.API_VERSION,
        "status": "running",
        "database": "not_configured",
        "endpoints": {
            "rest_api": {
                "consultar_cliente": "/banco-estado/consultar-cliente",
                "registrar_pago": "/banco-estado/registrar-pago",
                "health_check": "/banco-estado/health"
            },
            "soap_compatibility": {
                "php_endpoint": "/bancoestado/web/index.php",
                "wsdl": "/bancoestado/web/index.php?wsdl"
            }
        },
        "documentation": "/docs",
        "note": "Requiere configurar base de datos para funcionar correctamente"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )