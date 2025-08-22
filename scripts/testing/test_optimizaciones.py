#!/usr/bin/env python3
"""
Script para probar las nuevas optimizaciones:
1. Búsqueda optimizada de items
2. Detección de automatización para evitar bucles
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_busqueda_optimizada():
    """Prueba la nueva búsqueda optimizada vs la anterior."""
    print("🚀 PRUEBA DE BÚSQUEDA OPTIMIZADA")
    print("=" * 50)
    
    try:
        # Importar módulos necesarios
        from monday_api_handler import MondayAPIHandler
        from sync_logic import (
            _obtener_item_id_por_google_event_id_optimizado,
            _obtener_item_id_por_google_event_id_mejorado
        )
        import config
        
        # Inicializar handler
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        print("✅ Monday API Handler inicializado")
        
        # ID de prueba conocido (del script anterior)
        test_google_event_id = "mnjvjb1igd0a2f6l84fipo5iuk"
        
        print(f"🔍 Buscando Google Event ID: {test_google_event_id}")
        
        # Probar método OPTIMIZADO
        print("\n⚡ MÉTODO OPTIMIZADO:")
        start_time = time.time()
        result_optimized = _obtener_item_id_por_google_event_id_optimizado(
            test_google_event_id, 
            monday_handler
        )
        optimized_time = time.time() - start_time
        print(f"   Resultado: {result_optimized}")
        print(f"   Tiempo: {optimized_time:.2f} segundos")
        
        # Probar método ANTERIOR (para comparación)
        print("\n🐌 MÉTODO ANTERIOR:")
        start_time = time.time()
        result_legacy = _obtener_item_id_por_google_event_id_mejorado(
            test_google_event_id, 
            monday_handler
        )
        legacy_time = time.time() - start_time
        print(f"   Resultado: {result_legacy}")
        print(f"   Tiempo: {legacy_time:.2f} segundos")
        
        # Comparar resultados
        print("\n📊 COMPARACIÓN:")
        print(f"   Optimizado: {optimized_time:.2f}s")
        print(f"   Anterior:   {legacy_time:.2f}s")
        
        if optimized_time < legacy_time:
            mejora = ((legacy_time - optimized_time) / legacy_time) * 100
            print(f"   🎉 ¡Mejora del {mejora:.1f}%!")
        else:
            print(f"   ⚠️  El método optimizado no fue más rápido")
        
        if result_optimized == result_legacy:
            print(f"   ✅ Ambos métodos devolvieron el mismo resultado")
        else:
            print(f"   ❌ Los métodos devolvieron resultados diferentes")
        
        return result_optimized == result_legacy
        
    except Exception as e:
        print(f"❌ Error en prueba de búsqueda: {e}")
        return False

def test_deteccion_automatizacion():
    """Prueba la detección de cambios de automatización."""
    print("\n🤖 PRUEBA DE DETECCIÓN DE AUTOMATIZACIÓN")
    print("=" * 50)
    
    try:
        # Importar módulos necesarios
        from monday_api_handler import MondayAPIHandler
        from sync_logic import _detectar_cambio_de_automatizacion
        import config
        
        # Inicializar handler
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        print("✅ Monday API Handler inicializado")
        
        # ID de prueba conocido
        test_item_id = "9733398727"
        
        print(f"🔍 Analizando item: {test_item_id}")
        print(f"🤖 Usuario de automatización: {config.AUTOMATION_USER_NAME} (ID: {config.AUTOMATION_USER_ID})")
        
        # Detectar automatización
        es_automatizacion = _detectar_cambio_de_automatizacion(test_item_id, monday_handler)
        
        if es_automatizacion:
            print("🤖 ✅ Automatización DETECTADA - Se frenaría el bucle")
        else:
            print("👤 ✅ Usuario real detectado - Sincronización continuaría")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de automatización: {e}")
        return False

def test_sincronizacion_completa():
    """Prueba una sincronización completa con las optimizaciones."""
    print("\n🔄 PRUEBA DE SINCRONIZACIÓN COMPLETA OPTIMIZADA")
    print("=" * 50)
    
    try:
        # Importar módulos necesarios
        from google_calendar_service import get_calendar_service
        from monday_api_handler import MondayAPIHandler
        from sync_logic import sincronizar_desde_google
        
        # Inicializar servicios
        google_service = get_calendar_service()
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        print("✅ Servicios inicializados")
        
        # ID de prueba conocido
        test_master_event_id = "mnjvjb1igd0a2f6l84fipo5iuk"
        
        print(f"🔄 Sincronizando desde Google: {test_master_event_id}")
        
        # Ejecutar sincronización completa
        start_time = time.time()
        success = sincronizar_desde_google(
            test_master_event_id,
            monday_handler=monday_handler,
            google_service=google_service
        )
        total_time = time.time() - start_time
        
        print(f"\n📊 RESULTADO:")
        print(f"   Éxito: {'✅' if success else '❌'}")
        print(f"   Tiempo total: {total_time:.2f} segundos")
        
        if success and total_time < 30:  # Menos de 30 segundos es bueno
            print(f"   🎉 ¡Sincronización rápida y exitosa!")
        elif success:
            print(f"   ✅ Sincronización exitosa (tiempo aceptable)")
        else:
            print(f"   ❌ Sincronización falló")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en prueba de sincronización: {e}")
        return False

def main():
    """Ejecuta todas las pruebas de optimización."""
    print("🧪 PRUEBAS DE OPTIMIZACIONES MONDAY-GOOGLE")
    print("=" * 60)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    resultados = []
    
    # 1. Prueba de búsqueda optimizada
    try:
        resultado_busqueda = test_busqueda_optimizada()
        resultados.append(("Búsqueda Optimizada", resultado_busqueda))
    except Exception as e:
        print(f"❌ Error en prueba de búsqueda: {e}")
        resultados.append(("Búsqueda Optimizada", False))
    
    # 2. Prueba de detección de automatización
    try:
        resultado_automatizacion = test_deteccion_automatizacion()
        resultados.append(("Detección Automatización", resultado_automatizacion))
    except Exception as e:
        print(f"❌ Error en prueba de automatización: {e}")
        resultados.append(("Detección Automatización", False))
    
    # 3. Prueba de sincronización completa
    try:
        resultado_sinc = test_sincronizacion_completa()
        resultados.append(("Sincronización Completa", resultado_sinc))
    except Exception as e:
        print(f"❌ Error en prueba de sincronización: {e}")
        resultados.append(("Sincronización Completa", False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    exitos = 0
    for nombre, resultado in resultados:
        estado = "✅ ÉXITO" if resultado else "❌ FALLO"
        print(f"{nombre}: {estado}")
        if resultado:
            exitos += 1
    
    print(f"\n🎯 Total: {exitos}/{len(resultados)} pruebas exitosas")
    
    if exitos == len(resultados):
        print("🎉 ¡Todas las optimizaciones funcionan perfectamente!")
    elif exitos > 0:
        print("⚠️ Algunas optimizaciones funcionan, revisar las que fallaron")
    else:
        print("❌ Ninguna optimización funcionó, revisar implementación")
    
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
