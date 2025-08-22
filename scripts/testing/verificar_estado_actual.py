#!/usr/bin/env python3
"""
Script para verificar el estado actual de Monday.com y Google Calendar
"""
import os
import sys
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from google_calendar_service import GoogleCalendarService
from config import BOARD_ID_GRABACIONES, MASTER_CALENDAR_ID, COL_FECHA_GRAB

def verificar_estado_actual():
    """Verifica el estado actual de Monday.com y Google Calendar"""
    
    print("🔍 VERIFICANDO ESTADO ACTUAL")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Inicializar servicios
    monday_handler = MondayAPIHandler()
    google_service = GoogleCalendarService()
    
    # Buscar el item en Monday.com
    print("📋 Buscando item 'PRUEBA SINCRONIZACIÓN' en Monday.com...")
    
    try:
        # Buscar por nombre
        items = monday_handler.get_items(
            board_id=BOARD_ID_GRABACIONES,
            query_params={"column_values": [{"column_id": "name", "column_values": ["PRUEBA SINCRONIZACIÓN"]}]}
        )
        
        if not items:
            print("❌ No se encontró el item 'PRUEBA SINCRONIZACIÓN' en Monday.com")
            return
        
        item = items[0]
        item_id = item['id']
        item_name = item['name']
        
        print(f"✅ Item encontrado: {item_name} (ID: {item_id})")
        
        # Obtener fecha de Monday.com
        fecha_monday = None
        google_event_id = None
        
        for column in item.get('column_values', []):
            if column.get('id') == COL_FECHA_GRAB:
                fecha_monday = column.get('text', 'No fecha')
            elif column.get('id') == 'text_mktfdhm3':  # Google Event ID
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
        events = google_service.service.events().list(
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
    else:
        print("❌ Hay desincronización")
        print("💡 El sistema debería sincronizar automáticamente")

def main():
    """Función principal"""
    print("🔍 VERIFICADOR DE ESTADO ACTUAL")
    print("=" * 60)
    
    try:
        verificar_estado_actual()
    except KeyboardInterrupt:
        print("\n👋 Verificación cancelada")
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")

if __name__ == "__main__":
    main()
