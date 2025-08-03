import os
import requests
from dotenv import load_dotenv

# Importamos nuestra nueva función desde el otro archivo
from google_calendar_service import get_calendar_service

# Carga las variables del archivo .env (tu clave de API de Monday)
load_dotenv()

# --- Configuración de Monday ---
MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_API_URL = "https://api.monday.com/v2"
HEADERS = {"Authorization": MONDAY_API_KEY}
# --- Fin de la Configuración ---


def main():
    """Función principal de la aplicación."""
    print("Iniciando Sincronizador Stupendastic...")
    
    # 1. Inicializar el servicio de Google Calendar
    google_service = get_calendar_service()
    if not google_service:
        print("Error: No se pudo inicializar el servicio de Google Calendar. Abortando.")
        return # Detiene la ejecución si no podemos conectar con Google

    # 2. Probar la conexión a Monday (temporalmente)
    # Por ahora, solo imprimimos un mensaje para confirmar que la clave está cargada.
    if MONDAY_API_KEY:
        print("✅ Clave de API de Monday cargada correctamente.")
    else:
        print("Error: No se encontró la clave de API de Monday en el archivo .env. Abortando.")
        return

    print("\n¡Listo para sincronizar! (próximos pasos aquí)")


if __name__ == "__main__":
    main()