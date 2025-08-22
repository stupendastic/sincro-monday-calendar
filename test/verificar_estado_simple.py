#!/usr/bin/env python3
"""
Script simple para verificar el estado actual
"""
import os
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service
from config import BOARD_ID_GRABACIONES, MASTER_CALENDAR_ID

def verificar_estado_simple():
    """Verifica el estado actual de forma simple"""
    
    print("🔍 VERIFICANDO ESTADO ACTUAL (SIMPLE)")
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
        # Usar el método que ya funciona
        items = monday_handler.search_items_by_name(BOARD_ID_GRABACIONES, "PRUEBA SINCRONIZACIÓN")
        
        if not items:
            print("❌ No se encontró el item 'PRUEBA SINCRONIZACIÓN' en Monday.com")
            return
        
        item = items[0]
        item_id = item.id
        item_name = item.name
        
        print(f"✅ Item encontrado: {item_name} (ID: {item_id})")
        
        # Obtener fecha y Google Event ID
        fecha_monday = "No encontrada"
        google_event_id = "No encontrado"
        
        for column in item.column_values or []:
            if column.get('id') == 'fecha56':
                fecha_monday = column.get('text', 'No fecha')
            elif column.get('id') == 'text_mktfdhm3':
                google_event_id = column.get('text', 'No ID')
        
        print(f"📅 Fecha en Monday.com: {fecha_monday}")
        print(f"🆔 Google Event ID: {google_event_id}")
        
    except Exception as e:
        print(f"❌ Error obteniendo datos de Monday.com: {e}")
        return
    
    # Buscar el evento en Google Calendar
    print("\n📅 Buscando evento en Google Calendar...")
    
    try:
        # Buscar por nombre
        events = google_service.events().list(
            calendarId=MASTER_CALENDAR_ID,
            q="PRUEBA SINCRONIZACIÓN",
            maxResults=1
        ).execute()
        
        if not events.get('items'):
            print("❌ No se encontró el evento 'PRUEBA SINCRONIZACIÓN' en Google Calendar")
            return
        
        event = events['items'][0]
        event_id = event['id']
        event_name = event['summary']
        event_start = event['start'].get('dateTime', event['start'].get('date'))
        
        print(f"✅ Evento encontrado: {event_name} (ID: {event_id})")
        print(f"📅 Fecha en Google Calendar: {event_start}")
        
    except Exception as e:
        print(f"❌ Error obteniendo datos de Google Calendar: {e}")
        return
    
    # Comparar fechas
    print("\n🔄 COMPARACIÓN DE FECHAS")
    print("=" * 30)
    print(f"Monday.com: {fecha_monday}")
    print(f"Google Calendar: {event_start}")
    
    if fecha_monday == event_start:
        print("✅ Las fechas coinciden - ya están sincronizados")
    else:
        print("❌ Las fechas NO coinciden - necesitan sincronización")
    
    # Verificar IDs
    print("\n🆔 COMPARACIÓN DE IDs")
    print("=" * 25)
    print(f"Monday.com Google Event ID: {google_event_id}")
    print(f"Google Calendar Event ID: {event_id}")
    
    if google_event_id == event_id:
        print("✅ Los IDs coinciden")
    else:
        print("❌ Los IDs NO coinciden")
    
    print("\n" + "=" * 50)
    print("🎯 RECOMENDACIONES:")
    print("=" * 50)
    
    if fecha_monday == event_start and google_event_id == event_id:
        print("✅ Todo está sincronizado correctamente")
        print("💡 Para probar, cambia la fecha en Monday.com a una diferente")
        print("💡 Por ejemplo: 2025-08-30 20:00:00")
    else:
        print("❌ Hay desincronización")
        print("💡 El sistema debería sincronizar automáticamente")

def main():
    """Función principal"""
    print("🔍 VERIFICADOR DE ESTADO ACTUAL (SIMPLE)")
    print("=" * 60)
    
    try:
        verificar_estado_simple()
    except KeyboardInterrupt:
        print("\n👋 Verificación cancelada")
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")

if __name__ == "__main__":
    main()
