#!/usr/bin/env python3
"""
Script para verificar el estado del evento en Google Calendar
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

def verificar_evento_google():
    """Verifica el estado del evento en Google Calendar"""
    
    print("🔍 VERIFICANDO EVENTO EN GOOGLE CALENDAR")
    print("=" * 60)
    
    # Obtener servicio de Google
    google_service = get_calendar_service()
    
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # Obtener calendario maestro
    master_calendar = config.MASTER_CALENDAR_ID
    
    try:
        print(f"📅 Buscando eventos en calendario maestro: {master_calendar}")
        
        # Buscar eventos en el calendario maestro
        events_result = google_service.events().list(
            calendarId=master_calendar,
            timeMin=(datetime.now() - timedelta(days=30)).isoformat() + 'Z',
            timeMax=(datetime.now() + timedelta(days=30)).isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("❌ No se encontraron eventos en el calendario maestro")
            return False
        
        print(f"✅ Encontrados {len(events)} eventos en el calendario maestro")
        
        # Buscar el evento específico
        evento = None
        for event in events:
            if event.get('summary') == 'PRUEBA SINCRONIZACIÓN':
                evento = event
                break
        
        if not evento:
            print("❌ No se encontró el evento 'PRUEBA SINCRONIZACIÓN'")
            print("\n📋 Eventos disponibles:")
            for i, event in enumerate(events[:10], 1):  # Solo los primeros 10
                summary = event.get('summary', 'Sin título')
                start = event.get('start', {})
                if 'dateTime' in start:
                    fecha = start['dateTime']
                elif 'date' in start:
                    fecha = start['date']
                else:
                    fecha = 'Sin fecha'
                print(f"   {i}. {summary} - {fecha}")
            return False
        
        event_id = evento['id']
        event_summary = evento.get('summary', 'Sin título')
        
        print(f"✅ Evento encontrado: {event_summary}")
        print(f"   ID: {event_id}")
        
        # Mostrar información del evento
        start = evento.get('start', {})
        if 'dateTime' in start:
            print(f"   Fecha: {start['dateTime']}")
        elif 'date' in start:
            print(f"   Fecha: {start['date']}")
        
        end = evento.get('end', {})
        if 'dateTime' in end:
            print(f"   Fin: {end['dateTime']}")
        elif 'date' in end:
            print(f"   Fin: {end['date']}")
        
        # Verificar si el evento tiene el ID correcto
        if event_id == 'e7iutjdiolkedm63b6drcbp1k8':
            print("✅ ID del evento coincide con Monday.com")
        else:
            print(f"⚠️  ID del evento no coincide: {event_id} vs e7iutjdiolkedm63b6drcbp1k8")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando evento: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 VERIFICADOR DE EVENTO GOOGLE CALENDAR")
    print("=" * 80)
    
    success = verificar_evento_google()
    
    if success:
        print("\n✅ Evento verificado correctamente")
    else:
        print("\n❌ Error verificando evento")

if __name__ == "__main__":
    main()
