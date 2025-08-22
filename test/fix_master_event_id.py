#!/usr/bin/env python3
"""
Script para arreglar el master_event_id usando el ID correcto de Monday.
"""

import os
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service, update_google_event_by_id
import config

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal para arreglar master_event_id."""
    print("🔄 Arreglando master_event_id...")
    
    # Obtener servicio de Google Calendar
    google_service = get_calendar_service()
    if not google_service:
        print("❌ Error al inicializar servicio de Google Calendar")
        return
    
    print("✅ Servicio de Google Calendar inicializado")
    
    # El ID correcto que está en Monday
    correct_master_event_id = "u6qas96o6qbvh54770ulivkvrk"
    
    # Calendario maestro
    master_calendar_id = config.MASTER_CALENDAR_ID
    print(f"\n📅 Arreglando evento en calendario maestro: {master_calendar_id}")
    
    # Buscar el evento en el calendario maestro
    events_result = google_service.events().list(
        calendarId=master_calendar_id,
        showDeleted=False,
        singleEvents=True
    ).execute()
    
    events = events_result.get('items', [])
    
    for event in events:
        event_id = event.get('id')
        event_summary = event.get('summary', 'Sin título')
        
        print(f"  📋 Evento encontrado: '{event_summary}' (ID: {event_id})")
        
        # Actualizar con el master_event_id correcto usando la función correcta
        extended_props = {
            'private': {
                'master_event_id': correct_master_event_id
            }
        }
        
        try:
            success = update_google_event_by_id(
                google_service,
                master_calendar_id,
                event_id,
                event,  # Usar el evento completo
                extended_properties=extended_props
            )
            
            if success:
                print(f"    ✅ Actualizado: '{event_summary}' con master_event_id: {correct_master_event_id}")
            else:
                print(f"    ❌ Error actualizando '{event_summary}'")
            
        except Exception as e:
            print(f"    ❌ Error actualizando '{event_summary}': {e}")
    
    # También actualizar en calendarios de filmmakers
    print(f"\n👥 Arreglando eventos en calendarios de filmmakers...")
    
    for perfil in config.FILMMAKER_PROFILES:
        if perfil.get('calendar_id'):
            calendar_id = perfil['calendar_id']
            filmmaker_name = perfil['monday_name']
            
            print(f"\n  📅 Arreglando eventos para {filmmaker_name}: {calendar_id}")
            
            # Buscar eventos en este calendario
            events_result = google_service.events().list(
                calendarId=calendar_id,
                showDeleted=False,
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            
            for event in events:
                event_id = event.get('id')
                event_summary = event.get('summary', 'Sin título')
                
                print(f"    📋 Evento encontrado: '{event_summary}' (ID: {event_id})")
                
                # Actualizar con el master_event_id correcto
                extended_props = {
                    'private': {
                        'master_event_id': correct_master_event_id
                    }
                }
                
                try:
                    success = update_google_event_by_id(
                        google_service,
                        calendar_id,
                        event_id,
                        event,  # Usar el evento completo
                        extended_properties=extended_props
                    )
                    
                    if success:
                        print(f"      ✅ Actualizado: '{event_summary}' con master_event_id: {correct_master_event_id}")
                    else:
                        print(f"      ❌ Error actualizando '{event_summary}'")
                    
                except Exception as e:
                    print(f"      ❌ Error actualizando '{event_summary}': {e}")
    
    print("\n🎉 ¡Master Event ID arreglado!")
    print(f"📝 Todos los eventos ahora usan: {correct_master_event_id}")
    print("🔄 La sincronización Google → Monday debería funcionar correctamente")

if __name__ == "__main__":
    main() 