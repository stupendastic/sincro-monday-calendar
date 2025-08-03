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
    """Obtiene todos los elementos de un tablero usando paginación."""
    
    # 1. Inicializar variables
    all_items = []
    cursor = None
    
    ids_string = '", "'.join(column_ids)

    # 2. Bucle infinito para paginación
    while True:
        # 3. Query modificada para aceptar cursor
        query = f"""
        query($cursor: String) {{
            boards(ids: {board_id}) {{
                items_page(limit: 100, cursor: $cursor) {{
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
                
                if time_value:
                    # Si hay hora, usamos formato datetime
                    parsed_item['fecha_inicio'] = f"{date_value}T{time_value}"
                    # Para la fecha fin, asumimos 9 horas de duración
                    parsed_item['fecha_fin'] = f"{date_value}T{time_value}"  # TODO: calcular hora fin
                else:
                    # Si no hay hora, es evento de día completo
                    parsed_item['fecha_inicio'] = date_value
                    parsed_item['fecha_fin'] = date_value
            else:
                parsed_item['fecha_inicio'] = None
                parsed_item['fecha_fin'] = None

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
    
    try:
        response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
        response.raise_for_status()
        result = response.json()
        
        if 'errors' in result:
            print(f"Error al actualizar columna en Monday: {result['errors']}")
            return False
        
        print(f"✅ ID de evento guardado en Monday: {value}")
        return True
        
    except Exception as e:
        print(f"Error al actualizar columna en Monday: {e}")
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

    if not monday_response or 'errors' in monday_response:
        print("Error al obtener datos de Monday:", monday_response.get('errors'))
        return

    items = monday_response.get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
    print(f"Se encontraron {len(items)} elemento(s). Sincronizando...")
    print("-" * 40)

    for item in items:
        item_procesado = parse_monday_item(item)
        items_procesados += 1  # Incrementar contador de procesados
        
        # --- LÓGICA DE SINCRONIZACIÓN REFACTORIZADA ---
        
        # 1. Obtenemos datos del operario desde Monday
        operario_email = item_procesado.get('operario_email')
        operario_nombre = item_procesado.get('operario')
        
        # 2. Comprobamos si el item es apto (tiene fecha y un operario)
        if not operario_nombre or not item_procesado.get('fecha_inicio'):
            if not operario_nombre:
                print(f"-> Saltando '{item_procesado['name']}': No tiene operario asignado.")
            else:
                print(f"-> Saltando '{item_procesado['name']}': No tiene fecha asignada.")
            items_saltados += 1
            continue

        # 3. Buscamos el perfil del filmmaker usando estrategia de dos pasos
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
        
        # 4. Si encontramos un perfil, procesamos el evento con lógica de upsert
        if filmmaker_profile:
            calendar_id = filmmaker_profile['calendar_id']
            google_event_id = item_procesado.get('google_event_id')
            
            print(f"Procesando '{item_procesado['name']}' para {filmmaker_profile['monday_name']}...")
            
            # LÓGICA DE UPSERT
            if google_event_id:
                # Si ya existe un ID de evento, actualizamos
                print(f"🔄 Actualizando evento existente: {google_event_id}")
                update_google_event(google_service, calendar_id, item_procesado)
                items_sincronizados += 1
            else:
                # Si no existe ID, creamos nuevo evento
                print(f"➕ Creando nuevo evento...")
                new_event_id = create_google_event(google_service, calendar_id, item_procesado)
                
                if new_event_id:
                    # Guardamos el ID del nuevo evento en Monday
                    print(f"💾 Guardando ID de evento en Monday: {new_event_id}")
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
            print(f"-> Saltando '{item_procesado['name']}': Operario '{operario_nombre}' no encontrado en la configuración.")
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