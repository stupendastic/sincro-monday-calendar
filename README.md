# Sincro Monday Calendar

Proyecto para sincronización de eventos entre Monday.com y Google Calendar.

## Descripción

Este proyecto permite sincronizar automáticamente eventos de Monday.com con Google Calendar, creando eventos detallados con toda la información relevante del proyecto.

## Configuración

1. **Instalar dependencias Python:**
```bash
pip install -r requirements.txt
```

2. **Configurar credenciales:**
   - Crear archivo `credentials.json` con las credenciales de Google API
   - Configurar `MONDAY_API_KEY` en variables de entorno

3. **Autorizar Google Calendar:**
```bash
python autorizar_google.py
```

4. **Ejecutar sincronización:**
```bash
python main.py
```

## Estructura del Proyecto

- `main.py` - Script principal de sincronización
- `config.py` - Configuración de IDs y perfiles
- `google_calendar_service.py` - Servicios de Google Calendar
- `autorizar_google.py` - Script de autorización de Google
- `requirements.txt` - Dependencias Python

## Funcionalidades

- ✅ Sincronización automática de eventos
- ✅ Filtrado por operario y fecha
- ✅ Creación/actualización de eventos (upsert)
- ✅ Paginación para manejar grandes volúmenes de datos
- ✅ Optimización de consultas API (estrategia de dos pasos)
- ✅ Formato detallado de eventos con contactos y enlaces

## Regla de Oro para Fechas en Monday.com API

### El Problema
La API de Monday.com es muy específica sobre cómo manejar las columnas de tipo "Fecha". Después de extensa investigación, hemos descubierto la regla de oro.

### La Solución

#### 1. Formato del Objeto
Cuando quieras establecer o actualizar una columna de fecha que incluye una hora, siempre debes proporcionar un objeto JavaScript con dos claves: `date` y `time`.

```javascript
const dateValue = {
  date: "YYYY-MM-DD", // El día, mes y año
  time: "HH:MM:SS"    // La hora, minutos y segundos
};
```

**Formato de fecha:** Debe ser un string en formato `YYYY-MM-DD`
**Formato de hora:** Debe ser un string en formato `HH:MM:SS` (formato de 24 horas)

#### 2. El "Doble Stringify"
Aquí está el truco que nos ha costado tanto descubrir. Cuando construyes la mutation de GraphQL, Monday no quiere recibir el objeto directamente. Quiere recibir un string que contenga un string JSON.

Esto se logra con un doble `JSON.stringify`:

```javascript
// Primer JSON.stringify
'{"date0":{"date":"2025-08-10","time":"14:30:00"},"status":{"index":4}}'

// Segundo JSON.stringify (formato final que la API espera)
'"{\\"date0\\":{\\"date\\":\\"2025-08-10\\",\\"time\\":\\"14:30:00\\"},\\"status\\":{\\"index\\":4}}"'
```

#### 3. Implementación en Python
```python
# Crear el objeto de fecha
date_object = {"date": "2025-08-10", "time": "14:30:00"}

# Crear el objeto column_values principal
column_values = {column_id: date_object}

# Aplicar doble JSON.stringify
value_string = json.dumps(json.dumps(column_values))
```

### Resumen de la Regla de Oro
Para actualizar una columna de Fecha y Hora en Monday a través de la API:
1. Crea un objeto JS `{ date: "YYYY-MM-DD", time: "HH:MM:SS" }`
2. Insértalo en el objeto `column_values` principal
3. Aplica `JSON.stringify()` dos veces a ese objeto `column_values`
4. Inyecta el resultado en tu mutation de GraphQL

### Función Implementada
El proyecto incluye la función `update_monday_date_column()` que implementa esta regla de oro automáticamente.

## Tecnologías

- Python 3.x
- Google Calendar API
- Monday.com GraphQL API
- Requests (HTTP client)
- Google Auth libraries 