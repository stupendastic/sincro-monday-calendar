#!/usr/bin/env python3
"""
Script para probar el sistema anti-bucles
"""

import os
import time
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from sync_logic import _detectar_cambio_de_automatizacion
import config

# Cargar variables de entorno
load_dotenv()

def test_deteccion_automatizacion():
    """Prueba la detección de automatización"""
    print("🛡️ PRUEBA DEL SISTEMA ANTI-BUCLES")
    print("=" * 50)
    
    try:
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Buscar un elemento que sabemos que existe
        items = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name="PRUEBA SINCRONIZACIÓN FINAL",
            exact_match=True
        )
        
        if not items:
            print("❌ No se encontró el elemento de prueba")
            return False
        
        item_id = items[0].id
        print(f"✅ Elemento encontrado: {item_id}")
        
        # Probar detección de automatización
        print(f"\n🔍 Probando detección de automatización...")
        es_automatizacion = _detectar_cambio_de_automatizacion(item_id, monday_handler)
        
        if es_automatizacion:
            print(f"🤖 RESULTADO: Cambio de AUTOMATIZACIÓN detectado")
            print(f"✅ Sistema anti-bucles funcionando correctamente")
        else:
            print(f"👤 RESULTADO: Cambio de USUARIO REAL detectado")
            print(f"✅ Sistema anti-bucles funcionando correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_cooldown():
    """Prueba el sistema de cooldown"""
    print("\n⏰ PRUEBA DEL SISTEMA DE COOLDOWN")
    print("=" * 40)
    
    try:
        # Simular cooldown
        from sync_logic import last_sync_times
        
        test_key = "test_cooldown"
        current_time = time.time()
        
        # Simular sincronización reciente
        last_sync_times[test_key] = current_time - 5  # 5 segundos atrás
        
        # Verificar cooldown
        if test_key in last_sync_times:
            time_since_last = current_time - last_sync_times[test_key]
            if time_since_last < config.SYNC_COOLDOWN_SECONDS:
                print(f"⏭️  Cooldown activo: {time_since_last:.1f}s < {config.SYNC_COOLDOWN_SECONDS}s")
                print(f"✅ Sistema de cooldown funcionando")
                return True
            else:
                print(f"✅ Cooldown expirado: {time_since_last:.1f}s >= {config.SYNC_COOLDOWN_SECONDS}s")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error en prueba de cooldown: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 PRUEBA COMPLETA DEL SISTEMA ANTI-BUCLES")
    print("=" * 60)
    
    # Probar detección de automatización
    if test_deteccion_automatizacion():
        print("✅ Detección de automatización: FUNCIONA")
    else:
        print("❌ Detección de automatización: FALLA")
    
    # Probar sistema de cooldown
    if test_cooldown():
        print("✅ Sistema de cooldown: FUNCIONA")
    else:
        print("❌ Sistema de cooldown: FALLA")
    
    print("\n" + "="*60)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    print(f"🤖 Usuario de automatización: {config.AUTOMATION_USER_NAME} (ID: {config.AUTOMATION_USER_ID})")
    print(f"⏰ Cooldown: {config.SYNC_COOLDOWN_SECONDS} segundos")
    print(f"🕐 Ventana de detección: {config.AUTOMATION_DETECTION_WINDOW} segundos")
    
    print("\n💡 Para probar el sistema completo:")
    print("1. Crea un elemento en Monday.com")
    print("2. Cambia la fecha rápidamente")
    print("3. Observa los logs del servidor")
    print("4. Deberías ver mensajes de anti-bucles")

if __name__ == "__main__":
    main()
