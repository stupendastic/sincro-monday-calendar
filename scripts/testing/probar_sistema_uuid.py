#!/usr/bin/env python3
"""
Script para probar el nuevo sistema de UUIDs únicos
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import requests
import json
import time
import uuid

def probar_sistema_uuid():
    """Prueba el sistema de UUIDs únicos"""
    
    print("🧪 PROBADOR DEL SISTEMA DE UUIDs ÚNICOS")
    print("=" * 60)
    
    # URL del webhook
    webhook_url = "https://2e6cc727ffae.ngrok-free.app/monday-webhook"
    
    # Datos del item de prueba
    item_id = 9881971936  # PRUEBA SINCRONIZACIÓN
    
    print(f"🎯 Probando con item: {item_id}")
    print(f"📡 URL del webhook: {webhook_url}")
    print("=" * 60)
    
    # Simular múltiples cambios rápidos
    for i in range(3):
        print(f"\n🔄 PRUEBA {i+1}/3")
        print("-" * 30)
        
        # Generar UUID único para este cambio
        change_uuid = str(uuid.uuid4())
        print(f"🆔 UUID generado: {change_uuid[:8]}...")
        
        # Simular webhook de Monday.com
        webhook_data = {
            "type": "update",
            "boardId": 3324095194,
            "pulseId": item_id,
            "columnId": "fecha56",
            "value": {
                "text": f"2025-08-{15+i} 16:00:00"
            },
            "previousValue": {
                "text": f"2025-08-{14+i} 16:00:00"
            },
            "triggerTime": "2025-08-22T23:30:00.000000",
            "subscriptionId": 12345,
            "userId": 34210704
        }
        
        print(f"📋 Enviando webhook con fecha: {webhook_data['value']['text']}")
        
        try:
            response = requests.post(webhook_url, json=webhook_data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Webhook enviado exitosamente (Status: {response.status_code})")
                response_data = response.json()
                print(f"📊 Respuesta: {response_data.get('message', 'Sin mensaje')}")
            else:
                print(f"❌ Error en webhook (Status: {response.status_code})")
                print(f"📊 Respuesta: {response.text}")
                
        except Exception as e:
            print(f"❌ Error enviando webhook: {e}")
        
        # Esperar un poco entre cambios
        if i < 2:  # No esperar después del último
            print("⏳ Esperando 2 segundos...")
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 PRUEBAS COMPLETADAS")
    print("=" * 60)
    print("📋 Verifica los logs del servidor para ver:")
    print("   - UUIDs únicos generados")
    print("   - Detección de cambios duplicados")
    print("   - Sincronizaciones procesadas")
    print("=" * 60)

def mostrar_instrucciones():
    """Muestra instrucciones para usar el sistema"""
    
    print("\n📋 INSTRUCCIONES:")
    print("=" * 60)
    print("🎯 OBJETIVO:")
    print("   Probar el nuevo sistema de UUIDs únicos que evita")
    print("   falsos positivos en la detección de cambios duplicados")
    print("=" * 60)
    print("🔧 FUNCIONAMIENTO:")
    print("   1. Cada cambio recibe un UUID único")
    print("   2. El sistema verifica si el UUID ya fue procesado")
    print("   3. Solo procesa cambios con UUIDs nuevos")
    print("   4. Limpia UUIDs antiguos automáticamente")
    print("=" * 60)
    print("🧪 PRUEBA:")
    print("   - Se envían 3 webhooks rápidos")
    print("   - Cada uno con un UUID único")
    print("   - El sistema debería procesar todos")
    print("=" * 60)

def main():
    """Función principal"""
    print("🚀 SISTEMA DE UUIDs ÚNICOS - MONDAY ↔ GOOGLE")
    print("=" * 80)
    
    mostrar_instrucciones()
    
    # Preguntar si quiere ejecutar la prueba
    print("\n¿Quieres ejecutar la prueba del sistema de UUIDs? (s/n): ", end="")
    
    try:
        respuesta = input().lower().strip()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            probar_sistema_uuid()
        else:
            print("👋 Prueba cancelada")
    except KeyboardInterrupt:
        print("\n👋 Hasta luego!")

if __name__ == "__main__":
    main()
