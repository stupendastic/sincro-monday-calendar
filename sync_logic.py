import json
import requests
import os
import uuid
import time
from datetime import datetime, timedelta

# Importaciones de nuestros módulos
import config
from google_calendar_service import get_calendar_service, create_google_event, update_google_event, update_google_event_by_id, create_and_share_calendar, find_event_copy_by_master_id, delete_event_by_id
from monday_api_handler import MondayAPIHandler

def generar_uuid_cambio():
    """Genera un UUID único para identificar un cambio específico"""
    return str(uuid.uuid4())

def registrar_cambio_reciente(item_id, change_uuid, timestamp=None):
    """Registra un cambio reciente con su UUID único"""
    if timestamp is None:
        timestamp = time.time()
    
    if not hasattr(config, 'RECENT_CHANGES'):
        config.RECENT_CHANGES = {}
    
    if item_id not in config.RECENT_CHANGES:
        config.RECENT_CHANGES[item_id] = {}
    
    config.RECENT_CHANGES[item_id][change_uuid] = timestamp
    print(f"🆔 Registrado cambio {change_uuid[:8]}... para item {item_id}")

def es_cambio_reciente(item_id, change_uuid, window_seconds=30):
    """Verifica si un cambio específico ya fue procesado recientemente"""
    if not hasattr(config, 'RECENT_CHANGES'):
        return False
    
    if item_id not in config.RECENT_CHANGES:
        return False
    
    if change_uuid not in config.RECENT_CHANGES[item_id]:
        return False
    
    timestamp = config.RECENT_CHANGES[item_id][change_uuid]
    current_time = time.time()
    
    # Si el cambio es muy reciente, lo consideramos duplicado
    if current_time - timestamp < window_seconds:
        print(f"⚠️  Cambio {change_uuid[:8]}... procesado recientemente. Saltando...")
        return True
    
    return False

def limpiar_cambios_antiguos(window_seconds=300):
    """Limpia cambios antiguos del registro"""
    if not hasattr(config, 'RECENT_CHANGES'):
        return
    
    current_time = time.time()
    items_to_remove = []
    
    for item_id, changes in config.RECENT_CHANGES.items():
        changes_to_remove = []
        for change_uuid, timestamp in changes.items():
            if current_time - timestamp > window_seconds:
                changes_to_remove.append(change_uuid)
        
        for change_uuid in changes_to_remove:
            del changes[change_uuid]
        
        if not changes:
            items_to_remove.append(item_id)
    
    for item_id in items_to_remove:
        del config.RECENT_CHANGES[item_id]

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
    
    # Diccionario para rastrear cambios recientes con UUIDs únicos
    # {item_id: {change_uuid: timestamp}}
    if not hasattr(config, 'RECENT_CHANGES'):
        config.RECENT_CHANGES = {}
    
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
            
            # Normalizar formato de Google (convertir a UTC si es necesario)
            if fecha_hora_google.endswith('Z'):
                # Google en UTC, convertir a string sin Z
                fecha_hora_google = fecha_hora_google[:-1]
            elif '+' in fecha_hora_google:
                # Google con zona horaria, extraer solo la parte sin zona horaria
                fecha_hora_google = fecha_hora_google.split('+')[0]
            
            # Normalizar formato de Monday si es necesario
            if 'T' in fecha_monday:
                # Monday ya tiene formato ISO, extraer solo la parte sin zona horaria
                if '+' in fecha_monday:
                    fecha_monday_normalizada = fecha_monday.split('+')[0]
                else:
                    fecha_monday_normalizada = fecha_monday
            else:
                # Monday solo tiene fecha, agregar hora por defecto
                fecha_monday_normalizada = f"{fecha_monday}T00:00:00"
            
            # Comparar fechas normalizadas (sin zonas horarias)
            try:
                # Parsear fechas sin zonas horarias para comparación directa
                dt_monday = datetime.fromisoformat(fecha_monday_normalizada)
                dt_google = datetime.fromisoformat(fecha_hora_google)
                
                # Comparar con tolerancia de 1 minuto para manejar pequeñas diferencias
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
        # Si ya tiene un Google Event ID, usar el calendario maestro
        # Si no tiene, usar el calendario de eventos sin asignar
        google_event_id = item_procesado.get('google_event_id')
        if google_event_id:
            # Si ya existe un evento, debe estar en el calendario maestro
            calendar_id = config.MASTER_CALENDAR_ID
        else:
            # Si es nuevo, crear en el calendario de eventos sin asignar
            calendar_id = config.UNASSIGNED_CALENDAR_ID
        
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
        
        # Mantener las extended_properties existentes o crear nuevas si no existen
        extended_props = {
            'private': {
                'master_event_id': google_event_id
            }
        }
        
        success = update_google_event_by_id(google_service, calendar_id, google_event_id, event_body, extended_properties=extended_props)
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
        
        # Crear extended_properties para el evento maestro (se referenciará a sí mismo)
        # Primero creamos el evento sin extended_properties para obtener su ID
        temp_event_id = create_google_event(google_service, calendar_id, event_body)
        
        if temp_event_id:
            # Ahora actualizamos el evento con las extended_properties que incluyen su propio ID
            extended_props = {
                'private': {
                    'master_event_id': temp_event_id
                }
            }
            
            # Actualizar el evento con las propiedades extendidas
            updated_event_id = update_google_event_by_id(google_service, calendar_id, temp_event_id, event_body, extended_properties=extended_props)
            new_event_id = updated_event_id if updated_event_id else temp_event_id
        else:
            new_event_id = None
        
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

def sincronizar_item_via_webhook(item_id, monday_handler, google_service=None, change_uuid: str = None):
    """
    Sincroniza un item específico de Monday.com con Google Calendar - VERSIÓN OPTIMIZADA PARA WEBHOOKS.
    
    Esta función es una versión ligera que evita la inicialización completa del entorno
    y se enfoca únicamente en procesar el item específico para máxima velocidad.
    
    Args:
        item_id (int): ID del item de Monday.com a sincronizar
        monday_handler: Instancia de MondayAPIHandler ya inicializada
        google_service: Instancia del servicio de Google Calendar ya inicializada (opcional)
        change_uuid (str): UUID único del cambio (opcional)
        
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario
    """
    # Generar UUID si no se proporciona
    if change_uuid is None:
        change_uuid = generar_uuid_cambio()
    
    # Verificar si este cambio ya fue procesado
    if es_cambio_reciente(item_id, change_uuid):
        print(f"⚠️  Cambio {change_uuid[:8]}... ya procesado recientemente. Saltando...")
        return True  # Consideramos éxito para evitar reintentos
    
    # Registrar este cambio
    registrar_cambio_reciente(item_id, change_uuid)
    
    print(f"⚡ INICIANDO SINCRONIZACIÓN WEBHOOK - Item {item_id}")
    print("=" * 50)
    print(f"🆔 UUID del cambio: {change_uuid}")
    
    # Limpiar cambios antiguos
    limpiar_cambios_antiguos()
    
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
        
        # Si ya tiene un Google Event ID, usar el calendario maestro
        # Si no tiene, usar el calendario de eventos sin asignar
        google_event_id = item_procesado.get('google_event_id')
        if google_event_id:
            # Si ya existe un evento, debe estar en el calendario maestro
            calendar_id = config.MASTER_CALENDAR_ID
        else:
            # Si es nuevo, crear en el calendario de eventos sin asignar
            calendar_id = config.UNASSIGNED_CALENDAR_ID
        
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


def sincronizar_desde_google(master_event_id, monday_handler, google_service=None, change_uuid: str = None):
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
        change_uuid (str): UUID único del cambio (opcional)
        
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario
    """
    # Generar UUID si no se proporciona
    if change_uuid is None:
        change_uuid = generar_uuid_cambio()
    
    # Verificar si este cambio ya fue procesado
    if es_cambio_reciente(master_event_id, change_uuid):
        print(f"⚠️  Cambio {change_uuid[:8]}... ya procesado recientemente. Saltando...")
        return True  # Consideramos éxito para evitar reintentos
    
    # Registrar este cambio
    registrar_cambio_reciente(master_event_id, change_uuid)
    
    print(f"🔄 INICIANDO SINCRONIZACIÓN DESDE GOOGLE")
    print(f"📋 Evento maestro: {master_event_id}")
    print("=" * 60)
    print(f"🆔 UUID del cambio: {change_uuid}")
    
    # Limpiar cambios antiguos
    limpiar_cambios_antiguos()
    
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
        # FAST-PATH: intentar por nombre exacto primero (evita escanear todo el tablero)
        nombre_evento = master_event.get('summary') or ''
        item_id = _obtener_item_id_por_nombre(nombre_evento, monday_handler)
        if not item_id:
            # Fallback al método por Google Event ID
            item_id = _obtener_item_id_por_google_event_id(master_event_id, monday_handler)
        if not item_id:
            print(f"❌ No se pudo obtener el item_id de Monday")
            return False
        
        print(f"✅ Item ID de Monday obtenido: {item_id}")
        
        # ========================================
        # 🤖 DETECCIÓN DE AUTOMATIZACIÓN (ANTI-BUCLES)
        # ========================================
        print("\n🛡️ VERIFICANDO ORIGEN DEL CAMBIO...")
        print("-" * 40)
        
        es_automatizacion = _detectar_cambio_de_automatizacion(item_id, monday_handler)
        
        if es_automatizacion:
            print(f"🤖 ¡CAMBIO DE AUTOMATIZACIÓN DETECTADO!")
            print(f"🛑 El último cambio fue hecho por la cuenta de automatización ({config.AUTOMATION_USER_NAME})")
            print(f"🔄 Esto significa que el cambio vino del sistema, no de un usuario real")
            print(f"✋ FRENANDO SINCRONIZACIÓN para evitar bucle infinito")
            return True  # Retornamos éxito pero NO sincronizamos
        else:
            print(f"👤 Cambio detectado de USUARIO REAL")
            print(f"✅ Continuando con sincronización normal...")
        
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

def _obtener_item_id_por_google_event_id_mejorado(google_event_id, monday_handler):
    """
    Obtiene el item_id de Monday.com usando el Google Event ID.
    Versión optimizada que usa búsqueda eficiente con límites.
    
    Args:
        google_event_id (str): ID del evento de Google Calendar
        monday_handler: Instancia de MondayAPIHandler
        
    Returns:
        str: ID del item de Monday, o None si no se encuentra
    """
    # 1. LIMPIAR EL GOOGLE_EVENT_ID
    cleaned_event_id = google_event_id.strip().replace('"', '').replace("'", "")
    print(f"🔍 Buscando item en Monday con Google Event ID: '{cleaned_event_id}'")
    
    try:
        # 2. BÚSQUEDA EFICIENTE: Primero buscar en los últimos 100 items (más probable)
        items = monday_handler.get_items(
            board_id=str(config.BOARD_ID_GRABACIONES),
            column_ids=[config.COL_GOOGLE_EVENT_ID],
            limit_per_page=100  # Buscar solo en los últimos 100 items
        )
        
        print(f"📊 Items en búsqueda inicial: {len(items)}")
        
        # 3. BUSCAR EN LOS ÚLTIMOS ITEMS (más probable que tengan Google Event ID)
        for item in items:
            item_id = item.get('id')
            item_name = item.get('name')
            column_values = item.get('column_values', [])
            
            for col in column_values:
                if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                    text_value = col.get('text', '').strip()
                    if text_value == cleaned_event_id:
                        print(f"✅ Item encontrado en búsqueda inicial: '{item_name}' (ID: {item_id})")
                        return item_id
        
        # 4. SI NO SE ENCUENTRA, BUSCAR EN ITEMS MÁS ANTIGUOS (paginación)
        print(f"🔍 Item no encontrado en búsqueda inicial. Buscando en items más antiguos...")
        
        # Obtener más items (hasta 500 total)
        all_items = items
        page_count = 0
        max_pages = 5  # Máximo 5 páginas para evitar búsquedas infinitas
        
        while len(all_items) < 500 and page_count < max_pages:
            page_count += 1
            print(f"📄 Buscando en página {page_count}...")
            
            # Obtener siguiente página
            next_items = monday_handler.get_items(
                board_id=str(config.BOARD_ID_GRABACIONES),
                column_ids=[config.COL_GOOGLE_EVENT_ID],
                limit_per_page=100
            )
            
            if not next_items or len(next_items) == 0:
                break
                
            all_items.extend(next_items)
            
            # Buscar en esta página
            for item in next_items:
                item_id = item.get('id')
                item_name = item.get('name')
                column_values = item.get('column_values', [])
                
                for col in column_values:
                    if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                        text_value = col.get('text', '').strip()
                        if text_value == cleaned_event_id:
                            print(f"✅ Item encontrado en página {page_count}: '{item_name}' (ID: {item_id})")
                            return item_id
        
        print(f"❌ No se encontró ningún item con Google Event ID: '{cleaned_event_id}' después de buscar en {len(all_items)} items")
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener item_id usando MondayAPIHandler: {e}")
        return None

def _obtener_item_id_por_google_event_id_optimizado(google_event_id, monday_handler):
    """
    Versión SÚPER OPTIMIZADA para buscar item_id por Google Event ID.
    Usa búsqueda limitada y eficiente.
    """
    print(f"⚡ Búsqueda SÚPER OPTIMIZADA: '{google_event_id}'")
    
    try:
        # BÚSQUEDA LIMITADA Y EFICIENTE
        # Buscar solo en los últimos 100 items (más probable que tengan Google Event ID)
        query = f"""
        query {{
            boards(ids: [{config.BOARD_ID_GRABACIONES}]) {{
                items_page(limit: 100) {{
                    items {{
                        id
                        name
                        column_values(ids: ["{config.COL_GOOGLE_EVENT_ID}"]) {{
                            id
                            text
                        }}
                    }}
                }}
            }}
        }}
        """
        
        response = monday_handler._make_request(query)
        
        if response and 'data' in response:
            boards = response['data'].get('boards', [])
            if boards:
                items_page = boards[0].get('items_page', {})
                items = items_page.get('items', [])
                
                print(f"📊 Buscando en {len(items)} items recientes")
                
                # Buscar el item con el Google Event ID específico
                for item in items:
                    item_id = item.get('id')
                    item_name = item.get('name', 'Sin nombre')
                    column_values = item.get('column_values', [])
                    
                    for column in column_values:
                        if column.get('id') == config.COL_GOOGLE_EVENT_ID:
                            stored_event_id = column.get('text', '').strip()
                            if stored_event_id == google_event_id:
                                print(f"✅ Item encontrado SÚPER RÁPIDO: '{item_name}' (ID: {item_id})")
                                return item_id
        
        print(f"❌ No se encontró item con Google Event ID: '{google_event_id}' en items recientes")
        return None
        
    except Exception as e:
        print(f"❌ Error en búsqueda optimizada: {e}")
        # Fallback a búsqueda por nombre si la búsqueda directa falla
        print("🔄 Usando fallback por nombre...")
        return _buscar_por_nombre_fallback(google_event_id, monday_handler)

def _buscar_por_nombre_fallback(google_event_id, monday_handler):
    """
    Fallback: buscar por nombre del evento en Google Calendar
    """
    try:
        # Obtener el evento de Google para obtener el nombre
        google_service = get_calendar_service()
        if not google_service:
            return None
        
        # Buscar en el calendario maestro
        event = google_service.events().get(
            calendarId=config.MASTER_CALENDAR_ID,
            eventId=google_event_id
        ).execute()
        
        event_name = event.get('summary', '')
        if event_name:
            print(f"🔍 Buscando por nombre del evento: '{event_name}'")
            return _obtener_item_id_por_nombre(event_name, monday_handler)
        
        return None
        
    except Exception as e:
        print(f"❌ Error en fallback por nombre: {e}")
        return None

def _obtener_item_id_por_nombre(item_name, monday_handler):
    """
    Busca el item_id en Monday.com por nombre EXACTO usando una query paginada eficiente.
    Devuelve el primer match exacto encontrado o None.
    """
    try:
        if not item_name:
            return None
        # Usar el método del handler que ya implementa búsqueda por nombre con items_page
        items = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name=item_name,
            exact_match=True
        )
        if items:
            # Devolver el primer resultado
            return items[0].id
        return None
    except Exception as e:
        print(f"❌ Error buscando por nombre '{item_name}': {e}")
        return None

def _detectar_cambio_de_automatizacion(item_id, monday_handler):
    """
    Detecta si el último cambio en un item fue hecho por la cuenta de automatización.
    
    Args:
        item_id (str): ID del item de Monday
        monday_handler: Instancia de MondayAPIHandler
        
    Returns:
        bool: True si el último cambio fue hecho por automatización
    """
    try:
        # Obtener actualizaciones recientes del item
        query = f"""
        query {{
            items(ids: [{item_id}]) {{
                id
                name
                updates(limit: 5) {{
                    id
                    creator {{
                        id
                        name
                    }}
                    created_at
                    body
                }}
            }}
        }}
        """
        
        response = monday_handler._make_request(query)
        
        if response and 'data' in response:
            items = response['data'].get('items', [])
            if items:
                item = items[0]
                updates = item.get('updates', [])
                
                if updates:
                    # Revisar las últimas actualizaciones
                    for update in updates[:3]:  # Solo las 3 más recientes
                        creator = update.get('creator', {})
                        creator_id = creator.get('id')
                        creator_name = creator.get('name', '')
                        created_at = update.get('created_at')
                        body = update.get('body', '')
                        
                        print(f"📝 Update: {creator_name} ({creator_id}) - {created_at}")
                        print(f"   Contenido: {body[:100]}...")
                        
                        # Verificar si fue tu cuenta (automatización)
                        if str(creator_id) == str(config.AUTOMATION_USER_ID):
                            print(f"🤖 ¡Detectado cambio de AUTOMATIZACIÓN! Usuario: {creator_name}")
                            return True
                        
                        # También verificar por nombre como fallback
                        if creator_name == config.AUTOMATION_USER_NAME:
                            print(f"🤖 ¡Detectado cambio de AUTOMATIZACIÓN por nombre! Usuario: {creator_name}")
                            return True
                
                print("👤 Último cambio fue de usuario REAL, no automatización")
                return False
        
        print("⚠️ No se pudieron obtener actualizaciones del item")
        return False
        
    except Exception as e:
        print(f"❌ Error detectando automatización: {e}")
        return False

def _obtener_item_id_por_google_event_id(google_event_id, monday_handler):
    """
    Wrapper para mantener compatibilidad con código existente.
    Usa la versión optimizada por defecto.
    """
    return _obtener_item_id_por_google_event_id_optimizado(google_event_id, monday_handler)

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

def sincronizar_desde_google_calendar(evento_cambiado, google_service, monday_handler, change_uuid: str = None):
    """
    Sincroniza cambios desde Google Calendar a Monday.com y propaga a calendarios personales.
    
    Args:
        evento_cambiado (dict): Evento de Google Calendar que ha cambiado
        google_service: Servicio de Google Calendar
        monday_handler: Instancia de MondayAPIHandler
        change_uuid (str): UUID único del cambio (opcional)
        
    Returns:
        bool: True si la sincronización fue exitosa
    """
    # Generar UUID si no se proporciona
    if change_uuid is None:
        change_uuid = generar_uuid_cambio()
    
    # Verificar si este cambio ya fue procesado
    event_id = evento_cambiado.get('id')
    if es_cambio_reciente(event_id, change_uuid):
        print(f"⚠️  Cambio {change_uuid[:8]}... ya procesado recientemente. Saltando...")
        return True  # Consideramos éxito para evitar reintentos
    
    # Registrar este cambio
    registrar_cambio_reciente(event_id, change_uuid)
    
    print(f"\n🔄 SINCRONIZANDO DESDE GOOGLE CALENDAR")
    print("=" * 50)
    print(f"🆔 UUID del cambio: {change_uuid}")
    
    # Limpiar cambios antiguos
    limpiar_cambios_antiguos()
    
    try:
        # 1. Extraer información del evento
        event_id = evento_cambiado.get('id')
        event_summary = evento_cambiado.get('summary', 'Sin título')
        
        print(f"📋 Evento: {event_summary} (ID: {event_id})")
        
        # 2. Buscar el item de Monday correspondiente
        item_id = None
        
        # Fast-path: buscar por nombre
        if event_summary:
            print(f"🔍 Buscando por nombre: '{event_summary}'")
            try:
                items_by_name = monday_handler.search_items_by_name(
                    board_id=str(config.BOARD_ID_GRABACIONES),
                    item_name=event_summary,
                    exact_match=True
                )
                if items_by_name:
                    item_id = items_by_name[0].id
                    print(f"✅ Encontrado por nombre: {item_id}")
            except Exception as e:
                print(f"⚠️ Error buscando por nombre: {e}")
        
        # Fallback: buscar por Google Event ID
        if not item_id:
            print(f"🔍 Buscando por Google Event ID: {event_id}")
            item_id = _obtener_item_id_por_google_event_id(event_id, monday_handler)
        
        if not item_id:
            print(f"❌ No se pudo encontrar el item de Monday correspondiente")
            return False
        
        print(f"✅ Item de Monday encontrado: {item_id}")
        
        # 3. Extraer nueva fecha/hora del evento de Google
        start = evento_cambiado.get('start', {})
        end = evento_cambiado.get('end', {})
        
        if 'dateTime' in start:
            # Evento con hora específica
            fecha_inicio = start['dateTime']
            fecha_fin = end.get('dateTime', fecha_inicio)
            
            # Convertir a formato de Monday
            from datetime import datetime
            dt_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
            
            fecha_monday = dt_inicio.strftime('%Y-%m-%d')
            hora_monday = dt_inicio.strftime('%H:%M:%S')
            
            print(f"📅 Nueva fecha: {fecha_monday} {hora_monday}")
            
        elif 'date' in start:
            # Evento de día completo
            fecha_monday = start['date']
            hora_monday = None
            
            print(f"📅 Nueva fecha: {fecha_monday} (día completo)")
        else:
            print(f"❌ Formato de fecha no reconocido")
            return False
        
        # 4. Actualizar Monday.com
        print(f"🔄 Actualizando Monday.com...")
        
        success = update_monday_date_column_v2(
            item_id=item_id,
            board_id=str(config.BOARD_ID_GRABACIONES),
            column_id=config.COL_FECHA,
            date_value=fecha_monday,
            time_value=hora_monday,
            monday_handler=monday_handler
        )
        
        if not success:
            print(f"❌ Error actualizando Monday.com")
            return False
        
        print(f"✅ Monday.com actualizado exitosamente")
        
        # 5. Propagar cambios a calendarios personales
        print(f"🔄 Propagando cambios a calendarios personales...")
        
        # Obtener operarios actuales del item
        operarios_actuales = _obtener_operarios_actuales(item_id, monday_handler)
        print(f"👥 Operarios actuales: {operarios_actuales}")
        
        # Actualizar copias en calendarios personales
        for profile in config.FILMMAKER_PROFILES:
            if profile["monday_name"] in operarios_actuales:
                calendar_id = profile["calendar_id"]
                print(f"🔄 Actualizando copia para {profile['monday_name']}...")
                
                # Buscar la copia existente
                copia_event_id = _buscar_evento_copia_por_master_id(event_id, calendar_id, google_service)
                
                if copia_event_id:
                    # Actualizar la copia existente
                    try:
                        # Crear el cuerpo del evento actualizado
                        event_body = {
                            'summary': event_summary,
                            'start': start,
                            'end': end,
                            'extendedProperties': {
                                'private': {
                                    'master_event_id': event_id,
                                    'monday_item_id': str(item_id)
                                }
                            }
                        }
                        
                        # Actualizar el evento
                        updated_event = google_service.events().update(
                            calendarId=calendar_id,
                            eventId=copia_event_id,
                            body=event_body
                        ).execute()
                        
                        print(f"✅ Copia actualizada: {updated_event['id']}")
                        
                    except Exception as e:
                        print(f"❌ Error actualizando copia: {e}")
                else:
                    print(f"⚠️ No se encontró copia para {profile['monday_name']}")
        
        print(f"✅ Sincronización desde Google Calendar completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en sincronización desde Google Calendar: {e}")
        return False

def _buscar_evento_copia_por_master_id(master_event_id, calendar_id, google_service):
    """
    Busca un evento copia por su master_event_id en un calendario específico.
    
    Args:
        master_event_id (str): ID del evento maestro
        calendar_id (str): ID del calendario donde buscar
        google_service: Servicio de Google Calendar
        
    Returns:
        str: ID del evento copia si se encuentra, None en caso contrario
    """
    try:
        # Buscar eventos en el calendario
        events_result = google_service.events().list(
            calendarId=calendar_id,
            maxResults=100
        ).execute()
        
        events = events_result.get('items', [])
        
        for event in events:
            extended_props = event.get('extendedProperties', {})
            private_props = extended_props.get('private', {})
            
            if private_props.get('master_event_id') == master_event_id:
                return event['id']
        
        return None
        
    except Exception as e:
        print(f"❌ Error buscando evento copia: {e}")
        return None

def sincronizar_desde_calendario_personal(evento_cambiado, calendar_id, google_service, monday_handler):
    """
    Sincroniza cambios desde un calendario personal hacia el máster y Monday.com.
    Solo funciona si el cambio fue hecho por la cuenta admin.
    
    Args:
        evento_cambiado: Evento de Google Calendar que cambió
        calendar_id: ID del calendario personal donde ocurrió el cambio
        google_service: Servicio de Google Calendar
        monday_handler: Handler de Monday.com
    
    Returns:
        bool: True si la sincronización fue exitosa
    """
    print(f"\n🔄 SINCRONIZANDO DESDE CALENDARIO PERSONAL")
    print("=" * 60)
    
    event_id = evento_cambiado.get('id')
    event_summary = evento_cambiado.get('summary', 'Sin título')
    
    print(f"📋 Evento: {event_summary} (ID: {event_id})")
    print(f"📅 Calendario personal: {calendar_id}")
    
    # 1. Verificar que es un evento copia (debe tener master_event_id)
    extended_props = evento_cambiado.get('extendedProperties', {})
    private_props = extended_props.get('private', {})
    master_event_id = private_props.get('master_event_id')
    
    if not master_event_id:
        print(f"❌ No es un evento copia (no tiene master_event_id)")
        return False
    
    print(f"🎯 Evento maestro: {master_event_id}")
    
    # 2. Buscar el item de Monday.com usando el master_event_id
    print(f"🔍 Buscando item de Monday con master_event_id: {master_event_id}")
    
    item_id = _obtener_item_id_por_google_event_id_optimizado(master_event_id, monday_handler)
    
    if not item_id:
        print(f"❌ No se encontró el item de Monday correspondiente")
        return False
    
    print(f"✅ Item de Monday encontrado: {item_id}")
    
    # 3. Extraer la nueva fecha del evento
    start = evento_cambiado.get('start', {})
    if 'dateTime' in start:
        fecha_str = start['dateTime']
        # Convertir a datetime para formatear
        from datetime import datetime
        fecha_dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
        fecha_formateada = fecha_dt.strftime('%Y-%m-%d')
        hora_formateada = fecha_dt.strftime('%H:%M:%S')
    elif 'date' in start:
        fecha_formateada = start['date']
        hora_formateada = None
    else:
        print(f"❌ No se pudo extraer la fecha del evento")
        return False
    
    print(f"📅 Nueva fecha: {fecha_formateada} {hora_formateada if hora_formateada else ''}")
    
    # 4. Actualizar Monday.com
    print(f"🔄 Actualizando Monday.com...")
    try:
        # Preparar el valor de la columna de fecha
        if hora_formateada:
            fecha_value = f"{fecha_formateada} {hora_formateada}"
        else:
            fecha_value = fecha_formateada
        
        # Actualizar la fecha en Monday.com
        success = monday_handler.update_column_value(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_id=item_id,
            column_id=config.COL_FECHA,
            value=fecha_value,
            column_type="date"
        )
        
        if success:
            print(f"✅ Monday.com actualizado exitosamente")
        else:
            print(f"❌ Error actualizando Monday.com")
            return False
            
    except Exception as e:
        print(f"❌ Error actualizando Monday.com: {e}")
        return False
    
    # 5. Actualizar el evento maestro en Google Calendar
    print(f"🔄 Actualizando evento maestro...")
    try:
        # Obtener el evento maestro actual
        master_event = google_service.events().get(
            calendarId=config.MASTER_CALENDAR_ID,
            eventId=master_event_id
        ).execute()
        
        # Actualizar la fecha del evento maestro
        master_event['start'] = evento_cambiado['start']
        master_event['end'] = evento_cambiado['end']
        
        # Actualizar el evento maestro
        updated_master = google_service.events().update(
            calendarId=config.MASTER_CALENDAR_ID,
            eventId=master_event_id,
            body=master_event
        ).execute()
        
        print(f"✅ Evento maestro actualizado: {updated_master['id']}")
        
    except Exception as e:
        print(f"❌ Error actualizando evento maestro: {e}")
        return False
    
    # 6. Propagar el cambio a todos los otros calendarios personales
    print(f"🔄 Propagando cambios a otros calendarios personales...")
    
    try:
        # Obtener todos los perfiles de filmmakers
        filmmaker_profiles = config.FILMMAKER_PROFILES
        
        for filmmaker_name, profile in filmmaker_profiles.items():
            filmmaker_calendar = profile.get('calendar_id')
            
            # Saltar el calendario donde ocurrió el cambio original
            if filmmaker_calendar == calendar_id:
                continue
            
            print(f"  -> Actualizando copia para {filmmaker_name}...")
            
            # Buscar la copia en este calendario
            copy_event = _buscar_evento_copia_por_master_id(master_event_id, filmmaker_calendar, google_service)
            
            if copy_event:
                # Actualizar la copia existente
                copy_event['start'] = evento_cambiado['start']
                copy_event['end'] = evento_cambiado['end']
                
                updated_copy = google_service.events().update(
                    calendarId=filmmaker_calendar,
                    eventId=copy_event['id'],
                    body=copy_event
                ).execute()
                
                print(f"    ✅ Copia actualizada: {updated_copy['id']}")
            else:
                print(f"    ⚠️  No se encontró copia para {filmmaker_name}")
        
        print(f"✅ Propagación completada")
        
    except Exception as e:
        print(f"❌ Error propagando cambios: {e}")
        return False
    
    print(f"✅ Sincronización desde calendario personal completada")
    return True