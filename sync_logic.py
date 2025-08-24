"""
Sync Logic - Clean Version for Unidirectional System
===================================================

This module contains the core synchronization logic for Monday → Google Calendar.
All Google → Monday functions have been removed for unidirectional sync.

Functions included:
- sincronizar_item_via_webhook() - Main Monday → Google sync function
- generate_content_hash() - Content hashing for change detection
- Supporting utility functions
"""

import json
import requests
import time
import hashlib
from datetime import datetime, timedelta

# Importaciones de nuestros módulos
import config
from google_calendar_service import create_google_event, update_google_event
from sync_state_manager import update_sync_state


def generate_content_hash(content_data):
    """
    Genera un hash MD5 determinístico del contenido relevante de un item/evento.
    Solo incluye campos que importan para la sincronización, ignorando metadata.
    
    Args:
        content_data (dict): Diccionario con los datos relevantes del item/evento
        
    Returns:
        str: Hash MD5 del contenido serializado
    """
    # Crear una copia del contenido para no modificar el original
    relevant_data = {}
    
    # Campos relevantes para Monday.com
    if 'name' in content_data:
        relevant_data['name'] = content_data['name']
    if 'fecha_inicio' in content_data:
        relevant_data['fecha_inicio'] = content_data['fecha_inicio']
    if 'fecha_fin' in content_data:
        relevant_data['fecha_fin'] = content_data['fecha_fin']
    if 'operario' in content_data:
        relevant_data['operario'] = content_data['operario']
    
    # Ordenar el diccionario para consistencia
    sorted_content = json.dumps(relevant_data, sort_keys=True, ensure_ascii=False)
    
    # Generar hash MD5
    content_hash = hashlib.md5(sorted_content.encode('utf-8')).hexdigest()
    
    return content_hash


def get_monday_user_directory(monday_handler):
    """Obtiene el directorio de usuarios de Monday.com"""
    try:
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
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error al obtener directorio de usuarios: {response_data['errors']}")
            return None
        
        users = response_data.get('data', {}).get('users', [])
        user_directory = {user['id']: user['name'] for user in users}
        
        return user_directory
        
    except Exception as e:
        print(f"❌ Error al obtener directorio de usuarios: {e}")
        return None


def parse_monday_item(item):
    """Parsea un item de Monday.com a un formato más manejable"""
    try:
        parsed_item = {
            'id': item.get('id'),
            'name': item.get('name', ''),
            'group_title': item.get('group', {}).get('title', '')
        }
        
        # Procesar column_values
        column_values = item.get('column_values', [])
        
        for col in column_values:
            col_id = col.get('id')
            # col_type = col.get('type')  # No utilizado por ahora
            col_text = col.get('text', '')
            col_value = col.get('value')
            
            # Mapear columnas conocidas
            if col_id == config.COL_FECHA:
                parsed_item['fecha_inicio'] = col_text
            elif col_id == config.COL_GOOGLE_EVENT_ID:
                parsed_item['google_event_id'] = col_text
            elif col_id == "personas1":
                parsed_item['operario'] = col_text
                # Procesar IDs de operarios si están disponibles
                if col_value:
                    try:
                        value_data = json.loads(col_value) if isinstance(col_value, str) else col_value
                        if isinstance(value_data, dict) and 'personsAndTeams' in value_data:
                            parsed_item['operario_ids'] = [p.get('id') for p in value_data['personsAndTeams']]
                    except:
                        parsed_item['operario_ids'] = []
            elif col_id == config.COL_CLIENTE:
                parsed_item['cliente'] = col_text
            elif col_id == "ubicaci_n":  # Columna de ubicación
                parsed_item['ubicacion'] = col_text
            
        return parsed_item
        
    except Exception as e:
        print(f"❌ Error parseando item de Monday: {e}")
        return None


def _get_personal_calendar_id_for_item(item_procesado):
    """Obtiene el calendar_id personal según el operario del item.

    Busca por nombre de usuario de Monday en FILMMAKER_PROFILES (config.FILMMAKER_PROFILES).
    Si no hay operario o no hay coincidencia, devuelve None.
    """
    try:
        operario_nombre = item_procesado.get('operario')
        print(f"🔍 Debug: Operario del item: '{operario_nombre}'")
        
        if not operario_nombre:
            print("❌ Debug: No hay operario asignado")
            return None

        profiles = getattr(config, 'FILMMAKER_PROFILES', [])
        print(f"🔍 Debug: Buscando en {len(profiles)} perfiles disponibles")
        
        # Limpiar el nombre del operario (quitar espacios extra, etc.)
        operario_limpio = operario_nombre.strip() if operario_nombre else ""
        
        for profile in profiles:
            monday_name = profile.get('monday_name', '').strip()
            print(f"🔍 Debug: Comparando '{operario_limpio}' con '{monday_name}'")
            
            # Comparación exacta
            if monday_name == operario_limpio:
                calendar_id = profile.get('calendar_id')
                if calendar_id:
                    print(f"✅ Debug: Coincidencia encontrada! Calendar ID: {calendar_id}")
                    return calendar_id
                else:
                    print(f"⚠️  Debug: Perfil encontrado pero sin calendar_id")
        
        print("❌ Debug: No se encontró coincidencia en perfiles")
        return None
    except Exception as e:
        print(f"❌ Debug: Error en _get_personal_calendar_id_for_item: {e}")
        return None


def _get_personal_calendar_id_by_name(operario_name):
    """Obtiene el calendar_id personal por nombre de operario directo."""
    try:
        if not operario_name:
            return None
            
        profiles = getattr(config, 'FILMMAKER_PROFILES', [])
        operario_limpio = operario_name.strip()
        
        for profile in profiles:
            monday_name = profile.get('monday_name', '').strip()
            if monday_name == operario_limpio:
                return profile.get('calendar_id')
        
        return None
    except Exception:
        return None


def _handle_operario_change(google_service, monday_item_id, old_operario, new_operario):
    """Maneja el cambio de operario moviendo el evento personal del calendario anterior al nuevo."""
    try:
        print(f"👤 Detectado cambio de operario: '{old_operario}' → '{new_operario}'")
        
        # Obtener calendarios personal anterior y nuevo
        old_calendar_id = _get_personal_calendar_id_by_name(old_operario)
        new_calendar_id = _get_personal_calendar_id_by_name(new_operario)
        
        if not old_calendar_id:
            print(f"ℹ️  No hay calendario personal configurado para operario anterior: {old_operario}")
            return None
            
        if not new_calendar_id:
            print(f"ℹ️  No hay calendario personal configurado para nuevo operario: {new_operario}")
            return None
            
        if old_calendar_id == new_calendar_id:
            print(f"ℹ️  Mismo calendar_id para ambos operarios, no es necesario mover")
            return new_calendar_id
        
        # Buscar el evento en el calendario anterior
        print(f"🔍 Buscando evento personal en calendario anterior...")
        events_result = google_service.events().list(
            calendarId=old_calendar_id,
            maxResults=50,
            singleEvents=True
        ).execute()
        
        events = events_result.get('items', [])
        old_event_id = None
        event_to_move = None
        
        # Buscar el evento que tenga el mismo monday_item_id
        for event in events:
            extended_props = event.get('extendedProperties', {}).get('private', {})
            if extended_props.get('monday_item_id') == str(monday_item_id):
                old_event_id = event.get('id')
                event_to_move = event
                print(f"🔍 Encontrado evento personal en calendario anterior: {old_event_id}")
                break
        
        if not event_to_move:
            print(f"ℹ️  No se encontró evento personal en calendario anterior")
            return new_calendar_id
        
        # Eliminar del calendario anterior
        print(f"🗑️  Eliminando evento del calendario anterior...")
        google_service.events().delete(
            calendarId=old_calendar_id,
            eventId=old_event_id
        ).execute()
        print(f"✅ Evento eliminado del calendario anterior")
        
        return new_calendar_id
        
    except Exception as e:
        print(f"⚠️  Error manejando cambio de operario: {e}")
        return new_calendar_id if 'new_calendar_id' in locals() else None

def _adaptar_item_monday_a_evento_google(item_procesado, board_id=None):
    """
    Adapta un item de Monday.com al formato de evento de Google Calendar.
    """
    try:
        # Título del evento
        summary = item_procesado.get('name', 'Evento sin título')
        
        # Descripción completa con todos los datos relevantes
        operario = item_procesado.get('operario', 'No asignado')
        cliente = item_procesado.get('cliente', 'No especificado')
        ubicacion = item_procesado.get('ubicacion', 'No especificada')
        
        description = f"""📋 DETALLES DEL EVENTO
🎬 Proyecto: {summary}
👤 Operario: {operario}
🏢 Cliente: {cliente}
📍 Ubicación: {ubicacion}

🔗 ENLACES
📊 Ver en Monday.com: https://stupendastic.monday.com/boards/{board_id}
📅 Item ID: {item_procesado.get('id', 'N/A')}

⚙️ INFORMACIÓN DEL SISTEMA
🔄 Sincronizado automáticamente desde Monday.com
📊 Board ID: {board_id}"""
        
        # Procesar fecha
        fecha_inicio_str = item_procesado.get('fecha_inicio', '')
        
        if not fecha_inicio_str:
            # Fecha por defecto: mañana
            fecha_inicio = datetime.now() + timedelta(days=1)
            fecha_fin = fecha_inicio + timedelta(hours=2)
            
            start_time = {
                'dateTime': fecha_inicio.isoformat(),
                'timeZone': 'Europe/Madrid'
            }
            end_time = {
                'dateTime': fecha_fin.isoformat(),
                'timeZone': 'Europe/Madrid'
            }
        else:
            try:
                # Intentar parsear la fecha
                if 'T' in fecha_inicio_str:
                    # Fecha con hora
                    fecha_inicio = datetime.fromisoformat(fecha_inicio_str.replace('Z', ''))
                    fecha_fin = fecha_inicio + timedelta(hours=2)  # 2 horas por defecto
                    
                    start_time = {
                        'dateTime': fecha_inicio.isoformat(),
                        'timeZone': 'Europe/Madrid'
                    }
                    end_time = {
                        'dateTime': fecha_fin.isoformat(),
                        'timeZone': 'Europe/Madrid'
                    }
                else:
                    # Solo fecha (día completo)
                    fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
                    fecha_fin = fecha_inicio + timedelta(days=1)
                    
                    start_time = {
                        'date': fecha_inicio.strftime('%Y-%m-%d')
                    }
                    end_time = {
                        'date': fecha_fin.strftime('%Y-%m-%d')
                    }
                    
            except Exception as e:
                print(f"⚠️  Error parseando fecha '{fecha_inicio_str}': {e}")
                # Fecha por defecto
                fecha_inicio = datetime.now() + timedelta(days=1)
                fecha_fin = fecha_inicio + timedelta(hours=2)
                
                start_time = {
                    'dateTime': fecha_inicio.isoformat(),
                    'timeZone': 'Europe/Madrid'
                }
                end_time = {
                    'dateTime': fecha_fin.isoformat(),
                    'timeZone': 'Europe/Madrid'
                }
        
        # Construir el evento con protecciones de solo lectura
        event_body = {
            'summary': summary,
            'description': description,
            'start': start_time,
            'end': end_time,
            'extendedProperties': {
                'private': {
                    'monday_item_id': str(item_procesado.get('id', '')),
                    'board_id': str(board_id) if board_id else '',
                    'sync_version': str(int(time.time())),
                    'source': 'monday_sync_system',
                    'read_only': 'true'
                }
            },
            # Marcar como solo lectura para prevenir ediciones manuales
            'transparency': 'opaque',
            'visibility': 'default',
            # Agregar aviso en el título para desalentar ediciones
            'summary': f'📌 {summary}',
            'description': f'{description}\n\n🚨 IMPORTANTE: Este evento se sincroniza automáticamente desde Monday.com\n⚠️  NO EDITAR MANUALMENTE - Los cambios se perderán en la próxima sincronización\n✅ Para modificar: Editar en Monday.com → https://stupendastic.monday.com/boards/{board_id}'
        }
        
        return event_body
        
    except Exception as e:
        print(f"❌ Error adaptando item Monday a evento Google: {e}")
        return None


def sincronizar_item_via_webhook(item_id, monday_handler, google_service=None, change_uuid=None):
    """
    Sincroniza un item específico de Monday.com con Google Calendar.
    Versión limpia y simplificada para sistema unidireccional.
    
    Args:
        item_id (int): ID del item de Monday.com a sincronizar
        monday_handler: Instancia de MondayAPIHandler ya inicializada
        google_service: Instancia del servicio de Google Calendar
        change_uuid (str): UUID único del cambio (opcional)
        
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario
    """
    print(f"⚡ INICIANDO SINCRONIZACIÓN WEBHOOK - Item {item_id}")
    print("=" * 50)
    
    try:
        # 1. Verificar parámetros de entrada
        if not item_id:
            print("❌ Error: item_id no proporcionado")
            return False
            
        # 2. Verificar servicios
        if not google_service:
            print("❌ Error: google_service no disponible")
            return False
            
        if not monday_handler:
            print("❌ Error: monday_handler no disponible")
            return False
        
        # 2. Obtener datos del item
        print(f"📋 Obteniendo datos del item {item_id}...")
        
        try:
            item_data = monday_handler.get_item_by_id(
                board_id=str(config.BOARD_ID_GRABACIONES),
                item_id=str(item_id),
                column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name", config.COL_CLIENTE, "ubicaci_n"]
            )
            
            if not item_data:
                print(f"❌ No se pudo obtener datos del item {item_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error obteniendo item {item_id}: {e}")
            return False
        
        # 3. Procesar item
        item_procesado = parse_monday_item(item_data)
        if not item_procesado:
            print(f"❌ Error procesando item {item_id}")
            return False
        
        # 4. Verificar que tiene fecha
        if not item_procesado.get('fecha_inicio'):
            print(f"⚠️  Item {item_id} no tiene fecha asignada")
            return False
        
        # 4.1 Verificar que tiene nombre
        if not item_procesado.get('name'):
            print(f"⚠️  Item {item_id} no tiene nombre")
            return False
        
        # 4.2 Verificar que la fecha es válida (permitir fechas pasadas para testing)
        try:
            fecha_str = item_procesado.get('fecha_inicio', '')
            if fecha_str:
                if 'T' in fecha_str:
                    fecha = datetime.fromisoformat(fecha_str.replace('Z', ''))
                else:
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                
                # Solo validar que la fecha no sea muy antigua (más de 1 año)
                fecha_limite = datetime.now() - timedelta(days=365)
                if fecha < fecha_limite:
                    print(f"⚠️  Item {item_id} tiene fecha muy antigua: {fecha_str}")
                    return False
        except Exception as e:
            print(f"⚠️  Error validando fecha del item {item_id}: {e}")
            return False
        
        # 5. Generar hash para detección de cambios
        monday_content_hash = generate_content_hash(item_procesado)
        print(f"📊 Hash del contenido: {monday_content_hash[:16]}...")
        
        # 6. Sincronizar con Google
        google_event_id = item_procesado.get('google_event_id')
        
        # Adaptar datos de Monday a formato de Google
        event_body = _adaptar_item_monday_a_evento_google(item_procesado, config.BOARD_ID_GRABACIONES)
        
        if not event_body:
            print(f"❌ Error adaptando datos para Google")
            return False
        
        if google_event_id:
            # Actualizar evento existente
            print(f"🔄 Actualizando evento existente: {google_event_id}")
            
            success = update_google_event(
                google_service, 
                config.MASTER_CALENDAR_ID, 
                google_event_id, 
                event_body
            )
            
            if success:
                print(f"✅ Evento actualizado exitosamente")
                
                # También actualizar en calendario personal si existe
                personal_calendar_id = _get_personal_calendar_id_for_item(item_procesado)
                if personal_calendar_id:
                    try:
                        print(f"👤 Verificando evento personal para actualización...")
                        # Buscar el evento personal usando las extendedProperties (más confiable)
                        monday_item_id = str(item_procesado.get('id', ''))
                        
                        if monday_item_id:
                            try:
                                # Listar eventos del calendario personal
                                events_result = google_service.events().list(
                                    calendarId=personal_calendar_id,
                                    maxResults=50,
                                    singleEvents=True
                                ).execute()
                                
                                events = events_result.get('items', [])
                                personal_event_id = None
                                
                                # Buscar el evento que tenga el mismo monday_item_id en extendedProperties
                                for event in events:
                                    extended_props = event.get('extendedProperties', {}).get('private', {})
                                    if extended_props.get('monday_item_id') == monday_item_id:
                                        personal_event_id = event.get('id')
                                        print(f"🔍 Encontrado evento personal con ID: {personal_event_id}")
                                        break
                                
                                if personal_event_id:
                                    print(f"🔄 Actualizando evento personal: {personal_event_id}")
                                    update_success = update_google_event(
                                        google_service,
                                        personal_calendar_id,
                                        personal_event_id,
                                        event_body
                                    )
                                    if update_success:
                                        print(f"✅ Evento personal actualizado correctamente")
                                    else:
                                        print(f"⚠️  Error actualizando evento personal")
                                else:
                                    print(f"ℹ️  No se encontró evento personal con monday_item_id: {monday_item_id}")
                                    print(f"ℹ️  Esto puede ser normal si es la primera sincronización")
                            except Exception as search_error:
                                print(f"⚠️  Error buscando evento personal: {search_error}")
                        else:
                            print(f"⚠️  No se puede buscar evento personal sin monday_item_id")
                    except Exception as e:
                        print(f"⚠️  Error actualizando evento personal: {e}")
            else:
                print(f"❌ Error actualizando evento")
                return False
                
        else:
            # Crear nuevo evento
            print(f"🆕 Creando nuevo evento en Google Calendar")
            
            try:
                new_event_id = create_google_event(
                    google_service,
                    config.MASTER_CALENDAR_ID,
                    event_body
                )
            except Exception as e:
                print(f"❌ Error creando evento en calendario master: {e}")
                return False
            
            if new_event_id and new_event_id.strip():
                print(f"✅ Evento creado: {new_event_id}")
                google_event_id = new_event_id
                
                # Guardar el ID en Monday
                try:
                    update_success = monday_handler.update_column_value(
                        item_procesado['id'], 
                        config.BOARD_ID_GRABACIONES, 
                        config.COL_GOOGLE_EVENT_ID, 
                        new_event_id,
                        'text'
                    )
                except Exception as e:
                    print(f"❌ Error guardando ID en Monday: {e}")
                    update_success = False
                
                if update_success:
                    print(f"💾 ID guardado en Monday.com")
                else:
                    print(f"⚠️  Evento creado pero no se pudo guardar ID en Monday")
                    # Continuar de todas formas, el evento ya existe en Google

                # Intentar crear también en calendario personal (si hay operario configurado)
                print(f"🔍 Debug: Verificando calendario personal para operario...")
                personal_calendar_id = _get_personal_calendar_id_for_item(item_procesado)
                if personal_calendar_id:
                    try:
                        print(f"👤 Creando evento en calendario personal: {personal_calendar_id}")
                        personal_event_id = create_google_event(
                            google_service,
                            personal_calendar_id,
                            event_body
                        )
                        if personal_event_id:
                            print(f"✅ Evento creado en calendario personal: {personal_event_id}")
                        else:
                            print("⚠️  No se pudo crear el evento personal (sin ID)")
                    except Exception as e:
                        print(f"⚠️  Error creando evento personal: {e}")
                else:
                    print("ℹ️  No hay calendario personal configurado para este operario")
            else:
                print(f"❌ Error creando evento - no se recibió ID válido")
                return False
        
        # 7. Actualizar estado de sincronización
        if google_event_id:
            try:
                update_sync_state(
                    item_id=str(item_id),
                    event_id=google_event_id,
                    monday_content_hash=monday_content_hash,
                    sync_direction="monday_to_google",
                    monday_update_time=time.time()
                )
                print(f"📊 Estado de sincronización actualizado")
            except Exception as e:
                print(f"⚠️  Error actualizando estado de sincronización: {e}")
                # No fallar la sincronización por un error en el estado
        
        print(f"🎉 SINCRONIZACIÓN COMPLETADA para '{item_procesado['name']}'")
        return True
        
    except Exception as e:
        print(f"❌ Error inesperado en sincronización: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# UTILITY FUNCTIONS (Optional - for future use)
# =============================================================================

def _obtener_item_id_por_google_event_id(google_event_id, monday_handler):
    """
    Busca un item de Monday.com por su Google Event ID.
    """
    try:
        print(f"🔍 Buscando item con Google Event ID: {google_event_id}")
        
        query = f"""
        query {{
            items(limit: 50) {{
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
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            print(f"❌ Error buscando item: {response_data['errors']}")
            return None
        
        items = response_data.get('data', {}).get('items', [])
        
        for item in items:
            column_values = item.get('column_values', [])
            for col in column_values:
                if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                    if col.get('text') == google_event_id:
                        item_id = item.get('id')
                        print(f"✅ Item encontrado: {item_id}")
                        return item_id
        
        print(f"❌ No se encontró item con Google Event ID: {google_event_id}")
        return None
        
    except Exception as e:
        print(f"❌ Error buscando item por Google Event ID: {e}")
        return None


def _detectar_cambio_de_automatizacion(item_id, monday_handler):
    """
    Detecta si un cambio fue realizado por una automatización de Monday.
    
    Args:
        item_id: ID del item a verificar
        monday_handler: Handler de Monday API
        
    Returns:
        bool: True si fue un cambio de automatización
    """
    try:
        # Obtener actualizaciones recientes del item
        query = f"""
        query {{
            items(ids: [{item_id}]) {{
                updates(limit: 5) {{
                    id
                    body
                    creator {{
                        id
                        name
                        kind
                    }}
                    created_at
                }}
            }}
        }}
        """
        
        data = {'query': query}
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errors' in response_data:
            return False
        
        items = response_data.get('data', {}).get('items', [])
        if not items:
            return False
        
        updates = items[0].get('updates', [])
        
        # Verificar las últimas actualizaciones
        for update in updates[:3]:  # Solo las 3 más recientes
            creator = update.get('creator', {})
            creator_kind = creator.get('kind', '')
            
            # Si el creador es del tipo 'person' es un usuario real
            # Si es otro tipo puede ser automatización
            if creator_kind != 'person':
                print(f"🤖 Cambio de automatización detectado: {creator_kind}")
                return True
        
        return False
        
    except Exception as e:
        print(f"⚠️  Error detectando cambio de automatización: {e}")
        return False