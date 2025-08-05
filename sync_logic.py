import json
import requests
import os
from datetime import datetime, timedelta

# Importaciones de nuestros módulos
import config
from google_calendar_service import get_calendar_service, create_google_event, update_google_event, update_google_event_by_id, create_and_share_calendar, find_event_copy_by_master_id, delete_event_by_id
from monday_api_handler import MondayAPIHandler

def inicializar_y_preparar_entorno():
    """
    Inicializa y prepara todo el entorno de calendarios antes de procesar cualquier item.
    
    Esta función se asegura de que:
    1. Los servicios de Google Calendar estén inicializados
    2. Todos los calendarios de filmmakers existan
    3. Los calendarios especiales (Máster y Sin Asignar) existan
    4. La configuración se guarde permanentemente si hay cambios
    
    Returns:
        google_service: El servicio de Google Calendar inicializado
    """
    print("🔧 INICIALIZANDO Y PREPARANDO ENTORNO DE CALENDARIOS")
    print("=" * 60)
    
    # 1. Inicializar Servicios
    print("📡 Inicializando servicios de Google Calendar...")
    google_service = get_calendar_service()
    if not google_service:
        print("❌ Error en la inicialización de servicios. Abortando.")
        return None
    
    print("✅ Servicios de Google Calendar inicializados correctamente.")
    
    # Variables para rastrear cambios
    config_changed = False
    
    # 2. Verificar y Crear Calendarios de Filmmakers
    print("\n🎬 VERIFICANDO CALENDARIOS DE FILMMAKERS")
    print("-" * 40)
    
    for i, perfil in enumerate(config.FILMMAKER_PROFILES):
        filmmaker_name = perfil.get('monday_name', 'Desconocido')
        calendar_id = perfil.get('calendar_id')
        
        if calendar_id is None:
            print(f"  🗑️  Creando calendario para {filmmaker_name}...")
            personal_email = perfil.get('personal_email')
            
            if not personal_email:
                print(f"    ❌ Error: {filmmaker_name} no tiene email configurado")
                continue
            
            new_calendar_id = create_and_share_calendar(google_service, filmmaker_name, personal_email)
            
            if new_calendar_id:
                # Actualizar el perfil en memoria
                config.FILMMAKER_PROFILES[i]['calendar_id'] = new_calendar_id
                config_changed = True
                print(f"    ✅ Calendario creado para {filmmaker_name}: {new_calendar_id}")
            else:
                print(f"    ❌ Error al crear calendario para {filmmaker_name}")
        else:
            print(f"  ✅ {filmmaker_name} ya tiene calendario: {calendar_id}")
    
    # 3. Verificar y Crear Calendarios Especiales
    print("\n👑 VERIFICANDO CALENDARIOS ESPECIALES")
    print("-" * 40)
    
    # 3a. Calendario Máster
    if config.MASTER_CALENDAR_ID is None:
        print("  🗑️  Creando Calendario Máster...")
        
        try:
            calendar_body = {
                'summary': "Máster Stupendastic",
                'timeZone': 'Europe/Madrid'
            }
            
            created_calendar = google_service.calendars().insert(body=calendar_body).execute()
            new_master_id = created_calendar.get('id')
            
            if new_master_id:
                config.MASTER_CALENDAR_ID = new_master_id
                config_changed = True
                print(f"    ✅ Calendario Máster creado: {new_master_id}")
            else:
                print("    ❌ Error al crear Calendario Máster")
        except Exception as e:
            print(f"    ❌ Error al crear Calendario Máster: {e}")
    else:
        print(f"  ✅ Calendario Máster ya existe: {config.MASTER_CALENDAR_ID}")
    
    # 3b. Calendario Sin Asignar
    if config.UNASSIGNED_CALENDAR_ID is None:
        print("  🗑️  Creando Calendario Sin Asignar...")
        
        try:
            calendar_body = {
                'summary': "Sin Asignar Stupendastic",
                'timeZone': 'Europe/Madrid'
            }
            
            created_calendar = google_service.calendars().insert(body=calendar_body).execute()
            new_unassigned_id = created_calendar.get('id')
            
            if new_unassigned_id:
                config.UNASSIGNED_CALENDAR_ID = new_unassigned_id
                config_changed = True
                print(f"    ✅ Calendario Sin Asignar creado: {new_unassigned_id}")
            else:
                print("    ❌ Error al crear Calendario Sin Asignar")
        except Exception as e:
            print(f"    ❌ Error al crear Calendario Sin Asignar: {e}")
    else:
        print(f"  ✅ Calendario Sin Asignar ya existe: {config.UNASSIGNED_CALENDAR_ID}")
    
    # 4. Guardar Configuración si hay cambios
    if config_changed:
        print("\n💾 GUARDANDO CONFIGURACIÓN ACTUALIZADA")
        print("-" * 40)
        
        try:
            # Leer el archivo config.py actual
            with open('config.py', 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Actualizar MASTER_CALENDAR_ID
            if config.MASTER_CALENDAR_ID:
                if 'MASTER_CALENDAR_ID = None' in config_content:
                    config_content = config_content.replace(
                        'MASTER_CALENDAR_ID = None',
                        f'MASTER_CALENDAR_ID = "{config.MASTER_CALENDAR_ID}"'
                    )
                elif 'MASTER_CALENDAR_ID =' in config_content:
                    # Buscar y reemplazar la línea existente
                    import re
                    config_content = re.sub(
                        r'MASTER_CALENDAR_ID = "[^"]*"',
                        f'MASTER_CALENDAR_ID = "{config.MASTER_CALENDAR_ID}"',
                        config_content
                    )
            
            # Actualizar UNASSIGNED_CALENDAR_ID
            if config.UNASSIGNED_CALENDAR_ID:
                if 'UNASSIGNED_CALENDAR_ID = None' in config_content:
                    config_content = config_content.replace(
                        'UNASSIGNED_CALENDAR_ID = None',
                        f'UNASSIGNED_CALENDAR_ID = "{config.UNASSIGNED_CALENDAR_ID}"'
                    )
                elif 'UNASSIGNED_CALENDAR_ID =' in config_content:
                    # Buscar y reemplazar la línea existente
                    import re
                    config_content = re.sub(
                        r'UNASSIGNED_CALENDAR_ID = "[^"]*"',
                        f'UNASSIGNED_CALENDAR_ID = "{config.UNASSIGNED_CALENDAR_ID}"',
                        config_content
                    )
            
            # Actualizar calendar_id en FILMMAKER_PROFILES
            for perfil in config.FILMMAKER_PROFILES:
                if perfil.get('calendar_id'):
                    filmmaker_name = perfil['monday_name']
                    calendar_id = perfil['calendar_id']
                    
                    # Buscar y reemplazar la línea específica
                    old_line = f'        "calendar_id": None,'
                    new_line = f'        "calendar_id": "{calendar_id}",'
                    
                    # Buscar la línea específica para este filmmaker
                    lines = config_content.split('\n')
                    for i, line in enumerate(lines):
                        if f'"monday_name": "{filmmaker_name}"' in line:
                            # Buscar la línea calendar_id en las siguientes líneas
                            for j in range(i, min(i + 10, len(lines))):
                                if '"calendar_id": None' in lines[j]:
                                    lines[j] = lines[j].replace('"calendar_id": None', f'"calendar_id": "{calendar_id}"')
                                    break
                    
                    config_content = '\n'.join(lines)
            
            # Escribir el archivo actualizado
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print("    ✅ Configuración guardada exitosamente en config.py")
            
        except Exception as e:
            print(f"    ❌ Error al guardar configuración: {e}")
            print("    ⚠️  Los cambios solo están en memoria")
    
    print("\n✅ ENTORNO PREPARADO CORRECTAMENTE")
    print("=" * 60)
    
    return google_service

def estan_sincronizados(item_procesado, evento_google):
    """
    Compara un item de Monday procesado con un evento de Google para determinar si están sincronizados.
    
    Args:
        item_procesado (dict): Diccionario de un item de Monday ya procesado
        evento_google (dict): Objeto de evento de Google Calendar
        
    Returns:
        bool: True si las fechas/horas coinciden, False en caso contrario o si hay errores
    """
    try:
        # Validación de seguridad: verificar que los parámetros no sean None
        if evento_google is None:
            print("⚠️  evento_google es None - considerando no sincronizados")
            return False
            
        if item_procesado is None:
            print("⚠️  item_procesado es None - considerando no sincronizados")
            return False
        
        # Verificar que item_procesado tenga la clave fecha_inicio
        if 'fecha_inicio' not in item_procesado:
            print("⚠️  item_procesado no tiene clave 'fecha_inicio' - considerando no sincronizados")
            return False
        
        fecha_monday = item_procesado['fecha_inicio']
        if fecha_monday is None:
            print("⚠️  fecha_inicio en item_procesado es None - considerando no sincronizados")
            return False
        
        # Obtener la fecha del evento de Google
        start = evento_google.get('start')
        if not start:
            print("⚠️  evento_google no tiene clave 'start' - considerando no sincronizados")
            return False
        
        # Comprobar si el evento de Google es de "todo el día" o tiene hora específica
        if 'date' in start:
            # Evento de "todo el día" - comparar solo la fecha
            fecha_google = start['date']
            print(f"📅 Comparando evento de día completo: Monday '{fecha_monday}' vs Google '{fecha_google}'")
            
            # Para eventos de día completo, Monday puede tener formato "YYYY-MM-DD" o "YYYY-MM-DDTHH:MM:SS"
            # Extraer solo la parte de la fecha de Monday si tiene hora
            if 'T' in fecha_monday:
                fecha_monday_solo = fecha_monday.split('T')[0]
            else:
                fecha_monday_solo = fecha_monday
            
            return fecha_monday_solo == fecha_google
            
        elif 'dateTime' in start:
            # Evento con hora específica - comparar fecha y hora completa
            fecha_hora_google = start['dateTime']
            print(f"🕐 Comparando evento con hora: Monday '{fecha_monday}' vs Google '{fecha_hora_google}'")
            
            # Normalizar formato de Google (remover 'Z' si existe)
            if fecha_hora_google.endswith('Z'):
                fecha_hora_google = fecha_hora_google[:-1] + '+00:00'
            
            # Normalizar formato de Monday si es necesario
            if 'T' in fecha_monday:
                # Monday ya tiene formato ISO
                fecha_monday_normalizada = fecha_monday
            else:
                # Monday solo tiene fecha, agregar hora por defecto
                fecha_monday_normalizada = f"{fecha_monday}T00:00:00"
            
            # Comparar fechas normalizadas
            try:
                dt_monday = datetime.fromisoformat(fecha_monday_normalizada)
                dt_google = datetime.fromisoformat(fecha_hora_google)
                
                # Comparar con tolerancia de 1 minuto para manejar diferencias de zona horaria
                diferencia = abs((dt_monday - dt_google).total_seconds())
                return diferencia <= 60  # 1 minuto de tolerancia
                
            except ValueError as e:
                print(f"⚠️  Error al parsear fechas: {e} - considerando no sincronizados")
                return False
        else:
            # Formato de fecha no reconocido
            print(f"⚠️  Formato de fecha no reconocido en evento_google: {start} - considerando no sincronizados")
            return False
            
    except Exception as e:
        print(f"❌ Error inesperado en estan_sincronizados: {e} - considerando no sincronizados")
        return False

def get_monday_user_directory(monday_handler):
    """
    Obtiene el directorio completo de usuarios de Monday.com.
    
    Args:
        monday_handler: Instancia de MondayAPIHandler ya inicializada
    
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
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
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

def parse_monday_item(item):
    """
    Toma un 'item' de la respuesta de Monday y lo convierte en un diccionario limpio.
    Ahora entiende las columnas de tipo 'mirror' (reflejo).
    Compatible con el nuevo MondayAPIHandler.
    """
    parsed_item = {
        'id': item.get('id'),
        'name': item.get('name'),
        'group_title': item.get('group', {}).get('title', 'N/A') if item.get('group') else 'N/A',
        'update_body': item.get('updates', [{}])[0].get('body', '') if item.get('updates') else ''
    }

    # Creamos un diccionario para acceder fácilmente a los valores por su ID
    column_values_by_id = {cv['id']: cv for cv in item.get('column_values', [])}

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

def sincronizar_item_especifico(item_id, monday_handler, google_service):
    """
    Sincroniza un item específico de Monday.com con Google Calendar.
    
    Args:
        item_id (int): ID del item de Monday.com a sincronizar
        monday_handler: Instancia de MondayAPIHandler ya inicializada
        google_service: Instancia del servicio de Google Calendar ya inicializada
        
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario
    """
    print(f"Iniciando sincronización del item {item_id}...")
    
    # 1. Verificar que los servicios están disponibles
    if not google_service:
        print("❌ Error: google_service no proporcionado")
        return False
    
    if not monday_handler:
        print("❌ Error: monday_handler no proporcionado")
        return False

    print("✅ Servicios verificados.")

    # 3. Obtener directorio de usuarios de Monday.com
    user_directory = get_monday_user_directory(monday_handler)
    if not user_directory:
        print("❌ Error al obtener directorio de usuarios. Abortando.")
        return False

    # 4. Obtener detalles completos del item específico usando el handler
    # Usar una query directa para obtener solo el item específico
    column_ids_str = '", "'.join(config.COLUMN_IDS)
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
            column_values(ids: ["{column_ids_str}"]) {{
                id
                text
                value
                type
                ... on BoardRelationValue {{
                    linked_item_ids
                }}
                ... on MirrorValue {{
                    display_value
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
            print(f"❌ Error al obtener detalles del item {item_id}: {response_data['errors']}")
            return False
        
        items = response_data.get('data', {}).get('items', [])
        if not items:
            print(f"❌ No se encontró el item {item_id}")
            return False
        
        item_completo = items[0]  # Tomar el primer (y único) item
        
    except Exception as e:
        print(f"❌ Error al obtener detalles del item {item_id}: {e}")
        return False
    
    # 4. Procesar el item
    item_procesado = parse_monday_item(item_completo)
    
    # 5. Verificar que el item tiene fecha
    if not item_procesado.get('fecha_inicio'):
        print(f"❌ Item {item_id} no tiene fecha asignada. Saltando.")
        return False
    
    # 6. PUERTA DE SEGURIDAD: Verificar si ya está sincronizado
    print(f"🔍 Verificando estado de sincronización para '{item_procesado['name']}'...")
    
    # Obtener el evento maestro correspondiente en Google Calendar
    evento_maestro = None
    google_event_id = item_procesado.get('google_event_id')
    
    if google_event_id:
        try:
            # Intentar obtener el evento maestro desde Google Calendar
            evento_maestro = google_service.events().get(
                calendarId=config.MASTER_CALENDAR_ID,
                eventId=google_event_id
            ).execute()
            print(f"  -> Evento maestro encontrado en Google: {evento_maestro.get('summary', 'Sin título')}")
        except Exception as e:
            print(f"  ⚠️  No se pudo obtener el evento maestro desde Google: {e}")
            # Continuar con el flujo normal si no se puede obtener el evento
    else:
        print(f"  -> Item no tiene Google Event ID, continuando con sincronización...")
    
    # Llamar a la Puerta de Seguridad
    ya_sincronizado = estan_sincronizados(item_procesado, evento_maestro)
    
    # Aplicar la Lógica de Decisión
    if ya_sincronizado:
        print(f"-> [INFO] Monday -> Google: Ya sincronizado. Se ignora el eco.")
        return True  # Terminar la función inmediatamente
    else:
        print(f"-> [INFO] Monday -> Google: No sincronizado. Continuando con sincronización...")
    
    # 7. COMPROBACIÓN PARA ITEMS SIN OPERARIO
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
            # Adaptar datos de Monday a formato de Google
            event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
            success = update_google_event(google_service, calendar_id, google_event_id, event_body)
            if success:
                print(f"✅ Evento sin asignar actualizado exitosamente para '{item_procesado['name']}'")
                return True
            else:
                print(f"❌ Error al actualizar evento sin asignar para '{item_procesado['name']}'")
                return False
        else:
            # Si no existe ID, creamos nuevo evento
            print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando...")
            # Adaptar datos de Monday a formato de Google
            event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
            new_event_id = create_google_event(google_service, calendar_id, event_body)
            
            if new_event_id:
                # Guardamos el ID del nuevo evento en Monday
                print(f"> [DEBUG] Google devolvió el ID: {new_event_id}. Guardándolo en Monday...")
                update_success = monday_handler.update_column_value(
                    item_procesado['id'], 
                    config.BOARD_ID_GRABACIONES, 
                    config.COL_GOOGLE_EVENT_ID, 
                    new_event_id,
                    'text'
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
    
    # 8. Verificar que el item tiene operario (para items con operario asignado)
    operario_nombre = item_procesado.get('operario')
    if not operario_nombre:
        print(f"❌ Item {item_id} no tiene operario asignado. Saltando.")
        return False
    
    # 9. Buscar el perfil del filmmaker correspondiente
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
    
    # 10. Verificar que el perfil tiene calendar_id configurado (ya garantizado por inicializar_y_preparar_entorno)
    if perfil_encontrado['calendar_id'] is None:
        print(f"❌ Error: El perfil para {operario_nombre} no tiene calendar_id configurado.")
        print(f"   Esto no debería ocurrir después de inicializar_y_preparar_entorno().")
        return False
    
    # 11. Ejecutar la lógica de crear/actualizar el evento en el CALENDARIO MAESTRO
    calendar_id = config.MASTER_CALENDAR_ID
    google_event_id = item_procesado.get('google_event_id')
    master_event_created = False
    master_event_id = None  # Variable para almacenar el ID del evento maestro
    
    print(f"Procesando '{item_procesado['name']}' para {operario_nombre} en el Calendario Máster...")
    
    # LÓGICA DE UPSERT EN CALENDARIO MAESTRO
    if google_event_id:
        # Si ya existe un ID de evento, actualizamos
        print(f"-> [INFO] Item '{item_procesado['name']}' ya tiene evento maestro. Actualizando...")
        # Adaptar datos de Monday a formato de Google
        event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
        success = update_google_event(google_service, calendar_id, google_event_id, event_body)
        if success:
            print(f"✅ Evento maestro actualizado exitosamente para '{item_procesado['name']}'")
            master_event_created = True
            master_event_id = google_event_id  # Usar el ID existente
        else:
            print(f"❌ Error al actualizar evento maestro para '{item_procesado['name']}'")
            return False
    else:
        # Si no existe ID, creamos nuevo evento maestro
        print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando evento maestro...")
        # Adaptar datos de Monday a formato de Google
        event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
        new_event_id = create_google_event(google_service, calendar_id, event_body)
        
        if new_event_id:
            # Guardamos el ID del nuevo evento maestro en Monday
            print(f"> [DEBUG] Google devolvió el ID del evento maestro: {new_event_id}. Guardándolo en Monday...")
            update_success = monday_handler.update_column_value(
                item_procesado['id'], 
                config.BOARD_ID_GRABACIONES, 
                config.COL_GOOGLE_EVENT_ID, 
                new_event_id,
                'text'
            )
            if update_success:
                print(f"✅ Evento maestro creado y guardado exitosamente para '{item_procesado['name']}'")
            else:
                print(f"⚠️  Evento maestro creado pero no se pudo guardar el ID en Monday")
            master_event_created = True
            master_event_id = new_event_id  # Usar el nuevo ID
        else:
            print(f"❌ Error al crear evento maestro para '{item_procesado['name']}'")
            return False
    
    # 12. SINCRONIZACIÓN DE COPIAS PARA FILMMAKERS
    print(f"🔄 Iniciando sincronización de copias para filmmakers...")
    
    # Obtener la lista de operarios actuales
    operario_nombre = item_procesado.get('operario')
    operarios_actuales = set()
    
    # Buscar el perfil del operario por nombre (maneja múltiples operarios)
    if operario_nombre:
        # Si hay múltiples operarios separados por comas, procesar cada uno
        operarios_lista = [op.strip() for op in operario_nombre.split(',') if op.strip()]
        
        for operario in operarios_lista:
            for perfil in config.FILMMAKER_PROFILES:
                if perfil.get('monday_name') == operario and perfil.get('calendar_id'):
                    operarios_actuales.add(perfil['calendar_id'])
                    print(f"  -> Encontrado perfil para '{operario}': {perfil['calendar_id']}")
                    break
    
    print(f"  -> Filmmakers asignados: {len(operarios_actuales)} calendarios")
    
    # Usar el ID del evento maestro que acabamos de crear/actualizar
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
            
            # Adaptar datos de Monday a formato de Google
            event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
            copy_event_id = create_google_event(
                google_service, 
                target_calendar_id, 
                event_body, 
                extended_properties=extended_props
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
            
            # Mantener las extended_properties existentes para preservar la vinculación
            extended_props = {
                'private': {
                    'master_event_id': master_event_id
                }
            }
            
            # Adaptar datos de Monday a formato de Google
            event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
            success = update_google_event_by_id(
                google_service, 
                target_calendar_id, 
                copy_event_id,
                event_body,
                extended_properties=extended_props
            )
            
            if success:
                print(f"    ✅ Copia actualizada exitosamente para calendario {target_calendar_id}")
            else:
                print(f"    ❌ Error al actualizar copia para calendario {target_calendar_id}")
    
    print(f"✅ Sincronización de copias completada para '{item_procesado['name']}'")
    
    # 13. LIMPIEZA DE COPIAS OBSOLETAS
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

def sincronizar_item_via_webhook(item_id, monday_handler, google_service=None):
    """
    Sincroniza un item específico de Monday.com con Google Calendar - VERSIÓN OPTIMIZADA PARA WEBHOOKS.
    
    Esta función es una versión ligera que evita la inicialización completa del entorno
    y se enfoca únicamente en procesar el item específico para máxima velocidad.
    
    Args:
        item_id (int): ID del item de Monday.com a sincronizar
        monday_handler: Instancia de MondayAPIHandler ya inicializada
        google_service: Instancia del servicio de Google Calendar ya inicializada (opcional)
        
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario
    """
    print(f"⚡ INICIANDO SINCRONIZACIÓN WEBHOOK - Item {item_id}")
    print("=" * 50)
    
    # 1. Verificar que los servicios están disponibles
    print("📡 Verificando servicios...")
    if not google_service:
        print("❌ Error: google_service no proporcionado. Abortando.")
        return False
    
    print("✅ Servicios verificados.")

    # 2. Obtener directorio de usuarios de Monday.com
    user_directory = get_monday_user_directory(monday_handler)
    if not user_directory:
        print("❌ Error al obtener directorio de usuarios. Abortando.")
        return False

    # 3. Obtener datos únicamente del item específico
    print(f"📋 Obteniendo datos del item {item_id}...")
    column_ids_str = '", "'.join(config.COLUMN_IDS)
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
            column_values(ids: ["{column_ids_str}"]) {{
                id
                text
                value
                type
                ... on BoardRelationValue {{
                    linked_item_ids
                }}
                ... on MirrorValue {{
                    display_value
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
            print(f"❌ Error al obtener detalles del item {item_id}: {response_data['errors']}")
            return False
        
        items = response_data.get('data', {}).get('items', [])
        if not items:
            print(f"❌ No se encontró el item {item_id}")
            return False
        
        item_completo = items[0]
        
    except Exception as e:
        print(f"❌ Error al obtener detalles del item {item_id}: {e}")
        return False
    
    # 4. Procesar el item
    item_procesado = parse_monday_item(item_completo)
    
    # 5. Verificar que el item tiene fecha
    if not item_procesado.get('fecha_inicio'):
        print(f"❌ Item {item_id} no tiene fecha asignada. Saltando.")
        return False
    
    # 6. Verificar sincronización (puerta de seguridad)
    print(f"🔍 Verificando estado de sincronización para '{item_procesado['name']}'...")
    
    evento_maestro = None
    google_event_id = item_procesado.get('google_event_id')
    
    if google_event_id:
        try:
            evento_maestro = google_service.events().get(
                calendarId=config.MASTER_CALENDAR_ID,
                eventId=google_event_id
            ).execute()
            print(f"  -> Evento maestro encontrado en Google: {evento_maestro.get('summary', 'Sin título')}")
        except Exception as e:
            print(f"  ⚠️  No se pudo obtener el evento maestro desde Google: {e}")
    else:
        print(f"  -> Item no tiene Google Event ID, continuando con sincronización...")
    
    ya_sincronizado = estan_sincronizados(item_procesado, evento_maestro)
    
    if ya_sincronizado:
        print(f"-> [INFO] Monday -> Google: Ya sincronizado. Se ignora el eco.")
        return True
    else:
        print(f"-> [INFO] Monday -> Google: No sincronizado. Continuando con sincronización...")
    
    # 7. LÓGICA MASTER-COPIAS (versión optimizada)
    print(f"🔄 Ejecutando lógica Master-Copia para '{item_procesado['name']}'...")
    
    # 7a. Procesar eventos sin operario
    operario_ids = item_procesado.get('operario_ids', [])
    if not operario_ids:
        print(f"📋 Item {item_id} no tiene operario asignado. Procesando como evento sin asignar...")
        
        calendar_id = config.UNASSIGNED_CALENDAR_ID
        google_event_id = item_procesado.get('google_event_id')
        
        if google_event_id:
            print(f"-> [INFO] Item '{item_procesado['name']}' ya tiene evento. Actualizando...")
            # Adaptar datos de Monday a formato de Google
            event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
            success = update_google_event(google_service, calendar_id, google_event_id, event_body)
            if success:
                print(f"✅ Evento sin asignar actualizado exitosamente")
                return True
            else:
                print(f"❌ Error al actualizar evento sin asignar")
                return False
        else:
            print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando...")
            # Adaptar datos de Monday a formato de Google
            event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
            new_event_id = create_google_event(google_service, calendar_id, event_body)
            
            if new_event_id:
                print(f"> [DEBUG] Google devolvió el ID: {new_event_id}. Guardándolo en Monday...")
                update_success = monday_handler.update_column_value(
                    item_procesado['id'], 
                    config.BOARD_ID_GRABACIONES, 
                    config.COL_GOOGLE_EVENT_ID, 
                    new_event_id,
                    'text'
                )
                if update_success:
                    print(f"✅ Evento sin asignar creado y guardado exitosamente")
                    return True
                else:
                    print(f"⚠️  Evento sin asignar creado pero no se pudo guardar el ID en Monday")
                    return True
            else:
                print(f"❌ Error al crear evento sin asignar")
                return False
    
    # 7b. Procesar eventos con operario asignado
    operario_nombre = item_procesado.get('operario')
    if not operario_nombre:
        print(f"❌ Item {item_id} no tiene operario asignado. Saltando.")
        return False
    
    # Buscar perfil del filmmaker
    perfil_encontrado = None
    user_id = None
    
    for perfil in config.FILMMAKER_PROFILES:
        if perfil['monday_name'] == operario_nombre:
            perfil_encontrado = perfil
            user_id = user_directory.get(perfil['monday_name'])
            break
    
    if not perfil_encontrado:
        print(f"❌ No se encontró perfil para el operario '{operario_nombre}'.")
        return False
    
    if not user_id:
        print(f"❌ No se pudo encontrar el ID de usuario para '{operario_nombre}' en Monday.com.")
        return False
    
    print(f"✅ Perfil encontrado para: {operario_nombre} (ID: {user_id})")
    
    # Verificar calendar_id (asumiendo que ya está configurado)
    if perfil_encontrado['calendar_id'] is None:
        print(f"❌ Error: El perfil para {operario_nombre} no tiene calendar_id configurado.")
        return False
    
    # 8. CREAR/ACTUALIZAR EVENTO MAESTRO
    print(f"👑 Procesando evento maestro para '{item_procesado['name']}'...")
    
    calendar_id = config.MASTER_CALENDAR_ID
    google_event_id = item_procesado.get('google_event_id')
    master_event_id = None
    
    if google_event_id:
        print(f"-> [INFO] Item '{item_procesado['name']}' ya tiene evento maestro. Actualizando...")
        # Adaptar datos de Monday a formato de Google
        event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
        success = update_google_event(google_service, calendar_id, google_event_id, event_body)
        if success:
            print(f"✅ Evento maestro actualizado exitosamente")
            master_event_id = google_event_id
        else:
            print(f"❌ Error al actualizar evento maestro")
            return False
    else:
        print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando evento maestro...")
        # Adaptar datos de Monday a formato de Google
        event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
        new_event_id = create_google_event(google_service, calendar_id, event_body)
        
        if new_event_id:
            print(f"> [DEBUG] Google devolvió el ID del evento maestro: {new_event_id}. Guardándolo en Monday...")
            update_success = monday_handler.update_column_value(
                item_procesado['id'], 
                config.BOARD_ID_GRABACIONES, 
                config.COL_GOOGLE_EVENT_ID, 
                new_event_id,
                'text'
            )
            if update_success:
                print(f"✅ Evento maestro creado y guardado exitosamente")
            else:
                print(f"⚠️  Evento maestro creado pero no se pudo guardar el ID en Monday")
            master_event_id = new_event_id
        else:
            print(f"❌ Error al crear evento maestro")
            return False
    
    # 9. SINCRONIZAR COPIAS PARA FILMMAKERS
    print(f"🔄 Sincronizando copias para filmmakers...")
    
    operario_nombre = item_procesado.get('operario')
    operarios_actuales = set()
    
    if operario_nombre:
        operarios_lista = [op.strip() for op in operario_nombre.split(',') if op.strip()]
        
        for operario in operarios_lista:
            for perfil in config.FILMMAKER_PROFILES:
                if perfil.get('monday_name') == operario and perfil.get('calendar_id'):
                    operarios_actuales.add(perfil['calendar_id'])
                    print(f"  -> Encontrado perfil para '{operario}': {perfil['calendar_id']}")
                    break
    
    print(f"  -> Filmmakers asignados: {len(operarios_actuales)} calendarios")
    
    if not master_event_id:
        print(f"  ❌ No se pudo obtener el ID del evento maestro. Saltando copias.")
        return True
    
    # Procesar cada calendario de filmmaker
    for target_calendar_id in operarios_actuales:
        print(f"  -> Procesando copia para calendario: {target_calendar_id}")
        
        existing_copy = find_event_copy_by_master_id(google_service, target_calendar_id, master_event_id)
        
        if not existing_copy:
            print(f"    -> [ACCIÓN] Creando copia para el filmmaker...")
            
            extended_props = {
                'private': {
                    'master_event_id': master_event_id
                }
            }
            
            # Adaptar datos de Monday a formato de Google
            event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
            copy_event_id = create_google_event(
                google_service, 
                target_calendar_id, 
                event_body, 
                extended_properties=extended_props
            )
            
            if copy_event_id:
                print(f"    ✅ Copia creada exitosamente")
            else:
                print(f"    ❌ Error al crear copia")
        else:
            print(f"    -> [INFO] La copia ya existe. Actualizando...")
            
            copy_event_id = existing_copy.get('id')
            extended_props = {
                'private': {
                    'master_event_id': master_event_id
                }
            }
            
            # Adaptar datos de Monday a formato de Google
            event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
            success = update_google_event_by_id(
                google_service, 
                target_calendar_id, 
                copy_event_id,
                event_body,
                extended_properties=extended_props
            )
            
            if success:
                print(f"    ✅ Copia actualizada exitosamente")
            else:
                print(f"    ❌ Error al actualizar copia")
    
    # 10. LIMPIEZA DE COPIAS OBSOLETAS
    print(f"🧹 Limpiando copias obsoletas...")
    
    operarios_con_copia_anterior = set()
    
    for perfil in config.FILMMAKER_PROFILES:
        if perfil.get('calendar_id'):
            existing_copy = find_event_copy_by_master_id(google_service, perfil['calendar_id'], master_event_id)
            if existing_copy:
                operarios_con_copia_anterior.add(perfil['calendar_id'])
    
    calendarios_a_limpiar = operarios_con_copia_anterior - operarios_actuales
    
    if calendarios_a_limpiar:
        print(f"  -> Filmmakers a limpiar: {len(calendarios_a_limpiar)} calendarios")
        
        for calendar_id_a_limpiar in calendarios_a_limpiar:
            print(f"    -> [ACCIÓN] Eliminando copia obsoleta del calendario {calendar_id_a_limpiar}...")
            
            copy_to_delete = find_event_copy_by_master_id(google_service, calendar_id_a_limpiar, master_event_id)
            
            if copy_to_delete:
                copy_event_id = copy_to_delete.get('id')
                success = delete_event_by_id(google_service, calendar_id_a_limpiar, copy_event_id)
                
                if success:
                    print(f"      ✅ Copia eliminada exitosamente")
                else:
                    print(f"      ❌ Error al eliminar copia")
            else:
                print(f"      ⚠️  No se encontró copia para eliminar")
    else:
        print(f"  -> No hay copias obsoletas para limpiar")
    
    print(f"✅ SINCRONIZACIÓN WEBHOOK COMPLETADA para '{item_procesado['name']}'")
    return True

def _actualizar_fecha_en_monday(google_event_id, nueva_fecha_inicio, nueva_fecha_fin, monday_handler):
    """
    Actualiza la fecha de un item en Monday.com basándose en cambios en Google Calendar.
    
    Args:
        google_event_id (str): ID del evento de Google Calendar
        nueva_fecha_inicio (dict): Nueva fecha de inicio de Google (ej: {'date': '2025-08-10'} o {'dateTime': '...'})
        nueva_fecha_fin (dict): Nueva fecha de fin de Google (ej: {'date': '2025-08-10'} o {'dateTime': '...'})
        monday_handler: Instancia de MondayAPIHandler ya inicializada
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    print(f"🔄 Buscando item en Monday con Google Event ID: {google_event_id}")
    
    # 1. Usar la función robusta para buscar el item
    item_id = _obtener_item_id_por_google_event_id(google_event_id, monday_handler)
    
    if not item_id:
        print(f"❌ Error al actualizar fecha en Monday.com")
        return False
    
    # Obtener board_id usando una consulta simple
    board_id = config.BOARD_ID_GRABACIONES
    print(f"✅ Item encontrado (ID: {item_id}, Board: {board_id})")
    
    try:
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
        
        # 3. Construir el valor para Monday.com (diccionario Python, no JSON string)
        if hora_monday:
            # Evento con hora específica
            monday_value = {"date": fecha_monday, "time": hora_monday}
        else:
            # Evento de día completo
            monday_value = {"date": fecha_monday}
        
        print(f"  -> Valor para Monday: {monday_value}")
        
        # 4. Actualizar la columna de fecha en Monday usando el handler
        success = monday_handler.update_column_value(
            item_id, 
            board_id, 
            config.COL_FECHA_GRAB, 
            monday_value,
            'date'
        )
        
        if success:
            print(f"✅ Fecha actualizada exitosamente en Monday")
            return True
        else:
            print(f"❌ Error al actualizar fecha en Monday")
            return False
            
    except Exception as e:
        print(f"❌ Error al actualizar fecha en Monday: {e}")
        return False


def sincronizar_desde_google(master_event_id, monday_handler, google_service=None):
    """
    Sincroniza cambios desde Google Calendar hacia Monday.com y propaga a todas las copias.
    
    Flujo estricto:
    1. Obtener la Verdad de Google: Obtener datos completos del evento maestro
    2. Propagar la Verdad a Monday: Actualizar item en Monday.com
    3. Propagar la Verdad a las Copias: Gestionar copias en calendarios de filmmakers
    
    Args:
        master_event_id (str): ID del evento maestro en Google Calendar
        monday_handler: Instancia de MondayAPIHandler ya inicializada
        google_service: Instancia del servicio de Google Calendar ya inicializada (opcional)
        
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario
    """
    print(f"🔄 INICIANDO SINCRONIZACIÓN DESDE GOOGLE")
    print(f"📋 Evento maestro: {master_event_id}")
    print("=" * 60)
    
    # Verificar que los servicios están disponibles
    if not google_service:
        print("❌ Error: google_service no proporcionado")
        return False
    
    try:
        # ========================================
        # 1. OBTENER LA VERDAD DE GOOGLE
        # ========================================
        print("🔍 PASO 1: OBTENIENDO LA VERDAD DE GOOGLE")
        print("-" * 40)
        
        # Obtener el evento maestro actualizado desde Google Calendar
        master_event = google_service.events().get(
            calendarId=config.MASTER_CALENDAR_ID,
            eventId=master_event_id
        ).execute()
        
        if not master_event:
            print(f"❌ No se encontró el evento maestro {master_event_id} en Google Calendar")
            return False
        
        print(f"✅ Evento maestro obtenido: '{master_event.get('summary', 'Sin título')}'")
        
        # Verificar que tiene fechas válidas
        start = master_event.get('start', {})
        end = master_event.get('end', {})
        
        if not start or not end:
            print(f"❌ Evento maestro {master_event_id} no tiene fechas válidas")
            return False
        
        print(f"📅 Fechas del evento maestro: {start} -> {end}")
        
        # ========================================
        # 2. PROPAGAR LA VERDAD A MONDAY
        # ========================================
        print("\n📤 PASO 2: PROPAGANDO LA VERDAD A MONDAY")
        print("-" * 40)
        
        # Actualizar fecha en Monday.com
        monday_success = _actualizar_fecha_en_monday(master_event_id, start, end, monday_handler)
        
        if not monday_success:
            print(f"❌ Error al actualizar fecha en Monday.com")
            return False
        
        print(f"✅ Fecha actualizada exitosamente en Monday.com")
        
        # Obtener el item_id de Monday para el siguiente paso
        item_id = _obtener_item_id_por_google_event_id(master_event_id, monday_handler)
        if not item_id:
            print(f"❌ No se pudo obtener el item_id de Monday")
            return False
        
        print(f"✅ Item ID de Monday obtenido: {item_id}")
        
        # ========================================
        # 3. PROPAGAR LA VERDAD A LAS COPIAS
        # ========================================
        print("\n🔄 PASO 3: PROPAGANDO LA VERDAD A LAS COPIAS")
        print("-" * 40)
        
        # Obtener operarios actuales de Monday
        operarios_actuales = _obtener_operarios_actuales(item_id, monday_handler)
        print(f"📋 Operarios actuales en Monday: {operarios_actuales}")
        
        # Iterar sobre TODOS los perfiles de filmmakers
        print(f"\n🎬 PROCESANDO TODOS LOS FILMMAKERS")
        print("-" * 30)
        
        for perfil in config.FILMMAKER_PROFILES:
            filmmaker_name = perfil.get('monday_name', 'Desconocido')
            calendar_id = perfil.get('calendar_id')
            
            if not calendar_id:
                print(f"⏭️  Saltando {filmmaker_name} - No tiene calendar_id configurado")
                continue
            
            print(f"\n👤 Procesando {filmmaker_name}...")
            print(f"   📅 Calendario: {calendar_id}")
            
            # Verificar si el filmmaker está asignado actualmente
            filmmaker_asignado = filmmaker_name in operarios_actuales
            print(f"   📋 Estado: {'✅ Asignado' if filmmaker_asignado else '❌ No asignado'}")
            
            # Buscar si existe una copia del evento maestro
            existing_copy = find_event_copy_by_master_id(google_service, calendar_id, master_event_id)
            
            if existing_copy:
                print(f"   📄 Copia existente encontrada: {existing_copy.get('id')}")
                
                if filmmaker_asignado:
                    # CASO A: Existe copia Y filmmaker está asignado → ACTUALIZAR
                    print(f"   🔄 Actualizando copia existente...")
                    
                    copy_event_id = existing_copy.get('id')
                    extended_props = {
                        'private': {
                            'master_event_id': master_event_id
                        }
                    }
                    
                    success = update_google_event_by_id(
                        google_service, 
                        calendar_id, 
                        copy_event_id,
                        master_event,  # Usar datos del evento maestro directamente
                        extended_properties=extended_props
                    )
                    
                    if success:
                        print(f"   ✅ Copia actualizada exitosamente")
                    else:
                        print(f"   ❌ Error al actualizar copia")
                else:
                    # CASO B: Existe copia PERO filmmaker NO está asignado → ELIMINAR
                    print(f"   🗑️  Eliminando copia obsoleta...")
                    
                    copy_event_id = existing_copy.get('id')
                    success = delete_event_by_id(google_service, calendar_id, copy_event_id)
                    
                    if success:
                        print(f"   ✅ Copia eliminada exitosamente")
                    else:
                        print(f"   ❌ Error al eliminar copia")
            else:
                print(f"   📄 No existe copia")
                
                if filmmaker_asignado:
                    # CASO C: NO existe copia PERO filmmaker SÍ está asignado → CREAR
                    print(f"   ➕ Creando nueva copia...")
                    
                    extended_props = {
                        'private': {
                            'master_event_id': master_event_id
                        }
                    }
                    
                    success = create_google_event(
                        google_service,
                        calendar_id,
                        master_event,  # Usar datos del evento maestro directamente
                        extended_properties=extended_props
                    )
                    
                    if success:
                        print(f"   ✅ Copia creada exitosamente")
                    else:
                        print(f"   ❌ Error al crear copia")
                else:
                    # CASO D: NO existe copia Y filmmaker NO está asignado → NO HACER NADA
                    print(f"   ⏭️  No hay acción necesaria")
        
        print(f"\n✅ SINCRONIZACIÓN DESDE GOOGLE COMPLETADA")
        print(f"📊 Resumen: Evento maestro '{master_event.get('summary', 'Sin título')}' propagado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en sincronización desde Google: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_monday_date_column(item_id, board_id, column_id, date_value, time_value=None, monday_handler=None):
    """
    Actualiza una columna de fecha en Monday.com usando la regla de oro.
    
    Args:
        item_id: ID del item
        board_id: ID del tablero
        column_id: ID de la columna de fecha
        date_value: Fecha en formato "YYYY-MM-DD"
        time_value: Hora en formato "HH:MM:SS" (opcional)
        monday_handler: Instancia de MondayAPIHandler ya inicializada
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
    
    # Verificar que monday_handler está disponible
    if monday_handler is None:
        print("❌ Error: monday_handler no proporcionado")
        return False
    
    try:
        # Usar el handler para actualizar la columna de fecha
        date_object = {"date": date_value}
        if time_value:
            date_object["time"] = time_value
        
        success = monday_handler.update_column_value(
            item_id, 
            board_id, 
            column_id, 
            date_object,
            'date'
        )
        
        if success:
            print(f"✅ Escritura de fecha en Monday OK.")
            return True
        else:
            print(f"❌ ERROR al escribir fecha en Monday")
            return False
        
    except Exception as e:
        print(f"❌ ERROR al escribir fecha en Monday: {e}")
        return False

def update_monday_date_column_v2(item_id, board_id, column_id, date_value, time_value=None, monday_handler=None):
    """
    Actualiza una columna de fecha en Monday.com usando change_column_value.
    Esta función es más robusta para columnas de fecha complejas.
    
    Args:
        item_id: ID del item
        board_id: ID del tablero
        column_id: ID de la columna de fecha
        date_value: Fecha en formato "YYYY-MM-DD"
        time_value: Hora en formato "HH:MM:SS" (opcional)
        monday_handler: Instancia de MondayAPIHandler ya inicializada (opcional)
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
    
    # Verificar que monday_handler está disponible
    if monday_handler is None:
        print("❌ Error: monday_handler no proporcionado")
        return False
    
    try:
        # Usar el handler para actualizar la columna de fecha
        date_object = {"date": date_value}
        if time_value:
            date_object["time"] = time_value
        
        success = monday_handler.update_column_value(
            item_id, 
            board_id, 
            column_id, 
            date_object,
            'date'
        )
        
        if success:
            print(f"✅ Escritura de fecha en Monday OK.")
            return True
        else:
            print(f"❌ ERROR al escribir fecha en Monday")
            return False
        
    except Exception as e:
        print(f"❌ ERROR al escribir fecha en Monday: {e}")
        return False 

def _obtener_item_id_por_google_event_id(google_event_id, monday_handler):
    """
    Obtiene el item_id de Monday.com usando el Google Event ID.
    Versión robusta con limpieza de datos y logging detallado.
    
    Args:
        google_event_id (str): ID del evento de Google Calendar
        monday_handler: Instancia de MondayAPIHandler
        
    Returns:
        str: ID del item de Monday, o None si no se encuentra
    """
    # 1. LIMPIAR EL GOOGLE_EVENT_ID
    cleaned_event_id = google_event_id.strip().replace('"', '').replace("'", "")
    print(f"🔍 Buscando item en Monday con Google Event ID: '{cleaned_event_id}'")
    print(f"   ID original: '{google_event_id}'")
    print(f"   ID limpio: '{cleaned_event_id}'")
    
    # 2. CONSULTA ROBUSTA USANDO items específicos por ID
    # Primero intentamos buscar el item específico por su ID
    query = f"""
    query {{
        items(ids: [9733398727]) {{
            id
            name
            column_values(ids: ["{config.COL_GOOGLE_EVENT_ID}"]) {{
                id
                text
                value
            }}
        }}
    }}
    """
    
    data = {'query': query}
    
    # 3. LOGGING DETALLADO DE LA CONSULTA
    print(f"📋 Query GraphQL enviada a Monday:")
    print(f"   {query}")
    print(f"📋 Variables enviadas:")
    print(f"   board_id: {config.BOARD_ID_GRABACIONES}")
    print(f"   column_id: {config.COL_GOOGLE_EVENT_ID}")
    print(f"   buscando_value: '{cleaned_event_id}'")
    
    try:
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        
        # 4. LOGGING DE LA RESPUESTA
        print(f"📡 Respuesta de Monday:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"   Response Text: {response.text}")
            return None
            
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error GraphQL de Monday:")
            for error in response_data['errors']:
                print(f"   {error}")
            return None
        
        # 5. PROCESAR RESULTADOS
        items = response_data.get('data', {}).get('items', [])
        print(f"📊 Items encontrados: {len(items)}")
        
        if not items:
            print(f"❌ No se encontró ningún item en Monday con Google Event ID: '{cleaned_event_id}'")
            print(f"   Board ID: {config.BOARD_ID_GRABACIONES}")
            print(f"   Column ID: {config.COL_GOOGLE_EVENT_ID}")
            return None
        
        # 6. VERIFICAR RESULTADOS
        for item in items:
            item_id = item.get('id')
            item_name = item.get('name')
            column_values = item.get('column_values', [])
            
            print(f"🔍 Verificando item: '{item_name}' (ID: {item_id})")
            
            for col in column_values:
                if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                    text_value = col.get('text', '').strip()
                    print(f"   Columna {config.COL_GOOGLE_EVENT_ID}: '{text_value}'")
                    
                    if text_value == cleaned_event_id:
                        print(f"✅ ¡MATCH ENCONTRADO! Item: '{item_name}' (ID: {item_id})")
                        return item_id
                    else:
                        print(f"   ❌ No coincide: '{text_value}' != '{cleaned_event_id}'")
        
        print(f"❌ No se encontró ningún item con el Google Event ID exacto: '{cleaned_event_id}'")
        return None
        
    except Exception as e:
        print(f"❌ Error inesperado al obtener item_id:")
        print(f"   Exception: {type(e).__name__}: {e}")
        print(f"   Query enviada: {query}")
        print(f"   Variables: board_id={config.BOARD_ID_GRABACIONES}, column_id={config.COL_GOOGLE_EVENT_ID}, buscando_value='{cleaned_event_id}'")
        return None

def _adaptar_item_monday_a_evento_google(item_procesado, board_id=None):
    """
    Adapta un item procesado de Monday al formato esperado por la API de Google Calendar.
    
    Args:
        item_procesado: Diccionario con datos procesados de Monday
        board_id: ID del tablero de Monday para generar el link (opcional)
    
    Returns:
        dict: Diccionario con el formato de evento de Google Calendar
    """
    # Lógica del Link de Dropbox
    dropbox_link = item_procesado.get('linkdropbox', '')
    if dropbox_link:
        dropbox_link_html = f'<a href="{dropbox_link}">Abrir Enlace</a>'
    else:
        dropbox_link_html = '<i>Sin link a Dropbox Dron</i>'
    
    # Generar link a Monday si se proporciona board_id
    monday_link = ""
    if board_id and item_procesado.get('id'):
        monday_link = f'<b>🔗 Link a Monday:</b> <a href="https://monday.com/boards/{board_id}/pulses/{item_procesado["id"]}">Ver Item</a>'
    
    # Construimos la descripción del evento usando HTML para que se vea bien
    description = f"""<b>Cliente:</b> {item_procesado.get('cliente', 'N/A')}
<b>Grupo:</b> {item_procesado.get('group_title', 'N/A')}
<b>📋 Estado Permisos:</b> {item_procesado.get('estadopermisos', 'N/A')}
<b>🛠️ Acciones a Realizar:</b> {item_procesado.get('accionesrealizar', 'N/A')}

<b>--- 📞 Contactos de Obra ---</b>
{item_procesado.get('contacto_obra_formateado', 'No disponible')}

<b>--- 👤 Contactos Comerciales ---</b>
{item_procesado.get('contacto_comercial_formateado', 'No disponible')}

<b>--- 🔗 Enlaces y Novedades ---</b>
{monday_link}
<b>Link Dropbox Dron:</b> {dropbox_link_html}
<b>Updates en el elemento en Monday:</b>
{item_procesado.get('all_updates_html', '<i>Sin updates.</i>')}
    """

    # Determinar si es evento de día completo o con hora específica
    fecha_inicio = item_procesado['fecha_inicio']
    fecha_fin = item_procesado['fecha_fin']
    
    if 'T' in fecha_inicio:
        # Evento con hora específica
        event = {
            'summary': item_procesado['name'],
            'location': item_procesado.get('ubicacion', ''),
            'description': description,
            'guestsCanModify': False,
            'start': {
                'dateTime': fecha_inicio,
                'timeZone': 'Europe/Madrid',
            },
            'end': {
                'dateTime': fecha_fin,
                'timeZone': 'Europe/Madrid',
            },
        }
    else:
        # Evento de día completo
        event = {
            'summary': item_procesado['name'],
            'location': item_procesado.get('ubicacion', ''),
            'description': description,
            'guestsCanModify': False,
            'start': {
                'date': fecha_inicio,
            },
            'end': {
                'date': fecha_fin,
            },
        }
    
    return event

def _obtener_operarios_actuales(item_id, monday_handler):
    """
    Obtiene la lista de operarios actuales de un item de Monday.com.
    
    Args:
        item_id (str): ID del item de Monday.com
        monday_handler: Instancia de MondayAPIHandler
        
    Returns:
        set: Conjunto de nombres de operarios asignados
    """
    query = f"""
    query {{
        items(ids: [{item_id}]) {{
            id
            name
            column_values(ids: ["{config.COLUMN_MAP_REVERSE['Operario']}"]) {{
                id
                text
                value
                type
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
            print(f"❌ Error al obtener operarios: {response_data['errors']}")
            return set()
        
        items = response_data.get('data', {}).get('items', [])
        if not items:
            print(f"❌ No se encontró el item {item_id}")
            return set()
        
        item = items[0]
        operarios_actuales = set()
        
        # Procesar la columna de operario
        column_values = item.get('column_values', [])
        for col in column_values:
            if col.get('id') == config.COLUMN_MAP_REVERSE['Operario']:
                operario_text = col.get('text', '')
                if operario_text:
                    # Si hay múltiples operarios separados por comas, procesar cada uno
                    operarios_lista = [op.strip() for op in operario_text.split(',') if op.strip()]
                    operarios_actuales.update(operarios_lista)
                    break
        
        return operarios_actuales
        
    except Exception as e:
        print(f"❌ Error al obtener operarios actuales: {e}")
        return set() 