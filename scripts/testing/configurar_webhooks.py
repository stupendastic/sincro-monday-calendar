#!/usr/bin/env python3
"""
Script para configurar webhooks de Monday.com y Google Calendar
con la nueva URL de ngrok
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import json
import requests
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

# Nueva URL de ngrok
NGROK_URL = "https://1f6deb6593e0.ngrok-free.app"

def configurar_monday_webhook():
    """Configura el webhook de Monday.com"""
    
    print("🔧 CONFIGURANDO WEBHOOK DE MONDAY.COM")
    print("=" * 50)
    
    # URL del webhook
    webhook_url = f"{NGROK_URL}/monday-webhook"
    
    # Headers para la API de Monday
    headers = {
        'Authorization': os.getenv('MONDAY_API_KEY'),
        'Content-Type': 'application/json'
    }
    
    # Query GraphQL para crear webhook
    query = '''
    mutation ($boardId: ID!, $url: String!, $event: WebhookEventType!) {
        create_webhook (board_id: $boardId, url: $url, event: $event) {
            id
            board_id
            event
        }
    }
    '''
    
    variables = {
        'boardId': config.BOARD_ID_GRABACIONES,
        'url': webhook_url,
        'event': 'update'
    }
    
    try:
        # Hacer la petición a Monday.com
        response = requests.post(
            'https://api.monday.com/v2',
            json={'query': query, 'variables': variables},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print(f"❌ Error en Monday.com: {data['errors']}")
                return False
            
            webhook_data = data['data']['create_webhook']
            print(f"✅ Webhook de Monday.com creado:")
            print(f"   ID: {webhook_data['id']}")
            print(f"   URL: {webhook_data['url']}")
            print(f"   Evento: {webhook_data['event']}")
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error configurando webhook de Monday: {e}")
        return False

def configurar_google_webhook():
    """Configura el webhook de Google Calendar"""
    
    print("\n🔧 CONFIGURANDO WEBHOOK DE GOOGLE CALENDAR")
    print("=" * 50)
    
    # Obtener servicio de Google
    google_service = get_calendar_service()
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    # URL del webhook
    webhook_url = f"{NGROK_URL}/google-webhook"
    
    try:
        # Configurar push notifications para el calendario maestro
        channel_body = {
            'id': 'stupendastic-sync-channel',
            'type': 'web_hook',
            'address': webhook_url
        }
        
        # Crear el webhook
        response = google_service.events().watch(
            calendarId=config.MASTER_CALENDAR_ID,
            body=channel_body
        ).execute()
        
        print(f"✅ Webhook de Google Calendar creado:")
        print(f"   Channel ID: {response['id']}")
        print(f"   Resource ID: {response['resourceId']}")
        print(f"   Expiración: {response['expiration']}")
        print(f"   URL: {webhook_url}")
        
        # Guardar información del canal
        channel_info = {
            'channel_id': response['id'],
            'resource_id': response['resourceId'],
            'expiration': response['expiration'],
            'webhook_url': webhook_url,
            'calendar_id': config.MASTER_CALENDAR_ID
        }
        
        with open('config/channels/google_channel_info.json', 'w', encoding='utf-8') as f:
            json.dump(channel_info, f, indent=2)
        
        # Actualizar el mapeo de canales
        with open('config/channels/config/channels/google_channel_map.json', 'r', encoding='utf-8') as f:
            channel_map = json.load(f)
        
        channel_map[response['id']] = config.MASTER_CALENDAR_ID
        
        with open('config/channels/config/channels/google_channel_map.json', 'w', encoding='utf-8') as f:
            json.dump(channel_map, f, indent=2)
        
        print(f"✅ Información del canal guardada")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando webhook de Google: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 CONFIGURADOR DE WEBHOOKS")
    print("=" * 60)
    print(f"🌐 URL de ngrok: {NGROK_URL}")
    print()
    
    # Configurar Monday.com
    monday_success = configurar_monday_webhook()
    
    # Configurar Google Calendar
    google_success = configurar_google_webhook()
    
    print("\n" + "=" * 60)
    if monday_success and google_success:
        print("🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("✅ Monday.com webhook configurado")
        print("✅ Google Calendar webhook configurado")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Reinicia el servidor Flask")
        print("2. Haz una prueba moviendo un evento")
    else:
        print("❌ CONFIGURACIÓN INCOMPLETA")
        if not monday_success:
            print("❌ Monday.com webhook falló")
        if not google_success:
            print("❌ Google Calendar webhook falló")

if __name__ == "__main__":
    main()
