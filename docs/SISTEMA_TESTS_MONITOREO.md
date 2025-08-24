# Sistema de Tests y Monitoreo para Sincronización

## Descripción

Se ha implementado un sistema completo de tests y monitoreo para el sistema de sincronización Monday ↔ Google Calendar. Este sistema permite probar la funcionalidad sin crear bucles de sincronización y monitorear el comportamiento en tiempo real.

## Componentes del Sistema

### 1. **SyncMonitor** - Monitor en Tiempo Real

Clase principal para detectar bucles de sincronización:

```python
class SyncMonitor:
    def __init__(self):
        self.sync_events = []
        self.loop_detected = False
    
    def log_sync(self, source, destination, item_id, event_id, action):
        # Registra eventos de sincronización
    
    def detect_loop(self, window_seconds=30):
        # Detecta bucles (3+ sincronizaciones en 30s)
    
    def print_summary(self):
        # Imprime resumen de eventos
```

**Características**:
- ✅ **Registro de eventos**: Cada sincronización se registra con timestamp
- ✅ **Detección de bucles**: Identifica 3+ sincronizaciones del mismo item en 30s
- ✅ **Estadísticas**: Conteo por tipo de acción (synced, echo_ignored, etc.)
- ✅ **Resumen temporal**: Últimos 5 eventos con timestamps

### 2. **SyncTester** - Sistema de Tests

Clase principal para ejecutar tests de sincronización:

```python
class SyncTester:
    def __init__(self):
        self.monitor = SyncMonitor()
        self.monday_handler = None
        self.google_service = None
        self.test_item_id = None
        self.test_event_id = None
    
    def setup_test_item(self):
        # Configura item de prueba automáticamente
    
    def test_unidirectional_monday_to_google(self):
        # Test Monday → Google
    
    def test_unidirectional_google_to_monday(self):
        # Test Google → Monday
    
    def test_loop_detection(self):
        # Test de detección de bucles
    
    def test_content_hash_consistency(self):
        # Test de consistencia de hashes
```

## Tests Implementados

### ✅ **1. Test de Consistencia de Hashes**

**Propósito**: Verificar que `generate_content_hash()` funciona correctamente.

**Casos de prueba**:
- Contenido idéntico → hashes idénticos
- Contenido diferente → hashes diferentes

**Ejemplo**:
```python
content1 = {
    'fecha': '2024-01-15T10:00:00Z',
    'titulo': 'Test Event',
    'operarios': 'Test User'
}

content2 = {
    'fecha': '2024-01-15T10:00:00Z',
    'titulo': 'Test Event',
    'operarios': 'Test User'
}

hash1 = generate_content_hash(content1)
hash2 = generate_content_hash(content2)
# hash1 == hash2 ✅
```

### ✅ **2. Test Monday → Google**

**Propósito**: Verificar sincronización unidireccional Monday → Google.

**Flujo**:
1. Obtener estado inicial de sincronización
2. Obtener contenido actual de Monday
3. Generar hash del contenido
4. Verificar si es un eco (hash idéntico)
5. Verificar si fue cambio de automatización
6. Proceder con sincronización si es necesario
7. Actualizar estado de sincronización

**Logs esperados**:
```
=== Test: Monday → Google ===
📋 Estado inicial: True
📊 Hash del contenido actual: a1b2c3d4e5f6...
🔄 Eco detectado - contenido idéntico
📊 SYNC LOG: monday → google | Item: 123456789 | Action: echo_ignored
```

### ✅ **3. Test Google → Monday**

**Propósito**: Verificar sincronización unidireccional Google → Monday.

**Flujo**:
1. Obtener evento de Google Calendar
2. Generar hash del contenido de Google
3. Obtener estado de sincronización
4. Verificar si es un eco
5. Proceder con sincronización
6. Actualizar estado

**Logs esperados**:
```
=== Test: Google → Monday ===
📅 Evento de Google: Reunión Cliente
📊 Hash del contenido Google: d4e5f6a1b2c3...
🔄 Eco detectado - contenido idéntico
📊 SYNC LOG: google → monday | Item: 123456789 | Action: echo_ignored
```

### ✅ **4. Test de Detección de Bucles**

**Propósito**: Verificar que el sistema detecta bucles de sincronización.

**Simulación**:
```python
# Simular múltiples sincronizaciones rápidas
for i in range(3):
    # Monday → Google
    self.monitor.log_sync('monday', 'google', item_id, event_id, 'synced')
    time.sleep(1)
    
    # Google → Monday
    self.monitor.log_sync('google', 'monday', item_id, event_id, 'synced')
    time.sleep(1)
```

**Detección esperada**:
```
⚠️ POSIBLE BUCLE DETECTADO: {'123456789': 6}
🚨 BUCLE DETECTADO - Deteniendo tests
```

## Endpoints de Debugging

### 📊 **GET /debug/sync-state/<item_id>**

Muestra el estado de sincronización para un item específico.

**Respuesta**:
```json
{
    "item_id": "123456789",
    "states": {
        "abc123def456": {
            "monday_content_hash": "a1b2c3d4e5f6...",
            "google_content_hash": "d4e5f6a1b2c3...",
            "sync_direction": "monday_to_google",
            "last_sync_timestamp": 1705312800.0,
            "monday_update_time": 1705312800.0,
            "google_update_time": 1705312800.0
        }
    },
    "total_states": 1
}
```

### 📊 **GET /debug/last-syncs**

Muestra las últimas 10 sincronizaciones.

**Respuesta**:
```json
{
    "statistics": {
        "total_states": 25,
        "last_cleanup": "2024-01-15T10:00:00Z",
        "old_states_removed": 5
    },
    "last_syncs": [
        {
            "key": "123456789_abc123def456",
            "item_id": "123456789",
            "event_id": "abc123def456",
            "state": {
                "sync_direction": "monday_to_google",
                "last_sync_timestamp": 1705312800.0
            }
        }
    ],
    "total_states": 25
}
```

### 🗑️ **DELETE /debug/clear-state/<item_id>**

Limpia el estado de sincronización para un item específico (para testing).

**Respuesta**:
```json
{
    "item_id": "123456789",
    "message": "Estado limpiado para 2 eventos",
    "cleared_states": ["abc123def456", "def456ghi789"]
}
```

### 📊 **GET /debug/sync-monitor**

Endpoint para monitorear sincronizaciones en tiempo real.

**Respuesta**:
```json
{
    "monitor_status": "active",
    "statistics": {
        "total_states": 25,
        "last_cleanup": "2024-01-15T10:00:00Z",
        "old_states_removed": 5
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "message": "Monitor de sincronización activo"
}
```

## Monitor en Tiempo Real

### 🚀 **RealtimeSyncMonitor**

Monitor que verifica el estado del servidor periódicamente:

```python
class RealtimeSyncMonitor:
    def __init__(self, server_url="http://localhost:6754"):
        self.server_url = server_url
        self.monitor = SyncMonitor()
        self.check_interval = 5  # segundos
    
    def start_monitoring(self):
        # Inicia monitoreo continuo
    
    def check_sync_status(self):
        # Verifica estado del servidor
```

**Uso**:
```bash
python3 scripts/testing/monitor_sync_realtime.py --mode realtime
```

**Salida**:
```
[14:30:15] 📊 Estado del Sistema:
   Total de estados: 25
   Última limpieza: 2024-01-15T10:00:00Z
   Estados antiguos eliminados: 5
   Últimas sincronizaciones: 3
   🔄 Última sync: hace 45s
```

### 🎮 **InteractiveMonitor**

Monitor interactivo con comandos:

```python
class InteractiveMonitor:
    def start_interactive(self):
        # Inicia interfaz interactiva
```

**Comandos disponibles**:
- `stats` - Mostrar estadísticas actuales
- `monitor` - Iniciar monitoreo en tiempo real
- `activity` - Mostrar actividad reciente
- `clear` - Limpiar estado de un item
- `test` - Ejecutar test de sincronización
- `help` - Mostrar ayuda
- `quit` - Salir

**Uso**:
```bash
python3 scripts/testing/monitor_sync_realtime.py --mode interactive
```

**Ejemplo de sesión**:
```
🎮 Monitor Interactivo de Sincronización
==================================================
Comandos disponibles:
  stats    - Mostrar estadísticas actuales
  monitor  - Iniciar monitoreo en tiempo real
  activity - Mostrar actividad reciente
  clear    - Limpiar estado de un item
  test     - Ejecutar test de sincronización
  help     - Mostrar esta ayuda
  quit     - Salir

📊 Monitor > stats

📊 ESTADÍSTICAS DEL SISTEMA:
========================================
Total de estados: 25
Última limpieza: 2024-01-15T10:00:00Z
Estados antiguos eliminados: 5

📊 Monitor > activity

🕒 ACTIVIDAD RECIENTE:
========================================
1. Item 123456789 → abc123def456 | monday_to_google | hace 45s
2. Item 987654321 → def456ghi789 | google_to_monday | hace 2m
3. Item 123456789 → abc123def456 | echo_ignored | hace 5m

📊 Monitor > quit
👋 ¡Hasta luego!
```

## Ejecución de Tests

### 🧪 **Test Completo del Sistema**

```bash
python3 scripts/testing/test_sync_system.py
```

**Salida esperada**:
```
🚀 Iniciando tests completos del sistema de sincronización...

✅ Configuración verificada:
   - Usuario automatización: Arnau Admin
   - Board ID: 123456789
   - Columna fecha: fecha56

🔧 Configurando item de prueba...
✅ Item de prueba configurado: 123456789
   Google Event ID: abc123def456
   Nombre: Reunión Cliente

🧪 Ejecutando test de consistencia de hashes...
=== Test: Consistencia de Hashes ===
✅ Hashes idénticos para contenido idéntico
✅ Hashes diferentes para contenido diferente

🧪 Ejecutando test Monday → Google...
=== Test: Monday → Google ===
📋 Estado inicial: True
📊 Hash del contenido actual: a1b2c3d4e5f6...
🔄 Eco detectado - contenido idéntico
📊 SYNC LOG: monday → google | Item: 123456789 | Action: echo_ignored

🧪 Ejecutando test Google → Monday...
=== Test: Google → Monday ===
📅 Evento de Google: Reunión Cliente
📊 Hash del contenido Google: d4e5f6a1b2c3...
🔄 Eco detectado - contenido idéntico
📊 SYNC LOG: google → monday | Item: 123456789 | Action: echo_ignored

🧪 Ejecutando test de detección de bucles...
=== Test: Detección de Bucles ===
🔄 Simulando cambio rápido Monday → Google → Monday...
   Iteración 1/3
   Iteración 2/3
   Iteración 3/3
⚠️ POSIBLE BUCLE DETECTADO: {'123456789': 6}
🚨 Bucle detectado correctamente

============================================================
📊 RESUMEN DE TESTS
============================================================
   Consistencia de Hashes: ✅ PASÓ
   Monday → Google: ✅ PASÓ
   Google → Monday: ✅ PASÓ
   Detección de Bucles: ✅ PASÓ

📈 Resultado: 4/4 tests pasaron

📊 RESUMEN DE SINCRONIZACIÓN (8 eventos):
   echo_ignored: 6
   synced: 2

🕒 ÚLTIMOS 5 EVENTOS:
   14:30:15 | monday → google | echo_ignored
   14:30:16 | google → monday | echo_ignored
   14:30:17 | monday → google | synced
   14:30:18 | google → monday | synced
   14:30:19 | monday → google | synced
🚨 BUCLE DETECTADO DURANTE LOS TESTS

🎉 ¡Todos los tests pasaron exitosamente!
```

### 🔧 **Configuración de Tests**

**Variables requeridas en config.py**:
```python
# Monday API
MONDAY_API_KEY = "tu_api_key_aqui"

# Usuario de automatización
AUTOMATION_USER_NAME = "Arnau Admin"
AUTOMATION_USER_ID = 34210704

# Board y columnas
BOARD_ID_GRABACIONES = 123456789
COL_FECHA = "fecha56"
COL_GOOGLE_EVENT_ID = "text_mktfdhm3"

# Google Calendar
MASTER_CALENDAR_ID = "primary"
```

## Detección de Bucles

### 🔄 **Algoritmo de Detección**

```python
def detect_loop(self, window_seconds=30):
    # Obtener eventos recientes en la ventana de tiempo
    recent_events = [
        e for e in self.sync_events 
        if (datetime.now() - e['timestamp']).seconds < window_seconds
    ]
    
    # Contar eventos por item
    item_counts = {}
    for event in recent_events:
        key = f"{event['item_id']}"
        item_counts[key] = item_counts.get(key, 0) + 1
    
    # Detectar bucles (3+ eventos del mismo item)
    loops = {k: v for k, v in item_counts.items() if v >= 3}
    
    if loops:
        print(f"⚠️ POSIBLE BUCLE DETECTADO: {loops}")
        return True
    return False
```

### 📊 **Criterios de Bucle**

- **Ventana de tiempo**: 30 segundos
- **Umbral de detección**: 3+ sincronizaciones del mismo item
- **Tipos de eventos**: Cualquier acción (synced, echo_ignored, automation_ignored, error)

### 🚨 **Ejemplo de Bucle Detectado**

```
📊 SYNC LOG: monday → google | Item: 123456789 | Action: synced
📊 SYNC LOG: google → monday | Item: 123456789 | Action: synced
📊 SYNC LOG: monday → google | Item: 123456789 | Action: synced
📊 SYNC LOG: google → monday | Item: 123456789 | Action: synced
📊 SYNC LOG: monday → google | Item: 123456789 | Action: synced
📊 SYNC LOG: google → monday | Item: 123456789 | Action: synced
⚠️ POSIBLE BUCLE DETECTADO: {'123456789': 6}
🚨 BUCLE DETECTADO - Deteniendo tests
```

## Monitoreo en Producción

### 📡 **Configuración del Servidor**

Para usar los endpoints de debugging en producción:

1. **Verificar que el servidor esté ejecutándose**:
```bash
python3 app.py
```

2. **Probar endpoints**:
```bash
# Verificar salud del servidor
curl http://localhost:6754/health

# Obtener estadísticas
curl http://localhost:6754/debug/sync-monitor

# Ver últimas sincronizaciones
curl http://localhost:6754/debug/last-syncs

# Ver estado de un item específico
curl http://localhost:6754/debug/sync-state/123456789
```

### 🔍 **Monitoreo Continuo**

Para monitoreo continuo en producción:

```bash
# Modo tiempo real
python3 scripts/testing/monitor_sync_realtime.py --mode realtime --server http://tu-servidor:6754

# Modo interactivo
python3 scripts/testing/monitor_sync_realtime.py --mode interactive --server http://tu-servidor:6754
```

### 📊 **Logs de Monitoreo**

**Logs normales**:
```
[14:30:15] 📊 Estado del Sistema:
   Total de estados: 25
   Última limpieza: 2024-01-15T10:00:00Z
   Estados antiguos eliminados: 5
   Últimas sincronizaciones: 3
   🔄 Última sync: hace 45s
```

**Logs con actividad**:
```
[14:30:20] 📊 Estado del Sistema:
   Total de estados: 26
   Última limpieza: 2024-01-15T10:00:00Z
   Estados antiguos eliminados: 5
   Últimas sincronizaciones: 4
   🔄 Última sync: hace 5s
```

## Troubleshooting

### ❌ **Problema: Tests No Encuentran Item de Prueba**

**Solución**:
1. Verificar que hay items en el tablero con Google Event ID
2. Confirmar que `BOARD_ID_GRABACIONES` es correcto
3. Verificar permisos de API en Monday.com

### ❌ **Problema: Monitor No Se Conecta al Servidor**

**Solución**:
1. Verificar que el servidor esté ejecutándose en el puerto correcto
2. Confirmar la URL del servidor
3. Verificar firewall/red

### ❌ **Problema: Detección de Bucles No Funciona**

**Solución**:
1. Verificar que `SyncMonitor` esté registrando eventos correctamente
2. Confirmar que la ventana de tiempo (30s) es apropiada
3. Revisar logs para ver si se están detectando eventos

### ❌ **Problema: Endpoints de Debugging No Responden**

**Solución**:
1. Verificar que el servidor esté ejecutándose
2. Confirmar que los endpoints están correctamente implementados
3. Revisar logs del servidor para errores

## Conclusión

El sistema de tests y monitoreo proporciona:

- ✅ **Tests completos**: Verificación de todas las funcionalidades
- ✅ **Detección de bucles**: Prevención de bucles infinitos
- ✅ **Monitoreo en tiempo real**: Seguimiento continuo del sistema
- ✅ **Endpoints de debugging**: Herramientas para diagnóstico
- ✅ **Interfaz interactiva**: Fácil uso para administradores
- ✅ **Logs detallados**: Información completa para troubleshooting
- ✅ **Configuración flexible**: Adaptable a diferentes entornos

Este sistema es fundamental para mantener la estabilidad y confiabilidad del sistema de sincronización Monday.com ↔ Google Calendar en producción.
