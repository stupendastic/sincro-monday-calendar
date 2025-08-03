import os
import requests
from dotenv import load_dotenv
import json # Para imprimir la respuesta de forma legible

# Carga las variables del archivo .env (tu clave de API de Monday)
load_dotenv()

# --- Configuración ---
API_KEY = os.getenv("MONDAY_API_KEY")
API_URL = "https://api.monday.com/v2"
HEADERS = {"Authorization": API_KEY}
# --- Fin de la Configuración ---

def probar_conexion_monday():
    """
    Función para hacer una consulta simple a Monday y verificar la conexión.
    Esta consulta pide la lista de todos los tableros en tu cuenta.
    """
    # Esta es la "pregunta" que le hacemos a Monday en su idioma (GraphQL)
    query = '{ boards { id, name } }'
    data = {'query': query}

    print("Intentando conectar con Monday.com...")
    
    try:
        # Hacemos la llamada a la API
        response = requests.post(url=API_URL, json=data, headers=HEADERS)
        response.raise_for_status() # Lanza un error si la respuesta es mala (ej: 401, 404)

        # Imprimimos la respuesta de forma bonita
        print("¡Conexión exitosa!")
        print("Tus tableros son:")
        pretty_response = json.dumps(response.json(), indent=2)
        print(pretty_response)

    except requests.exceptions.HTTPError as err:
        print(f"Error de HTTP: {err}")
        print("Verifica que tu clave de API en el archivo .env sea correcta.")
    except Exception as err:
        print(f"Ocurrió un error inesperado: {err}")


# Esto hace que la función se ejecute cuando corremos el archivo
if __name__ == "__main__":
    probar_conexion_monday()