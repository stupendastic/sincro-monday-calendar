"""
Google Calendar Change Monitor for Unidirectional Sync System
============================================================

This module provides passive monitoring of Google Calendar changes to detect
when someone manually modifies events that are synced from Monday.com.

IMPORTANT: This is a READ-ONLY monitoring system. It DOES NOT sync changes 
back to Monday.com to maintain the unidirectional Monday → Google flow.

Features:
- Detects manual changes to Google Calendar events
- Compares events with stored hashes to identify modifications
- Logs conflicts without creating sync loops
- Optional notification system for admin alerts
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import config
from google_calendar_service import get_calendar_service
from monday_api_handler import MondayAPIHandler
from sync_state_manager import get_sync_state
from sync_logic import generate_content_hash


class GoogleChangeMonitor:
    """
    Monitors Google Calendar events for manual changes without syncing back to Monday.
    """
    
    def __init__(self, google_service=None, monday_handler=None):
        """
        Initialize the Google Change Monitor.
        
        Args:
            google_service: Google Calendar service instance
            monday_handler: Monday.com API handler instance
        """
        self.google_service = google_service or get_calendar_service()
        self.monday_handler = monday_handler or MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        self.monitored_calendars = [config.MASTER_CALENDAR_ID]
        
        # Add personal calendars to monitoring list
        for profile in config.FILMMAKER_PROFILES:
            calendar_id = profile.get('calendar_id')
            if calendar_id:
                self.monitored_calendars.append(calendar_id)
                
        print(f"📊 Inicializado monitor para {len(self.monitored_calendars)} calendarios")
    
    def detect_manual_changes(self) -> Dict[str, List[Dict]]:
        """
        Detects manual changes in Google Calendar events.
        
        Returns:
            Dict with calendar_id as key and list of changed events as value
        """
        print("\n🔍 DETECCIÓN DE CAMBIOS MANUALES EN GOOGLE CALENDAR")
        print("=" * 60)
        
        all_changes = {}
        
        for calendar_id in self.monitored_calendars:
            changes = self._check_calendar_changes(calendar_id)
            if changes:
                all_changes[calendar_id] = changes
        
        if all_changes:
            print(f"⚠️  DETECTADOS CAMBIOS MANUALES en {len(all_changes)} calendarios")
            self._log_changes(all_changes)
        else:
            print("✅ No se detectaron cambios manuales")
        
        return all_changes
    
    def _check_calendar_changes(self, calendar_id: str) -> List[Dict]:
        """
        Check for changes in a specific calendar.
        
        Args:
            calendar_id: ID of the calendar to check
            
        Returns:
            List of detected changes
        """
        print(f"📅 Verificando calendario: {calendar_id[:20]}...")
        
        if not self.google_service:
            print("❌ Servicio de Google Calendar no disponible")
            return []
        
        changes = []
        
        try:
            # Get recent events from Google Calendar
            time_min = datetime.utcnow() - timedelta(hours=24)  # Last 24 hours
            time_min_iso = time_min.isoformat() + 'Z'
            
            response = self.google_service.events().list(
                calendarId=calendar_id,
                timeMin=time_min_iso,
                maxResults=100,
                singleEvents=True,
                orderBy='updated'
            ).execute()
            
            events = response.get('items', [])
            print(f"  📋 Encontrados {len(events)} eventos recientes")
            
            for event in events:
                change = self._analyze_event_change(event, calendar_id)
                if change:
                    changes.append(change)
            
        except Exception as e:
            print(f"❌ Error verificando calendario {calendar_id}: {e}")
        
        return changes
    
    def _analyze_event_change(self, event: Dict, calendar_id: str) -> Optional[Dict]:
        """
        Analyze if an event has been manually changed.
        
        Args:
            event: Google Calendar event
            calendar_id: ID of the calendar
            
        Returns:
            Change information if detected, None otherwise
        """
        event_id = event.get('id')
        event_summary = event.get('summary', 'Sin título')
        
        # Check if this is a synced event from Monday
        if not self._is_synced_event(event):
            return None
        
        # Get Monday item ID
        item_id = self._get_monday_item_id_for_event(event)
        if not item_id:
            return None
        
        # Get current sync state
        sync_state = get_sync_state(str(item_id), event_id)
        if not sync_state:
            return None
        
        # Generate current hash
        google_content = {
            'fecha': event.get('start', {}).get('dateTime', ''),
            'titulo': event.get('summary', ''),
            'descripcion': event.get('description', ''),
            'location': event.get('location', '')
        }
        current_hash = generate_content_hash(google_content)
        
        # Compare with stored hash
        stored_hash = sync_state.get('google_content_hash')
        
        if stored_hash and stored_hash != current_hash:
            return {
                'event_id': event_id,
                'event_summary': event_summary,
                'calendar_id': calendar_id,
                'item_id': item_id,
                'stored_hash': stored_hash[:16],
                'current_hash': current_hash[:16],
                'updated': event.get('updated'),
                'change_detected_at': datetime.now().isoformat()
            }
        
        return None
    
    def _is_synced_event(self, event: Dict) -> bool:
        """
        Check if an event is synced from Monday.com.
        
        Args:
            event: Google Calendar event
            
        Returns:
            True if event is synced from Monday
        """
        # Check for extended properties that indicate sync
        extended_props = event.get('extendedProperties', {})
        private_props = extended_props.get('private', {})
        
        # Events synced from Monday should have these properties
        return (
            'monday_item_id' in private_props or
            'master_event_id' in private_props or
            'board_id' in private_props
        )
    
    def _get_monday_item_id_for_event(self, event: Dict) -> Optional[str]:
        """
        Get the Monday.com item ID for a Google Calendar event.
        
        Args:
            event: Google Calendar event
            
        Returns:
            Monday item ID if found
        """
        extended_props = event.get('extendedProperties', {})
        private_props = extended_props.get('private', {})
        
        # Try direct Monday item ID
        item_id = private_props.get('monday_item_id')
        if item_id:
            return item_id
        
        # Try via master event ID
        master_event_id = private_props.get('master_event_id')
        if master_event_id and self.monday_handler:
            try:
                from sync_logic import _obtener_item_id_por_google_event_id
                return _obtener_item_id_por_google_event_id(master_event_id, self.monday_handler)
            except:
                pass
        
        return None
    
    def _log_changes(self, changes: Dict[str, List[Dict]]) -> None:
        """
        Log detected changes to file and console.
        
        Args:
            changes: Dictionary of changes by calendar ID
        """
        print("\n⚠️  RESUMEN DE CAMBIOS MANUALES DETECTADOS:")
        print("-" * 50)
        
        total_changes = 0
        log_entries = []
        
        for calendar_id, calendar_changes in changes.items():
            calendar_name = self._get_calendar_display_name(calendar_id)
            print(f"\n📅 {calendar_name} ({len(calendar_changes)} cambios):")
            
            for change in calendar_changes:
                total_changes += 1
                event_summary = change['event_summary']
                item_id = change['item_id']
                
                print(f"  🔧 '{event_summary}' (Item: {item_id})")
                print(f"     Hash almacenado: {change['stored_hash']}...")
                print(f"     Hash actual:     {change['current_hash']}...")
                print(f"     Actualizado:     {change['updated']}")
                
                log_entries.append(change)
        
        print(f"\n📊 TOTAL: {total_changes} cambios manuales detectados")
        
        # Save to log file
        self._save_change_log(log_entries)
        
        print("\n💡 NOTA: Los cambios manuales NO se sincronizan de vuelta a Monday.com")
        print("   Monday.com es la fuente única de verdad en el sistema unidireccional")
    
    def _get_calendar_display_name(self, calendar_id: str) -> str:
        """
        Get a display name for the calendar.
        
        Args:
            calendar_id: Calendar ID
            
        Returns:
            Human-readable calendar name
        """
        if calendar_id == config.MASTER_CALENDAR_ID:
            return "Calendario Maestro"
        
        # Check if it's a personal calendar
        for profile in config.FILMMAKER_PROFILES:
            if profile.get('calendar_id') == calendar_id:
                return f"Calendario Personal - {profile.get('monday_name', 'Desconocido')}"
        
        return f"Calendario {calendar_id[:20]}..."
    
    def _save_change_log(self, changes: List[Dict]) -> None:
        """
        Save changes to a log file.
        
        Args:
            changes: List of detected changes
        """
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_file = os.path.join(log_dir, "google_manual_changes.json")
            
            # Load existing log
            existing_log = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        existing_log = json.load(f)
                except:
                    existing_log = []
            
            # Add new changes
            existing_log.extend(changes)
            
            # Keep only last 1000 entries
            existing_log = existing_log[-1000:]
            
            # Save updated log
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_log, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Cambios guardados en: {log_file}")
            
        except Exception as e:
            print(f"⚠️  Error guardando log de cambios: {e}")
    
    def generate_conflict_report(self) -> str:
        """
        Generate a detailed conflict report.
        
        Returns:
            HTML report string
        """
        changes = self.detect_manual_changes()
        
        if not changes:
            return "<p>✅ No se detectaron cambios manuales en Google Calendar.</p>"
        
        html = """
        <h2>⚠️ Cambios Manuales Detectados en Google Calendar</h2>
        <p><strong>IMPORTANTE:</strong> El sistema es unidireccional Monday → Google. 
        Los cambios manuales en Google Calendar NO se sincronizan de vuelta a Monday.com.</p>
        """
        
        for calendar_id, calendar_changes in changes.items():
            calendar_name = self._get_calendar_display_name(calendar_id)
            html += f"<h3>📅 {calendar_name}</h3><ul>"
            
            for change in calendar_changes:
                html += f"""
                <li>
                    <strong>{change['event_summary']}</strong> (Item Monday: {change['item_id']})
                    <br>Último cambio: {change['updated']}
                    <br>Hash cambió de {change['stored_hash']} a {change['current_hash']}
                </li>
                """
            
            html += "</ul>"
        
        html += """
        <p><strong>Recomendación:</strong> Revisar estos eventos manualmente y realizar 
        los cambios necesarios en Monday.com para mantener la consistencia.</p>
        """
        
        return html


def run_monitoring_check():
    """
    Run a single monitoring check.
    Convenience function for scripts and scheduled tasks.
    """
    print("🚀 Ejecutando verificación de cambios manuales...")
    
    monitor = GoogleChangeMonitor()
    changes = monitor.detect_manual_changes()
    
    if changes:
        print(f"\n⚠️  ACCIÓN REQUERIDA: Se detectaron {sum(len(c) for c in changes.values())} cambios manuales")
        print("📋 Ver detalles en logs/google_manual_changes.json")
        return False  # Indicates manual intervention needed
    else:
        print("✅ No se requiere acción - no hay cambios manuales")
        return True


if __name__ == "__main__":
    run_monitoring_check()