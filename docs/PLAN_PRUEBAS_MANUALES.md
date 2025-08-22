# 🧪 Plan de Pruebas Manuales - Sincronización Bidireccional

## 📋 Objetivo
Verificar que la sincronización Monday ↔ Google Calendar funciona correctamente en ambas direcciones, incluyendo el sistema anti-bucles.

## ⚠️ Requisitos Previos
1. **Servidor funcionando**: `python3 app.py` (puerto 6754)
2. **ngrok activo**: `ngrok http 6754` (para webhooks)
3. **Credenciales configuradas**: `.env` con API keys válidas
4. **Cuenta de prueba**: Una cuenta diferente a "Arnau Admin" para hacer cambios

## 🎯 Pruebas a Realizar

### PRUEBA 1: Monday → Google (Crear Evento Nuevo)
**Objetivo**: Verificar que al crear un evento en Monday, se crea automáticamente en Google Calendar.

**Pasos**:
1. **Abrir Monday.com** en una cuenta diferente a "Arnau Admin"
2. **Ir al tablero "Grabaciones"** (ID: 3324095194)
3. **Crear un nuevo item** con:
   - Nombre: "PRUEBA MANUAL 1 - Monday → Google"
   - Fecha: Mañana a las 10:00
   - Operario: Asignar a cualquier filmmaker (ej: "Jordi Vas")
   - Cliente: "Cliente de Prueba"
4. **Guardar el item**
5. **Verificar en Google Calendar**:
   - Buscar el evento "PRUEBA MANUAL 1 - Monday → Google"
   - Confirmar que aparece en el calendario maestro
   - Confirmar que aparece en el calendario personal del filmmaker asignado

**Resultado esperado**: ✅ Evento creado en ambos lados

---

### PRUEBA 2: Monday → Google (Modificar Fecha)
**Objetivo**: Verificar que al cambiar la fecha en Monday, se actualiza en Google.

**Pasos**:
1. **Usar el evento creado en Prueba 1**
2. **En Monday.com** (con cuenta diferente a Arnau Admin):
   - Cambiar la fecha a 2 días después
   - Cambiar la hora a las 15:00
3. **Verificar en Google Calendar**:
   - El evento debe actualizarse automáticamente
   - Tanto en calendario maestro como en calendario personal

**Resultado esperado**: ✅ Fecha actualizada en ambos lados

---

### PRUEBA 3: Google → Monday (Mover Evento)
**Objetivo**: Verificar que al mover un evento en Google, se actualiza en Monday.

**Pasos**:
1. **Usar el evento de la Prueba 2**
2. **En Google Calendar** (con cuenta diferente a Arnau Admin):
   - Ir al calendario maestro
   - Buscar "PRUEBA MANUAL 1 - Monday → Google"
   - **Arrastrar el evento** a una fecha diferente (ej: 3 días después)
   - **Cambiar la hora** a las 14:00
3. **Verificar en Monday.com**:
   - La fecha debe actualizarse automáticamente
   - La hora debe actualizarse automáticamente

**Resultado esperado**: ✅ Fecha actualizada en Monday

---

### PRUEBA 4: Google → Monday (Calendario Personal)
**Objetivo**: Verificar que al mover un evento en el calendario personal, se propaga.

**Pasos**:
1. **Usar el evento de la Prueba 3**
2. **En Google Calendar** (con cuenta diferente a Arnau Admin):
   - Ir al calendario personal del filmmaker asignado
   - Buscar "PRUEBA MANUAL 1 - Monday → Google"
   - **Arrastrar el evento** a una fecha diferente
   - **Cambiar la hora** a las 16:00
3. **Verificar en Monday.com**:
   - La fecha debe actualizarse automáticamente
4. **Verificar en Google Calendar**:
   - El evento maestro también debe actualizarse
   - Las copias en otros calendarios deben actualizarse

**Resultado esperado**: ✅ Cambios propagados a Monday y otros calendarios

---

### PRUEBA 5: Sistema Anti-Bucles
**Objetivo**: Verificar que el sistema detecta automatización y evita bucles.

**Pasos**:
1. **Usar el evento de la Prueba 4**
2. **En Monday.com** (con cuenta "Arnau Admin" - tu cuenta):
   - Cambiar la fecha del evento
   - Guardar
3. **Verificar en Google Calendar**:
   - El evento NO debe cambiar (porque detecta automatización)
4. **En Google Calendar** (con cuenta diferente):
   - Mover el evento a otra fecha
5. **Verificar en Monday.com**:
   - La fecha SÍ debe actualizarse (porque es cambio de usuario real)

**Resultado esperado**: ✅ Cambios de Arnau Admin ignorados, cambios de usuario real propagados

---

### PRUEBA 6: Cambiar Operario
**Objetivo**: Verificar que al cambiar el operario, se gestionan las copias correctamente.

**Pasos**:
1. **Usar el evento de la Prueba 5**
2. **En Monday.com** (con cuenta diferente a Arnau Admin):
   - Cambiar el operario asignado a otro filmmaker
   - Guardar
3. **Verificar en Google Calendar**:
   - El evento debe desaparecer del calendario del operario anterior
   - El evento debe aparecer en el calendario del nuevo operario
   - El evento maestro debe mantenerse

**Resultado esperado**: ✅ Copias gestionadas correctamente

---

### PRUEBA 7: Rendimiento y Velocidad
**Objetivo**: Verificar que las búsquedas optimizadas funcionan rápido.

**Pasos**:
1. **Crear 5 eventos nuevos** en Monday con nombres únicos
2. **Medir el tiempo** de sincronización para cada uno
3. **Verificar en los logs** que aparece "Búsqueda SÚPER OPTIMIZADA"

**Resultado esperado**: ✅ Sincronización rápida (< 10 segundos por evento)

---

## 🔍 Qué Observar Durante las Pruebas

### En la Terminal (Logs del Servidor)
```
✅ Evento maestro creado y guardado exitosamente
🔄 Sincronizando copias para filmmakers...
✅ Copia creada exitosamente
🤖 ¡CAMBIO DE AUTOMATIZACIÓN DETECTADO!
🛑 FRENANDO SINCRONIZACIÓN para evitar bucle infinito
```

### En Monday.com
- Fechas actualizándose automáticamente
- Columna "ID Evento Google" poblándose
- Operarios asignándose correctamente

### En Google Calendar
- Eventos apareciendo en calendarios correctos
- Fechas sincronizándose
- Descripciones con información completa

## 🚨 Posibles Problemas y Soluciones

### Problema: Evento no aparece en Google
**Causa**: Error en webhook o configuración
**Solución**: 
- Verificar logs del servidor
- Comprobar que ngrok está activo
- Verificar API keys en `.env`

### Problema: Cambios no se propagan
**Causa**: Sistema anti-bucles activado incorrectamente
**Solución**:
- Verificar que usas cuenta diferente a "Arnau Admin"
- Revisar logs para ver si detecta automatización

### Problema: Sincronización lenta
**Causa**: Búsqueda no optimizada
**Solución**:
- Verificar que aparece "Búsqueda SÚPER OPTIMIZADA" en logs
- Comprobar que el evento tiene nombre único

## 📊 Criterios de Éxito

✅ **Sincronización Monday → Google**: Eventos se crean/actualizan en Google
✅ **Sincronización Google → Monday**: Fechas se actualizan en Monday
✅ **Sistema Anti-Bucles**: Cambios de Arnau Admin se ignoran
✅ **Gestión de Copias**: Copias se crean/eliminan correctamente
✅ **Rendimiento**: Sincronización < 10 segundos por evento
✅ **Búsqueda Optimizada**: Logs muestran "SÚPER OPTIMIZADA"

## 🎯 Próximos Pasos

1. **Ejecutar todas las pruebas** en orden
2. **Documentar resultados** en cada prueba
3. **Reportar problemas** encontrados
4. **Ajustar configuración** si es necesario
5. **Validar en producción** una vez que todo funcione

---

**¿Listo para empezar las pruebas?** 🚀
