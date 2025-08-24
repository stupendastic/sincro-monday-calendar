#!/usr/bin/env python3
"""
Script de prueba para verificar la sincronización real con un evento existente.
"""

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def test_sincronizacion_evento_existente():
    """Prueba la sincronización con un evento que ya existe en Monday"""
    print("🧪 PRUEBA: SINCRONIZACIÓN CON EVENTO EXISTENTE")
    print("=" * 50)
    
    try:
        google_service = get_calendar_service()
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Buscar un evento que ya existe en Monday
        event_name = "ARNAU PRUEBAS CALENDARIO 1"
        print(f"🔍 Buscando evento existente: '{event_name}'")
        
        items_by_name = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name=event_name,
            exact_match=True
        )
        
        if not items_by_name:
            print("❌ No se encontró el evento de prueba en Monday")
            return False
        
        item_id = items_by_name[0].id
        print(f"✅ Evento encontrado en Monday: {item_id}")
        
        # Buscar el evento correspondiente en Google Calendar
        print("🔍 Buscando evento en Google Calendar...")
        
        # Buscar por nombre en el calendario maestro
        events_result = google_service.events().list(
            calendarId=config.MASTER_CALENDAR_ID,
            q=event_name,
            maxResults=10
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("❌ No se encontró el evento en Google Calendar")
            return False
        
        google_event = events[0]
        google_event_id = google_event.get('id')
        print(f"✅ Evento encontrado en Google: {google_event_id}")
        
        # Mostrar fecha actual
        start = google_event.get('start', {})
        if 'dateTime' in start:
            current_date = start['dateTime']
            print(f"📅 Fecha actual: {current_date}")
        else:
            current_date = start.get('date', 'Sin fecha')
            print(f"📅 Fecha actual: {current_date}")
        
        # Crear una nueva fecha para el test
        new_date = datetime.now() + timedelta(days=2)
        new_date_str = new_date.isoformat()
        
        print(f"📅 Nueva fecha de prueba: {new_date_str}")
        
        # Actualizar el evento en Google Calendar
        print("🔄 Actualizando evento en Google Calendar...")
        
        updated_event = google_event.copy()
        updated_event['start'] = {
            'dateTime': new_date_str,
            'timeZone': 'Europe/Madrid'
        }
        updated_event['end'] = {
            'dateTime': (new_date + timedelta(hours=2)).isoformat(),
            'timeZone': 'Europe/Madrid'
        }
        
        # Actualizar en Google
        google_service.events().update(
            calendarId=config.MASTER_CALENDAR_ID,
            eventId=google_event_id,
            body=updated_event
        ).execute()
        
        print("✅ Evento actualizado en Google Calendar")
        
        # Probar sincronización
        print("🔄 Probando sincronización Google → Monday...")
        
        from sync_logic import sincronizar_desde_google_calendar
        
        start_time = time.time()
        success = sincronizar_desde_google_calendar(
            evento_cambiado=updated_event,
            google_service=google_service,
            monday_handler=monday_handler
        )
        tiempo_sincronizacion = time.time() - start_time
        
        if success:
            print(f"✅ Sincronización exitosa en {tiempo_sincronizacion:.3f} segundos")
            
            # Verificar que Monday se actualizó
            print("🔍 Verificando actualización en Monday...")
            
            # Obtener el item actualizado
            item_updated = monday_handler.get_item(item_id)
            if item_updated:
                column_values = item_updated.get('column_values', [])
                for col in column_values:
                    if col.get('id') == config.COL_FECHA:
                        fecha_monday = col.get('text', 'Sin fecha')
                        print(f"📅 Fecha en Monday después de sincronización: {fecha_monday}")
                        break
            else:
                print("⚠️ No se pudo verificar la fecha en Monday")
        else:
            print(f"❌ Error en sincronización (tiempo: {tiempo_sincronizacion:.3f}s)")
        
        # Restaurar fecha original
        print("🔄 Restaurando fecha original...")
        google_service.events().update(
            calendarId=config.MASTER_CALENDAR_ID,
            eventId=google_event_id,
            body=google_event
        ).execute()
        
        print("✅ Fecha original restaurada")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_sincronizacion_calendario_personal():
    """Prueba la sincronización desde un calendario personal"""
    print("\n🧪 PRUEBA: SINCRONIZACIÓN DESDE CALENDARIO PERSONAL")
    print("=" * 50)
    
    try:
        google_service = get_calendar_service()
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Buscar el calendario personal de Arnau Admin
        calendar_personal = None
        for perfil in config.FILMMAKER_PROFILES:
            if perfil.get('monday_name') == 'Arnau Admin':
                calendar_personal = perfil.get('calendar_id')
                break
        
        if not calendar_personal:
            print("❌ No se encontró el calendario personal de Arnau Admin")
            return False
        
        print(f"📅 Calendario personal: {calendar_personal}")
        
        # Buscar eventos en el calendario personal
        events_result = google_service.events().list(
            calendarId=calendar_personal,
            maxResults=5
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("❌ No se encontraron eventos en el calendario personal")
            return False
        
        # Buscar un evento que tenga master_event_id
        test_event = None
        for event in events:
            extended_props = event.get('extendedProperties', {})
            private_props = extended_props.get('private', {})
            if private_props.get('master_event_id'):
                test_event = event
                break
        
        if not test_event:
            print("❌ No se encontró un evento con master_event_id en el calendario personal")
            return False
        
        print(f"✅ Evento de prueba encontrado: {test_event.get('summary')}")
        
        # Probar sincronización desde calendario personal
        from sync_logic import sincronizar_desde_calendario_personal
        
        start_time = time.time()
        success = sincronizar_desde_calendario_personal(
            evento_cambiado=test_event,
            calendar_id_origen=calendar_personal,
            google_service=google_service,
            monday_handler=monday_handler
        )
        tiempo_sincronizacion = time.time() - start_time
        
        if success:
            print(f"✅ Sincronización desde calendario personal exitosa en {tiempo_sincronizacion:.3f} segundos")
        else:
            print(f"❌ Error en sincronización desde calendario personal (tiempo: {tiempo_sincronizacion:.3f}s)")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en prueba de calendario personal: {e}")
        return False

def main():
    """Ejecuta las pruebas de sincronización real"""
    print("🚀 INICIANDO PRUEBAS DE SINCRONIZACIÓN REAL")
    print("=" * 60)
    
    resultados = {}
    
    # Prueba 1: Sincronización con evento existente
    try:
        sync_existente = test_sincronizacion_evento_existente()
        resultados['sincronizacion_existente'] = sync_existente
    except Exception as e:
        print(f"❌ Error en prueba de evento existente: {e}")
        resultados['sincronizacion_existente'] = False
    
    # Prueba 2: Sincronización desde calendario personal
    try:
        sync_personal = test_sincronizacion_calendario_personal()
        resultados['sincronizacion_personal'] = sync_personal
    except Exception as e:
        print(f"❌ Error en prueba de calendario personal: {e}")
        resultados['sincronizacion_personal'] = False
    
    # Resumen
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 30)
    
    for prueba, resultado in resultados.items():
        status = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{prueba}: {status}")
    
    exitos = sum(resultados.values())
    total = len(resultados)
    
    print(f"\n🎯 RESULTADO FINAL: {exitos}/{total} pruebas exitosas")
    
    if exitos == total:
        print("🎉 ¡Sincronización real funciona correctamente!")
    else:
        print("⚠️  Hay problemas que necesitan ser solucionados")

if __name__ == "__main__":
    main()

