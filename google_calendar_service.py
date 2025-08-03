import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Alcance de permisos: Acceso total a los calendarios.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_calendar_service():
    """
    Crea y devuelve un objeto de servicio para interactuar con la API de Google Calendar.
    Reutiliza el token.json si existe, o pide autorización si es necesario.
    """
    creds = None
    # El archivo token.json guarda tus credenciales de acceso y se crea
    # automáticamente la primera vez que autorizas la aplicación.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Si no hay credenciales válidas disponibles, permite al usuario iniciar sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error al refrescar el token: {e}")
                print("Por favor, borra el archivo 'token.json' y vuelve a ejecutar para autorizar de nuevo.")
                return None
        else:
            # Esto nunca debería pasar en nuestro servidor principal, ya que 
            # deberíamos haber generado el token.json antes. Es una medida de seguridad.
            print("No se encontró 'token.json' o no es válido.")
            print("Ejecuta 'autorizar_google.py' primero.")
            return None
            
        # Guarda las credenciales actualizadas para la próxima vez
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    try:
        # Construye el objeto de servicio que nos permitirá hacer llamadas a la API
        service = build("calendar", "v3", credentials=creds)
        print("✅ Servicio de Google Calendar inicializado correctamente.")
        return service
    except HttpError as error:
        print(f"Ocurrió un error al construir el servicio de Google: {error}")
        return None

def create_google_event(service, calendar_id, item_data):
    """
    Crea un nuevo evento en un calendario de Google a partir de datos procesados de Monday.
    """
    # Construimos la descripción del evento usando HTML para que se vea bien
    description = f"""
<b>Estado Permisos:</b> {item_data.get('estadopermisos', 'N/A')}
<b>Acciones a Realizar:</b> {item_data.get('accionesrealizar', 'N/A')}
<br>
<b>--- Contactos ---</b>
<b>Obra:</b> {item_data.get('contactoobra', 'N/A')} ({item_data.get('telefonoobra', 'N/A')})
<b>Comercial:</b> {item_data.get('contactocomercial', 'N/A')} ({item_data.get('telefonocomercial', 'N/A')})
<br>
<b>--- Enlaces y Novedades ---</b>
<b>Dropbox:</b> {item_data.get('linkdropbox', 'N/A')}
<b>Última Novedad en Monday:</b>
<i>{item_data.get('update_body', 'Sin novedades.')}</i>
    """

    # Construimos el cuerpo del evento para la API de Google
    event = {
        'summary': item_data['name'],
        'location': item_data.get('ubicacion', ''),
        'description': description,
        'start': {
            'dateTime': item_data['fecha_inicio'],
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': item_data['fecha_fin'],
            'timeZone': 'Europe/Madrid',
        },
        # Aquí añadiremos más cosas en el futuro, como recordatorios.
    }

    try:
        print(f"  -> Creando evento en Google Calendar: '{item_data['name']}'")
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"  ✅ ¡Evento creado! ID: {created_event.get('id')}")
        return created_event.get('id')
    except HttpError as error:
        print(f"  ❌ Error al crear evento en Google Calendar: {error}")
        return None

def update_google_event(service, calendar_id, item_data):
    """
    Actualiza un evento existente en Google Calendar a partir de datos procesados de Monday.
    """
    # Construimos la descripción del evento usando HTML para que se vea bien
    description = f"""
<b>Estado Permisos:</b> {item_data.get('estadopermisos', 'N/A')}
<b>Acciones a Realizar:</b> {item_data.get('accionesrealizar', 'N/A')}
<br>
<b>--- Contactos ---</b>
<b>Obra:</b> {item_data.get('contactoobra', 'N/A')} ({item_data.get('telefonoobra', 'N/A')})
<b>Comercial:</b> {item_data.get('contactocomercial', 'N/A')} ({item_data.get('telefonocomercial', 'N/A')})
<br>
<b>--- Enlaces y Novedades ---</b>
<b>Dropbox:</b> {item_data.get('linkdropbox', 'N/A')}
<b>Última Novedad en Monday:</b>
<i>{item_data.get('update_body', 'Sin novedades.')}</i>
    """

    # Construimos el cuerpo del evento para la API de Google
    event = {
        'summary': item_data['name'],
        'location': item_data.get('ubicacion', ''),
        'description': description,
        'start': {
            'dateTime': item_data['fecha_inicio'],
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': item_data['fecha_fin'],
            'timeZone': 'Europe/Madrid',
        },
        # Aquí añadiremos más cosas en el futuro, como recordatorios.
    }

    try:
        event_id = item_data['google_event_id']
        print(f"  -> Actualizando evento en Google Calendar: '{item_data['name']}' (ID: {event_id})")
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