# Sincro Monday Calendar - Sistema de Sincronización Inteligente

Sistema avanzado de sincronización bidireccional entre Monday.com y Google Calendar con arquitectura "Master-Copia" para gestión de múltiples filmmakers.

## 🎯 Descripción General

Este proyecto implementa un sistema de sincronización inteligente que mantiene perfectamente sincronizados los eventos de Monday.com con Google Calendar, utilizando una arquitectura "Master-Copia" que permite asignar eventos a múltiples filmmakers sin conflictos.

### Características Principales

- ✅ **Arquitectura Master-Copia**: Un evento maestro central + copias automáticas para cada filmmaker
- ✅ **Sincronización Bidireccional**: Monday ↔ Google Calendar
- ✅ **Webhooks Automáticos**: Respuesta inmediata a cambios en Monday.com
- ✅ **Gestión Multi-Filmmaker**: Soporte para múltiples operarios por evento
- ✅ **Limpieza Automática**: Eliminación de copias obsoletas
- ✅ **Eventos Sin Asignar**: Gestión de eventos sin operario específico

## 🏗️ Arquitectura del Sistema

### Arquitectura "Master-Copia"

```
Monday.com Item
    ↓
Evento Maestro (Calendario Central)
    ↓
Copias Automáticas (Calendarios Personales)
```

#### Componentes:

1. **Evento Maestro**: 
   - Ubicado en `config.MASTER_CALENDAR_ID`
   - Contiene toda la información del evento
   - Incluye link directo a Monday.com
   - Es la "fuente única de verdad"

2. **Copias de Filmmakers**:
   - Una copia por cada filmmaker asignado
   - Ubicadas en calendarios personales de cada filmmaker
   - Vinculadas al evento maestro mediante `extended_properties`
   - Se crean/actualizan/eliminan automáticamente

3. **Eventos Sin Asignar**:
   - Ubicados en `config.UNASSIGNED_CALENDAR_ID`
   - Para eventos sin operario específico
   - No son parte de la arquitectura Master-Copia

## 🔄 Flujo de Trabajo Completo

### 1. Trigger: Webhook de Monday.com
```
Monday.com → POST /monday-webhook → item_id
```

### 2. Procesamiento del Item
```python
# Obtener datos completos de Monday
item_completo = get_single_item_details(item_id)
item_procesado = parse_monday_item(item_completo)
```

### 3. Decisión de Ruta

#### 3A. Items Sin Operarios
```python
if not operario_ids:
    # → Calendario UNASSIGNED_CALENDAR_ID
    # → NO es parte de Master-Copia
```

#### 3B. Items Con Operarios
```python
# → Arquitectura Master-Copia
```

### 4. Sincronización del Evento Maestro
```python
# Siempre usar MASTER_CALENDAR_ID
if google_event_id:
    update_google_event(MASTER_CALENDAR_ID, item_data)
else:
    new_event_id = create_google_event(MASTER_CALENDAR_ID, item_data)
    # Guardar ID en Monday
    update_monday_column(item_id, COL_GOOGLE_EVENT_ID, new_event_id)
```

### 5. Creación/Actualización de Copias
```python
for filmmaker in operarios_asignados:
    existing_copy = find_event_copy_by_master_id(calendar_id, master_event_id)
    
    if not existing_copy:
        # Crear nueva copia
        create_google_event(calendar_id, item_data, extended_props)
    else:
        # Actualizar copia existente
        update_google_event_by_id(calendar_id, copy_id, item_data)
```

### 6. Limpieza de Copias Obsoletas
```python
# Encontrar copias anteriores
operarios_con_copia_anterior = buscar_copias_existentes()

# Calcular diferencias
calendarios_a_limpiar = operarios_con_copia_anterior - operarios_actuales

# Eliminar copias obsoletas
for calendar_id in calendarios_a_limpiar:
    delete_event_by_id(calendar_id, copy_id)
```

## 📋 Configuración del Sistema

### 1. Variables de Entorno Requeridas

```bash
# Monday.com API
MONDAY_API_KEY=your_monday_api_key

# Google Calendar (generado automáticamente)
GOOGLE_TOKEN_JSON={"token_type": "Bearer", "access_token": "...", ...}
```

### 2. Configuración de Calendarios

```python
# config.py
MASTER_CALENDAR_ID = "c_4db25ae132f391943ecad1b9ef49076a143d88739b7ad7c4378db60c070abf39@group.calendar.google.com"
UNASSIGNED_CALENDAR_ID = "c_52a614880d3306538360d3a8353dc3aec730ca6bafef182fdf956af03e900657@group.calendar.google.com"
```

### 3. Perfiles de Filmmakers

```python
FILMMAKER_PROFILES = [
    {
        "monday_name": "Arnau Admin",
        "personal_email": "seonrtn@gmail.com",
        "calendar_id": "c_59e3a26fba95603b4d085cc0c672573d52c1fd98d4b1e96b08b846c8be800c1a@group.calendar.google.com",
        "monday_user_id": None  # Se resuelve automáticamente
    },
    # ... más perfiles
]
```

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciales
```bash
# Crear archivo .env con:
MONDAY_API_KEY=tu_api_key_de_monday
```

### 3. Autorizar Google Calendar
```bash
python autorizar_google.py
```

### 4. Iniciar Servidor Webhook
```bash
python app.py
```

## 🔧 Funcionalidades del Sistema

### Sincronización Automática
- **Webhooks de Monday**: Respuesta inmediata a cambios
- **Webhooks de Google**: Sincronización inversa (Google → Monday)
- **Upsert Inteligente**: Crear/actualizar según estado actual

### Gestión de Múltiples Filmmakers
- **Asignación Dinámica**: Soporte para 1, 3, 10+ filmmakers por evento
- **Vinculación Inteligente**: Cada copia tiene referencia al evento maestro
- **Limpieza Automática**: Eliminación de copias cuando se desasigna filmmaker

### Eventos Detallados
- **Información Completa**: Cliente, grupo, estado de permisos, acciones
- **Contactos Formateados**: Obra y comerciales con teléfonos
- **Enlaces Directos**: Link a Monday.com y Dropbox
- **Updates del Item**: Historial de actualizaciones

## ⚠️ Posibles Fallos y Soluciones

### 1. Error de Credenciales Google
```
❌ GOOGLE_TOKEN_JSON no encontrado
```
**Solución**: Ejecutar `python autorizar_google.py`

### 2. Filmmaker No Encontrado
```
❌ No se encontró perfil para el operario 'Nombre'
```
**Solución**: Añadir perfil en `config.FILMMAKER_PROFILES`

### 3. Calendario No Configurado
```
❌ El perfil necesita un calendario. Creando ahora...
```
**Solución**: El sistema crea automáticamente el calendario

### 4. Error de API Monday
```
❌ Error al obtener detalles del item
```
**Solución**: Verificar `MONDAY_API_KEY` y permisos

### 5. Copias No Sincronizadas
```
❌ Error al crear copia para calendario
```
**Solución**: Verificar permisos de escritura en calendarios de filmmakers

## 🔄 Acciones Manuales Ocasionales

### 1. Añadir Nuevo Filmmaker
1. Añadir perfil en `config.FILMMAKER_PROFILES`
2. El sistema creará automáticamente su calendario
3. No requiere reinicio del servidor

### 2. Cambiar Calendario Maestro
1. Actualizar `MASTER_CALENDAR_ID` en `config.py`
2. Los eventos existentes mantendrán su ID en Monday
3. Las copias se recrearán automáticamente

### 3. Limpiar Eventos Obsoletos
```python
# Función disponible para limpieza manual
delete_event_by_id(service, calendar_id, event_id)
```

### 4. Regenerar Credenciales Google
```bash
# Eliminar GOOGLE_TOKEN_JSON del .env
# Ejecutar:
python autorizar_google.py
```

## 📊 Monitoreo y Logs

### Logs del Sistema
```
✅ Servicios inicializados.
🔄 Iniciando sincronización de copias para filmmakers...
  -> Filmmakers asignados: 3 calendarios
  -> [ACCIÓN] Creando copia para el filmmaker...
  ✅ Copia creada exitosamente
🧹 Iniciando limpieza de copias obsoletas...
  -> [ACCIÓN] Eliminando copia obsoleta...
  ✅ Copia eliminada exitosamente
```

### Endpoints de Monitoreo
- `GET /`: Estado del servidor
- `POST /monday-webhook`: Webhook de Monday.com
- `POST /google-webhook`: Webhook de Google Calendar

## 🛠️ Estructura del Proyecto

```
sincro-monday-calendar/
├── app.py                    # Servidor Flask con webhooks
├── sync_logic.py            # Lógica principal de sincronización
├── google_calendar_service.py # Servicios de Google Calendar
├── monday_service.py        # Servicios de Monday.com
├── config.py               # Configuración centralizada
├── autorizar_google.py     # Script de autorización Google
├── requirements.txt        # Dependencias Python
└── README.md              # Este archivo
```

## 🔗 Integración con Monday.com

### Configuración de Webhook
1. En Monday.com, ir a Integrations → Webhooks
2. URL: `https://tu-dominio.com/monday-webhook`
3. Eventos: Item Created, Item Updated, Item Deleted

### Columnas Requeridas
- **Operario**: Columna de personas (personas1)
- **Fecha Grab**: Columna de fecha (fecha56)
- **ID Evento Google**: Columna de texto (text_mktfdhm3)
- **Cliente**: Columna de texto (text_mktefg5)
- **Link Dropbox**: Columna de link (link_mktcbghq)
- **Contactos**: Columnas de lookup (lookup_mkteg56h, etc.)

## 🎯 Casos de Uso

### Escenario 1: Asignación Única
- Item asignado a 1 filmmaker
- Se crea evento maestro + 1 copia
- Monday guarda ID del evento maestro

### Escenario 2: Asignación Múltiple
- Item asignado a 3 filmmakers
- Se crea evento maestro + 3 copias
- Cada copia tiene referencia al maestro
- Monday guarda solo ID del evento maestro

### Escenario 3: Cambio de Asignación
- Item cambia de Arnau → Jordi
- Se actualiza evento maestro
- Se crea copia para Jordi
- Se elimina copia de Arnau

### Escenario 4: Evento Sin Asignar
- Item sin operario específico
- Se crea en calendario UNASSIGNED
- No es parte de arquitectura Master-Copia

## 🚀 Tecnologías Utilizadas

- **Python 3.x**: Lógica principal
- **Flask**: Servidor webhook
- **Google Calendar API**: Gestión de calendarios
- **Monday.com GraphQL API**: Integración con Monday
- **Requests**: Cliente HTTP
- **Google Auth**: Autenticación OAuth2

---

**Desarrollado para Stupendastic** - Sistema de sincronización inteligente para gestión de proyectos audiovisuales. 