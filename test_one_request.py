"""
Script ultra simple: SOLO UNA REQUEST para diagnosticar el problema de autenticación
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"

def single_test():
    """Una sola request de prueba"""
    print("🔍 TEST DE UNA SOLA REQUEST")
    print("=" * 50)
    
    try:
        # UNA SOLA REQUEST
        url = f"{BASE_URL}/banco-estado/test-splynx"
        print(f"📡 Haciendo request a: {url}")
        
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        print(f"⏱️  Tiempo: {response.elapsed.total_seconds():.2f}s")
        
        result = response.json()
        print("📋 Respuesta:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Diagnóstico
        if result.get('connection', {}).get('success'):
            print("\n✅ ÉXITO: Conexión con Splynx OK")
        else:
            print("\n❌ PROBLEMA DE AUTENTICACIÓN DETECTADO")
            print("🔧 SOLUCIONES:")
            print("   1. Verificar API_KEY en .env")
            print("   2. Verificar API_SECRET en .env") 
            print("   3. En Splynx: Administration > Main > API Keys")
            print("   4. Confirmar permisos del API key")
            print("   5. Habilitar 'Unsecure access' si es necesario")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al servidor")
        print("   ➤ Ejecuta: python main.py")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    single_test()