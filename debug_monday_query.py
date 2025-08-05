#!/usr/bin/env python3
"""
Script de debug para investigar el problema con la consulta a Monday.com.
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

def debug_monday_query():
    """
    Debug de la consulta a Monday.com para identificar el problema.
    """
    print("🔍 DEBUG DE CONSULTA A MONDAY.COM")
    print("=" * 50)
    
    # Inicializar Monday API Handler
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    # Google Event ID de prueba
    google_event_id = "ijhp0rh2vj05dgl0v4llifid30"
    
    print(f"📋 Configuración:")
    print(f"  - BOARD_ID_GRABACIONES: {config.BOARD_ID_GRABACIONES}")
    print(f"  - COL_GOOGLE_EVENT_ID: {config.COL_GOOGLE_EVENT_ID}")
    print(f"  - Google Event ID: {google_event_id}")
    print()
    
    # Método 1: Usando items_by_column_values (el que está fallando)
    print("🔍 MÉTODO 1: items_by_column_values")
    print("-" * 40)
    
    column_value = json.dumps({"text": google_event_id})
    query1 = f"""
    query {{
        items_by_column_values(board_id: {config.BOARD_ID_GRABACIONES}, column_id: "{config.COL_GOOGLE_EVENT_ID}", column_value: "{column_value}") {{
            id
            name
        }}
    }}
    """
    
    data1 = {'query': query1}
    
    print(f"Query enviada:")
    print(json.dumps(data1, indent=2))
    print()
    
    try:
        response1 = requests.post(url=monday_handler.API_URL, json=data1, headers=monday_handler.HEADERS)
        print(f"Status Code: {response1.status_code}")
        print(f"Response Headers: {dict(response1.headers)}")
        print(f"Response Body: {response1.text}")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
    
    # Método 2: Usando items con filtro manual
    print("🔍 MÉTODO 2: items con filtro manual")
    print("-" * 40)
    
    query2 = f"""
    query {{
        items(board_id: {config.BOARD_ID_GRABACIONES}, limit: 100) {{
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
    
    data2 = {'query': query2}
    
    print(f"Query enviada:")
    print(json.dumps(data2, indent=2))
    print()
    
    try:
        response2 = requests.post(url=monday_handler.API_URL, json=data2, headers=monday_handler.HEADERS)
        print(f"Status Code: {response2.status_code}")
        
        if response2.status_code == 200:
            response_data2 = response2.json()
            print(f"Response Body: {json.dumps(response_data2, indent=2)}")
            
            # Buscar items que tengan el Google Event ID
            items = response_data2.get('data', {}).get('items', [])
            print(f"\n📋 Items encontrados: {len(items)}")
            
            for item in items:
                column_values = item.get('column_values', [])
                for col in column_values:
                    if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                        text_value = col.get('text', '').strip()
                        if text_value:
                            print(f"  ✅ Item {item.get('id')} '{item.get('name')}' tiene Google Event ID: {text_value}")
                        else:
                            print(f"  ℹ️  Item {item.get('id')} '{item.get('name')}' tiene columna vacía")
        else:
            print(f"Response Body: {response2.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
    
    # Método 3: Verificar la estructura de column_value
    print("🔍 MÉTODO 3: Diferentes formatos de column_value")
    print("-" * 40)
    
    test_formats = [
        json.dumps({"text": google_event_id}),
        json.dumps({"text": google_event_id, "additional_info": ""}),
        google_event_id,
        f'"{google_event_id}"'
    ]
    
    for i, column_value in enumerate(test_formats, 1):
        print(f"\n📋 Formato {i}: {column_value}")
        
        query3 = f"""
        query {{
            items_by_column_values(board_id: {config.BOARD_ID_GRABACIONES}, column_id: "{config.COL_GOOGLE_EVENT_ID}", column_value: "{column_value}") {{
                id
                name
            }}
        }}
        """
        
        data3 = {'query': query3}
        
        try:
            response3 = requests.post(url=monday_handler.API_URL, json=data3, headers=monday_handler.HEADERS)
            print(f"  Status: {response3.status_code}")
            if response3.status_code != 200:
                print(f"  Error: {response3.text}")
        except Exception as e:
            print(f"  ❌ Exception: {e}")

if __name__ == "__main__":
    debug_monday_query() 