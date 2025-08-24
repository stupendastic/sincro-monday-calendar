#!/usr/bin/env python3
"""
Monitor en Tiempo Real para Sistema de Sincronización Monday ↔ Google Calendar
Permite monitorear las sincronizaciones en tiempo real y detectar bucles.
"""

import sys
import time
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import config
    from scripts.testing.test_sync_system import SyncMonitor
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)


class RealtimeSyncMonitor:
    """Monitor en tiempo real para sincronizaciones."""
    
    def __init__(self, server_url="http://localhost:6754"):
        self.server_url = server_url
        self.monitor = SyncMonitor()
        self.running = False
        self.check_interval = 5  # segundos
        
    def start_monitoring(self):
        """Inicia el monitoreo en tiempo real."""
        print("🚀 Iniciando monitor en tiempo real...")
        print(f"📡 Conectando a servidor: {self.server_url}")
        print(f"⏱️  Intervalo de verificación: {self.check_interval} segundos")
        print("🛑 Presiona Ctrl+C para detener\n")
        
        self.running = True
        
        try:
            while self.running:
                self.check_sync_status()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido por el usuario")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Detiene el monitoreo."""
        self.running = False
        print("📊 Resumen final:")
        self.monitor.print_summary()
    
    def check_sync_status(self):
        """Verifica el estado de sincronización del servidor."""
        try:
            # Verificar salud del servidor
            health_response = requests.get(f"{self.server_url}/health", timeout=5)
            if health_response.status_code != 200:
                print(f"⚠️  Servidor no responde: {health_response.status_code}")
                return
            
            # Obtener estadísticas de sincronización
            stats_response = requests.get(f"{self.server_url}/debug/sync-monitor", timeout=5)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                self.display_stats(stats)
            else:
                print(f"⚠️  No se pudieron obtener estadísticas: {stats_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error conectando al servidor: {e}")
        except Exception as e:
            print(f"❌ Error en verificación: {e}")
    
    def display_stats(self, stats):
        """Muestra las estadísticas de sincronización."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if 'statistics' in stats:
            stats_data = stats['statistics']
            
            print(f"[{timestamp}] 📊 Estado del Sistema:")
            print(f"   Total de estados: {stats_data.get('total_states', 0)}")
            print(f"   Última limpieza: {stats_data.get('last_cleanup', 'N/A')}")
            print(f"   Estados antiguos eliminados: {stats_data.get('old_states_removed', 0)}")
            
            # Mostrar últimas sincronizaciones si están disponibles
            if 'last_syncs' in stats:
                last_syncs = stats['last_syncs']
                if last_syncs:
                    print(f"   Últimas sincronizaciones: {len(last_syncs)}")
                    
                    # Mostrar la más reciente
                    latest = last_syncs[0]
                    if 'state' in latest:
                        state = latest['state']
                        sync_time = state.get('last_sync_timestamp', 0)
                        if sync_time:
                            sync_dt = datetime.fromtimestamp(sync_time)
                            time_diff = datetime.now() - sync_dt
                            
                            if time_diff.seconds < 60:
                                print(f"   🔄 Última sync: hace {time_diff.seconds}s")
                            elif time_diff.seconds < 3600:
                                print(f"   🔄 Última sync: hace {time_diff.seconds // 60}m")
                            else:
                                print(f"   🔄 Última sync: hace {time_diff.seconds // 3600}h")
        
        print()  # Línea en blanco para separar
    
    def simulate_sync_event(self, source, destination, item_id, event_id, action):
        """Simula un evento de sincronización para testing."""
        self.monitor.log_sync(source, destination, item_id, event_id, action)
    
    def get_recent_activity(self, minutes=10):
        """Obtiene actividad reciente del servidor."""
        try:
            response = requests.get(f"{self.server_url}/debug/last-syncs", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"⚠️  No se pudieron obtener datos: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error obteniendo actividad: {e}")
            return None


class InteractiveMonitor:
    """Monitor interactivo con comandos."""
    
    def __init__(self, server_url="http://localhost:6754"):
        self.server_url = server_url
        self.realtime_monitor = RealtimeSyncMonitor(server_url)
    
    def start_interactive(self):
        """Inicia el monitor interactivo."""
        print("🎮 Monitor Interactivo de Sincronización")
        print("=" * 50)
        print("Comandos disponibles:")
        print("  stats    - Mostrar estadísticas actuales")
        print("  monitor  - Iniciar monitoreo en tiempo real")
        print("  activity - Mostrar actividad reciente")
        print("  clear    - Limpiar estado de un item")
        print("  test     - Ejecutar test de sincronización")
        print("  help     - Mostrar esta ayuda")
        print("  quit     - Salir")
        print()
        
        while True:
            try:
                command = input("📊 Monitor > ").strip().lower()
                
                if command == 'quit' or command == 'exit':
                    print("👋 ¡Hasta luego!")
                    break
                elif command == 'help':
                    self.show_help()
                elif command == 'stats':
                    self.show_stats()
                elif command == 'monitor':
                    self.start_realtime_monitoring()
                elif command == 'activity':
                    self.show_activity()
                elif command == 'clear':
                    self.clear_state()
                elif command == 'test':
                    self.run_test()
                else:
                    print("❌ Comando no reconocido. Usa 'help' para ver comandos disponibles.")
                    
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        """Muestra la ayuda de comandos."""
        print("\n📖 AYUDA DE COMANDOS:")
        print("  stats    - Muestra estadísticas actuales del sistema")
        print("  monitor  - Inicia monitoreo en tiempo real (Ctrl+C para detener)")
        print("  activity - Muestra las últimas 10 sincronizaciones")
        print("  clear    - Limpia el estado de sincronización de un item")
        print("  test     - Ejecuta un test completo del sistema")
        print("  help     - Muestra esta ayuda")
        print("  quit     - Sale del monitor")
        print()
    
    def show_stats(self):
        """Muestra estadísticas actuales."""
        try:
            response = requests.get(f"{self.server_url}/debug/sync-monitor", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print("\n📊 ESTADÍSTICAS DEL SISTEMA:")
                print("=" * 40)
                
                if 'statistics' in stats:
                    stats_data = stats['statistics']
                    print(f"Total de estados: {stats_data.get('total_states', 0)}")
                    print(f"Última limpieza: {stats_data.get('last_cleanup', 'N/A')}")
                    print(f"Estados antiguos eliminados: {stats_data.get('old_states_removed', 0)}")
                else:
                    print("No hay estadísticas disponibles")
            else:
                print(f"❌ Error obteniendo estadísticas: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
    
    def start_realtime_monitoring(self):
        """Inicia monitoreo en tiempo real."""
        print("\n🔄 Iniciando monitoreo en tiempo real...")
        print("Presiona Ctrl+C para detener\n")
        
        try:
            self.realtime_monitor.start_monitoring()
        except KeyboardInterrupt:
            print("\n🛑 Monitoreo detenido")
        print()
    
    def show_activity(self):
        """Muestra actividad reciente."""
        try:
            response = requests.get(f"{self.server_url}/debug/last-syncs", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("\n🕒 ACTIVIDAD RECIENTE:")
                print("=" * 40)
                
                if 'last_syncs' in data and data['last_syncs']:
                    for i, sync in enumerate(data['last_syncs'][:5], 1):
                        state = sync.get('state', {})
                        sync_time = state.get('last_sync_timestamp', 0)
                        
                        if sync_time:
                            sync_dt = datetime.fromtimestamp(sync_time)
                            time_diff = datetime.now() - sync_dt
                            
                            if time_diff.seconds < 60:
                                time_str = f"hace {time_diff.seconds}s"
                            elif time_diff.seconds < 3600:
                                time_str = f"hace {time_diff.seconds // 60}m"
                            else:
                                time_str = f"hace {time_diff.seconds // 3600}h"
                        else:
                            time_str = "N/A"
                        
                        direction = state.get('sync_direction', 'unknown')
                        print(f"{i}. Item {sync['item_id']} → {sync['event_id']} | {direction} | {time_str}")
                else:
                    print("No hay actividad reciente")
            else:
                print(f"❌ Error obteniendo actividad: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
    
    def clear_state(self):
        """Limpia el estado de un item."""
        try:
            item_id = input("Ingresa el ID del item a limpiar: ").strip()
            if not item_id:
                print("❌ ID de item requerido")
                return
            
            response = requests.delete(f"{self.server_url}/debug/clear-state/{item_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data.get('message', 'Estado limpiado')}")
                if 'cleared_states' in data:
                    print(f"   Estados limpiados: {data['cleared_states']}")
            else:
                print(f"❌ Error limpiando estado: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
    
    def run_test(self):
        """Ejecuta un test del sistema."""
        print("\n🧪 Ejecutando test del sistema...")
        try:
            # Importar y ejecutar el test
            from test_sync_system import SyncTester
            
            tester = SyncTester()
            success = tester.run_all_tests()
            
            if success:
                print("✅ Test completado exitosamente")
            else:
                print("❌ Test falló")
        except Exception as e:
            print(f"❌ Error ejecutando test: {e}")
        print()


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de Sincronización en Tiempo Real')
    parser.add_argument('--server', default='http://localhost:6754', 
                       help='URL del servidor (default: http://localhost:6754)')
    parser.add_argument('--mode', choices=['realtime', 'interactive'], default='interactive',
                       help='Modo de operación (default: interactive)')
    
    args = parser.parse_args()
    
    print("🚀 Monitor de Sincronización Monday ↔ Google Calendar")
    print(f"📡 Servidor: {args.server}")
    print(f"🎮 Modo: {args.mode}")
    print()
    
    if args.mode == 'realtime':
        # Modo tiempo real
        monitor = RealtimeSyncMonitor(args.server)
        monitor.start_monitoring()
    else:
        # Modo interactivo
        monitor = InteractiveMonitor(args.server)
        monitor.start_interactive()


if __name__ == "__main__":
    main()
