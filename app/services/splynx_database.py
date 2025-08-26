"""
Cliente para conectar directamente a la base de datos MySQL de Splynx
Implementación igual a ms-nxchile-mcp-server para buscar clientes por RUT real
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class SplynxDatabase:
    """Cliente para conectar directamente a la base de datos de Splynx"""
    
    def __init__(self):
        from config.settings import settings
        
        # Configuración de base de datos (igual a ms-nxchile)
        self.connection_string = self._get_db_connection_string()
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)
        
        logger.info("Conexión a base de datos Splynx inicializada")

    def _get_db_connection_string(self) -> str:
        """Obtener string de conexión a la base de datos"""
        # Usar las mismas credenciales que ms-nxchile-mcp-server
        host = "192.168.50.13"
        user = "openai"  
        password = "090731Nx"
        database = "splynx"
        
        return f"mysql+pymysql://{user}:{password}@{host}/{database}"
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        """Ejecutar query y retornar resultados"""
        try:
            with self.Session() as session:
                result = session.execute(text(query), params or {})
                return [dict(row) for row in result.mappings().all()]
        except Exception as e:
            logger.error(f"Error ejecutando query: {str(e)}")
            raise e

    def execute_commit(self, query: str, params: Dict = None):
        """Ejecutar query con commit"""
        try:
            with self.Session() as session:
                session.execute(text(query), params or {})
                session.commit()
        except Exception as e:
            logger.error(f"Error ejecutando commit: {str(e)}")
            session.rollback()
            raise e

    def buscar_cliente_por_rut(self, rut: str) -> Optional[Dict[str, Any]]:
        """
        Buscar cliente por RUT usando stored procedure
        Igual que ms-nxchile-mcp-server
        """
        try:
            logger.info(f"Buscando cliente por RUT en BD: {rut}")
            
            # Usar el mismo stored procedure que ms-nxchile
            query = "CALL splynx.buscar_cliente_por_rut(:rut_cliente);"
            params = {"rut_cliente": rut}
            
            result = self.execute_query(query, params)
            
            if result and len(result) > 0:
                cliente = result[0]
                logger.info(f"Cliente encontrado en BD: {cliente.get('nombre', 'Sin nombre')}")
                return cliente
            else:
                logger.warning(f"Cliente con RUT {rut} no encontrado en BD")
                return None
                
        except Exception as e:
            logger.error(f"Error buscando cliente por RUT {rut}: {str(e)}")
            return None

    def obtener_facturas_cliente(self, customer_id: int) -> List[Dict[str, Any]]:
        """Obtener facturas de un cliente desde la base de datos"""
        try:
            logger.info(f"Obteniendo facturas del cliente {customer_id} desde BD")
            
            # Skip if no customer_id
            if not customer_id:
                logger.warning("Customer ID vacío, no se pueden obtener facturas")
                return []
            
            # Query para obtener facturas del cliente (usar solo columnas que sabemos existen)
            query = """
            SELECT 
                id,
                customer_id,
                total,
                status,
                date_created,
                date_till as date_to_pay,
                discount,
                tax
            FROM invoices 
            WHERE customer_id = :customer_id 
            ORDER BY date_created DESC
            LIMIT 20
            """
            
            params = {"customer_id": customer_id}
            facturas = self.execute_query(query, params)
            
            logger.info(f"Encontradas {len(facturas)} facturas para cliente {customer_id}")
            return facturas
            
        except Exception as e:
            logger.error(f"Error obteniendo facturas del cliente {customer_id}: {str(e)}")
            return []

    def test_connection(self) -> Dict[str, Any]:
        """Probar la conexión a la base de datos"""
        try:
            logger.info("Probando conexión a base de datos Splynx")
            
            # Query simple para probar conexión
            result = self.execute_query("SELECT COUNT(*) as total FROM customers LIMIT 1")
            
            if result:
                total_customers = result[0].get('total', 0)
                return {
                    "success": True,
                    "message": "Conexión exitosa a base de datos Splynx",
                    "total_customers": total_customers
                }
            else:
                return {
                    "success": False,
                    "message": "No se pudieron obtener datos de la BD"
                }
                
        except Exception as e:
            logger.error(f"Error probando conexión BD: {str(e)}")
            return {
                "success": False,
                "message": f"Error de conexión BD: {str(e)}"
            }

    def close(self):
        """Cerrar conexión a la base de datos"""
        try:
            self.engine.dispose()
            logger.info("Conexión a base de datos cerrada")
        except Exception as e:
            logger.error(f"Error cerrando conexión BD: {str(e)}")

    def __del__(self):
        """Destructor para cerrar conexión automáticamente"""
        try:
            self.close()
        except:
            pass