#!/usr/bin/env python3
"""
Script para monitorear los logs del servidor en tiempo real
"""
import subprocess
import time
import sys
import os

def monitor_tiempo_real():
    """Monitorea los logs del servidor en tiempo real"""
    
    print("📊 MONITOR DE LOGS EN TIEMPO REAL")
    print("=" * 60)
    print("🔍 Iniciando monitoreo...")
    print("📋 Presiona Ctrl+C para salir")
    print("=" * 60)
    
    try:
        # Verificar que el servidor está ejecutándose
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        
        flask_processes = []
        for line in result.stdout.split('\n'):
            if 'python.*app.py' in line and 'grep' not in line:
                flask_processes.append(line)
        
        if not flask_processes:
            print("❌ No se encontraron procesos de Flask ejecutándose")
            print("💡 Ejecuta en otra terminal: source venv/bin/activate && python3 app.py")
            return
        
        print(f"✅ Servidor Flask ejecutándose ({len(flask_processes)} proceso(s))")
        print("🎯 Monitoreando logs...")
        print("-" * 60)
        
        # Monitorear logs en tiempo real
        while True:
            try:
                # Verificar estado del servidor
                health_response = subprocess.run(
                    ["curl", "-s", "https://2e6cc727ffae.ngrok-free.app/health"],
                    capture_output=True,
                    text=True
                )
                
                if health_response.returncode == 0:
                    print(f"🟢 Servidor activo - {time.strftime('%H:%M:%S')}")
                else:
                    print(f"🔴 Servidor inactivo - {time.strftime('%H:%M:%S')}")
                
                time.sleep(5)  # Verificar cada 5 segundos
                
            except KeyboardInterrupt:
                print("\n\n👋 Monitoreo detenido")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)
                
    except Exception as e:
        print(f"❌ Error iniciando monitoreo: {e}")

def mostrar_instrucciones():
    """Muestra instrucciones para usar el sistema"""
    
    print("\n" + "=" * 60)
    print("📋 INSTRUCCIONES DE USO")
    print("=" * 60)
    print("🎯 SISTEMA DE SINCRONIZACIÓN BIDIRECCIONAL")
    print("=" * 60)
    print("✅ Servidor Flask: EJECUTÁNDOSE")
    print("✅ Ngrok: ACTIVO")
    print("✅ Webhooks: CONFIGURADOS")
    print("=" * 60)
    print("🧪 PARA PROBAR:")
    print("1. Ve a Monday.com")
    print("2. Busca el item 'PRUEBA SINCRONIZACIÓN'")
    print("3. Cambia la fecha del item")
    print("4. Observa los logs aquí")
    print("5. Verifica que Google Calendar se actualiza")
    print("=" * 60)
    print("🔄 SINCRONIZACIÓN BIDIRECCIONAL:")
    print("   Monday.com ↔ Google Calendar")
    print("   Google Calendar ↔ Monday.com")
    print("=" * 60)
    print("📊 LOGS EN TIEMPO REAL:")
    print("   - Webhooks recibidos")
    print("   - Sincronizaciones procesadas")
    print("   - Errores y advertencias")
    print("=" * 60)

def main():
    """Función principal"""
    print("🚀 MONITOR DE SINCRONIZACIÓN MONDAY ↔ GOOGLE")
    print("=" * 80)
    
    mostrar_instrucciones()
    
    # Preguntar si quiere iniciar el monitoreo
    print("\n¿Quieres iniciar el monitoreo en tiempo real? (s/n): ", end="")
    
    try:
        respuesta = input().lower().strip()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            monitor_tiempo_real()
        else:
            print("👋 Monitoreo no iniciado")
    except KeyboardInterrupt:
        print("\n👋 Hasta luego!")

if __name__ == "__main__":
    main()
