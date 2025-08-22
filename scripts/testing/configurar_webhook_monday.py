#!/usr/bin/env python3
"""
Script para configurar automáticamente el webhook de Monday.com
"""

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import json
import requests
from dotenv import load_dotenv
import config

# Cargar variables de entorno
load_dotenv()

def obtener_url_ngrok():
    """Obtener la URL actual de ngrok"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('tunnels'):
                return data['tunnels'][0]['public_url']
    except Exception as e:
        print(f"❌ Error obteniendo URL de ngrok: {e}")
    return None

def configurar_webhook_monday():
    """Configurar webhook en Monday.com usando su API"""
    print("🔧 CONFIGURANDO WEBHOOK DE MONDAY.COM")
    print("=" * 50)
    
    # Obtener URL de ngrok
    ngrok_url = obtener_url_ngrok()
    if not ngrok_url:
        print("❌ No se pudo obtener la URL de ngrok")
        return False
    
    webhook_url = f"{ngrok_url}/monday-webhook"
    print(f"🌐 URL del webhook: {webhook_url}")
    
    # Verificar que el endpoint responde
    try:
        response = requests.get(webhook_url, timeout=10)
        if response.status_code == 200:
            print("✅ Endpoint de webhook responde correctamente")
        else:
            print(f"❌ Endpoint no responde: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error verificando endpoint: {e}")
        return False
    
    # Configurar webhook usando Monday.com API
    monday_api_key = os.getenv("MONDAY_API_KEY")
    if not monday_api_key:
        print("❌ MONDAY_API_KEY no encontrada en .env")
        return False
    
    # Query para crear webhook
    query = """
    mutation ($boardId: ID!, $url: String!, $event: WebhookEventType!) {
        create_webhook(board_id: $boardId, url: $url, event: $event) {
            id
            board_id
            url
            event
        }
    }
    """
    
    # Variables para la mutación
    variables = {
        "boardId": str(config.BOARD_ID_GRABACIONES),
        "url": webhook_url,
        "event": "create_pulse"
    }
    
    headers = {
        "Authorization": monday_api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        print(f"📋 Creando webhook para tablero: {config.BOARD_ID_GRABACIONES}")
        response = requests.post(
            "https://api.monday.com/v2",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('create_webhook'):
                webhook_info = data['data']['create_webhook']
                print(f"✅ Webhook creado exitosamente")
                print(f"📊 Webhook ID: {webhook_info.get('id')}")
                print(f"🌐 URL: {webhook_info.get('url')}")
                print(f"📅 Evento: {webhook_info.get('event')}")
                return True
            elif 'errors' in data:
                error_msg = str(data['errors'])
                if "already exists" in error_msg.lower():
                    print("⚠️  Webhook ya existe, intentando crear para update_column_value...")
                    return crear_webhook_update_column(variables, headers)
                else:
                    print(f"❌ Error en Monday.com API: {error_msg}")
                    return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error configurando webhook: {e}")
        return False

def crear_webhook_update_column(variables, headers):
    """Crear webhook para update_column_value"""
    try:
        variables["event"] = "update_column_value"
        
        query = """
        mutation ($boardId: ID!, $url: String!, $event: WebhookEventType!) {
            create_webhook(board_id: $boardId, url: $url, event: $event) {
                id
                board_id
                url
                event
            }
        }
        """
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        response = requests.post(
            "https://api.monday.com/v2",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('create_webhook'):
                webhook_info = data['data']['create_webhook']
                print(f"✅ Webhook para update_column_value creado")
                print(f"📊 Webhook ID: {webhook_info.get('id')}")
                return True
            else:
                print(f"❌ Error creando webhook update_column_value: {data}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error creando webhook update_column_value: {e}")
        return False

def listar_webhooks_existentes():
    """Listar webhooks existentes en Monday.com"""
    print("\n📋 LISTANDO WEBHOOKS EXISTENTES")
    print("=" * 40)
    
    monday_api_key = os.getenv("MONDAY_API_KEY")
    if not monday_api_key:
        print("❌ MONDAY_API_KEY no encontrada")
        return False
    
    query = """
    query ($boardId: ID!) {
        boards(ids: [$boardId]) {
            webhooks {
                id
                url
                event
                config
            }
        }
    }
    """
    
    variables = {
        "boardId": str(config.BOARD_ID_GRABACIONES)
    }
    
    headers = {
        "Authorization": monday_api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post(
            "https://api.monday.com/v2",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('boards'):
                board = data['data']['boards'][0]
                webhooks = board.get('webhooks', [])
                
                if webhooks:
                    print(f"📊 Webhooks encontrados: {len(webhooks)}")
                    for webhook in webhooks:
                        print(f"  - ID: {webhook.get('id')}")
                        print(f"    URL: {webhook.get('url')}")
                        print(f"    Evento: {webhook.get('event')}")
                        print()
                else:
                    print("ℹ️  No se encontraron webhooks")
                
                return True
            else:
                print(f"❌ Error obteniendo webhooks: {data}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error listando webhooks: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 CONFIGURACIÓN AUTOMÁTICA DE WEBHOOK DE MONDAY.COM")
    print("=" * 60)
    
    # Verificar que ngrok está funcionando
    ngrok_url = obtener_url_ngrok()
    if not ngrok_url:
        print("❌ ngrok no está funcionando. Ejecuta 'ngrok http 6754' primero.")
        return
    
    print(f"✅ ngrok funcionando: {ngrok_url}")
    
    # Listar webhooks existentes
    listar_webhooks_existentes()
    
    # Configurar nuevo webhook
    if configurar_webhook_monday():
        print("\n🎉 WEBHOOK DE MONDAY.COM CONFIGURADO EXITOSAMENTE")
        print("=" * 50)
        print("📋 RESUMEN:")
        print(f"  - URL del servidor: {ngrok_url}")
        print(f"  - Webhook Monday: {ngrok_url}/monday-webhook")
        print("\n💡 Ahora puedes:")
        print("  1. Crear elementos en Monday.com")
        print("  2. Cambiar fechas en Monday.com")
        print("  3. Ver la sincronización automática en los logs")
    else:
        print("\n❌ ERROR CONFIGURANDO WEBHOOK DE MONDAY.COM")
        print("💡 Configuración manual:")
        print("  1. Ve a Monday.com → Tu tablero → Configuración")
        print("  2. Integraciones → Webhooks")
        print(f"  3. URL: {ngrok_url}/monday-webhook")
        print("  4. Eventos: create_pulse, update_column_value")

if __name__ == "__main__":
    main()
