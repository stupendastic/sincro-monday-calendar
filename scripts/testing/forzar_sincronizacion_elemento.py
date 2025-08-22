#!/usr/bin/env python3
"""
Script para forzar la sincronización de un elemento específico de Monday a Google Calendar.
"""

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service
from sync_logic import sincronizar_item_especifico
import config

# Cargar variables de entorno
load_dotenv()

def forzar_sincronizacion_elemento(item_name):
    """Fuerza la sincronización de un elemento específico"""
    print(f"🔄 FORZANDO SINCRONIZACIÓN: {item_name}")
    print("=" * 50)
    
    try:
        # Inicializar servicios
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        google_service = get_calendar_service()
        
        # Buscar el elemento por nombre
        print(f"🔍 Buscando elemento: {item_name}")
        items = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name=item_name,
            exact_match=True
        )
        
        if not items:
            print(f"❌ Elemento '{item_name}' no encontrado")
            return False
        
        item = items[0]
        item_id = item.id
        print(f"✅ Elemento encontrado: {item_id}")
        
        # Verificar si ya tiene Google Event ID
        print(f"🔄 Verificando si el elemento ya tiene Google Event ID...")
        
        # Buscar el elemento en la lista de items para obtener sus column_values
        items_list = monday_handler.get_items(str(config.BOARD_ID_GRABACIONES))
        item_details = None
        
        for item in items_list:
            if item.get('id') == item_id:
                item_details = item
                break
        
        if item_details:
            column_values = item_details.get('column_values', [])
            google_event_id = None
            
            for col in column_values:
                if col.get('id') == config.COLUMN_MAP_REVERSE.get('ID Evento Google'):
                    google_event_id = col.get('text')
                    break
            
            if google_event_id:
                print(f"⚠️  Elemento ya tiene Google Event ID: {google_event_id}")
                print("¿Quieres forzar la sincronización de todas formas? (s/n): ", end="")
                respuesta = input().lower()
                if respuesta != 's':
                    print("❌ Sincronización cancelada")
                    return False
        
        # Forzar sincronización
        print(f"🔄 Iniciando sincronización forzada...")
        success = sincronizar_item_especifico(
            item_id=item_id,
            monday_handler=monday_handler,
            google_service=google_service
        )
        
        if success:
            print(f"✅ Sincronización forzada exitosa para {item_name}")
            
            # Verificar resultado
            print(f"🔄 Verificando resultado de la sincronización...")
            
            # Buscar el elemento actualizado
            items_list_actualizado = monday_handler.get_items(str(config.BOARD_ID_GRABACIONES))
            item_details_actualizado = None
            
            for item in items_list_actualizado:
                if item.get('id') == item_id:
                    item_details_actualizado = item
                    break
            
            if item_details_actualizado:
                column_values = item_details_actualizado.get('column_values', [])
                google_event_id_nuevo = None
                
                for col in column_values:
                    if col.get('id') == config.COLUMN_MAP_REVERSE.get('ID Evento Google'):
                        google_event_id_nuevo = col.get('text')
                        break
                
                if google_event_id_nuevo:
                    print(f"✅ Google Event ID asignado: {google_event_id_nuevo}")
                    
                    # Verificar que existe en Google Calendar
                    try:
                        google_event = google_service.events().get(
                            calendarId=config.MASTER_CALENDAR_ID,
                            eventId=google_event_id_nuevo
                        ).execute()
                        print(f"✅ Evento confirmado en Google Calendar")
                        print(f"📅 Fecha: {google_event.get('start', {}).get('dateTime', 'Sin fecha')}")
                        return True
                    except Exception as e:
                        print(f"❌ Evento NO existe en Google Calendar: {e}")
                        return False
                else:
                    print("❌ No se asignó Google Event ID")
                    return False
            else:
                print("❌ No se pudo verificar el resultado")
                return False
        else:
            print(f"❌ Error en sincronización forzada")
            return False
            
    except Exception as e:
        print(f"❌ Error forzando sincronización: {e}")
        return False

def listar_elementos_recientes():
    """Lista elementos recientes para facilitar la selección"""
    print("📋 ELEMENTOS RECIENTES EN MONDAY")
    print("=" * 40)
    
    try:
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        
        # Obtener elementos recientes
        items = monday_handler.get_items(
            board_id=str(config.BOARD_ID_GRABACIONES)
        )
        
        # Mostrar solo los primeros 10
        items = items[:10]
        
        if items:
            print("Elementos encontrados:")
            for i, item in enumerate(items, 1):
                print(f"{i}. {item.name} (ID: {item.id})")
        else:
            print("❌ No se encontraron elementos")
            
    except Exception as e:
        print(f"❌ Error listando elementos: {e}")

def main():
    """Función principal"""
    print("🚀 FORZAR SINCRONIZACIÓN MONDAY → GOOGLE")
    print("=" * 50)
    
    # Listar elementos recientes
    listar_elementos_recientes()
    
    print("\n💡 OPCIONES:")
    print("1. Forzar sincronización de 'ARNAU PRUEBAS CALENDARIO 2'")
    print("2. Forzar sincronización de 'ARNAU PRUEBAS CALENDARIO 7'")
    print("3. Introducir nombre manualmente")
    print("4. Salir")
    
    opcion = input("\nSelecciona una opción (1-4): ").strip()
    
    if opcion == "1":
        forzar_sincronizacion_elemento("ARNAU PRUEBAS CALENDARIO 2")
    elif opcion == "2":
        forzar_sincronizacion_elemento("ARNAU PRUEBAS CALENDARIO 7")
    elif opcion == "3":
        nombre = input("Introduce el nombre del elemento: ").strip()
        if nombre:
            forzar_sincronizacion_elemento(nombre)
        else:
            print("❌ Nombre no válido")
    elif opcion == "4":
        print("👋 ¡Hasta luego!")
    else:
        print("❌ Opción no válida")

if __name__ == "__main__":
    main()
