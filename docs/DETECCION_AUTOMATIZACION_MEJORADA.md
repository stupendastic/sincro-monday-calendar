# Detección de Automatización Mejorada

## Descripción

Se ha implementado un sistema mejorado de detección de automatización en `sync_logic.py` que analiza `activity_logs` en lugar de `updates` para detectar cambios específicos y evitar bucles de sincronización. Este sistema es más preciso y confiable que la versión anterior.

## Problema Resuelto

**Antes**: El sistema solo analizaba `updates` (comentarios) para detectar automatización, lo cual era impreciso y no detectaba cambios específicos en columnas.

**Después**: El sistema analiza `activity_logs` que registran todos los cambios reales en el item, incluyendo modificaciones específicas de columnas, usuarios y timestamps exactos.

## Componentes Implementados

### 1. Query GraphQL Mejorada

**Nueva query que analiza activity_logs**:
```graphql
query($itemId: [Int!]) {
    items(ids: $itemId) {
        id
        name
        activity_logs(limit: 10) {
            id
            event
            data
            created_at
            user {
                id
                name
                email
            }
        }
    }
}
```

**Ventajas sobre la query anterior**:
- ✅ Analiza los últimos 10 activity_logs (vs 5 updates)
- ✅ Incluye `event` para identificar tipo de cambio
- ✅ Incluye `data` con detalles específicos del cambio
- ✅ Timestamps precisos en `created_at`
- ✅ Información completa del usuario

### 2. Detección Específica de Cambios en Columna de Fecha

**Análisis inteligente de `data`**:
```python
if event == 'change_column_value' and data:
    # Analizar el data JSON para identificar la columna
    data_obj = json.loads(data) if isinstance(data, str) else data
    
    # Verificar si es cambio en la columna de fecha
    if isinstance(data_obj, dict):
        column_id = data_obj.get('column_id', '')
        if column_id == config.COL_FECHA:  # "fecha56"
            fecha_changes.append({
                'timestamp': log_timestamp,
                'user_id': user_id,
                'user_name': user_name,
                'data': data_obj
            })
```

**Detección específica**:
- ✅ Identifica cambios en la columna `fecha56` específicamente
- ✅ Registra timestamp exacto del cambio
- ✅ Captura información del usuario que hizo el cambio
- ✅ Almacena datos completos del cambio para análisis posterior

### 3. Detección de Usuario de Automatización

**Verificación dual (ID y nombre)**:
```python
is_automation = (
    str(user_id) == str(config.AUTOMATION_USER_ID) or 
    user_name == config.AUTOMATION_USER_NAME
)
```

**Configuración requerida**:
```python
# En config.py
AUTOMATION_USER_NAME = "Arnau Admin"
AUTOMATION_USER_ID = 34210704  # ID de Monday.com para Arnau Admin
```

### 4. Análisis de Timestamps

**Verificación de cambios recientes**:
```python
# Verificar si el último cambio fue de automatización en los últimos 10 segundos
if automation_changes:
    latest_automation = automation_changes[0]  # Más reciente
    time_diff = current_time - latest_automation['timestamp']
    
    if time_diff < 10:  # Últimos 10 segundos
        print(f"🤖 Cambio de automatización detectado, ignorando para evitar bucle")
        return True
```

**Conversión de timestamps**:
```python
# Monday.com usa formato ISO 8601
from datetime import datetime
log_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
log_timestamp = log_time.timestamp()
```

### 5. Detección de Bucles

**Sistema de detección de bucles**:
```python
# DETECCIÓN DE BUCLE: Mismo valor cambiado 2+ veces en 30 segundos
if len(fecha_changes) >= 2:
    # Verificar si hay cambios repetitivos en la columna de fecha
    recent_fecha_changes = [
        change for change in fecha_changes 
        if (current_time - change['timestamp']) < 30
    ]
    
    if len(recent_fecha_changes) >= 2:
        # Verificar si son del mismo usuario (automatización)
        automation_fecha_changes = [
            change for change in recent_fecha_changes
            if (str(change['user_id']) == str(config.AUTOMATION_USER_ID) or 
                change['user_name'] == config.AUTOMATION_USER_NAME)
        ]
        
        if len(automation_fecha_changes) >= 2:
            print(f"🔄 BUCLE DETECTADO: {len(automation_fecha_changes)} cambios de fecha por automatización en 30s")
            print(f"🛑 Deteniendo sincronización para evitar bucle infinito")
            return True
```

**Criterios de bucle**:
- ✅ 2+ cambios en la columna de fecha
- ✅ En un período de 30 segundos
- ✅ Realizados por el usuario de automatización
- ✅ Detección automática y bloqueo inmediato

## Flujo de Detección Completo

### 1. Obtención de Activity Logs
```python
# Obtener activity_logs recientes del item (más preciso que updates)
query = f"""
query {{
    items(ids: [{item_id}]) {{
        id
        name
        activity_logs(limit: 10) {{
            id
            event
            data
            created_at
            user {{
                id
                name
                email
            }}
        }}
    }}
}}
"""
```

### 2. Análisis de Cada Activity Log
```python
for log in activity_logs[:10]:
    event = log.get('event', '')
    data = log.get('data', '')
    created_at = log.get('created_at', '')
    user = log.get('user', {})
    user_id = user.get('id')
    user_name = user.get('name', '')
    
    # Convertir timestamp
    log_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    log_timestamp = log_time.timestamp()
```

### 3. Detección de Cambios Específicos
```python
# 1. DETECTAR CAMBIOS EN COLUMNA DE FECHA
if event == 'change_column_value' and data:
    # Analizar data para identificar columna
    # Si es fecha56, agregar a fecha_changes

# 2. DETECTAR CAMBIOS DE AUTOMATIZACIÓN
is_automation = (
    str(user_id) == str(config.AUTOMATION_USER_ID) or 
    user_name == config.AUTOMATION_USER_NAME
)
```

### 4. Análisis de Resultados
```python
# 3. ANÁLISIS DE DETECCIÓN DE AUTOMATIZACIÓN
# Verificar cambios recientes de automatización

# 4. DETECCIÓN DE BUCLE
# Verificar cambios repetitivos en 30 segundos

# 5. DETECCIÓN ESPECÍFICA DE CAMBIO DE FECHA POR AUTOMATIZACIÓN
# Verificar último cambio de fecha por automatización
```

## Casos de Uso

### Caso 1: Cambio Reciente de Automatización
```
🔍 Analizando 8 activity_logs para item 123456789
📝 Activity: change_column_value - Arnau Admin (34210704) - 2024-01-15T10:30:45Z
🤖 Cambio de automatización detectado: change_column_value
🤖 Cambio de automatización detectado, ignorando para evitar bucle
```

### Caso 2: Bucle Detectado
```
🔍 Analizando 10 activity_logs para item 123456789
📅 Cambio detectado en columna de fecha por Arnau Admin
📅 Cambio detectado en columna de fecha por Arnau Admin
🔄 BUCLE DETECTADO: 2 cambios de fecha por automatización en 30s
🛑 Deteniendo sincronización para evitar bucle infinito
```

### Caso 3: Usuario Real
```
🔍 Analizando 5 activity_logs para item 123456789
📝 Activity: change_column_value - Juan Pérez (12345) - 2024-01-15T10:25:30Z
👤 Último cambio fue de usuario REAL, no automatización
```

## Configuración Requerida

### Variables en config.py
```python
# Usuario de automatización
AUTOMATION_USER_NAME = "Arnau Admin"
AUTOMATION_USER_ID = 34210704

# Columna de fecha
COL_FECHA_GRAB = "fecha56"
COL_FECHA = COL_FECHA_GRAB
```

### Verificación de Configuración
```python
# Verificar que las variables estén configuradas
if not hasattr(config, 'AUTOMATION_USER_ID') or not config.AUTOMATION_USER_ID:
    print("❌ Error: AUTOMATION_USER_ID no está configurado")
    return False

if not hasattr(config, 'COL_FECHA') or not config.COL_FECHA:
    print("❌ Error: COL_FECHA no está configurado")
    return False
```

## Integración con el Sistema

### Uso en sincronizar_item_via_webhook()
```python
def sincronizar_item_via_webhook(item_id, monday_handler, google_service=None, change_uuid: str = None):
    # ... código existente ...
    
    # Detectar si el último cambio fue de automatización
    es_automatizacion = _detectar_cambio_de_automatizacion(item_id, monday_handler)
    
    if es_automatizacion:
        print(f"🛑 El último cambio fue hecho por la cuenta de automatización ({config.AUTOMATION_USER_NAME})")
        print(f"🛑 Saltando sincronización para evitar bucle")
        return True
    
    # ... continuar con sincronización ...
```

### Logs de Detección
```
🔍 Analizando 6 activity_logs para item 123456789
📝 Activity: change_column_value - Arnau Admin (34210704) - 2024-01-15T10:30:45Z
📅 Cambio detectado en columna de fecha por Arnau Admin
🤖 Cambio de automatización detectado: change_column_value
🤖 Cambio de automatización detectado, ignorando para evitar bucle
```

## Ventajas del Sistema Mejorado

### 1. Precisión Mejorada
- ✅ **Activity_logs vs Updates**: Más preciso y confiable
- ✅ **Detección específica**: Identifica cambios en columnas específicas
- ✅ **Timestamps exactos**: Usa timestamps reales de Monday.com
- ✅ **Información completa**: Incluye datos del cambio y usuario

### 2. Prevención de Bucles
- ✅ **Detección temprana**: Identifica bucles antes de que se propaguen
- ✅ **Múltiples criterios**: Verifica usuario, columna y tiempo
- ✅ **Bloqueo automático**: Detiene sincronización inmediatamente
- ✅ **Logs detallados**: Registra todos los eventos para debugging

### 3. Flexibilidad
- ✅ **Configurable**: Fácil ajuste de thresholds y criterios
- ✅ **Extensible**: Fácil agregar nuevas columnas o criterios
- ✅ **Robusto**: Manejo de errores y casos edge
- ✅ **Compatible**: No rompe funcionalidad existente

### 4. Rendimiento
- ✅ **Eficiente**: Solo analiza los últimos 10 logs
- ✅ **Rápido**: Detección en milisegundos
- ✅ **Optimizado**: Usa queries GraphQL eficientes
- ✅ **Caché-friendly**: Compatible con sistema de caché

## Troubleshooting

### Problema: No Detecta Automatización
**Solución**:
1. Verificar `AUTOMATION_USER_ID` y `AUTOMATION_USER_NAME` en config.py
2. Confirmar que el usuario de automatización existe en Monday.com
3. Verificar que los activity_logs están disponibles para el item

### Problema: Falsos Positivos
**Solución**:
1. Ajustar el threshold de tiempo (actualmente 10 segundos)
2. Verificar que `COL_FECHA` apunta a la columna correcta
3. Revisar logs para identificar patrones incorrectos

### Problema: No Detecta Bucles
**Solución**:
1. Verificar que hay suficientes activity_logs (mínimo 2)
2. Confirmar que los cambios son en la misma columna
3. Ajustar el threshold de tiempo para bucles (actualmente 30 segundos)

### Problema: Errores en Query
**Solución**:
1. Verificar permisos de API en Monday.com
2. Confirmar que el item_id es válido
3. Revisar logs de error para detalles específicos

## Pruebas

### Script de Pruebas
```bash
python3 scripts/testing/test_detection_automatizacion.py
```

### Casos de Prueba
1. **Prueba básica**: Item con ID ficticio
2. **Prueba con item real**: Item existente del tablero
3. **Prueba de query**: Verificación directa de activity_logs
4. **Prueba múltiple**: Varios items para consistencia
5. **Prueba de errores**: Manejo de casos edge

### Resultados Esperados
```
🚀 Iniciando pruebas de detección de automatización mejorada...

✅ Configuración verificada:
   - Usuario automatización: Arnau Admin (ID: 34210704)
   - Columna fecha: fecha56
   - Board ID: 123456789

=== Prueba de Query Activity Logs ===
✅ Query exitosa - 5 activity_logs encontrados

=== Prueba con Item Real ===
🔍 Probando con item real: Reunión Cliente (ID: 987654321)
📊 Tiempo de detección: 0.234s
📊 Resultado: Usuario Real

🎉 ¡Pruebas de detección de automatización completadas!
```

## Conclusión

El sistema mejorado de detección de automatización proporciona:

- ✅ **Detección precisa**: Basada en activity_logs reales
- ✅ **Prevención de bucles**: Múltiples niveles de verificación
- ✅ **Rendimiento optimizado**: Análisis rápido y eficiente
- ✅ **Logs detallados**: Para debugging y monitoreo
- ✅ **Configuración flexible**: Fácil ajuste de parámetros
- ✅ **Integración transparente**: Compatible con sistema existente

Este sistema es fundamental para evitar bucles infinitos de sincronización y mantener la estabilidad del sistema de integración Monday.com ↔ Google Calendar.
