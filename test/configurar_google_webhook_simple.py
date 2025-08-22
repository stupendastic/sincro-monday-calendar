#!/usr/bin/env python3
"""
Script simplificado para configurar notificaciones push de Google Calendar
"""
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service

# Cargar variables de entorno
load_dotenv()

def configurar_google_webhook():
    """Configura las notificaciones push para Google Calendar"""
    
    print("🔧 CONFIGURANDO NOTIFICACIONES PUSH DE GOOGLE CALENDAR")
    print("=" * 60)
    
    # Obtener el servicio de Google Calendar
    service = get_calendar_service()
    if not service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # Obtener la URL de ngrok desde .env
    ngrok_url = os.getenv('NGROK_PUBLIC_URL')
    if not ngrok_url:
        print("❌ NGROK_PUBLIC_URL no configurada en .env")
        return False
    
    webhook_url = f"{ngrok_url}/google-webhook"
    print(f"📡 URL del webhook: {webhook_url}")
    
    # Obtener el calendario maestro desde config
    from config import MASTER_CALENDAR_ID
    calendar_id = MASTER_CALENDAR_ID
    
    print(f"📅 Calendario maestro: {calendar_id}")
    
    try:
        # Crear el canal de notificaciones push con formato simplificado
        channel_body = {
            'id': 'stupendastic-sync-channel',
            'type': 'web_hook',
            'address': webhook_url
        }
        
        print(f"🔄 Creando canal de notificaciones...")
        print(f"   ID: {channel_body['id']}")
        print(f"   URL: {channel_body['address']}")
        
        # Crear el canal usando events().watch()
        result = service.events().watch(
            calendarId=calendar_id,
            body=channel_body
        ).execute()
        
        print("✅ Canal creado exitosamente!")
        print(f"   Resource ID: {result.get('resourceId')}")
        print(f"   Expiración: {result.get('expiration')}")
        
        # Guardar la información del canal
        channel_info = {
            'resource_id': result.get('resourceId'),
            'expiration': result.get('expiration'),
            'webhook_url': webhook_url,
            'calendar_id': calendar_id,
            'created_at': datetime.now().isoformat()
        }
        
        with open('google_channel_info.json', 'w') as f:
            json.dump(channel_info, f, indent=2)
        
        print("💾 Información del canal guardada en 'google_channel_info.json'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando el canal: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        
        # Intentar con un enfoque alternativo
        print("\n🔄 Intentando enfoque alternativo...")
        try:
            # Usar el calendario principal del usuario
            calendar_list = service.calendarList().list().execute()
            primary_calendar = None
            
            for calendar in calendar_list.get('items', []):
                if calendar.get('primary'):
                    primary_calendar = calendar['id']
                    break
            
            if primary_calendar:
                print(f"📅 Usando calendario principal: {primary_calendar}")
                
                result = service.events().watch(
                    calendarId=primary_calendar,
                    body=channel_body
                ).execute()
                
                print("✅ Canal creado exitosamente en calendario principal!")
                print(f"   Resource ID: {result.get('resourceId')}")
                
                # Guardar información
                channel_info = {
                    'resource_id': result.get('resourceId'),
                    'expiration': result.get('expiration'),
                    'webhook_url': webhook_url,
                    'calendar_id': primary_calendar,
                    'created_at': datetime.now().isoformat(),
                    'note': 'Usando calendario principal como fallback'
                }
                
                with open('google_channel_info.json', 'w') as f:
                    json.dump(channel_info, f, indent=2)
                
                return True
            else:
                print("❌ No se encontró calendario principal")
                return False
                
        except Exception as e2:
            print(f"❌ Error en enfoque alternativo: {e2}")
            return False

def main():
    """Función principal"""
    print("🧪 CONFIGURADOR SIMPLIFICADO DE NOTIFICACIONES PUSH")
    print("=" * 60)
    
    success = configurar_google_webhook()
    
    if success:
        print("\n🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("=" * 40)
        print("✅ Google Calendar enviará notificaciones a tu servidor")
        print("✅ Cuando muevas eventos en Google, se sincronizarán con Monday")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Mueve un evento en Google Calendar")
        print("2. Observa los logs del servidor")
        print("3. Verifica que se actualiza en Monday")
        print("\n⚠️ NOTA: El canal expira en 7 días")
        print("   Para renovarlo, ejecuta este script nuevamente")
    else:
        print("\n❌ Error en la configuración")
        print("Verifica las credenciales de Google y la URL de ngrok")

if __name__ == "__main__":
    main()
