#!/usr/bin/env python3
"""
Script para forzar la sincronización manual
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service
from config import BOARD_ID_GRABACIONES, MASTER_CALENDAR_ID
from sync_logic import sincronizar_item_via_webhook

def forzar_sincronizacion_manual():
    """Fuerza la sincronización manual del item"""
    
    print("🔄 FORZANDO SINCRONIZACIÓN MANUAL")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Inicializar servicios
    monday_token = os.getenv('MONDAY_API_KEY')
    if not monday_token:
        print("❌ No se encontró MONDAY_API_KEY en las variables de entorno")
        return
    
    monday_handler = MondayAPIHandler(monday_token)
    google_service = get_calendar_service()
    
    if not google_service:
        print("❌ No se pudo conectar a Google Calendar")
        return
    
    # Buscar el item en Monday.com
    print("📋 Buscando item 'PRUEBA SINCRONIZACIÓN' en Monday.com...")
    
    try:
        items = monday_handler.search_items_by_name(BOARD_ID_GRABACIONES, "PRUEBA SINCRONIZACIÓN")
        
        if not items:
            print("❌ No se encontró el item 'PRUEBA SINCRONIZACIÓN' en Monday.com")
            return
        
        item = items[0]
        item_id = item.id
        item_name = item.name
        
        print(f"✅ Item encontrado: {item_name} (ID: {item_id})")
        
        # Obtener fecha actual
        fecha_monday = "No encontrada"
        for column in item.column_values or []:
            if column.get('id') == 'fecha56':
                fecha_monday = column.get('text', 'No fecha')
                break
        
        print(f"📅 Fecha actual en Monday.com: {fecha_monday}")
        
    except Exception as e:
        print(f"❌ Error obteniendo datos de Monday.com: {e}")
        return
    
    # Forzar sincronización
    print("\n🔄 Forzando sincronización Monday → Google...")
    
    try:
        # Limpiar el Google Event ID para forzar recreación
        print("🧹 Limpiando Google Event ID para forzar recreación...")
        
        # Actualizar el campo de Google Event ID a vacío
        mutation = """
        mutation {
            change_column_value(board_id: 3324095194, item_id: 9881971936, column_id: "text_mktfdhm3", value: "") {
                id
            }
        }
        """
        
        result = monday_handler._make_request(mutation)
        if result and result.get('data', {}).get('change_column_value'):
            print("✅ Google Event ID limpiado")
        else:
            print("⚠️  No se pudo limpiar el Google Event ID")
        
        # Esperar un momento
        import time
        time.sleep(2)
        
        # Forzar sincronización
        print("🔄 Ejecutando sincronización...")
        success = sincronizar_item_via_webhook(
            item_id=item_id,
            monday_handler=monday_handler,
            google_service=google_service,
            change_uuid="manual-sync-" + str(int(time.time()))
        )
        
        if success:
            print("✅ Sincronización forzada completada")
        else:
            print("❌ Error en sincronización forzada")
        
    except Exception as e:
        print(f"❌ Error durante sincronización forzada: {e}")
        return
    
    # Verificar resultado
    print("\n🔍 Verificando resultado...")
    
    try:
        # Buscar el evento en Google Calendar
        events = google_service.events().list(
            calendarId=MASTER_CALENDAR_ID,
            q="PRUEBA SINCRONIZACIÓN",
            maxResults=1
        ).execute()
        
        if events.get('items'):
            event = events['items'][0]
            event_id = event['id']
            event_start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"✅ Evento creado en Google Calendar:")
            print(f"   - ID: {event_id}")
            print(f"   - Fecha: {event_start}")
        else:
            print("❌ No se encontró el evento en Google Calendar")
        
    except Exception as e:
        print(f"❌ Error verificando resultado: {e}")

def main():
    """Función principal"""
    print("🔄 FORZADOR DE SINCRONIZACIÓN MANUAL")
    print("=" * 60)
    
    try:
        forzar_sincronizacion_manual()
    except KeyboardInterrupt:
        print("\n👋 Sincronización cancelada")
    except Exception as e:
        print(f"❌ Error durante la sincronización: {e}")

if __name__ == "__main__":
    main()
