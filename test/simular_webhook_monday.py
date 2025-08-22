#!/usr/bin/env python3
"""
Script para simular un webhook de Monday.com
"""
import requests
import json
from datetime import datetime

def simular_webhook_monday():
    """Simula un webhook de Monday.com"""
    
    print("🧪 SIMULANDO WEBHOOK DE MONDAY.COM")
    print("=" * 50)
    
    # URL del webhook
    webhook_url = "https://2e6cc727ffae.ngrok-free.app/monday-webhook"
    
    # Datos del webhook de Monday.com (formato real)
    webhook_data = {
        "type": "update",
        "boardId": 3324095194,
        "pulseId": 9881971936,  # ID del item que creamos
        "columnId": "fecha56",  # Columna de fecha
        "value": {
            "text": "2025-08-27 15:30:00"  # Nueva fecha
        },
        "previousValue": {
            "text": "2025-08-23 14:00:00"  # Fecha anterior
        },
        "triggerTime": datetime.now().isoformat(),
        "subscriptionId": 12345,
        "userId": 34210704  # Arnau Admin
    }
    
    print(f"📡 Enviando webhook a: {webhook_url}")
    print(f"📋 Datos:")
    print(f"   Board ID: {webhook_data['boardId']}")
    print(f"   Item ID: {webhook_data['pulseId']}")
    print(f"   Columna: {webhook_data['columnId']}")
    print(f"   Nueva fecha: {webhook_data['value']['text']}")
    print(f"   Usuario: {webhook_data['userId']}")
    
    try:
        # Enviar el webhook
        response = requests.post(
            webhook_url,
            json=webhook_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n📊 Respuesta:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Webhook enviado exitosamente")
            print(f"🎯 El servidor debería haber procesado la sincronización")
        else:
            print(f"❌ Error enviando webhook")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 SIMULADOR DE WEBHOOK MONDAY.COM")
    print("=" * 60)
    
    success = simular_webhook_monday()
    
    if success:
        print("\n🎉 ¡WEBHOOK SIMULADO!")
        print("Verifica los logs del servidor para ver si procesó la sincronización")
    else:
        print("\n❌ ERROR SIMULANDO WEBHOOK")

if __name__ == "__main__":
    main()
