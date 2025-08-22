#!/usr/bin/env python3
"""
Script para actualizar el webhook de Monday.com con la nueva URL
"""
import os
import requests
from dotenv import load_dotenv
import config

# Cargar variables de entorno
load_dotenv()

# Nueva URL de ngrok
NGROK_URL = "https://2e6cc727ffae.ngrok-free.app"

def actualizar_webhook_monday():
    """Actualiza el webhook de Monday.com con la nueva URL"""
    
    print("🔧 ACTUALIZANDO WEBHOOK DE MONDAY.COM")
    print("=" * 60)
    print(f"🌐 Nueva URL: {NGROK_URL}")
    print()
    
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
            print(f"✅ Webhook de Monday.com actualizado:")
            print(f"   ID: {webhook_data['id']}")
            print(f"   URL: {webhook_url}")
            print(f"   Evento: {webhook_data['event']}")
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error actualizando webhook de Monday: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 ACTUALIZADOR DE WEBHOOK MONDAY.COM")
    print("=" * 60)
    
    success = actualizar_webhook_monday()
    
    if success:
        print("\n🎉 ¡WEBHOOK ACTUALIZADO!")
        print("✅ Monday.com ahora usará la nueva URL")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Haz una prueba moviendo un evento en Google Calendar")
        print("2. Verifica que Monday.com recibe las notificaciones")
        print("3. Verifica que la sincronización funciona")
    else:
        print("\n❌ ERROR ACTUALIZANDO WEBHOOK")
        print("Verifica los errores arriba")

if __name__ == "__main__":
    main()
