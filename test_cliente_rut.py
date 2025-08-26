"""
Script simple para consultar un cliente específico por RUT
Test directo del endpoint consultar-cliente
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"
RUT_CLIENTE = "27240598-0"

def test_consultar_cliente_por_rut():
    """Consultar cliente específico por RUT - UNA SOLA REQUEST"""
    print("🔍 CONSULTAR CLIENTE POR RUT")
    print("=" * 50)
    print(f"🆔 RUT: {RUT_CLIENTE}")
    print()
    
    try:
        # Preparar request
        url = f"{BASE_URL}/banco-estado/consultar-cliente"
        payload = {"rut_cliente": RUT_CLIENTE}
        headers = {"Content-Type": "application/json"}
        
        print(f"📡 Endpoint: {url}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        print("⏳ Enviando request...")
        print()
        
        # UNA SOLA REQUEST
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️  Tiempo de respuesta: {response.elapsed.total_seconds():.2f}s")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("📄 RESPUESTA COMPLETA:")
            print("-" * 40)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("-" * 40)
            
            # Análisis de la respuesta
            if result.get('success'):
                print("\n✅ CLIENTE ENCONTRADO:")
                cliente = result.get('data', {})
                
                print(f"   🆔 ID Cliente: {cliente.get('id_cliente', 'N/A')}")
                print(f"   👤 Nombre: {cliente.get('nombre', 'N/A')}")
                print(f"   📱 RUT: {cliente.get('rut_cliente', 'N/A')}")
                print(f"   📊 Estado: {cliente.get('estado', 'N/A')}")
                
                # Facturas
                facturas = cliente.get('facturas', [])
                print(f"   💰 Facturas: {len(facturas)} encontradas")
                
                if facturas:
                    print("\n📋 DETALLE DE FACTURAS:")
                    for i, factura in enumerate(facturas, 1):
                        print(f"   {i}. ID: {factura.get('id', 'N/A')}")
                        print(f"      💵 Monto: ${factura.get('monto', 'N/A')}")
                        print(f"      📅 Vencimiento: {factura.get('vencimiento', 'N/A')}")
                        print(f"      🔍 Estado: {factura.get('estado', 'N/A')}")
                        if factura.get('numero'):
                            print(f"      📄 Número: {factura.get('numero', 'N/A')}")
                        print()
                        
                        # Solo mostrar primeras 3 facturas
                        if i >= 3:
                            total = len(facturas)
                            if total > 3:
                                print(f"   ... y {total - 3} facturas más")
                            break
                else:
                    print("   (Sin facturas pendientes)")
                    
            else:
                print("\n❌ CLIENTE NO ENCONTRADO O ERROR:")
                error = result.get('error', {})
                if isinstance(error, dict):
                    print(f"   🚨 Código: {error.get('codigo_error', 'N/A')}")
                    print(f"   📝 Descripción: {error.get('descripcion_error', 'N/A')}")
                else:
                    print(f"   📝 Error: {error}")
                    
                print("\n🔧 POSIBLES CAUSAS:")
                print("   1. Cliente no existe en Splynx")
                print("   2. RUT está en diferente campo (no en 'login')")
                print("   3. Error de autenticación con Splynx")
                print("   4. Cliente existe pero sin permisos de acceso")
                
        else:
            print(f"\n❌ ERROR HTTP {response.status_code}:")
            try:
                error_json = response.json()
                print(json.dumps(error_json, indent=2, ensure_ascii=False))
            except:
                print(response.text)
                
    except requests.exceptions.Timeout:
        print("⏰ ERROR: Timeout - El servidor tardó más de 15 segundos")
    except requests.exceptions.ConnectionError:
        print("🔌 ERROR: No se pudo conectar al servidor")
        print("   ➤ Asegúrate de que esté ejecutándose: python main.py")
    except Exception as e:
        print(f"💥 ERROR INESPERADO: {e}")

def main():
    """Ejecutar consulta de cliente"""
    print("🏦 BANCOESTADO API - CONSULTA POR RUT")
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"📅 Fecha: {json.dumps(requests.get('http://worldtimeapi.org/api/timezone/America/Santiago').json()['datetime'][:19], default=str) if True else 'N/A'}")
    print()
    
    # Verificar servidor
    try:
        health = requests.get(f"{BASE_URL}/banco-estado/health", timeout=5)
        if health.status_code == 200:
            print("✅ Servidor API activo")
        else:
            print(f"⚠️  Servidor responde con código {health.status_code}")
    except:
        print("❌ Servidor no disponible - ejecuta: python main.py")
    
    print()
    
    # Ejecutar test
    test_consultar_cliente_por_rut()
    
    print("\n" + "=" * 50)
    print("🏁 CONSULTA COMPLETADA")
    print("=" * 50)
    
    print("\n📖 NOTAS:")
    print("• Este RUT es de prueba según tu configuración")
    print("• Si no se encuentra, verifica que exista en Splynx")
    print("• El campo RUT puede estar en 'login', 'name' o campos adicionales")
    print("• Usa /debug-splynx/27240598-0 para ver estructura de datos")

if __name__ == "__main__":
    main()