#!/usr/bin/env python3
"""
Script para crear el item en Monday.com correspondiente al evento de Google Calendar
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def crear_item_monday():
    """Crea el item en Monday.com para el evento de Google Calendar"""
    
    print("🎯 CREANDO ITEM EN MONDAY.COM")
    print("=" * 50)
    
    # Obtener servicios
    google_service = get_calendar_service()
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    if not monday_handler:
        print("❌ No se pudo obtener el servicio de Monday")
        return False
    
    # Obtener calendario maestro
    master_calendar = config.MASTER_CALENDAR_ID
    
    try:
        # Buscar el evento de prueba
        print(f"🔍 Buscando evento 'PRUEBA SINCRONIZACIÓN' en calendario maestro...")
        
        # Buscar eventos en el calendario maestro
        events_result = google_service.events().list(
            calendarId=master_calendar,
            timeMin=(datetime.now() - timedelta(days=30)).isoformat() + 'Z',
            timeMax=(datetime.now() + timedelta(days=30)).isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("❌ No se encontró el evento de prueba")
            return False
        
        # Buscar el evento específico
        evento = None
        for event in events:
            if event.get('summary') == 'PRUEBA SINCRONIZACIÓN':
                evento = event
                break
        
        if not evento:
            print("❌ No se encontró el evento 'PRUEBA SINCRONIZACIÓN'")
            return False
        
        event_id = evento['id']
        event_summary = evento.get('summary', 'Sin título')
        
        print(f"✅ Evento encontrado: {event_summary} (ID: {event_id})")
        
        # Extraer información del evento
        start = evento.get('start', {})
        if 'dateTime' in start:
            fecha_str = start['dateTime']
            # Convertir a datetime para formatear
            fecha_dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
            fecha_formateada = fecha_dt.strftime('%Y-%m-%d')
            hora_formateada = fecha_dt.strftime('%H:%M:%S')
        elif 'date' in start:
            fecha_formateada = start['date']
            hora_formateada = None
        else:
            print(f"❌ No se pudo extraer la fecha del evento")
            return False
        
        print(f"📅 Fecha del evento: {fecha_formateada} {hora_formateada if hora_formateada else ''}")
        
        # Crear el item en Monday.com
        print(f"🔄 Creando item en Monday.com...")
        
        # Preparar el valor de la columna de fecha
        if hora_formateada:
            fecha_value = f"{fecha_formateada} {hora_formateada}"
        else:
            fecha_value = fecha_formateada
        
        # Crear el item
        item_data = {
            'board_id': config.BOARD_ID_GRABACIONES,
            'item_name': event_summary,
            'column_values': {
                config.COL_FECHA: fecha_value,
                config.COL_GOOGLE_EVENT_ID: event_id
            }
        }
        
        # Crear el item usando la API de Monday.com directamente
        query = '''
        mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
            create_item (board_id: $boardId, item_name: $itemName, column_values: $columnValues) {
                id
                name
            }
        }
        '''
        
        variables = {
            'boardId': config.BOARD_ID_GRABACIONES,
            'itemName': event_summary,
            'columnValues': json.dumps(item_data['column_values'])
        }
        
        # Hacer la petición usando el método interno del handler
        data = monday_handler._make_request(query, variables)
        
        if data and 'data' in data and 'create_item' in data['data']:
            item_created = data['data']['create_item']
            print(f"✅ Item creado exitosamente en Monday.com")
            print(f"   ID: {item_created['id']}")
            print(f"   Nombre: {item_created['name']}")
            print(f"   Fecha: {fecha_value}")
            print(f"   Google Event ID: {event_id}")
            
            print(f"\n📋 PRÓXIMOS PASOS:")
            print(f"1. Actualiza manualmente el webhook de Monday.com")
            print(f"2. Haz una prueba moviendo el evento en Google Calendar")
            print(f"3. Verifica que Monday.com se actualiza")
            
            success = True
        else:
            print(f"❌ Error creando item en Monday.com")
            if data and 'errors' in data:
                print(f"   Errores: {data['errors']}")
            success = False
        
        if success:
            print(f"✅ Item creado exitosamente en Monday.com")
            print(f"   Nombre: {event_summary}")
            print(f"   Fecha: {fecha_value}")
            print(f"   Google Event ID: {event_id}")
            
            print(f"\n📋 PRÓXIMOS PASOS:")
            print(f"1. Actualiza manualmente el webhook de Monday.com")
            print(f"2. Haz una prueba moviendo el evento en Google Calendar")
            print(f"3. Verifica que Monday.com se actualiza")
            
            return True
        else:
            print(f"❌ Error creando item en Monday.com")
            return False
        
    except Exception as e:
        print(f"❌ Error durante la creación: {e}")
        return False

def main():
    """Función principal"""
    print("🎯 CREADOR DE ITEM EN MONDAY.COM")
    print("=" * 60)
    
    success = crear_item_monday()
    
    if success:
        print("\n🎉 ¡ITEM CREADO!")
        print("Ahora puedes hacer la prueba moviendo el evento en Google Calendar")
    else:
        print("\n❌ ERROR CREANDO ITEM")

if __name__ == "__main__":
    main()
