# Scripts del Sistema

Esta carpeta contiene todos los scripts auxiliares del sistema de sincronización, organizados por categorías.

## Estructura

```
scripts/
├── README.md                    # Este archivo
├── testing/                     # Scripts de testing y configuración
│   ├── configurar_*.py         # Scripts para configurar webhooks
│   ├── probar_*.py             # Scripts para probar funcionalidades
│   ├── test_*.py               # Scripts de testing automatizado
│   ├── verificar_*.py          # Scripts para verificar estados
│   ├── monitor_*.py            # Scripts de monitoreo
│   ├── simular_*.py            # Scripts para simular webhooks
│   ├── crear_*.py              # Scripts para crear elementos de prueba
│   ├── forzar_*.py             # Scripts para forzar sincronizaciones
│   ├── buscar_*.py             # Scripts para buscar elementos
│   ├── listar_*.py             # Scripts para listar elementos
│   ├── limpiar_*.py            # Scripts para limpiar configuraciones
│   └── actualizar_*.py         # Scripts para actualizar configuraciones
├── legacy/                      # Scripts obsoletos o versiones anteriores
│   ├── autorizar_google.py     # Autorización de Google (versión anterior)
│   ├── init_google_notifications.py # Inicialización de notificaciones
│   ├── fix_master_event_id.py  # Corrección de IDs de eventos maestros
│   ├── migrate_existing_events.py # Migración de eventos existentes
│   └── prueba_completa_sistema.py # Pruebas completas del sistema
└── utilities/                   # Scripts de utilidades generales
    ├── webhook_channel_mapper.py # Mapeo de canales de webhooks
    └── update_paths.py          # Actualización de rutas (usado en reorganización)
```

## Categorías

### `testing/`
Scripts para testing, configuración y verificación del sistema:
- **Configuración**: Scripts para configurar webhooks de Monday.com y Google Calendar
- **Testing**: Scripts para probar funcionalidades específicas
- **Verificación**: Scripts para verificar el estado de elementos
- **Monitoreo**: Scripts para monitorear logs y actividad
- **Simulación**: Scripts para simular webhooks y eventos
- **Creación**: Scripts para crear elementos de prueba
- **Forzado**: Scripts para forzar sincronizaciones
- **Búsqueda**: Scripts para buscar elementos específicos
- **Limpieza**: Scripts para limpiar configuraciones obsoletas

### `legacy/`
Scripts obsoletos o versiones anteriores que se mantienen por referencia:
- Versiones anteriores de autorización
- Scripts de migración ya ejecutados
- Pruebas completas del sistema (versiones anteriores)
- Scripts de inicialización obsoletos

### `utilities/`
Scripts de utilidades generales:
- **webhook_channel_mapper.py**: Herramienta para mapear canales de webhooks
- **update_paths.py**: Script usado durante la reorganización del proyecto

## Uso

### Scripts de Testing
```bash
# Configurar webhooks
python3 scripts/testing/configurar_webhooks.py

# Probar sincronización
python3 scripts/testing/probar_sincronizacion_optimizada.py

# Verificar estado
python3 scripts/testing/verificar_estado_simple.py
```

### Scripts de Utilidades
```bash
# Mapear canales
python3 scripts/utilities/webhook_channel_mapper.py

# Actualizar rutas (solo durante reorganización)
python3 scripts/utilities/update_paths.py
```

## Mantenimiento

- Los scripts en `testing/` están activos y se usan regularmente
- Los scripts en `legacy/` son de referencia y no se ejecutan
- Los scripts en `utilities/` son herramientas auxiliares
- Todos los scripts mantienen las rutas actualizadas después de la reorganización
