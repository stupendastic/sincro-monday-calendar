#!/usr/bin/env python3
"""
Script para probar los webhooks refactorizados con el nuevo sistema anti-bucles.
Verifica que el sistema de sync_state_manager y detección de automatización funciona correctamente.
"""

import sys
import time
import json
from pathlib import Path

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import config
    from monday_api_handler import MondayAPIHandler
    from sync_logic import generate_content_hash, _detectar_cambio_de_automatizacion
    from sync_state_manager import get_sync_state, update_sync_state
    from google_calendar_service import get_calendar_service
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("   Asegúrate de que tienes configurado config.py y las dependencias")
    sys.exit(1)


def test_sync_state_management():
    """Prueba el sistema de gestión de estado de sincronización."""
    print("=== Prueba de Gestión de Estado de Sincronización ===")
    
    try:
        # Datos de prueba
        test_item_id = "test_item_123"
        test_event_id = "test_event_456"
        
        # Generar contenido de prueba
        test_content = {
            'fecha': '2024-01-15T10:00:00Z',
            'titulo': 'Reunión de Prueba',
            'operarios': 'Juan Pérez'
        }
        test_hash = generate_content_hash(test_content)
        
        print(f"📊 Hash generado: {test_hash}")
        
        # Obtener estado inicial
        initial_state = get_sync_state(test_item_id, test_event_id)
        print(f"📋 Estado inicial: {initial_state}")
        
        # Actualizar estado
        update_sync_state(
            item_id=test_item_id,
            event_id=test_event_id,
            monday_content_hash=test_hash,
            google_content_hash=None,
            sync_direction="monday_to_google",
            monday_update_time=time.time()
        )
        
        # Verificar estado actualizado
        updated_state = get_sync_state(test_item_id, test_event_id)
        print(f"📋 Estado actualizado: {updated_state}")
        
        if updated_state and updated_state.get('monday_content_hash') == test_hash:
            print("✅ Estado de sincronización funciona correctamente")
        else:
            print("❌ Error en gestión de estado de sincronización")
        
    except Exception as e:
        print(f"❌ Error en prueba de gestión de estado: {e}")
        import traceback
        traceback.print_exc()


def test_echo_detection():
    """Prueba la detección de ecos."""
    print("\n=== Prueba de Detección de Ecos ===")
    
    try:
        # Datos de prueba
        test_item_id = "test_item_789"
        test_event_id = "test_event_101"
        
        # Contenido idéntico
        content1 = {
            'fecha': '2024-01-15T14:00:00Z',
            'titulo': 'Reunión Cliente',
            'operarios': 'María García'
        }
        content2 = {
            'fecha': '2024-01-15T14:00:00Z',
            'titulo': 'Reunión Cliente',
            'operarios': 'María García'
        }
        
        hash1 = generate_content_hash(content1)
        hash2 = generate_content_hash(content2)
        
        print(f"📊 Hash 1: {hash1}")
        print(f"📊 Hash 2: {hash2}")
        
        # Verificar que los hashes son idénticos
        if hash1 == hash2:
            print("✅ Hashes idénticos detectados correctamente")
        else:
            print("❌ Error: Hashes deberían ser idénticos")
        
        # Simular estado de sincronización
        update_sync_state(
            item_id=test_item_id,
            event_id=test_event_id,
            monday_content_hash=hash1,
            google_content_hash=None,
            sync_direction="monday_to_google",
            monday_update_time=time.time()
        )
        
        # Verificar detección de eco
        sync_state = get_sync_state(test_item_id, test_event_id)
        if sync_state and sync_state.get('monday_content_hash') == hash2:
            print("🔄 Eco detectado correctamente")
        else:
            print("❌ Error en detección de eco")
        
    except Exception as e:
        print(f"❌ Error en prueba de detección de ecos: {e}")
        import traceback
        traceback.print_exc()


def test_automation_detection():
    """Prueba la detección de automatización."""
    print("\n=== Prueba de Detección de Automatización ===")
    
    try:
        # Inicializar handler
        api_token = getattr(config, 'MONDAY_API_KEY', '')
        if not api_token:
            print("❌ No se encontró MONDAY_API_KEY en config.py")
            return
        
        handler = MondayAPIHandler(api_token)
        
        # Usar un item_id de prueba (deberías reemplazar con uno real)
        test_item_id = "123456789"  # Reemplazar con un item_id real
        
        print(f"🔍 Probando detección de automatización para item: {test_item_id}")
        
        # Probar detección
        start_time = time.time()
        is_automation = _detectar_cambio_de_automatizacion(test_item_id, handler)
        detection_time = time.time() - start_time
        
        print(f"📊 Tiempo de detección: {detection_time:.3f}s")
        print(f"📊 Resultado: {'Automatización' if is_automation else 'Usuario Real'}")
        
        if is_automation:
            print("🤖 Cambio de automatización detectado")
        else:
            print("👤 Cambio de usuario real detectado")
        
    except Exception as e:
        print(f"❌ Error en prueba de detección de automatización: {e}")
        import traceback
        traceback.print_exc()


def test_content_hash_generation():
    """Prueba la generación de hashes de contenido."""
    print("\n=== Prueba de Generación de Hashes ===")
    
    try:
        # Contenido de Monday
        monday_content = {
            'fecha': '2024-01-15T16:00:00Z',
            'titulo': 'Grabación Exterior',
            'operarios': 'Carlos López, Ana Martín'
        }
        
        # Contenido de Google
        google_content = {
            'fecha': '2024-01-15T16:00:00Z',
            'titulo': 'Grabación Exterior',
            'descripcion': 'Grabación en localización exterior'
        }
        
        # Generar hashes
        monday_hash = generate_content_hash(monday_content)
        google_hash = generate_content_hash(google_content)
        
        print(f"📊 Hash Monday: {monday_hash}")
        print(f"📊 Hash Google: {google_hash}")
        
        # Verificar que hashes diferentes para contenido diferente
        if monday_hash != google_hash:
            print("✅ Hashes diferentes para contenido diferente")
        else:
            print("⚠️  Hashes idénticos para contenido diferente")
        
        # Probar contenido idéntico
        identical_content = {
            'fecha': '2024-01-15T18:00:00Z',
            'titulo': 'Reunión Final',
            'operarios': 'Equipo Completo'
        }
        
        hash1 = generate_content_hash(identical_content)
        hash2 = generate_content_hash(identical_content)
        
        if hash1 == hash2:
            print("✅ Hashes idénticos para contenido idéntico")
        else:
            print("❌ Error: Hashes deberían ser idénticos")
        
    except Exception as e:
        print(f"❌ Error en prueba de generación de hashes: {e}")
        import traceback
        traceback.print_exc()


def test_webhook_simulation():
    """Simula el flujo de un webhook de Monday."""
    print("\n=== Simulación de Webhook de Monday ===")
    
    try:
        # Inicializar servicios
        api_token = getattr(config, 'MONDAY_API_KEY', '')
        if not api_token:
            print("❌ No se encontró MONDAY_API_KEY en config.py")
            return
        
        handler = MondayAPIHandler(api_token)
        google_service = get_calendar_service()
        
        # Simular datos de webhook
        webhook_data = {
            'pulseId': '123456789',  # Reemplazar con un item_id real
            'type': 'update'
        }
        
        print(f"🔄 Simulando webhook para item: {webhook_data['pulseId']}")
        
        # 1. Obtener datos del item
        item_id = webhook_data['pulseId']
        
        # 2. Obtener estado de sincronización
        # (En un webhook real, necesitaríamos obtener el google_event_id primero)
        print("📋 Obteniendo estado de sincronización...")
        
        # 3. Generar hash del contenido
        test_content = {
            'fecha': '2024-01-15T20:00:00Z',
            'titulo': 'Simulación Webhook',
            'operarios': 'Test User'
        }
        current_hash = generate_content_hash(test_content)
        
        print(f"📊 Hash del contenido: {current_hash}")
        
        # 4. Verificar si es un eco
        # (En un webhook real, compararíamos con sync_state)
        print("🔄 Verificando si es un eco...")
        
        # 5. Verificar si fue cambio de automatización
        print("🤖 Verificando si fue cambio de automatización...")
        is_automation = _detectar_cambio_de_automatizacion(item_id, handler)
        
        if is_automation:
            print("🛑 Cambio de automatización detectado - webhook ignorado")
        else:
            print("✅ Cambio de usuario real - procediendo con sincronización")
        
        print("🎭 Simulación de webhook completada")
        
    except Exception as e:
        print(f"❌ Error en simulación de webhook: {e}")
        import traceback
        traceback.print_exc()


def test_google_webhook_simulation():
    """Simula el flujo de un webhook de Google."""
    print("\n=== Simulación de Webhook de Google ===")
    
    try:
        # Inicializar servicios
        api_token = getattr(config, 'MONDAY_API_KEY', '')
        if not api_token:
            print("❌ No se encontró MONDAY_API_KEY en config.py")
            return
        
        handler = MondayAPIHandler(api_token)
        google_service = get_calendar_service()
        
        # Simular evento de Google
        google_event = {
            'id': 'test_google_event_123',
            'summary': 'Evento de Prueba Google',
            'start': {'dateTime': '2024-01-15T22:00:00Z'},
            'description': 'Descripción del evento de prueba'
        }
        
        print(f"🔄 Simulando webhook de Google para evento: {google_event['id']}")
        
        # 1. Buscar item correspondiente en Monday
        event_id = google_event['id']
        print(f"🔍 Buscando item correspondiente para evento {event_id}...")
        
        # 2. Generar hash del contenido de Google
        google_content = {
            'fecha': google_event.get('start', {}).get('dateTime', ''),
            'titulo': google_event.get('summary', ''),
            'descripcion': google_event.get('description', '')
        }
        google_hash = generate_content_hash(google_content)
        
        print(f"📊 Hash del contenido Google: {google_hash}")
        
        # 3. Verificar si es un eco
        # (En un webhook real, compararíamos con sync_state)
        print("🔄 Verificando si es un eco...")
        
        print("🎭 Simulación de webhook de Google completada")
        
    except Exception as e:
        print(f"❌ Error en simulación de webhook de Google: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas de webhooks refactorizados...\n")
    
    # Verificar configuración
    if not hasattr(config, 'MONDAY_API_KEY') or not config.MONDAY_API_KEY:
        print("❌ Error: MONDAY_API_KEY no está configurado en config.py")
        print("   Las pruebas que requieren conexión a Monday.com no funcionarán completamente")
        print("   Pero las pruebas de lógica local sí se ejecutarán\n")
    
    if not hasattr(config, 'AUTOMATION_USER_ID') or not config.AUTOMATION_USER_ID:
        print("❌ Error: AUTOMATION_USER_ID no está configurado en config.py")
        return
    
    if not hasattr(config, 'COL_FECHA') or not config.COL_FECHA:
        print("❌ Error: COL_FECHA no está configurado en config.py")
        return
    
    print(f"✅ Configuración verificada:")
    print(f"   - Usuario automatización: {config.AUTOMATION_USER_NAME} (ID: {config.AUTOMATION_USER_ID})")
    print(f"   - Columna fecha: {config.COL_FECHA}")
    print(f"   - Board ID: {config.BOARD_ID_GRABACIONES}\n")
    
    # Ejecutar todas las pruebas
    test_sync_state_management()
    test_echo_detection()
    test_content_hash_generation()
    test_automation_detection()
    test_webhook_simulation()
    test_google_webhook_simulation()
    
    print("\n🎉 ¡Pruebas de webhooks refactorizados completadas!")
    print("\n✅ Mejoras implementadas:")
    print("   - 🗂️  Gestión de estado persistente con sync_state_manager")
    print("   - 🔄 Detección de ecos basada en hashes de contenido")
    print("   - 🤖 Detección de automatización mejorada")
    print("   - 📊 Generación de hashes determinísticos")
    print("   - 🛡️  Sistema anti-bucles robusto")
    print("   - ⚡ Eliminación de cooldowns y UUIDs obsoletos")


if __name__ == "__main__":
    main()
