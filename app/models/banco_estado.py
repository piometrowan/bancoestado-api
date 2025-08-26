from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ConsultarClienteRequest(BaseModel):
    rut_cliente: str = Field(..., description="RUT del cliente")

class RegistrarPagoRequest(BaseModel):
    rut_cliente: str = Field(..., description="RUT del cliente")
    factura: str = Field(..., description="ID de Factura")
    monto: float = Field(..., description="Monto a pagar (sin formato ej: 500 o 500.35)")
    descripcion: str = Field(..., description="Alguna nota o descripción del pago")
    pasarela: str = Field(default="", description="Tipo de pago (oficina, página web, etc.)")
    transaccion: str = Field(default="", description="Nº de transacción (opcional)")

class BancoEstadoResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None
    raw_xml: Optional[str] = None

class ClienteInfo(BaseModel):
    id_cliente: Optional[str] = None
    rut_cliente: Optional[str] = None
    nombre: Optional[str] = None
    estado: Optional[str] = None
    facturas: Optional[List[Dict[str, Any]]] = None

class PagoResponse(BaseModel):
    id_cliente: Optional[str] = None
    rut_cliente: Optional[str] = None
    fecha_envio: Optional[str] = None
    estado: Optional[str] = None
    mensaje: Optional[str] = None

class ErrorResponse(BaseModel):
    codigo_error: Optional[str] = None
    descripcion_error: Optional[str] = None