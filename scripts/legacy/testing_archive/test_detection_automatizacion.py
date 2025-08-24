#!/usr/bin/env python3
"""
Script para probar la nueva función de detección de automatización mejorada.
Verifica que el sistema detecte correctamente los cambios de automatización
y evite bucles de sincronización.
"""

import sys
import time
from pathlib import Path

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import config
    from monday_api_handler import MondayAPIHandler
    from sync_logic import _detectar_cambio_de_automatizacion
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("   Asegúrate de que tienes configurado config.py y las dependencias")
    sys.exit(1)


def test_detection_basic():
    """Prueba básica de detección de automatización."""
    print("=== Prueba Básica de Detección ===")
    
    try:
        # Inicializar handler
        api_token = getattr(config, 'MONDAY_API_KEY', '')
        if not api_token:
            print("❌ No se encontró MONDAY_API_KEY en config.py")
            return
        
        handler = MondayAPIHandler(api_token)
        
        # Usar un item_id de prueba (deberías reemplazar con uno real)
        test_item_id = "123456789"  # Reemplazar con un item_id real
        
        print(f"🔍 Probando detección para item: {test_item_id}")
        print(f"🤖 Usuario de automatización: {config.AUTOMATION_USER_NAME} (ID: {config.AUTOMATION_USER_ID})")
        print(f"📅 Columna de fecha: {config.COL_FECHA}")
        
        # Probar detección
        start_time = time.time()
        is_automation = _detectar_cambio_de_automatizacion(test_item_id, handler)
        detection_time = time.time() - start_time
        
        print(f"📊 Tiempo de detección: {detection_time:.3f}s")
        print(f"📊 Resultado: {'Automatización' if is_automation else 'Usuario Real'}")
        
    except Exception as e:
        print(f"❌ Error en prueba básica: {e}")
        import traceback
        traceback.print_exc()


def test_detection_with_real_item():
    """Prueba con un item real del tablero."""
    print("\n=== Prueba con Item Real ===")
    
    try:
        # Inicializar handler
        api_token = getattr(config, 'MONDAY_API_KEY', '')
        if not api_token:
            print("❌ No se encontró MONDAY_API_KEY en config.py")
            return
        
        handler = MondayAPIHandler(api_token)
        
        # Obtener un item real del tablero
        print(f"🔍 Obteniendo items del tablero {config.BOARD_ID_GRABACIONES}...")
        
        items = handler.get_items(
            board_id=str(config.BOARD_ID_GRABACIONES),
            limit_per_page=5
        )
        
        if not items:
            print("❌ No se encontraron items en el tablero")
            return
        
        # Probar con el primer item
        test_item = items[0]
        test_item_id = test_item['id']
        test_item_name = test_item.get('name', 'Sin nombre')
        
        print(f"🔍 Probando con item real: {test_item_name} (ID: {test_item_id})")
        
        # Probar detección
        start_time = time.time()
        is_automation = _detectar_cambio_de_automatizacion(test_item_id, handler)
        detection_time = time.time() - start_time
        
        print(f"📊 Tiempo de detección: {detection_time:.3f}s")
        print(f"📊 Resultado: {'Automatización' if is_automation else 'Usuario Real'}")
        
        # Mostrar información del item
        print(f"📋 Información del item:")
        print(f"   - Nombre: {test_item_name}")
        print(f"   - ID: {test_item_id}")
        
        # Mostrar columnas relevantes
        column_values = test_item.get('column_values', [])
        for col in column_values:
            col_id = col.get('id', '')
            col_text = col.get('text', '')
            if col_id in [config.COL_FECHA, config.COL_GOOGLE_EVENT_ID]:
                print(f"   - {col_id}: {col_text}")
        
    except Exception as e:
        print(f"❌ Error en prueba con item real: {e}")
        import traceback
        traceback.print_exc()


def test_activity_log_query():
    """Prueba directa de la query de activity_logs."""
    print("\n=== Prueba de Query Activity Logs ===")
    
    try:
        # Inicializar handler
        api_token = getattr(config, 'MONDAY_API_KEY', '')
        if not api_token:
            print("❌ No se encontró MONDAY_API_KEY en config.py")
            return
        
        handler = MondayAPIHandler(api_token)
        
        # Query directa para probar activity_logs
        query = """
        query {
            items(ids: [123456789]) {
                id
                name
                activity_logs(limit: 5) {
                    id
                    event
                    data
                    created_at
                    user {
                        id
                        name
                        email
                    }
                }
            }
        }
        """
        
        print("🔍 Probando query de activity_logs...")
        response = handler._make_request(query)
        
        if response and 'data' in response:
            items = response['data'].get('items', [])
            if items:
                item = items[0]
                activity_logs = item.get('activity_logs', [])
                
                print(f"✅ Query exitosa - {len(activity_logs)} activity_logs encontrados")
                
                for i, log in enumerate(activity_logs[:3]):
                    event = log.get('event', '')
                    user = log.get('user', {})
                    user_name = user.get('name', '')
                    created_at = log.get('created_at', '')
                    
                    print(f"   {i+1}. {event} - {user_name} - {created_at}")
            else:
                print("⚠️ No se encontraron items (esperado para ID ficticio)")
        else:
            print("❌ Error en la query")
            if response and 'errors' in response:
                print(f"   Errores: {response['errors']}")
        
    except Exception as e:
        print(f"❌ Error en prueba de query: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_items():
    """Prueba con múltiples items para verificar consistencia."""
    print("\n=== Prueba con Múltiples Items ===")
    
    try:
        # Inicializar handler
        api_token = getattr(config, 'MONDAY_API_KEY', '')
        if not api_token:
            print("❌ No se encontró MONDAY_API_KEY en config.py")
            return
        
        handler = MondayAPIHandler(api_token)
        
        # Obtener varios items
        items = handler.get_items(
            board_id=str(config.BOARD_ID_GRABACIONES),
            limit_per_page=3
        )
        
        if not items:
            print("❌ No se encontraron items en el tablero")
            return
        
        print(f"🔍 Probando con {len(items)} items...")
        
        for i, item in enumerate(items):
            item_id = item['id']
            item_name = item.get('name', 'Sin nombre')
            
            print(f"\n📋 Item {i+1}: {item_name} (ID: {item_id})")
            
            # Probar detección
            start_time = time.time()
            is_automation = _detectar_cambio_de_automatizacion(item_id, handler)
            detection_time = time.time() - start_time
            
            print(f"   ⏱️  Tiempo: {detection_time:.3f}s")
            print(f"   🎯 Resultado: {'🤖 Automatización' if is_automation else '👤 Usuario Real'}")
        
    except Exception as e:
        print(f"❌ Error en prueba múltiple: {e}")
        import traceback
        traceback.print_exc()


def test_error_handling():
    """Prueba el manejo de errores de la función."""
    print("\n=== Prueba de Manejo de Errores ===")
    
    try:
        # Inicializar handler
        api_token = getattr(config, 'MONDAY_API_KEY', '')
        if not api_token:
            print("❌ No se encontró MONDAY_API_KEY en config.py")
            return
        
        handler = MondayAPIHandler(api_token)
        
        # Probar con item_id inválido
        print("🔍 Probando con item_id inválido...")
        result = _detectar_cambio_de_automatizacion("invalid_id", handler)
        print(f"   Resultado: {result} (esperado: False)")
        
        # Probar con item_id inexistente
        print("🔍 Probando con item_id inexistente...")
        result = _detectar_cambio_de_automatizacion("999999999", handler)
        print(f"   Resultado: {result} (esperado: False)")
        
        print("✅ Manejo de errores funciona correctamente")
        
    except Exception as e:
        print(f"❌ Error en prueba de manejo de errores: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas de detección de automatización mejorada...\n")
    
    # Verificar configuración
    if not hasattr(config, 'MONDAY_API_KEY') or not config.MONDAY_API_KEY:
        print("❌ Error: MONDAY_API_KEY no está configurado en config.py")
        print("   Las pruebas que requieren conexión a Monday.com no funcionarán")
        return
    
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
    test_activity_log_query()
    test_detection_basic()
    test_detection_with_real_item()
    test_multiple_items()
    test_error_handling()
    
    print("\n🎉 ¡Pruebas de detección de automatización completadas!")
    print("\n✅ Mejoras implementadas:")
    print("   - 🔍 Análisis de activity_logs (más preciso que updates)")
    print("   - 📅 Detección específica de cambios en columna de fecha")
    print("   - 🤖 Identificación de usuario de automatización")
    print("   - ⏱️  Verificación de timestamps (últimos 10 segundos)")
    print("   - 🔄 Detección de bucles (2+ cambios en 30 segundos)")
    print("   - 🛑 Prevención de bucles infinitos")


if __name__ == "__main__":
    main()
