import os
import json
import time
import ssl
import socket
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest
import httplib2

# Configuración de la API de Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_http_with_retries():
    """
    Crea un objeto HTTP con configuración robusta para evitar errores SSL.
    """
    # Configurar timeouts más largos
    timeout = 60  # 60 segundos
    
    # Crear contexto SSL personalizado con configuración más permisiva
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Configurar opciones SSL adicionales
    ssl_context.options |= ssl.OP_NO_SSLv2
    ssl_context.options |= ssl.OP_NO_SSLv3
    ssl_context.options |= ssl.OP_NO_TLSv1
    ssl_context.options |= ssl.OP_NO_TLSv1_1
    
    # Configurar HTTP con reintentos y configuración SSL robusta
    http = httplib2.Http(
        timeout=timeout,
        disable_ssl_certificate_validation=True,
        ca_certs=None
    )
    
    return http

def get_calendar_service():
    """
    Obtiene el servicio de Google Calendar autenticado con manejo robusto de errores SSL.
    """
    creds = None
    
    # El archivo config/token.json almacena los tokens de acceso y actualización del usuario
    if os.path.exists('config/token.json'):
        creds = Credentials.from_authorized_user_file('config/token.json', SCOPES)
    
    # Si no hay credenciales válidas disponibles, deja que el usuario se autentique
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"❌ Error refrescando credenciales: {e}")
                return None
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"❌ Error en autenticación: {e}")
                return None
        
        # Guarda las credenciales para la próxima ejecución
        try:
            with open('config/token.json', 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"❌ Error guardando credenciales: {e}")
    
    try:
        # Crear servicio con configuración simplificada para unidirectional sync
        service = build(
            'calendar', 
            'v3', 
            credentials=creds, 
            cache_discovery=False
        )
        
        return service
    except Exception as e:
        print(f"❌ Error al crear el servicio de Google Calendar: {e}")
        return None

def create_google_event(service, calendar_id, event_body, extended_properties=None):
    """
    Crea un nuevo evento en un calendario de Google con manejo robusto de errores.
    
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario donde crear el evento
        event_body: Diccionario con el cuerpo del evento (summary, description, start, end, etc.)
        extended_properties: Propiedades extendidas opcionales para el evento
    """
    if not service:
        print("  ❌ Servicio de Google Calendar no disponible")
        return None
        
    # Crear una copia del event_body para no modificar el original
    event = event_body.copy()
    
    # Añadir propiedades extendidas si se proporcionan
    if extended_properties:
        event['extendedProperties'] = extended_properties

    # Reintentos para manejar errores SSL
    max_retries = 3
    for attempt in range(max_retries):
        try:
            event_name = event.get('summary', 'Sin título')
            print(f"  -> Creando evento en Google Calendar: '{event_name}' (intento {attempt + 1}/{max_retries})")
            
            # Configurar timeout más largo para evitar errores SSL
            request = service.events().insert(calendarId=calendar_id, body=event)
            created_event = request.execute()
            
            print(f"  ✅ ¡Evento creado! ID: {created_event.get('id')}")
            return created_event.get('id')
        except HttpError as error:
            print(f"  ❌ Error HTTP al crear evento: {error}")
            if attempt < max_retries - 1:
                print(f"  🔄 Reintentando en 2 segundos...")
                time.sleep(2)
                continue
            return None
        except Exception as e:
            print(f"  ❌ Error inesperado al crear evento: {e}")
            if attempt < max_retries - 1:
                print(f"  🔄 Reintentando en 2 segundos...")
                time.sleep(2)
                continue
            return None
    
    return None

def update_google_event(service, calendar_id, event_id, event_body):
    """
    Actualiza un evento existente en Google Calendar con manejo robusto de errores.
    
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario donde actualizar el evento
        event_id: ID del evento a actualizar
        event_body: Diccionario con el cuerpo del evento (summary, description, start, end, etc.)
    """
    if not service:
        print("  ❌ Servicio de Google Calendar no disponible")
        return None
        
    # Reintentos para manejar errores SSL
    max_retries = 3
    for attempt in range(max_retries):
        try:
            event_name = event_body.get('summary', 'Sin título')
            print(f"  -> Actualizando evento en Google Calendar: '{event_name}' (ID: {event_id}) (intento {attempt + 1}/{max_retries})")
            
            # Configurar timeout más largo para evitar errores SSL
            request = service.events().update(
                calendarId=calendar_id, 
                eventId=event_id, 
                body=event_body
            )
            updated_event = request.execute()
            
            print(f"  ✅ ¡Evento actualizado! ID: {updated_event.get('id')}")
            return updated_event.get('id')
        except HttpError as error:
            print(f"  ❌ Error HTTP al actualizar evento: {error}")
            if attempt < max_retries - 1:
                print(f"  🔄 Reintentando en 2 segundos...")
                time.sleep(2)
                continue
            return None
        except Exception as e:
            print(f"  ❌ Error inesperado al actualizar evento: {e}")
            if attempt < max_retries - 1:
                print(f"  🔄 Reintentando en 2 segundos...")
                time.sleep(2)
                continue
            return None
    
    return None

def update_google_event_by_id(service, calendar_id, event_id, event_body, extended_properties=None):
    """
    Actualiza un evento específico en Google Calendar por su ID.
    
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario donde actualizar el evento
        event_id: ID específico del evento a actualizar
        event_body: Diccionario con el cuerpo del evento (summary, description, start, end, etc.)
        extended_properties: Propiedades extendidas opcionales para el evento
    """
    # Crear una copia del event_body para no modificar el original
    event = event_body.copy()
    
    # Añadir propiedades extendidas si se proporcionan
    if extended_properties:
        event['extendedProperties'] = extended_properties

    try:
        event_name = event_body.get('summary', 'Sin título')
        print(f"  -> Actualizando evento en Google Calendar: '{event_name}' (ID: {event_id})")
        updated_event = service.events().update(
            calendarId=calendar_id, 
            eventId=event_id, 
            body=event
        ).execute()
        print(f"  ✅ ¡Evento actualizado! ID: {updated_event.get('id')}")
        return updated_event.get('id')
    except HttpError as error:
        print(f"  ❌ Error al actualizar evento en Google Calendar: {error}")
        return None

def find_event_copy_by_master_id(service, calendar_id, master_event_id):
    """
    Busca un evento copia en un calendario específico usando el ID del evento maestro.
    
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario donde buscar
        master_event_id: ID del evento maestro para buscar la copia
        
    Returns:
        dict: El evento copia encontrado, o None si no se encuentra
    """
    try:
        print(f"  -> Buscando evento copia para master_id: {master_event_id} en calendario {calendar_id}")
        
        # Buscar eventos con la propiedad extendida específica
        response = service.events().list(
            calendarId=calendar_id, 
            privateExtendedProperty=f"master_event_id={master_event_id}"
        ).execute()
        
        items = response.get('items', [])
        
        if items:
            found_event = items[0]
            print(f"  ✅ Evento copia encontrado: {found_event.get('summary', 'Sin título')} (ID: {found_event.get('id')})")
            return found_event
        else:
            print(f"  ℹ️  No se encontró evento copia para master_id: {master_event_id}")
            return None
            
    except HttpError as error:
        print(f"  ❌ Error al buscar evento copia: {error}")
        return None

def delete_event_by_id(service, calendar_id, event_id):
    """
    Elimina un evento específico de un calendario de Google.
    
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario donde eliminar el evento
        event_id: ID del evento a eliminar
        
    Returns:
        bool: True si el evento fue eliminado exitosamente, False si hubo error
    """
    try:
        print(f"  -> Eliminando evento {event_id} del calendario {calendar_id}")
        
        service.events().delete(
            calendarId=calendar_id, 
            eventId=event_id
        ).execute()
        
        print(f"  ✅ Evento {event_id} eliminado exitosamente")
        return True
        
    except HttpError as error:
        print(f"  ❌ Error al eliminar evento {event_id}: {error}")
        return False

def get_recently_updated_events(service, calendar_id, minutes_ago=5):
    """
    Obtiene los eventos que han sido actualizados recientemente en un calendario de Google.
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario donde buscar eventos
        minutes_ago: Minutos hacia atrás desde la hora actual para buscar eventos (por defecto 5)
    Returns:
        list: Lista de eventos encontrados, o lista vacía si hay errores
    """
    try:
        time_min = datetime.utcnow() - timedelta(minutes=minutes_ago)
        time_min_iso = time_min.isoformat() + 'Z'
        print(f"  -> Buscando eventos actualizados desde: {time_min_iso}")
        response = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min_iso,
            showDeleted=True,
            singleEvents=True
        ).execute()
        events = response.get('items', [])
        print(f"  ✅ Encontrados {len(events)} eventos actualizados recientemente")
        return events
    except HttpError as error:
        print(f"  ❌ Error al obtener eventos actualizados: {error}")
        return []

# get_incremental_sync_events REMOVED for unidirectional sync
# System now only supports Monday → Google synchronization

# compare_event_values REMOVED for unidirectional sync
# System now only supports Monday → Google synchronization

def create_and_share_calendar(service, filmmaker_name, filmmaker_email):
    """
    Crea un nuevo calendario de Google y lo comparte con el filmmaker especificado.
    
    Args:
        service: Objeto de servicio de Google Calendar
        filmmaker_name: Nombre del filmmaker para el título del calendario
        filmmaker_email: Email del filmmaker para compartir el calendario
    
    Returns:
        str: ID del calendario creado, o None si hubo error
    """
    try:
        # Definir el cuerpo del nuevo calendario
        calendar_body = {
            'summary': f"{filmmaker_name} STUPENDASTIC",
            'timeZone': 'Europe/Madrid'
        }
        
        # Crear el calendario
        print(f"  -> Creando calendario para {filmmaker_name}...")
        created_calendar = service.calendars().insert(body=calendar_body).execute()
        
        # Obtener el ID del calendario recién creado
        new_calendar_id = created_calendar.get('id')
        
        print(f"  ✅ Calendario creado para {filmmaker_name}.")
        
        # Definir la regla de compartición (ACL)
        rule = {
            'scope': {
                'type': 'user',
                'value': filmmaker_email
            },
            'role': 'writer'  # Permisos para añadir y modificar eventos
        }
        
        # Aplicar la regla de compartición
        print(f"  -> Compartiendo calendario con {filmmaker_email}...")
        service.acl().insert(calendarId=new_calendar_id, body=rule).execute()
        
        print(f"  ↪️  Compartido con {filmmaker_email}.")
        
        return new_calendar_id
        
    except HttpError as error:
        print(f"  ❌ Error al crear/compartir calendario para {filmmaker_name}: {error}")
        return None

def sync_event_to_multiple_calendars_optimized(service, master_event, target_calendars, master_calendar_id):
    """
    Sincronización INSTANTÁNEA y OPTIMIZADA de un evento a múltiples calendarios.
    Usa operaciones paralelas para máxima velocidad.
    
    Args:
        service: Servicio de Google Calendar
        master_event: Evento maestro desde el cual sincronizar
        target_calendars: Lista de calendar_ids donde sincronizar
        master_calendar_id: ID del calendario maestro
    
    Returns:
        dict: Resultados de sincronización {calendar_id: success}
    """
    import concurrent.futures
    import threading
    
    print(f"⚡ SINCRONIZACIÓN INSTANTÁNEA a {len(target_calendars)} calendarios")
    
    results = {}
    master_event_id = master_event.get('id')
    event_summary = master_event.get('summary', 'Sin título')
    
    def sync_to_single_calendar(calendar_id):
        """Sincronizar a un solo calendario - función interna para threading"""
        try:
            print(f"  🔄 Sincronizando '{event_summary}' → {calendar_id[:20]}...")
            
            # Buscar si ya existe una copia del evento
            existing_copy = find_event_copy_by_master_id(service, calendar_id, master_event_id)
            
            # Preparar el cuerpo del evento (sin el ID para evitar conflictos)
            event_body = {
                'summary': master_event.get('summary'),
                'description': master_event.get('description', ''),
                'start': master_event.get('start'),
                'end': master_event.get('end'),
                'location': master_event.get('location', ''),
                'extendedProperties': {
                    'private': {
                        'masterEventId': master_event_id,
                        'masterCalendarId': master_calendar_id,
                        'syncVersion': str(int(time.time()))  # Versión de sincronización
                    }
                }
            }
            
            if existing_copy:
                # Actualizar evento existente
                copy_id = existing_copy.get('id')
                updated_id = update_google_event_by_id(
                    service, calendar_id, copy_id, event_body
                )
                success = updated_id is not None
                print(f"    ✅ Actualizado en {calendar_id[:20]}" if success else f"    ❌ Error actualizando en {calendar_id[:20]}")
            else:
                # Crear nuevo evento
                created_id = create_google_event(
                    service, calendar_id, event_body
                )
                success = created_id is not None
                print(f"    ✅ Creado en {calendar_id[:20]}" if success else f"    ❌ Error creando en {calendar_id[:20]}")
            
            return calendar_id, success
            
        except Exception as e:
            print(f"    ❌ Error sincronizando a {calendar_id[:20]}: {e}")
            return calendar_id, False
    
    # Ejecutar sincronización en paralelo para máxima velocidad
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(target_calendars), 5)) as executor:
        # Enviar todos los trabajos
        future_to_calendar = {
            executor.submit(sync_to_single_calendar, calendar_id): calendar_id 
            for calendar_id in target_calendars
        }
        
        # Recoger resultados conforme se completan
        for future in concurrent.futures.as_completed(future_to_calendar):
            calendar_id, success = future.result()
            results[calendar_id] = success
    
    successful_syncs = sum(1 for success in results.values() if success)
    print(f"⚡ SINCRONIZACIÓN INSTANTÁNEA COMPLETADA: {successful_syncs}/{len(target_calendars)} exitosas")
    
    return results