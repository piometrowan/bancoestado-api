# 🚀 BancoEstado API - Integración con Splynx ✅ CORREGIDA

**API REST para integración con Splynx CRM usando la documentación oficial Splynx API v2.0**

Esta API proporciona endpoints REST para BancoEstado con integración completa a Splynx CRM.

## 🔧 Correcciones Implementadas

✅ **Autenticación Splynx corregida** según documentación oficial  
✅ **Parámetros de búsqueda** en formato correcto para Splynx API  
✅ **Manejo de errores** completo según códigos Splynx  
✅ **Configuración centralizada** con variables de entorno  
✅ **Script de debug mejorado** para diagnosticar problemas  

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
# Configuración de Splynx API
SPLYNX_BASE_URL=https://crm.metrowan.cl/api/2.0
SPLYNX_API_KEY=tu_api_key_aqui
SPLYNX_API_SECRET=tu_api_secret_aqui
SPLYNX_TIMEOUT=30

# Configuración de transacciones
SPLYNX_DEFAULT_TRANSACTION_CATEGORY=1
SPLYNX_DEFAULT_TAX_PERCENT=0
```

### 2. Permisos API Key en Splynx

Tu API key debe tener permisos para:
- ✅ **Customers** (lectura) - buscar clientes
- ✅ **Invoices** (lectura) - consultar facturas
- ✅ **Transactions** (escritura) - registrar pagos

**⚠️ Importante:** Habilita "Unsecure access" en tu API key si tienes problemas de autenticación.

## 📁 Instalación

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables (copiar .env.example a .env)
cp .env.example .env
# Editar .env con tus credenciales

# 3. Ejecutar API
python main.py
```

## 🧪 Pruebas y Diagnóstico

### Script de Prueba Completo

```bash
python test_complete.py
```

El script incluye:
1. **Test de conexión** con Splynx
2. **Debug detallado** de estructura de datos
3. **Consultar cliente** por REST
4. **Consultar cliente** por SOAP (compatibilidad PHP)
5. **Registrar pago** 
6. **Verificar WSDL**

### Debug Individual

```bash
# Test solo conexión Splynx
curl http://localhost:8000/banco-estado/test-splynx

# Debug específico para un RUT
curl http://localhost:8000/banco-estado/debug-splynx/12345678-9
```

## 📚 Endpoints API

### 🔍 Consultar Cliente
```bash
POST /banco-estado/consultar-cliente
Content-Type: application/json

{
    "rut_cliente": "12345678-9"
}
```

**Respuesta exitosa:**
```json
{
    "success": true,
    "data": {
        "id_cliente": "123",
        "rut_cliente": "12345678-9", 
        "nombre": "Juan Pérez",
        "estado": "activo",
        "facturas": [
            {
                "id": "456",
                "numero": "INV-2025-001",
                "monto": "25000.50",
                "estado": "not_paid",
                "vencimiento": "2025-09-15"
            }
        ]
    }
}
```

### 💳 Registrar Pago
```bash
POST /banco-estado/registrar-pago
Content-Type: application/json

{
    "rut_cliente": "12345678-9",
    "factura": "456",
    "monto": 25000.50,
    "descripcion": "Pago mensual internet",
    "pasarela": "BancoEstado",
    "transaccion": "TXN-2025-001"
}
```

### 🩺 Health Check
```bash
GET /banco-estado/health
```

## 🔍 Búsqueda de Clientes por RUT

La API busca el RUT en múltiples campos de Splynx:

**Campos principales:**
- `login` (campo login del cliente)
- `name` (nombre del cliente)

**Campos adicionales configurables:**
- `rut`, `cedula`, `identification`
- `tax_id`, `document`, `dni`, `ci`

**Modificar campos de búsqueda** en `config/settings.py`:
```python
SPLYNX_RUT_FIELDS = [
    "login", "name", "rut", "cedula", 
    "identification", "tax_id", "document"
]
```

## 🛠️ Solución de Problemas

### Error 401 - Unauthorized
```
✅ Verificar SPLYNX_API_KEY y SPLYNX_API_SECRET
✅ Confirmar permisos del API key en Splynx
✅ Habilitar "Unsecure access" si es necesario
```

### Cliente no encontrado
```
✅ Verificar que el RUT existe en Splynx
✅ Usar endpoint debug para ver estructura: /debug-splynx/{rut}
✅ Configurar SPLYNX_RUT_FIELDS según tu setup
```

### Error de transacciones
```
✅ Configurar SPLYNX_DEFAULT_TRANSACTION_CATEGORY correcto
✅ Verificar permisos de API para crear transacciones
✅ Revisar logs del servidor para detalles
```

### Timeout de conexión
```
✅ Verificar SPLYNX_BASE_URL accesible
✅ Ajustar SPLYNX_TIMEOUT si es necesario
✅ Revisar firewall/conectividad
```

## 📊 Compatibilidad SOAP (opcional)

Para compatibilidad con sistemas legacy:

**WSDL:** `http://localhost:8000/bancoestado/web/index.php?wsdl`  
**Endpoint:** `POST /bancoestado/web/index.php`

## 📁 Estructura del Proyecto

```
banco_estado_python_api/
├── main.py                     # 🚀 Aplicación principal FastAPI
├── requirements.txt            # 📦 Dependencias Python
├── .env.example               # ⚙️  Variables de entorno de ejemplo
├── test_complete.py           # 🧪 Script de pruebas completo
├── config/
│   └── settings.py            # ⚙️  Configuración centralizada
├── app/
│   ├── endpoints/
│   │   └── banco_estado.py    # 🌐 Endpoints REST
│   ├── models/
│   │   └── banco_estado.py    # 📋 Modelos de datos
│   └── services/
│       ├── banco_estado_internal.py  # 🔧 Lógica de negocio
│       └── splynx_client.py          # 🔌 Cliente Splynx API ✅ CORREGIDO
```

## 📋 Registro de Correcciones

### Autenticación Splynx
- ✅ Firma HMAC-SHA256 corregida según documentación PHP
- ✅ Nonce usando `round(microtime(true) * 100)` 
- ✅ Fallback a autenticación básica
- ✅ Manejo completo de códigos de error HTTP

### Búsqueda de Clientes  
- ✅ Parámetros usando formato `main_attributes[campo]`
- ✅ Soporte para operadores LIKE, BETWEEN, IN
- ✅ Búsqueda en campos adicionales `additional_attributes[campo]`
- ✅ Debug detallado de estructura de datos

### Gestión de Facturas
- ✅ Filtrado por `customer_id` correcto
- ✅ Ordenamiento por fecha descendente
- ✅ Filtro de facturas pendientes (`not_paid`, `pending`)

### Configuración
- ✅ Variables de entorno para credenciales
- ✅ Campos de búsqueda RUT configurables
- ✅ Configuración de categorías de transacciones

---

## 🎉 API Lista para Producción

**✅ Integración Splynx corregida y validada**  
**✅ Autenticación según documentación oficial**  
**✅ Manejo robusto de errores**  
**✅ Debug y logging completo**  

**¡Ejecuta `python test_complete.py` para validar tu configuración!** 🚀