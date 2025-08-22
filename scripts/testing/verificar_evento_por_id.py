#!/usr/bin/env python3
"""
Script para verificar un evento específico por ID
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from config import MASTER_CALENDAR_ID

def verificar_evento_por_id():
    """Verifica un evento específico por ID"""
    
    print("🔍 VERIFICANDO EVENTO POR ID")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Inicializar servicios
    google_service = get_calendar_service()
    
    if not google_service:
        print("❌ No se pudo conectar a Google Calendar")
        return
    
    # IDs de eventos a verificar
    event_ids = [
        "e7iutjdiolkedm63b6drcbp1k8",  # ID original
        "1du67efu98h0ej0le53j7vphvk",  # ID nuevo
    ]
    
    # Calendarios a verificar
    calendarios = [
        ("MASTER", MASTER_CALENDAR_ID),
        ("UNASSIGNED", "c_49d5be3fada7594d92ff64036b07afb75c4c83436844cb1f3c834bc9e31d4e2e@group.calendar.google.com"),
    ]
    
    for event_id in event_ids:
        print(f"\n🆔 Verificando evento ID: {event_id}")
        print("-" * 40)
        
        for nombre, calendar_id in calendarios:
            print(f"📅 Buscando en calendario: {nombre}")
            
            try:
                event = google_service.events().get(
                    calendarId=calendar_id,
                    eventId=event_id
                ).execute()
                
                print(f"   ✅ ENCONTRADO:")
                print(f"      - Nombre: {event.get('summary', 'Sin título')}")
                print(f"      - Fecha: {event['start'].get('dateTime', event['start'].get('date'))}")
                print(f"      - Calendario: {nombre}")
                print(f"      - Estado: {event.get('status', 'confirmado')}")
                
            except Exception as e:
                if "Not Found" in str(e):
                    print(f"   ❌ No encontrado en {nombre}")
                else:
                    print(f"   ❌ Error: {e}")

def main():
    """Función principal"""
    print("🔍 VERIFICADOR DE EVENTO POR ID")
    print("=" * 60)
    
    try:
        verificar_evento_por_id()
    except KeyboardInterrupt:
        print("\n👋 Verificación cancelada")
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")

if __name__ == "__main__":
    main()
