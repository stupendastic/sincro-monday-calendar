#!/usr/bin/env python3
"""
Script para configurar webhooks en todos los calendarios personales
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import json
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

# URL de ngrok
NGROK_URL = "https://2e6cc727ffae.ngrok-free.app"

def configurar_webhook_calendario_personal(calendar_id, filmmaker_name):
    """
    Configura webhook para un calendario personal específico
    """
    print(f"🔧 Configurando webhook para {filmmaker_name}...")
    
    # Obtener servicio de Google
    google_service = get_calendar_service()
    if not google_service:
        print(f"❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # URL del webhook
    webhook_url = f"{NGROK_URL}/google-webhook"
    
    try:
        # Crear un ID único para este canal
        channel_id = f"stupendastic-personal-{filmmaker_name.lower().replace(' ', '-')}"
        
        # Configurar push notifications
        channel_body = {
            'id': channel_id,
            'type': 'web_hook',
            'address': webhook_url
        }
        
        # Crear el webhook
        response = google_service.events().watch(
            calendarId=calendar_id,
            body=channel_body
        ).execute()
        
        print(f"  ✅ Webhook creado:")
        print(f"     Channel ID: {response['id']}")
        print(f"     Calendar: {calendar_id}")
        print(f"     Expiración: {response['expiration']}")
        
        # Guardar información del canal
        channel_info = {
            'channel_id': response['id'],
            'resource_id': response['resourceId'],
            'expiration': response['expiration'],
            'webhook_url': webhook_url,
            'calendar_id': calendar_id,
            'filmmaker_name': filmmaker_name
        }
        
        # Guardar en archivo específico para este filmmaker
        filename = f"config/channels/google_channel_info_{filmmaker_name.lower().replace(' ', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(channel_info, f, indent=2)
        
        # Actualizar el mapeo de canales
        try:
            with open('config/channels/config/channels/google_channel_map.json', 'r', encoding='utf-8') as f:
                channel_map = json.load(f)
        except FileNotFoundError:
            channel_map = {}
        
        channel_map[response['id']] = calendar_id
        
        with open('config/channels/config/channels/google_channel_map.json', 'w', encoding='utf-8') as f:
            json.dump(channel_map, f, indent=2)
        
        print(f"  ✅ Información guardada")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 CONFIGURADOR DE WEBHOOKS PARA CALENDARIOS PERSONALES")
    print("=" * 70)
    print(f"🌐 URL de ngrok: {NGROK_URL}")
    print()
    
    # Obtener todos los perfiles de filmmakers
    filmmaker_profiles = config.FILMMAKER_PROFILES
    
    if not filmmaker_profiles:
        print("❌ No se encontraron perfiles de filmmakers en config.py")
        return
    
    print(f"📋 Configurando webhooks para {len(filmmaker_profiles)} calendarios personales:")
    print()
    
    success_count = 0
    total_count = len(filmmaker_profiles)
    
    for profile in filmmaker_profiles:
        filmmaker_name = profile.get('monday_name')
        calendar_id = profile.get('calendar_id')
        
        if not calendar_id:
            print(f"⚠️  {filmmaker_name}: No tiene calendar_id configurado")
            continue
        
        success = configurar_webhook_calendario_personal(calendar_id, filmmaker_name)
        
        if success:
            success_count += 1
        
        print()  # Línea en blanco entre filmmakers
    
    print("=" * 70)
    print(f"📊 RESUMEN:")
    print(f"   ✅ Exitosos: {success_count}/{total_count}")
    print(f"   ❌ Fallidos: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 ¡TODOS LOS WEBHOOKS CONFIGURADOS!")
        print("✅ Los calendarios personales ahora enviarán notificaciones")
        print("✅ La cuenta admin puede mover eventos y se sincronizarán")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Reinicia el servidor Flask")
        print("2. Haz una prueba moviendo un evento desde un calendario personal")
    else:
        print(f"\n⚠️  {total_count - success_count} webhooks fallaron")
        print("Revisa los errores arriba")

if __name__ == "__main__":
    main()
