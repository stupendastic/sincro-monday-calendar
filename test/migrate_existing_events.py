#!/usr/bin/env python3
"""
Script para migrar eventos existentes en Google Calendar
y añadirles master_event_id en sus propiedades extendidas.
"""

import os
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service, migrate_existing_events_with_master_id
import config

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal para migrar eventos existentes."""
    print("🔄 Iniciando migración de eventos existentes...")
    
    # Obtener servicio de Google Calendar
    google_service = get_calendar_service()
    if not google_service:
        print("❌ Error al inicializar servicio de Google Calendar")
        return
    
    print("✅ Servicio de Google Calendar inicializado")
    
    # Migrar eventos en el calendario maestro
    master_calendar_id = config.MASTER_CALENDAR_ID
    print(f"\n📅 Migrando eventos en calendario maestro: {master_calendar_id}")
    
    # Para el calendario maestro, usamos su propio ID como master_event_id
    success = migrate_existing_events_with_master_id(
        google_service, 
        master_calendar_id, 
        master_calendar_id  # El calendario maestro se referencia a sí mismo
    )
    
    if success:
        print("✅ Migración del calendario maestro completada")
    else:
        print("❌ Error en migración del calendario maestro")
    
    # Migrar eventos en calendarios de filmmakers
    print(f"\n👥 Migrando eventos en calendarios de filmmakers...")
    
    for perfil in config.FILMMAKER_PROFILES:
        if perfil.get('calendar_id'):
            calendar_id = perfil['calendar_id']
            filmmaker_name = perfil['monday_name']
            
            print(f"\n  📅 Migrando eventos para {filmmaker_name}: {calendar_id}")
            
            # Para calendarios de filmmakers, usamos el ID del calendario maestro
            success = migrate_existing_events_with_master_id(
                google_service,
                calendar_id,
                master_calendar_id  # Todos los eventos de filmmakers se refieren al calendario maestro
            )
            
            if success:
                print(f"  ✅ Migración completada para {filmmaker_name}")
            else:
                print(f"  ❌ Error en migración para {filmmaker_name}")
    
    print("\n🎉 Proceso de migración completado!")
    print("📝 Los eventos existentes ahora tienen master_event_id")
    print("🔄 La sincronización Google → Monday debería funcionar correctamente")

if __name__ == "__main__":
    main() 