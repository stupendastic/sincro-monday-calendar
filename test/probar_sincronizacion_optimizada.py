#!/usr/bin/env python3
"""
Script para probar la sincronización optimizada
"""
import os
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service
import config

def probar_sincronizacion_optimizada():
    """Prueba la sincronización optimizada"""
    
    print("🧪 PROBANDO SINCRONIZACIÓN OPTIMIZADA")
    print("=" * 50)
    
    load_dotenv()
    
    # Inicializar servicios
    monday_token = os.getenv('MONDAY_API_KEY')
    if not monday_token:
        print("❌ No se encontró MONDAY_API_KEY")
        return
    
    monday_handler = MondayAPIHandler(monday_token)
    google_service = get_calendar_service()
    
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return
    
    print("✅ Servicios inicializados")
    
    # Probar búsqueda optimizada por Google Event ID
    print("\n🔍 PROBANDO BÚSQUEDA OPTIMIZADA")
    print("-" * 30)
    
    # Buscar el evento "Prueba Arnau Calendar Sync 1"
    event_id = "kqu8tv7mo0b0s1lsqmh4pqcs90"
    
    print(f"🎯 Buscando item con Google Event ID: {event_id}")
    
    # Importar la función optimizada
    from sync_logic import _obtener_item_id_por_google_event_id_optimizado
    
    item_id = _obtener_item_id_por_google_event_id_optimizado(event_id, monday_handler)
    
    if item_id:
        print(f"✅ Item encontrado: {item_id}")
        
        # Obtener detalles del item
        query = f"""
        query {{
            items(ids: [{item_id}]) {{
                id
                name
                column_values(ids: ["fecha56", "text_mktfdhm3"]) {{
                    id
                    text
                }}
            }}
        }}
        """
        
        data = monday_handler._make_request(query)
        if data and 'items' in data and data['items']:
            item = data['items'][0]
            print(f"📋 Nombre: {item['name']}")
            
            for col in item['column_values']:
                if col['id'] == 'fecha56':
                    print(f"📅 Fecha: {col.get('text', 'No fecha')}")
                elif col['id'] == 'text_mktfdhm3':
                    print(f"🆔 Google ID: {col.get('text', 'No ID')}")
    else:
        print("❌ Item no encontrado")
    
    # Probar búsqueda por nombre
    print("\n🔍 PROBANDO BÚSQUEDA POR NOMBRE")
    print("-" * 30)
    
    from sync_logic import _obtener_item_id_por_nombre
    
    item_name = "Prueba Arnau Calendar Sync 1"
    print(f"🎯 Buscando item por nombre: {item_name}")
    
    item_id_nombre = _obtener_item_id_por_nombre(item_name, monday_handler)
    
    if item_id_nombre:
        print(f"✅ Item encontrado por nombre: {item_id_nombre}")
    else:
        print("❌ Item no encontrado por nombre")

if __name__ == "__main__":
    probar_sincronizacion_optimizada()
