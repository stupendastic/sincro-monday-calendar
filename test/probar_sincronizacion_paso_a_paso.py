#!/usr/bin/env python3
"""
Script para probar la sincronización paso a paso
"""
import os
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service, create_google_event
from config import BOARD_ID_GRABACIONES, MASTER_CALENDAR_ID, UNASSIGNED_CALENDAR_ID

def probar_sincronizacion_paso_a_paso():
    """Prueba la sincronización paso a paso"""
    
    print("🧪 PROBANDO SINCRONIZACIÓN PASO A PASO")
    print("=" * 60)
    
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
    
    # PASO 1: Obtener datos del item de Monday.com
    print("\n📋 PASO 1: Obtener datos del item de Monday.com")
    print("-" * 50)
    
    try:
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
    
    # PASO 2: Crear evento en Google Calendar
    print("\n📅 PASO 2: Crear evento en Google Calendar")
    print("-" * 50)
    
    try:
        # Parsear la fecha de Monday.com
        from datetime import datetime
        
        if len(fecha_monday.split(':')) == 2:
            fecha_dt = datetime.strptime(fecha_monday, '%Y-%m-%d %H:%M')
        else:
            fecha_dt = datetime.strptime(fecha_monday, '%Y-%m-%d %H:%M:%S')
        
        # Crear evento en el calendario maestro
        event_body = {
            'summary': item_name,
            'description': f'Evento sincronizado desde Monday.com (ID: {item_id})',
            'start': {
                'dateTime': fecha_dt.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
            'end': {
                'dateTime': (fecha_dt.replace(hour=fecha_dt.hour + 1)).isoformat(),
                'timeZone': 'Europe/Madrid',
            },
            'extendedProperties': {
                'private': {
                    'monday_item_id': str(item_id),
                    'sync_source': 'monday'
                }
            }
        }
        
        print(f"📅 Creando evento en calendario MAESTRO...")
        print(f"   - Nombre: {item_name}")
        print(f"   - Fecha: {fecha_dt.isoformat()}")
        print(f"   - Calendario: {MASTER_CALENDAR_ID}")
        
        # Crear el evento
        new_event_id = create_google_event(google_service, MASTER_CALENDAR_ID, event_body)
        
        if new_event_id:
            print(f"✅ Evento creado exitosamente")
            print(f"   - ID: {new_event_id}")
            
            # PASO 3: Actualizar Monday.com con el nuevo ID
            print("\n📋 PASO 3: Actualizar Monday.com con el nuevo ID")
            print("-" * 50)
            
            mutation = f"""
            mutation {{
                change_column_value(board_id: 3324095194, item_id: {item_id}, column_id: "text_mktfdhm3", value: "{new_event_id}") {{
                    id
                }}
            }}
            """
            
            result = monday_handler._make_request(mutation)
            if result and result.get('data', {}).get('change_column_value'):
                print("✅ Google Event ID actualizado en Monday.com")
            else:
                print("❌ Error actualizando Google Event ID en Monday.com")
                
        else:
            print("❌ Error creando evento en Google Calendar")
        
    except Exception as e:
        print(f"❌ Error durante la creación del evento: {e}")
        return
    
    # PASO 4: Verificar resultado
    print("\n🔍 PASO 4: Verificar resultado")
    print("-" * 50)
    
    try:
        # Buscar el evento en Google Calendar
        events = google_service.events().list(
            calendarId=MASTER_CALENDAR_ID,
            q=item_name,
            maxResults=1
        ).execute()
        
        if events.get('items'):
            event = events['items'][0]
            event_id = event['id']
            event_start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"✅ Evento encontrado en Google Calendar:")
            print(f"   - ID: {event_id}")
            print(f"   - Fecha: {event_start}")
            print(f"   - Calendario: MASTER")
        else:
            print("❌ No se encontró el evento en Google Calendar")
        
    except Exception as e:
        print(f"❌ Error verificando resultado: {e}")

def main():
    """Función principal"""
    print("🧪 PROBADOR DE SINCRONIZACIÓN PASO A PASO")
    print("=" * 70)
    
    try:
        probar_sincronizacion_paso_a_paso()
    except KeyboardInterrupt:
        print("\n👋 Prueba cancelada")
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")

if __name__ == "__main__":
    main()
