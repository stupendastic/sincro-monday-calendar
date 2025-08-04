import os
import requests
import json
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service, create_google_event, update_google_event

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
    """Obtiene todos los elementos de un tablero usando paginación - VERSIÓN LIGERA para filtrar."""
    
    # 1. Inicializar variables
    all_items = []
    cursor = None
    
    # Solo necesitamos las columnas mínimas para filtrar: FechaGrab y Operario
    filter_columns = ["fecha56", "personas1"]  # IDs de FechaGrab y Operario
    ids_string = '", "'.join(filter_columns)

    # 2. Bucle infinito para paginación
    while True:
        # 3. Query LIGERA para filtrar - solo datos mínimos
        query = f"""
        query($cursor: String) {{
            boards(ids: {board_id}) {{
                items_page(limit: 100, cursor: $cursor) {{
                    items {{
                        id
                        name
                        column_values(ids: ["{ids_string}"]) {{
                            id
                            text
                            value
                            type
                        }}
                    }}
                    cursor
                }}
            }}
        }}
        """
        
        # Variables para la petición
        variables = {}
        if cursor:
            variables['cursor'] = cursor
            
        data = {'query': query, 'variables': variables}
        
        try:
            # 4a. Hacer llamada a la API
            response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
            response.raise_for_status()
            response_data = response.json()
            
            # 4b. Añadir items de esta página a la lista
            items_page = response_data.get('data', {}).get('boards', [{}])[0].get('items_page', {})
            current_items = items_page.get('items', [])
            all_items.extend(current_items)
            
            # 4c. Extraer el nuevo cursor
            new_cursor = items_page.get('cursor')
            
            # 4d. Condición de salida
            if not new_cursor:
                break
                
            # 4e. Actualizar cursor para la siguiente iteración
            cursor = new_cursor
            
        except Exception as e:
            print(f"Error al obtener los elementos de Monday: {e}")
            return None
    
    # 5. Devolver la lista completa
    return {'data': {'boards': [{'items_page': {'items': all_items}}]}}


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


def parse_light_item_for_filtering(item):
    """Procesa un item ligero para extraer solo la información necesaria para filtrar."""
    
    parsed_item = {
        'id': item.get('id'),
        'name': item.get('name')
    }

    # Creamos un diccionario para acceder fácilmente a los valores por su ID
    column_values_by_id = {cv['id']: cv for cv in item['column_values']}

    # Solo procesamos las columnas necesarias para filtrar
    # FechaGrab
    fecha_col = column_values_by_id.get('fecha56')
    if fecha_col and fecha_col.get('value'):
        value_data = json.loads(fecha_col['value'])
        date_value = value_data.get('date')
        time_value = value_data.get('time')
        
        if time_value and time_value != 'null':
            parsed_item['fecha_inicio'] = f"{date_value}T{time_value}"
        else:
            parsed_item['fecha_inicio'] = date_value
    else:
        parsed_item['fecha_inicio'] = None

    # Operario
    operario_col = column_values_by_id.get('personas1')
    if operario_col:
        parsed_item['operario'] = operario_col.get('text')
        
        # Extraer email del operario
        if operario_col.get('value'):
            try:
                value_data = json.loads(operario_col['value'])
                persons = value_data.get('personsAndTeams', [])
                parsed_item['operario_email'] = persons[0].get('email') if persons else None
            except (json.JSONDecodeError, KeyError):
                parsed_item['operario_email'] = None
        else:
            parsed_item['operario_email'] = None
    else:
        parsed_item['operario'] = None
        parsed_item['operario_email'] = None

    return parsed_item


def parse_monday_item(item):
    """
    Toma un 'item' de la respuesta de Monday y lo convierte en un diccionario limpio.
    Ahora entiende las columnas de tipo 'mirror' (reflejo).
    """
    parsed_item = {
        'id': item.get('id'),
        'name': item.get('name'),
        'group_title': item.get('group', {}).get('title', 'N/A'),
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
            # El nombre visible del operario ya lo tenemos en el campo 'text'
            parsed_item['operario'] = col_data.get('text')
            
            # Ahora, extraemos el email del campo 'value'
            if col_data.get('value'):
                value_data = json.loads(col_data['value'])
                persons = value_data.get('personsAndTeams', [])
                # Nos quedamos con el email de la PRIMERA persona asignada (si existe)
                parsed_item['operario_email'] = persons[0].get('email') if persons else None
            else:
                parsed_item['operario_email'] = None

        elif col_name == 'FechaGrab': # Columna de Fecha
            if col_data.get('value'):
                value_data = json.loads(col_data['value'])
                date_value = value_data.get('date')
                time_value = value_data.get('time')
                
                if time_value and time_value != 'null':
                    # Si hay hora, usamos formato datetime ISO
                    parsed_item['fecha_inicio'] = f"{date_value}T{time_value}"
                    # Calculamos una hora después para la fecha fin
                    from datetime import datetime, timedelta
                    inicio_dt = datetime.fromisoformat(f"{date_value}T{time_value}")
                    fin_dt = inicio_dt + timedelta(hours=1)
                    parsed_item['fecha_fin'] = fin_dt.strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    # Si no hay hora, es evento de día completo
                    parsed_item['fecha_inicio'] = date_value
                    parsed_item['fecha_fin'] = date_value
            else:
                parsed_item['fecha_inicio'] = None
                parsed_item['fecha_fin'] = None

        elif col_name == 'Cliente': # Columna de Cliente
            parsed_item['cliente'] = col_data.get('text', '')
            
        elif col_name == 'LinkDropbox': # Columna de Link
            # Leer el campo 'value' que contiene un objeto JSON
            if col_data.get('value'):
                try:
                    value_data = json.loads(col_data['value'])
                    # Extraer la URL del objeto JSON
                    parsed_item['linkdropbox'] = value_data.get('url', '')
                except (json.JSONDecodeError, KeyError):
                    parsed_item['linkdropbox'] = ''
            else:
                parsed_item['linkdropbox'] = ''
                
        else: # Para el resto de columnas, usamos el campo 'text'
            parsed_item[col_name.lower()] = col_data.get('text', '')

    # Procesar contactos para crear fichas formateadas
    # Contactos de Obra
    contactos_obra = parsed_item.get('contactoobra', '').split(',') if parsed_item.get('contactoobra') else []
    telefonos_obra = parsed_item.get('telefonoobra', '').split(',') if parsed_item.get('telefonoobra') else []
    
    # Limpiar y emparejar contactos de obra
    contactos_obra = [c.strip() for c in contactos_obra if c.strip()]
    telefonos_obra = [t.strip() for t in telefonos_obra if t.strip()]
    
    # Crear fichas de contacto de obra
    fichas_obra = []
    for i, contacto in enumerate(contactos_obra):
        telefono = telefonos_obra[i] if i < len(telefonos_obra) else 'Sin teléfono'
        fichas_obra.append(f"- {contacto} (Tel: {telefono})")
    
    parsed_item['contacto_obra_formateado'] = '\n'.join(fichas_obra) if fichas_obra else 'No disponible'
    
    # Contactos Comerciales
    contactos_comercial = parsed_item.get('contactocomercial', '').split(',') if parsed_item.get('contactocomercial') else []
    telefonos_comercial = parsed_item.get('telefonocomercial', '').split(',') if parsed_item.get('telefonocomercial') else []
    
    # Limpiar y emparejar contactos comerciales
    contactos_comercial = [c.strip() for c in contactos_comercial if c.strip()]
    telefonos_comercial = [t.strip() for t in telefonos_comercial if t.strip()]
    
    # Crear fichas de contacto comercial
    fichas_comercial = []
    for i, contacto in enumerate(contactos_comercial):
        telefono = telefonos_comercial[i] if i < len(telefonos_comercial) else 'Sin teléfono'
        fichas_comercial.append(f"- {contacto} (Tel: {telefono})")
    
    parsed_item['contacto_comercial_formateado'] = '\n'.join(fichas_comercial) if fichas_comercial else 'No disponible'

    # Procesar todos los updates
    updates = item.get('updates', [])
    if updates:
        update_bodies = []
        for update in updates:
            body = update.get('body', '').strip()
            if body:
                update_bodies.append(body)
        
        if update_bodies:
            parsed_item['all_updates_html'] = '<hr>'.join(update_bodies)
        else:
            parsed_item['all_updates_html'] = 'Sin updates.'
    else:
        parsed_item['all_updates_html'] = 'Sin updates.'

    # Extraer el ID del evento de Google si existe
    google_event_col = column_values_by_id.get(config.COL_GOOGLE_EVENT_ID)
    if google_event_col:
        parsed_item['google_event_id'] = google_event_col.get('text', '').strip()
    else:
        parsed_item['google_event_id'] = None

    return parsed_item

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


def update_monday_date_column(item_id, board_id, column_id, date_value, time_value=None):
    """
    Actualiza una columna de fecha en Monday.com usando la regla de oro.
    
    Args:
        item_id: ID del item
        board_id: ID del tablero
        column_id: ID de la columna de fecha
        date_value: Fecha en formato "YYYY-MM-DD"
        time_value: Hora en formato "HH:MM:SS" (opcional)
    """
    
    # Crear el objeto de fecha según la regla de oro
    date_object = {"date": date_value}
    if time_value:
        date_object["time"] = time_value
    
    # Crear el objeto column_values principal
    column_values = {column_id: date_object}
    
    # Aplicar doble JSON.stringify según la regla de oro
    value_string = json.dumps(json.dumps(column_values))
    
    mutation = """
    mutation ($boardId: Int!, $itemId: Int!, $columnValues: String!) {
        change_multiple_column_values(board_id: $boardId, item_id: $itemId, column_values: $columnValues) {
            id
        }
    }
    """
    
    variables = {
        "boardId": board_id,
        "itemId": int(item_id),
        "columnValues": value_string
    }
    
    data = {'query': mutation, 'variables': variables}
    
    # Mensaje de depuración antes de la llamada
    print(f"> Escribiendo fecha en Monday... | Item: {item_id} | Columna: {column_id} | Fecha: {date_value} | Hora: {time_value}")
    
    try:
        response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
        response.raise_for_status()
        result = response.json()
        
        if 'errors' in result:
            print(f"❌ ERROR al escribir fecha en Monday: {result['errors']}")
            return False
        
        print(f"✅ Escritura de fecha en Monday OK.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR al escribir fecha en Monday: {e}")
        return False

def main():
    """Función principal de la aplicación."""
    print("Iniciando Sincronizador Stupendastic...")
    
    # 1. Inicializar contadores
    items_procesados = 0
    items_sincronizados = 0
    items_saltados = 0
    
    google_service = get_calendar_service()
    if not google_service or not MONDAY_API_KEY:
        print("Error en la inicialización de servicios. Abortando.")
        return

    print("✅ Servicios inicializados.")

    print(f"Obteniendo datos del tablero: {config.BOARD_ID_GRABACIONES}...")
    monday_response = get_monday_board_items(config.BOARD_ID_GRABACIONES, config.COLUMN_IDS)

    if not monday_response:
        print("Error al obtener datos de Monday: No se recibió respuesta")
        return
    
    if 'errors' in monday_response:
        print("Error al obtener datos de Monday:", monday_response.get('errors'))
        return

    items = monday_response.get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
    print(f"Se encontraron {len(items)} elemento(s). Filtrando...")
    print("-" * 40)

    # PASO 1: Filtrar items ligeros
    for item in items:
        item_ligero = parse_light_item_for_filtering(item)
        items_procesados += 1
        
        # Comprobamos si el item es apto (tiene fecha y un operario)
        operario_email = item_ligero.get('operario_email')
        operario_nombre = item_ligero.get('operario')
        
        if not operario_nombre or not item_ligero.get('fecha_inicio'):
            if not operario_nombre:
                print(f"-> Saltando '{item_ligero['name']}': No tiene operario asignado.")
            else:
                print(f"-> Saltando '{item_ligero['name']}': No tiene fecha asignada.")
            items_saltados += 1
            continue

        # Buscamos el perfil del filmmaker usando estrategia de dos pasos
        filmmaker_profile = None
        
        # PASO 1: Match por Email (para miembros completos)
        if operario_email:
            for profile in config.FILMMAKER_PROFILES:
                if profile['monday_email'] == operario_email:
                    filmmaker_profile = profile
                    break
        
        # PASO 2: Match por Nombre (para invitados o si no se encontró por email)
        if not filmmaker_profile:
            for profile in config.FILMMAKER_PROFILES:
                if profile['monday_name'] == operario_nombre:
                    filmmaker_profile = profile
                    break
        
        # PASO 2: Si encontramos un perfil, obtenemos los detalles completos del item
        if filmmaker_profile:
            print(f"✅ Item '{item_ligero['name']}' pasa el filtro. Obteniendo detalles completos...")
            
            # Obtener detalles completos del item
            item_completo = get_single_item_details(item_ligero['id'])
            if not item_completo:
                print(f"❌ Error al obtener detalles del item '{item_ligero['name']}'. Saltando...")
                items_saltados += 1
                continue
            
            # Procesar el item completo
            item_procesado = parse_monday_item(item_completo)
            calendar_id = filmmaker_profile['calendar_id']
            google_event_id = item_procesado.get('google_event_id')
            
            print(f"Procesando '{item_procesado['name']}' para {filmmaker_profile['monday_name']}...")
            
            # LÓGICA DE UPSERT
            if google_event_id:
                # Si ya existe un ID de evento, actualizamos
                print(f"-> [INFO] Item '{item_procesado['name']}' ya tiene evento. Actualizando...")
                update_google_event(google_service, calendar_id, item_procesado)
                items_sincronizados += 1
            else:
                # Si no existe ID, creamos nuevo evento
                print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando...")
                new_event_id = create_google_event(google_service, calendar_id, item_procesado)
                
                if new_event_id:
                    # Guardamos el ID del nuevo evento en Monday
                    print(f"> [DEBUG] Google devolvió el ID: {new_event_id}. Intentando guardarlo en Monday...")
                    update_monday_column(
                        item_procesado['id'], 
                        config.BOARD_ID_GRABACIONES, 
                        config.COL_GOOGLE_EVENT_ID, 
                        new_event_id
                    )
                    items_sincronizados += 1
                else:
                    print(f"❌ Error al crear evento para '{item_procesado['name']}'")
                    items_saltados += 1
            
            print("-" * 20)
        else:
            print(f"-> Saltando '{item_ligero['name']}': Operario '{operario_nombre}' no encontrado en la configuración.")
            items_saltados += 1

    # Resumen detallado
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE SINCRONIZACIÓN")
    print("=" * 50)
    print(f"📋 Elementos procesados: {items_procesados}")
    print(f"✅ Eventos sincronizados: {items_sincronizados}")
    print(f"⏭️  Elementos saltados: {items_saltados}")
    print("=" * 50)

    print("\nProceso de sincronización terminado.")

if __name__ == "__main__":
    main()