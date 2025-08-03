import os
import requests
import json
from dotenv import load_dotenv

# Importamos nuestros módulos locales
import config  # Importa nuestro nuevo archivo de configuración
from google_calendar_service import get_calendar_service

# Carga las variables del archivo .env
load_dotenv()

# --- Configuración de APIs ---
MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_API_URL = "https://api.monday.com/v2"
HEADERS = {"Authorization": MONDAY_API_KEY}
# --- Fin de la Configuración ---

def get_monday_board_items(board_id, column_ids):
    """Obtiene todos los elementos de un tablero, usando fragmentos en línea para columnas reflejo."""
    
    ids_string = '", "'.join(column_ids)

    # ESTA ES LA QUERY MEJORADA
    query = f"""
    query {{
        boards(ids: {board_id}) {{
            items_page (limit: 100) {{
                items {{
                    id
                    name
                    updates(limit: 1) {{
                        body
                    }}
                    column_values(ids: ["{ids_string}"]) {{
                        id
                        text
                        value
                        type  # Pedimos el tipo para saber cómo tratarlo
                        ... on MirrorValue {{
                            display_value # ¡La clave para las columnas reflejo!
                        }}
                    }}
                }}
            }}
        }}
    }}
    """
    data = {'query': query}
    
    try:
        response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error al obtener los elementos de Monday: {e}")
        return None


def parse_monday_item(item):
    """
    Toma un 'item' de la respuesta de Monday y lo convierte en un diccionario limpio.
    Ahora entiende las columnas de tipo 'mirror' (reflejo).
    """
    parsed_item = {
        'id': item.get('id'),
        'name': item.get('name'),
        'update_body': item.get('updates', [{}])[0].get('body', '') if item.get('updates') else ''
    }

    # Creamos un diccionario para acceder fácilmente a los valores por su ID
    column_values_by_id = {cv['id']: cv for cv in item['column_values']}

    # Recorremos nuestro mapa de columnas de config.py
    for col_name, col_id in config.COLUMN_MAP_REVERSE.items():
        col_data = column_values_by_id.get(col_id)
        
        if not col_data:
            parsed_item[col_name.lower()] = None
            continue

        # --- Lógica de Procesamiento por Tipo ---
        col_type = col_data.get('type')

        if col_type == 'mirror':
            # ¡BINGO! Si es una columna reflejo, usamos display_value.
            parsed_item[col_name.lower()] = col_data.get('display_value')
        
        elif col_name == 'Operario': # Columna de Persona
            value_data = json.loads(col_data['value']) if col_data.get('value') else {}
            persons = value_data.get('personsAndTeams', [])
            # Monday.com no proporciona email en los datos de persona
            parsed_item['operario_email'] = None  # No disponible en Monday.com
            parsed_item['operario'] = col_data.get('text') # El nombre visible ya viene en 'text'

        elif col_name == 'FechaGrab': # Columna de Fecha
            if col_data.get('value'):
                value_data = json.loads(col_data['value'])
                # Asumimos un horario por defecto, luego lo podemos hacer más inteligente
                parsed_item['fecha_inicio'] = f"{value_data.get('date')}T09:00:00"
                parsed_item['fecha_fin'] = f"{value_data.get('date')}T18:00:00"
            else:
                parsed_item['fecha_inicio'] = None
                parsed_item['fecha_fin'] = None

        else: # Para el resto de columnas, usamos el campo 'text'
            parsed_item[col_name.lower()] = col_data.get('text', '')

    return parsed_item

def main():
    """Función principal de la aplicación."""
    print("Iniciando Sincronizador Stupendastic...")
    
    # Inicializar servicios
    google_service = get_calendar_service()
    if not google_service or not MONDAY_API_KEY:
        print("Error en la inicialización de servicios. Abortando.")
        return

    print("✅ Servicios de Google y Monday inicializados.")

    # Obtener los datos del tablero de Grabaciones
    print(f"Obteniendo datos del tablero de Monday con ID: {config.BOARD_ID_GRABACIONES}...")
    monday_response = get_monday_board_items(config.BOARD_ID_GRABACIONES, config.COLUMN_IDS)

    if not monday_response or 'errors' in monday_response:
        print("Error al obtener datos de Monday:", monday_response.get('errors'))
        return

    # Extraemos la lista de items de la respuesta
    items = monday_response.get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
    
    if not items:
        print("No se encontraron elementos en el tablero.")
        return

    print(f"Se encontraron {len(items)} elemento(s). Procesando...")
    print("-" * 40)

    # Recorremos cada item, lo procesamos y lo imprimimos
    for item in items:
        item_procesado = parse_monday_item(item)
        print(json.dumps(item_procesado, indent=2))
        print("-" * 20)

    print("\nProceso terminado.")

if __name__ == "__main__":
    main()