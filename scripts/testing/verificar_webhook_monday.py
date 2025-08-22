#!/usr/bin/env python3
"""
Script para verificar que el webhook de Monday está funcionando.
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def verificar_webhook_monday():
    """Verifica que el webhook de Monday está configurado y funcionando"""
    print("🔍 VERIFICANDO WEBHOOK DE MONDAY")
    print("=" * 40)
    
    try:
        # Obtener URL de ngrok
        ngrok_url = os.getenv("NGROK_PUBLIC_URL")
        if not ngrok_url:
            print("❌ NGROK_PUBLIC_URL no configurada en .env")
            return False
        
        webhook_url = f"{ngrok_url}/monday-webhook"
        print(f"📡 Webhook URL: {webhook_url}")
        
        # Probar endpoint de health
        health_url = f"{ngrok_url}/health"
        print(f"🏥 Probando health endpoint: {health_url}")
        
        try:
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                print("✅ Health endpoint responde correctamente")
            else:
                print(f"❌ Health endpoint falló: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
            return False
        
        # Verificar que el servidor está procesando webhooks
        print("\n📋 INSTRUCCIONES PARA PROBAR:")
        print("1. Ve a Monday.com → Tablero 'Grabaciones'")
        print("2. Crea un nuevo elemento:")
        print("   - Nombre: 'PRUEBA SINCRONIZACIÓN 1'")
        print("   - Fecha Grab: 25 de agosto de 2025")
        print("   - Operario: Arnau Admin")
        print("3. Guarda el elemento")
        print("4. Observa los logs del servidor para ver si se procesa")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando webhook: {e}")
        return False

def verificar_elemento_creado():
    """Verifica si se creó el elemento de prueba"""
    print("\n🔍 VERIFICANDO ELEMENTO CREADO")
    print("=" * 40)
    
    try:
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Buscar el elemento de prueba
        items = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name="PRUEBA SINCRONIZACIÓN 1",
            exact_match=True
        )
        
        if items:
            item = items[0]
            item_id = item.id
            print(f"✅ Elemento encontrado: {item_id}")
            
            # Verificar si tiene Google Event ID
            item_details = monday_handler.get_item(item_id)
            if item_details:
                column_values = item_details.get('column_values', [])
                google_event_id = None
                
                for col in column_values:
                    if col.get('id') == config.COLUMN_MAP_REVERSE.get('ID Evento Google'):
                        google_event_id = col.get('text')
                        break
                
                if google_event_id:
                    print(f"✅ Tiene Google Event ID: {google_event_id}")
                    
                    # Verificar si existe en Google Calendar
                    from google_calendar_service import get_calendar_service
                    google_service = get_calendar_service()
                    
                    try:
                        google_event = google_service.events().get(
                            calendarId=config.MASTER_CALENDAR_ID,
                            eventId=google_event_id
                        ).execute()
                        print(f"✅ Evento existe en Google Calendar")
                        print(f"📅 Fecha: {google_event.get('start', {}).get('dateTime', 'Sin fecha')}")
                        return True
                    except Exception as e:
                        print(f"❌ Evento NO existe en Google Calendar: {e}")
                        return False
                else:
                    print("❌ NO tiene Google Event ID - No se sincronizó")
                    return False
            else:
                print("❌ No se pudo obtener detalles del elemento")
                return False
        else:
            print("❌ Elemento no encontrado - ¿Lo creaste en Monday?")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando elemento: {e}")
        return False

def forzar_sincronizacion_manual():
    """Fuerza la sincronización manual de un elemento"""
    print("\n🔄 FORZANDO SINCRONIZACIÓN MANUAL")
    print("=" * 40)
    
    try:
        from google_calendar_service import get_calendar_service
        from sync_logic import sincronizar_item_especifico
        
        google_service = get_calendar_service()
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Buscar el elemento de prueba
        items = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name="PRUEBA SINCRONIZACIÓN 1",
            exact_match=True
        )
        
        if not items:
            print("❌ Elemento no encontrado. Crea primero el elemento en Monday.")
            return False
        
        item_id = items[0].id
        print(f"🔄 Sincronizando elemento: {item_id}")
        
        # Forzar sincronización
        success = sincronizar_item_especifico(
            item_id=item_id,
            google_service=google_service,
            monday_handler=monday_handler
        )
        
        if success:
            print("✅ Sincronización manual exitosa")
            return True
        else:
            print("❌ Error en sincronización manual")
            return False
            
    except Exception as e:
        print(f"❌ Error en sincronización manual: {e}")
        return False

def main():
    """Ejecuta la verificación completa"""
    print("🚀 VERIFICACIÓN DE SINCRONIZACIÓN MONDAY → GOOGLE")
    print("=" * 60)
    
    # Paso 1: Verificar webhook
    webhook_ok = verificar_webhook_monday()
    
    if webhook_ok:
        print("\n📋 SIGUE ESTOS PASOS:")
        print("1. Crea el elemento en Monday.com")
        print("2. Observa los logs del servidor")
        print("3. Ejecuta: python verificar_webhook_monday.py --check")
        print("4. Si falla, ejecuta: python verificar_webhook_monday.py --force")
    
    print("\n💡 COMANDOS DISPONIBLES:")
    print("python verificar_webhook_monday.py --check    # Verificar elemento creado")
    print("python verificar_webhook_monday.py --force    # Forzar sincronización manual")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            verificar_elemento_creado()
        elif sys.argv[1] == "--force":
            forzar_sincronizacion_manual()
        else:
            main()
    else:
        main()

