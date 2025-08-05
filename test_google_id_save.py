#!/usr/bin/env python3
"""
Script para probar si el Google Event ID se guarda correctamente en Monday.
"""

import os
import json
import requests
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def test_google_id_save():
    """Prueba si se puede guardar un Google Event ID en Monday."""
    
    # Inicializar Monday handler
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    # Item de prueba
    test_item_id = 9733398727
    test_google_id = "test_google_id_12345"
    
    print(f"🧪 Probando guardado de Google Event ID")
    print(f"   Item ID: {test_item_id}")
    print(f"   Google Event ID: {test_google_id}")
    print(f"   Board ID: {config.BOARD_ID_GRABACIONES}")
    print(f"   Column ID: {config.COL_GOOGLE_EVENT_ID}")
    
    # Intentar guardar el Google Event ID
    success = monday_handler.update_column_value(
        test_item_id,
        config.BOARD_ID_GRABACIONES,
        config.COL_GOOGLE_EVENT_ID,
        test_google_id,
        'text'
    )
    
    if success:
        print(f"✅ Google Event ID guardado exitosamente")
        
        # Verificar que se guardó correctamente
        print(f"🔍 Verificando que se guardó correctamente...")
        
        query = f"""
        query {{
            items(ids: [{test_item_id}]) {{
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
        
        if response.status_code == 200:
            response_data = response.json()
            items = response_data.get('data', {}).get('items', [])
            
            if items:
                item = items[0]
                column_values = item.get('column_values', [])
                
                for col in column_values:
                    if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                        saved_value = col.get('text', '').strip()
                        print(f"   Valor guardado: '{saved_value}'")
                        print(f"   Valor esperado: '{test_google_id}'")
                        
                        if saved_value == test_google_id:
                            print(f"✅ ¡VERIFICACIÓN EXITOSA! El Google Event ID se guardó correctamente")
                        else:
                            print(f"❌ ¡ERROR! El valor guardado no coincide")
                        break
                else:
                    print(f"❌ No se encontró la columna {config.COL_GOOGLE_EVENT_ID}")
            else:
                print(f"❌ No se encontró el item {test_item_id}")
        else:
            print(f"❌ Error al verificar: {response.status_code}")
            print(f"   Response: {response.text}")
    else:
        print(f"❌ Error al guardar Google Event ID")

if __name__ == "__main__":
    test_google_id_save() 