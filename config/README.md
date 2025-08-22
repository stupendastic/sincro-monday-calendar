# Configuración del Sistema

Esta carpeta contiene todos los archivos de configuración del sistema de sincronización.

## Estructura

```
config/
├── README.md                           # Este archivo
├── sync_tokens.json                    # Tokens de sincronización de Google Calendar
├── token.json                          # Token de autenticación de Google
├── channels/                           # Configuración de canales de webhooks
│   ├── google_channel_map.json         # Mapeo channel_id -> calendar_id
│   ├── google_channel_info_master.json # Info del canal del calendario maestro
│   ├── google_channel_info_arnau_admin.json # Info del canal de Arnau Admin
│   └── ...                             # Otros canales de filmmakers
└── webhooks/                           # Configuración de webhooks
    └── webhooks_personales_info.json   # Información de webhooks personales
```

## Archivos Principales

### `sync_tokens.json`
Contiene los tokens de sincronización incremental para cada calendario de Google Calendar. Permite sincronizar solo los cambios recientes.

### `token.json`
Token de autenticación de Google Calendar API. Se genera automáticamente durante la autorización.

### `channels/google_channel_map.json`
Mapeo entre los IDs de canal de Google Calendar y los IDs de calendario correspondientes. Esencial para identificar de qué calendario proviene cada notificación push.

### `channels/google_channel_info_*.json`
Información detallada de cada canal de webhook configurado, incluyendo:
- Channel ID
- Resource ID
- Fecha de expiración
- URL del webhook
- ID del calendario

### `webhooks/webhooks_personales_info.json`
Información de los webhooks configurados para los calendarios personales de los filmmakers.

## Mantenimiento

- Los archivos se generan automáticamente durante la configuración
- No editar manualmente a menos que sea necesario
- Hacer backup antes de cambios importantes
- Los archivos se actualizan automáticamente cuando se configuran nuevos webhooks
