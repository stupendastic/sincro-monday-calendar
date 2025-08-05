# 🧪 Scripts de Pruebas de Sincronización

Este directorio contiene scripts para probar y depurar el flujo de sincronización entre Monday.com y Google Calendar de forma aislada, sin depender de webhooks.

## 📁 Archivos de Pruebas

### `test_sync_flow.py`
Script principal de pruebas que simula los flujos de sincronización:
- **Monday → Google**: Simula la sincronización cuando se cambia un item en Monday
- **Google → Monday**: Simula la sincronización cuando se cambia un evento en Google Calendar

### `cleanup_test_state.py`
Script de limpieza para preparar el estado antes de las pruebas:
- Limpia el Google Event ID del item de prueba en Monday
- Elimina eventos relacionados de Google Calendar
- Prepara el estado para pruebas limpias

## 🎯 Item de Prueba

**ID del item de prueba**: `9733398727`

Este item debe tener:
- ✅ Operario asignado
- ✅ Fecha asignada
- ✅ Estar en el tablero de grabaciones

## 🚀 Cómo Usar los Scripts

### 1. Preparar el Estado (Opcional)
Si quieres empezar con un estado completamente limpio:

```bash
python3 cleanup_test_state.py
```

### 2. Ejecutar las Pruebas
```bash
python3 test_sync_flow.py
```

## 📋 Flujo de Pruebas

### PRUEBA 1: Monday → Google
1. **Limpieza inicial**: Borra el Google Event ID del item y eventos relacionados
2. **Sincronización**: Llama a `sincronizar_item_via_webhook()`
3. **Verificación**: Confirma que se creó el evento maestro y las copias

### PRUEBA 2: Google → Monday
1. **Obtención del ID**: Lee el Google Event ID generado en la PRUEBA 1
2. **Sincronización**: Llama a `sincronizar_desde_google()`
3. **Verificación**: Confirma que se propagaron los cambios

## 🔒 Seguridad

### ✅ Lo que SÍ se modifica:
- **Monday**: Solo la columna de Google Event ID (se limpia y se actualiza)
- **Google Calendar**: Se eliminan eventos relacionados con el item de prueba

### ❌ Lo que NO se modifica:
- **Monday**: No se borra ni modifica ningún otro dato del item
- **Google Calendar**: No se tocan eventos no relacionados con el item de prueba

## 📊 Logs y Debugging

Los scripts proporcionan logs detallados:
- 🔍 **Verificación**: Confirma que el item existe y es válido
- 🧹 **Limpieza**: Muestra qué se está limpiando
- 🔄 **Sincronización**: Detalla cada paso del proceso
- ✅ **Resultados**: Confirma el éxito o fallo de cada prueba

## ⚠️ Importante

1. **No invasivo**: Los scripts solo modifican el item de prueba específico
2. **Limpieza automática**: Se limpia el estado antes y después de las pruebas
3. **Logs claros**: Cada paso se documenta con emojis y mensajes descriptivos
4. **Seguridad**: Nunca se borra nada de Monday más allá del Google Event ID

## 🛠️ Personalización

Para cambiar el item de prueba, modifica la constante en ambos scripts:
```python
ITEM_DE_PRUEBA_ID = 9733398727  # Cambiar por tu ID
```

## 🎯 Casos de Uso

- **Debugging**: Identificar problemas en el flujo de sincronización
- **Testing**: Verificar que los cambios funcionan correctamente
- **Desarrollo**: Probar nuevas funcionalidades de forma aislada
- **Validación**: Confirmar que los webhooks funcionarían correctamente

## 📝 Notas Técnicas

- Los scripts usan las mismas funciones que los webhooks reales
- Se inicializan los servicios de la misma forma que en `app.py`
- Se respetan todas las reglas de negocio y validaciones
- Los logs son idénticos a los que verías en producción 