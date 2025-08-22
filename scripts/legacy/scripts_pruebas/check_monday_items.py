#!/usr/bin/env python3
"""
Script para verificar qué items existen en Monday con Google Event IDs.
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

def check_monday_items():
    """
    Verifica qué items existen en Monday con Google Event IDs.
    """
    print("🔍 VERIFICANDO ITEMS EN MONDAY.COM")
    print("=" * 50)
    
    # Inicializar Monday API Handler
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    # Consulta para obtener todos los items del board
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
        
        items_con_google_id = 0
        
        for item in items:
            item_id = item.get('id')
            item_name = item.get('name', 'Sin nombre')
            column_values = item.get('column_values', [])
            
            google_event_id = None
            for col in column_values:
                if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                    google_event_id = col.get('text', '').strip()
                    break
            
            if google_event_id:
                items_con_google_id += 1
                print(f"✅ Item {item_id}: '{item_name}' -> Google Event ID: {google_event_id}")
            else:
                print(f"ℹ️  Item {item_id}: '{item_name}' -> Sin Google Event ID")
        
        print()
        print(f"📊 Resumen:")
        print(f"  - Total de items: {len(items)}")
        print(f"  - Items con Google Event ID: {items_con_google_id}")
        print(f"  - Items sin Google Event ID: {len(items) - items_con_google_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_monday_items() 