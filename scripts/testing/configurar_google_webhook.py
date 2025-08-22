#!/usr/bin/env python3
"""
Script para configurar notificaciones push de Google Calendar
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service

# Cargar variables de entorno
load_dotenv()

def configurar_notificaciones_google():
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
        # Crear el canal de notificaciones push
        channel = {
            'id': 'stupendastic-sync-channel',
            'type': 'web_hook',
            'address': webhook_url,
            'expiration': (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
        }
        
        print(f"🔄 Creando canal de notificaciones...")
        print(f"   ID: {channel['id']}")
        print(f"   Expiración: {channel['expiration']}")
        
        # Crear el canal
        result = service.events().watch(
            calendarId=calendar_id,
            body=channel
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
        
        with open('config/channels/google_channel_info.json', 'w') as f:
            json.dump(channel_info, f, indent=2)
        
        print("💾 Información del canal guardada en 'config/channels/google_channel_info.json'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando el canal: {e}")
        return False

def verificar_canales_existentes():
    """Verifica si ya existen canales configurados"""
    print("\n🔍 VERIFICANDO CANALES EXISTENTES")
    print("-" * 40)
    
    try:
        with open('config/channels/google_channel_info.json', 'r') as f:
            channel_info = json.load(f)
        
        print("✅ Canal existente encontrado:")
        print(f"   Resource ID: {channel_info.get('resource_id')}")
        print(f"   Expiración: {channel_info.get('expiration')}")
        print(f"   Webhook URL: {channel_info.get('webhook_url')}")
        
        # Verificar si el canal ha expirado
        expiration_str = channel_info.get('expiration')
        if expiration_str:
            expiration = datetime.fromisoformat(expiration_str.replace('Z', '+00:00'))
            if expiration > datetime.now(expiration.tzinfo):
                print("✅ Canal aún válido")
                return True
            else:
                print("⚠️ Canal expirado, necesita renovación")
                return False
                
    except FileNotFoundError:
        print("❌ No se encontró información de canal existente")
        return False
    except Exception as e:
        print(f"❌ Error verificando canal: {e}")
        return False

def renovar_canal():
    """Renueva un canal expirado"""
    print("\n🔄 RENOVANDO CANAL EXPIRADO")
    print("-" * 40)
    
    try:
        with open('config/channels/google_channel_info.json', 'r') as f:
            channel_info = json.load(f)
        
        # Detener el canal anterior
        service = get_calendar_service()
        if service:
            try:
                service.channels().stop(body={
                    'id': 'stupendastic-sync-channel',
                    'resourceId': channel_info.get('resource_id')
                }).execute()
                print("✅ Canal anterior detenido")
            except:
                print("⚠️ No se pudo detener el canal anterior (puede estar ya expirado)")
        
        # Crear nuevo canal
        return configurar_notificaciones_google()
        
    except Exception as e:
        print(f"❌ Error renovando canal: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 CONFIGURADOR DE NOTIFICACIONES PUSH DE GOOGLE CALENDAR")
    print("=" * 60)
    
    # Verificar si ya existe un canal
    if verificar_canales_existentes():
        print("\n✅ Ya tienes un canal configurado y válido")
        print("🎯 Google Calendar enviará notificaciones automáticamente")
        return True
    
    # Si no existe o está expirado, crear uno nuevo
    print("\n🆕 Creando nuevo canal de notificaciones...")
    success = configurar_notificaciones_google()
    
    if success:
        print("\n🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("=" * 40)
        print("✅ Google Calendar enviará notificaciones a tu servidor")
        print("✅ Cuando muevas eventos en Google, se sincronizarán con Monday")
        print("✅ El canal expira en 7 días (se puede renovar)")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Mueve un evento en Google Calendar")
        print("2. Observa los logs del servidor")
        print("3. Verifica que se actualiza en Monday")
    else:
        print("\n❌ Error en la configuración")
        print("Verifica las credenciales de Google y la URL de ngrok")

if __name__ == "__main__":
    main()
