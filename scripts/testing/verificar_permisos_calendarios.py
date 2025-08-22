#!/usr/bin/env python3
"""
Script para verificar los permisos de los calendarios de Google
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def verificar_permisos_calendarios():
    """Verifica los permisos de todos los calendarios"""
    
    print("🔐 VERIFICACIÓN DE PERMISOS DE CALENDARIOS")
    print("=" * 60)
    
    service = get_calendar_service()
    if not service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    try:
        # Listar todos los calendarios disponibles
        print("📋 CALENDARIOS DISPONIBLES:")
        print("-" * 40)
        
        calendar_list = service.calendarList().list().execute()
        
        for calendar in calendar_list.get('items', []):
            calendar_id = calendar.get('id')
            summary = calendar.get('summary', 'Sin nombre')
            access_role = calendar.get('accessRole', 'Sin acceso')
            primary = calendar.get('primary', False)
            
            print(f"📅 {summary}")
            print(f"   ID: {calendar_id}")
            print(f"   Acceso: {access_role}")
            print(f"   Principal: {'Sí' if primary else 'No'}")
            print()
        
        # Verificar calendarios específicos del sistema
        print("🎯 CALENDARIOS DEL SISTEMA:")
        print("-" * 40)
        
        # Calendario maestro
        try:
            master_calendar = config.MASTER_CALENDAR_ID
            calendar = service.calendars().get(calendarId=master_calendar).execute()
            print(f"✅ Calendario Maestro: {calendar.get('summary', 'Sin nombre')}")
            print(f"   ID: {master_calendar}")
            print(f"   Acceso: {calendar.get('accessRole', 'Sin acceso')}")
        except Exception as e:
            print(f"❌ Error accediendo al calendario maestro: {e}")
        
        print()
        
        # Calendarios de filmmakers
        print("👥 CALENDARIOS DE FILMMAKERS:")
        print("-" * 40)
        
        for profile in config.FILMMAKER_PROFILES:
            try:
                calendar_id = profile["calendar_id"]
                calendar = service.calendars().get(calendarId=calendar_id).execute()
                print(f"✅ {profile['monday_name']}: {calendar.get('summary', 'Sin nombre')}")
                print(f"   ID: {calendar_id}")
                print(f"   Acceso: {calendar.get('accessRole', 'Sin acceso')}")
            except Exception as e:
                print(f"❌ Error accediendo al calendario de {profile['monday_name']}: {e}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def test_acceso_calendario(calendar_id, nombre):
    """Prueba el acceso a un calendario específico"""
    
    print(f"🧪 PROBANDO ACCESO A {nombre}")
    print("-" * 40)
    
    service = get_calendar_service()
    if not service:
        return False
    
    try:
        # Intentar listar eventos
        events_result = service.events().list(
            calendarId=calendar_id,
            maxResults=1
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ Acceso exitoso - {len(events)} eventos encontrados")
        return True
        
    except Exception as e:
        print(f"❌ Error de acceso: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO DE PERMISOS DE CALENDARIOS")
    print("=" * 60)
    
    # Verificar todos los calendarios
    verificar_permisos_calendarios()
    
    # Probar acceso a calendarios específicos
    print("\n🧪 PRUEBAS DE ACCESO ESPECÍFICAS:")
    print("=" * 60)
    
    # Probar calendario maestro
    test_acceso_calendario(
        config.MASTER_CALENDAR_ID, 
        "Calendario Maestro"
    )
    
    # Probar calendario de Arnau Admin
    for profile in config.FILMMAKER_PROFILES:
        if profile["monday_name"] == "Arnau Admin":
            test_acceso_calendario(
                profile["calendar_id"],
                "Calendario Arnau Admin"
            )
            break
    
    print("\n🎯 DIAGNÓSTICO COMPLETADO")
    print("=" * 40)
    print("📋 PRÓXIMOS PASOS:")
    print("1. Verificar que todos los calendarios tienen acceso 'writer' o 'owner'")
    print("2. Si hay errores de acceso, revisar permisos en Google Calendar")
    print("3. Asegurar que la cuenta tiene permisos en todos los calendarios")

if __name__ == "__main__":
    main()
