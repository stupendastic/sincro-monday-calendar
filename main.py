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
    """Obtiene todos los elementos de un tablero con sus columnas específicas."""
    
    # Convierte la lista de IDs de columnas a un string para la consulta
    ids_string = '", "'.join(column_ids)

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
    """
    # Manejo seguro de updates
    updates = item.get('updates', [])
    update_body = updates[0].get('body', '') if updates else ''
    
    parsed_item = {
        'id': item.get('id'),
        'name': item.get('name'),
        'update_body': update_body
    }

    # Creamos un diccionario para acceder fácilmente a los valores por su ID
    column_values = {cv['id']: cv for cv in item['column_values']}

    # --- Extraemos cada valor de forma segura ---
    # Si una columna no existe o está vacía, se asignará 'None' o un valor por defecto.

    # Operario (Columna de Persona)
    operario_val = column_values.get(config.COLUMN_MAP_REVERSE['Operario'])
    if operario_val and operario_val.get('value'):
        # El valor es un JSON, lo cargamos
        value_data = json.loads(operario_val['value'])
        # Nos quedamos con el email de la primera persona asignada
        if value_data.get('personsAndTeams'):
            parsed_item['operario_email'] = value_data['personsAndTeams'][0].get('email')
        else:
            parsed_item['operario_email'] = None
    else:
        parsed_item['operario_email'] = None

    # Fecha de Grabación (Columna de Fecha)
    fecha_val = column_values.get(config.COLUMN_MAP_REVERSE['FechaGrab'])
    if fecha_val and fecha_val.get('value'):
        value_data = json.loads(fecha_val['value'])
        parsed_item['fecha_inicio'] = f"{value_data.get('date')}T{value_data.get('time', '09:00:00')}"
        parsed_item['fecha_fin'] = f"{value_data.get('date')}T{value_data.get('time', '18:00:00')}" # Asumimos un horario, lo mejoraremos luego
    else:
        parsed_item['fecha_inicio'] = None
        parsed_item['fecha_fin'] = None
        
    # El resto de columnas son de texto simple
    for key_legible, col_id in config.COLUMN_MAP_REVERSE.items():
        if key_legible not in parsed_item: # Evitamos sobreescribir los ya procesados
             parsed_item[key_legible.lower()] = column_values.get(col_id, {}).get('text', '')

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