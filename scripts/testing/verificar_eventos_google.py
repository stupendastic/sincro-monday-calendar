#!/usr/bin/env python3
"""
Script para verificar eventos en Google Calendar y diagnosticar problemas de sincronización.
"""

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def verificar_calendario_maestro():
    """Verifica eventos en el calendario maestro"""
    print("🔍 VERIFICANDO CALENDARIO MAESTRO")
    print("=" * 40)
    
    try:
        google_service = get_calendar_service()
        
        # Buscar eventos en el calendario maestro
        time_min = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
        time_max = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'
        
        events_result = google_service.events().list(
            calendarId=config.MASTER_CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        print(f"📅 Calendario maestro: {config.MASTER_CALENDAR_ID}")
        print(f"📊 Eventos encontrados: {len(events)}")
        
        if not events:
            print("❌ No hay eventos en el calendario maestro")
            return
        
        print("\n📋 LISTA DE EVENTOS:")
        for i, event in enumerate(events, 1):
            start = event.get('start', {})
            summary = event.get('summary', 'Sin título')
            event_id = event.get('id')
            
            if 'dateTime' in start:
                start_time = start['dateTime']
            else:
                start_time = start.get('date', 'Sin fecha')
            
            print(f"{i}. {summary}")
            print(f"   📅 Fecha: {start_time}")
            print(f"   🆔 ID: {event_id}")
            
            # Verificar si tiene extended properties
            extended_props = event.get('extendedProperties', {})
            if extended_props:
                print(f"   📝 Tiene extended properties")
            
            print()
        
    except Exception as e:
        print(f"❌ Error verificando calendario maestro: {e}")

def verificar_calendarios_personales():
    """Verifica eventos en calendarios personales"""
    print("\n🔍 VERIFICANDO CALENDARIOS PERSONALES")
    print("=" * 40)
    
    try:
        google_service = get_calendar_service()
        
        for perfil in config.FILMMAKER_PROFILES:
            filmmaker_name = perfil.get('monday_name', 'Desconocido')
            calendar_id = perfil.get('calendar_id')
            
            if not calendar_id:
                print(f"⏭️  {filmmaker_name}: Sin calendario configurado")
                continue
            
            print(f"\n👤 {filmmaker_name}")
            print(f"📅 Calendario: {calendar_id}")
            
            # Buscar eventos
            time_min = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
            time_max = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'
            
            events_result = google_service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            print(f"📊 Eventos encontrados: {len(events)}")
            
            if events:
                for event in events:
                    summary = event.get('summary', 'Sin título')
                    event_id = event.get('id')
                    
                    # Verificar extended properties
                    extended_props = event.get('extendedProperties', {})
                    private_props = extended_props.get('private', {})
                    master_event_id = private_props.get('master_event_id')
                    
                    if master_event_id:
                        print(f"   ✅ {summary} (ID: {event_id})")
                        print(f"      🔗 Master Event ID: {master_event_id}")
                    else:
                        print(f"   ⚠️  {summary} (ID: {event_id}) - Sin master_event_id")
            else:
                print("   ❌ No hay eventos")
        
    except Exception as e:
        print(f"❌ Error verificando calendarios personales: {e}")

def verificar_sincronizacion_monday():
    """Verifica si hay eventos en Monday que deberían estar en Google"""
    print("\n🔍 VERIFICANDO SINCRONIZACIÓN MONDAY")
    print("=" * 40)
    
    try:
        from monday_api_handler import MondayAPIHandler
        
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Buscar items recientes en Monday
        items = monday_handler.get_items(
            board_id=str(config.BOARD_ID_GRABACIONES),
            limit_per_page=10
        )
        
        print(f"📊 Items encontrados en Monday: {len(items)}")
        
        for item in items:
            item_id = item.get('id')
            name = item.get('name', 'Sin nombre')
            
            # Buscar Google Event ID
            google_event_id = None
            column_values = item.get('column_values', [])
            for col in column_values:
                if col.get('id') == config.COLUMN_MAP_REVERSE.get('ID Evento Google'):
                    google_event_id = col.get('text')
                    break
            
            print(f"\n📋 Item: {name} (ID: {item_id})")
            
            if google_event_id:
                print(f"   ✅ Tiene Google Event ID: {google_event_id}")
                
                # Verificar si existe en Google
                try:
                    google_service = get_calendar_service()
                    google_event = google_service.events().get(
                        calendarId=config.MASTER_CALENDAR_ID,
                        eventId=google_event_id
                    ).execute()
                    print(f"   ✅ Existe en Google Calendar")
                except Exception as e:
                    print(f"   ❌ NO existe en Google Calendar: {e}")
            else:
                print(f"   ⚠️  NO tiene Google Event ID")
        
    except Exception as e:
        print(f"❌ Error verificando Monday: {e}")

def main():
    """Ejecuta todas las verificaciones"""
    print("🚀 DIAGNÓSTICO DE SINCRONIZACIÓN")
    print("=" * 60)
    
    verificar_calendario_maestro()
    verificar_calendarios_personales()
    verificar_sincronizacion_monday()
    
    print("\n📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 30)
    print("✅ Verificación completada")
    print("📋 Revisa los resultados arriba para identificar problemas")

if __name__ == "__main__":
    main()

