#!/usr/bin/env python3
"""
Script para probar la sincronización Monday ↔ Google Calendar paso a paso.
Este script te guía a través del proceso de prueba.
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def check_system_status():
    """Verifica el estado del sistema."""
    print("🔍 VERIFICANDO ESTADO DEL SISTEMA")
    print("=" * 40)
    
    # 1. Verificar servidor
    try:
        response = requests.get("http://localhost:6754/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Servidor: {data.get('status', 'unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
        else:
            print(f"❌ Servidor: Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Servidor: No disponible - {e}")
        return False
    
    # 2. Verificar ngrok
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                ngrok_url = tunnels[0].get('public_url')
                print(f"✅ ngrok: {ngrok_url}")
                
                # Verificar que ngrok responde
                ngrok_health = requests.get(f"{ngrok_url}/health", timeout=5)
                if ngrok_health.status_code == 200:
                    print(f"   ✅ ngrok responde correctamente")
                else:
                    print(f"   ⚠️ ngrok no responde correctamente")
            else:
                print("❌ ngrok: No hay túneles activos")
                return False
        else:
            print(f"❌ ngrok: Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ngrok: No disponible - {e}")
        return False
    
    # 3. Verificar archivo de estado
    state_file = Path("config/sync_state.json")
    if state_file.exists():
        print(f"✅ Estado de sincronización: Disponible")
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            total_states = len(state_data.get('sync_states', {}))
            print(f"   Estados activos: {total_states}")
        except Exception as e:
            print(f"   ⚠️ Error leyendo estado: {e}")
    else:
        print(f"ℹ️ Estado de sincronización: No existe (se creará automáticamente)")
    
    print()
    return True

def get_test_item():
    """Obtiene información de un item de prueba."""
    print("📋 SELECCIONANDO ITEM DE PRUEBA")
    print("=" * 35)
    
    try:
        import config
        from monday_api_handler import MondayAPIHandler
        from dotenv import load_dotenv
        import os
        
        # Cargar variables de entorno
        load_dotenv()
        
        # Obtener API key de Monday
        monday_api_key = os.getenv('MONDAY_API_KEY')
        if not monday_api_key:
            print("❌ No se encontró MONDAY_API_KEY en las variables de entorno")
            return None
        
        # Crear handler de Monday
        handler = MondayAPIHandler(monday_api_key)
        
        # Obtener items del board
        items = handler.get_items(
            board_id=str(config.BOARD_ID_GRABACIONES),
            column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name"],
            limit_per_page=5
        )
        
        if not items:
            print("❌ No se encontraron items en Monday")
            return None
        
        print(f"✅ Encontrados {len(items)} items")
        print()
        
        # Mostrar items disponibles
        print("📝 ITEMS DISPONIBLES PARA PRUEBA:")
        for i, item in enumerate(items, 1):
            item_id = item.get('id')
            name = item.get('name', 'Sin nombre')
            google_event_id = None
            
            # Buscar Google Event ID
            for col in item.get('column_values', []):
                if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                    google_event_id = col.get('text', '').strip()
                    break
            
            status = "✅ Con Google Event ID" if google_event_id else "⚠️ Sin Google Event ID"
            print(f"   {i}. {name} (ID: {item_id}) - {status}")
            if google_event_id:
                print(f"      Google Event ID: {google_event_id}")
        
        print()
        
        # Seleccionar el primer item con Google Event ID
        for item in items:
            google_event_id = None
            for col in item.get('column_values', []):
                if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                    google_event_id = col.get('text', '').strip()
                    break
            
            if google_event_id:
                return {
                    'item_id': item.get('id'),
                    'name': item.get('name', 'Sin nombre'),
                    'google_event_id': google_event_id
                }
        
        print("⚠️ No se encontró ningún item con Google Event ID")
        return None
        
    except Exception as e:
        print(f"❌ Error obteniendo items: {e}")
        return None

def show_test_instructions(test_item):
    """Muestra las instrucciones para la prueba."""
    print("🧪 INSTRUCCIONES PARA LA PRUEBA")
    print("=" * 35)
    print()
    
    print(f"📋 ITEM SELECCIONADO:")
    print(f"   Nombre: {test_item['name']}")
    print(f"   Monday ID: {test_item['item_id']}")
    print(f"   Google Event ID: {test_item['google_event_id']}")
    print()
    
    print("🔄 PASOS PARA PROBAR SINCRONIZACIÓN:")
    print()
    print("1. 📅 CAMBIAR FECHA EN MONDAY:")
    print(f"   - Ve a Monday.com")
    print(f"   - Busca el item: '{test_item['name']}'")
    print(f"   - Cambia la fecha en la columna de fecha")
    print(f"   - Guarda el cambio")
    print()
    
    print("2. 👀 OBSERVAR LOGS:")
    print("   - Abre otra terminal")
    print("   - Ejecuta: tail -f logs/sync_system.log")
    print("   - Observa los logs cuando hagas el cambio")
    print()
    
    print("3. ✅ VERIFICAR EN GOOGLE CALENDAR:")
    print(f"   - Ve a Google Calendar")
    print(f"   - Busca el evento correspondiente")
    print(f"   - Verifica que la fecha se actualizó")
    print()
    
    print("4. 🔄 PROBAR DIRECCIÓN INVERSA:")
    print("   - Cambia la fecha en Google Calendar")
    print("   - Verifica que se actualice en Monday")
    print()
    
    print("⚠️  IMPORTANTE:")
    print("   - Solo cambia la FECHA, no otros campos")
    print("   - Espera 5-10 segundos entre cambios")
    print("   - Observa los logs para ver el proceso")
    print()
    
    return test_item

def monitor_logs():
    """Inicia el monitoreo de logs."""
    print("📊 MONITOREO DE LOGS")
    print("=" * 25)
    print()
    print("Para monitorear los logs en tiempo real:")
    print("   tail -f logs/sync_system.log")
    print()
    print("Para ver solo logs de sincronización:")
    print("   tail -f logs/sync_system.log | grep -E '(SYNC|webhook|Monday|Google)'")
    print()
    print("Para ver logs de errores:")
    print("   tail -f logs/sync_system.log | grep -E '(ERROR|WARNING|BUCLE)'")
    print()

def show_debug_commands(test_item):
    """Muestra comandos de debugging útiles."""
    print("🔧 COMANDOS DE DEBUGGING")
    print("=" * 25)
    print()
    
    print("Ver estado de sincronización:")
    print(f"   curl http://localhost:6754/debug/sync-state/{test_item['item_id']}")
    print()
    
    print("Ver últimas sincronizaciones:")
    print("   curl http://localhost:6754/debug/last-syncs")
    print()
    
    print("Limpiar estado de sincronización (si hay problemas):")
    print(f"   curl -X DELETE http://localhost:6754/debug/clear-state/{test_item['item_id']}")
    print()
    
    print("Monitor interactivo:")
    print("   python3 scripts/testing/monitor_sync_realtime.py --mode interactive")
    print()

def main():
    """Función principal."""
    print("🧪 PRUEBA DE SINCRONIZACIÓN MONDAY ↔ GOOGLE CALENDAR")
    print("=" * 60)
    print()
    
    # 1. Verificar estado del sistema
    if not check_system_status():
        print("❌ El sistema no está listo para pruebas")
        print("   Verifica que el servidor y ngrok estén funcionando")
        return
    
    # 2. Obtener item de prueba
    test_item = get_test_item()
    if not test_item:
        print("❌ No se pudo obtener un item de prueba")
        print("   Verifica que haya items en Monday con Google Event ID")
        return
    
    # 3. Mostrar instrucciones
    show_test_instructions(test_item)
    
    # 4. Mostrar monitoreo de logs
    monitor_logs()
    
    # 5. Mostrar comandos de debugging
    show_debug_commands(test_item)
    
    print("🎯 ¡LISTO PARA PROBAR!")
    print("=" * 20)
    print("Sigue las instrucciones anteriores para probar la sincronización.")
    print("Si encuentras problemas, usa los comandos de debugging.")
    print()

if __name__ == "__main__":
    main()
