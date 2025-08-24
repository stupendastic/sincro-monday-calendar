#!/usr/bin/env python3
"""
Script simple para renovar webhooks de Google Calendar usando credenciales de servicio.
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def get_current_ngrok_url():
    """Obtiene la URL actual de ngrok."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                return tunnels[0].get('public_url')
    except Exception as e:
        print(f"⚠️ Error obteniendo URL de ngrok: {e}")
    
    return None

def load_webhooks_info():
    """Carga la información de webhooks existentes."""
    webhooks_file = Path("config/webhooks/webhooks_personales_info.json")
    if not webhooks_file.exists():
        print("❌ No se encontró el archivo de webhooks")
        return None
    
    try:
        with open(webhooks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando webhooks: {e}")
        return None

def create_google_service():
    """Crea el servicio de Google Calendar usando OAuth."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        
        # El archivo config/token.json almacena los tokens de acceso y actualización del usuario
        if os.path.exists('config/token.json'):
            creds = Credentials.from_authorized_user_file('config/token.json', SCOPES)
        
        # Si no hay credenciales válidas disponibles, deja que el usuario se autentique
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"❌ Error refrescando credenciales: {e}")
                    return None
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"❌ Error en autenticación: {e}")
                    return None
            
            # Guarda las credenciales para la próxima ejecución
            try:
                with open('config/token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"❌ Error guardando credenciales: {e}")
        
        # Crear servicio
        service = build('calendar', 'v3', credentials=creds)
        return service
        
    except Exception as e:
        print(f"❌ Error creando servicio de Google Calendar: {e}")
        return None

def delete_old_webhook(service, calendar_id, resource_id):
    """Elimina un webhook existente."""
    try:
        service.events().watch().stop(
            calendarId=calendar_id,
            resourceId=resource_id
        ).execute()
        print(f"   ✅ Webhook eliminado")
        return True
    except Exception as e:
        print(f"   ⚠️ Error eliminando webhook: {e}")
        return False

def create_new_webhook(service, calendar_id, calendar_name, new_webhook_url):
    """Crea un nuevo webhook."""
    try:
        # Configuración del webhook
        webhook_config = {
            'id': f"stupendastic-personal-{calendar_id.split('@')[0][-8:]}",
            'type': 'web_hook',
            'address': new_webhook_url,
            'params': {
                'ttl': '604800'  # 7 días
            }
        }
        
        # Crear el webhook
        result = service.events().watch(
            calendarId=calendar_id,
            body=webhook_config
        ).execute()
        
        print(f"   ✅ Nuevo webhook creado")
        return result
    except Exception as e:
        print(f"   ❌ Error creando webhook: {e}")
        return None

def main():
    """Función principal."""
    print("🔄 RENOVACIÓN SIMPLE DE WEBHOOKS DE GOOGLE CALENDAR")
    print("=" * 55)
    print()
    
    # 1. Obtener URL actual de ngrok
    print("1. 🔍 Obteniendo URL actual de ngrok...")
    current_ngrok_url = get_current_ngrok_url()
    if not current_ngrok_url:
        print("❌ No se pudo obtener la URL de ngrok")
        return
    
    new_webhook_url = f"{current_ngrok_url}/google-webhook"
    print(f"   ✅ URL actual: {current_ngrok_url}")
    print(f"   ✅ Nueva URL de webhook: {new_webhook_url}")
    print()
    
    # 2. Cargar información de webhooks existentes
    print("2. 📂 Cargando información de webhooks existentes...")
    webhooks_data = load_webhooks_info()
    if not webhooks_data:
        print("❌ No se pudo cargar la información de webhooks")
        return
    
    existing_webhooks = webhooks_data.get('webhooks_personales', [])
    print(f"   ✅ {len(existing_webhooks)} webhooks encontrados")
    print()
    
    # 3. Verificar si las URLs son diferentes
    first_webhook = existing_webhooks[0] if existing_webhooks else None
    if first_webhook and first_webhook.get('webhook_url') == new_webhook_url:
        print("✅ Las URLs de webhooks ya están actualizadas")
        print(f"   URL actual: {first_webhook.get('webhook_url')}")
        return
    
    print("3. 🔄 Renovando webhooks...")
    print(f"   URL anterior: {first_webhook.get('webhook_url') if first_webhook else 'N/A'}")
    print(f"   URL nueva: {new_webhook_url}")
    print()
    
    # 4. Obtener servicio de Google Calendar
    print("4. 🔑 Conectando con Google Calendar API...")
    service = create_google_service()
    if not service:
        print("❌ No se pudo conectar con Google Calendar API")
        return
    print("   ✅ Conexión exitosa")
    print()
    
    # 5. Renovar cada webhook
    print("5. 🔄 Procesando webhooks...")
    successful_updates = 0
    failed_updates = 0
    
    for i, webhook in enumerate(existing_webhooks, 1):
        calendar_id = webhook.get('calendar_id')
        calendar_name = webhook.get('calendar_name')
        resource_id = webhook.get('resource_id')
        
        print(f"   [{i}/{len(existing_webhooks)}] {calendar_name}")
        
        # Eliminar webhook anterior
        delete_old_webhook(service, calendar_id, resource_id)
        
        # Crear nuevo webhook
        time.sleep(2)  # Pausa para evitar rate limiting
        new_webhook_result = create_new_webhook(service, calendar_id, calendar_name, new_webhook_url)
        
        if new_webhook_result:
            # Actualizar información del webhook
            webhook.update({
                'webhook_url': new_webhook_url,
                'resource_id': new_webhook_result.get('resourceId'),
                'expiration': new_webhook_result.get('expiration'),
                'updated_at': datetime.now().isoformat()
            })
            successful_updates += 1
            print(f"      ✅ Renovado exitosamente")
        else:
            failed_updates += 1
            print(f"      ❌ Error renovando webhook")
        
        print()
    
    # 6. Guardar información actualizada
    print("6. 💾 Guardando información actualizada...")
    webhooks_file = Path("config/webhooks/webhooks_personales_info.json")
    
    # Crear backup
    if webhooks_file.exists():
        backup_file = webhooks_file.with_suffix('.json.backup')
        webhooks_file.rename(backup_file)
        print(f"   📁 Backup creado: {backup_file}")
    
    # Guardar nueva información
    try:
        with open(webhooks_file, 'w', encoding='utf-8') as f:
            json.dump(webhooks_data, f, indent=2, ensure_ascii=False)
        print(f"   💾 Información actualizada: {webhooks_file}")
    except Exception as e:
        print(f"   ❌ Error guardando: {e}")
    print()
    
    # 7. Resumen
    print("📊 RESUMEN DE RENOVACIÓN")
    print("=" * 30)
    print(f"✅ Webhooks renovados exitosamente: {successful_updates}")
    print(f"❌ Webhooks con errores: {failed_updates}")
    print(f"📁 Total procesados: {len(existing_webhooks)}")
    print()
    print(f"🔗 Nueva URL de webhook: {new_webhook_url}")
    print(f"⏰ Fecha de renovación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if successful_updates > 0:
        print("✅ Renovación completada exitosamente")
        print("   Los webhooks ahora apuntan a la URL correcta de ngrok")
    else:
        print("❌ No se pudo renovar ningún webhook")
        print("   Revisa los errores anteriores")

if __name__ == "__main__":
    main()
