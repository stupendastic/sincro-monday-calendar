#!/usr/bin/env python3
"""
Script de prueba optimizado para verificar la sincronización Monday ↔ Google Calendar
"""

import os
import time
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service
from sync_logic import sincronizar_item_especifico
import config

# Cargar variables de entorno
load_dotenv()

def test_busqueda_optimizada():
    """Prueba la búsqueda optimizada por Google Event ID"""
    print("🔍 PRUEBA DE BÚSQUEDA OPTIMIZADA")
    print("=" * 40)
    
    try:
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Buscar un elemento que sabemos que existe
        items = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name="PRUEBA SINCRONIZACIÓN AUTOMÁTICA",
            exact_match=True
        )
        
        if not items:
            print("❌ No se encontró el elemento de prueba")
            return False
        
        item = items[0]
        item_id = item.id
        print(f"✅ Elemento encontrado: {item_id}")
        
        # Obtener el Google Event ID
        items_list = monday_handler.get_items(str(config.BOARD_ID_GRABACIONES))
        google_event_id = None
        
        for item_data in items_list:
            if item_data.get('id') == item_id:
                column_values = item_data.get('column_values', [])
                for col in column_values:
                    if col.get('id') == config.COLUMN_MAP_REVERSE.get('ID Evento Google'):
                        google_event_id = col.get('text')
                        break
                break
        
        if not google_event_id:
            print("❌ No se encontró Google Event ID")
            return False
        
        print(f"✅ Google Event ID: {google_event_id}")
        
        # Probar búsqueda optimizada
        from sync_logic import _obtener_item_id_por_google_event_id_optimizado
        
        start_time = time.time()
        found_item_id = _obtener_item_id_por_google_event_id_optimizado(
            google_event_id, monday_handler
        )
        end_time = time.time()
        
        if found_item_id:
            print(f"✅ Búsqueda optimizada exitosa en {end_time - start_time:.2f}s")
            print(f"📊 Item ID encontrado: {found_item_id}")
            return True
        else:
            print("❌ Búsqueda optimizada falló")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de búsqueda: {e}")
        return False

def test_sincronizacion_completa():
    """Prueba la sincronización completa Monday ↔ Google"""
    print("\n🔄 PRUEBA DE SINCRONIZACIÓN COMPLETA")
    print("=" * 40)
    
    try:
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        google_service = get_calendar_service()
        
        # Buscar elemento de prueba
        items = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name="PRUEBA SINCRONIZACIÓN AUTOMÁTICA",
            exact_match=True
        )
        
        if not items:
            print("❌ No se encontró el elemento de prueba")
            return False
        
        item_id = items[0].id
        print(f"✅ Elemento de prueba: {item_id}")
        
        # Probar sincronización
        start_time = time.time()
        success = sincronizar_item_especifico(
            item_id=item_id,
            monday_handler=monday_handler,
            google_service=google_service
        )
        end_time = time.time()
        
        if success:
            print(f"✅ Sincronización exitosa en {end_time - start_time:.2f}s")
            return True
        else:
            print("❌ Sincronización falló")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de sincronización: {e}")
        return False

def test_webhook_processing():
    """Prueba el procesamiento de webhooks"""
    print("\n📡 PRUEBA DE PROCESAMIENTO DE WEBHOOKS")
    print("=" * 40)
    
    try:
        # Simular webhook de Monday
        webhook_data = {
            "event": {
                "type": "update_column_value",
                "pulseId": "9880829856",
                "pulseName": "PRUEBA SINCRONIZACIÓN AUTOMÁTICA",
                "columnId": "fecha56"
            }
        }
        
        print(f"📋 Webhook simulado: {webhook_data['event']['type']}")
        print(f"📊 Item ID: {webhook_data['event']['pulseId']}")
        print(f"📝 Nombre: {webhook_data['event']['pulseName']}")
        
        # Verificar que el servidor está funcionando
        import requests
        response = requests.get("http://localhost:6754/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Servidor saludable: {health_data['status']}")
            print(f"📊 Cola de sincronización: {health_data['queue_size']}")
            return True
        else:
            print(f"❌ Servidor no responde: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de webhook: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 PRUEBA DE SINCRONIZACIÓN OPTIMIZADA")
    print("=" * 50)
    
    # Verificar que el servidor está corriendo
    print("🔍 Verificando servidor...")
    if not test_webhook_processing():
        print("❌ El servidor no está funcionando. Ejecuta 'python3 app.py' primero.")
        return
    
    # Probar búsqueda optimizada
    print("\n" + "="*50)
    if test_busqueda_optimizada():
        print("✅ Búsqueda optimizada: FUNCIONA")
    else:
        print("❌ Búsqueda optimizada: FALLA")
    
    # Probar sincronización completa
    print("\n" + "="*50)
    if test_sincronizacion_completa():
        print("✅ Sincronización completa: FUNCIONA")
    else:
        print("❌ Sincronización completa: FALLA")
    
    print("\n" + "="*50)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 50)
    print("💡 Para probar la sincronización automática:")
    print("1. Crea un elemento en Monday.com")
    print("2. Observa los logs del servidor")
    print("3. Verifica que se crea en Google Calendar")
    print("4. Cambia la fecha en Monday.com")
    print("5. Verifica que se actualiza en Google Calendar")

if __name__ == "__main__":
    main()

