#!/usr/bin/env python3
"""
Script para verificar el acceso de la cuenta admin a los calendarios personales
"""
import os
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def verificar_acceso_admin():
    """Verifica el acceso de la cuenta admin a los calendarios personales"""
    
    print("🔐 VERIFICANDO ACCESO DE CUENTA ADMIN")
    print("=" * 60)
    
    service = get_calendar_service()
    if not service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    try:
        # Listar todos los calendarios disponibles
        print("📋 CALENDARIOS DISPONIBLES PARA ADMIN:")
        print("-" * 40)
        
        calendar_list = service.calendarList().list().execute()
        
        for calendar in calendar_list.get('items', []):
            calendar_id = calendar.get('id')
            summary = calendar.get('summary', 'Sin nombre')
            access_role = calendar.get('accessRole', 'Sin acceso')
            primary = calendar.get('primary', False)
            
            # Verificar si es un calendario de filmmaker
            es_filmmaker = False
            for profile in config.FILMMAKER_PROFILES:
                if profile["calendar_id"] == calendar_id:
                    es_filmmaker = True
                    break
            
            if es_filmmaker:
                print(f"👥 {summary} (FILMMAKER)")
            elif calendar_id == config.MASTER_CALENDAR_ID:
                print(f"👑 {summary} (MAESTRO)")
            else:
                print(f"📅 {summary}")
            
            print(f"   ID: {calendar_id}")
            print(f"   Acceso: {access_role}")
            print(f"   Principal: {'Sí' if primary else 'No'}")
            print()
        
        # Verificar permisos específicos
        print("🎯 VERIFICANDO PERMISOS ESPECÍFICOS:")
        print("-" * 40)
        
        # Verificar calendario maestro
        try:
            master_calendar = config.MASTER_CALENDAR_ID
            calendar = service.calendars().get(calendarId=master_calendar).execute()
            print(f"✅ Calendario Maestro: {calendar.get('summary', 'Sin nombre')}")
            print(f"   Acceso: {calendar.get('accessRole', 'Sin acceso')}")
        except Exception as e:
            print(f"❌ Error accediendo al calendario maestro: {e}")
        
        print()
        
        # Verificar calendarios de filmmakers
        print("👥 CALENDARIOS DE FILMMAKERS:")
        print("-" * 40)
        
        for profile in config.FILMMAKER_PROFILES:
            try:
                calendar_id = profile["calendar_id"]
                calendar = service.calendars().get(calendarId=calendar_id).execute()
                
                access_role = calendar.get('accessRole', 'Sin acceso')
                puede_editar = access_role in ['owner', 'writer']
                
                print(f"✅ {profile['monday_name']}: {calendar.get('summary', 'Sin nombre')}")
                print(f"   ID: {calendar_id}")
                print(f"   Acceso: {access_role}")
                print(f"   Puede editar: {'✅ Sí' if puede_editar else '❌ No'}")
                
            except Exception as e:
                print(f"❌ Error accediendo al calendario de {profile['monday_name']}: {e}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def test_edicion_calendario_personal():
    """Prueba si se puede editar un calendario personal"""
    
    print("🧪 PROBANDO EDICIÓN DE CALENDARIO PERSONAL")
    print("-" * 40)
    
    service = get_calendar_service()
    if not service:
        return False
    
    # Buscar el calendario de Arnau Admin
    calendar_id = None
    for profile in config.FILMMAKER_PROFILES:
        if profile["monday_name"] == "Arnau Admin":
            calendar_id = profile["calendar_id"]
            break
    
    if not calendar_id:
        print("❌ No se encontró el calendario de Arnau Admin")
        return False
    
    try:
        # Intentar listar eventos (prueba de acceso)
        events_result = service.events().list(
            calendarId=calendar_id,
            maxResults=1
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ Acceso de lectura exitoso - {len(events)} eventos encontrados")
        
        # Intentar crear un evento de prueba (prueba de escritura)
        from datetime import datetime, timedelta
        
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        event_body = {
            'summary': 'PRUEBA EDICIÓN ADMIN',
            'description': 'Evento de prueba para verificar permisos de edición',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
        }
        
        # Crear evento de prueba
        event = service.events().insert(
            calendarId=calendar_id,
            body=event_body
        ).execute()
        
        event_id = event['id']
        print(f"✅ Acceso de escritura exitoso - Evento creado: {event_id}")
        
        # Limpiar evento de prueba
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        print(f"✅ Evento de prueba eliminado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de acceso: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN DE ACCESO ADMIN")
    print("=" * 60)
    
    # Verificar acceso general
    verificar_acceso_admin()
    
    # Probar edición
    print("\n🧪 PRUEBA DE EDICIÓN:")
    print("=" * 60)
    
    success = test_edicion_calendario_personal()
    
    if success:
        print("\n🎉 ¡ACCESO ADMIN FUNCIONA!")
        print("=" * 40)
        print("✅ La cuenta admin puede editar calendarios personales")
        print("✅ Podemos implementar la sincronización inversa")
    else:
        print("\n❌ PROBLEMA DE ACCESO")
        print("=" * 40)
        print("❌ La cuenta admin no puede editar calendarios personales")
        print("📋 Necesitamos configurar permisos en Google Calendar")

if __name__ == "__main__":
    main()
