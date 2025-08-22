#!/usr/bin/env python3
"""
Script para simular webhook de creación/actualización de item
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import requests
import json
from datetime import datetime

def simular_webhook_creacion():
    """Simula un webhook de Monday.com para el item creado"""
    
    print("🔄 SIMULANDO WEBHOOK DE CREACIÓN")
    print("=" * 50)
    
    # URL del webhook local
    webhook_url = "http://127.0.0.1:6754/monday-webhook"
    
    # Datos del item real
    item_id = 9882299305  # Prueba Arnau Calendar Sync 1
    
    print(f"🎯 Simulando webhook para item: {item_id}")
    print(f"📡 URL: {webhook_url}")
    print("=" * 50)
    
    # Simular webhook de actualización de fecha
    payload = {
        "type": "update",
        "boardId": 3324095194,
        "pulseId": item_id,
        "columnId": "fecha56",
        "value": {
            "text": "2025-08-13 14:00:00"
        },
        "previousValue": {
            "text": ""
        },
        "triggerTime": datetime.now().isoformat(),
        "subscriptionId": 12345,
        "userId": 34210704
    }
    
    print("📤 Enviando webhook...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(webhook_url, json=payload)
        print(f"✅ Response Status: {response.status_code}")
        print(f"✅ Response Body: {response.text}")
        
        if response.status_code == 200:
            print("🎉 Webhook enviado exitosamente")
            print("💡 Revisa los logs del servidor para ver el procesamiento")
        else:
            print("❌ Error en el webhook")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        print("Asegúrate de que el servidor Flask esté corriendo en http://127.0.0.1:6754")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def main():
    """Función principal"""
    print("🔄 SIMULADOR DE WEBHOOK DE CREACIÓN")
    print("=" * 60)
    
    try:
        simular_webhook_creacion()
    except KeyboardInterrupt:
        print("\n👋 Simulación cancelada")
    except Exception as e:
        print(f"❌ Error durante la simulación: {e}")

if __name__ == "__main__":
    main()
