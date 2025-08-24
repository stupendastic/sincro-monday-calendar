# --- CONFIGURACIÓN DE MONDAY.COM ---

# ID del tablero principal que vamos a sincronizar
BOARD_ID_GRABACIONES = 3324095194

# --- CONFIGURACIÓN DE CALENDARIOS MAESTROS ---

# ID del calendario maestro donde se centralizarán todos los eventos
MASTER_CALENDAR_ID = "c_54252371e4711a101b072dd3715ed3aadcf71ac45af65b988a5a7d272ffbe31d@group.calendar.google.com"

# ID del calendario para eventos sin asignar
# UNASSIGNED_CALENDAR_ID = "c_49d5be3fada7594d92ff64036b07afb75c4c83436844cb1f3c834bc9e31d4e2e@group.calendar.google.com"
# UNASSIGNED_CALENDAR_ID = "c_49d5be3fada7594d92ff64036b07afb75c4c83436844cb1f3c834bc9e31d4e2e@group.calendar.google.com"
UNASSIGNED_CALENDAR_ID = "c_49d5be3fada7594d92ff64036b07afb75c4c83436844cb1f3c834bc9e31d4e2e@group.calendar.google.com"

# IDs de las columnas que queremos leer del tablero
COLUMN_IDS = [
    "personas1",           # Operario
    "fecha56",             # Fecha Grab
    "color",               # Estado Permisos
    "bien_estado_volcado", # Evento Volcado
    "men__desplegable2",   # Acciones a Realizar
    "ubicaci_n",           # Ubicación
    "link_mktcbghq",       # Enlace Dron Dropbox
    "lookup_mkteg56h",     # Contacto Obra
    "lookup_mktetkek",     # Teléfono Obra
    "lookup_mkte8baj",     # Contacto Comercial
    "lookup_mkte7deh",     # Teléfono Comercial
    "text_mktfdhm3",       # ID Evento Google (Sincro)
    "text_mktefg5"         # Cliente
]

# Diccionario para mapear ID de columna a un nombre legible (opcional pero útil)
COLUMN_MAP = {
    "personas1": "Operario",
    "fecha56": "FechaGrab",
    "color": "EstadoPermisos",
    "bien_estado_volcado": "EventoVolcado",
    "men__desplegable2": "AccionesRealizar",
    "ubicaci_n": "Ubicacion",
    "link_mktcbghq": "LinkDropbox",
    "lookup_mkteg56h": "ContactoObra",
    "lookup_mktetkek": "TelefonoObra",
    "lookup_mkte8baj": "ContactoComercial",
    "lookup_mkte7deh": "TelefonoComercial",
    "text_mktfdhm3": "GoogleEventId",
    "text_mktefg5": "Cliente"
}

# Mapeo inverso para encontrar el ID a partir del nombre legible
COLUMN_MAP_REVERSE = {v: k for k, v in COLUMN_MAP.items()}

# ID de la columna para guardar el ID del evento de Google
COL_GOOGLE_EVENT_ID = "text_mktfdhm3"

# ID de la columna para el cliente
COL_CLIENTE = "text_mktefg5"

# ID de la columna para la fecha de grabación
COL_FECHA_GRAB = "fecha56"

# Alias para compatibilidad
COL_FECHA = COL_FECHA_GRAB

# --- CONFIGURACIÓN DE AUTOMATIZACIÓN ---

# Usuario que representa la automatización del sistema
# Cuando este usuario hace cambios, sabemos que es el sistema sincronizando (no un usuario real)
AUTOMATION_USER_NAME = "Arnau Admin"
AUTOMATION_USER_ID = 34210704  # ID de Monday.com para Arnau Admin

# Configuración de cooldowns para evitar bucles
SYNC_COOLDOWN_SECONDS = 3  # Tiempo mínimo entre sincronizaciones del mismo item (reducido para UUIDs)
AUTOMATION_DETECTION_WINDOW = 60  # Tiempo para detectar cambios de automatización (segundos)
CONFLICT_RESOLUTION_WINDOW = 30  # Ventana para resolver conflictos entre Monday y Google (segundos)

# --- CONFIGURACIÓN DE FILMMAKERS ---

# Lista de perfiles de filmmakers
# Cada perfil contiene la información necesaria para sincronizar con Google Calendar
FILMMAKER_PROFILES = [

    {
        "monday_name": "Arnau Admin",
        "personal_email": "seonrtn@gmail.com",
        "calendar_id": "c_e3eb24d0025d12e9f506b9b988563f744cc59f7869d7c79aaca7ab9043769d85@group.calendar.google.com",
        "monday_user_id": None
    },
    {
        "monday_name": "Xavi Alba",
        "personal_email": "retrobcn365@gmail.com",
        "calendar_id": "c_69308b9a3d04d3f03b5de726e8c1e39c55993896c4e5bf4fa43c15ea30304841@group.calendar.google.com",
        "monday_user_id": None
    },
    {
        "monday_name": "Oriol",
        "personal_email": "orioldevigoprat@gmail.com",
        "calendar_id": "c_3f590bced29ca0483a2ea4ef2596cb4cd6f05245ffeef5887b96c4921ac48412@group.calendar.google.com",
        "monday_user_id": None
    },
    {
        "monday_name": "Jordi Vas",
        "personal_email": "jordivas94@gmail.com",
        "calendar_id": "c_7bebe0169cb41ecba6662220c3699628a3bfa5f1c82b7a1d816ab495298a5c63@group.calendar.google.com",
        "monday_user_id": None
    },
    {
        "monday_name": "Rubén García",
        "personal_email": "rgarriscado@gmail.com",
        "calendar_id": "c_7b9e66757dacfbda0f0224b6fc04ca477ceac501ab42ae1834b2ccdbeb53528e@group.calendar.google.com",
        "monday_user_id": None
    },
    {
        "monday_name": "Tono Burguete",
        "personal_email": "infotonoburguete@gmail.com",
        "calendar_id": "c_e35f6a0f60db31f23bac8481e81ad877521ca86d6fae11bc0a9d52c9b25ee1cd@group.calendar.google.com",
        "monday_user_id": None
    },
    {
        "monday_name": "Josep",
        "personal_email": "films.pep@gmail.com",
        "calendar_id": "c_9b7f0685a7a9436ae17d102933065432c4597791b0f5ec796a0851f76b54b11f@group.calendar.google.com",
        "monday_user_id": None
    }
]

# Resumen: Esta configuración centraliza todos los perfiles de filmmakers en una estructura unificada.
# Para añadir nuevos filmmakers, simplemente agrega un nuevo diccionario a la lista FILMMAKER_PROFILES.
# Si el calendar_id es None, significa que el calendario aún no se ha creado para ese filmmaker.
# Si el monday_user_id es None, significa que el ID de usuario de Monday aún no se ha resuelto.