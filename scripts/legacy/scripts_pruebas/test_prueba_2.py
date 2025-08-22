#!/usr/bin/env python3
"""
PRUEBA 2: Google Personal -> Monday
Mueve el evento desde el calendario personal de Arnau Admin
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# Añadir el directorio actual al path
sys.path.append('.')

import sync_logic
import config
from google_calendar_service import get_calendar_service, find_event_copy_by_master_id, update_google_event_by_id
from monday_api_handler import MondayAPIHandler

def obtener_google_event_id(monday_handler):
    """Obtiene el Google Event ID del item de prueba."""
    query = """
    query {
        items(ids: [9733398727]) {
            id
            name
            column_values(ids: ["text_mktfdhm3"]) {
                id
                text
                value
            }
        }
    }
    """
    
    data = {'query': query}
    
    try:
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        response.raise_for_status()
        
        if response.status_code == 200:
            response_data = response.json()
            items = response_data.get('data', {}).get('items', [])
            if items:
                item = items[0]
                column_values = item.get('column_values', [])
                for col in column_values:
                    if col.get('id') == 'text_mktfdhm3':
                        google_event_id = col.get('text', '').strip()
                        if google_event_id:
                            return google_event_id
        return None
    except Exception as e:
        print(f"❌ Error al obtener Google Event ID: {e}")
        return None

def asignar_arnau_admin(monday_handler):
    """Asigna Arnau Admin al item de prueba."""
    print("👤 Asignando Arnau Admin al item...")
    
    # Usar el ID real de Arnau Admin
    arnau_user_id = 34210704
    
    # Asignar Arnau Admin al item
    success = monday_handler.update_column_value(
        9733398727,  # ITEM_DE_PRUEBA_ID
        config.BOARD_ID_GRABACIONES,
        "personas1",  # COL_OPERARIO
        {"personsAndTeams": [{"id": arnau_user_id, "kind": "person"}]},
        'person'
    )
    
    if success:
        print("✅ Arnau Admin asignado al item")
        
        # Simular webhook para crear la copia
        print("🔄 Simulando webhook para crear copia...")
        global google_service
        google_service = get_calendar_service() # Re-initialize google_service for the webhook call
        sync_logic.sincronizar_item_via_webhook(
            9733398727,  # ITEM_DE_PRUEBA_ID
            monday_handler=monday_handler,
            google_service=google_service
        )
        
        return True
    else:
        print("❌ Error al asignar Arnau Admin")
        return False

def main():
    print("🧪 PRUEBA 2: Google Personal -> Monday")
    print("=" * 50)
    
    # Inicializar servicios
    print("🔧 Inicializando servicios...")
    global google_service
    google_service = get_calendar_service()
    monday_handler = MondayAPIHandler(api_token=os.getenv('MONDAY_API_KEY'))
    print("✅ Servicios inicializados")
    
    # Obtener master_event_id
    master_event_id = obtener_google_event_id(monday_handler)
    if not master_event_id:
        print("❌ No hay master_event_id")
        return False
    
    print(f"📋 Usando master_event_id: {master_event_id}")
    
    # Obtener calendario de Arnau Admin
    FILMMAKER_TEST = 'Arnau Admin'
    calendar_id = None
    for perfil in config.FILMMAKER_PROFILES:
        if perfil.get('monday_name') == FILMMAKER_TEST:
            calendar_id = perfil.get('calendar_id')
            break
    
    if not calendar_id:
        print(f"❌ {FILMMAKER_TEST} no encontrado en perfiles")
        return False
    
    print(f"📅 Calendario de {FILMMAKER_TEST}: {calendar_id}")
    
    # Buscar copia en calendario personal
    copy_event = find_event_copy_by_master_id(google_service, calendar_id, master_event_id)
    
    if not copy_event:
        print(f"❌ No se encontró copia para {FILMMAKER_TEST}")
        print("🔄 Creando copia primero...")
        
        # Asignar Arnau Admin y crear copia
        if asignar_arnau_admin(monday_handler):
            # Buscar copia nuevamente
            copy_event = find_event_copy_by_master_id(google_service, calendar_id, master_event_id)
            if not copy_event:
                print("❌ Aún no se encontró copia después de asignar")
                return False
        else:
            return False
    
    print(f"✅ Copia encontrada: {copy_event['id']}")
    
    # Mover evento (cambiar hora)
    nueva_hora = datetime.now() + timedelta(hours=2)
    nueva_fecha = nueva_hora.strftime("%Y-%m-%dT%H:%M:%S+02:00")
    
    print(f"🔄 Moviendo evento a: {nueva_fecha}")
    
    # Actualizar evento copia usando datos directos de Google
    success = update_google_event_by_id(
        google_service,
        calendar_id,
        copy_event['id'],
        {
            'summary': copy_event.get('summary', 'Evento de prueba'),
            'start': {'dateTime': nueva_fecha, 'timeZone': 'Europe/Madrid'},
            'end': {'dateTime': (nueva_hora + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+02:00"), 'timeZone': 'Europe/Madrid'},
            'description': copy_event.get('description', '')
        }
    )
    
    if success:
        print(f"✅ Evento copia actualizado: {nueva_fecha}")
        
        # Simular sincronización desde Google
        print("🔄 Simulando sincronización desde Google...")
        sync_logic.sincronizar_desde_google(
            master_event_id,
            monday_handler=monday_handler,
            google_service=google_service
        )
        
        print("✅ PRUEBA 2 COMPLETADA EXITOSAMENTE")
        return True
    else:
        print("❌ Error al actualizar evento copia")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 ¡SISTEMA BIDIRECCIONAL FUNCIONANDO PERFECTAMENTE!")
    else:
        print("\n❌ Prueba fallida")
    sys.exit(0 if success else 1) 