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
    # Lógica del Link de Dropbox
    dropbox_link = item_data.get('linkdropbox', '')
    if dropbox_link:
        dropbox_link_html = f'<a href="{dropbox_link}">Abrir Enlace</a>'
    else:
        dropbox_link_html = '<i>Sin link a Dropbox Dron</i>'
    
    # Construimos la descripción del evento usando HTML para que se vea bien
    description = f"""<b>Cliente:</b> {item_data.get('cliente', 'N/A')}
<b>Grupo:</b> {item_data.get('group_title', 'N/A')}
<b>📋 Estado Permisos:</b> {item_data.get('estadopermisos', 'N/A')}
<b>🛠️ Acciones a Realizar:</b> {item_data.get('accionesrealizar', 'N/A')}

<b>--- 📞 Contactos de Obra ---</b>
{item_data.get('contacto_obra_formateado', 'No disponible')}

<b>--- 👤 Contactos Comerciales ---</b>
{item_data.get('contacto_comercial_formateado', 'No disponible')}

<b>--- 🔗 Enlaces y Novedades ---</b>
<b>Link Dropbox Dron:</b> {dropbox_link_html}
<b>Updates en el elemento en Monday:</b>
{item_data.get('all_updates_html', '<i>Sin updates.</i>')}
    """

    # Determinar si es evento de día completo o con hora específica
    fecha_inicio = item_data['fecha_inicio']
    fecha_fin = item_data['fecha_fin']
    
    if 'T' in fecha_inicio:
        # Evento con hora específica
        event = {
            'summary': item_data['name'],
            'location': item_data.get('ubicacion', ''),
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
            'summary': item_data['name'],
            'location': item_data.get('ubicacion', ''),
            'description': description,
            'guestsCanModify': False,
            'start': {
                'date': fecha_inicio,
            },
            'end': {
                'date': fecha_fin,
            },
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
    # Lógica del Link de Dropbox
    dropbox_link = item_data.get('linkdropbox', '')
    if dropbox_link:
        dropbox_link_html = f'<a href="{dropbox_link}">Abrir Enlace</a>'
    else:
        dropbox_link_html = '<i>Sin link a Dropbox Dron</i>'
    
    # Construimos la descripción del evento usando HTML para que se vea bien
    description = f"""<b>Cliente:</b> {item_data.get('cliente', 'N/A')}
<b>Grupo:</b> {item_data.get('group_title', 'N/A')}
<b>📋 Estado Permisos:</b> {item_data.get('estadopermisos', 'N/A')}
<b>🛠️ Acciones a Realizar:</b> {item_data.get('accionesrealizar', 'N/A')}

<b>--- 📞 Contactos de Obra ---</b>
{item_data.get('contacto_obra_formateado', 'No disponible')}

<b>--- 👤 Contactos Comerciales ---</b>
{item_data.get('contacto_comercial_formateado', 'No disponible')}

<b>--- 🔗 Enlaces y Novedades ---</b>
<b>Link Dropbox Dron:</b> {dropbox_link_html}
<b>Updates en el elemento en Monday:</b>
{item_data.get('all_updates_html', '<i>Sin updates.</i>')}
    """

    # Determinar si es evento de día completo o con hora específica
    fecha_inicio = item_data['fecha_inicio']
    fecha_fin = item_data['fecha_fin']
    
    if 'T' in fecha_inicio:
        # Evento con hora específica
        event = {
            'summary': item_data['name'],
            'location': item_data.get('ubicacion', ''),
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
            'summary': item_data['name'],
            'location': item_data.get('ubicacion', ''),
            'description': description,
            'guestsCanModify': False,
            'start': {
                'date': fecha_inicio,
            },
            'end': {
                'date': fecha_fin,
            },
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