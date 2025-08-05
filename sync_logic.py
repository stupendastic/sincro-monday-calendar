import json
import requests
from datetime import datetime, timedelta

# Importaciones de nuestros módulos
import config
from google_calendar_service import get_calendar_service, create_google_event, update_google_event, update_google_event_by_id, create_and_share_calendar, find_event_copy_by_master_id, delete_event_by_id
from monday_service import get_monday_user_directory, get_single_item_details, update_monday_column, MONDAY_API_URL, HEADERS

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
    if not google_service:
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
    
    # 5. Verificar que el item tiene fecha
    if not item_procesado.get('fecha_inicio'):
        print(f"❌ Item {item_id} no tiene fecha asignada. Saltando.")
        return False
    
    # 6. COMPROBACIÓN PARA ITEMS SIN OPERARIO
    operario_ids = item_procesado.get('operario_ids', [])
    if not operario_ids:
        print(f"📋 Item {item_id} no tiene operario asignado. Procesando como evento sin asignar...")
        
        # Lógica de upsert para eventos sin asignar
        calendar_id = config.UNASSIGNED_CALENDAR_ID
        google_event_id = item_procesado.get('google_event_id')
        
        print(f"Procesando '{item_procesado['name']}' como evento sin asignar...")
        
        if google_event_id:
            # Si ya existe un ID de evento, actualizamos
            print(f"-> [INFO] Item '{item_procesado['name']}' ya tiene evento. Actualizando...")
            success = update_google_event(google_service, calendar_id, item_procesado, board_id=config.BOARD_ID_GRABACIONES)
            if success:
                print(f"✅ Evento sin asignar actualizado exitosamente para '{item_procesado['name']}'")
                return True
            else:
                print(f"❌ Error al actualizar evento sin asignar para '{item_procesado['name']}'")
                return False
        else:
            # Si no existe ID, creamos nuevo evento
            print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando...")
            new_event_id = create_google_event(google_service, calendar_id, item_procesado, board_id=config.BOARD_ID_GRABACIONES)
            
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
                    print(f"✅ Evento sin asignar creado y guardado exitosamente para '{item_procesado['name']}'")
                    return True
                else:
                    print(f"⚠️  Evento sin asignar creado pero no se pudo guardar el ID en Monday")
                    return True  # Consideramos éxito porque el evento se creó
            else:
                print(f"❌ Error al crear evento sin asignar para '{item_procesado['name']}'")
                return False
    
    # 7. Verificar que el item tiene operario (para items con operario asignado)
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
    
    # 8. Ejecutar la lógica de crear/actualizar el evento en el CALENDARIO MAESTRO
    calendar_id = config.MASTER_CALENDAR_ID
    google_event_id = item_procesado.get('google_event_id')
    
    print(f"Procesando '{item_procesado['name']}' para {operario_nombre} en el Calendario Máster...")
    
    # LÓGICA DE UPSERT EN CALENDARIO MAESTRO
    if google_event_id:
        # Si ya existe un ID de evento, actualizamos
        print(f"-> [INFO] Item '{item_procesado['name']}' ya tiene evento maestro. Actualizando...")
        success = update_google_event(google_service, calendar_id, item_procesado, board_id=config.BOARD_ID_GRABACIONES)
        if success:
            print(f"✅ Evento maestro actualizado exitosamente para '{item_procesado['name']}'")
            return True
        else:
            print(f"❌ Error al actualizar evento maestro para '{item_procesado['name']}'")
            return False
    else:
        # Si no existe ID, creamos nuevo evento maestro
        print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando evento maestro...")
        new_event_id = create_google_event(google_service, calendar_id, item_procesado, board_id=config.BOARD_ID_GRABACIONES)
        
        if new_event_id:
            # Guardamos el ID del nuevo evento maestro en Monday
            print(f"> [DEBUG] Google devolvió el ID del evento maestro: {new_event_id}. Guardándolo en Monday...")
            update_success = update_monday_column(
                item_procesado['id'], 
                config.BOARD_ID_GRABACIONES, 
                config.COL_GOOGLE_EVENT_ID, 
                new_event_id
            )
            if update_success:
                print(f"✅ Evento maestro creado y guardado exitosamente para '{item_procesado['name']}'")
                return True
            else:
                print(f"⚠️  Evento maestro creado pero no se pudo guardar el ID en Monday")
                return True  # Consideramos éxito porque el evento se creó
        else:
            print(f"❌ Error al crear evento maestro para '{item_procesado['name']}'")
            return False
    
    # 9. SINCRONIZACIÓN DE COPIAS PARA FILMMAKERS
    print(f"🔄 Iniciando sincronización de copias para filmmakers...")
    
    # Obtener la lista de operarios actuales
    operario_ids = item_procesado.get('operario_ids', [])
    operarios_actuales = set()
    
    # Crear set con los calendar_id de todos los filmmakers asignados
    for operario_id in operario_ids:
        for perfil in config.FILMMAKER_PROFILES:
            if perfil.get('monday_user_id') == operario_id and perfil.get('calendar_id'):
                operarios_actuales.add(perfil['calendar_id'])
                break
    
    print(f"  -> Filmmakers asignados: {len(operarios_actuales)} calendarios")
    
    # Obtener el ID del evento maestro (el que acabamos de sincronizar)
    master_event_id = item_procesado.get('google_event_id')
    if not master_event_id:
        print(f"  ❌ No se pudo obtener el ID del evento maestro. Saltando copias.")
        return True  # Consideramos éxito porque el evento maestro se creó
    
    # Iterar sobre cada calendario de filmmaker
    for target_calendar_id in operarios_actuales:
        print(f"  -> Procesando copia para calendario: {target_calendar_id}")
        
        # Buscar si ya existe una copia
        existing_copy = find_event_copy_by_master_id(google_service, target_calendar_id, master_event_id)
        
        if not existing_copy:
            # No existe copia, crear nueva
            print(f"    -> [ACCIÓN] Creando copia para el filmmaker en el calendario {target_calendar_id}...")
            
            # Crear copia con extended_properties para vincular con el evento maestro
            extended_props = {
                'private': {
                    'master_event_id': master_event_id
                }
            }
            
            copy_event_id = create_google_event(
                google_service, 
                target_calendar_id, 
                item_procesado, 
                extended_properties=extended_props,
                board_id=config.BOARD_ID_GRABACIONES
            )
            
            if copy_event_id:
                print(f"    ✅ Copia creada exitosamente para calendario {target_calendar_id}")
            else:
                print(f"    ❌ Error al crear copia para calendario {target_calendar_id}")
        else:
            # Existe copia, actualizar
            print(f"    -> [INFO] La copia para el filmmaker ya existe. Actualizando...")
            
            # Actualizar la copia existente usando su ID específico
            copy_event_id = existing_copy.get('id')
            success = update_google_event_by_id(
                google_service, 
                target_calendar_id, 
                copy_event_id,
                item_procesado,
                board_id=config.BOARD_ID_GRABACIONES
            )
            
            if success:
                print(f"    ✅ Copia actualizada exitosamente para calendario {target_calendar_id}")
            else:
                print(f"    ❌ Error al actualizar copia para calendario {target_calendar_id}")
    
    print(f"✅ Sincronización de copias completada para '{item_procesado['name']}'")
    
    # 10. LIMPIEZA DE COPIAS OBSOLETAS
    print(f"🧹 Iniciando limpieza de copias obsoletas...")
    
    # Obtener el estado anterior: qué filmmakers tenían copias antes de este cambio
    operarios_con_copia_anterior = set()
    
    # Iterar sobre TODOS los perfiles para encontrar copias existentes
    for perfil in config.FILMMAKER_PROFILES:
        if perfil.get('calendar_id'):
            existing_copy = find_event_copy_by_master_id(google_service, perfil['calendar_id'], master_event_id)
            if existing_copy:
                operarios_con_copia_anterior.add(perfil['calendar_id'])
                print(f"  -> Encontrada copia anterior en calendario: {perfil['calendar_id']}")
    
    print(f"  -> Filmmakers con copia anterior: {len(operarios_con_copia_anterior)} calendarios")
    
    # Calcular quiénes han sido eliminados (diferencia entre estado anterior y actual)
    calendarios_a_limpiar = operarios_con_copia_anterior - operarios_actuales
    
    if calendarios_a_limpiar:
        print(f"  -> Filmmakers a limpiar: {len(calendarios_a_limpiar)} calendarios")
        
        # Ejecutar la limpieza
        for calendar_id_a_limpiar in calendarios_a_limpiar:
            print(f"    -> [ACCIÓN] Eliminando copia obsoleta del calendario {calendar_id_a_limpiar}...")
            
            # Buscar el ID de la copia que hay que borrar
            copy_to_delete = find_event_copy_by_master_id(google_service, calendar_id_a_limpiar, master_event_id)
            
            if copy_to_delete:
                copy_event_id = copy_to_delete.get('id')
                print(f"      -> Encontrada copia a eliminar con ID: {copy_event_id}")
                
                # Eliminar el evento
                success = delete_event_by_id(google_service, calendar_id_a_limpiar, copy_event_id)
                
                if success:
                    print(f"      ✅ Copia eliminada exitosamente del calendario {calendar_id_a_limpiar}")
                else:
                    print(f"      ❌ Error al eliminar copia del calendario {calendar_id_a_limpiar}")
            else:
                print(f"      ⚠️  No se encontró copia para eliminar en calendario {calendar_id_a_limpiar}")
    else:
        print(f"  -> No hay copias obsoletas para limpiar")
    
    print(f"✅ Limpieza de copias obsoletas completada para '{item_procesado['name']}'")
    return True

def actualizar_fecha_en_monday(google_event_id, nueva_fecha_inicio, nueva_fecha_fin):
    """
    Actualiza la fecha de un item en Monday.com basándose en cambios en Google Calendar.
    
    Args:
        google_event_id (str): ID del evento de Google Calendar
        nueva_fecha_inicio (dict): Nueva fecha de inicio de Google (ej: {'date': '2025-08-10'} o {'dateTime': '...'})
        nueva_fecha_fin (dict): Nueva fecha de fin de Google (ej: {'date': '2025-08-10'} o {'dateTime': '...'})
        
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
        
        # 2. Procesar las fechas de Google Calendar
        # Google puede enviar fechas en formato {'date': 'YYYY-MM-DD'} o {'dateTime': 'ISO_STRING'}
        
        # Procesar fecha de inicio
        if 'dateTime' in nueva_fecha_inicio:
            # Evento con hora específica
            date_time_str = nueva_fecha_inicio['dateTime']
            # Remover la 'Z' si existe y convertir a datetime
            if date_time_str.endswith('Z'):
                date_time_str = date_time_str[:-1] + '+00:00'
            
            inicio_dt = datetime.fromisoformat(date_time_str)
            fecha_monday = inicio_dt.strftime("%Y-%m-%d")
            hora_monday = inicio_dt.strftime("%H:%M:%S")
            es_evento_con_hora = True
            
        elif 'date' in nueva_fecha_inicio:
            # Evento de día completo
            fecha_monday = nueva_fecha_inicio['date']
            hora_monday = None
            es_evento_con_hora = False
            
        else:
            print(f"❌ Formato de fecha de inicio no reconocido: {nueva_fecha_inicio}")
            return False
        
        print(f"  -> Actualizando fecha en Monday: {fecha_monday} {hora_monday if hora_monday else '(día completo)'}")
        
        # 3. Actualizar la columna de fecha en Monday usando la nueva función
        success = update_monday_date_column_v2(
            item_id, 
            board_id, 
            config.COL_FECHA_GRAB, 
            fecha_monday, 
            hora_monday
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
        "columnId": column_id,
        "value": value_string
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

def update_monday_date_column_v2(item_id, board_id, column_id, date_value, time_value=None):
    """
    Actualiza una columna de fecha en Monday.com usando change_column_value.
    Esta función es más robusta para columnas de fecha complejas.
    
    Args:
        item_id: ID del item
        board_id: ID del tablero
        column_id: ID de la columna de fecha
        date_value: Fecha en formato "YYYY-MM-DD"
        time_value: Hora en formato "HH:MM:SS" (opcional)
    """
    
    # Crear el objeto de fecha para Monday
    date_object = {"date": date_value}
    if time_value:
        date_object["time"] = time_value
    
    # Convertir a JSON string para la mutación
    value_string = json.dumps(date_object)
    
    mutation = """
    mutation ($boardId: Int!, $itemId: Int!, $columnId: String!, $value: String!) {
        change_column_value(board_id: $boardId, item_id: $itemId, column_id: $columnId, value: $value) {
            id
        }
    }
    """
    
    variables = {
        "boardId": board_id,
        "itemId": int(item_id),
        "columnId": column_id,
        "value": value_string
    }
    
    data = {'query': mutation, 'variables': variables}
    
    # Mensaje de depuración antes de la llamada
    print(f"> Escribiendo fecha en Monday (v2)... | Item: {item_id} | Columna: {column_id} | Fecha: {date_value} | Hora: {time_value}")
    
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