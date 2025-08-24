# ============================================================================
# CONFIGURACIÓN DEL SISTEMA DE SINCRONIZACIÓN MONDAY ↔ GOOGLE CALENDAR
# ============================================================================
# 
# Este archivo contiene la configuración completa del sistema anti-bucles.
# Copia este archivo como config.py y ajusta los valores según tu entorno.
# 
# IMPORTANTE: Nunca subas config.py al control de versiones con credenciales reales.
# ============================================================================

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================================
# SISTEMA ANTI-BUCLES
# ============================================================================

# Archivo de estado de sincronización
SYNC_STATE_FILE = "config/sync_state.json"

# Configuración de limpieza de estados
SYNC_STATE_TTL_DAYS = 30  # Días para mantener estados antiguos
SYNC_STATE_CLEANUP_INTERVAL = 24  # Horas entre limpiezas automáticas

# Detección de bucles
LOOP_DETECTION_WINDOW = 30  # Segundos para detectar bucles
MAX_SYNCS_PER_ITEM = 2  # Máximo de sincronizaciones por item en la ventana
LOOP_DETECTION_THRESHOLD = 3  # Umbral para considerar bucle

# Campos para generación de hash de contenido
CONTENT_HASH_FIELDS = ['fecha_inicio', 'name', 'operario']

# Detección de automatización
AUTOMATION_DETECTION_WINDOW = 10  # Segundos para detectar cambios de automatización
AUTOMATION_USER_NAME = "Arnau Admin"
AUTOMATION_USER_ID = 34210704

# ============================================================================
# CONFIGURACIÓN DE MONDAY.COM
# ============================================================================

# API Key de Monday.com (obtener desde https://monday.com/developers/v2)
MONDAY_API_KEY = os.getenv("MONDAY_API_KEY", "tu_api_key_aqui")

# Board de grabaciones
BOARD_ID_GRABACIONES = 123456789  # Reemplazar con tu Board ID

# Columnas del board
COL_FECHA_GRAB = "fecha56"  # ID de la columna de fecha
COL_FECHA = COL_FECHA_GRAB
COL_GOOGLE_EVENT_ID = "text_mktfdhm3"  # ID de la columna Google Event ID
COL_OPERARIOS = "personas1"  # ID de la columna de operarios

# Configuración de webhooks de Monday
MONDAY_WEBHOOK_URL = "https://tu-servidor.com/monday-webhook"
MONDAY_WEBHOOK_EVENTS = ["update"]  # Eventos a escuchar

# ============================================================================
# CONFIGURACIÓN DE GOOGLE CALENDAR
# ============================================================================

# Credenciales de Google Calendar
GOOGLE_CREDENTIALS_FILE = "config/google_credentials.json"
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", GOOGLE_CREDENTIALS_FILE)

# Calendarios
MASTER_CALENDAR_ID = "primary"  # Calendario maestro
PERSONAL_CALENDARS = [
    # Lista de calendarios personales de los operarios
    # Ejemplo: {"name": "Juan Pérez", "calendar_id": "juan.perez@empresa.com"}
]

# Configuración de webhooks de Google
GOOGLE_WEBHOOK_URL = "https://tu-servidor.com/google-webhook"
GOOGLE_WEBHOOK_TTL = 604800  # 7 días en segundos

# Configuración de sync tokens
SYNC_TOKEN_FILE = "config/sync_tokens.json"
SYNC_TOKEN_TTL = 3600  # 1 hora en segundos

# ============================================================================
# CONFIGURACIÓN DEL SERVIDOR
# ============================================================================

# Configuración del servidor Flask
SERVER_PORT = 6754
SERVER_HOST = "0.0.0.0"
DEBUG_MODE = True

# Configuración de SSL (para producción)
SSL_CERT_FILE = None  # "config/cert.pem"
SSL_KEY_FILE = None   # "config/key.pem"

# ============================================================================
# CONFIGURACIÓN DE CACHÉ Y OPTIMIZACIÓN
# ============================================================================

# Cache en memoria
CACHE_TTL_SECONDS = 300  # 5 minutos
MAX_SCAN_ITEMS = 200  # Máximo items a escanear en búsquedas

# Configuración de búsquedas optimizadas
MONDAY_SEARCH_LIMIT = 50  # Límite de items por búsqueda
MONDAY_PAGE_SIZE = 25  # Items por página

# ============================================================================
# CONFIGURACIÓN DE WEBHOOKS
# ============================================================================

# Timeouts y reintentos
WEBHOOK_TIMEOUT = 30  # Segundos de timeout para webhooks
WEBHOOK_RETRY_ATTEMPTS = 3  # Intentos de reintento
WEBHOOK_RETRY_DELAY = 5  # Segundos entre reintentos

# Configuración de rate limiting
RATE_LIMIT_REQUESTS = 100  # Requests por minuto
RATE_LIMIT_WINDOW = 60  # Ventana en segundos

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

# Nivel de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Archivos de log
LOG_FILE = "logs/sync_system.log"
LOG_ERROR_FILE = "logs/sync_system_error.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Rotación de logs
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5  # Número de archivos de backup

# ============================================================================
# CONFIGURACIÓN DE MONITOREO
# ============================================================================

# Monitor en tiempo real
MONITOR_CHECK_INTERVAL = 5  # Segundos entre verificaciones del monitor
MONITOR_HISTORY_SIZE = 1000  # Número máximo de eventos en historial
MONITOR_ALERT_THRESHOLD = 10  # Número de eventos para alerta

# Configuración de alertas
ALERT_EMAIL_ENABLED = False
ALERT_EMAIL_SMTP_SERVER = "smtp.gmail.com"
ALERT_EMAIL_SMTP_PORT = 587
ALERT_EMAIL_USERNAME = os.getenv("ALERT_EMAIL_USERNAME", "")
ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD", "")
ALERT_EMAIL_RECIPIENTS = ["admin@empresa.com"]

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# ============================================================================

# Autenticación de webhooks
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "tu_webhook_secret_aqui")

# Configuración de CORS
CORS_ORIGINS = [
    "https://monday.com",
    "https://www.googleapis.com",
    "http://localhost:3000",  # Para desarrollo
]

# Configuración de rate limiting por IP
RATE_LIMIT_PER_IP = 100  # Requests por minuto por IP
RATE_LIMIT_BURST = 10  # Requests burst permitidos

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS (OPCIONAL)
# ============================================================================

# Si quieres usar una base de datos en lugar de archivos JSON
USE_DATABASE = False
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sync_system.db")

# Configuración de conexión a base de datos
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20
DATABASE_POOL_TIMEOUT = 30

# ============================================================================
# CONFIGURACIÓN DE BACKUP
# ============================================================================

# Backup automático de estados
BACKUP_ENABLED = True
BACKUP_INTERVAL_HOURS = 24  # Horas entre backups
BACKUP_RETENTION_DAYS = 7  # Días para mantener backups
BACKUP_DIR = "backups/"

# ============================================================================
# CONFIGURACIÓN DE MANTENIMIENTO
# ============================================================================

# Limpieza automática
AUTO_CLEANUP_ENABLED = True
AUTO_CLEANUP_INTERVAL_HOURS = 24  # Horas entre limpiezas
AUTO_CLEANUP_OLD_STATES_DAYS = 30  # Días para mantener estados

# Compresión de logs
LOG_COMPRESSION_ENABLED = True
LOG_COMPRESSION_DAYS = 7  # Comprimir logs más antiguos de X días

# ============================================================================
# CONFIGURACIÓN DE DESARROLLO
# ============================================================================

# Modo de desarrollo
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "True").lower() == "true"

# Configuración de debugging
DEBUG_DETAILED_LOGS = DEVELOPMENT_MODE
DEBUG_SHOW_SQL = DEVELOPMENT_MODE
DEBUG_SHOW_QUERIES = DEVELOPMENT_MODE

# Configuración de testing
TEST_MODE = False
TEST_ITEM_ID = "123456789"  # Item de prueba
TEST_EVENT_ID = "test_event_123"  # Evento de prueba

# ============================================================================
# CONFIGURACIÓN DE MÉTRICAS Y MONITOREO
# ============================================================================

# Métricas de rendimiento
METRICS_ENABLED = True
METRICS_PORT = 9090  # Puerto para métricas Prometheus

# Configuración de health checks
HEALTH_CHECK_INTERVAL = 30  # Segundos entre health checks
HEALTH_CHECK_TIMEOUT = 10  # Timeout para health checks

# Configuración de alertas de salud
HEALTH_ALERT_THRESHOLD = 3  # Fallos consecutivos para alerta
HEALTH_ALERT_COOLDOWN = 300  # Segundos de cooldown entre alertas

# ============================================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================================

def validate_config():
    """Valida que la configuración sea correcta."""
    errors = []
    
    # Validar API keys
    if not MONDAY_API_KEY or MONDAY_API_KEY == "tu_api_key_aqui":
        errors.append("MONDAY_API_KEY no está configurada")
    
    # Validar Board ID
    if not BOARD_ID_GRABACIONES or BOARD_ID_GRABACIONES == 123456789:
        errors.append("BOARD_ID_GRABACIONES no está configurado")
    
    # Validar columnas
    if not COL_FECHA or not COL_GOOGLE_EVENT_ID:
        errors.append("Columnas de Monday no están configuradas")
    
    # Validar credenciales de Google
    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        errors.append(f"Archivo de credenciales de Google no encontrado: {GOOGLE_CREDENTIALS_FILE}")
    
    # Validar directorios
    required_dirs = ["config", "logs", "backups"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
    
    if errors:
        print("❌ Errores de configuración encontrados:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ Configuración válida")
    return True

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def get_config_summary():
    """Retorna un resumen de la configuración actual."""
    return {
        "monday": {
            "api_key_configured": bool(MONDAY_API_KEY and MONDAY_API_KEY != "tu_api_key_aqui"),
            "board_id": BOARD_ID_GRABACIONES,
            "columns": {
                "fecha": COL_FECHA,
                "google_event_id": COL_GOOGLE_EVENT_ID,
                "operarios": COL_OPERARIOS
            }
        },
        "google": {
            "credentials_file": GOOGLE_CREDENTIALS_FILE,
            "master_calendar": MASTER_CALENDAR_ID,
            "personal_calendars": len(PERSONAL_CALENDARS)
        },
        "server": {
            "port": SERVER_PORT,
            "host": SERVER_HOST,
            "debug_mode": DEBUG_MODE
        },
        "anti_loop": {
            "detection_window": LOOP_DETECTION_WINDOW,
            "max_syncs_per_item": MAX_SYNCS_PER_ITEM,
            "automation_detection_window": AUTOMATION_DETECTION_WINDOW
        },
        "monitoring": {
            "check_interval": MONITOR_CHECK_INTERVAL,
            "history_size": MONITOR_HISTORY_SIZE,
            "metrics_enabled": METRICS_ENABLED
        }
    }

# ============================================================================
# EJECUCIÓN DE VALIDACIÓN
# ============================================================================

if __name__ == "__main__":
    print("🔧 Validando configuración del sistema de sincronización...")
    print()
    
    if validate_config():
        print("\n📊 Resumen de configuración:")
        summary = get_config_summary()
        
        for section, config in summary.items():
            print(f"\n{section.upper()}:")
            for key, value in config.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"    {sub_key}: {sub_value}")
                else:
                    print(f"  {key}: {value}")
        
        print("\n✅ Configuración lista para usar")
    else:
        print("\n❌ Corrige los errores antes de continuar")
        exit(1)
