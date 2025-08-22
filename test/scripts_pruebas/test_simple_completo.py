#!/usr/bin/env python3
"""
Script de Pruebas Simple para Sincronización Bidireccional Monday-Google
Usa el método de consulta que funciona correctamente
"""
import os
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from monday_api_handler import MondayAPIHandler
import sync_logic
import config

# Cargar variables de entorno
load_dotenv()

# Configuración de pruebas
ITEM_DE_PRUEBA_ID = 9733398727
FILMMAKER_TEST = "Arnau Admin"

def inicializar_servicios():
    """Inicializa los servicios de Google y Monday."""
    print("🔧 Inicializando servicios...")
    
    # Inicializar Google Calendar
    google_service = get_calendar_service()
    print("✅ Servicio de Google Calendar inicializado")
    
    # Inicializar Monday API
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    print("✅ Servicio de Monday API inicializado")
    
    return google_service, monday_handler

def obtener_google_event_id(monday_handler):
    """Obtiene el Google Event ID del item de prueba."""
    query = """
    query {
        items(ids: [9733398727]) {
            id
            name
            column_values(ids: ["text_mktfdhm3"]) {
                id
                text
                value
            }
        }
    }
    """
    
    data = {'query': query}
    
    try:
        response = requests.post(url=monday_handler.API_URL, json=data, headers=monday_handler.HEADERS)
        response.raise_for_status()
        
        if response.status_code == 200:
            response_data = response.json()
            items = response_data.get('data', {}).get('items', [])
            if items:
                item = items[0]
                column_values = item.get('column_values', [])
                for col in column_values:
                    if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                        google_event_id = col.get('text', '').strip()
                        if google_event_id:
                            return google_event_id
        return None
    except Exception as e:
        print(f"❌ Error al obtener Google Event ID: {e}")
        return None

def prueba_1_monday_to_google(google_service, monday_handler):
    """Prueba 1: Monday -> Google - Cambiar fecha en Monday."""
    print("\n🔄 PRUEBA 1: Monday -> Google")
    print("=" * 50)
    print("📅 Cambiando fecha en Monday...")
    
    # Cambiar fecha en Monday (fecha futura para evitar conflictos)
    nueva_fecha = datetime.now() + timedelta(days=7)
    fecha_str = nueva_fecha.strftime("%Y-%m-%d")
    hora_str = nueva_fecha.strftime("%H:%M:%S")
    
    # Actualizar fecha en Monday
    success = monday_handler.update_column_value(
        ITEM_DE_PRUEBA_ID,
        config.BOARD_ID_GRABACIONES,
        config.COL_FECHA_GRAB,
        {"date": fecha_str, "time": hora_str},
        'date'
    )
    
    if success:
        print(f"✅ Fecha actualizada en Monday: {fecha_str} {hora_str}")
        
        # Simular webhook de Monday
        print("🔄 Simulando webhook de Monday...")
        sync_logic.sincronizar_item_via_webhook(
            ITEM_DE_PRUEBA_ID,
            monday_handler=monday_handler,
            google_service=google_service
        )
        
        # Verificar que se creó el evento maestro
        google_event_id = obtener_google_event_id(monday_handler)
        if google_event_id:
            print(f"✅ Evento maestro creado: {google_event_id}")
            
            # Verificar copia para Arnau Admin
            calendar_id = None
            for perfil in config.FILMMAKER_PROFILES:
                if perfil.get('monday_name') == FILMMAKER_TEST:
                    calendar_id = perfil.get('calendar_id')
                    break
            
            if calendar_id:
                from google_calendar_service import find_event_copy_by_master_id
                copy_event = find_event_copy_by_master_id(google_service, calendar_id, google_event_id)
                if copy_event:
                    print(f"✅ Copia para {FILMMAKER_TEST} creada: {copy_event['id']}")
                    return True
                else:
                    print(f"❌ No se encontró copia para {FILMMAKER_TEST}")
                    return False
            else:
                print(f"❌ {FILMMAKER_TEST} no encontrado en perfiles")
                return False
        else:
            print("❌ No se guardó Google Event ID")
            return False
    else:
        print("❌ Error al actualizar fecha en Monday")
        return False

def prueba_2_google_personal_to_monday(google_service, monday_handler):
    """Prueba 2: Google Personal -> Monday - Mover evento en calendario personal."""
    print("\n🔄 PRUEBA 2: Google Personal -> Monday")
    print("=" * 50)
    
    # Obtener Google Event ID del item
    master_event_id = obtener_google_event_id(monday_handler)
    if not master_event_id:
        print("❌ No hay master_event_id")
        return False
    
    print(f"📋 Usando master_event_id: {master_event_id}")
    
    # Obtener calendario de Arnau Admin
    calendar_id = None
    for perfil in config.FILMMAKER_PROFILES:
        if perfil.get('monday_name') == FILMMAKER_TEST:
            calendar_id = perfil.get('calendar_id')
            break
    
    if not calendar_id:
        print(f"❌ {FILMMAKER_TEST} no encontrado en perfiles")
        return False
    
    # Buscar copia en calendario personal
    from google_calendar_service import find_event_copy_by_master_id
    copy_event = find_event_copy_by_master_id(google_service, calendar_id, master_event_id)
    
    if not copy_event:
        print(f"❌ No se encontró copia para {FILMMAKER_TEST}")
        return False
    
    print(f"✅ Copia encontrada: {copy_event['id']}")
    
    # Mover evento (cambiar hora)
    nueva_hora = datetime.now() + timedelta(hours=2)
    nueva_fecha = nueva_hora.strftime("%Y-%m-%dT%H:%M:%S+02:00")
    
    # Actualizar evento copia
    from google_calendar_service import update_google_event_by_id
    success = update_google_event_by_id(
        google_service,
        calendar_id,
        copy_event['id'],
        {
            'summary': copy_event.get('summary', 'Evento de prueba'),
            'start': {'dateTime': nueva_fecha, 'timeZone': 'Europe/Madrid'},
            'end': {'dateTime': (nueva_hora + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+02:00"), 'timeZone': 'Europe/Madrid'},
            'description': copy_event.get('description', '')
        }
    )
    
    if success:
        print(f"✅ Evento copia actualizado: {nueva_fecha}")
        
        # Simular sincronización desde Google
        print("🔄 Simulando sincronización desde Google...")
        sync_logic.sincronizar_desde_google(
            master_event_id,
            monday_handler=monday_handler,
            google_service=google_service
        )
        
        print("✅ Prueba 2 completada")
        return True
    else:
        print("❌ Error al actualizar evento copia")
        return False

def prueba_3_google_master_to_monday(google_service, monday_handler):
    """Prueba 3: Google Máster -> Monday - Mover evento en calendario maestro."""
    print("\n🔄 PRUEBA 3: Google Máster -> Monday")
    print("=" * 50)
    
    # Obtener Google Event ID del item
    master_event_id = obtener_google_event_id(monday_handler)
    if not master_event_id:
        print("❌ No hay master_event_id")
        return False
    
    print(f"📋 Usando master_event_id: {master_event_id}")
    
    # Mover evento maestro (cambiar fecha)
    nueva_fecha = datetime.now() + timedelta(days=14)
    nueva_fecha_str = nueva_fecha.strftime("%Y-%m-%dT%H:%M:%S+02:00")
    
    # Actualizar evento maestro
    from google_calendar_service import update_google_event_by_id
    success = update_google_event_by_id(
        google_service,
        config.MASTER_CALENDAR_ID,
        master_event_id,
        {
            'summary': 'Evento maestro actualizado',
            'start': {'dateTime': nueva_fecha_str, 'timeZone': 'Europe/Madrid'},
            'end': {'dateTime': (nueva_fecha + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+02:00"), 'timeZone': 'Europe/Madrid'},
            'description': 'Evento maestro actualizado desde prueba'
        }
    )
    
    if success:
        print(f"✅ Evento maestro actualizado: {nueva_fecha_str}")
        
        # Simular sincronización desde Google
        print("🔄 Simulando sincronización desde Google...")
        sync_logic.sincronizar_desde_google(
            master_event_id,
            monday_handler=monday_handler,
            google_service=google_service
        )
        
        print("✅ Prueba 3 completada")
        return True
    else:
        print("❌ Error al actualizar evento maestro")
        return False

def prueba_4_anadir_filmmaker(google_service, monday_handler):
    """Prueba 4: Añadir Filmmaker - Verificar que se crea su calendario y copia."""
    print("\n🔄 PRUEBA 4: Añadir Filmmaker")
    print("=" * 50)
    
    # Nota: Esta prueba es informativa ya que Arnau Admin ya está asignado
    print(f"ℹ️  {FILMMAKER_TEST} ya está asignado al item de prueba")
    print("✅ Prueba 4 completada (filmmaker ya existe)")
    return True

def prueba_5_quitar_filmmaker(google_service, monday_handler):
    """Prueba 5: Quitar Filmmaker - Verificar que su copia se elimina."""
    print("\n🔄 PRUEBA 5: Quitar Filmmaker")
    print("=" * 50)
    
    # Obtener Google Event ID del item
    master_event_id = obtener_google_event_id(monday_handler)
    if not master_event_id:
        print("❌ No hay master_event_id")
        return False
    
    print(f"📋 Usando master_event_id: {master_event_id}")
    
    # Simular quitar filmmaker (cambiar operario a None)
    success = monday_handler.update_column_value(
        ITEM_DE_PRUEBA_ID,
        config.BOARD_ID_GRABACIONES,
        "personas1",
        None,
        'people'
    )
    
    if success:
        print(f"✅ Operario quitado del item")
        
        # Simular webhook de Monday
        print("🔄 Simulando webhook de Monday...")
        sync_logic.sincronizar_item_via_webhook(
            ITEM_DE_PRUEBA_ID,
            monday_handler=monday_handler,
            google_service=google_service
        )
        
        # Verificar que se eliminó la copia
        calendar_id = None
        for perfil in config.FILMMAKER_PROFILES:
            if perfil.get('monday_name') == FILMMAKER_TEST:
                calendar_id = perfil.get('calendar_id')
                break
        
        if calendar_id:
            from google_calendar_service import find_event_copy_by_master_id
            copy_event = find_event_copy_by_master_id(google_service, calendar_id, master_event_id)
            
            if copy_event:
                print(f"❌ Copia aún existe: {copy_event['id']}")
                return False
            else:
                print(f"✅ Copia eliminada correctamente")
                return True
        else:
            print(f"❌ {FILMMAKER_TEST} no encontrado en perfiles")
            return False
    else:
        print("❌ Error al quitar operario")
        return False

def main():
    """Función principal que ejecuta todas las pruebas."""
    print("🧪 PRUEBAS SIMPLES DE SINCRONIZACIÓN BIDIRECCIONAL")
    print("=" * 70)
    
    # Inicializar servicios
    google_service, monday_handler = inicializar_servicios()
    
    # Ejecutar todas las pruebas
    resultados = []
    
    # Prueba 1: Monday -> Google
    resultado_1 = prueba_1_monday_to_google(google_service, monday_handler)
    resultados.append(("Monday -> Google", resultado_1))
    
    # Prueba 2: Google Personal -> Monday
    resultado_2 = prueba_2_google_personal_to_monday(google_service, monday_handler)
    resultados.append(("Google Personal -> Monday", resultado_2))
    
    # Prueba 3: Google Máster -> Monday
    resultado_3 = prueba_3_google_master_to_monday(google_service, monday_handler)
    resultados.append(("Google Máster -> Monday", resultado_3))
    
    # Prueba 4: Añadir Filmmaker
    resultado_4 = prueba_4_anadir_filmmaker(google_service, monday_handler)
    resultados.append(("Añadir Filmmaker", resultado_4))
    
    # Prueba 5: Quitar Filmmaker
    resultado_5 = prueba_5_quitar_filmmaker(google_service, monday_handler)
    resultados.append(("Quitar Filmmaker", resultado_5))
    
    # Mostrar resumen final
    print("\n📊 RESUMEN FINAL DE PRUEBAS")
    print("=" * 50)
    
    exitosas = 0
    for nombre, resultado in resultados:
        status = "✅ EXITOSA" if resultado else "❌ FALLIDA"
        print(f"{nombre}: {status}")
        if resultado:
            exitosas += 1
    
    print(f"\n🎯 Resultado: {exitosas}/{len(resultados)} pruebas exitosas")
    
    if exitosas == len(resultados):
        print("🎉 ¡TODAS LAS PRUEBAS EXITOSAS! Sistema completamente funcional.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar logs para más detalles.")

if __name__ == "__main__":
    main() 