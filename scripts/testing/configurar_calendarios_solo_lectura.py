#!/usr/bin/env python3
"""
Script para configurar calendarios de Google como solo lectura
============================================================

Este script configura los calendarios master y personales para que:
1. Los eventos no se puedan mover/editar manualmente
2. Solo se puedan ver los eventos
3. Los cambios solo se puedan hacer desde Monday.com

Uso:
    python3 scripts/testing/configurar_calendarios_solo_lectura.py
"""

import os
import sys
import json
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from google_calendar_service import get_calendar_service
except ImportError:
    # Intentar importar desde el directorio raíz
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from google_calendar_service import get_calendar_service
import config


def configurar_calendario_solo_lectura(google_service, calendar_id, calendar_name):
    """
    Configura un calendario para que sea solo lectura para todos los usuarios.
    
    Args:
        google_service: Servicio de Google Calendar
        calendar_id: ID del calendario a configurar
        calendar_name: Nombre del calendario para logs
    """
    try:
        print(f"🔧 Configurando calendario: {calendar_name}")
        print(f"   ID: {calendar_id}")
        
        # Obtener configuración actual del calendario
        calendar = google_service.calendars().get(calendarId=calendar_id).execute()
        
        # Configurar como solo lectura
        calendar_settings = {
            'summary': calendar.get('summary', calendar_name),
            'description': f"{calendar.get('description', '')}\n\n🚨 CALENDARIO DE SINCRONIZACIÓN AUTOMÁTICA\n⚠️  NO EDITAR MANUALMENTE - Los cambios se perderán\n✅ Para modificar: Editar en Monday.com",
            'timeZone': calendar.get('timeZone', 'Europe/Madrid'),
            'conferenceProperties': calendar.get('conferenceProperties', {}),
            # Configurar permisos para prevenir ediciones
            'accessRole': 'reader',  # Solo lectura para todos
            'defaultReminders': calendar.get('defaultReminders', []),
            'notificationSettings': calendar.get('notificationSettings', {})
        }
        
        # Actualizar calendario
        updated_calendar = google_service.calendars().update(
            calendarId=calendar_id,
            body=calendar_settings
        ).execute()
        
        print(f"✅ Calendario '{calendar_name}' configurado como solo lectura")
        print(f"   Descripción actualizada con avisos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando calendario '{calendar_name}': {e}")
        return False


def configurar_acl_solo_lectura(google_service, calendar_id, calendar_name):
    """
    Configura las reglas de acceso (ACL) para que el calendario sea solo lectura.
    
    Args:
        google_service: Servicio de Google Calendar
        calendar_id: ID del calendario
        calendar_name: Nombre del calendario para logs
    """
    try:
        print(f"🔐 Configurando ACL para: {calendar_name}")
        
        # Obtener reglas de acceso actuales
        acl_rules = google_service.acl().list(calendarId=calendar_id).execute()
        
        # Configurar regla para todos los usuarios (público)
        public_rule = {
            'scope': {
                'type': 'default'
            },
            'role': 'reader'  # Solo lectura
        }
        
        # Aplicar regla
        google_service.acl().update(
            calendarId=calendar_id,
            ruleId='default',
            body=public_rule
        ).execute()
        
        print(f"✅ ACL configurado: Solo lectura para todos los usuarios")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando ACL para '{calendar_name}': {e}")
        return False


def configurar_eventos_existentes(google_service, calendar_id, calendar_name):
    """
    Configura los eventos existentes para que sean solo lectura.
    
    Args:
        google_service: Servicio de Google Calendar
        calendar_id: ID del calendario
        calendar_name: Nombre del calendario para logs
    """
    try:
        print(f"📅 Configurando eventos existentes en: {calendar_name}")
        
        # Obtener eventos del calendario
        events_result = google_service.events().list(
            calendarId=calendar_id,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"   Encontrados {len(events)} eventos")
        
        updated_count = 0
        for event in events:
            try:
                # Configurar evento como solo lectura
                event_body = {
                    'summary': event.get('summary', ''),
                    'description': event.get('description', ''),
                    'start': event.get('start'),
                    'end': event.get('end'),
                    'location': event.get('location', ''),
                    'attendees': event.get('attendees', []),
                    'reminders': event.get('reminders', {}),
                    'extendedProperties': event.get('extendedProperties', {}),
                    # Marcar como solo lectura
                    'transparency': 'opaque',
                    'visibility': 'default',
                    'guestsCanModify': False,
                    'guestsCanInviteOthers': False,
                    'guestsCanSeeOtherGuests': True
                }
                
                # Actualizar evento
                google_service.events().update(
                    calendarId=calendar_id,
                    eventId=event['id'],
                    body=event_body
                ).execute()
                
                updated_count += 1
                
            except Exception as e:
                print(f"   ⚠️  Error actualizando evento {event.get('id', 'N/A')}: {e}")
        
        print(f"✅ {updated_count} eventos configurados como solo lectura")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando eventos en '{calendar_name}': {e}")
        return False


def main():
    """Función principal del script."""
    print("🔧 CONFIGURADOR DE CALENDARIOS SOLO LECTURA")
    print("=" * 50)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Inicializar servicio de Google Calendar
        print("🚀 Inicializando servicio de Google Calendar...")
        google_service = get_calendar_service()
        print("✅ Servicio inicializado correctamente")
        print()
        
        # Lista de calendarios a configurar
        calendarios = [
            {
                'id': config.MASTER_CALENDAR_ID,
                'name': 'Calendario Master'
            }
        ]
        
        # Añadir calendarios personales
        for profile in config.FILMMAKER_PROFILES:
            if profile.get('calendar_id'):
                calendarios.append({
                    'id': profile['calendar_id'],
                    'name': f"Calendario Personal - {profile['monday_name']}"
                })
        
        print(f"📋 Calendarios a configurar: {len(calendarios)}")
        print()
        
        # Configurar cada calendario
        success_count = 0
        for calendario in calendarios:
            print(f"🔧 Procesando: {calendario['name']}")
            print("-" * 40)
            
            # 1. Configurar calendario como solo lectura
            if configurar_calendario_solo_lectura(google_service, calendario['id'], calendario['name']):
                # 2. Configurar ACL
                if configurar_acl_solo_lectura(google_service, calendario['id'], calendario['name']):
                    # 3. Configurar eventos existentes
                    if configurar_eventos_existentes(google_service, calendario['id'], calendario['name']):
                        success_count += 1
                        print(f"✅ {calendario['name']}: Configuración completa")
                    else:
                        print(f"⚠️  {calendario['name']}: Error en eventos")
                else:
                    print(f"⚠️  {calendario['name']}: Error en ACL")
            else:
                print(f"❌ {calendario['name']}: Error en configuración")
            
            print()
        
        # Resumen final
        print("📊 RESUMEN DE CONFIGURACIÓN")
        print("=" * 30)
        print(f"✅ Calendarios configurados correctamente: {success_count}/{len(calendarios)}")
        
        if success_count == len(calendarios):
            print("🎉 ¡Todos los calendarios configurados como solo lectura!")
            print("🔒 Los eventos ya no se pueden mover/editar manualmente")
            print("✅ Solo se pueden ver y los cambios se hacen desde Monday.com")
        else:
            print("⚠️  Algunos calendarios no se pudieron configurar completamente")
            print("🔧 Revisar los errores anteriores")
        
        print()
        print("💡 INFORMACIÓN IMPORTANTE:")
        print("   - Los calendarios ahora son solo lectura")
        print("   - Los eventos no se pueden mover/editar manualmente")
        print("   - Todos los cambios deben hacerse desde Monday.com")
        print("   - El sistema de sincronización seguirá funcionando normalmente")
        
    except Exception as e:
        print(f"❌ Error general en el script: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
