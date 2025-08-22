#!/usr/bin/env python3
"""
Script para ver los logs del servidor en tiempo real
"""
import subprocess
import time
import sys

def ver_logs_tiempo_real():
    """Muestra los logs del servidor en tiempo real"""
    
    print("📊 LOGS DEL SERVIDOR EN TIEMPO REAL")
    print("=" * 60)
    print("🔍 Iniciando monitoreo...")
    print("📋 Presiona Ctrl+C para salir")
    print("=" * 60)
    
    try:
        # Buscar el proceso de Flask
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
                
                time.sleep(2)  # Verificar cada 2 segundos
                
            except KeyboardInterrupt:
                print("\n\n👋 Monitoreo detenido")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(2)
                
    except Exception as e:
        print(f"❌ Error iniciando monitoreo: {e}")

def main():
    """Función principal"""
    print("📊 MONITOR DE LOGS EN TIEMPO REAL")
    print("=" * 80)
    
    print("💡 INSTRUCCIONES:")
    print("1. Ejecuta este script en una terminal")
    print("2. En otra terminal, haz cambios en Monday.com")
    print("3. Observa los logs aquí")
    print("=" * 80)
    
    ver_logs_tiempo_real()

if __name__ == "__main__":
    main()
