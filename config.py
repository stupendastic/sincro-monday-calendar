# --- CONFIGURACIÓN DE MONDAY.COM ---

# ID del tablero principal que vamos a sincronizar
BOARD_ID_GRABACIONES = 3324095194

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

# --- CONFIGURACIÓN DE FILMMAKERS ---

# Lista de perfiles de filmmakers
# Cada perfil contiene la información necesaria para sincronizar con Google Calendar
FILMMAKER_PROFILES = [

    {
        "monday_name": "Arnau Admin",
        "personal_email": "seonrtn@gmail.com",
        "calendar_id": "c_59e3a26fba95603b4d085cc0c672573d52c1fd98d4b1e96b08b846c8be800c1a@group.calendar.google.com"
    },
    {
        "monday_name": "Xavi Alba",
        "personal_email": "retrobcn365@gmail.com",
        "calendar_id": "c_a80927ecf0d03dcd054477b44ac8d74abf9cf6245ff0bee2dfec72d9050b0683@group.calendar.google.com"
    },
    {
        "monday_name": "Oriol",
        "personal_email": "orioldevigoprat@gmail.com",
        "calendar_id": "c_cc448b4b77516c4f5a48be282ec844316fa4cb5fa3003cb5187ae72ebe74d83e@group.calendar.google.com"
    },
    {
        "monday_name": "Jordi Vas",
        "personal_email": "jordivas94@gmail.com",
        "calendar_id": "c_085d9236303489b51ccdf60a932e9477162c7ec66add17501b8f949343037e7e@group.calendar.google.com"
    },
    {
        "monday_name": "Rubén García",
        "personal_email": "rgarriscado@gmail.com",
        "calendar_id": "c_b0c49b5f37b32c3b18bf61538c2d5bc201effdb4848737ea18c4dae2c34163ab@group.calendar.google.com"
    },
    {
        "monday_name": "Tono Burguete",
        "personal_email": "infotonoburguete@gmail.com",
        "calendar_id": "c_0ae0b93dcc19c0ae1912d06563ef63e142dea6abddf23dd41d28cf7f65bf1120@group.calendar.google.com"
    },
    {
        "monday_name": "Josep",
        "personal_email": "films.pep@gmail.com",
        "calendar_id": "c_097379e79f8344e974c206a87608e26edf2a1132b344f0298bd8f524982a55a1@group.calendar.google.com"
    }
]

# Resumen: Esta configuración centraliza todos los perfiles de filmmakers en una estructura unificada.
# Para añadir nuevos filmmakers, simplemente agrega un nuevo diccionario a la lista FILMMAKER_PROFILES.
# Si el calendar_id es None, significa que el calendario aún no se ha creado para ese filmmaker.