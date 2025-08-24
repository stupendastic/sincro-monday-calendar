#!/usr/bin/env python3
"""
Ejemplo de integración del SyncStateManager con el sistema de sincronización.
Este script muestra cómo usar el gestor de estado para optimizar las operaciones
de sincronización entre Monday.com y Google Calendar.
"""

import sys
import json
import time
from pathlib import Path

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from sync_state_manager import SyncStateManager, get_sync_state, update_sync_state, is_change_needed


def simular_contenido_monday(item_id: str) -> dict:
    """
    Simula el contenido de un item de Monday.com.
    En la implementación real, esto vendría de la API de Monday.
    """
    return {
        "name": f"Reunión {item_id}",
        "date": {"date": "2024-01-15"},
        "status": {"label": "Working on it"},
        "priority": {"label": "High"},
        "last_updated": time.time()
    }


def simular_contenido_google(event_id: str) -> dict:
    """
    Simula el contenido de un evento de Google Calendar.
    En la implementación real, esto vendría de la API de Google.
    """
    return {
        "summary": f"Reunión {event_id}",
        "start": {"dateTime": "2024-01-15T10:00:00Z"},
        "end": {"dateTime": "2024-01-15T11:00:00Z"},
        "description": "Reunión importante",
        "updated": time.time()
    }


def sincronizar_monday_a_google(item_id: str, event_id: str, manager: SyncStateManager):
    """
    Simula la sincronización desde Monday.com hacia Google Calendar.
    """
    print(f"\n🔄 Sincronizando Monday → Google: {item_id} → {event_id}")
    
    # Obtener contenido actual de Monday
    monday_content = simular_contenido_monday(item_id)
    monday_hash = manager._generate_content_hash(monday_content)
    
    # Verificar si se necesita sincronizar
    if not is_change_needed(item_id, event_id, monday_hash, "monday"):
        print("✅ No se detectaron cambios en Monday, sincronización omitida")
        return False
    
    print("📝 Cambios detectados en Monday, procediendo con sincronización...")
    
    # Simular actualización en Google Calendar
    google_content = simular_contenido_google(event_id)
    google_hash = manager._generate_content_hash(google_content)
    
    # Simular delay de operación
    time.sleep(0.1)
    
    # Actualizar estado de sincronización
    success = update_sync_state(
        item_id, event_id,
        monday_content_hash=monday_hash,
        google_content_hash=google_hash,
        sync_direction="monday_to_google",
        monday_update_time=time.time()
    )
    
    if success:
        print("✅ Sincronización Monday → Google completada")
        return True
    else:
        print("❌ Error en sincronización Monday → Google")
        return False


def sincronizar_google_a_monday(item_id: str, event_id: str, manager: SyncStateManager):
    """
    Simula la sincronización desde Google Calendar hacia Monday.com.
    """
    print(f"\n🔄 Sincronizando Google → Monday: {event_id} → {item_id}")
    
    # Obtener contenido actual de Google
    google_content = simular_contenido_google(event_id)
    google_hash = manager._generate_content_hash(google_content)
    
    # Verificar si se necesita sincronizar
    if not is_change_needed(item_id, event_id, google_hash, "google"):
        print("✅ No se detectaron cambios en Google, sincronización omitida")
        return False
    
    print("📝 Cambios detectados en Google, procediendo con sincronización...")
    
    # Simular actualización en Monday.com
    monday_content = simular_contenido_monday(item_id)
    monday_hash = manager._generate_content_hash(monday_content)
    
    # Simular delay de operación
    time.sleep(0.1)
    
    # Actualizar estado de sincronización
    success = update_sync_state(
        item_id, event_id,
        monday_content_hash=monday_hash,
        google_content_hash=google_hash,
        sync_direction="google_to_monday",
        google_update_time=time.time()
    )
    
    if success:
        print("✅ Sincronización Google → Monday completada")
        return True
    else:
        print("❌ Error en sincronización Google → Monday")
        return False


def mostrar_estado_sincronizacion(item_id: str, event_id: str, manager: SyncStateManager):
    """
    Muestra el estado actual de sincronización para un par item/event.
    """
    state = get_sync_state(item_id, event_id)
    
    if state:
        print(f"\n📊 Estado de sincronización para {item_id} ↔ {event_id}:")
        print(f"   Versión: {state['sync_version']}")
        print(f"   Última dirección: {state['last_sync_direction']}")
        print(f"   Última sincronización: {time.ctime(state['last_sync_timestamp'])}")
        print(f"   Hash Monday: {state['monday_content_hash'][:16]}...")
        print(f"   Hash Google: {state['google_content_hash'][:16]}...")
    else:
        print(f"\n📊 No hay estado de sincronización para {item_id} ↔ {event_id}")


def ejemplo_uso_completo():
    """
    Ejemplo completo de uso del SyncStateManager.
    """
    print("🚀 Ejemplo de integración del SyncStateManager")
    print("=" * 50)
    
    # Crear instancia del gestor
    manager = SyncStateManager("config/ejemplo_sync_state.json")
    
    # Datos de ejemplo
    item_id = "item_12345"
    event_id = "google_event_67890"
    
    print(f"📋 Configuración inicial:")
    print(f"   Item Monday: {item_id}")
    print(f"   Event Google: {event_id}")
    
    # Mostrar estado inicial
    mostrar_estado_sincronizacion(item_id, event_id, manager)
    
    # Primera sincronización (Monday → Google)
    print("\n" + "="*50)
    print("🎯 PRIMERA SINCRONIZACIÓN")
    sincronizar_monday_a_google(item_id, event_id, manager)
    mostrar_estado_sincronizacion(item_id, event_id, manager)
    
    # Segunda sincronización (mismo contenido, debe omitirse)
    print("\n" + "="*50)
    print("🎯 SEGUNDA SINCRONIZACIÓN (mismo contenido)")
    sincronizar_monday_a_google(item_id, event_id, manager)
    mostrar_estado_sincronizacion(item_id, event_id, manager)
    
    # Tercera sincronización (Google → Monday)
    print("\n" + "="*50)
    print("🎯 TERCERA SINCRONIZACIÓN (dirección inversa)")
    sincronizar_google_a_monday(item_id, event_id, manager)
    mostrar_estado_sincronizacion(item_id, event_id, manager)
    
    # Simular cambio en Monday
    print("\n" + "="*50)
    print("🎯 SIMULANDO CAMBIO EN MONDAY")
    
    # Crear contenido modificado para detectar cambios
    contenido_modificado = {
        "name": f"Reunión {item_id} - MODIFICADA",
        "date": {"date": "2024-01-15"},
        "status": {"label": "Done"},
        "priority": {"label": "High"},
        "last_updated": time.time()
    }
    
    # Generar hash del contenido modificado
    monday_hash_modificado = manager._generate_content_hash(contenido_modificado)
    
    # Verificar si se detecta el cambio
    if is_change_needed(item_id, event_id, monday_hash_modificado, "monday"):
        print("✅ Cambio detectado correctamente")
        
        # Actualizar estado con el nuevo contenido
        update_sync_state(
            item_id, event_id,
            monday_content_hash=monday_hash_modificado,
            sync_direction="monday_to_google",
            monday_update_time=time.time()
        )
        
        mostrar_estado_sincronizacion(item_id, event_id, manager)
    else:
        print("❌ No se detectó el cambio")
    
    # Mostrar estadísticas finales
    print("\n" + "="*50)
    print("📈 ESTADÍSTICAS FINALES")
    stats = manager.get_sync_statistics()
    print(f"   Total de sincronizaciones: {stats['total_syncs']}")
    print(f"   Sincronizaciones recientes: {stats['recent_syncs']}")
    print(f"   Sincronización más antigua: {stats['oldest_sync']}")
    print(f"   Sincronización más reciente: {stats['newest_sync']}")
    
    # Limpiar estados obsoletos (simulación)
    print("\n" + "="*50)
    print("🧹 LIMPIEZA DE ESTADOS")
    cleaned = manager.cleanup_old_states(days_threshold=30)
    print(f"   Estados eliminados: {cleaned}")
    
    print("\n✅ Ejemplo completado exitosamente!")


def ejemplo_webhook_integration():
    """
    Ejemplo de cómo integrar el SyncStateManager en un webhook.
    """
    print("\n🔗 Ejemplo de integración en webhook")
    print("=" * 50)
    
    manager = SyncStateManager("config/webhook_sync_state.json")
    
    def procesar_webhook_monday(webhook_data: dict):
        """
        Simula el procesamiento de un webhook de Monday.com.
        """
        print("📥 Webhook de Monday.com recibido")
        
        # Extraer datos del webhook
        item_id = webhook_data.get("item_id", "unknown")
        event_id = webhook_data.get("google_event_id", "unknown")
        
        print(f"   Item ID: {item_id}")
        print(f"   Event ID: {event_id}")
        
        # Obtener contenido actualizado de Monday
        monday_content = simular_contenido_monday(item_id)
        monday_hash = manager._generate_content_hash(monday_content)
        
        # Verificar si se necesita sincronizar
        if is_change_needed(item_id, event_id, monday_hash, "monday"):
            print("   ✅ Cambios detectados, procediendo con sincronización...")
            
            # Aquí iría la lógica real de sincronización
            # sync_to_google_calendar(item_id, event_id, monday_content)
            
            # Actualizar estado
            update_sync_state(
                item_id, event_id,
                monday_content_hash=monday_hash,
                sync_direction="monday_to_google",
                monday_update_time=time.time()
            )
            
            print("   ✅ Sincronización completada")
        else:
            print("   ⏭️  No se detectaron cambios, sincronización omitida")
    
    def procesar_webhook_google(webhook_data: dict):
        """
        Simula el procesamiento de un webhook de Google Calendar.
        """
        print("📥 Webhook de Google Calendar recibido")
        
        # Extraer datos del webhook
        event_id = webhook_data.get("event_id", "unknown")
        item_id = webhook_data.get("monday_item_id", "unknown")
        
        print(f"   Event ID: {event_id}")
        print(f"   Item ID: {item_id}")
        
        # Obtener contenido actualizado de Google
        google_content = simular_contenido_google(event_id)
        google_hash = manager._generate_content_hash(google_content)
        
        # Verificar si se necesita sincronizar
        if is_change_needed(item_id, event_id, google_hash, "google"):
            print("   ✅ Cambios detectados, procediendo con sincronización...")
            
            # Aquí iría la lógica real de sincronización
            # sync_to_monday(item_id, event_id, google_content)
            
            # Actualizar estado
            update_sync_state(
                item_id, event_id,
                google_content_hash=google_hash,
                sync_direction="google_to_monday",
                google_update_time=time.time()
            )
            
            print("   ✅ Sincronización completada")
        else:
            print("   ⏭️  No se detectaron cambios, sincronización omitida")
    
    # Simular webhooks
    webhook_monday = {
        "item_id": "webhook_item_123",
        "google_event_id": "webhook_event_456",
        "type": "update"
    }
    
    webhook_google = {
        "event_id": "webhook_event_456",
        "monday_item_id": "webhook_item_123",
        "type": "update"
    }
    
    # Procesar webhooks
    procesar_webhook_monday(webhook_monday)
    procesar_webhook_google(webhook_google)
    
    print("\n✅ Ejemplo de webhook completado!")


if __name__ == "__main__":
    try:
        ejemplo_uso_completo()
        ejemplo_webhook_integration()
        
        print("\n🎉 Todos los ejemplos ejecutados exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en los ejemplos: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
