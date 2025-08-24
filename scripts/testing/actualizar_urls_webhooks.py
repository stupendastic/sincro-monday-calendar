#!/usr/bin/env python3
"""
Script simple para actualizar las URLs de webhooks en el archivo de configuración.
Esto es útil cuando ngrok cambia de URL pero los webhooks de Google siguen funcionando.
"""

import json
import requests
from datetime import datetime
from pathlib import Path

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

def update_webhooks_urls():
    """Actualiza las URLs de webhooks en el archivo de configuración."""
    print("🔄 ACTUALIZACIÓN DE URLs DE WEBHOOKS")
    print("=" * 40)
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
    
    # 2. Cargar archivo de webhooks
    webhooks_file = Path("config/webhooks/webhooks_personales_info.json")
    if not webhooks_file.exists():
        print("❌ No se encontró el archivo de webhooks")
        return
    
    try:
        with open(webhooks_file, 'r', encoding='utf-8') as f:
            webhooks_data = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando webhooks: {e}")
        return
    
    existing_webhooks = webhooks_data.get('webhooks_personales', [])
    print(f"2. 📂 Cargando {len(existing_webhooks)} webhooks...")
    
    # 3. Verificar si las URLs son diferentes
    first_webhook = existing_webhooks[0] if existing_webhooks else None
    if first_webhook and first_webhook.get('webhook_url') == new_webhook_url:
        print("✅ Las URLs de webhooks ya están actualizadas")
        print(f"   URL actual: {first_webhook.get('webhook_url')}")
        return
    
    print(f"3. 🔄 Actualizando URLs...")
    print(f"   URL anterior: {first_webhook.get('webhook_url') if first_webhook else 'N/A'}")
    print(f"   URL nueva: {new_webhook_url}")
    print()
    
    # 4. Actualizar URLs
    updated_count = 0
    for webhook in existing_webhooks:
        old_url = webhook.get('webhook_url', '')
        if old_url != new_webhook_url:
            webhook['webhook_url'] = new_webhook_url
            webhook['updated_at'] = datetime.now().isoformat()
            updated_count += 1
            print(f"   ✅ {webhook.get('calendar_name', 'Unknown')}: {old_url} → {new_webhook_url}")
    
    # 5. Actualizar metadatos
    webhooks_data['updated_at'] = datetime.now().isoformat()
    webhooks_data['previous_created_at'] = webhooks_data.get('created_at')
    
    print()
    print(f"4. 💾 Guardando cambios...")
    
    # Crear backup
    backup_file = webhooks_file.with_suffix('.json.backup')
    if webhooks_file.exists():
        webhooks_file.rename(backup_file)
        print(f"   📁 Backup creado: {backup_file}")
    
    # Guardar archivo actualizado
    try:
        with open(webhooks_file, 'w', encoding='utf-8') as f:
            json.dump(webhooks_data, f, indent=2, ensure_ascii=False)
        print(f"   💾 Archivo actualizado: {webhooks_file}")
    except Exception as e:
        print(f"   ❌ Error guardando: {e}")
        return
    
    print()
    print("📊 RESUMEN DE ACTUALIZACIÓN")
    print("=" * 30)
    print(f"✅ URLs actualizadas: {updated_count}")
    print(f"📁 Total webhooks: {len(existing_webhooks)}")
    print(f"🔗 Nueva URL: {new_webhook_url}")
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if updated_count > 0:
        print("✅ Actualización completada exitosamente")
        print("   Las URLs de webhooks han sido actualizadas en la configuración")
        print()
        print("⚠️  IMPORTANTE:")
        print("   - Los webhooks de Google Calendar pueden seguir funcionando")
        print("   - Si hay problemas, ejecuta el script de renovación completa")
        print("   - Verifica que el servidor esté funcionando en la nueva URL")
    else:
        print("ℹ️  No se necesitaron actualizaciones")

if __name__ == "__main__":
    update_webhooks_urls()
