#!/usr/bin/env python3
"""
Script para crear un evento de prueba en el calendario maestro
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def crear_evento_prueba():
    """Crea un evento de prueba en el calendario maestro"""
    
    print("🎯 CREANDO EVENTO DE PRUEBA")
    print("=" * 50)
    
    # Obtener servicio de Google
    google_service = get_calendar_service()
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # Crear evento para mañana
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=2)
    
    event = {
        'summary': 'PRUEBA SINCRONIZACIÓN',
        'description': 'Evento de prueba para verificar la sincronización bidireccional',
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
                'created_by': 'test_script'
            }
        }
    }
    
    try:
        # Crear el evento
        event_result = google_service.events().insert(
            calendarId=config.MASTER_CALENDAR_ID,
            body=event
        ).execute()
        
        print(f"✅ Evento creado exitosamente:")
        print(f"   ID: {event_result['id']}")
        print(f"   Título: {event_result['summary']}")
        print(f"   Fecha: {event_result['start']['dateTime']}")
        print(f"   Calendario: {config.MASTER_CALENDAR_ID}")
        
        print(f"\n📋 PRÓXIMOS PASOS:")
        print(f"1. Ve a Google Calendar y mueve este evento")
        print(f"2. Observa los logs del servidor")
        print(f"3. Verifica que Monday.com se actualiza")
        print(f"4. Verifica que los calendarios personales se actualizan")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando evento: {e}")
        return False

def main():
    """Función principal"""
    print("🎯 CREADOR DE EVENTO DE PRUEBA")
    print("=" * 60)
    
    success = crear_evento_prueba()
    
    if success:
        print("\n🎉 ¡EVENTO CREADO!")
        print("Ahora puedes hacer la prueba moviendo el evento en Google Calendar")
    else:
        print("\n❌ ERROR CREANDO EVENTO")

if __name__ == "__main__":
    main()
