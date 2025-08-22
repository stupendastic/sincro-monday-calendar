#!/usr/bin/env python3
"""
Script para configurar automáticamente los webhooks de Google Calendar
"""

import os
import json
import requests
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
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

def configurar_webhook_google_calendar():
    """Configurar webhook para el calendario maestro"""
    print("🔧 CONFIGURANDO WEBHOOK DE GOOGLE CALENDAR")
    print("=" * 50)
    
    # Obtener URL de ngrok
    ngrok_url = obtener_url_ngrok()
    if not ngrok_url:
        print("❌ No se pudo obtener la URL de ngrok")
        return False
    
    webhook_url = f"{ngrok_url}/google-webhook"
    print(f"🌐 URL del webhook: {webhook_url}")
    
    try:
        # Obtener servicio de Google Calendar
        google_service = get_calendar_service()
        if not google_service:
            print("❌ No se pudo inicializar el servicio de Google Calendar")
            return False
        
        # Configurar webhook para el calendario maestro
        calendar_id = config.MASTER_CALENDAR_ID
        print(f"📅 Configurando webhook para calendario: {calendar_id}")
        
        # Crear el canal de notificación con ID único
        import time
        unique_id = f"stupendastic-sync-{int(time.time())}"
        channel_body = {
            'id': unique_id,
            'type': 'web_hook',
            'address': webhook_url,
            'token': 'stupendastic-sync-token'
        }
        
        # Crear el webhook
        response = google_service.events().watch(
            calendarId=calendar_id,
            body=channel_body
        ).execute()
        
        print(f"✅ Webhook configurado exitosamente")
        print(f"📊 Channel ID: {response.get('id')}")
        print(f"📅 Resource ID: {response.get('resourceId')}")
        print(f"⏰ Expiración: {response.get('expiration')}")
        
        # Guardar en el archivo de mapeo
        channel_map = {}
        try:
            with open("google_channel_map.json", 'r') as f:
                channel_map = json.load(f)
        except FileNotFoundError:
            pass
        
        channel_map[response.get('id')] = calendar_id
        
        with open("google_channel_map.json", 'w') as f:
            json.dump(channel_map, f, indent=2)
        
        print(f"💾 Mapeo guardado en google_channel_map.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando webhook: {e}")
        return False

def configurar_webhooks_personales():
    """Configurar webhooks para calendarios personales"""
    print("\n👥 CONFIGURANDO WEBHOOKS DE CALENDARIOS PERSONALES")
    print("=" * 50)
    
    # Obtener URL de ngrok
    ngrok_url = obtener_url_ngrok()
    if not ngrok_url:
        print("❌ No se pudo obtener la URL de ngrok")
        return False
    
    webhook_url = f"{ngrok_url}/google-webhook"
    
    try:
        google_service = get_calendar_service()
        if not google_service:
            print("❌ No se pudo inicializar el servicio de Google Calendar")
            return False
        
        # Cargar mapeo existente
        channel_map = {}
        try:
            with open("google_channel_map.json", 'r') as f:
                channel_map = json.load(f)
        except FileNotFoundError:
            pass
        
        for i, profile in enumerate(config.FILMMAKER_PROFILES):
            calendar_id = profile.get('calendar_id')
            if not calendar_id:
                print(f"⚠️  {profile['monday_name']} no tiene calendar_id configurado")
                continue
            
            print(f"📅 Configurando webhook para {profile['monday_name']}: {calendar_id}")
            
            # Crear ID único para el canal
            import time
            channel_id = f"stupendastic-personal-{i:05d}-{int(time.time())}"
            
            # Crear el canal de notificación
            channel_body = {
                'id': channel_id,
                'type': 'web_hook',
                'address': webhook_url,
                'token': f'stupendastic-personal-{i}'
            }
            
            try:
                # Crear el webhook
                response = google_service.events().watch(
                    calendarId=calendar_id,
                    body=channel_body
                ).execute()
                
                print(f"✅ Webhook configurado para {profile['monday_name']}")
                print(f"📊 Channel ID: {response.get('id')}")
                
                # Guardar en el mapeo
                channel_map[response.get('id')] = calendar_id
                
            except Exception as e:
                print(f"❌ Error configurando webhook para {profile['monday_name']}: {e}")
        
        # Guardar mapeo actualizado
        with open("google_channel_map.json", 'w') as f:
            json.dump(channel_map, f, indent=2)
        
        print(f"💾 Mapeo actualizado guardado")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando webhooks personales: {e}")
        return False

def verificar_webhooks():
    """Verificar que los webhooks están funcionando"""
    print("\n🔍 VERIFICANDO WEBHOOKS")
    print("=" * 30)
    
    # Verificar archivo de mapeo
    try:
        with open("google_channel_map.json", 'r') as f:
            channel_map = json.load(f)
        
        print(f"📊 Canales configurados: {len(channel_map)}")
        for channel_id, calendar_id in channel_map.items():
            print(f"  - {channel_id} → {calendar_id}")
        
    except FileNotFoundError:
        print("❌ Archivo google_channel_map.json no encontrado")
        return False
    
    # Verificar que el servidor responde
    ngrok_url = obtener_url_ngrok()
    if ngrok_url:
        try:
            response = requests.get(f"{ngrok_url}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Servidor responde correctamente")
                return True
            else:
                print(f"❌ Servidor no responde: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error verificando servidor: {e}")
            return False
    
    return False

def main():
    """Función principal"""
    print("🚀 CONFIGURACIÓN AUTOMÁTICA DE WEBHOOKS")
    print("=" * 50)
    
    # Verificar que ngrok está funcionando
    ngrok_url = obtener_url_ngrok()
    if not ngrok_url:
        print("❌ ngrok no está funcionando. Ejecuta 'ngrok http 6754' primero.")
        return
    
    print(f"✅ ngrok funcionando: {ngrok_url}")
    
    # Configurar webhook del calendario maestro
    if configurar_webhook_google_calendar():
        print("✅ Webhook del calendario maestro configurado")
    else:
        print("❌ Error configurando webhook del calendario maestro")
        return
    
    # Configurar webhooks de calendarios personales
    if configurar_webhooks_personales():
        print("✅ Webhooks de calendarios personales configurados")
    else:
        print("❌ Error configurando webhooks personales")
    
    # Verificar configuración
    if verificar_webhooks():
        print("\n🎉 CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 50)
        print("📋 RESUMEN:")
        print(f"  - URL del servidor: {ngrok_url}")
        print(f"  - Webhook Monday: {ngrok_url}/monday-webhook")
        print(f"  - Webhook Google: {ngrok_url}/google-webhook")
        print("\n💡 Ahora puedes:")
        print("  1. Crear elementos en Monday.com")
        print("  2. Cambiar fechas en Google Calendar")
        print("  3. Ver la sincronización automática en los logs")
    else:
        print("\n❌ ERROR EN LA VERIFICACIÓN")

if __name__ == "__main__":
    main()
