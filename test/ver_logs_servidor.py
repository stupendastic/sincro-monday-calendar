#!/usr/bin/env python3
"""
Script para ver los logs del servidor Flask en tiempo real
"""
import subprocess
import sys
import time

def ver_logs_servidor():
    """Muestra los logs del servidor Flask en tiempo real"""
    
    print("📊 LOGS DEL SERVIDOR FLASK")
    print("=" * 50)
    print("🔍 Buscando proceso de Flask...")
    
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
            print("💡 Ejecuta: source venv/bin/activate && python3 app.py")
            return
        
        print(f"✅ Encontrados {len(flask_processes)} proceso(s) de Flask")
        
        # Mostrar información del proceso
        for i, process in enumerate(flask_processes, 1):
            parts = process.split()
            if len(parts) >= 2:
                pid = parts[1]
                print(f"   {i}. PID: {pid}")
        
        print("\n📋 Para ver logs en tiempo real:")
        print("   tail -f /dev/null & python3 app.py")
        print("   (o ejecuta el servidor en otra terminal)")
        
        print("\n🔍 Últimas líneas de log (si existen):")
        print("-" * 30)
        
        # Intentar ver logs recientes
        try:
            # Buscar archivos de log o salida reciente
            log_result = subprocess.run(
                ["find", ".", "-name", "*.log", "-o", "-name", "*.out", "-mtime", "-1"],
                capture_output=True,
                text=True
            )
            
            if log_result.stdout.strip():
                log_files = log_result.stdout.strip().split('\n')
                for log_file in log_files[:3]:  # Solo los 3 primeros
                    print(f"📄 {log_file}")
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            for line in lines[-5:]:  # Últimas 5 líneas
                                print(f"   {line.strip()}")
                    except:
                        pass
            else:
                print("   No se encontraron archivos de log recientes")
                
        except Exception as e:
            print(f"   Error buscando logs: {e}")
        
        print("\n💡 CONSEJOS:")
        print("1. Ejecuta el servidor en una terminal separada:")
        print("   source venv/bin/activate && python3 app.py")
        print("2. En otra terminal, ejecuta este script para monitorear")
        print("3. Haz cambios en Monday.com y observa los logs")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("📊 MONITOR DE LOGS DEL SERVIDOR")
    print("=" * 60)
    
    ver_logs_servidor()
    
    print("\n" + "=" * 60)
    print("🎯 PRÓXIMOS PASOS:")
    print("1. Ejecuta el servidor en una terminal separada")
    print("2. Haz cambios en Monday.com")
    print("3. Observa los logs aquí")

if __name__ == "__main__":
    main()
