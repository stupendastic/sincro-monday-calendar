import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Alcance de permisos: Acceso total a los calendarios.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def autorizar():
    """Función de un solo uso para generar token.json."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        print(f"El archivo '{TOKEN_FILE}' ya existe. No es necesario autorizar de nuevo.")
        return

    # Inicia el flujo de autorización si no hay un token válido.
    flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    # Guarda el token.json para el futuro.
    with open(TOKEN_FILE, "w") as token_file:
        token_file.write(creds.to_json())
    
    print(f"¡Éxito! Se ha creado el archivo '{TOKEN_FILE}'.")
    print("Este es tu pase permanente a la API. ¡No lo compartas!")

if __name__ == "__main__":
    autorizar()