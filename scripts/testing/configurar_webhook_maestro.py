#!/usr/bin/env python3
"""
Script simple para configurar webhook del calendario maestro
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

def configurar_webhook_maestro():
    """Configura webhook para el calendario maestro"""
    
    print("🔧 CONFIGURANDO WEBHOOK DEL CALENDARIO MAESTRO")
    print("=" * 60)
    print(f"🌐 URL de ngrok: {NGROK_URL}")
    print()
    
    # Obtener servicio de Google
    google_service = get_calendar_service()
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # URL del webhook
    webhook_url = f"{NGROK_URL}/google-webhook"
    
    try:
        # Crear un ID único para el canal maestro
        channel_id = "stupendastic-master-calendar"
        
        # Configurar push notifications
        channel_body = {
            'id': channel_id,
            'type': 'web_hook',
            'address': webhook_url
        }
        
        # Crear el webhook
        response = google_service.events().watch(
            calendarId=config.MASTER_CALENDAR_ID,
            body=channel_body
        ).execute()
        
        print(f"✅ Webhook del calendario maestro creado:")
        print(f"   Channel ID: {response['id']}")
        print(f"   Calendar: {config.MASTER_CALENDAR_ID}")
        print(f"   Expiración: {response['expiration']}")
        print(f"   URL: {webhook_url}")
        
        # Guardar información del canal
        channel_info = {
            'channel_id': response['id'],
            'resource_id': response['resourceId'],
            'expiration': response['expiration'],
            'webhook_url': webhook_url,
            'calendar_id': config.MASTER_CALENDAR_ID,
            'type': 'master'
        }
        
        with open('config/channels/google_channel_info_master.json', 'w', encoding='utf-8') as f:
            json.dump(channel_info, f, indent=2)
        
        # Actualizar el mapeo de canales
        try:
            with open('config/channels/config/channels/google_channel_map.json', 'r', encoding='utf-8') as f:
                channel_map = json.load(f)
        except FileNotFoundError:
            channel_map = {}
        
        channel_map[response['id']] = config.MASTER_CALENDAR_ID
        
        with open('config/channels/config/channels/google_channel_map.json', 'w', encoding='utf-8') as f:
            json.dump(channel_map, f, indent=2)
        
        print(f"✅ Información guardada")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    success = configurar_webhook_maestro()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡WEBHOOK DEL CALENDARIO MAESTRO CONFIGURADO!")
        print("✅ El calendario maestro ahora enviará notificaciones")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Reinicia el servidor Flask")
        print("2. Haz una prueba moviendo un evento")
        print("3. Verifica que la sincronización funciona en ambas direcciones")
    else:
        print("❌ CONFIGURACIÓN FALLIDA")
        print("Revisa los errores arriba")

if __name__ == "__main__":
    main()
