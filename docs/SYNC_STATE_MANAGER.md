# SyncStateManager - Gestor de Estado de Sincronización

## Descripción

El `SyncStateManager` es un componente clave del sistema de sincronización entre Monday.com y Google Calendar. Su función principal es mantener un registro persistente del estado de cada sincronización para evitar bucles infinitos, optimizar las operaciones y proporcionar trazabilidad completa.

## Características Principales

- **Persistencia**: Almacena el estado en archivo JSON (`config/sync_state.json`)
- **Thread-safe**: Manejo seguro de concurrencia con file locking
- **Detección de cambios**: Compara hashes de contenido para determinar si es necesario sincronizar
- **Trazabilidad**: Registra dirección, timestamps y versiones de cada sincronización
- **Limpieza automática**: Elimina estados obsoletos (más de 30 días por defecto)
- **Estadísticas**: Proporciona métricas de uso y rendimiento

## Estructura de Datos

### Clave de Sincronización
```
{item_id}_{event_id}
```
Ejemplo: `12345_google_event_67890`

### Estado de Sincronización
```json
{
  "last_monday_update": 1640995200.0,
  "last_google_update": 1640995200.0,
  "monday_content_hash": "a1e32e68aaf64f6e...",
  "google_content_hash": "6212d90a73e308be...",
  "sync_version": 5,
  "last_sync_direction": "monday_to_google",
  "last_sync_timestamp": 1640995200.0
}
```

### Campos del Estado

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `last_monday_update` | float | Timestamp de última actualización en Monday |
| `last_google_update` | float | Timestamp de última actualización en Google |
| `monday_content_hash` | string | Hash SHA-256 del contenido actual en Monday |
| `google_content_hash` | string | Hash SHA-256 del contenido actual en Google |
| `sync_version` | int | Número incremental de versión de sincronización |
| `last_sync_direction` | string | Dirección de la última sincronización |
| `last_sync_timestamp` | float | Timestamp de la última sincronización exitosa |

## Uso Básico

### Importación
```python
from sync_state_manager import SyncStateManager, get_sync_state, update_sync_state, is_change_needed
```

### Crear Instancia
```python
# Usar archivo por defecto (config/sync_state.json)
manager = SyncStateManager()

# Usar archivo personalizado
manager = SyncStateManager("config/mi_estado_sync.json")
```

### Verificar si se Necesita Sincronizar
```python
# Generar hash del contenido actual
monday_content = obtener_contenido_monday(item_id)
monday_hash = manager._generate_content_hash(monday_content)

# Verificar si hay cambios
if is_change_needed(item_id, event_id, monday_hash, "monday"):
    print("Se detectaron cambios, proceder con sincronización")
else:
    print("No hay cambios, omitir sincronización")
```

### Actualizar Estado Después de Sincronización
```python
success = update_sync_state(
    item_id="12345",
    event_id="google_event_67890",
    monday_content_hash=monday_hash,
    google_content_hash=google_hash,
    sync_direction="monday_to_google",
    monday_update_time=time.time()
)
```

### Obtener Estado Actual
```python
state = get_sync_state(item_id, event_id)
if state:
    print(f"Versión: {state['sync_version']}")
    print(f"Última dirección: {state['last_sync_direction']}")
```

## Integración con Webhooks

### Webhook de Monday.com
```python
def procesar_webhook_monday(webhook_data):
    item_id = webhook_data.get("item_id")
    event_id = webhook_data.get("google_event_id")
    
    # Obtener contenido actualizado
    monday_content = obtener_contenido_monday(item_id)
    monday_hash = manager._generate_content_hash(monday_content)
    
    # Verificar si se necesita sincronizar
    if is_change_needed(item_id, event_id, monday_hash, "monday"):
        # Realizar sincronización
        sync_to_google_calendar(item_id, event_id, monday_content)
        
        # Actualizar estado
        update_sync_state(
            item_id, event_id,
            monday_content_hash=monday_hash,
            sync_direction="monday_to_google",
            monday_update_time=time.time()
        )
```

### Webhook de Google Calendar
```python
def procesar_webhook_google(webhook_data):
    event_id = webhook_data.get("event_id")
    item_id = webhook_data.get("monday_item_id")
    
    # Obtener contenido actualizado
    google_content = obtener_contenido_google(event_id)
    google_hash = manager._generate_content_hash(google_content)
    
    # Verificar si se necesita sincronizar
    if is_change_needed(item_id, event_id, google_hash, "google"):
        # Realizar sincronización
        sync_to_monday(item_id, event_id, google_content)
        
        # Actualizar estado
        update_sync_state(
            item_id, event_id,
            google_content_hash=google_hash,
            sync_direction="google_to_monday",
            google_update_time=time.time()
        )
```

## Funciones de Mantenimiento

### Limpiar Estados Obsoletos
```python
# Eliminar estados de más de 30 días
cleaned_count = manager.cleanup_old_states(days_threshold=30)
print(f"Estados eliminados: {cleaned_count}")

# Eliminar estados de más de 7 días
cleaned_count = manager.cleanup_old_states(days_threshold=7)
```

### Obtener Estadísticas
```python
stats = manager.get_sync_statistics()
print(f"Total de sincronizaciones: {stats['total_syncs']}")
print(f"Sincronizaciones recientes: {stats['recent_syncs']}")
print(f"Sincronización más antigua: {stats['oldest_sync']}")
print(f"Sincronización más reciente: {stats['newest_sync']}")
```

### Resetear Estado Específico
```python
# Eliminar estado de un par item/event específico
success = manager.reset_sync_state(item_id, event_id)
if success:
    print("Estado reseteado correctamente")
```

## Manejo de Errores

El `SyncStateManager` incluye manejo robusto de errores:

- **Archivo corrupto**: Se crea un nuevo archivo automáticamente
- **Errores de escritura**: Se mantiene la integridad con operaciones atómicas
- **Concurrencia**: Se evitan conflictos con file locking
- **Logging**: Todos los errores se registran con logging apropiado

### Ejemplo de Manejo de Errores
```python
try:
    state = get_sync_state(item_id, event_id)
    if state is None:
        # Estado no existe, crear nuevo
        update_sync_state(item_id, event_id, ...)
except Exception as e:
    logger.error(f"Error al acceder al estado: {e}")
    # Fallback: asumir que se necesita sincronizar
    return True
```

## Optimizaciones

### Generación de Hashes
```python
# El hash se genera de forma consistente
content = {"title": "Reunión", "date": "2024-01-15"}
hash1 = manager._generate_content_hash(content)
hash2 = manager._generate_content_hash(content)
assert hash1 == hash2  # Siempre igual para el mismo contenido
```

### Operaciones Atómicas
```python
# Las escrituras son atómicas (usando archivo temporal)
manager._save_state(new_state)
# Si falla, el archivo original se mantiene intacto
```

### Thread Safety
```python
# Múltiples hilos pueden acceder simultáneamente
import threading

def worker(thread_id):
    manager.update_sync_state(f"item_{thread_id}", f"event_{thread_id}", ...)

threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Configuración

### Variables de Entorno
```bash
# No requiere variables de entorno específicas
# El archivo se crea automáticamente en config/sync_state.json
```

### Personalización
```python
# Cambiar ruta del archivo
manager = SyncStateManager("/ruta/personalizada/estado.json")

# Cambiar nivel de logging
import logging
logging.getLogger('sync_state_manager').setLevel(logging.DEBUG)
```

## Monitoreo y Debugging

### Verificar Estado del Archivo
```python
import os
from pathlib import Path

state_file = Path("config/sync_state.json")
if state_file.exists():
    size = state_file.stat().st_size
    print(f"Archivo de estado: {size} bytes")
    
    # Ver contenido
    with open(state_file, 'r') as f:
        data = json.load(f)
        print(f"Estados registrados: {len(data)}")
```

### Logs de Debug
```python
# Habilitar logs detallados
logging.basicConfig(level=logging.DEBUG)

# Los logs incluyen:
# - Creación de archivos
# - Actualizaciones de estado
# - Detección de cambios
# - Operaciones de limpieza
# - Errores y excepciones
```

## Casos de Uso Comunes

### 1. Sincronización Inicial
```python
# Primera vez que se sincroniza un item/event
if not get_sync_state(item_id, event_id):
    # No existe estado previo, sincronizar
    sync_content(item_id, event_id)
    update_sync_state(item_id, event_id, ...)
```

### 2. Sincronización Incremental
```python
# Verificar cambios antes de sincronizar
content = get_current_content(source)
hash = manager._generate_content_hash(content)

if is_change_needed(item_id, event_id, hash, source):
    sync_content(item_id, event_id)
    update_sync_state(item_id, event_id, ...)
```

### 3. Resolución de Conflictos
```python
# Detectar conflictos comparando timestamps
state = get_sync_state(item_id, event_id)
if state:
    monday_time = state['last_monday_update']
    google_time = state['last_google_update']
    
    if monday_time > google_time:
        # Monday es más reciente
        sync_direction = "monday_to_google"
    else:
        # Google es más reciente
        sync_direction = "google_to_monday"
```

### 4. Limpieza Programada
```python
# Ejecutar limpieza periódicamente
import schedule
import time

def cleanup_job():
    cleaned = manager.cleanup_old_states(days_threshold=30)
    print(f"Limpieza completada: {cleaned} estados eliminados")

schedule.every().day.at("02:00").do(cleanup_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Troubleshooting

### Problema: Archivo Corrupto
```python
# El sistema maneja automáticamente archivos corruptos
# Si persiste el problema:
manager = SyncStateManager()
manager._save_state({})  # Resetear completamente
```

### Problema: Estados Desincronizados
```python
# Resetear estado específico
manager.reset_sync_state(item_id, event_id)

# O resetear todos los estados
manager._save_state({})
```

### Problema: Rendimiento Lento
```python
# Verificar tamaño del archivo
stats = manager.get_sync_statistics()
if stats['total_syncs'] > 10000:
    # Considerar limpieza más agresiva
    manager.cleanup_old_states(days_threshold=7)
```

## Pruebas

### Ejecutar Pruebas Unitarias
```bash
python3 scripts/testing/test_sync_state_manager.py
```

### Ejecutar Ejemplo de Integración
```bash
python3 scripts/testing/ejemplo_integracion_sync_state.py
```

## Contribución

Para contribuir al `SyncStateManager`:

1. Añadir pruebas para nuevas funcionalidades
2. Mantener compatibilidad con la estructura de datos existente
3. Documentar cambios en la API
4. Seguir las convenciones de logging y manejo de errores

## Changelog

### v1.0.0
- Implementación inicial del SyncStateManager
- Funcionalidades básicas de CRUD
- Detección de cambios con hashes
- Thread safety con file locking
- Limpieza automática de estados obsoletos
- Estadísticas y monitoreo
- Manejo robusto de errores
