#!/usr/bin/env python3
"""
Script de limpieza para preparar el estado antes de las pruebas.
Este script limpia completamente el estado del item de prueba.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Importar módulos necesarios
import config
from google_calendar_service import get_calendar_service, delete_event_by_id
from monday_api_handler import MondayAPIHandler

# Cargar variables de entorno
load_dotenv()

# ID del item de prueba en Monday.com
ITEM_DE_PRUEBA_ID = 9733398727

def limpiar_google_event_id_en_monday(item_id, monday_handler):
    """
    Limpia el Google Event ID del item en Monday.com.
    Solo modifica la columna de Google Event ID, no borra nada más.
    """
    print(f"🧹 Limpiando Google Event ID del item {item_id}...")
    
    try:
        # Actualizar la columna de Google Event ID con valor vacío
        success = monday_handler.update_column_value(
            item_id,
            config.BOARD_ID_GRABACIONES,
            config.COL_GOOGLE_EVENT_ID,
            "",
            'text'
        )
        
        if success:
            print(f"✅ Google Event ID limpiado exitosamente del item {item_id}")
            return True
        else:
            print(f"❌ Error al limpiar Google Event ID del item {item_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error inesperado al limpiar Google Event ID: {e}")
        return False

def obtener_google_event_id_de_monday(item_id, monday_handler):
    """
    Obtiene el Google Event ID del item en Monday.com.
    """
    print(f"🔍 Obteniendo Google Event ID del item {item_id}...")
    
    try:
        # Query para obtener el Google Event ID
        query = f"""
        query {{
            items(ids: [{item_id}]) {{
                id
                name
                column_values(ids: ["{config.COL_GOOGLE_EVENT_ID}"]) {{
                    id
                    text
                    value
                }}
            }}
        }}
        """
        
        data = {'query': query}
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error al obtener Google Event ID: {response_data['errors']}")
            return None
        
        items = response_data.get('data', {}).get('items', [])
        if not items:
            print(f"❌ No se encontró el item {item_id}")
            return None
        
        item = items[0]
        column_values = item.get('column_values', [])
        
        for col in column_values:
            if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                google_event_id = col.get('text', '').strip()
                if google_event_id:
                    print(f"✅ Google Event ID encontrado: {google_event_id}")
                    return google_event_id
                else:
                    print(f"ℹ️  Item {item_id} no tiene Google Event ID asignado")
                    return None
        
        print(f"ℹ️  Item {item_id} no tiene columna de Google Event ID")
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener Google Event ID: {e}")
        return None

def limpiar_eventos_de_google_calendar(google_service, master_event_id):
    """
    Limpia todos los eventos relacionados con el master_event_id de Google Calendar.
    """
    print(f"🧹 Limpiando eventos de Google Calendar para master_event_id: {master_event_id}")
    
    try:
        # Lista de calendarios donde buscar y eliminar eventos
        calendarios_a_limpiar = [config.MASTER_CALENDAR_ID, config.UNASSIGNED_CALENDAR_ID]
        
        # Añadir calendarios de filmmakers
        for perfil in config.FILMMAKER_PROFILES:
            if perfil.get('calendar_id'):
                calendarios_a_limpiar.append(perfil['calendar_id'])
        
        eventos_eliminados = 0
        
        for calendar_id in calendarios_a_limpiar:
            try:
                # Buscar eventos con el master_event_id en extended properties
                events_result = google_service.events().list(
                    calendarId=calendar_id,
                    timeMin=None,
                    maxResults=100,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                for event in events:
                    # Verificar si el evento tiene el master_event_id en extended properties
                    extended_props = event.get('extendedProperties', {})
                    private_props = extended_props.get('private', {})
                    event_master_id = private_props.get('master_event_id')
                    
                    # También verificar si el evento es el maestro mismo
                    event_id = event.get('id')
                    
                    if event_master_id == master_event_id or event_id == master_event_id:
                        print(f"  🗑️  Eliminando evento '{event.get('summary', 'Sin título')}' del calendario {calendar_id}")
                        
                        success = delete_event_by_id(google_service, calendar_id, event_id)
                        if success:
                            eventos_eliminados += 1
                            print(f"    ✅ Evento eliminado exitosamente")
                        else:
                            print(f"    ❌ Error al eliminar evento")
                
            except Exception as e:
                print(f"  ⚠️  Error al procesar calendario {calendar_id}: {e}")
                continue
        
        print(f"✅ Limpieza completada. {eventos_eliminados} eventos eliminados")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza de Google Calendar: {e}")
        return False

def main():
    """
    Función principal del script de limpieza.
    """
    print("🧹 INICIANDO SCRIPT DE LIMPIEZA DE ESTADO")
    print("=" * 50)
    
    # 1. Inicializar servicios
    print("📡 Inicializando servicios...")
    google_service = get_calendar_service()
    if not google_service:
        print("❌ Error al inicializar Google Calendar service")
        return
    
    monday_handler_global = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    print("✅ Servicios inicializados correctamente")
    
    # 2. Verificar que el item de prueba existe
    print(f"\n🔍 Verificando item de prueba: {ITEM_DE_PRUEBA_ID}")
    try:
        query = f"""
        query {{
            items(ids: [{ITEM_DE_PRUEBA_ID}]) {{
                id
                name
            }}
        }}
        """
        
        data = {'query': query}
        response = requests.post(url=monday_handler_global.API_URL, json=data, headers=monday_handler_global.HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error al verificar item: {response_data['errors']}")
            return
        
        items = response_data.get('data', {}).get('items', [])
        if not items:
            print(f"❌ No se encontró el item {ITEM_DE_PRUEBA_ID}")
            return
        
        item = items[0]
        item_name = item.get('name', 'Sin nombre')
        print(f"✅ Item encontrado: '{item_name}'")
        
    except Exception as e:
        print(f"❌ Error al verificar item: {e}")
        return
    
    # 3. Limpiar estado
    print(f"\n🧹 LIMPIANDO ESTADO")
    print("-" * 30)
    
    # Obtener Google Event ID actual
    google_event_id_actual = obtener_google_event_id_de_monday(ITEM_DE_PRUEBA_ID, monday_handler_global)
    
    if google_event_id_actual:
        # Limpiar eventos de Google Calendar
        limpiar_eventos_de_google_calendar(google_service, google_event_id_actual)
    
    # Limpiar Google Event ID en Monday
    limpiar_google_event_id_en_monday(ITEM_DE_PRUEBA_ID, monday_handler_global)
    
    print("✅ Estado limpiado completamente")
    print("\n🎉 Script de limpieza completado exitosamente")
    print("💡 Ahora puedes ejecutar test_sync_flow.py para las pruebas")

if __name__ == "__main__":
    main() 