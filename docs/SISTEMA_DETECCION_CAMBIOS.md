# Sistema de Detección de Cambios - Anti-Bucles

## Descripción

El nuevo sistema de detección de cambios implementado en `sync_logic.py` está diseñado para evitar bucles infinitos de sincronización entre Monday.com y Google Calendar. Utiliza hashes de contenido determinísticos y un gestor de estado persistente para distinguir entre cambios reales y "ecos" de sincronización previa.

## Componentes Principales

### 1. `generate_content_hash(content_data)`

**Propósito**: Genera un hash MD5 determinístico del contenido relevante de un item/evento.

**Características**:
- Solo incluye campos que importan para la sincronización
- Ignora campos de metadata (updated_at, etags, etc.)
- Ordena el contenido para consistencia
- Funciona tanto para Monday.com como Google Calendar

**Campos relevantes para Monday.com**:
- `name`: Nombre del item
- `fecha_inicio`: Fecha de inicio
- `fecha_fin`: Fecha de fin
- `operario`: Operario asignado
- `cliente`: Cliente
- `ubicacion`: Ubicación
- `estadopermisos`: Estado de permisos
- `accionesrealizar`: Acciones a realizar
- `contactoobra`: Contactos de obra
- `telefonoobra`: Teléfonos de obra
- `contactocomercial`: Contactos comerciales
- `telefonocomercial`: Teléfonos comerciales
- `linkdropbox`: Link de Dropbox

**Campos relevantes para Google Calendar**:
- `summary`: Título del evento
- `start`: Fecha/hora de inicio
- `end`: Fecha/hora de fin
- `location`: Ubicación
- `description`: Descripción

### 2. `detect_real_change(item_id, event_id, content_hash, source)`

**Propósito**: Detecta si un cambio es real o es un "eco" de sincronización previa.

**Lógica de detección**:
1. **Sin estado previo**: Cambio real (primera sincronización)
2. **Hash diferente**: Cambio real (contenido modificado)
3. **Hash idéntico + tiempo reciente (< 5 min)**: Eco (saltar sincronización)
4. **Hash idéntico + tiempo antiguo (> 5 min)**: Posible cambio real (permitir sincronización por seguridad)

**Parámetros**:
- `item_id`: ID del item de Monday.com
- `event_id`: ID del evento de Google Calendar
- `content_hash`: Hash del contenido actual
- `source`: Fuente del cambio ("monday" o "google")

**Retorna**: `True` si es cambio real, `False` si es eco

### 3. Integración con `sincronizar_item_via_webhook()`

**Flujo actualizado**:
1. Obtener datos del item de Monday.com
2. Generar hash del contenido actual
3. Verificar si el cambio es real usando `detect_real_change()`
4. Si es eco → salir sin hacer nada
5. Si es cambio real → proceder con sincronización
6. Al final, actualizar `sync_state` con nuevos hashes y timestamps

## Ventajas del Sistema

### 1. Prevención de Bucles Infinitos
- Detecta automáticamente cuando un cambio es un "eco"
- Evita sincronizaciones innecesarias
- Reduce la carga en las APIs

### 2. Detección Inteligente
- Compara solo contenido relevante
- Ignora campos de metadata que cambian automáticamente
- Usa timestamps para validación adicional

### 3. Persistencia
- Estado guardado en `config/sync_state.json`
- Thread-safe con file locking
- Operaciones atómicas

### 4. Bidireccional
- Funciona en ambas direcciones (Monday ↔ Google)
- Mantiene hashes separados para cada fuente
- Permite sincronización bidireccional segura

## Ejemplos de Uso

### Ejemplo 1: Cambio Real en Monday.com
```python
# Usuario modifica un item en Monday.com
item_content = {
    "name": "Reunión importante",
    "fecha_inicio": "2024-01-15T10:00:00",
    "operario": "Arnau Admin",
    "cliente": "Cliente A"
}

# Generar hash
content_hash = generate_content_hash(item_content)

# Detectar si es cambio real
is_real = detect_real_change("item_123", "event_456", content_hash, "monday")

if is_real:
    # Proceder con sincronización
    sincronizar_item_via_webhook("item_123", monday_handler, google_service)
else:
    # Es un eco, saltar
    print("Eco detectado, saltando sincronización")
```

### Ejemplo 2: Eco de Sincronización
```python
# Después de una sincronización, Monday.com envía el mismo contenido
# El sistema detecta que es un eco y lo ignora

content_hash = "abc123def456"  # Mismo hash que antes
is_real = detect_real_change("item_123", "event_456", content_hash, "monday")

# is_real = False (eco detectado)
```

### Ejemplo 3: Cambio Real Después de Tiempo
```python
# Si el mismo contenido se envía después de mucho tiempo,
# el sistema lo considera un posible cambio real por seguridad

# Simular tiempo antiguo
old_state = get_sync_state("item_123", "event_456")
if old_state:
    old_state["last_sync_timestamp"] = time.time() - 360  # 6 minutos atrás
    # ... actualizar estado

content_hash = "abc123def456"  # Mismo hash
is_real = detect_real_change("item_123", "event_456", content_hash, "monday")

# is_real = True (por seguridad)
```

## Configuración

### Umbral de Tiempo
El sistema usa un umbral de 5 minutos para detectar ecos:
```python
if time_diff < 300:  # 5 minutos
    return False  # Eco
else:
    return True   # Posible cambio real
```

### Archivo de Estado
El estado se guarda en `config/sync_state.json` con esta estructura:
```json
{
  "item_123_event_456": {
    "last_monday_update": 1640995200.0,
    "last_google_update": 1640995200.0,
    "monday_content_hash": "abc123...",
    "google_content_hash": "def456...",
    "sync_version": 5,
    "last_sync_direction": "monday_to_google",
    "last_sync_timestamp": 1640995200.0
  }
}
```

## Monitoreo y Debugging

### Logs de Detección
El sistema genera logs detallados:
```
🔍 Detectando cambio real para item_123 ↔ event_456
   Fuente: monday
   Hash actual: abc123def456...
   Hash almacenado: abc123def456...
   ⚠️  Hash idéntico - probable eco de sincronización
   📅 Última sincronización: hace 0.0s
   🛑 Eco confirmado (última sync hace 0.0s)
```

### Estadísticas
Puedes obtener estadísticas del estado de sincronización:
```python
from sync_state_manager import sync_state_manager

stats = sync_state_manager.get_sync_statistics()
print(f"Total de sincronizaciones: {stats['total_syncs']}")
print(f"Sincronizaciones recientes: {stats['recent_syncs']}")
```

## Casos de Uso Comunes

### 1. Webhook de Monday.com
```python
def procesar_webhook_monday(webhook_data):
    item_id = webhook_data.get("item_id")
    
    # Obtener contenido actualizado
    item_content = obtener_contenido_monday(item_id)
    content_hash = generate_content_hash(item_content)
    
    # Verificar si es cambio real
    if detect_real_change(item_id, event_id, content_hash, "monday"):
        # Realizar sincronización
        sincronizar_item_via_webhook(item_id, monday_handler, google_service)
    else:
        # Es un eco, ignorar
        print("Eco detectado, ignorando webhook")
```

### 2. Webhook de Google Calendar
```python
def procesar_webhook_google(webhook_data):
    event_id = webhook_data.get("event_id")
    
    # Obtener contenido actualizado
    event_content = obtener_contenido_google(event_id)
    content_hash = generate_content_hash(event_content)
    
    # Verificar si es cambio real
    if detect_real_change(item_id, event_id, content_hash, "google"):
        # Realizar sincronización
        sincronizar_desde_google(event_id, monday_handler, google_service)
    else:
        # Es un eco, ignorar
        print("Eco detectado, ignorando webhook")
```

## Troubleshooting

### Problema: Falsos Positivos
Si el sistema detecta ecos cuando debería detectar cambios reales:
1. Verificar que los campos relevantes están incluidos en `generate_content_hash()`
2. Ajustar el umbral de tiempo si es necesario
3. Revisar los logs para entender la lógica de detección

### Problema: Falsos Negativos
Si el sistema no detecta ecos y permite bucles:
1. Verificar que el `sync_state` se está actualizando correctamente
2. Revisar que los hashes se están generando de forma consistente
3. Comprobar que el archivo de estado no está corrupto

### Problema: Rendimiento
Si el sistema es lento:
1. Verificar que el archivo de estado no es muy grande
2. Ejecutar limpieza de estados obsoletos: `cleanup_old_states()`
3. Considerar optimizar la generación de hashes

## Pruebas

### Ejecutar Pruebas Unitarias
```bash
python3 scripts/testing/test_simple_detection.py
```

### Verificar Funcionamiento
```python
# Prueba manual
from sync_logic import generate_content_hash, detect_real_change

# Generar hash
content = {"name": "Test", "fecha_inicio": "2024-01-15"}
hash = generate_content_hash(content)

# Detectar cambio
is_real = detect_real_change("item_123", "event_456", hash, "monday")
print(f"Es cambio real: {is_real}")
```

## Conclusión

El nuevo sistema de detección de cambios proporciona una solución robusta para evitar bucles infinitos en la sincronización entre Monday.com y Google Calendar. Utiliza hashes determinísticos, validación temporal y persistencia de estado para distinguir entre cambios reales y ecos de sincronización.

**Beneficios principales**:
- ✅ Eliminación de bucles infinitos
- ✅ Reducción de carga en APIs
- ✅ Sincronización más eficiente
- ✅ Detección inteligente de cambios
- ✅ Persistencia y trazabilidad
- ✅ Funcionamiento bidireccional
