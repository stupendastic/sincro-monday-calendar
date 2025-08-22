#!/usr/bin/env python3
"""
Script para probar la sincronización inversa desde calendarios personales
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from sync_logic import sincronizar_desde_calendario_personal, es_calendario_personal
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def test_sincronizacion_inversa():
    """Prueba la sincronización inversa desde un calendario personal"""
    
    print("🧪 PRUEBA DE SINCRONIZACIÓN INVERSA")
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
    
    # Buscar el calendario de Arnau Admin (para la prueba)
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
        # Buscar eventos en el calendario personal
        print(f"🔍 Buscando eventos en el calendario personal...")
        
        events_result = google_service.events().list(
            calendarId=calendar_id,
            maxResults=10
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("❌ No se encontraron eventos en el calendario personal")
            return False
        
        # Buscar un evento que sea una copia (que tenga master_event_id)
        evento_copia = None
        for event in events:
            extended_props = event.get('extendedProperties', {})
            private_props = extended_props.get('private', {})
            
            if private_props.get('master_event_id'):
                evento_copia = event
                break
        
        if not evento_copia:
            print("❌ No se encontró ningún evento copia en el calendario personal")
            print("💡 Los eventos copia deben tener master_event_id en sus propiedades")
            return False
        
        event_id = evento_copia['id']
        event_summary = evento_copia.get('summary', 'Sin título')
        master_event_id = evento_copia['extendedProperties']['private']['master_event_id']
        
        print(f"✅ Evento copia encontrado: {event_summary}")
        print(f"   📋 ID: {event_id}")
        print(f"   🔗 Master Event ID: {master_event_id}")
        
        # Mostrar información actual del evento
        start = evento_copia.get('start', {})
        if 'dateTime' in start:
            print(f"📅 Fecha actual: {start['dateTime']}")
        elif 'date' in start:
            print(f"📅 Fecha actual: {start['date']}")
        
        # Crear una copia modificada del evento para simular un cambio
        print(f"\n🔄 Simulando cambio en el evento copia...")
        
        # Modificar la fecha (añadir 2 días)
        if 'dateTime' in start:
            # Evento con hora específica
            fecha_actual = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            fecha_nueva = fecha_actual + timedelta(days=2)
            
            evento_modificado = evento_copia.copy()
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
            
            evento_modificado = evento_copia.copy()
            evento_modificado['start'] = {
                'date': fecha_nueva.strftime('%Y-%m-%d')
            }
            evento_modificado['end'] = {
                'date': fecha_nueva.strftime('%Y-%m-%d')
            }
            
            print(f"📅 Nueva fecha simulada: {fecha_nueva.strftime('%Y-%m-%d')}")
        
        # Probar la función de sincronización inversa
        print(f"\n🧪 Probando sincronización inversa...")
        
        success = sincronizar_desde_calendario_personal(
            evento_cambiado=evento_modificado,
            calendar_id_origen=calendar_id,
            google_service=google_service,
            monday_handler=monday_handler
        )
        
        if success:
            print(f"✅ Sincronización inversa exitosa")
            print(f"🎯 El evento maestro debería haberse actualizado")
            print(f"🎯 Monday.com debería haberse actualizado")
            print(f"🎯 Otros calendarios personales deberían haberse actualizado")
        else:
            print(f"❌ Error en la sincronización inversa")
        
        return success
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

def verificar_webhooks_personales():
    """Verifica que los webhooks personales están configurados"""
    
    print("🔍 VERIFICANDO WEBHOOKS PERSONALES")
    print("-" * 40)
    
    # Verificar que el archivo de mapeo existe
    if not os.path.exists("config/channels/config/channels/google_channel_map.json"):
        print("❌ config/channels/google_channel_map.json no encontrado")
        return False
    
    # Cargar el mapa
    import json
    with open("config/channels/config/channels/google_channel_map.json", 'r', encoding='utf-8') as f:
        channel_map = json.load(f)
    
    # Contar webhooks personales
    webhooks_personales = 0
    for channel_id, calendar_id in channel_map.items():
        if channel_id.startswith("stupendastic-personal-"):
            webhooks_personales += 1
            print(f"   ✅ {channel_id} → {calendar_id}")
    
    print(f"📊 Total webhooks personales: {webhooks_personales}")
    
    if webhooks_personales > 0:
        print(f"✅ Webhooks personales configurados correctamente")
        return True
    else:
        print(f"❌ No se encontraron webhooks personales")
        return False

def main():
    """Función principal"""
    print("🧪 TEST DE SINCRONIZACIÓN INVERSA")
    print("=" * 60)
    
    # Verificar webhooks
    webhooks_ok = verificar_webhooks_personales()
    
    if not webhooks_ok:
        print("\n❌ Los webhooks personales no están configurados")
        print("💡 Ejecuta configurar_webhooks_personales.py primero")
        return False
    
    # Probar sincronización inversa
    success = test_sincronizacion_inversa()
    
    if success:
        print("\n🎉 ¡PRUEBA EXITOSA!")
        print("=" * 40)
        print("✅ La sincronización inversa funciona")
        print("✅ Los cambios en calendarios personales se propagan correctamente")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Mueve un evento real en un calendario personal")
        print("2. Observa los logs del servidor")
        print("3. Verifica que el calendario maestro se actualiza")
        print("4. Verifica que Monday.com se actualiza")
    else:
        print("\n❌ PRUEBA FALLIDA")
        print("Verifica los logs para más detalles")

if __name__ == "__main__":
    main()
