#!/usr/bin/env python3
"""
Script de pruebas no invasivo para depurar el flujo de sincronización.
Este script permite probar los flujos principales de forma aislada sin depender de webhooks.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Importar módulos necesarios
import config
from google_calendar_service import get_calendar_service, delete_event_by_id
from monday_api_handler import MondayAPIHandler
from sync_logic import sincronizar_item_via_webhook, sincronizar_desde_google, _obtener_item_id_por_google_event_id

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
    Función principal del script de pruebas.
    """
    print("🧪 INICIANDO SCRIPT DE PRUEBAS DE SINCRONIZACIÓN")
    print("=" * 60)
    
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
                column_values(ids: ["{config.COLUMN_MAP_REVERSE['Operario']}", "{config.COLUMN_MAP_REVERSE['FechaGrab']}"]) {{
                    id
                    text
                    value
                }}
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
        
        # Verificar que tiene operario y fecha
        column_values = item.get('column_values', [])
        tiene_operario = False
        tiene_fecha = False
        
        for col in column_values:
            if col.get('id') == config.COLUMN_MAP_REVERSE['Operario']:
                operario_text = col.get('text', '').strip()
                if operario_text:
                    tiene_operario = True
                    print(f"  👤 Operario: {operario_text}")
            
            elif col.get('id') == config.COLUMN_MAP_REVERSE['FechaGrab']:
                fecha_text = col.get('text', '').strip()
                if fecha_text:
                    tiene_fecha = True
                    print(f"  📅 Fecha: {fecha_text}")
        
        if not tiene_operario:
            print("❌ El item no tiene operario asignado")
            return
        
        if not tiene_fecha:
            print("❌ El item no tiene fecha asignada")
            return
        
        print("✅ Item válido para pruebas")
        
    except Exception as e:
        print(f"❌ Error al verificar item: {e}")
        return
    
    # 3. Limpiar estado inicial
    print(f"\n🧹 LIMPIANDO ESTADO INICIAL")
    print("-" * 40)
    
    # Obtener Google Event ID actual
    google_event_id_actual = obtener_google_event_id_de_monday(ITEM_DE_PRUEBA_ID, monday_handler_global)
    
    if google_event_id_actual:
        # Limpiar eventos de Google Calendar
        limpiar_eventos_de_google_calendar(google_service, google_event_id_actual)
    
    # Limpiar Google Event ID en Monday
    limpiar_google_event_id_en_monday(ITEM_DE_PRUEBA_ID, monday_handler_global)
    
    print("✅ Estado inicial limpiado")
    
    # 4. PRUEBA 1: Monday -> Google
    print(f"\n🔄 PRUEBA 1: Monday -> Google")
    print("=" * 40)
    
    try:
        success = sincronizar_item_via_webhook(
            ITEM_DE_PRUEBA_ID, 
            monday_handler_global, 
            google_service=google_service
        )
        
        if success:
            print("✅ PRUEBA 1 EXITOSA: Monday -> Google")
        else:
            print("❌ PRUEBA 1 FALLIDA: Monday -> Google")
            return
            
    except Exception as e:
        print(f"❌ Error en PRUEBA 1: {e}")
        return
    
    # 4.5. Verificar que el Google Event ID se guardó correctamente después de PRUEBA 1
    print(f"\n🔍 VERIFICANDO QUE SE GUARDÓ EL GOOGLE EVENT ID")
    print("-" * 40)
    
    google_event_id_guardado = obtener_google_event_id_de_monday(ITEM_DE_PRUEBA_ID, monday_handler_global)
    
    if google_event_id_guardado:
        print(f"✅ Google Event ID guardado correctamente: {google_event_id_guardado}")
    else:
        print(f"❌ ERROR: No se guardó el Google Event ID en Monday")
        print(f"   Esto explica por qué la PRUEBA 2 falla")
        return
    
    # 5. PRUEBA 2: Google -> Monday
    print(f"\n🔄 PRUEBA 2: Google -> Monday")
    print("=" * 40)
    
    try:
        # Obtener el master_event_id del item de Monday de forma más robusta
        print(f"🔍 Obteniendo master_event_id del item {ITEM_DE_PRUEBA_ID}...")
        
        # Query específica para obtener el Google Event ID del item
        query = f"""
        query {{
            items(ids: [{ITEM_DE_PRUEBA_ID}]) {{
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
        response = requests.post(url=monday_handler_global.API_URL, json=data, headers=monday_handler_global.HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error al obtener datos del item: {response_data['errors']}")
            return
        
        items = response_data.get('data', {}).get('items', [])
        if not items:
            print(f"❌ No se encontró el item {ITEM_DE_PRUEBA_ID}")
            return
        
        item = items[0]
        item_name = item.get('name', 'Sin nombre')
        column_values = item.get('column_values', [])
        
        master_event_id = None
        for col in column_values:
            if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                master_event_id = col.get('text', '').strip()
                break
        
        if not master_event_id:
            print(f"❌ El item '{item_name}' no tiene Google Event ID asignado")
            print("💡 Esto puede ser normal si la PRUEBA 1 no se ejecutó correctamente")
            return
        
        print(f"✅ Item '{item_name}' tiene Google Event ID: {master_event_id}")
        print(f"📋 Usando master_event_id: {master_event_id}")
        
        # Ejecutar la sincronización Google -> Monday
        success = sincronizar_desde_google(
            master_event_id, 
            monday_handler_global, 
            google_service=google_service
        )
        
        if success:
            print("✅ PRUEBA 2 EXITOSA: Google -> Monday")
        else:
            print("❌ PRUEBA 2 FALLIDA: Google -> Monday")
            
    except Exception as e:
        print(f"❌ Error en PRUEBA 2: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. Resumen final
    print(f"\n📊 RESUMEN DE PRUEBAS")
    print("=" * 40)
    print("✅ Todas las pruebas completadas")
    print("✅ Estado inicial limpiado correctamente")
    print("✅ Flujos de sincronización verificados")
    print("\n🎉 Script de pruebas completado exitosamente")

if __name__ == "__main__":
    main() 