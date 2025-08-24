# Refactorización de Webhooks con Nuevo Sistema Anti-Bucles

## Descripción

Se ha refactorizado completamente `app.py` para usar el nuevo sistema anti-bucles basado en `sync_state_manager` y detección de automatización mejorada. Esta refactorización elimina el sistema obsoleto de UUIDs y cooldowns, reemplazándolo con un sistema más robusto y eficiente.

## Cambios Implementados

### ✅ **1. Eliminación de Sistema Obsoleto**

**Antes** (sistema obsoleto):
```python
# Variables globales obsoletas
SYNC_COOLDOWN = config.SYNC_COOLDOWN_SECONDS
AUTOMATION_DETECTION_WINDOW = config.AUTOMATION_DETECTION_WINDOW
CONFLICT_RESOLUTION_WINDOW = config.CONFLICT_RESOLUTION_WINDOW
last_sync_times = {}  # Cache de últimos tiempos
sync_origin = {}  # Origen de la última sincronización

# Lógica obsoleta en webhooks
if item_id in last_sync_times:
    time_since_last = current_time - last_sync_times[item_id]
    if time_since_last < SYNC_COOLDOWN:
        return jsonify({'message': 'Sincronización en cooldown'}), 200

last_sync_times[item_id] = current_time
```

**Después** (nuevo sistema):
```python
# Configuración del nuevo sistema anti-bucles
print("🚀 Inicializando sistema anti-bucles con sync_state_manager y detección de automatización")

# Lógica nueva en webhooks
sync_state = get_sync_state(str(item_id), google_event_id)
current_hash = generate_content_hash(current_content)

if sync_state and sync_state.get('monday_content_hash') == current_hash:
    print("🔄 Eco detectado - contenido idéntico, ignorando")
    return jsonify({'status': 'echo_ignored'}), 200
```

### ✅ **2. Nuevas Importaciones**

```python
from sync_logic import (
    sincronizar_item_via_webhook, 
    _obtener_item_id_por_google_event_id, 
    update_monday_date_column_v2,
    _detectar_cambio_de_automatizacion,
    generate_content_hash
)
from sync_state_manager import get_sync_state, update_sync_state
```

### ✅ **3. Refactorización de `handle_monday_webhook()`**

**Nuevo flujo completo**:

```python
@app.route('/monday-webhook', methods=['POST'])
def handle_monday_webhook():
    """
    Webhook de Monday.com - Sincronización inteligente Monday → Google.
    Usa el nuevo sistema anti-bucles con sync_state_manager y detección de automatización.
    """
    
    # 1. OBTENER DATOS DEL ITEM DE MONDAY
    item_completo = monday_handler_global.get_items(
        board_id=str(config.BOARD_ID_GRABACIONES),
        column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name"],
        limit_per_page=1
    )
    
    # Filtrar por item_id específico
    item_data = None
    for item in item_completo:
        if str(item.get('id')) == str(item_id):
            item_data = item
            break
    
    # Procesar item de Monday
    item_procesado = parse_monday_item(item_data)
    google_event_id = item_procesado.get('google_event_id')
    
    # 2. OBTENER ESTADO DE SINCRONIZACIÓN
    sync_state = get_sync_state(str(item_id), google_event_id)
    
    # 3. GENERAR HASH DEL CONTENIDO ACTUAL
    current_content = {
        'fecha': item_procesado.get('fecha_inicio', ''),
        'titulo': item_procesado.get('name', ''),
        'operarios': item_procesado.get('operario', '')
    }
    current_hash = generate_content_hash(current_content)
    
    # 4. VERIFICAR SI ES UN ECO
    if sync_state and sync_state.get('monday_content_hash') == current_hash:
        print("🔄 Eco detectado - contenido idéntico, ignorando")
        return jsonify({'status': 'echo_ignored', 'message': 'Eco detectado'}), 200
    
    # 5. VERIFICAR SI FUE CAMBIO DE AUTOMATIZACIÓN
    if _detectar_cambio_de_automatizacion(str(item_id), monday_handler_global):
        print("🤖 Cambio de automatización detectado, ignorando")
        return jsonify({'status': 'automation_ignored', 'message': 'Cambio de automatización detectado'}), 200
    
    # 6. PROCEDER CON SINCRONIZACIÓN
    success = sincronizar_item_via_webhook(
        item_id, 
        monday_handler=monday_handler_global,
        google_service=google_service_global,
        change_uuid=str(uuid.uuid4())
    )
    
    # 7. ACTUALIZAR ESTADO SI FUE EXITOSO
    if success:
        # Obtener hash del contenido final de Google
        event = google_service_global.events().get(
            calendarId=config.MASTER_CALENDAR_ID,
            eventId=google_event_id
        ).execute()
        
        google_content = {
            'fecha': event.get('start', {}).get('dateTime', ''),
            'titulo': event.get('summary', ''),
            'descripcion': event.get('description', '')
        }
        google_hash = generate_content_hash(google_content)
        
        # Actualizar estado de sincronización
        update_sync_state(
            item_id=str(item_id),
            event_id=google_event_id,
            monday_content_hash=current_hash,
            google_content_hash=google_hash,
            sync_direction="monday_to_google",
            monday_update_time=time.time()
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Sincronización completada',
            'item_id': item_id,
            'google_event_id': google_event_id
        }), 200
```

### ✅ **4. Refactorización de `handle_google_webhook()`**

**Nuevo flujo completo**:

```python
@app.route('/google-webhook', methods=['POST'])
def handle_google_webhook():
    """
    Webhook de Google Calendar - Sincronización inteligente Google → Monday.
    Usa el nuevo sistema anti-bucles con sync_state_manager y sync tokens.
    """
    
    # Procesar cada evento cambiado con nuevo sistema anti-bucles
    for evento_cambiado in eventos_cambiados:
        event_id = evento_cambiado.get('id')
        event_summary = evento_cambiado.get('summary', 'Sin título')
        
        # 7. OBTENER ESTADO DE SINCRONIZACIÓN
        # Buscar item_id correspondiente en Monday
        item_id = _obtener_item_id_por_google_event_id(event_id, monday_handler_global)
        
        if not item_id:
            print(f"  ⚠️  Evento {event_id} no tiene item correspondiente en Monday")
            continue
        
        sync_state = get_sync_state(str(item_id), event_id)
        
        # 8. GENERAR HASH DEL CONTENIDO ACTUAL DE GOOGLE
        google_content = {
            'fecha': evento_cambiado.get('start', {}).get('dateTime', ''),
            'titulo': evento_cambiado.get('summary', ''),
            'descripcion': evento_cambiado.get('description', '')
        }
        google_hash = generate_content_hash(google_content)
        
        # 9. VERIFICAR SI ES UN ECO
        if sync_state and sync_state.get('google_content_hash') == google_hash:
            print(f"  🔄 Eco detectado - contenido idéntico, ignorando evento {event_id}")
            continue
        
        # 10. PROCEDER CON SINCRONIZACIÓN SEGÚN TIPO DE CALENDARIO
        if is_master_calendar:
            success = sincronizar_desde_google_calendar(
                evento_cambiado=evento_cambiado,
                google_service=google_service_global,
                monday_handler=monday_handler_global,
                change_uuid=str(uuid.uuid4())
            )
            
            if success:
                # Obtener hash del contenido final de Monday
                item_data = monday_handler_global.get_items(
                    board_id=str(config.BOARD_ID_GRABACIONES),
                    column_ids=[config.COL_FECHA, "personas1", "name"],
                    limit_per_page=1
                )
                
                # Filtrar por item_id específico
                monday_item = None
                for item in item_data:
                    if str(item.get('id')) == str(item_id):
                        monday_item = item
                        break
                
                if monday_item:
                    item_procesado = parse_monday_item(monday_item)
                    
                    monday_content = {
                        'fecha': item_procesado.get('fecha_inicio', ''),
                        'titulo': item_procesado.get('name', ''),
                        'operarios': item_procesado.get('operario', '')
                    }
                    monday_hash = generate_content_hash(monday_content)
                else:
                    monday_hash = None
                
                # Actualizar estado de sincronización
                update_sync_state(
                    item_id=str(item_id),
                    event_id=event_id,
                    monday_content_hash=monday_hash,
                    google_content_hash=google_hash,
                    sync_direction="google_to_monday",
                    google_update_time=time.time()
                )
```

## Ventajas del Nuevo Sistema

### 🚀 **1. Eliminación de Cooldowns**

**Antes**: Sistema de cooldowns basado en tiempo
```python
if time_since_last < SYNC_COOLDOWN:
    return jsonify({'message': 'Sincronización en cooldown'}), 200
```

**Después**: Detección inteligente basada en contenido
```python
if sync_state and sync_state.get('monday_content_hash') == current_hash:
    return jsonify({'status': 'echo_ignored'}), 200
```

### 🛡️ **2. Prevención de Bucles Mejorada**

**Antes**: Solo cooldowns temporales
**Después**: Múltiples niveles de protección:
- ✅ Detección de ecos basada en hashes
- ✅ Detección de automatización mejorada
- ✅ Estado persistente de sincronización
- ✅ Verificación de contenido real

### 📊 **3. Gestión de Estado Persistente**

**Antes**: Variables en memoria (`last_sync_times`, `sync_origin`)
**Después**: Estado persistente en JSON
```python
# Estado persistente con información completa
{
    "item_id_event_id": {
        "monday_content_hash": "abc123...",
        "google_content_hash": "def456...",
        "sync_direction": "monday_to_google",
        "last_sync_timestamp": 1705312800.0,
        "monday_update_time": 1705312800.0,
        "google_update_time": 1705312800.0
    }
}
```

### 🔄 **4. Detección de Ecos Inteligente**

**Antes**: No detectaba ecos
**Después**: Detección basada en hashes de contenido
```python
# Generar hash del contenido actual
current_content = {
    'fecha': item_procesado.get('fecha_inicio', ''),
    'titulo': item_procesado.get('name', ''),
    'operarios': item_procesado.get('operario', '')
}
current_hash = generate_content_hash(current_content)

# Verificar si es un eco
if sync_state and sync_state.get('monday_content_hash') == current_hash:
    print("🔄 Eco detectado - contenido idéntico, ignorando")
    return jsonify({'status': 'echo_ignored'}), 200
```

### 🤖 **5. Detección de Automatización Mejorada**

**Antes**: Sistema básico de detección
**Después**: Sistema completo con activity_logs
```python
if _detectar_cambio_de_automatizacion(str(item_id), monday_handler_global):
    print("🤖 Cambio de automatización detectado, ignorando")
    return jsonify({'status': 'automation_ignored'}), 200
```

## Flujo de Webhook Refactorizado

### Monday.com → Google Calendar

```
1. Recibir webhook de Monday.com
2. Extraer item_id del webhook
3. Obtener datos completos del item
4. Obtener estado de sincronización
5. Generar hash del contenido actual
6. Verificar si es un eco (hash idéntico)
7. Verificar si fue cambio de automatización
8. Proceder con sincronización
9. Actualizar estado de sincronización
10. Retornar respuesta con estado
```

### Google Calendar → Monday.com

```
1. Recibir notificación push de Google
2. Obtener eventos usando sync tokens
3. Para cada evento cambiado:
   a. Buscar item correspondiente en Monday
   b. Obtener estado de sincronización
   c. Generar hash del contenido de Google
   d. Verificar si es un eco
   e. Proceder con sincronización según tipo de calendario
   f. Actualizar estado de sincronización
4. Retornar respuesta
```

## Respuestas de Webhook Mejoradas

### Monday Webhook

```json
{
    "status": "success|echo_ignored|automation_ignored|error",
    "message": "Descripción del resultado",
    "item_id": "123456789",
    "google_event_id": "abc123def456"
}
```

### Google Webhook

```json
{
    "status": "processed",
    "events_processed": 3,
    "events_ignored": 1,
    "errors": 0
}
```

## Configuración Requerida

### Variables en config.py
```python
# Usuario de automatización
AUTOMATION_USER_NAME = "Arnau Admin"
AUTOMATION_USER_ID = 34210704

# Columnas
COL_FECHA_GRAB = "fecha56"
COL_FECHA = COL_FECHA_GRAB
COL_GOOGLE_EVENT_ID = "text_mktfdhm3"

# Board
BOARD_ID_GRABACIONES = 123456789
```

### Archivos de Estado
```
config/
├── sync_state.json          # Estado de sincronización
├── sync_tokens.json         # Sync tokens de Google
└── channels/
    └── google_channel_map.json  # Mapeo de canales
```

## Pruebas

### Script de Pruebas
```bash
python3 scripts/testing/test_webhooks_refactored.py
```

### Casos de Prueba
1. **Gestión de estado de sincronización**
2. **Detección de ecos**
3. **Generación de hashes de contenido**
4. **Detección de automatización**
5. **Simulación de webhook de Monday**
6. **Simulación de webhook de Google**

## Logs de Ejemplo

### Webhook de Monday Exitoso
```
--- ¡Webhook de Monday Recibido! ---
🔄 Procesando webhook para item 123456789
📊 Hash del contenido actual: a1b2c3d4e5f6...
🔄 Eco detectado - contenido idéntico, ignorando
```

### Webhook de Monday con Automatización
```
--- ¡Webhook de Monday Recibido! ---
🔄 Procesando webhook para item 123456789
🔍 Analizando 8 activity_logs para item 123456789
🤖 Cambio de automatización detectado, ignorando
```

### Webhook de Google Exitoso
```
--- ¡Notificación Push de Google Calendar Recibida! ---
📅 Calendar ID: primary
🔄 Procesando 2 eventos actualizados...
📋 Procesando evento: 'Reunión Cliente' (ID: abc123def456)
📊 Hash del contenido Google: d4e5f6a1b2c3...
✅ Sincronización desde calendario maestro completada
💾 Estado de sincronización actualizado
```

## Troubleshooting

### Problema: Webhook No Detecta Ecos
**Solución**:
1. Verificar que `sync_state_manager` está funcionando
2. Confirmar que `generate_content_hash` genera hashes consistentes
3. Revisar logs para ver si se está generando el hash correctamente

### Problema: Detección de Automatización No Funciona
**Solución**:
1. Verificar `AUTOMATION_USER_ID` y `AUTOMATION_USER_NAME` en config.py
2. Confirmar que los activity_logs están disponibles
3. Revisar permisos de API en Monday.com

### Problema: Estado No Se Actualiza
**Solución**:
1. Verificar permisos de escritura en `config/sync_state.json`
2. Confirmar que `update_sync_state` se está llamando correctamente
3. Revisar logs de error para detalles específicos

### Problema: Webhook de Google No Procesa Eventos
**Solución**:
1. Verificar que los sync tokens están configurados correctamente
2. Confirmar que el mapeo de canales está actualizado
3. Revisar que `get_incremental_sync_events` funciona

## Conclusión

La refactorización de webhooks proporciona:

- ✅ **Sistema anti-bucles robusto**: Basado en hashes de contenido y estado persistente
- ✅ **Detección de ecos inteligente**: Evita sincronizaciones innecesarias
- ✅ **Detección de automatización mejorada**: Previene bucles de automatización
- ✅ **Gestión de estado persistente**: Información completa de sincronización
- ✅ **Respuestas estructuradas**: Logs claros y estados específicos
- ✅ **Eliminación de cooldowns**: Sistema más eficiente y preciso
- ✅ **Compatibilidad total**: No rompe funcionalidad existente

Este sistema es fundamental para mantener la estabilidad y eficiencia del sistema de sincronización Monday.com ↔ Google Calendar.
