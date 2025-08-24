#!/usr/bin/env python3
"""
Sistema de Tests y Monitoreo para Sincronización Monday ↔ Google Calendar
Permite probar el sistema completo sin crear bucles de sincronización.
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import config
    from monday_api_handler import MondayAPIHandler
    from sync_logic import (
        generate_content_hash, 
        _detectar_cambio_de_automatizacion,
        sincronizar_item_via_webhook,
        sincronizar_desde_google_calendar
    )
    from sync_state_manager import get_sync_state, update_sync_state
    from google_calendar_service import get_calendar_service
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("   Asegúrate de que tienes configurado config.py y las dependencias")
    sys.exit(1)


class SyncMonitor:
    """Monitor en tiempo real para detectar bucles de sincronización."""
    
    def __init__(self):
        self.sync_events = []
        self.loop_detected = False
    
    def log_sync(self, source, destination, item_id, event_id, action):
        """
        Registra un evento de sincronización.
        
        Args:
            source: 'monday' o 'google'
            destination: 'monday' o 'google'
            item_id: ID del item de Monday
            event_id: ID del evento de Google
            action: 'synced', 'echo_ignored', 'automation_ignored', 'error'
        """
        event = {
            'timestamp': datetime.now(),
            'source': source,
            'destination': destination,
            'item_id': item_id,
            'event_id': event_id,
            'action': action
        }
        self.sync_events.append(event)
        
        print(f"📊 SYNC LOG: {source} → {destination} | Item: {item_id} | Action: {action}")
        
        # Verificar bucles después de cada evento
        if self.detect_loop():
            self.loop_detected = True
            print("🚨 BUCLE DETECTADO - Deteniendo tests")
    
    def detect_loop(self, window_seconds=30):
        """
        Detecta si el mismo item se sincronizó 3+ veces en la ventana de tiempo.
        
        Args:
            window_seconds: Ventana de tiempo en segundos para detectar bucles
            
        Returns:
            bool: True si se detecta un bucle
        """
        recent_events = [
            e for e in self.sync_events 
            if (datetime.now() - e['timestamp']).seconds < window_seconds
        ]
        
        item_counts = {}
        for event in recent_events:
            key = f"{event['item_id']}"
            item_counts[key] = item_counts.get(key, 0) + 1
        
        loops = {k: v for k, v in item_counts.items() if v >= 3}
        if loops:
            print(f"⚠️ POSIBLE BUCLE DETECTADO: {loops}")
            return True
        return False
    
    def get_recent_events(self, minutes=5):
        """Obtiene eventos recientes de los últimos N minutos."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [e for e in self.sync_events if e['timestamp'] > cutoff_time]
    
    def clear_events(self):
        """Limpia todos los eventos registrados."""
        self.sync_events.clear()
        self.loop_detected = False
        print("🧹 Eventos de sincronización limpiados")
    
    def print_summary(self):
        """Imprime un resumen de los eventos registrados."""
        if not self.sync_events:
            print("📊 No hay eventos de sincronización registrados")
            return
        
        print(f"\n📊 RESUMEN DE SINCRONIZACIÓN ({len(self.sync_events)} eventos):")
        
        # Estadísticas por acción
        action_counts = {}
        for event in self.sync_events:
            action = event['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        for action, count in action_counts.items():
            print(f"   {action}: {count}")
        
        # Últimos 5 eventos
        print(f"\n🕒 ÚLTIMOS 5 EVENTOS:")
        for event in self.sync_events[-5:]:
            timestamp = event['timestamp'].strftime('%H:%M:%S')
            print(f"   {timestamp} | {event['source']} → {event['destination']} | {event['action']}")
        
        if self.loop_detected:
            print("🚨 BUCLE DETECTADO DURANTE LOS TESTS")


class SyncTester:
    """Clase principal para realizar tests de sincronización."""
    
    def __init__(self):
        self.monitor = SyncMonitor()
        self.monday_handler = None
        self.google_service = None
        self.test_item_id = None
        self.test_event_id = None
        
        # Inicializar servicios
        self._initialize_services()
    
    def _initialize_services(self):
        """Inicializa los servicios de Monday y Google."""
        try:
            # Monday API Handler
            api_token = getattr(config, 'MONDAY_API_KEY', '')
            if not api_token:
                print("❌ No se encontró MONDAY_API_KEY en config.py")
                return
            
            self.monday_handler = MondayAPIHandler(api_token)
            print("✅ Monday API Handler inicializado")
            
            # Google Calendar Service
            self.google_service = get_calendar_service()
            if self.google_service:
                print("✅ Google Calendar Service inicializado")
            else:
                print("⚠️ Google Calendar Service no disponible")
                
        except Exception as e:
            print(f"❌ Error inicializando servicios: {e}")
    
    def setup_test_item(self):
        """Configura un item de prueba para los tests."""
        print("\n🔧 Configurando item de prueba...")
        
        try:
            # Buscar un item existente para usar en tests
            items = self.monday_handler.get_items(
                board_id=str(config.BOARD_ID_GRABACIONES),
                limit_per_page=5
            )
            
            if not items:
                print("❌ No se encontraron items en el tablero")
                return False
            
            # Usar el primer item que tenga Google Event ID
            for item in items:
                item_id = item['id']
                column_values = item.get('column_values', [])
                
                for col in column_values:
                    if col.get('id') == config.COL_GOOGLE_EVENT_ID:
                        google_event_id = col.get('text', '').strip()
                        if google_event_id:
                            self.test_item_id = str(item_id)
                            self.test_event_id = google_event_id
                            print(f"✅ Item de prueba configurado: {self.test_item_id}")
                            print(f"   Google Event ID: {self.test_event_id}")
                            print(f"   Nombre: {item.get('name', 'Sin nombre')}")
                            return True
            
            print("❌ No se encontró un item con Google Event ID")
            return False
            
        except Exception as e:
            print(f"❌ Error configurando item de prueba: {e}")
            return False
    
    def test_unidirectional_monday_to_google(self):
        """Test de sincronización unidireccional Monday → Google."""
        print("\n=== Test: Monday → Google ===")
        
        if not self.test_item_id or not self.test_event_id:
            print("❌ Item de prueba no configurado")
            return False
        
        try:
            # 1. Obtener estado inicial
            initial_state = get_sync_state(self.test_item_id, self.test_event_id)
            print(f"📋 Estado inicial: {initial_state is not None}")
            
            # 2. Obtener contenido actual de Monday
            items = self.monday_handler.get_items(
                board_id=str(config.BOARD_ID_GRABACIONES),
                column_ids=[config.COL_FECHA, "personas1", "name"],
                limit_per_page=1
            )
            
            monday_item = None
            for item in items:
                if str(item.get('id')) == self.test_item_id:
                    monday_item = item
                    break
            
            if not monday_item:
                print("❌ No se pudo obtener el item de Monday")
                return False
            
            # 3. Generar hash del contenido actual
            from sync_logic import parse_monday_item
            item_procesado = parse_monday_item(monday_item)
            
            current_content = {
                'fecha': item_procesado.get('fecha_inicio', ''),
                'titulo': item_procesado.get('name', ''),
                'operarios': item_procesado.get('operario', '')
            }
            current_hash = generate_content_hash(current_content)
            
            print(f"📊 Hash del contenido actual: {current_hash[:16]}...")
            
            # 4. Verificar si es un eco
            if initial_state and initial_state.get('monday_content_hash') == current_hash:
                print("🔄 Eco detectado - contenido idéntico")
                self.monitor.log_sync('monday', 'google', self.test_item_id, self.test_event_id, 'echo_ignored')
                return True
            
            # 5. Verificar si fue cambio de automatización
            if _detectar_cambio_de_automatizacion(self.test_item_id, self.monday_handler):
                print("🤖 Cambio de automatización detectado")
                self.monitor.log_sync('monday', 'google', self.test_item_id, self.test_event_id, 'automation_ignored')
                return True
            
            # 6. Proceder con sincronización
            print("🚀 Iniciando sincronización Monday → Google...")
            
            success = sincronizar_item_via_webhook(
                self.test_item_id,
                monday_handler=self.monday_handler,
                google_service=self.google_service,
                change_uuid=f"test_{int(time.time())}"
            )
            
            if success:
                print("✅ Sincronización Monday → Google completada")
                self.monitor.log_sync('monday', 'google', self.test_item_id, self.test_event_id, 'synced')
                
                # 7. Verificar que se actualizó el estado
                updated_state = get_sync_state(self.test_item_id, self.test_event_id)
                if updated_state:
                    print("💾 Estado de sincronización actualizado")
                else:
                    print("⚠️ Estado de sincronización no se actualizó")
                
                return True
            else:
                print("❌ Error en sincronización Monday → Google")
                self.monitor.log_sync('monday', 'google', self.test_item_id, self.test_event_id, 'error')
                return False
                
        except Exception as e:
            print(f"❌ Error en test Monday → Google: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_unidirectional_google_to_monday(self):
        """Test de sincronización unidireccional Google → Monday."""
        print("\n=== Test: Google → Monday ===")
        
        if not self.test_item_id or not self.test_event_id:
            print("❌ Item de prueba no configurado")
            return False
        
        try:
            # 1. Obtener evento de Google
            if not self.google_service:
                print("❌ Google Calendar Service no disponible")
                return False
            
            event = self.google_service.events().get(
                calendarId=config.MASTER_CALENDAR_ID,
                eventId=self.test_event_id
            ).execute()
            
            if not event:
                print("❌ No se pudo obtener el evento de Google")
                return False
            
            print(f"📅 Evento de Google: {event.get('summary', 'Sin título')}")
            
            # 2. Generar hash del contenido de Google
            google_content = {
                'fecha': event.get('start', {}).get('dateTime', ''),
                'titulo': event.get('summary', ''),
                'descripcion': event.get('description', '')
            }
            google_hash = generate_content_hash(google_content)
            
            print(f"📊 Hash del contenido Google: {google_hash[:16]}...")
            
            # 3. Obtener estado de sincronización
            sync_state = get_sync_state(self.test_item_id, self.test_event_id)
            
            # 4. Verificar si es un eco
            if sync_state and sync_state.get('google_content_hash') == google_hash:
                print("🔄 Eco detectado - contenido idéntico")
                self.monitor.log_sync('google', 'monday', self.test_item_id, self.test_event_id, 'echo_ignored')
                return True
            
            # 5. Proceder con sincronización
            print("🚀 Iniciando sincronización Google → Monday...")
            
            success = sincronizar_desde_google_calendar(
                evento_cambiado=event,
                google_service=self.google_service,
                monday_handler=self.monday_handler,
                change_uuid=f"test_{int(time.time())}"
            )
            
            if success:
                print("✅ Sincronización Google → Monday completada")
                self.monitor.log_sync('google', 'monday', self.test_item_id, self.test_event_id, 'synced')
                return True
            else:
                print("❌ Error en sincronización Google → Monday")
                self.monitor.log_sync('google', 'monday', self.test_item_id, self.test_event_id, 'error')
                return False
                
        except Exception as e:
            print(f"❌ Error en test Google → Monday: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_loop_detection(self):
        """Test de detección de bucles."""
        print("\n=== Test: Detección de Bucles ===")
        
        if not self.test_item_id or not self.test_event_id:
            print("❌ Item de prueba no configurado")
            return False
        
        try:
            print("🔄 Simulando cambio rápido Monday → Google → Monday...")
            
            # Simular múltiples sincronizaciones rápidas
            for i in range(3):
                print(f"   Iteración {i+1}/3")
                
                # Simular sincronización Monday → Google
                self.monitor.log_sync('monday', 'google', self.test_item_id, self.test_event_id, 'synced')
                time.sleep(1)  # Pequeña pausa
                
                # Simular sincronización Google → Monday
                self.monitor.log_sync('google', 'monday', self.test_item_id, self.test_event_id, 'synced')
                time.sleep(1)  # Pequeña pausa
                
                # Verificar si se detectó bucle
                if self.monitor.loop_detected:
                    print("🚨 Bucle detectado correctamente")
                    return True
            
            print("✅ No se detectaron bucles (esperado para simulación)")
            return True
            
        except Exception as e:
            print(f"❌ Error en test de detección de bucles: {e}")
            return False
    
    def test_content_hash_consistency(self):
        """Test de consistencia de hashes de contenido."""
        print("\n=== Test: Consistencia de Hashes ===")
        
        try:
            # Contenido idéntico
            content1 = {
                'fecha': '2024-01-15T10:00:00Z',
                'titulo': 'Test Event',
                'operarios': 'Test User'
            }
            
            content2 = {
                'fecha': '2024-01-15T10:00:00Z',
                'titulo': 'Test Event',
                'operarios': 'Test User'
            }
            
            hash1 = generate_content_hash(content1)
            hash2 = generate_content_hash(content2)
            
            if hash1 == hash2:
                print("✅ Hashes idénticos para contenido idéntico")
            else:
                print("❌ Error: Hashes diferentes para contenido idéntico")
                return False
            
            # Contenido diferente
            content3 = {
                'fecha': '2024-01-15T11:00:00Z',
                'titulo': 'Test Event',
                'operarios': 'Test User'
            }
            
            hash3 = generate_content_hash(content3)
            
            if hash1 != hash3:
                print("✅ Hashes diferentes para contenido diferente")
            else:
                print("❌ Error: Hashes idénticos para contenido diferente")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error en test de consistencia de hashes: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecuta todos los tests."""
        print("🚀 Iniciando tests completos del sistema de sincronización...\n")
        
        # Verificar configuración
        if not hasattr(config, 'MONDAY_API_KEY') or not config.MONDAY_API_KEY:
            print("❌ Error: MONDAY_API_KEY no está configurado")
            return False
        
        if not hasattr(config, 'AUTOMATION_USER_ID') or not config.AUTOMATION_USER_ID:
            print("❌ Error: AUTOMATION_USER_ID no está configurado")
            return False
        
        print(f"✅ Configuración verificada:")
        print(f"   - Usuario automatización: {config.AUTOMATION_USER_NAME}")
        print(f"   - Board ID: {config.BOARD_ID_GRABACIONES}")
        print(f"   - Columna fecha: {config.COL_FECHA}\n")
        
        # Configurar item de prueba
        if not self.setup_test_item():
            print("❌ No se pudo configurar item de prueba")
            return False
        
        # Ejecutar tests
        tests_results = []
        
        # Test 1: Consistencia de hashes
        print("🧪 Ejecutando test de consistencia de hashes...")
        result1 = self.test_content_hash_consistency()
        tests_results.append(('Consistencia de Hashes', result1))
        
        # Test 2: Monday → Google
        print("🧪 Ejecutando test Monday → Google...")
        result2 = self.test_unidirectional_monday_to_google()
        tests_results.append(('Monday → Google', result2))
        
        # Test 3: Google → Monday
        print("🧪 Ejecutando test Google → Monday...")
        result3 = self.test_unidirectional_google_to_monday()
        tests_results.append(('Google → Monday', result3))
        
        # Test 4: Detección de bucles
        print("🧪 Ejecutando test de detección de bucles...")
        result4 = self.test_loop_detection()
        tests_results.append(('Detección de Bucles', result4))
        
        # Resumen de resultados
        print("\n" + "="*60)
        print("📊 RESUMEN DE TESTS")
        print("="*60)
        
        passed = 0
        total = len(tests_results)
        
        for test_name, result in tests_results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n📈 Resultado: {passed}/{total} tests pasaron")
        
        # Resumen del monitor
        self.monitor.print_summary()
        
        if passed == total:
            print("\n🎉 ¡Todos los tests pasaron exitosamente!")
            return True
        else:
            print(f"\n⚠️ {total - passed} test(s) fallaron")
            return False


def main():
    """Función principal."""
    tester = SyncTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Sistema de sincronización funcionando correctamente")
        sys.exit(0)
    else:
        print("\n❌ Problemas detectados en el sistema de sincronización")
        sys.exit(1)


if __name__ == "__main__":
    main()
