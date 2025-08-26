import os
from typing import Optional

class Settings:
    # API Configuration
    API_TITLE: str = "BancoEstado API for Splynx"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Timeout settings
    REQUEST_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Splynx Configuration (usar variables de entorno en producción)
    SPLYNX_BASE_URL: str = os.getenv("SPLYNX_BASE_URL", "https://micuenta.gosur.cl/api/2.0")
    SPLYNX_API_KEY: str = os.getenv("SPLYNX_API_KEY", "28565dbe25d9fc7229163d71ec86787e")
    SPLYNX_API_SECRET: str = os.getenv("SPLYNX_API_SECRET", "aaf2eec4adbef84560c611465d8f7f2d")
    SPLYNX_TIMEOUT: int = int(os.getenv("SPLYNX_TIMEOUT", "30"))
    
    # Configuración de búsqueda de clientes por RUT
    # Campos donde se puede encontrar el RUT del cliente en Splynx
    SPLYNX_RUT_FIELDS: list = [
        "login",           # Campo login
        "name",            # Nombre del cliente
        "rut",             # Campo adicional RUT
        "cedula",          # Campo adicional cédula
        "identification",  # Campo adicional identificación
        "tax_id",          # Campo adicional tax ID
        "document",        # Campo adicional documento
        "dni",             # Campo adicional DNI
        "ci"               # Campo adicional CI
    ]
    
    # Configuración de transacciones
    SPLYNX_DEFAULT_TRANSACTION_CATEGORY: str = os.getenv("SPLYNX_DEFAULT_TRANSACTION_CATEGORY", "1")
    SPLYNX_DEFAULT_TAX_PERCENT: float = float(os.getenv("SPLYNX_DEFAULT_TAX_PERCENT", "0"))
    
    # Modo Mock/Prueba (para cuando no hay acceso a Splynx real)
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "false").lower() == "true"
    
    def get_splynx_config(self) -> dict:
        """Obtener configuración de Splynx para el cliente"""
        return {
            "base_url": self.SPLYNX_BASE_URL,
            "api_key": self.SPLYNX_API_KEY,
            "api_secret": self.SPLYNX_API_SECRET,
            "timeout": self.SPLYNX_TIMEOUT,
            "rut_fields": self.SPLYNX_RUT_FIELDS,
            "default_category": self.SPLYNX_DEFAULT_TRANSACTION_CATEGORY,
            "default_tax": self.SPLYNX_DEFAULT_TAX_PERCENT
        }

settings = Settings()