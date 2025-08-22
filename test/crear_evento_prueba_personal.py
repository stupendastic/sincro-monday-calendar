#!/usr/bin/env python3
"""
Script para crear un evento de prueba en el calendario personal
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def crear_evento_prueba_personal():
    """Crea un evento de prueba en el calendario personal de Arnau Admin"""
    
    print("🎬 CREANDO EVENTO DE PRUEBA EN CALENDARIO PERSONAL")
    print("=" * 60)
    
    # Obtener servicios
    google_service = get_calendar_service()
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # Buscar el calendario de Arnau Admin
    calendar_id = None
    for profile in config.FILMMAKER_PROFILES:
        if profile["monday_name"] == "Arnau Admin":
            calendar_id = profile["calendar_id"]
            break
    
    if not calendar_id:
        print("❌ No se encontró el calendario de Arnau Admin")
        return False
    
    print(f"📅 Usando calendario: {calendar_id}")
    
    try:
        # Crear un evento de prueba para mañana
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        event_body = {
            'summary': 'EVENTO PRUEBA SINCRONIZACIÓN INVERSA',
            'description': 'Evento de prueba para verificar la sincronización inversa desde calendario personal',
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
                    'master_event_id': 'evento_prueba_master_123',
                    'monday_item_id': '9733398727'
                }
            }
        }
        
        # Crear el evento
        event = google_service.events().insert(
            calendarId=calendar_id,
            body=event_body
        ).execute()
        
        event_id = event['id']
        print(f"✅ Evento de prueba creado exitosamente")
        print(f"   📋 ID: {event_id}")
        print(f"   📅 Fecha: {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   🔗 Master Event ID: evento_prueba_master_123")
        print(f"   📋 Monday Item ID: 9733398727")
        
        return event_id
        
    except Exception as e:
        print(f"❌ Error creando evento de prueba: {e}")
        return False

def main():
    """Función principal"""
    print("🎬 CREADOR DE EVENTO DE PRUEBA")
    print("=" * 60)
    
    event_id = crear_evento_prueba_personal()
    
    if event_id:
        print(f"\n🎉 ¡EVENTO CREADO!")
        print("=" * 40)
        print(f"✅ Evento de prueba creado: {event_id}")
        print(f"📋 Ahora puedes probar la sincronización inversa")
        print(f"💡 Ejecuta test_sincronizacion_inversa.py para probar")
    else:
        print(f"\n❌ ERROR")
        print("=" * 40)
        print(f"❌ No se pudo crear el evento de prueba")

if __name__ == "__main__":
    main()
