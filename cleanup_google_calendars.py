#!/usr/bin/env python3
"""
Script de limpieza infalible para Google Calendar
Elimina todos los calendarios de Stupendastic basándose en los datos reales de Google Calendar.
"""

import config
from google_calendar_service import get_calendar_service
from googleapiclient.errors import HttpError

def cleanup_google_calendars():
    """
    Elimina todos los calendarios de Stupendastic basándose en los datos reales de Google Calendar.
    """
    print("🧹 INICIANDO LIMPIEZA INFALIBLE DE GOOGLE CALENDAR")
    print("=" * 60)
    
    # Inicializar el servicio de Google Calendar
    print("📡 Inicializando servicio de Google Calendar...")
    service = get_calendar_service()
    
    if not service:
        print("❌ No se pudo inicializar el servicio de Google Calendar.")
        print("   Asegúrate de haber ejecutado autorizar_google.py primero.")
        return
    
    print("✅ Servicio de Google Calendar inicializado correctamente.")
    print()
    
    # 1. Obtener TODOS los calendarios del usuario
    print("📋 OBTENIENDO LISTA COMPLETA DE CALENDARIOS")
    print("-" * 50)
    
    try:
        # Obtener la lista completa de calendarios
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        print(f"✅ Se encontraron {len(calendars)} calendarios en total")
        print()
        
    except HttpError as error:
        print(f"❌ Error al obtener la lista de calendarios: {error}")
        return
    
    # 2. Identificar y eliminar calendarios de Stupendastic
    print("🎯 IDENTIFICANDO CALENDARIOS DE STUPENDASTIC")
    print("-" * 50)
    
    calendars_to_delete = []
    calendars_skipped = []
    
    for calendar in calendars:
        calendar_id = calendar.get('id')
        summary = calendar.get('summary', '')
        access_role = calendar.get('accessRole', '')
        
        # Saltar calendarios del sistema (primary, holidays, etc.)
        if calendar_id in ['primary', 'holiday@group.v.calendar.google.com']:
            print(f"⏭️  Saltando calendario del sistema: {summary}")
            calendars_skipped.append(summary)
            continue
        
        # Verificar si es un calendario de Stupendastic
        should_delete = False
        reason = ""
        
        # Condición 1: Termina en " STUPENDASTIC" (filmmakers)
        if summary.endswith(" STUPENDASTIC"):
            should_delete = True
            reason = "Filmmaker"
        
        # Condición 2: Es exactamente "Máster Stupendastic"
        elif summary == "Máster Stupendastic":
            should_delete = True
            reason = "Calendario Máster"
        
        # Condición 3: Es exactamente "Sin Asignar Stupendastic"
        elif summary == "Sin Asignar Stupendastic":
            should_delete = True
            reason = "Calendario Sin Asignar"
        
        if should_delete:
            print(f"🗑️  Calendario identificado para eliminar: '{summary}'")
            print(f"    ID: {calendar_id}")
            print(f"    Tipo: {reason}")
            print(f"    Rol de acceso: {access_role}")
            calendars_to_delete.append({
                'id': calendar_id,
                'summary': summary,
                'reason': reason
            })
        else:
            print(f"✅ Manteniendo calendario: '{summary}'")
            calendars_skipped.append(summary)
    
    print()
    
    # 3. Ejecutar el borrado
    if not calendars_to_delete:
        print("ℹ️  No se encontraron calendarios de Stupendastic para eliminar.")
        print("   El entorno ya está limpio.")
        return
    
    print("🚨 EJECUTANDO ELIMINACIÓN DE CALENDARIOS")
    print("-" * 50)
    
    deleted_count = 0
    failed_count = 0
    
    for calendar_info in calendars_to_delete:
        calendar_id = calendar_info['id']
        summary = calendar_info['summary']
        reason = calendar_info['reason']
        
        print(f"🗑️  Eliminando '{summary}' ({reason})...")
        print(f"    ID: {calendar_id}")
        
        try:
            service.calendars().delete(calendarId=calendar_id).execute()
            print(f"    ✅ Eliminado exitosamente")
            deleted_count += 1
            
        except HttpError as error:
            if error.resp.status == 404:
                print(f"    ℹ️  Ya no existe (404)")
                deleted_count += 1  # Consideramos éxito si ya no existe
            else:
                print(f"    ❌ Error: {error}")
                failed_count += 1
        
        print()
    
    # 4. Resumen final
    print("📊 RESUMEN DE LA LIMPIEZA")
    print("=" * 60)
    print(f"✅ Calendarios eliminados exitosamente: {deleted_count}")
    print(f"❌ Calendarios con error al eliminar: {failed_count}")
    print(f"⏭️  Calendarios mantenidos: {len(calendars_skipped)}")
    print(f"📈 Total de calendarios procesados: {len(calendars)}")
    
    if deleted_count > 0:
        print("\n🎉 ¡Limpieza completada! Los calendarios de Stupendastic han sido eliminados.")
        print("   El entorno está listo para la prueba de integración desde cero.")
    else:
        print("\nℹ️  No se eliminó ningún calendario. El entorno ya estaba limpio.")
    
    print("\n💡 Recuerda ejecutar el script principal para crear los nuevos calendarios.")
    
    # 5. Limpiar archivo config.py si se eliminaron calendarios
    if deleted_count > 0:
        print("\n🧹 LIMPIANDO ARCHIVO DE CONFIGURACIÓN")
        print("-" * 50)
        
        try:
            # Leer el archivo config.py actual
            with open('config.py', 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Establecer MASTER_CALENDAR_ID a None
            if 'MASTER_CALENDAR_ID =' in config_content:
                import re
                config_content = re.sub(
                    r'MASTER_CALENDAR_ID = "[^"]*"',
                    'MASTER_CALENDAR_ID = None',
                    config_content
                )
            
            # Establecer UNASSIGNED_CALENDAR_ID a None
            if 'UNASSIGNED_CALENDAR_ID =' in config_content:
                import re
                config_content = re.sub(
                    r'UNASSIGNED_CALENDAR_ID = "[^"]*"',
                    'UNASSIGNED_CALENDAR_ID = None',
                    config_content
                )
            
            # Establecer todos los calendar_id a None en FILMMAKER_PROFILES
            lines = config_content.split('\n')
            for i, line in enumerate(lines):
                if '"calendar_id": "' in line:
                    lines[i] = line.replace('"calendar_id": "', '"calendar_id": None,')
                    lines[i] = lines[i].replace('",', ',')
            
            config_content = '\n'.join(lines)
            
            # Escribir el archivo actualizado
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print("    ✅ Archivo config.py limpiado exitosamente")
            print("    📝 Todos los calendar_id establecidos a None")
            
        except Exception as e:
            print(f"    ❌ Error al limpiar config.py: {e}")
            print("    ⚠️  Los IDs de calendarios aún están en el archivo")

if __name__ == "__main__":
    cleanup_google_calendars() 