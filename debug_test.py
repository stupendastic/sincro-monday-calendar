#!/usr/bin/env python3
"""
Script de debug para verificar la búsqueda de items en Monday.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Importar módulos necesarios
import config
from monday_api_handler import MondayAPIHandler

# Cargar variables de entorno
load_dotenv()

def debug_search():
    """
    Debug de la búsqueda de items en Monday.
    """
    print("🔍 DEBUG DE BÚSQUEDA EN MONDAY")
    print("=" * 50)
    
    # Inicializar Monday API Handler
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    # Google Event ID de prueba
    google_event_id = "7h0ngvp61cbfaprs1d8lj8jung"
    
    print(f"📋 Configuración:")
    print(f"  - BOARD_ID_GRABACIONES: {config.BOARD_ID_GRABACIONES}")
    print(f"  - COL_GOOGLE_EVENT_ID: {config.COL_GOOGLE_EVENT_ID}")
    print(f"  - Google Event ID: {google_event_id}")
    print()
    
    # Query para obtener todos los items del board
    query = f"""
    query {{
        boards(ids: {config.BOARD_ID_GRABACIONES}) {{
            items_page {{
                items {{
                    id
                    name
                    column_values(ids: ["{config.COL_GOOGLE_EVENT_ID}"]) {{
                        id
                        text
                        value
                    }}
                }}
            }}
        }}
    }}
    """
    
    data = {'query': query}
    
    try:
        print(f"📋 Obteniendo items del board {config.BOARD_ID_GRABACIONES}...")
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error al obtener items: {response_data['errors']}")
            return
        
        # Extraer items de la respuesta
        boards = response_data.get('data', {}).get('boards', [])
        if not boards:
            print(f"❌ No se encontró el board {config.BOARD_ID_GRABACIONES}")
            return
        
        items_page = boards[0].get('items_page', {})
        items = items_page.get('items', [])
        
        print(f"📊 Total de items encontrados: {len(items)}")
        print()
        
        # Buscar items que tengan el Google Event ID específico
        items_con_google_id = []
        
        for item in items:
            item_id = item.get('id')
            item_name = item.get('name', 'Sin nombre')
            column_values = item.get('column_values', [])
            
            for col in column_values:
                if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                    text_value = col.get('text', '').strip()
                    if text_value:
                        items_con_google_id.append({
                            'id': item_id,
                            'name': item_name,
                            'google_event_id': text_value
                        })
                        print(f"✅ Item {item_id}: '{item_name}' -> Google Event ID: {text_value}")
                    else:
                        print(f"ℹ️  Item {item_id}: '{item_name}' -> Columna vacía")
                    break
        
        print()
        print(f"📊 Resumen:")
        print(f"  - Total de items: {len(items)}")
        print(f"  - Items con Google Event ID: {len(items_con_google_id)}")
        
        # Buscar específicamente el Google Event ID que estamos buscando
        item_encontrado = None
        for item_info in items_con_google_id:
            if item_info['google_event_id'] == google_event_id:
                item_encontrado = item_info
                break
        
        if item_encontrado:
            print(f"✅ ENCONTRADO: Item {item_encontrado['id']} '{item_encontrado['name']}' tiene el Google Event ID buscado")
        else:
            print(f"❌ NO ENCONTRADO: No hay ningún item con Google Event ID '{google_event_id}'")
            print(f"   Google Event IDs disponibles:")
            for item_info in items_con_google_id:
                print(f"     - {item_info['google_event_id']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_search() 