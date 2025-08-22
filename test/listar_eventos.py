#!/usr/bin/env python3
"""
Script para listar eventos del calendario maestro
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def listar_eventos():
    """Lista todos los eventos del calendario maestro"""
    
    print("📋 LISTANDO EVENTOS DEL CALENDARIO MAESTRO")
    print("=" * 60)
    
    # Obtener servicio
    google_service = get_calendar_service()
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # Obtener calendario maestro
    master_calendar = config.MASTER_CALENDAR_ID
    
    try:
        # Buscar eventos en los próximos 30 días
        now = datetime.now()
        start_time = now.isoformat() + 'Z'
        end_time = (now + timedelta(days=30)).isoformat() + 'Z'
        
        print(f"🔍 Buscando eventos desde {start_time} hasta {end_time}")
        
        events_result = google_service.events().list(
            calendarId=master_calendar,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("❌ No se encontraron eventos")
            return False
        
        print(f"✅ Encontrados {len(events)} eventos:")
        print("-" * 40)
        
        for i, event in enumerate(events, 1):
            event_id = event['id']
            summary = event.get('summary', 'Sin título')
            start = event.get('start', {})
            
            if 'dateTime' in start:
                fecha = start['dateTime']
            elif 'date' in start:
                fecha = start['date']
            else:
                fecha = 'Fecha no especificada'
            
            print(f"{i}. {summary}")
            print(f"   ID: {event_id}")
            print(f"   Fecha: {fecha}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error listando eventos: {e}")
        return False

def main():
    """Función principal"""
    print("📋 LISTADOR DE EVENTOS")
    print("=" * 60)
    
    success = listar_eventos()
    
    if success:
        print("✅ Listado completado")
    else:
        print("❌ Error en el listado")

if __name__ == "__main__":
    main()
