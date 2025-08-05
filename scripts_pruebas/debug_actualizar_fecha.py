#!/usr/bin/env python3
"""
Script de debug específico para la función _actualizar_fecha_en_monday.
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Importar módulos necesarios
import config
from monday_api_handler import MondayAPIHandler

# Cargar variables de entorno
load_dotenv()

def debug_actualizar_fecha():
    """
    Debug específico de la función _actualizar_fecha_en_monday.
    """
    print("🔍 DEBUG DE _ACTUALIZAR_FECHA_EN_MONDAY")
    print("=" * 50)
    
    # Inicializar Monday API Handler
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    # Simular los parámetros que recibe la función
    google_event_id = "41kaam95f67emv93agmcvmvgro"
    nueva_fecha_inicio = {'dateTime': '2025-08-19T10:30:00+02:00', 'timeZone': 'Europe/Madrid'}
    nueva_fecha_fin = {'dateTime': '2025-08-19T11:30:00+02:00', 'timeZone': 'Europe/Madrid'}
    
    print(f"📋 Parámetros de prueba:")
    print(f"  - Google Event ID: {google_event_id}")
    print(f"  - Nueva fecha inicio: {nueva_fecha_inicio}")
    print(f"  - Nueva fecha fin: {nueva_fecha_fin}")
    print()
    
    # 1. Buscar el item en Monday.com
    print("🔍 PASO 1: Buscando item en Monday...")
    query = f"""
    query {{
        boards(ids: {config.BOARD_ID_GRABACIONES}) {{
            items_page {{
                items {{
                    id
                    name
                    board {{
                        id
                    }}
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
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error al buscar item: {response_data['errors']}")
            return
        
        boards = response_data.get('data', {}).get('boards', [])
        if not boards:
            print(f"❌ No se encontró el board {config.BOARD_ID_GRABACIONES}")
            return
        
        items_page = boards[0].get('items_page', {})
        items = items_page.get('items', [])
        if not items:
            print(f"❌ No se encontraron items")
            return
        
        # Buscar el item específico
        item_encontrado = None
        for item in items:
            column_values = item.get('column_values', [])
            for col in column_values:
                if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                    text_value = col.get('text', '').strip()
                    if text_value == google_event_id:
                        item_encontrado = item
                        break
            if item_encontrado:
                break
        
        if not item_encontrado:
            print(f"❌ No se encontró item con Google Event ID: {google_event_id}")
            return
        
        item_id = item_encontrado.get('id')
        board_id = item_encontrado.get('board', {}).get('id')
        item_name = item_encontrado.get('name')
        
        print(f"✅ Item encontrado: '{item_name}' (ID: {item_id}, Board: {board_id})")
        
        # 2. Procesar las fechas
        print("\n🔍 PASO 2: Procesando fechas...")
        
        if 'dateTime' in nueva_fecha_inicio:
            date_time_str = nueva_fecha_inicio['dateTime']
            if date_time_str.endswith('Z'):
                date_time_str = date_time_str[:-1] + '+00:00'
            
            inicio_dt = datetime.fromisoformat(date_time_str)
            fecha_monday = inicio_dt.strftime("%Y-%m-%d")
            hora_monday = inicio_dt.strftime("%H:%M:%S")
            es_evento_con_hora = True
            
        elif 'date' in nueva_fecha_inicio:
            fecha_monday = nueva_fecha_inicio['date']
            hora_monday = None
            es_evento_con_hora = False
            
        else:
            print(f"❌ Formato de fecha no reconocido: {nueva_fecha_inicio}")
            return
        
        print(f"  -> Fecha procesada: {fecha_monday}")
        print(f"  -> Hora procesada: {hora_monday}")
        print(f"  -> Es evento con hora: {es_evento_con_hora}")
        
        # 3. Construir valor para Monday
        print("\n🔍 PASO 3: Construyendo valor para Monday...")
        
        if hora_monday:
            monday_value = {"date": fecha_monday, "time": hora_monday}
        else:
            monday_value = {"date": fecha_monday}
        
        print(f"  -> Valor para Monday: {monday_value}")
        print(f"  -> Tipo de valor: {type(monday_value)}")
        
        # 4. Intentar actualizar
        print("\n🔍 PASO 4: Intentando actualizar...")
        
        try:
            success = monday_handler.update_column_value(
                item_id,
                board_id,
                config.COL_FECHA_GRAB,
                monday_value,
                'date'
            )
            
            if success:
                print(f"✅ ÉXITO: Actualización completada")
            else:
                print(f"❌ FALLO: Actualización fallida")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_actualizar_fecha() 