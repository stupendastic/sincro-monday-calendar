#!/usr/bin/env python3
"""
Script para corregir la sincronización usando el calendario correcto
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from datetime import datetime
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from monday_api_handler import MondayAPIHandler
import config

# Cargar variables de entorno
load_dotenv()

def corregir_sincronizacion():
    """Corrige la sincronización usando el calendario correcto"""
    
    print("🔧 CORRIGIENDO SINCRONIZACIÓN")
    print("=" * 60)
    
    # Obtener servicios
    google_service = get_calendar_service()
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    if not monday_handler:
        print("❌ No se pudo obtener el servicio de Monday")
        return False
    
    try:
        # Item ID específico
        item_id = "9881971936"
        
        print(f"🔧 Corrigiendo sincronización para item {item_id}...")
        
        # Obtener datos del item de Monday.com
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
        
        # Extraer la fecha de Monday.com
        column_values = item.get('column_values', [])
        fecha_monday = None
        google_event_id = None
        
        for col in column_values:
            col_id = col.get('id')
            if col_id == config.COL_FECHA:
                fecha_monday = col.get('text', '')
            elif col_id == config.COL_GOOGLE_EVENT_ID:
                google_event_id = col.get('text', '')
        
        if not fecha_monday:
            print("❌ No se pudo extraer la fecha de Monday.com")
            return False
        
        if not google_event_id:
            print("❌ No se pudo extraer el Google Event ID de Monday.com")
            return False
        
        print(f"📅 Fecha en Monday.com: {fecha_monday}")
        print(f"🆔 Google Event ID: {google_event_id}")
        
        # Obtener el evento actual de Google Calendar
        try:
            event = google_service.events().get(
                calendarId=config.MASTER_CALENDAR_ID,
                eventId=google_event_id
            ).execute()
            
            print(f"✅ Evento encontrado en Google Calendar")
            print(f"   Fecha actual: {event.get('start', {}).get('dateTime', 'Sin fecha')}")
            
            # Actualizar el evento con la fecha de Monday.com
            # Parsear la fecha de Monday.com
            try:
                # Monday.com envía la fecha en formato "YYYY-MM-DD HH:MM" o "YYYY-MM-DD HH:MM:SS"
                if len(fecha_monday.split(':')) == 2:
                    fecha_dt = datetime.strptime(fecha_monday, '%Y-%m-%d %H:%M')
                else:
                    fecha_dt = datetime.strptime(fecha_monday, '%Y-%m-%d %H:%M:%S')
                fecha_iso = fecha_dt.isoformat()
                
                # Actualizar el evento
                event['start'] = {
                    'dateTime': fecha_iso,
                    'timeZone': 'Europe/Madrid'
                }
                
                # Calcular fin del evento (1 hora después)
                end_dt = fecha_dt.replace(hour=fecha_dt.hour + 1)
                event['end'] = {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'Europe/Madrid'
                }
                
                # Actualizar en Google Calendar
                updated_event = google_service.events().update(
                    calendarId=config.MASTER_CALENDAR_ID,
                    eventId=google_event_id,
                    body=event
                ).execute()
                
                print(f"✅ Evento actualizado en Google Calendar")
                print(f"   Nueva fecha: {updated_event.get('start', {}).get('dateTime', 'Sin fecha')}")
                return True
                
            except ValueError as e:
                print(f"❌ Error parseando fecha de Monday.com: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error obteniendo/actualizando evento de Google Calendar: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error durante corrección: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 CORRECTOR DE SINCRONIZACIÓN")
    print("=" * 80)
    
    success = corregir_sincronizacion()
    
    if success:
        print("\n🎉 ¡SINCRONIZACIÓN CORREGIDA!")
        print("Monday.com y Google Calendar deberían estar sincronizados")
    else:
        print("\n❌ ERROR CORRIGIENDO SINCRONIZACIÓN")

if __name__ == "__main__":
    main()
