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