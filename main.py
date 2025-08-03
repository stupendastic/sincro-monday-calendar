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

def main():
    """Función principal de la aplicación."""
    print("Iniciando Sincronizador Stupendastic...")
    
    # Inicializar servicios
    google_service = get_calendar_service()
    if not google_service or not MONDAY_API_KEY:
        print("Error en la inicialización de servicios. Abortando.")
        return

    print("✅ Servicios de Google y Monday inicializados.")

    # Obtener los datos del tablero de Grabaciones usando la configuración
    print(f"Obteniendo datos del tablero de Monday con ID: {config.BOARD_ID_GRABACIONES}...")
    monday_data = get_monday_board_items(config.BOARD_ID_GRABACIONES, config.COLUMN_IDS)

    if monday_data:
        pretty_data = json.dumps(monday_data, indent=2)
        print("Datos recibidos de Monday:")
        print(pretty_data)
    else:
        print("No se pudieron obtener datos de Monday.")

    print("\nProceso terminado.")


if __name__ == "__main__":
    main()