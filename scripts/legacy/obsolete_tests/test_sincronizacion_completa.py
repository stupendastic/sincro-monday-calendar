#!/usr/bin/env python3
"""
Script para probar la sincronización completa en ambas direcciones
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from sync_logic import sincronizar_desde_google_calendar, sincronizar_desde_calendario_personal
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def test_sincronizacion_completa():
    """Prueba la sincronización completa"""
    
    print("🧪 PRUEBA DE SINCRONIZACIÓN COMPLETA")
    print("=" * 60)
    
    # Obtener servicios
    google_service = get_calendar_service()
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    if not monday_handler:
        print("❌ No se pudo obtener el servicio de Monday")
        return False
    
    # Obtener calendario maestro
    master_calendar = config.MASTER_CALENDAR_ID
    
    try:
        # Buscar el evento de prueba
        print(f"🔍 Buscando evento 'ARNAU PRUEBAS CALENDARIO 1' en calendario maestro...")
        
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
            print("❌ No se encontró el evento de prueba")
            return False
        
        # Buscar el evento específico
        evento = None
        for event in events:
            if event.get('summary') == 'ARNAU PRUEBAS CALENDARIO 1':
                evento = event
                break
        
        if not evento:
            print("❌ No se encontró el evento 'ARNAU PRUEBAS CALENDARIO 1'")
            return False
        
        event_id = evento['id']
        event_summary = evento.get('summary', 'Sin título')
        
        print(f"✅ Evento encontrado: {event_summary} (ID: {event_id})")
        
        # Mostrar información actual del evento
        start = evento.get('start', {})
        if 'dateTime' in start:
            print(f"📅 Fecha actual: {start['dateTime']}")
        elif 'date' in start:
            print(f"📅 Fecha actual: {start['date']}")
        
        # Crear una copia modificada del evento para simular un cambio
        print(f"\n🔄 Simulando cambio en el evento...")
        
        # Modificar la fecha (añadir 2 días)
        if 'dateTime' in start:
            # Evento con hora específica
            fecha_actual = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            fecha_nueva = fecha_actual + timedelta(days=2)
            
            evento_modificado = evento.copy()
            evento_modificado['start'] = {
                'dateTime': fecha_nueva.isoformat(),
                'timeZone': 'Europe/Madrid'
            }
            evento_modificado['end'] = {
                'dateTime': (fecha_nueva + timedelta(hours=1)).isoformat(),
                'timeZone': 'Europe/Madrid'
            }
            
            print(f"📅 Nueva fecha simulada: {fecha_nueva.isoformat()}")
            
        elif 'date' in start:
            # Evento de día completo
            fecha_actual = datetime.fromisoformat(start['date'])
            fecha_nueva = fecha_actual + timedelta(days=2)
            
            evento_modificado = evento.copy()
            evento_modificado['start'] = {
                'date': fecha_nueva.strftime('%Y-%m-%d')
            }
            evento_modificado['end'] = {
                'date': fecha_nueva.strftime('%Y-%m-%d')
            }
            
            print(f"📅 Nueva fecha simulada: {fecha_nueva.strftime('%Y-%m-%d')}")
        
        # PRUEBA 1: Sincronización desde calendario maestro
        print(f"\n🧪 PRUEBA 1: Sincronización desde calendario MAESTRO")
        print("-" * 50)
        
        success1 = sincronizar_desde_google_calendar(
            evento_cambiado=evento_modificado,
            google_service=google_service,
            monday_handler=monday_handler
        )
        
        if success1:
            print(f"✅ Prueba 1 EXITOSA: Sincronización desde calendario maestro")
        else:
            print(f"❌ Prueba 1 FALLIDA: Sincronización desde calendario maestro")
        
        # PRUEBA 2: Sincronización desde calendario personal
        print(f"\n🧪 PRUEBA 2: Sincronización desde calendario PERSONAL")
        print("-" * 50)
        
        # Obtener el primer calendario personal
        filmmaker_profiles = config.FILMMAKER_PROFILES
        if filmmaker_profiles:
            primer_filmmaker = filmmaker_profiles[0]
            calendar_personal = primer_filmmaker.get('calendar_id')
            filmmaker_name = primer_filmmaker.get('monday_name')
            
            print(f"📅 Usando calendario personal de: {filmmaker_name}")
            print(f"📅 Calendar ID: {calendar_personal}")
            
            # Buscar el evento copia en el calendario personal
            copy_event = None
            try:
                copy_events_result = google_service.events().list(
                    calendarId=calendar_personal,
                    timeMin=(datetime.now() - timedelta(days=30)).isoformat() + 'Z',
                    timeMax=(datetime.now() + timedelta(days=30)).isoformat() + 'Z',
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                copy_events = copy_events_result.get('items', [])
                
                for event in copy_events:
                    if event.get('summary') == 'ARNAU PRUEBAS CALENDARIO 1':
                        copy_event = event
                        break
                
                if copy_event:
                    print(f"✅ Evento copia encontrado en calendario personal")
                    
                    # Modificar la fecha del evento copia
                    if 'dateTime' in copy_event.get('start', {}):
                        fecha_copia = datetime.fromisoformat(copy_event['start']['dateTime'].replace('Z', '+00:00'))
                        fecha_nueva_copia = fecha_copia + timedelta(days=1)
                        
                        copy_event_modificado = copy_event.copy()
                        copy_event_modificado['start'] = {
                            'dateTime': fecha_nueva_copia.isoformat(),
                            'timeZone': 'Europe/Madrid'
                        }
                        copy_event_modificado['end'] = {
                            'dateTime': (fecha_nueva_copia + timedelta(hours=1)).isoformat(),
                            'timeZone': 'Europe/Madrid'
                        }
                        
                        print(f"📅 Nueva fecha simulada en calendario personal: {fecha_nueva_copia.isoformat()}")
                        
                        success2 = sincronizar_desde_calendario_personal(
                            evento_cambiado=copy_event_modificado,
                            calendar_id=calendar_personal,
                            google_service=google_service,
                            monday_handler=monday_handler
                        )
                        
                        if success2:
                            print(f"✅ Prueba 2 EXITOSA: Sincronización desde calendario personal")
                        else:
                            print(f"❌ Prueba 2 FALLIDA: Sincronización desde calendario personal")
                    else:
                        print(f"⚠️  Evento copia no tiene fecha/hora específica")
                        success2 = False
                else:
                    print(f"❌ No se encontró evento copia en calendario personal")
                    success2 = False
                    
            except Exception as e:
                print(f"❌ Error buscando evento copia: {e}")
                success2 = False
        else:
            print(f"❌ No hay perfiles de filmmakers configurados")
            success2 = False
        
        return success1 and success2
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 TEST DE SINCRONIZACIÓN COMPLETA")
    print("=" * 60)
    
    success = test_sincronizacion_completa()
    
    if success:
        print("\n🎉 ¡PRUEBA EXITOSA!")
        print("=" * 40)
        print("✅ Sincronización desde calendario maestro funciona")
        print("✅ Sincronización desde calendarios personales funciona")
        print("✅ Monday.com se actualiza correctamente")
        print("✅ Los calendarios personales se actualizan")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Haz una prueba real moviendo un evento en Google Calendar")
        print("2. Verifica que Monday.com se actualiza")
        print("3. Verifica que los calendarios personales se actualizan")
    else:
        print("\n❌ PRUEBA FALLIDA")
        print("Verifica los logs para más detalles")

if __name__ == "__main__":
    main()
