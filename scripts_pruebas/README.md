# 📁 Scripts de Pruebas y Debugging

Esta carpeta contiene todos los scripts de prueba, debugging y herramientas auxiliares del proyecto de sincronización Monday ↔ Google Calendar.

## 🧪 Scripts de Pruebas

### **test_simple_completo.py**
Suite completa de pruebas con 5 escenarios:
- PRUEBA 1: Monday → Google
- PRUEBA 2: Google Personal → Monday
- PRUEBA 3: Google Máster → Monday
- PRUEBA 4: Añadir Filmmaker
- PRUEBA 5: Quitar Filmmaker

### **test_prueba_2.py**
Prueba específica de sincronización inversa (Google Personal → Monday)

### **test_sync_flow.py**
Script de prueba del flujo de sincronización básico

### **test_completo_sincronizacion.py**
Versión anterior de la suite de pruebas (mantenida por compatibilidad)

### **test_google_id_save.py**
Script para probar el guardado de IDs de Google en Monday

### **test_monday_query.py**
Script para probar queries de Monday.com

## 🔧 Scripts de Debugging

### **debug_actualizar_fecha.py**
Debugging de la actualización de fechas en Monday

### **debug_test.py**
Script de debugging general

### **debug_monday_query.py**
Debugging de queries de Monday.com

### **check_monday_items.py**
Verificación de items en Monday.com

### **get_user_id.py**
Herramienta para obtener IDs de usuarios de Monday

## 🧹 Scripts de Limpieza

### **cleanup_test_state.py**
Limpieza del estado de pruebas

### **cleanup_google_calendars.py**
Limpieza de calendarios de Google

## 📚 Documentación

### **TESTING_README.md**
Documentación completa de las pruebas del sistema

## 🚀 Uso

Para ejecutar las pruebas principales:

```bash
# Desde la raíz del proyecto
python scripts_pruebas/test_simple_completo.py

# O desde esta carpeta
cd scripts_pruebas
python test_simple_completo.py
```

## ⚠️ Nota

Estos scripts son para **pruebas y debugging**. No modificar archivos críticos del sistema sin revisión manual.

---

**Estado**: Scripts organizados y funcionales
**Última actualización**: Sistema v3.0 optimizado 