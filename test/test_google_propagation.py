#!/usr/bin/env python3
"""
Script para probar la propagación de eventos entre calendarios de Google
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def test_google_propagation():
    """Prueba la propagación de eventos entre calendarios de Google"""
    
    print("🧪 PRUEBA DE PROPAGACIÓN GOOGLE CALENDAR")
    print("=" * 60)
    
    # Obtener el servicio de Google Calendar
    service = get_calendar_service()
    if not service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # Obtener calendarios
    master_calendar = config.MASTER_CALENDAR_ID
    filmmaker_calendar = None
    
    # Buscar el calendario de Arnau Admin
    for profile in config.FILMMAKER_PROFILES:
        if profile["monday_name"] == "Arnau Admin":
            filmmaker_calendar = profile["calendar_id"]
            break
    
    if not filmmaker_calendar:
        print("❌ No se encontró el calendario de Arnau Admin")
        return False
    
    print(f"📅 Calendario Maestro: {master_calendar}")
    print(f"📅 Calendario Personal: {filmmaker_calendar}")
    
    # Crear un evento de prueba en el calendario maestro
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    
    event_body = {
        'summary': 'PRUEBA PROPAGACIÓN GOOGLE',
        'description': 'Evento de prueba para verificar propagación entre calendarios',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Europe/Madrid',
        },
        'extendedProperties': {
            'private': {
                'master_event_id': 'test_propagation_123',
                'monday_item_id': 'test_item_123'
            }
        }
    }
    
    try:
        # Crear evento en calendario maestro
        print(f"\n🔄 Creando evento de prueba en calendario maestro...")
        event = service.events().insert(
            calendarId=master_calendar,
            body=event_body
        ).execute()
        
        event_id = event['id']
        print(f"✅ Evento creado en maestro: {event_id}")
        
        # Verificar si aparece en el calendario personal
        print(f"\n🔍 Verificando si aparece en calendario personal...")
        
        # Buscar eventos en el calendario personal
        events_result = service.events().list(
            calendarId=filmmaker_calendar,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if events:
            print(f"✅ Encontrados {len(events)} eventos en calendario personal:")
            for event in events:
                print(f"   - {event.get('summary')} ({event.get('id')})")
        else:
            print("❌ No se encontraron eventos en calendario personal")
            print("⚠️ La propagación automática NO está funcionando")
        
        # Limpiar evento de prueba
        print(f"\n🧹 Limpiando evento de prueba...")
        service.events().delete(
            calendarId=master_calendar,
            eventId=event_id
        ).execute()
        print("✅ Evento de prueba eliminado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

def check_calendar_permissions():
    """Verifica los permisos de los calendarios"""
    
    print("\n🔐 VERIFICANDO PERMISOS DE CALENDARIOS")
    print("-" * 40)
    
    service = get_calendar_service()
    if not service:
        return False
    
    try:
        # Verificar calendario maestro
        master_calendar = config.MASTER_CALENDAR_ID
        calendar = service.calendars().get(calendarId=master_calendar).execute()
        
        print(f"📅 Calendario Maestro: {calendar.get('summary')}")
        print(f"   Acceso: {calendar.get('accessRole')}")
        print(f"   Propietario: {calendar.get('owner', {}).get('email')}")
        
        # Verificar calendario personal
        for profile in config.FILMMAKER_PROFILES:
            if profile["monday_name"] == "Arnau Admin":
                filmmaker_calendar = profile["calendar_id"]
                calendar = service.calendars().get(calendarId=filmmaker_calendar).execute()
                
                print(f"📅 Calendario Personal: {calendar.get('summary')}")
                print(f"   Acceso: {calendar.get('accessRole')}")
                print(f"   Propietario: {calendar.get('owner', {}).get('email')}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando permisos: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 DIAGNÓSTICO DE PROPAGACIÓN GOOGLE CALENDAR")
    print("=" * 60)
    
    # Verificar permisos
    check_calendar_permissions()
    
    # Probar propagación
    success = test_google_propagation()
    
    if success:
        print("\n🎯 DIAGNÓSTICO COMPLETADO")
        print("=" * 40)
        print("✅ Si no hay propagación automática, el problema está en:")
        print("   1. Permisos de calendarios")
        print("   2. Configuración de copias automáticas")
        print("   3. Arquitectura de sincronización")
    else:
        print("\n❌ Error durante el diagnóstico")

if __name__ == "__main__":
    main()
