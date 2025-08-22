#!/usr/bin/env python3
"""
Script para verificar que todo está preparado para las pruebas manuales
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_servidor():
    """Verifica que el servidor Flask está funcionando"""
    print("🔍 Verificando servidor Flask...")
    try:
        response = requests.get("http://localhost:6754/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor Flask funcionando en puerto 6754")
            return True
        else:
            print(f"❌ Servidor responde con código {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        print("   Ejecuta: python3 app.py")
        return False

def verificar_ngrok():
    """Verifica que ngrok está funcionando"""
    print("🔍 Verificando ngrok...")
    try:
        # Intentar obtener la URL pública de ngrok
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json().get('tunnels', [])
            for tunnel in tunnels:
                if tunnel.get('config', {}).get('addr') == 'localhost:6754':
                    public_url = tunnel.get('public_url')
                    print(f"✅ ngrok funcionando: {public_url}")
                    return True
        print("❌ ngrok no está configurado para el puerto 6754")
        return False
    except requests.exceptions.RequestException:
        print("❌ ngrok no está funcionando")
        print("   Ejecuta: ngrok http 6754")
        return False

def verificar_credenciales():
    """Verifica que las credenciales están configuradas"""
    print("🔍 Verificando credenciales...")
    
    # Verificar Monday API Key
    monday_key = os.getenv('MONDAY_API_KEY')
    if not monday_key:
        print("❌ MONDAY_API_KEY no encontrada en .env")
        return False
    print("✅ MONDAY_API_KEY configurada")
    
    # Verificar Google Token
    google_token = os.getenv('GOOGLE_TOKEN_JSON')
    if not google_token:
        print("❌ GOOGLE_TOKEN_JSON no encontrado en .env")
        return False
    print("✅ GOOGLE_TOKEN_JSON configurado")
    
    # Verificar ngrok URL
    ngrok_url = os.getenv('NGROK_PUBLIC_URL')
    if not ngrok_url:
        print("❌ NGROK_PUBLIC_URL no encontrada en .env")
        return False
    print("✅ NGROK_PUBLIC_URL configurada")
    
    return True

def verificar_apis():
    """Verifica que las APIs responden correctamente"""
    print("🔍 Verificando APIs...")
    
    try:
        # Verificar Monday API
        from monday_api_handler import MondayAPIHandler
        monday_handler = MondayAPIHandler(api_token=os.getenv('MONDAY_API_KEY'))
        
        # Query simple para verificar conexión
        query = """
        query {
            boards(ids: [3324095194]) {
                id
                name
            }
        }
        """
        
        response = monday_handler._make_request(query)
        if response and 'data' in response:
            board_name = response['data']['boards'][0]['name']
            print(f"✅ Monday API funcionando - Tablero: {board_name}")
        else:
            print("❌ Monday API no responde correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando Monday API: {e}")
        return False
    
    try:
        # Verificar Google Calendar API
        from google_calendar_service import get_calendar_service
        google_service = get_calendar_service()
        
        if google_service:
            # Query simple para verificar conexión
            calendar_list = google_service.calendarList().list().execute()
            print(f"✅ Google Calendar API funcionando - {len(calendar_list.get('items', []))} calendarios")
        else:
            print("❌ Google Calendar API no responde correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando Google Calendar API: {e}")
        return False
    
    return True

def verificar_webhooks():
    """Verifica que los webhooks están configurados"""
    print("🔍 Verificando webhooks...")
    
    ngrok_url = os.getenv('NGROK_PUBLIC_URL')
    if not ngrok_url:
        print("❌ NGROK_PUBLIC_URL no configurada")
        return False
    
    # Verificar que los endpoints responden
    try:
        # Monday webhook
        response = requests.post(f"{ngrok_url}/monday-webhook", 
                               json={"challenge": "test"}, 
                               timeout=5)
        if response.status_code == 200:
            print("✅ Monday webhook respondiendo")
        else:
            print(f"❌ Monday webhook error: {response.status_code}")
            return False
            
        # Google webhook
        response = requests.post(f"{ngrok_url}/google-webhook", 
                               timeout=5)
        if response.status_code == 200:
            print("✅ Google webhook respondiendo")
        else:
            print(f"❌ Google webhook error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error verificando webhooks: {e}")
        return False
    
    return True

def mostrar_instrucciones():
    """Muestra las instrucciones para las pruebas"""
    print("\n" + "="*60)
    print("📋 INSTRUCCIONES PARA PRUEBAS MANUALES")
    print("="*60)
    
    print("\n🎯 PRÓXIMOS PASOS:")
    print("1. Abre Monday.com en una cuenta diferente a 'Arnau Admin'")
    print("2. Ve al tablero 'Grabaciones'")
    print("3. Crea un evento de prueba con nombre único")
    print("4. Observa los logs en esta terminal")
    print("5. Verifica que aparece en Google Calendar")
    
    print("\n🔍 QUÉ OBSERVAR EN LOS LOGS:")
    print("- ✅ Evento maestro creado exitosamente")
    print("- 🔄 Sincronizando copias para filmmakers")
    print("- ✅ Copia creada exitosamente")
    print("- ⚡ Búsqueda SÚPER OPTIMIZADA")
    
    print("\n🚨 SI ALGO FALLA:")
    print("- Verifica que usas cuenta diferente a 'Arnau Admin'")
    print("- Comprueba que ngrok sigue funcionando")
    print("- Revisa que el servidor sigue corriendo")
    
    print("\n📖 PLAN COMPLETO:")
    print("- Lee el archivo PLAN_PRUEBAS_MANUALES.md")
    print("- Sigue las 7 pruebas paso a paso")
    print("- Documenta los resultados")

def main():
    """Función principal de verificación"""
    print("🧪 VERIFICACIÓN DE PREPARACIÓN PARA PRUEBAS MANUALES")
    print("=" * 60)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    verificaciones = []
    
    # Ejecutar todas las verificaciones
    verificaciones.append(("Servidor Flask", verificar_servidor()))
    verificaciones.append(("ngrok", verificar_ngrok()))
    verificaciones.append(("Credenciales", verificar_credenciales()))
    verificaciones.append(("APIs", verificar_apis()))
    verificaciones.append(("Webhooks", verificar_webhooks()))
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE VERIFICACIONES")
    print("="*60)
    
    exitos = 0
    for nombre, resultado in verificaciones:
        estado = "✅ ÉXITO" if resultado else "❌ FALLO"
        print(f"{nombre}: {estado}")
        if resultado:
            exitos += 1
    
    print(f"\n🎯 Total: {exitos}/{len(verificaciones)} verificaciones exitosas")
    
    if exitos == len(verificaciones):
        print("🎉 ¡Todo listo para las pruebas manuales!")
        mostrar_instrucciones()
    else:
        print("⚠️ Hay problemas que resolver antes de las pruebas")
        print("\n🔧 ACCIONES REQUERIDAS:")
        if not verificaciones[0][1]:
            print("- Ejecutar: python3 app.py")
        if not verificaciones[1][1]:
            print("- Ejecutar: ngrok http 6754")
        if not verificaciones[2][1]:
            print("- Configurar archivo .env con credenciales")
        if not verificaciones[3][1]:
            print("- Verificar API keys y permisos")
        if not verificaciones[4][1]:
            print("- Verificar configuración de webhooks")
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
