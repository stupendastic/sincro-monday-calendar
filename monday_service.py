import os
import requests
import json
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

# --- Configuración de APIs ---
MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_API_URL = "https://api.monday.com/v2"
HEADERS = {"Authorization": MONDAY_API_KEY}
# --- Fin de la Configuración ---

def get_monday_user_directory():
    """
    Obtiene el directorio completo de usuarios de Monday.com.
    
    Returns:
        dict: Diccionario donde la clave es el nombre del usuario y el valor es su ID.
              Ejemplo: {'Arnau Admin': 1234567, 'Jordi Vas': 8901234}
    """
    query = """
    query {
        users {
            id
            name
            email
        }
    }
    """
    
    data = {'query': query}
    
    try:
        print("  -> Obteniendo directorio de usuarios de Monday.com...")
        response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error al obtener usuarios de Monday: {response_data['errors']}")
            return None
        
        users = response_data.get('data', {}).get('users', [])
        user_directory = {}
        
        for user in users:
            user_id = user.get('id')
            user_name = user.get('name')
            if user_id and user_name:
                user_directory[user_name] = user_id
        
        print(f"  ✅ Directorio de usuarios obtenido: {len(user_directory)} usuarios encontrados.")
        return user_directory
        
    except Exception as e:
        print(f"❌ Error al obtener directorio de usuarios de Monday: {e}")
        return None

def get_single_item_details(item_id):
    """Obtiene todos los detalles de un item específico de Monday.com."""
    
    # Query completa para obtener todos los detalles de un item
    query = f"""
    query {{
        items(ids: [{item_id}]) {{
            id
            name
            group {{
                title
            }}
            updates {{
                body
            }}
            column_values(ids: ["personas1", "fecha56", "color", "bien_estado_volcado", "men__desplegable2", "ubicaci_n", "link_mktcbghq", "lookup_mkteg56h", "lookup_mktetkek", "lookup_mkte8baj", "lookup_mkte7deh", "text_mktfdhm3", "text_mktefg5"]) {{
                id
                text
                value
                type
                ... on MirrorValue {{
                    display_value
                }}
            }}
        }}
    }}
    """
    
    data = {'query': query}
    
    try:
        response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"Error al obtener detalles del item {item_id}: {response_data['errors']}")
            return None
        
        items = response_data.get('data', {}).get('items', [])
        if items:
            return items[0]  # Devolver el primer (y único) item
        else:
            print(f"No se encontró el item {item_id}")
            return None
            
    except Exception as e:
        print(f"Error al obtener detalles del item {item_id}: {e}")
        return None

def update_monday_column(item_id, board_id, column_id, value):
    """Actualiza una columna de texto en Monday.com con un valor específico."""
    
    mutation = """
    mutation ($boardId: Int!, $itemId: Int!, $columnId: String!, $value: String!) {
        change_simple_column_value(board_id: $boardId, item_id: $itemId, column_id: $columnId, value: $value) {
            id
        }
    }
    """
    
    variables = {
        "boardId": board_id,
        "itemId": int(item_id),
        "columnId": column_id,
        "value": value
    }
    
    data = {'query': mutation, 'variables': variables}
    
    # Mensaje de depuración antes de la llamada
    print(f"> Escribiendo en Monday... | Item: {item_id} | Columna: {column_id} | Valor: {value}")
    
    try:
        response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
        response.raise_for_status()
        result = response.json()
        
        if 'errors' in result:
            print(f"❌ ERROR al escribir en Monday: {result['errors']}")
            return False
        
        print(f"✅ Escritura en Monday OK.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR al escribir en Monday: {e}")
        return False 