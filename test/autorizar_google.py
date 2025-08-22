import os
import json
from dotenv import load_dotenv, set_key
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Cargar variables de entorno
load_dotenv()

# Alcance de permisos: Acceso total a los calendarios.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS_FILE = "credentials.json"

def autorizar():
    """Función de un solo uso para generar credenciales de Google Calendar."""
    creds = None

    # Inicia el flujo de autorización
    print("🔄 Iniciando autorización de Google Calendar...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    # Obtener el token en formato JSON
    token_json = creds.to_json()
    
    print("\n" + "=" * 80)
    print("🎉 ¡AUTORIZACIÓN COMPLETADA EXITOSAMENTE!")
    print("=" * 80)
    print()
    print("📋 COPIA Y PEGA ESTA LÍNEA COMPLETA EN TU ARCHIVO .env:")
    print()
    print(f"GOOGLE_TOKEN_JSON='{token_json}'")
    print()
    print("=" * 80)
    print("💡 Instrucciones:")
    print("   1. Abre tu archivo .env en un editor de texto")
    print("   2. Añade la línea de arriba al final del archivo")
    print("   3. Guarda el archivo")
    print("   4. ¡Listo! Tu aplicación ya puede usar Google Calendar")
    print()
    print("🔒 IMPORTANTE: No compartas estas credenciales con nadie")
    print("🔄 El token se actualizará automáticamente cuando expire")
    print("=" * 80)

if __name__ == "__main__":
    autorizar()