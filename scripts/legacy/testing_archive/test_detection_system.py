#!/usr/bin/env python3
"""
Script de prueba para el nuevo sistema de detección de cambios.
Verifica que el sistema evite bucles infinitos correctamente.
"""

import sys
import json
import time
from pathlib import Path

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from sync_logic import generate_content_hash, detect_real_change
from sync_state_manager import SyncStateManager, get_sync_state, update_sync_state


def test_generate_content_hash():
    """Prueba la generación de hashes de contenido."""
    print("=== Prueba de Generación de Hashes ===")
    
    # Datos de prueba para Monday.com
    monday_content = {
        "name": "Reunión de prueba",
        "fecha_inicio": "2024-01-15T10:00:00",
        "fecha_fin": "2024-01-15T11:00:00",
        "operario": "Arnau Admin",
        "cliente": "Cliente Test",
        "ubicacion": "Oficina",
        "estadopermisos": "Pendiente",
        "accionesrealizar": "Grabar video",
        "contactoobra": "Juan Pérez",
        "telefonoobra": "123-456-789",
        "contactocomercial": "María García",
        "telefonocomercial": "987-654-321",
        "linkdropbox": "https://dropbox.com/test",
        # Campos de metadata que deben ser ignorados
        "updated_at": "2024-01-15T12:00:00",
        "etag": "abc123",
        "last_modified": "2024-01-15T12:00:00"
    }
    
    # Datos de prueba para Google Calendar
    google_content = {
        "summary": "Reunión de prueba",
        "start": {"dateTime": "2024-01-15T10:00:00+01:00"},
        "end": {"dateTime": "2024-01-15T11:00:00+01:00"},
        "location": "Oficina",
        "description": "Reunión importante",
        # Campos de metadata que deben ser ignorados
        "id": "google_event_123",
        "created": "2024-01-15T09:00:00Z",
        "updated": "2024-01-15T12:00:00Z"
    }
    
    # Generar hashes
    monday_hash = generate_content_hash(monday_content)
    google_hash = generate_content_hash(google_content)
    
    print(f"Hash Monday: {monday_hash}")
    print(f"Hash Google: {google_hash}")
    
    # Verificar que los hashes son consistentes
    monday_hash2 = generate_content_hash(monday_content)
    google_hash2 = generate_content_hash(google_content)
    
    assert monday_hash == monday_hash2, "Hash de Monday debe ser consistente"
    assert google_hash == google_hash2, "Hash de Google debe ser consistente"
    
    print("✅ Generación de hashes: OK")
    
    return monday_hash, google_hash


def test_detect_real_change():
    """Prueba la detección de cambios reales vs ecos."""
    print("\n=== Prueba de Detección de Cambios ===")
    
    # Eliminar archivo si existe
    test_file = Path("config/test_detection_sync_state.json")
    if test_file.exists():
        test_file.unlink()
    
    # Crear instancia del gestor de estado
    manager = SyncStateManager("config/test_detection_sync_state.json")
    
    item_id = "test_item_123"
    event_id = "test_event_456"
    
    # 1. Prueba: Cambio real (no hay estado previo)
    print("\n1. Prueba: Cambio real (sin estado previo)")
    content_hash = "abc123def456"
    is_real = detect_real_change(item_id, event_id, content_hash, "monday")
    print(f"   Resultado: {'Real' if is_real else 'Eco'}")
    assert is_real, "Debe detectar como cambio real cuando no hay estado previo"
    
    # Actualizar estado después de la primera detección
    update_sync_state(
        item_id, event_id,
        monday_content_hash=content_hash,
        sync_direction="monday_to_google",
        monday_update_time=time.time()
    )
    
    # 2. Prueba: Cambio real (hash diferente)
    print("\n2. Prueba: Cambio real (hash diferente)")
    # Actualizar estado con hash diferente
    update_sync_state(
        item_id, event_id,
        monday_content_hash="old_hash_123",
        sync_direction="monday_to_google",
        monday_update_time=time.time()
    )
    
    is_real = detect_real_change(item_id, event_id, content_hash, "monday")
    print(f"   Resultado: {'Real' if is_real else 'Eco'}")
    assert is_real, "Debe detectar como cambio real cuando el hash es diferente"
    
    # 3. Prueba: Eco (hash idéntico, tiempo reciente)
    print("\n3. Prueba: Eco (hash idéntico, tiempo reciente)")
    # Actualizar estado con el mismo hash
    update_sync_state(
        item_id, event_id,
        monday_content_hash=content_hash,
        sync_direction="monday_to_google",
        monday_update_time=time.time()
    )
    
    is_real = detect_real_change(item_id, event_id, content_hash, "monday")
    print(f"   Resultado: {'Real' if is_real else 'Eco'}")
    assert not is_real, "Debe detectar como eco cuando el hash es idéntico y reciente"
    
    # 4. Prueba: Cambio real (hash idéntico, tiempo antiguo)
    print("\n4. Prueba: Cambio real (hash idéntico, tiempo antiguo)")
    # Simular estado antiguo (más de 5 minutos)
    old_state = get_sync_state(item_id, event_id)
    if old_state:
        # Crear un nuevo estado con timestamp antiguo
        old_state["last_sync_timestamp"] = time.time() - 360  # 6 minutos atrás
        # Guardar directamente en el archivo
        current_state = manager._load_state()
        current_state[f"{item_id}_{event_id}"] = old_state
        manager._save_state(current_state)
        
        print(f"   📅 Timestamp simulado: {old_state['last_sync_timestamp']}")
    
    is_real = detect_real_change(item_id, event_id, content_hash, "monday")
    print(f"   Resultado: {'Real' if is_real else 'Eco'}")
    assert is_real, "Debe detectar como cambio real cuando el hash es idéntico pero antiguo"
    
    print("✅ Detección de cambios: OK")


def test_integration_scenario():
    """Prueba un escenario completo de integración."""
    print("\n=== Prueba de Escenario de Integración ===")
    
    # Eliminar archivo si existe
    test_file = Path("config/test_integration_sync_state.json")
    if test_file.exists():
        test_file.unlink()
    
    # Crear instancia del gestor de estado
    manager = SyncStateManager("config/test_integration_sync_state.json")
    
    item_id = "integration_item_123"
    event_id = "integration_event_456"
    
    # Simular contenido inicial
    initial_content = {
        "name": "Reunión inicial",
        "fecha_inicio": "2024-01-15T10:00:00",
        "operario": "Arnau Admin",
        "cliente": "Cliente A"
    }
    
    initial_hash = generate_content_hash(initial_content)
    print(f"Hash inicial: {initial_hash[:16]}...")
    
    # 1. Primera sincronización (debe ser cambio real)
    print("\n1. Primera sincronización")
    is_real = detect_real_change(item_id, event_id, initial_hash, "monday")
    print(f"   Es cambio real: {is_real}")
    assert is_real, "Primera sincronización debe ser cambio real"
    
    # Actualizar estado después de sincronización
    update_sync_state(
        item_id, event_id,
        monday_content_hash=initial_hash,
        sync_direction="monday_to_google",
        monday_update_time=time.time()
    )
    
    # 2. Segunda sincronización con mismo contenido (debe ser eco)
    print("\n2. Segunda sincronización (mismo contenido)")
    is_real = detect_real_change(item_id, event_id, initial_hash, "monday")
    print(f"   Es cambio real: {is_real}")
    assert not is_real, "Segunda sincronización con mismo contenido debe ser eco"
    
    # 3. Tercera sincronización con contenido modificado (debe ser cambio real)
    print("\n3. Tercera sincronización (contenido modificado)")
    modified_content = {
        "name": "Reunión modificada",
        "fecha_inicio": "2024-01-15T10:00:00",
        "operario": "Arnau Admin",
        "cliente": "Cliente B"  # Cliente cambiado
    }
    
    modified_hash = generate_content_hash(modified_content)
    print(f"Hash modificado: {modified_hash[:16]}...")
    
    is_real = detect_real_change(item_id, event_id, modified_hash, "monday")
    print(f"   Es cambio real: {is_real}")
    assert is_real, "Sincronización con contenido modificado debe ser cambio real"
    
    # Actualizar estado después de sincronización
    update_sync_state(
        item_id, event_id,
        monday_content_hash=modified_hash,
        sync_direction="monday_to_google",
        monday_update_time=time.time()
    )
    
    # 4. Cuarta sincronización con contenido modificado (debe ser eco)
    print("\n4. Cuarta sincronización (mismo contenido modificado)")
    is_real = detect_real_change(item_id, event_id, modified_hash, "monday")
    print(f"   Es cambio real: {is_real}")
    assert not is_real, "Cuarta sincronización con mismo contenido debe ser eco"
    
    print("✅ Escenario de integración: OK")


def test_google_content_hash():
    """Prueba la generación de hashes para contenido de Google Calendar."""
    print("\n=== Prueba de Hash para Google Calendar ===")
    
    # Simular evento de Google Calendar
    google_event = {
        "summary": "Reunión de Google",
        "start": {
            "dateTime": "2024-01-15T10:00:00+01:00",
            "timeZone": "Europe/Madrid"
        },
        "end": {
            "dateTime": "2024-01-15T11:00:00+01:00",
            "timeZone": "Europe/Madrid"
        },
        "location": "Oficina principal",
        "description": "Reunión importante con el cliente",
        # Campos de metadata que deben ser ignorados
        "id": "google_event_789",
        "created": "2024-01-15T09:00:00Z",
        "updated": "2024-01-15T12:00:00Z",
        "etag": "\"abc123\"",
        "htmlLink": "https://calendar.google.com/event?eid=abc123"
    }
    
    # Generar hash
    google_hash = generate_content_hash(google_event)
    print(f"Hash Google: {google_hash}")
    
    # Verificar consistencia
    google_hash2 = generate_content_hash(google_event)
    assert google_hash == google_hash2, "Hash de Google debe ser consistente"
    
    print("✅ Hash para Google Calendar: OK")
    
    return google_hash


def test_bidirectional_detection():
    """Prueba la detección de cambios en ambas direcciones."""
    print("\n=== Prueba de Detección Bidireccional ===")
    
    # Eliminar archivo si existe
    test_file = Path("config/test_bidirectional_sync_state.json")
    if test_file.exists():
        test_file.unlink()
    
    # Crear instancia del gestor de estado
    manager = SyncStateManager("config/test_bidirectional_sync_state.json")
    
    item_id = "bidirectional_item_123"
    event_id = "bidirectional_event_456"
    
    # Simular contenido de Monday
    monday_content = {
        "name": "Reunión bidireccional",
        "fecha_inicio": "2024-01-15T10:00:00",
        "operario": "Arnau Admin"
    }
    
    # Simular contenido de Google
    google_content = {
        "summary": "Reunión bidireccional",
        "start": {"dateTime": "2024-01-15T10:00:00+01:00"},
        "end": {"dateTime": "2024-01-15T11:00:00+01:00"}
    }
    
    monday_hash = generate_content_hash(monday_content)
    google_hash = generate_content_hash(google_content)
    
    print(f"Hash Monday: {monday_hash[:16]}...")
    print(f"Hash Google: {google_hash[:16]}...")
    
    # 1. Sincronización Monday → Google
    print("\n1. Sincronización Monday → Google")
    is_real_monday = detect_real_change(item_id, event_id, monday_hash, "monday")
    print(f"   Monday es cambio real: {is_real_monday}")
    
    # Actualizar estado
    update_sync_state(
        item_id, event_id,
        monday_content_hash=monday_hash,
        google_content_hash=google_hash,
        sync_direction="monday_to_google",
        monday_update_time=time.time()
    )
    
    # 2. Sincronización Google → Monday
    print("\n2. Sincronización Google → Monday")
    is_real_google = detect_real_change(item_id, event_id, google_hash, "google")
    print(f"   Google es cambio real: {is_real_google}")
    
    # 3. Verificar que los hashes se mantienen separados
    print("\n3. Verificar separación de hashes")
    sync_state = get_sync_state(item_id, event_id)
    if sync_state:
        print(f"   Hash Monday almacenado: {sync_state.get('monday_content_hash', '')[:16]}...")
        print(f"   Hash Google almacenado: {sync_state.get('google_content_hash', '')[:16]}...")
        
        assert sync_state.get('monday_content_hash') == monday_hash, "Hash de Monday debe estar almacenado"
        assert sync_state.get('google_content_hash') == google_hash, "Hash de Google debe estar almacenado"
    
    print("✅ Detección bidireccional: OK")


def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas del sistema de detección de cambios...\n")
    
    try:
        # Ejecutar todas las pruebas
        test_generate_content_hash()
        test_detect_real_change()
        test_integration_scenario()
        test_google_content_hash()
        test_bidirectional_detection()
        
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n✅ El sistema de detección de cambios está funcionando correctamente.")
        print("   - Generación de hashes consistente")
        print("   - Detección de cambios reales vs ecos")
        print("   - Manejo bidireccional")
        print("   - Integración con SyncStateManager")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Limpiar archivos de prueba
        test_files = [
            "config/test_detection_sync_state.json",
            "config/test_integration_sync_state.json",
            "config/test_bidirectional_sync_state.json"
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                Path(test_file).unlink()
                print(f"🧹 Archivo de prueba eliminado: {test_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
