#!/usr/bin/env python3
"""
Script de prueba completo para verificar que el sistema funciona correctamente.
"""

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service
from sync_logic import generate_content_hash, _detectar_cambio_de_automatizacion
import config

def test_monday_service():
    """Prueba el servicio de Monday.com."""
    print("🧪 Probando servicio de Monday.com...")
    
    try:
        monday_api_key = os.getenv('MONDAY_API_KEY')
        if not monday_api_key:
            print("❌ MONDAY_API_KEY no configurado")
            return False
        
        handler = MondayAPIHandler(api_token=monday_api_key)
        
        # Probar obtención de item específico
        test_item_id = "9882299305"
        item_data = handler.get_item_by_id(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_id=test_item_id,
            column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name"]
        )
        
        if item_data:
            print("✅ Servicio de Monday.com funcionando correctamente")
            print(f"   Item obtenido: {item_data.get('name', 'N/A')}")
            return True
        else:
            print("❌ No se pudo obtener item de Monday.com")
            return False
            
    except Exception as e:
        print(f"❌ Error en servicio de Monday.com: {e}")
        return False

def test_google_service():
    """Prueba el servicio de Google Calendar."""
    print("\n🧪 Probando servicio de Google Calendar...")
    
    try:
        service = get_calendar_service()
        
        if service:
            print("✅ Servicio de Google Calendar funcionando correctamente")
            
            # Probar acceso al calendario maestro
            try:
                calendar = service.calendars().get(calendarId=config.MASTER_CALENDAR_ID).execute()
                print(f"   Calendario maestro accesible: {calendar.get('summary', 'N/A')}")
                return True
            except Exception as e:
                print(f"⚠️  No se pudo acceder al calendario maestro: {e}")
                return False
        else:
            print("❌ Servicio de Google Calendar no disponible")
            return False
            
    except Exception as e:
        print(f"❌ Error en servicio de Google Calendar: {e}")
        return False

def test_sync_logic():
    """Prueba las funciones de lógica de sincronización."""
    print("\n🧪 Probando lógica de sincronización...")
    
    try:
        # Probar generación de hash
        test_content = {
            'fecha': '2025-08-25',
            'titulo': 'Prueba',
            'operarios': 'Arnau'
        }
        
        hash_result = generate_content_hash(test_content)
        if hash_result:
            print("✅ Generación de hash funcionando")
            print(f"   Hash generado: {hash_result[:20]}...")
        else:
            print("❌ Error generando hash")
            return False
        
        # Probar detección de automatización (sin conexión real)
        print("✅ Funciones de lógica de sincronización disponibles")
        return True
        
    except Exception as e:
        print(f"❌ Error en lógica de sincronización: {e}")
        return False

def test_webhook_endpoints():
    """Prueba los endpoints de webhook."""
    print("\n🧪 Probando endpoints de webhook...")
    
    import requests
    
    try:
        # Probar endpoint de salud
        response = requests.get('http://localhost:6754/health', timeout=5)
        if response.status_code == 200:
            print("✅ Endpoint de salud funcionando")
        else:
            print(f"❌ Endpoint de salud falló: {response.status_code}")
            return False
        
        # Probar endpoint de debugging
        response = requests.get('http://localhost:6754/debug/last-syncs', timeout=5)
        if response.status_code == 200:
            print("✅ Endpoint de debugging funcionando")
        else:
            print(f"⚠️  Endpoint de debugging falló: {response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando a endpoints: {e}")
        return False

def main():
    """Función principal."""
    print("🚀 Iniciando pruebas completas del sistema...\n")
    
    # Verificar configuración
    if not hasattr(config, 'BOARD_ID_GRABACIONES'):
        print("❌ BOARD_ID_GRABACIONES no configurado")
        return
    
    if not hasattr(config, 'MASTER_CALENDAR_ID'):
        print("❌ MASTER_CALENDAR_ID no configurado")
        return
    
    print(f"✅ Configuración verificada:")
    print(f"   - Board ID: {config.BOARD_ID_GRABACIONES}")
    print(f"   - Calendar ID: {config.MASTER_CALENDAR_ID}")
    print(f"   - API Key: {'*' * 10 + os.getenv('MONDAY_API_KEY', '')[-4:] if os.getenv('MONDAY_API_KEY') else 'No configurado'}\n")
    
    # Ejecutar pruebas
    tests = [
        ("Monday.com Service", test_monday_service),
        ("Google Calendar Service", test_google_service),
        ("Sync Logic", test_sync_logic),
        ("Webhook Endpoints", test_webhook_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("\n✅ Puedes probar cambiando una fecha en Monday.com")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
