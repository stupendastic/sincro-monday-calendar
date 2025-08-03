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
    "text_mktfdhm3"        # ID Evento Google (Sincro)
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
    "text_mktfdhm3": "GoogleEventId"
}

# Mapeo inverso para encontrar el ID a partir del nombre legible
COLUMN_MAP_REVERSE = {v: k for k, v in COLUMN_MAP.items()}

# ID de la columna para guardar el ID del evento de Google
COL_GOOGLE_EVENT_ID = "text_mktfdhm3"


# Perfiles de Filmmakers - Configuración unificada
FILMMAKER_PROFILES = [
    {
        "monday_name": "Arnau Admin",           # Nombre visible en Monday.com
        "monday_email": "admin@stupendastic.com",  # Email en Monday.com
        "personal_email": "seonrtn@gmail.com",  # Email personal para notificaciones
        "calendar_id": "c_e6ca98cff5247dc9f08abfb6019aabc062bed12883a5cb80470e89261cad5d9c@group.calendar.google.com"  # ID del calendario de Google
    }
    
    # Añade más perfiles aquí siguiendo el mismo formato...
]