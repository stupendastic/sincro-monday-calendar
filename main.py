import os
import requests
import json
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service, create_google_event, update_google_event, create_and_share_calendar, register_google_push_notification

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
        
        # Extraer email y IDs del operario
        if operario_col.get('value'):
            try:
                value_data = json.loads(operario_col['value'])
                persons = value_data.get('personsAndTeams', [])
                parsed_item['operario_email'] = persons[0].get('email') if persons else None
                
                # Extraer IDs de todos los operarios asignados
                operario_ids = []
                for person in persons:
                    if person.get('id'):
                        operario_ids.append(person['id'])
                parsed_item['operario_ids'] = operario_ids
            except (json.JSONDecodeError, KeyError):
                parsed_item['operario_email'] = None
                parsed_item['operario_ids'] = []
        else:
            parsed_item['operario_email'] = None
            parsed_item['operario_ids'] = []
    else:
        parsed_item['operario'] = None
        parsed_item['operario_email'] = None
        parsed_item['operario_ids'] = []

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
            
            # Ahora, extraemos el email y los IDs del campo 'value'
            if col_data.get('value'):
                value_data = json.loads(col_data['value'])
                persons = value_data.get('personsAndTeams', [])
                
                # Extraer emails
                parsed_item['operario_email'] = persons[0].get('email') if persons else None
                
                # Extraer IDs de todos los operarios asignados
                operario_ids = []
                for person in persons:
                    if person.get('id'):
                        operario_ids.append(person['id'])
                parsed_item['operario_ids'] = operario_ids
            else:
                parsed_item['operario_email'] = None
                parsed_item['operario_ids'] = []

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

def sincronizar_item_especifico(item_id):
    """
    Sincroniza un item específico de Monday.com con Google Calendar.
    
    Args:
        item_id (int): ID del item de Monday.com a sincronizar
        
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario
    """
    print(f"Iniciando sincronización del item {item_id}...")
    
    # 1. Inicializar servicios
    google_service = get_calendar_service()
    if not google_service or not MONDAY_API_KEY:
        print("Error en la inicialización de servicios. Abortando.")
        return False

    print("✅ Servicios inicializados.")

    # 2. Obtener directorio de usuarios de Monday.com
    user_directory = get_monday_user_directory()
    if not user_directory:
        print("❌ Error al obtener directorio de usuarios. Abortando.")
        return False

    # 3. Obtener detalles completos del item específico
    item_completo = get_single_item_details(item_id)
    if not item_completo:
        print(f"❌ Error al obtener detalles del item {item_id}. Abortando.")
        return False
    
    # 4. Procesar el item
    item_procesado = parse_monday_item(item_completo)
    
    # 5. Verificar que el item tiene fecha y operario
    if not item_procesado.get('fecha_inicio'):
        print(f"❌ Item {item_id} no tiene fecha asignada. Saltando.")
        return False
    
    operario_nombre = item_procesado.get('operario')
    if not operario_nombre:
        print(f"❌ Item {item_id} no tiene operario asignado. Saltando.")
        return False
    
    # 6. Buscar el perfil del filmmaker correspondiente
    perfil_encontrado = None
    user_id = None
    
    for perfil in config.FILMMAKER_PROFILES:
        if perfil['monday_name'] == operario_nombre:
            perfil_encontrado = perfil
            user_id = user_directory.get(perfil['monday_name'])
            break
    
    if not perfil_encontrado:
        print(f"❌ No se encontró perfil para el operario '{operario_nombre}'.")
        print(f"   Perfiles disponibles: {[p['monday_name'] for p in config.FILMMAKER_PROFILES]}")
        return False
    
    if not user_id:
        print(f"❌ No se pudo encontrar el ID de usuario para '{operario_nombre}' en Monday.com.")
        return False
    
    print(f"✅ Perfil encontrado para: {operario_nombre} (ID: {user_id})")
    
    # 7. Verificar si el perfil tiene calendar_id configurado
    if perfil_encontrado['calendar_id'] is None:
        print(f"-> [ACCIÓN] El perfil para {operario_nombre} necesita un calendario. Creando ahora...")
        new_id = create_and_share_calendar(google_service, operario_nombre, perfil_encontrado['personal_email'])
        
        if new_id:
            # Actualizar el perfil en memoria
            perfil_encontrado['calendar_id'] = new_id
            print(f"-> [ÉXITO] El perfil de {operario_nombre} ha sido actualizado con el nuevo ID de calendario.")
        else:
            print(f"-> [ERROR] No se pudo crear el calendario para {operario_nombre}. Abortando.")
            return False
    
    # 8. Ejecutar la lógica de crear/actualizar el evento en Google Calendar
    calendar_id = perfil_encontrado['calendar_id']
    google_event_id = item_procesado.get('google_event_id')
    
    print(f"Procesando '{item_procesado['name']}' para {operario_nombre}...")
    
    # LÓGICA DE UPSERT
    if google_event_id:
        # Si ya existe un ID de evento, actualizamos
        print(f"-> [INFO] Item '{item_procesado['name']}' ya tiene evento. Actualizando...")
        success = update_google_event(google_service, calendar_id, item_procesado)
        if success:
            print(f"✅ Evento actualizado exitosamente para '{item_procesado['name']}'")
            return True
        else:
            print(f"❌ Error al actualizar evento para '{item_procesado['name']}'")
            return False
    else:
        # Si no existe ID, creamos nuevo evento
        print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando...")
        new_event_id = create_google_event(google_service, calendar_id, item_procesado)
        
        if new_event_id:
            # Guardamos el ID del nuevo evento en Monday
            print(f"> [DEBUG] Google devolvió el ID: {new_event_id}. Guardándolo en Monday...")
            update_success = update_monday_column(
                item_procesado['id'], 
                config.BOARD_ID_GRABACIONES, 
                config.COL_GOOGLE_EVENT_ID, 
                new_event_id
            )
            if update_success:
                print(f"✅ Evento creado y guardado exitosamente para '{item_procesado['name']}'")
                return True
            else:
                print(f"⚠️  Evento creado pero no se pudo guardar el ID en Monday")
                return True  # Consideramos éxito porque el evento se creó
        else:
            print(f"❌ Error al crear evento para '{item_procesado['name']}'")
            return False


def actualizar_fecha_en_monday(google_event_id, nueva_fecha_inicio, nueva_fecha_fin):
    """
    Actualiza la fecha de un item en Monday.com basándose en cambios en Google Calendar.
    
    Args:
        google_event_id (str): ID del evento de Google Calendar
        nueva_fecha_inicio (str): Nueva fecha de inicio en formato ISO
        nueva_fecha_fin (str): Nueva fecha de fin en formato ISO
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    print(f"🔄 Buscando item en Monday con Google Event ID: {google_event_id}")
    
    # 1. Buscar el item en Monday.com usando items_by_column_values
    query = f"""
    query {{
        items_by_column_values(board_id: {config.BOARD_ID_GRABACIONES}, column_id: "{config.COL_GOOGLE_EVENT_ID}", column_value: "{google_event_id}") {{
            id
            name
            board {{
                id
            }}
        }}
    }}
    """
    
    data = {'query': query}
    
    try:
        print(f"  -> Buscando item en Monday.com...")
        response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error al buscar item en Monday: {response_data['errors']}")
            return False
        
        items = response_data.get('data', {}).get('items_by_column_values', [])
        
        if not items:
            print(f"❌ No se encontró ningún item en Monday con Google Event ID: {google_event_id}")
            return False
        
        # Tomar el primer item encontrado (debería ser solo uno)
        item = items[0]
        item_id = item.get('id')
        board_id = item.get('board', {}).get('id')
        item_name = item.get('name')
        
        print(f"✅ Item encontrado: '{item_name}' (ID: {item_id}, Board: {board_id})")
        
        # 2. Preparar las nuevas fechas para Monday
        # Monday espera fecha en formato "YYYY-MM-DD" y hora en "HH:MM:SS"
        from datetime import datetime
        
        # Parsear la fecha de inicio
        if 'T' in nueva_fecha_inicio:
            # Evento con hora específica
            inicio_dt = datetime.fromisoformat(nueva_fecha_inicio.replace('Z', '+00:00'))
            fecha_monday = inicio_dt.strftime("%Y-%m-%d")
            hora_monday = inicio_dt.strftime("%H:%M:%S")
        else:
            # Evento de día completo
            fecha_monday = nueva_fecha_inicio
            hora_monday = None
        
        print(f"  -> Actualizando fecha en Monday: {fecha_monday} {hora_monday if hora_monday else '(día completo)'}")
        
        # 3. Actualizar la columna de fecha en Monday
        if hora_monday:
            # Evento con hora específica
            success = update_monday_date_column(
                item_id, 
                board_id, 
                config.COL_FECHA_GRAB, 
                fecha_monday, 
                hora_monday
            )
        else:
            # Evento de día completo
            success = update_monday_date_column(
                item_id, 
                board_id, 
                config.COL_FECHA_GRAB, 
                fecha_monday
            )
        
        if success:
            print(f"✅ Fecha actualizada exitosamente en Monday para '{item_name}'")
            return True
        else:
            print(f"❌ Error al actualizar fecha en Monday para '{item_name}'")
            return False
            
    except Exception as e:
        print(f"❌ Error al actualizar fecha en Monday: {e}")
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

    # 2. Obtener URL de ngrok para webhooks
    NGROK_URL = os.getenv("NGROK_PUBLIC_URL")
    if not NGROK_URL:
        print("⚠️  NGROK_PUBLIC_URL no está configurada en .env")
        print("   Los canales de notificación push no se registrarán.")
        print("   Añade NGROK_PUBLIC_URL=https://tu-url.ngrok.io a tu archivo .env")
    else:
        print(f"✅ URL de ngrok configurada: {NGROK_URL}")

    # 3. Obtener directorio de usuarios de Monday.com
    user_directory = get_monday_user_directory()
    if not user_directory:
        print("❌ Error al obtener directorio de usuarios. Abortando.")
        return

    print(f"Obteniendo datos del tablero: {config.BOARD_ID_GRABACIONES}...")
    monday_response = get_monday_board_items(config.BOARD_ID_GRABACIONES, config.COLUMN_IDS)

    if not monday_response:
        print("Error al obtener datos de Monday: No se recibió respuesta")
        return
    
    if 'errors' in monday_response:
        print("Error al obtener datos de Monday:", monday_response.get('errors'))
        return

    items = monday_response.get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
    print(f"Se encontraron {len(items)} elemento(s).")
    print("-" * 40)

    # PASO 1: Filtrar items ligeros para obtener información básica
    items_filtrados = []
    for item in items:
        item_ligero = parse_light_item_for_filtering(item)
        items_procesados += 1
        
        # Comprobamos si el item es apto (tiene fecha y un operario)
        operario_nombre = item_ligero.get('operario')
        operario_ids = item_ligero.get('operario_ids', [])
        
        if not operario_nombre or not item_ligero.get('fecha_inicio'):
            if not operario_nombre:
                print(f"-> Saltando '{item_ligero['name']}': No tiene operario asignado.")
            else:
                print(f"-> Saltando '{item_ligero['name']}': No tiene fecha asignada.")
            items_saltados += 1
            continue
        
        items_filtrados.append(item_ligero)

    print(f"Items aptos para procesamiento: {len(items_filtrados)}")
    print("-" * 40)

    # PASO 2: Iterar sobre cada perfil de filmmaker
    config_updated = False  # Variable para rastrear si se actualizó algún perfil
    
    for perfil in config.FILMMAKER_PROFILES:
        print(f"--- Procesando perfil para: {perfil['monday_name']} ---")
        
        # Traducir nombre del perfil a ID de usuario
        user_id = user_directory.get(perfil['monday_name'])
        if not user_id:
            print(f"❌ No se pudo encontrar el ID de usuario para '{perfil['monday_name']}' en Monday.com.")
            print(f"   Usuarios disponibles: {list(user_directory.keys())}")
            continue
        
        print(f"   -> ID de usuario encontrado: {user_id}")
        
        # Verificar si el perfil tiene calendar_id configurado
        if perfil['calendar_id'] is None:
            print(f"-> [ACCIÓN] El perfil para {perfil['monday_name']} necesita un calendario. Creando ahora...")
            new_id = create_and_share_calendar(google_service, perfil['monday_name'], perfil['personal_email'])
            
            if new_id:
                # Actualizar el perfil en memoria
                perfil['calendar_id'] = new_id
                config_updated = True
                print(f"-> [ÉXITO] El perfil de {perfil['monday_name']} ha sido actualizado en memoria con el nuevo ID de calendario.")
            else:
                print(f"-> [ERROR] No se pudo crear el calendario para {perfil['monday_name']}. Saltando sincronización.")
                continue
        
        # REGISTRAR CANAL DE NOTIFICACIONES PUSH DE GOOGLE
        if NGROK_URL and perfil['calendar_id']:
            print(f"-> [NOTIFICACIONES] Registrando canal push para {perfil['monday_name']}...")
            push_success = register_google_push_notification(
                google_service, 
                perfil['calendar_id'], 
                NGROK_URL
            )
            if push_success:
                print(f"✅ Canal de notificaciones registrado para {perfil['monday_name']}")
            else:
                print(f"⚠️  No se pudo registrar canal de notificaciones para {perfil['monday_name']}")
        
        # PASO 3: Iterar sobre todos los items filtrados
        for item_ligero in items_filtrados:
            # Comprobar si el ID del usuario del perfil está en la lista de IDs de operarios del item
            operario_ids = item_ligero.get('operario_ids', [])
            if user_id in operario_ids:
                print(f"✅ Coincidencia encontrada para '{item_ligero['name']}' con {perfil['monday_name']} (ID: {user_id})")
                
                # Obtener detalles completos del item
                item_completo = get_single_item_details(item_ligero['id'])
                if not item_completo:
                    print(f"❌ Error al obtener detalles del item '{item_ligero['name']}'. Saltando...")
                    items_saltados += 1
                    continue
                
                # Procesar el item completo
                item_procesado = parse_monday_item(item_completo)
                calendar_id = perfil['calendar_id']
                google_event_id = item_procesado.get('google_event_id')
                
                print(f"Procesando '{item_procesado['name']}' para {perfil['monday_name']}...")
                
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
                # No hay coincidencia, continuar con el siguiente item
                continue

    # Mostrar información sobre actualizaciones de configuración
    if config_updated:
        print("\n" + "=" * 50)
        print("⚠️  CONFIGURACIÓN ACTUALIZADA")
        print("=" * 50)
        print("Se han creado nuevos calendarios durante esta ejecución.")
        print("Para hacer permanentes estos cambios, actualiza manualmente config.py")
        print("con los nuevos calendar_id que se mostraron arriba.")
        print("=" * 50)

    # Guardar cambios en config.py si se actualizaron perfiles
    if config_updated:
        print("\n--- [GUARDANDO] Se han detectado cambios en la configuración. Escribiendo en config.py... ---")
        
        try:
            # Leer el contenido actual del archivo config.py
            with open('config.py', 'r', encoding='utf-8') as file:
                config_content = file.read()
            
            # Encontrar la línea donde empieza FILMMAKER_PROFILES
            lines = config_content.split('\n')
            new_lines = []
            in_filmmaker_profiles = False
            filmmaker_profiles_started = False
            
            for line in lines:
                if line.strip().startswith('FILMMAKER_PROFILES = ['):
                    # Marcar que hemos encontrado el inicio
                    filmmaker_profiles_started = True
                    in_filmmaker_profiles = True
                    new_lines.append(line)
                    continue
                
                if filmmaker_profiles_started and in_filmmaker_profiles:
                    # Si estamos dentro de FILMMAKER_PROFILES, saltamos las líneas hasta encontrar el final
                    if line.strip() == ']':
                        in_filmmaker_profiles = False
                        # Escribir la nueva lista de perfiles
                        new_lines.append('')
                        for i, perfil in enumerate(config.FILMMAKER_PROFILES):
                            if i == 0:
                                new_lines.append('    {')
                            else:
                                new_lines.append('    },')
                                new_lines.append('    {')
                            
                            new_lines.append(f'        "monday_name": "{perfil["monday_name"]}",')
                            new_lines.append(f'        "personal_email": "{perfil["personal_email"]}",')
                            
                            if perfil['calendar_id'] is None:
                                new_lines.append('        "calendar_id": None')
                            else:
                                new_lines.append(f'        "calendar_id": "{perfil["calendar_id"]}"')
                        
                        new_lines.append('    }')
                        new_lines.append(']')
                        continue
                    else:
                        # Saltar líneas dentro de FILMMAKER_PROFILES
                        continue
                
                # Si no estamos en FILMMAKER_PROFILES, añadir la línea tal como está
                new_lines.append(line)
            
            # Escribir el archivo actualizado
            with open('config.py', 'w', encoding='utf-8') as file:
                file.write('\n'.join(new_lines))
            
            print("✅ ¡Archivo config.py actualizado con los nuevos IDs de calendario!")
            
        except Exception as e:
            print(f"❌ Error al actualizar config.py: {e}")
            print("Los cambios se mantienen solo en memoria. Actualiza manualmente config.py.")

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