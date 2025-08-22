#!/usr/bin/env python3
"""
Script para listar todos los items del tablero
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from config import BOARD_ID_GRABACIONES

def listar_items_monday():
    """Lista todos los items del tablero"""
    
    print("📋 LISTANDO ITEMS DEL TABLERO")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Inicializar servicios
    monday_token = os.getenv('MONDAY_API_KEY')
    if not monday_token:
        print("❌ No se encontró MONDAY_API_KEY en las variables de entorno")
        return
    
    monday_handler = MondayAPIHandler(monday_token)
    
    try:
        # Obtener todos los items del tablero
        print(f"🔍 Buscando items en tablero: {BOARD_ID_GRABACIONES}")
        
        query = f"""
        query {{
            boards(ids: [{BOARD_ID_GRABACIONES}]) {{
                items_page(limit: 50) {{
                    items {{
                        id
                        name
                        column_values {{
                            id
                            text
                            value
                        }}
                    }}
                }}
            }}
        }}
        """
        
        result = monday_handler._make_request(query)
        
        if not result or not result.get('data', {}).get('boards'):
            print("❌ No se pudo obtener datos del tablero")
            return
        
        board = result['data']['boards'][0]
        items = board['items_page']['items']
        
        print(f"✅ Encontrados {len(items)} items:")
        print("-" * 60)
        
        for i, item in enumerate(items, 1):
            item_id = item['id']
            item_name = item['name']
            
            # Buscar columnas relevantes
            fecha = "No fecha"
            google_id = "No ID"
            
            for column in item.get('column_values', []):
                if column.get('id') == 'fecha56':
                    fecha = column.get('text', 'No fecha')
                elif column.get('id') == 'text_mktfdhm3':
                    google_id = column.get('text', 'No ID')
            
            print(f"{i:2d}. {item_name}")
            print(f"    ID: {item_id}")
            print(f"    Fecha: {fecha}")
            print(f"    Google ID: {google_id}")
            print()
        
        if not items:
            print("❌ No hay items en el tablero")
            
    except Exception as e:
        print(f"❌ Error obteniendo items: {e}")

def main():
    """Función principal"""
    print("📋 LISTADOR DE ITEMS DE MONDAY.COM")
    print("=" * 60)
    
    try:
        listar_items_monday()
    except KeyboardInterrupt:
        print("\n👋 Listado cancelado")
    except Exception as e:
        print(f"❌ Error durante el listado: {e}")

if __name__ == "__main__":
    main()
