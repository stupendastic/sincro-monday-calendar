#!/usr/bin/env python3
"""
Script para verificar la sincronización Google → Monday.
"""

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service
import config

def test_google_to_monday_sync():
    """Prueba la sincronización Google → Monday."""
    
    print("🧪 Probando sincronización Google → Monday...")
    
    try:
        # 1. Obtener servicios
        monday_api_key = os.getenv('MONDAY_API_KEY')
        if not monday_api_key:
            print("❌ MONDAY_API_KEY no configurado")
            return False
        
        monday_handler = MondayAPIHandler(api_token=monday_api_key)
        google_service = get_calendar_service()
        
        if not google_service:
            print("❌ Servicio de Google Calendar no disponible")
            return False
        
        # 2. Buscar el evento en Google Calendar
        print("🔍 Buscando evento en Google Calendar...")
        
        # Buscar eventos con el título específico
        events_result = google_service.events().list(
            calendarId=config.MASTER_CALENDAR_ID,
            q="Prueba Arnau Calendar Sync 1",
            maxResults=10
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("❌ No se encontró el evento en Google Calendar")
            return False
        
        event = events[0]  # Tomar el primer evento encontrado
        event_id = event.get('id')
        event_summary = event.get('summary', 'Sin título')
        
        print(f"✅ Evento encontrado en Google Calendar:")
        print(f"   ID: {event_id}")
        print(f"   Título: {event_summary}")
        print(f"   Fecha: {event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'N/A'))}")
        
        # 3. Buscar el item correspondiente en Monday
        print("\n🔍 Buscando item correspondiente en Monday...")
        
        # Buscar por Google Event ID
        item_id = monday_handler.get_item_id_by_google_event_id(
            board_id=str(config.BOARD_ID_GRABACIONES),
            google_event_column_id=config.COL_GOOGLE_EVENT_ID,
            google_event_id=event_id
        )
        
        if item_id:
            print(f"✅ Item encontrado en Monday:")
            print(f"   Item ID: {item_id}")
            
            # Obtener detalles del item
            item_data = monday_handler.get_item_by_id(
                board_id=str(config.BOARD_ID_GRABACIONES),
                item_id=item_id,
                column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name"]
            )
            
            if item_data:
                print(f"   Nombre: {item_data.get('name', 'N/A')}")
                
                # Mostrar column values
                column_values = item_data.get('column_values', [])
                for col in column_values:
                    col_id = col.get('id', '')
                    col_text = col.get('text', '')
                    if col_id == config.COL_FECHA:
                        print(f"   Fecha en Monday: {col_text}")
                    elif col_id == config.COL_GOOGLE_EVENT_ID:
                        print(f"   Google Event ID: {col_text}")
            
            return True
        else:
            print("❌ No se encontró el item correspondiente en Monday")
            print("   Esto puede indicar que:")
            print("   1. El evento no tiene el Google Event ID guardado en Monday")
            print("   2. El ID no coincide")
            print("   3. Hay un problema en la búsqueda")
            return False
            
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_google_calendar_access():
    """Prueba el acceso a Google Calendar."""
    print("🧪 Probando acceso a Google Calendar...")
    
    try:
        google_service = get_calendar_service()
        
        if not google_service:
            print("❌ Servicio de Google Calendar no disponible")
            return False
        
        # Probar acceso al calendario maestro
        calendar = google_service.calendars().get(calendarId=config.MASTER_CALENDAR_ID).execute()
        print(f"✅ Calendario maestro accesible: {calendar.get('summary', 'N/A')}")
        
        # Probar listar eventos
        events_result = google_service.events().list(
            calendarId=config.MASTER_CALENDAR_ID,
            maxResults=5
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ Se pueden listar eventos: {len(events)} eventos encontrados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accediendo a Google Calendar: {e}")
        return False

def main():
    """Función principal."""
    print("🚀 Iniciando pruebas de sincronización Google → Monday...\n")
    
    # Verificar configuración
    if not hasattr(config, 'BOARD_ID_GRABACIONES'):
        print("❌ BOARD_ID_GRABACIONES no configurado")
        return
    
    if not hasattr(config, 'MASTER_CALENDAR_ID'):
        print("❌ MASTER_CALENDAR_ID no configurado")
        return
    
    if not hasattr(config, 'COL_GOOGLE_EVENT_ID'):
        print("❌ COL_GOOGLE_EVENT_ID no configurado")
        return
    
    print(f"✅ Configuración verificada:")
    print(f"   - Board ID: {config.BOARD_ID_GRABACIONES}")
    print(f"   - Calendar ID: {config.MASTER_CALENDAR_ID}")
    print(f"   - Google Event ID Column: {config.COL_GOOGLE_EVENT_ID}\n")
    
    # Ejecutar pruebas
    google_access = test_google_calendar_access()
    
    if google_access:
        sync_test = test_google_to_monday_sync()
        
        print("\n" + "="*50)
        print("📊 RESUMEN DE PRUEBAS")
        print("="*50)
        
        if sync_test:
            print("✅ Sincronización Google → Monday: FUNCIONANDO")
            print("\n🎯 Para probar:")
            print("   1. Cambia la fecha del evento en Google Calendar")
            print("   2. Observa los logs del servidor")
            print("   3. Verifica que la fecha se actualiza en Monday")
        else:
            print("❌ Sincronización Google → Monday: NO FUNCIONA")
            print("\n🔧 Posibles problemas:")
            print("   1. El evento no tiene Google Event ID guardado en Monday")
            print("   2. Los IDs no coinciden")
            print("   3. Problemas de configuración")
    else:
        print("❌ No se puede acceder a Google Calendar")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
