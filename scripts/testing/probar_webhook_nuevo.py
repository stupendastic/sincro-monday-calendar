#!/usr/bin/env python3
"""
Script para probar el nuevo webhook de ngrok
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import requests
import json
from datetime import datetime

def probar_webhook_nuevo():
    """Prueba el nuevo webhook de ngrok"""
    
    print("🔄 PROBANDO NUEVO WEBHOOK DE NGROK")
    print("=" * 50)
    
    # Nueva URL de ngrok
    webhook_url = "https://1f6deb6593e0.ngrok-free.app/monday-webhook"
    
    # Datos del item real
    item_id = 9882299305  # Prueba Arnau Calendar Sync 1
    
    print(f"🎯 Probando con item: {item_id}")
    print(f"📡 URL del webhook: {webhook_url}")
    print("=" * 50)
    
    # Simular webhook de actualización de fecha
    payload = {
        "type": "update",
        "boardId": 3324095194,
        "pulseId": item_id,
        "columnId": "fecha56",
        "value": {
            "text": "2025-08-20 18:00:00"  # Nueva fecha para probar
        },
        "previousValue": {
            "text": "2025-08-13 14:00:00"
        },
        "triggerTime": datetime.now().isoformat(),
        "subscriptionId": 12345,
        "userId": 34210704
    }
    
    print(f"📤 Enviando webhook...")
    try:
        response = requests.post(webhook_url, json=payload)
        print(f"✅ Response Status: {response.status_code}")
        print(f"✅ Response Body: {response.text}")
        print("🎉 ¡Webhook enviado correctamente!")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        print("Asegúrate de que ngrok esté funcionando")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    probar_webhook_nuevo()
