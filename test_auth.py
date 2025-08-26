"""
Test específico de autenticación con Splynx
Prueba la firma HMAC-SHA256 paso a paso según la documentación
"""

import requests
import time
import hashlib
import hmac
import json

# Credenciales de tu .env
API_KEY = "aaf2eec4adbef84560c611465d8f7f2d"
API_SECRET = "28565dbe25d9fc7229163d71ec86787e"
SPLYNX_URL = "https://crm.metrowan.cl/api/2.0"

def test_signature_method_1():
    """Test método 1 de la documentación (round(microtime(true) * 100))"""
    print("🔐 MÉTODO 1 - Según líneas 41-42 de splynx.apib")
    print("-" * 50)
    
    # PASO 1: Generar nonce como en PHP
    nonce = int(round(time.time() * 100))
    print(f"1️⃣  Nonce: {nonce}")
    
    # PASO 2: Crear mensaje para firma
    message = f"{nonce}{API_KEY}"
    print(f"2️⃣  Message: '{message}'")
    
    # PASO 3: Generar firma HMAC-SHA256
    signature = hmac.new(
        API_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest().upper()
    print(f"3️⃣  Signature: {signature}")
    
    # PASO 4: Construir auth string
    auth_string = f"key={API_KEY}&signature={signature}&nonce={nonce}"
    print(f"4️⃣  Auth string: {auth_string}")
    
    # PASO 5: Construir header
    auth_header = f"Splynx-EA ({auth_string})"
    print(f"5️⃣  Auth header: {auth_header}")
    
    return {
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def test_signature_method_2():
    """Test método 2 de la documentación (time())"""
    print("\n🔐 MÉTODO 2 - Según líneas 79-83 de splynx.apib")
    print("-" * 50)
    
    # PASO 1: Generar nonce como en PHP
    nonce = int(time.time())
    print(f"1️⃣  Nonce: {nonce}")
    
    # PASO 2: Crear mensaje para firma
    message = f"{nonce}{API_KEY}"
    print(f"2️⃣  Message: '{message}'")
    
    # PASO 3: Generar firma HMAC-SHA256
    signature = hmac.new(
        API_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest().upper()
    print(f"3️⃣  Signature: {signature}")
    
    # PASO 4: Construir auth string
    auth_string = f"key={API_KEY}&signature={signature}&nonce={nonce}"
    print(f"4️⃣  Auth string: {auth_string}")
    
    # PASO 5: Construir header
    auth_header = f"Splynx-EA ({auth_string})"
    print(f"5️⃣  Auth header: {auth_header}")
    
    return {
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def test_basic_auth():
    """Test autenticación básica"""
    print("\n🔐 MÉTODO BÁSICO - Basic Authentication")
    print("-" * 50)
    
    import base64
    credentials = f"{API_KEY}:{API_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    print(f"1️⃣  Credentials: {credentials}")
    print(f"2️⃣  Encoded: {encoded}")
    
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def test_request_with_headers(headers, method_name):
    """Hacer request a Splynx con headers específicos"""
    print(f"\n📡 PROBANDO {method_name}")
    print("=" * 50)
    
    url = f"{SPLYNX_URL}/admin/customers/customer"
    params = {"limit": 1}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        print(f"⏱️  Tiempo: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            print("✅ ¡AUTENTICACIÓN EXITOSA!")
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                cliente = data[0]
                print(f"👤 Primer cliente: ID {cliente.get('id')}, Login: {cliente.get('login')}")
            return True
        elif response.status_code == 401:
            print("❌ Error 401 - Credenciales inválidas")
            try:
                error_data = response.json()
                print(f"📝 Error: {error_data}")
            except:
                print(f"📝 Texto: {response.text}")
            return False
        else:
            print(f"⚠️  Status {response.status_code}")
            print(f"📝 Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

def main():
    """Probar todos los métodos de autenticación"""
    print("🧪 PRUEBA DE AUTENTICACIÓN SPLYNX")
    print(f"🌐 URL: {SPLYNX_URL}")
    print(f"🔑 API Key: {API_KEY}")
    print(f"🔐 API Secret: {API_SECRET[:8]}...")
    print()
    
    # Probar método 1
    headers_1 = test_signature_method_1()
    success_1 = test_request_with_headers(headers_1, "MÉTODO 1 (microtime)")
    
    # Probar método 2  
    headers_2 = test_signature_method_2()
    success_2 = test_request_with_headers(headers_2, "MÉTODO 2 (time)")
    
    # Probar basic auth
    headers_basic = test_basic_auth()
    success_basic = test_request_with_headers(headers_basic, "BÁSICO")
    
    # Resumen
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 50)
    print(f"Método 1 (microtime): {'✅ FUNCIONA' if success_1 else '❌ FALLA'}")
    print(f"Método 2 (time): {'✅ FUNCIONA' if success_2 else '❌ FALLA'}")  
    print(f"Básico: {'✅ FUNCIONA' if success_basic else '❌ FALLA'}")
    
    if not any([success_1, success_2, success_basic]):
        print("\n🚨 NINGÚN MÉTODO FUNCIONA")
        print("🔧 VERIFICA:")
        print("   1. API Key y Secret correctos")
        print("   2. Permisos en Splynx")
        print("   3. 'Unsecure access' habilitado")
        print("   4. URL de Splynx accesible")
    else:
        print(f"\n🎉 ¡AL MENOS UN MÉTODO FUNCIONA!")

if __name__ == "__main__":
    main()