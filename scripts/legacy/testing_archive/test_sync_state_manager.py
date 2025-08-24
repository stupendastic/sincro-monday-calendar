#!/usr/bin/env python3
"""
Script de prueba para el SyncStateManager.
Verifica todas las funcionalidades principales del gestor de estado de sincronización.
"""

import sys
import os
import time
import json
from pathlib import Path

# Añadir el directorio raíz al path para importar el módulo
sys.path.append(str(Path(__file__).parent.parent.parent))

from sync_state_manager import SyncStateManager, sync_state_manager


def test_basic_functionality():
    """Prueba la funcionalidad básica del SyncStateManager."""
    print("=== Prueba de Funcionalidad Básica ===")
    
    # Crear instancia
    manager = SyncStateManager("config/test_sync_state.json")
    
    # Datos de prueba
    item_id = "test_item_123"
    event_id = "test_event_456"
    
    # Simular contenido
    monday_content = {
        "name": "Reunión de prueba",
        "date": {"date": "2024-01-15"},
        "status": {"label": "Working on it"}
    }
    
    google_content = {
        "summary": "Reunión de prueba",
        "start": {"dateTime": "2024-01-15T10:00:00Z"},
        "end": {"dateTime": "2024-01-15T11:00:00Z"}
    }
    
    # Generar hashes
    monday_hash = manager._generate_content_hash(monday_content)
    google_hash = manager._generate_content_hash(google_content)
    
    print(f"Hash Monday: {monday_hash[:16]}...")
    print(f"Hash Google: {google_hash[:16]}...")
    
    # 1. Probar get_sync_state (debe ser None inicialmente)
    initial_state = manager.get_sync_state(item_id, event_id)
    print(f"Estado inicial: {initial_state}")
    assert initial_state is None, "El estado inicial debe ser None"
    
    # 2. Probar update_sync_state
    success = manager.update_sync_state(
        item_id, event_id,
        monday_content_hash=monday_hash,
        google_content_hash=google_hash,
        sync_direction="monday_to_google"
    )
    print(f"Actualización exitosa: {success}")
    assert success, "La actualización debe ser exitosa"
    
    # 3. Verificar que el estado se guardó correctamente
    saved_state = manager.get_sync_state(item_id, event_id)
    print(f"Estado guardado: {saved_state}")
    assert saved_state is not None, "El estado debe haberse guardado"
    assert saved_state["monday_content_hash"] == monday_hash
    assert saved_state["google_content_hash"] == google_hash
    assert saved_state["last_sync_direction"] == "monday_to_google"
    assert saved_state["sync_version"] == 1
    
    print("✅ Funcionalidad básica: OK")


def test_change_detection():
    """Prueba la detección de cambios."""
    print("\n=== Prueba de Detección de Cambios ===")
    
    manager = SyncStateManager("config/test_sync_state.json")
    
    item_id = "test_item_123"
    event_id = "test_event_456"
    
    # Contenido original
    original_content = {"title": "Reunión original", "date": "2024-01-15"}
    original_hash = manager._generate_content_hash(original_content)
    
    # Actualizar estado con contenido original
    manager.update_sync_state(
        item_id, event_id,
        monday_content_hash=original_hash,
        sync_direction="monday_to_google"
    )
    
    # 1. Probar con mismo contenido (no debe detectar cambio)
    needs_sync = manager.is_change_needed(item_id, event_id, original_hash, "monday")
    print(f"¿Necesita sincronización con mismo contenido? {needs_sync}")
    assert not needs_sync, "No debe detectar cambio con el mismo contenido"
    
    # 2. Probar con contenido modificado (debe detectar cambio)
    modified_content = {"title": "Reunión modificada", "date": "2024-01-15"}
    modified_hash = manager._generate_content_hash(modified_content)
    
    needs_sync = manager.is_change_needed(item_id, event_id, modified_hash, "monday")
    print(f"¿Necesita sincronización con contenido modificado? {needs_sync}")
    assert needs_sync, "Debe detectar cambio con contenido modificado"
    
    # 3. Probar con estado inexistente (debe requerir sincronización)
    needs_sync = manager.is_change_needed("item_inexistente", "event_inexistente", modified_hash, "monday")
    print(f"¿Necesita sincronización con estado inexistente? {needs_sync}")
    assert needs_sync, "Debe requerir sincronización con estado inexistente"
    
    print("✅ Detección de cambios: OK")


def test_concurrent_access():
    """Prueba el acceso concurrente."""
    print("\n=== Prueba de Acceso Concurrente ===")
    
    import threading
    
    manager = SyncStateManager("config/test_concurrent_sync_state.json")
    
    def update_state(thread_id):
        """Función para actualizar estado desde un hilo."""
        item_id = f"item_thread_{thread_id}"
        event_id = f"event_thread_{thread_id}"
        
        content = {"title": f"Reunión hilo {thread_id}", "timestamp": time.time()}
        content_hash = manager._generate_content_hash(content)
        
        success = manager.update_sync_state(
            item_id, event_id,
            monday_content_hash=content_hash,
            sync_direction="monday_to_google"
        )
        
        return success
    
    # Crear múltiples hilos
    threads = []
    results = []
    
    for i in range(5):
        thread = threading.Thread(target=lambda i=i: results.append(update_state(i)))
        threads.append(thread)
        thread.start()
    
    # Esperar a que terminen todos los hilos
    for thread in threads:
        thread.join()
    
    # Verificar que todas las actualizaciones fueron exitosas
    print(f"Resultados de actualizaciones concurrentes: {results}")
    assert all(results), "Todas las actualizaciones concurrentes deben ser exitosas"
    
    # Verificar que todos los estados se guardaron
    for i in range(5):
        item_id = f"item_thread_{i}"
        event_id = f"event_thread_{i}"
        state = manager.get_sync_state(item_id, event_id)
        assert state is not None, f"El estado del hilo {i} debe haberse guardado"
    
    print("✅ Acceso concurrente: OK")


def test_cleanup_functionality():
    """Prueba la funcionalidad de limpieza."""
    print("\n=== Prueba de Funcionalidad de Limpieza ===")
    
    manager = SyncStateManager("config/test_cleanup_sync_state.json")
    
    # Crear estados con diferentes timestamps
    current_time = time.time()
    
    # Estado reciente (hace 1 hora)
    manager.update_sync_state(
        "item_reciente", "event_reciente",
        monday_content_hash="hash_reciente",
        sync_direction="monday_to_google"
    )
    
    # Estado muy antiguo (hace 60 días)
    manager.update_sync_state(
        "item_antiguo", "event_antiguo",
        monday_content_hash="hash_antiguo",
        sync_direction="monday_to_google"
    )
    
    # Modificar manualmente los timestamps para simular estados antiguos
    state = manager._load_state()
    
    # Hacer el estado reciente más reciente (hace 1 hora)
    if "item_reciente_event_reciente" in state:
        state["item_reciente_event_reciente"]["last_sync_timestamp"] = current_time - (1 * 3600)
    
    # Hacer el estado antiguo muy antiguo (hace 60 días)
    if "item_antiguo_event_antiguo" in state:
        state["item_antiguo_event_antiguo"]["last_sync_timestamp"] = current_time - (60 * 24 * 3600)
    
    # Guardar los cambios
    manager._save_state(state)
    
    # Verificar estados antes de la limpieza
    stats_before = manager.get_sync_statistics()
    print(f"Estados antes de limpieza: {stats_before}")
    
    # Ejecutar limpieza (eliminar estados de más de 30 días)
    cleaned_count = manager.cleanup_old_states(days_threshold=30)
    print(f"Estados eliminados: {cleaned_count}")
    
    # Verificar estados después de la limpieza
    stats_after = manager.get_sync_statistics()
    print(f"Estados después de limpieza: {stats_after}")
    
    # El estado reciente debe seguir existiendo
    recent_state = manager.get_sync_state("item_reciente", "event_reciente")
    assert recent_state is not None, "El estado reciente debe mantenerse"
    
    print("✅ Funcionalidad de limpieza: OK")


def test_statistics():
    """Prueba las estadísticas."""
    print("\n=== Prueba de Estadísticas ===")
    
    manager = SyncStateManager("config/test_stats_sync_state.json")
    
    # Limpiar estado inicial
    manager._save_state({})
    
    # Verificar estadísticas con estado vacío
    empty_stats = manager.get_sync_statistics()
    print(f"Estadísticas con estado vacío: {empty_stats}")
    assert empty_stats["total_syncs"] == 0, "Debe mostrar 0 sincronizaciones"
    
    # Añadir algunos estados
    for i in range(3):
        manager.update_sync_state(
            f"item_{i}", f"event_{i}",
            monday_content_hash=f"hash_{i}",
            sync_direction="monday_to_google"
        )
    
    # Verificar estadísticas con datos
    stats = manager.get_sync_statistics()
    print(f"Estadísticas con datos: {stats}")
    assert stats["total_syncs"] == 3, "Debe mostrar 3 sincronizaciones"
    assert stats["recent_syncs"] >= 3, "Todas deben ser recientes"
    
    print("✅ Estadísticas: OK")


def test_error_handling():
    """Prueba el manejo de errores."""
    print("\n=== Prueba de Manejo de Errores ===")
    
    # Probar con archivo JSON corrupto
    corrupt_file = Path("config/test_corrupt_sync_state.json")
    corrupt_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Crear archivo JSON corrupto
    with open(corrupt_file, 'w') as f:
        f.write("{ invalid json content")
    
    try:
        manager = SyncStateManager(str(corrupt_file))
        # Debe manejar el error y crear un nuevo estado
        state = manager.get_sync_state("test", "test")
        assert state is None, "Debe manejar archivo corrupto correctamente"
        print("✅ Manejo de archivo corrupto: OK")
    except Exception as e:
        print(f"❌ Error inesperado con archivo corrupto: {e}")
    
    # Limpiar archivo corrupto
    if corrupt_file.exists():
        corrupt_file.unlink()


def test_file_operations():
    """Prueba las operaciones de archivo."""
    print("\n=== Prueba de Operaciones de Archivo ===")
    
    test_file = Path("config/test_file_ops_sync_state.json")
    
    # Eliminar archivo si existe
    if test_file.exists():
        test_file.unlink()
    
    # Crear manager (debe crear el archivo automáticamente)
    manager = SyncStateManager(str(test_file))
    
    # Verificar que el archivo se creó
    assert test_file.exists(), "El archivo debe haberse creado automáticamente"
    
    # Verificar que el directorio se creó si no existía
    assert test_file.parent.exists(), "El directorio debe haberse creado"
    
    # Probar operaciones básicas
    manager.update_sync_state(
        "test_item", "test_event",
        monday_content_hash="test_hash",
        sync_direction="monday_to_google"
    )
    
    # Verificar que el archivo contiene datos válidos
    with open(test_file, 'r') as f:
        data = json.load(f)
        assert isinstance(data, dict), "El archivo debe contener un diccionario válido"
    
    print("✅ Operaciones de archivo: OK")


def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas del SyncStateManager...\n")
    
    try:
        test_basic_functionality()
        test_change_detection()
        test_concurrent_access()
        test_cleanup_functionality()
        test_statistics()
        test_error_handling()
        test_file_operations()
        
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Limpiar archivos de prueba
        test_files = [
            "config/test_sync_state.json",
            "config/test_concurrent_sync_state.json",
            "config/test_cleanup_sync_state.json",
            "config/test_stats_sync_state.json",
            "config/test_file_ops_sync_state.json"
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                Path(test_file).unlink()
                print(f"🧹 Archivo de prueba eliminado: {test_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
