import os
import json
from dotenv import load_dotenv, set_key
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Cargar variables de entorno
load_dotenv()

# Alcance de permisos: Acceso total a los calendarios.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS_FILE = "credentials.json"

def get_calendar_service():
    """
    Crea y devuelve un objeto de servicio para interactuar con la API de Google Calendar.
    Reutiliza las credenciales desde la variable de entorno GOOGLE_TOKEN_JSON.
    """
    creds = None
    
    # Buscar las credenciales en la variable de entorno GOOGLE_TOKEN_JSON
    token_json = os.getenv('GOOGLE_TOKEN_JSON')
    
    if token_json:
        try:
            # Cargar credenciales desde la variable de entorno
            creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        except Exception as e:
            print(f"Error al cargar credenciales desde GOOGLE_TOKEN_JSON: {e}")
            print("Por favor, ejecuta autorizar_google.py para regenerar las credenciales.")
            return None
    else:
        # Si no existe la variable de entorno, mostrar error claro
        print("❌ GOOGLE_TOKEN_JSON no encontrado. Por favor, ejecuta autorizar_google.py primero.")
        return None
    
    # Si no hay credenciales válidas disponibles, intentar refrescar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Guardar las credenciales actualizadas en la variable de entorno
                set_key('.env', 'GOOGLE_TOKEN_JSON', creds.to_json())
                print("✅ Token refrescado y guardado en .env")
            except Exception as e:
                print(f"Error al refrescar el token: {e}")
                print("Por favor, ejecuta autorizar_google.py para regenerar las credenciales.")
                return None
        else:
            print("❌ Credenciales no válidas. Por favor, ejecuta autorizar_google.py primero.")
            return None

    try:
        # Construye el objeto de servicio que nos permitirá hacer llamadas a la API
        service = build("calendar", "v3", credentials=creds)
        print("✅ Servicio de Google Calendar inicializado correctamente.")
        return service
    except HttpError as error:
        print(f"Ocurrió un error al construir el servicio de Google: {error}")
        return None

def create_google_event(service, calendar_id, event_body, extended_properties=None):
    """
    Crea un nuevo evento en un calendario de Google.
    
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario donde crear el evento
        event_body: Diccionario con el cuerpo del evento (summary, description, start, end, etc.)
        extended_properties: Propiedades extendidas opcionales para el evento
    """
    # Crear una copia del event_body para no modificar el original
    event = event_body.copy()
    
    # Añadir propiedades extendidas si se proporcionan
    if extended_properties:
        event['extendedProperties'] = extended_properties

    try:
        event_name = event.get('summary', 'Sin título')
        print(f"  -> Creando evento en Google Calendar: '{event_name}'")
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"  ✅ ¡Evento creado! ID: {created_event.get('id')}")
        return created_event.get('id')
    except HttpError as error:
        print(f"  ❌ Error al crear evento en Google Calendar: {error}")
        return None

def update_google_event(service, calendar_id, event_id, event_body):
    """
    Actualiza un evento existente en Google Calendar.
    
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario donde actualizar el evento
        event_id: ID del evento a actualizar
        event_body: Diccionario con el cuerpo del evento (summary, description, start, end, etc.)
    """
    try:
        event_name = event_body.get('summary', 'Sin título')
        print(f"  -> Actualizando evento en Google Calendar: '{event_name}' (ID: {event_id})")
        updated_event = service.events().update(
            calendarId=calendar_id, 
            eventId=event_id, 
            body=event_body
        ).execute()
        print(f"  ✅ ¡Evento actualizado! ID: {updated_event.get('id')}")
        return updated_event.get('id')
    except HttpError as error:
        print(f"  ❌ Error al actualizar evento en Google Calendar: {error}")
        return None

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


def register_google_push_notification(service, calendar_id, webhook_url_base):
    """
    Registra un canal de notificación push con Google Calendar para un calendario específico.
    
    Args:
        service: Objeto de servicio de Google Calendar
        calendar_id: ID del calendario a monitorizar
        webhook_url_base: URL base del webhook (ej: https://abc123.ngrok.io)
        
    Returns:
        tuple: (bool, str) - (éxito, channel_id si exitoso)
    """
    import uuid
    
    try:
        # Generar IDs únicos para el canal
        channel_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        # Construir la URL completa del webhook
        webhook_url = f"{webhook_url_base}/google-webhook"
        
        # Definir el cuerpo del canal de notificación
        channel_body = {
            'id': channel_id,
            'type': 'web_hook',
            'address': webhook_url,
            'params': {
                'ttl': '86400'  # Tiempo de vida en segundos (1 día)
            }
        }
        
        print(f"  -> Registrando canal de notificaciones para calendario {calendar_id}...")
        print(f"     URL del webhook: {webhook_url}")
        print(f"     ID del canal: {channel_id}")
        
        # Llamar a la API de Google Calendar para registrar el canal
        response = service.events().watch(
            calendarId=calendar_id, 
            body=channel_body
        ).execute()
        
        print(f"  ✅ Canal de notificaciones Google registrado para calendario {calendar_id}.")
        print(f"     Resource ID: {response.get('resourceId', 'N/A')}")
        print(f"     Expiración: {response.get('expiration', 'N/A')}")
        
        return True, channel_id
        
    except HttpError as error:
        print(f"  ❌ Error al registrar canal de notificaciones para calendario {calendar_id}: {error}")
        return False, None

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