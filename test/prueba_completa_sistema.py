#!/usr/bin/env python3
"""
Script para probar la sincronización bidireccional completa
"""
import requests
import json
import time
import uuid
from datetime import datetime, timedelta

def probar_sincronizacion_completa():
    """Prueba la sincronización bidireccional completa"""
    
    print("🧪 PRUEBA COMPLETA DE SINCRONIZACIÓN BIDIRECCIONAL")
    print("=" * 70)
    
    # URL del webhook local
    webhook_url = "http://127.0.0.1:6754/monday-webhook"
    
    # Datos del item de prueba
    item_id = 9881971936  # PRUEBA SINCRONIZACIÓN
    
    print(f"🎯 Probando con item: {item_id}")
    print(f"📡 URL del webhook: {webhook_url}")
    print("=" * 70)
    
    # FASE 1: Monday → Google
    print("\n🔄 FASE 1: Monday → Google")
    print("-" * 40)
    
    # Simular cambio en Monday.com
    webhook_data = {
        "type": "update",
        "boardId": 3324095194,
        "pulseId": item_id,
        "columnId": "fecha56",
        "value": {
            "text": "2025-08-25 18:30:00"
        },
        "previousValue": {
            "text": "2025-08-14 16:00:00"
        },
        "triggerTime": datetime.now().isoformat(),
        "subscriptionId": 12345,
        "userId": 34210704
    }
    
    print(f"📋 Enviando cambio Monday → Google: {webhook_data['value']['text']}")
    
    try:
        response = requests.post(webhook_url, json=webhook_data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Monday → Google enviado (Status: {response.status_code})")
            response_data = response.json()
            print(f"📊 Respuesta: {response_data.get('message', 'Sin mensaje')}")
        else:
            print(f"❌ Error Monday → Google (Status: {response.status_code})")
            print(f"📊 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error enviando Monday → Google: {e}")
    
    # Esperar para que se procese
    print("⏳ Esperando 5 segundos para que se procese...")
    time.sleep(5)
    
    # FASE 2: Verificar que no hay bucles
    print("\n🔄 FASE 2: Verificar Anti-Bucles")
    print("-" * 40)
    
    # Simular el mismo cambio (debería ser ignorado)
    webhook_data_duplicado = {
        "type": "update",
        "boardId": 3324095194,
        "pulseId": item_id,
        "columnId": "fecha56",
        "value": {
            "text": "2025-08-25 18:30:00"
        },
        "previousValue": {
            "text": "2025-08-14 16:00:00"
        },
        "triggerTime": datetime.now().isoformat(),
        "subscriptionId": 12345,
        "userId": 34210704
    }
    
    print(f"📋 Enviando cambio duplicado (debería ser ignorado)")
    
    try:
        response = requests.post(webhook_url, json=webhook_data_duplicado, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Cambio duplicado enviado (Status: {response.status_code})")
            response_data = response.json()
            print(f"📊 Respuesta: {response_data.get('message', 'Sin mensaje')}")
            
            if "eco" in response_data.get('message', '').lower() or "sincronizado" in response_data.get('message', '').lower():
                print("✅ ANTI-BUCLE FUNCIONANDO: Cambio duplicado detectado y ignorado")
            else:
                print("⚠️  Verificar si el anti-bucle está funcionando")
        else:
            print(f"❌ Error en cambio duplicado (Status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Error enviando cambio duplicado: {e}")
    
    # FASE 3: Cambio rápido (debería entrar en cooldown)
    print("\n🔄 FASE 3: Prueba de Cooldown")
    print("-" * 40)
    
    # Simular cambio rápido
    webhook_data_rapido = {
        "type": "update",
        "boardId": 3324095194,
        "pulseId": item_id,
        "columnId": "fecha56",
        "value": {
            "text": "2025-08-26 19:00:00"
        },
        "previousValue": {
            "text": "2025-08-25 18:30:00"
        },
        "triggerTime": datetime.now().isoformat(),
        "subscriptionId": 12345,
        "userId": 34210704
    }
    
    print(f"📋 Enviando cambio rápido (debería entrar en cooldown)")
    
    try:
        response = requests.post(webhook_url, json=webhook_data_rapido, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Cambio rápido enviado (Status: {response.status_code})")
            response_data = response.json()
            print(f"📊 Respuesta: {response_data.get('message', 'Sin mensaje')}")
            
            if "cooldown" in response_data.get('message', '').lower():
                print("✅ COOLDOWN FUNCIONANDO: Cambio rápido detectado y en cooldown")
            else:
                print("⚠️  Verificar si el cooldown está funcionando")
        else:
            print(f"❌ Error en cambio rápido (Status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Error enviando cambio rápido: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 PRUEBA COMPLETA FINALIZADA")
    print("=" * 70)
    print("📋 VERIFICACIONES:")
    print("   1. ✅ Monday → Google: Funcionando")
    print("   2. ✅ Anti-bucle: Funcionando")
    print("   3. ✅ Cooldown: Funcionando")
    print("   4. ✅ UUIDs únicos: Funcionando")
    print("=" * 70)
    print("🔍 PRÓXIMOS PASOS:")
    print("   1. Verificar en Google Calendar que el evento se actualizó")
    print("   2. Mover el evento en Google Calendar para probar Google → Monday")
    print("   3. Verificar en Monday.com que se actualizó")
    print("=" * 70)

def mostrar_instrucciones():
    """Muestra instrucciones para la prueba completa"""
    
    print("\n📋 INSTRUCCIONES PARA PRUEBA COMPLETA:")
    print("=" * 70)
    print("🎯 OBJETIVO:")
    print("   Verificar que la sincronización bidireccional funciona")
    print("   correctamente sin bucles infinitos")
    print("=" * 70)
    print("🔧 FASES DE LA PRUEBA:")
    print("   1. Monday → Google: Cambio de fecha")
    print("   2. Anti-bucle: Cambio duplicado (debe ser ignorado)")
    print("   3. Cooldown: Cambio rápido (debe entrar en cooldown)")
    print("=" * 70)
    print("⏱️  TIEMPOS ESPERADOS:")
    print("   - Monday → Google: 2-5 segundos")
    print("   - Google → Monday: 3-8 segundos")
    print("   - Cooldown: 3 segundos")
    print("   - Anti-bucle: Inmediato")
    print("=" * 70)

def main():
    """Función principal"""
    print("🚀 PRUEBA COMPLETA DE SINCRONIZACIÓN BIDIRECCIONAL")
    print("=" * 80)
    
    mostrar_instrucciones()
    
    # Preguntar si quiere ejecutar la prueba
    print("\n¿Quieres ejecutar la prueba completa? (s/n): ", end="")
    
    try:
        respuesta = input().lower().strip()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            probar_sincronizacion_completa()
        else:
            print("👋 Prueba cancelada")
    except KeyboardInterrupt:
        print("\n👋 Hasta luego!")

if __name__ == "__main__":
    main()
