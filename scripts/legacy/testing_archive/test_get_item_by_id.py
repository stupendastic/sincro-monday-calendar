#!/usr/bin/env python3
"""
Script de prueba para verificar el método get_item_by_id optimizado.
"""

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from monday_api_handler import MondayAPIHandler
import config

def test_get_item_by_id(api_token):
    """Prueba el método get_item_by_id con un item específico."""
    
    print("🧪 Probando método get_item_by_id optimizado...")
    
    # Crear handler
    handler = MondayAPIHandler(api_token=api_token)
    
    # Item de prueba (el que se usó en el webhook)
    test_item_id = "9882299305"
    
    print(f"📋 Obteniendo item {test_item_id}...")
    
    try:
        # Obtener item específico
        item_data = handler.get_item_by_id(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_id=test_item_id,
            column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name"]
        )
        
        if item_data:
            print("✅ Item obtenido exitosamente!")
            print(f"   ID: {item_data.get('id')}")
            print(f"   Nombre: {item_data.get('name')}")
            
            # Mostrar column values
            column_values = item_data.get('column_values', [])
            print(f"   Columnas obtenidas: {len(column_values)}")
            
            for col in column_values:
                col_id = col.get('id', '')
                col_text = col.get('text', '')
                print(f"     {col_id}: {col_text}")
            
            return True
        else:
            print("❌ No se pudo obtener el item")
            return False
            
    except Exception as e:
        print(f"❌ Error obteniendo item: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_items_comparison(api_token):
    """Compara el rendimiento entre get_items y get_item_by_id."""
    
    print("\n⚡ Comparando rendimiento...")
    
    handler = MondayAPIHandler(api_token=api_token)
    test_item_id = "9882299305"
    
    import time
    
    # Test get_item_by_id (optimizado)
    print("🔄 Probando get_item_by_id...")
    start_time = time.time()
    
    try:
        item_data = handler.get_item_by_id(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_id=test_item_id,
            column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name"]
        )
        optimized_time = time.time() - start_time
        print(f"   ✅ Tiempo: {optimized_time:.3f} segundos")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        optimized_time = float('inf')
    
    # Test get_items (método anterior)
    print("🔄 Probando get_items (método anterior)...")
    start_time = time.time()
    
    try:
        all_items = handler.get_items(
            board_id=str(config.BOARD_ID_GRABACIONES),
            column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name"],
            limit_per_page=100
        )
        
        # Filtrar por item_id
        item_data = None
        for item in all_items:
            if str(item.get('id')) == test_item_id:
                item_data = item
                break
                
        old_time = time.time() - start_time
        print(f"   ✅ Tiempo: {old_time:.3f} segundos")
        print(f"   📊 Items escaneados: {len(all_items)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        old_time = float('inf')
    
    # Comparación
    if optimized_time < float('inf') and old_time < float('inf'):
        improvement = (old_time - optimized_time) / old_time * 100
        print(f"\n🎯 Mejora de rendimiento: {improvement:.1f}% más rápido")
        print(f"   Optimizado: {optimized_time:.3f}s")
        print(f"   Anterior: {old_time:.3f}s")

def main():
    """Función principal."""
    print("🚀 Iniciando pruebas del método get_item_by_id optimizado...\n")
    
    # Verificar configuración
    monday_api_key = os.getenv('MONDAY_API_KEY')
    if not monday_api_key:
        print("❌ Error: MONDAY_API_KEY no está configurado en .env")
        return
    
    if not hasattr(config, 'BOARD_ID_GRABACIONES'):
        print("❌ Error: BOARD_ID_GRABACIONES no está configurado en config.py")
        return
    
    print(f"✅ Configuración verificada:")
    print(f"   - Board ID: {config.BOARD_ID_GRABACIONES}")
    print(f"   - API Key: {'*' * 10 + monday_api_key[-4:] if monday_api_key else 'No configurado'}\n")
    
    # Ejecutar pruebas
    success = test_get_item_by_id(monday_api_key)
    
    if success:
        test_get_items_comparison(monday_api_key)
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    main()
