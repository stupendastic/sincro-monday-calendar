#!/usr/bin/env python3
"""
Script para verificar el estado del item en Monday.com
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def verificar_item_monday():
    """Verifica el estado del item en Monday.com"""
    
    print("🔍 VERIFICANDO ITEM EN MONDAY.COM")
    print("=" * 60)
    
    # Obtener servicio de Monday
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    if not monday_handler:
        print("❌ No se pudo obtener el servicio de Monday")
        return False
    
    try:
        # Buscar el item específico
        item_id = "9881971936"
        print(f"🔍 Buscando item {item_id} en Monday.com...")
        
        # Obtener información del item
        items = monday_handler.get_items(
            board_id=str(config.BOARD_ID_GRABACIONES),
            column_ids=[config.COL_FECHA, config.COL_GOOGLE_EVENT_ID]
        )
        
        if not items:
            print("❌ No se encontraron items en Monday.com")
            return False
        
        # Buscar el item específico
        item = None
        for i in items:
            if str(i.get('id')) == item_id:
                item = i
                break
        
        if not item:
            print(f"❌ No se encontró el item {item_id}")
            return False
        
        print(f"✅ Item encontrado: {item.get('name', 'Sin nombre')}")
        print(f"   ID: {item.get('id')}")
        
        # Mostrar valores de las columnas
        column_values = item.get('column_values', [])
        for col in column_values:
            col_id = col.get('id')
            if col_id == config.COL_FECHA:
                value = col.get('text', 'Sin valor')
                print(f"   Fecha: {value}")
            elif col_id == config.COL_GOOGLE_EVENT_ID:
                value = col.get('text', 'Sin valor')
                print(f"   Google Event ID: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando item: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 VERIFICADOR DE ITEM MONDAY.COM")
    print("=" * 80)
    
    success = verificar_item_monday()
    
    if success:
        print("\n✅ Item verificado correctamente")
    else:
        print("\n❌ Error verificando item")

if __name__ == "__main__":
    main()
