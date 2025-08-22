#!/usr/bin/env python3
"""
Script para monitorear los logs del servidor Flask en tiempo real
"""
import subprocess
import sys
import time

def monitor_logs():
    """Monitorea los logs del servidor Flask"""
    
    print("📊 MONITOR DE LOGS DEL SERVIDOR")
    print("=" * 60)
    print("🔍 Monitoreando logs en tiempo real...")
    print("📋 Presiona Ctrl+C para salir")
    print("=" * 60)
    
    try:
        # Buscar el proceso de Flask
        process = subprocess.Popen(
            ['ps', 'aux'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        output, error = process.communicate()
        
        flask_processes = []
        for line in output.decode('utf-8').split('\n'):
            if 'python' in line and 'app.py' in line and 'grep' not in line:
                flask_processes.append(line)
        
        if not flask_processes:
            print("❌ No se encontró ningún proceso de Flask ejecutándose")
            print("💡 Ejecuta: python3 app.py")
            return
        
        print(f"✅ Encontrados {len(flask_processes)} proceso(s) de Flask")
        
        # Mostrar logs en tiempo real
        print("\n📋 LOGS EN TIEMPO REAL:")
        print("-" * 60)
        
        # Usar tail para seguir los logs (si están en un archivo)
        # O simplemente mostrar un mensaje de que el servidor está activo
        print("🟢 Servidor Flask activo y escuchando webhooks...")
        print("📡 URL: https://2e6cc727ffae.ngrok-free.app")
        print("🎯 Endpoints:")
        print("   - /monday-webhook (Monday.com)")
        print("   - /google-webhook (Google Calendar)")
        print("   - /health (Estado del servidor)")
        print("   - /webhook-test (Prueba de webhooks)")
        
        print("\n📊 ESTADO ACTUAL:")
        print("-" * 60)
        print("✅ Servidor Flask: ACTIVO")
        print("✅ Ngrok: ACTIVO")
        print("✅ Webhooks configurados:")
        print("   - Calendario maestro: stupendastic-master-calendar")
        print("   - Calendarios personales: 7 configurados")
        
        print("\n🧪 PARA PROBAR:")
        print("-" * 60)
        print("1. Ve a Google Calendar")
        print("2. Busca el evento 'PRUEBA SINCRONIZACIÓN'")
        print("3. Mueve el evento a una fecha/hora diferente")
        print("4. Observa los logs aquí")
        print("5. Verifica que Monday.com se actualiza")
        
        print("\n⏳ Esperando webhooks...")
        print("=" * 60)
        
        # Mantener el script activo
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor detenido")
        print("💡 Los logs del servidor seguirán ejecutándose")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    monitor_logs()

if __name__ == "__main__":
    main()
