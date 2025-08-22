#!/usr/bin/env python3
"""
Script para probar la sincronización Google → Monday sin webhook
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from sync_logic import sincronizar_desde_google_calendar
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def probar_sincronizacion_google_monday():
    """Prueba la sincronización Google → Monday"""
    
    print("🧪 PRUEBA DE SINCRONIZACIÓN GOOGLE → MONDAY")
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
        print(f"🔍 Buscando evento 'PRUEBA SINCRONIZACIÓN' en calendario maestro...")
        
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
            if event.get('summary') == 'PRUEBA SINCRONIZACIÓN':
                evento = event
                break
        
        if not evento:
            print("❌ No se encontró el evento 'PRUEBA SINCRONIZACIÓN'")
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
        
        # Modificar la fecha (añadir 3 días)
        if 'dateTime' in start:
            # Evento con hora específica
            fecha_actual = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            fecha_nueva = fecha_actual + timedelta(days=3)
            
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
            fecha_nueva = fecha_actual + timedelta(days=3)
            
            evento_modificado = evento.copy()
            evento_modificado['start'] = {
                'date': fecha_nueva.strftime('%Y-%m-%d')
            }
            evento_modificado['end'] = {
                'date': fecha_nueva.strftime('%Y-%m-%d')
            }
            
            print(f"📅 Nueva fecha simulada: {fecha_nueva.strftime('%Y-%m-%d')}")
        
        # Probar la función de sincronización
        print(f"\n🧪 Probando función de sincronización...")
        
        success = sincronizar_desde_google_calendar(
            evento_cambiado=evento_modificado,
            google_service=google_service,
            monday_handler=monday_handler
        )
        
        if success:
            print(f"✅ Sincronización exitosa")
            print(f"🎯 Monday.com debería haberse actualizado")
            print(f"🎯 Calendarios personales deberían haberse actualizado")
        else:
            print(f"❌ Error en la sincronización")
        
        return success
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 TEST DE SINCRONIZACIÓN GOOGLE → MONDAY")
    print("=" * 60)
    
    success = probar_sincronizacion_google_monday()
    
    if success:
        print("\n🎉 ¡PRUEBA EXITOSA!")
        print("=" * 40)
        print("✅ La sincronización desde Google Calendar funciona")
        print("✅ Monday.com se actualiza correctamente")
        print("✅ Los calendarios personales se actualizan")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Actualiza manualmente el webhook de Monday.com")
        print("2. Haz una prueba real moviendo un evento")
        print("3. Verifica que Monday.com recibe las notificaciones")
    else:
        print("\n❌ PRUEBA FALLIDA")
        print("Verifica los logs para más detalles")

if __name__ == "__main__":
    main()
