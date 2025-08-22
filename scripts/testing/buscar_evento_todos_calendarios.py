#!/usr/bin/env python3
"""
Script para buscar el evento en todos los calendarios
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from config import MASTER_CALENDAR_ID, FILMMAKER_PROFILES

def buscar_evento_todos_calendarios():
    """Busca el evento en todos los calendarios"""
    
    print("🔍 BUSCANDO EVENTO EN TODOS LOS CALENDARIOS")
    print("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Inicializar servicios
    google_service = get_calendar_service()
    
    if not google_service:
        print("❌ No se pudo conectar a Google Calendar")
        return
    
    # Lista de calendarios a buscar
    calendarios = [
        ("MASTER", MASTER_CALENDAR_ID),
        ("UNASSIGNED", "c_49d5be3fada7594d92ff64036b07afb75c4c83436844cb1f3c834bc9e31d4e2e@group.calendar.google.com"),
    ]
    
    # Añadir calendarios personales
    for profile in FILMMAKER_PROFILES:
        calendarios.append((profile['monday_name'], profile['calendar_id']))
    
    # Buscar en cada calendario
    evento_encontrado = False
    
    for nombre, calendar_id in calendarios:
        print(f"\n📅 Buscando en calendario: {nombre}")
        print(f"   ID: {calendar_id}")
        
        try:
            events = google_service.events().list(
                calendarId=calendar_id,
                q="PRUEBA SINCRONIZACIÓN",
                maxResults=1
            ).execute()
            
            if events.get('items'):
                event = events['items'][0]
                event_id = event['id']
                event_start = event['start'].get('dateTime', event['start'].get('date'))
                
                print(f"   ✅ ENCONTRADO:")
                print(f"      - ID: {event_id}")
                print(f"      - Fecha: {event_start}")
                print(f"      - Calendario: {nombre}")
                
                evento_encontrado = True
            else:
                print(f"   ❌ No encontrado")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    if not evento_encontrado:
        print("\n❌ El evento no se encontró en ningún calendario")
    else:
        print("\n✅ Evento encontrado en el sistema")

def main():
    """Función principal"""
    print("🔍 BUSCADOR DE EVENTO EN TODOS LOS CALENDARIOS")
    print("=" * 70)
    
    try:
        buscar_evento_todos_calendarios()
    except KeyboardInterrupt:
        print("\n👋 Búsqueda cancelada")
    except Exception as e:
        print(f"❌ Error durante la búsqueda: {e}")

if __name__ == "__main__":
    main()
