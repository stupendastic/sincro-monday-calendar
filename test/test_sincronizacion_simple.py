#!/usr/bin/env python3
"""
Script de prueba simple para verificar que la sincronización básica funciona.
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def test_servicios_basicos():
    """Prueba que los servicios básicos funcionan"""
    print("🧪 PRUEBA 1: SERVICIOS BÁSICOS")
    print("=" * 40)
    
    # Probar Google Calendar
    try:
        google_service = get_calendar_service()
        if google_service:
            print("✅ Google Calendar Service: OK")
            
            # Probar acceso a calendario maestro
            try:
                calendar = google_service.calendars().get(calendarId=config.MASTER_CALENDAR_ID).execute()
                print(f"✅ Calendario maestro accesible: {calendar.get('summary')}")
            except Exception as e:
                print(f"❌ Error accediendo al calendario maestro: {e}")
        else:
            print("❌ Google Calendar Service: FALLÓ")
            return False
    except Exception as e:
        print(f"❌ Error inicializando Google Calendar: {e}")
        return False
    
    # Probar Monday.com
    try:
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        print("✅ Monday API Handler: OK")
        
        # Probar acceso al tablero
        try:
            boards = monday_handler.get_boards()
            print(f"✅ Tableros accesibles: {len(boards)} encontrados")
        except Exception as e:
            print(f"❌ Error accediendo a tableros: {e}")
    except Exception as e:
        print(f"❌ Error inicializando Monday API: {e}")
        return False
    
    return True

def test_busqueda_evento():
    """Prueba la búsqueda de un evento específico"""
    print("\n🧪 PRUEBA 2: BÚSQUEDA DE EVENTO")
    print("=" * 40)
    
    try:
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Buscar evento de prueba
        event_name = "ARNAU PRUEBAS CALENDARIO 1"
        print(f"🔍 Buscando evento: '{event_name}'")
        
        start_time = time.time()
        items_by_name = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name=event_name,
            exact_match=True
        )
        tiempo_busqueda = time.time() - start_time
        
        if items_by_name:
            item_id = items_by_name[0].id
            print(f"✅ Evento encontrado: {item_id}")
            print(f"⏱️  Tiempo de búsqueda: {tiempo_busqueda:.3f} segundos")
            return item_id
        else:
            print("❌ Evento no encontrado")
            return None
            
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        return None

def test_sincronizacion_google_monday():
    """Prueba la sincronización desde Google a Monday"""
    print("\n🧪 PRUEBA 3: SINCRONIZACIÓN GOOGLE → MONDAY")
    print("=" * 40)
    
    try:
        google_service = get_calendar_service()
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Crear evento de prueba en Google
        test_event = {
            'summary': 'EVENTO PRUEBA SINCRONIZACIÓN',
            'start': {
                'dateTime': (datetime.now() + timedelta(days=1)).isoformat(),
                'timeZone': 'Europe/Madrid'
            },
            'end': {
                'dateTime': (datetime.now() + timedelta(days=1, hours=2)).isoformat(),
                'timeZone': 'Europe/Madrid'
            },
            'description': 'Evento de prueba para verificar sincronización'
        }
        
        print("📅 Creando evento de prueba en Google Calendar...")
        
        # Crear evento en calendario maestro
        created_event = google_service.events().insert(
            calendarId=config.MASTER_CALENDAR_ID,
            body=test_event
        ).execute()
        
        event_id = created_event.get('id')
        print(f"✅ Evento creado en Google: {event_id}")
        
        # Probar sincronización
        print("🔄 Probando sincronización...")
        
        from sync_logic import sincronizar_desde_google_calendar
        
        start_time = time.time()
        success = sincronizar_desde_google_calendar(
            evento_cambiado=created_event,
            google_service=google_service,
            monday_handler=monday_handler
        )
        tiempo_sincronizacion = time.time() - start_time
        
        if success:
            print(f"✅ Sincronización exitosa en {tiempo_sincronizacion:.3f} segundos")
        else:
            print(f"❌ Error en sincronización (tiempo: {tiempo_sincronizacion:.3f}s)")
        
        # Limpiar evento de prueba
        print("🧹 Limpiando evento de prueba...")
        google_service.events().delete(
            calendarId=config.MASTER_CALENDAR_ID,
            eventId=event_id
        ).execute()
        print("✅ Evento de prueba eliminado")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en prueba de sincronización: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DE SINCRONIZACIÓN BÁSICA")
    print("=" * 60)
    
    resultados = {}
    
    # Prueba 1: Servicios básicos
    try:
        servicios_ok = test_servicios_basicos()
        resultados['servicios_basicos'] = servicios_ok
    except Exception as e:
        print(f"❌ Error en prueba de servicios: {e}")
        resultados['servicios_basicos'] = False
    
    # Prueba 2: Búsqueda de evento
    try:
        item_id = test_busqueda_evento()
        resultados['busqueda_evento'] = item_id is not None
    except Exception as e:
        print(f"❌ Error en prueba de búsqueda: {e}")
        resultados['busqueda_evento'] = False
    
    # Prueba 3: Sincronización
    if resultados.get('servicios_basicos', False):
        try:
            sync_ok = test_sincronizacion_google_monday()
            resultados['sincronizacion'] = sync_ok
        except Exception as e:
            print(f"❌ Error en prueba de sincronización: {e}")
            resultados['sincronizacion'] = False
    else:
        print("⏭️  Saltando prueba de sincronización - servicios básicos fallaron")
        resultados['sincronizacion'] = False
    
    # Resumen
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 30)
    
    for prueba, resultado in resultados.items():
        status = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{prueba}: {status}")
    
    exitos = sum(resultados.values())
    total = len(resultados)
    
    print(f"\n🎯 RESULTADO FINAL: {exitos}/{total} pruebas exitosas")
    
    if exitos == total:
        print("🎉 ¡Sincronización básica funciona correctamente!")
    else:
        print("⚠️  Hay problemas que necesitan ser solucionados")

if __name__ == "__main__":
    main()

