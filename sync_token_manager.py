#!/usr/bin/env python3
"""
Sync Token Manager para Google Calendar
Gestiona los sync tokens para sincronización incremental eficiente.
"""

import json
import os
from datetime import datetime

class SyncTokenManager:
    """Gestiona sync tokens para múltiples calendarios"""
    
    def __init__(self, file_path="config/config/sync_tokens.json"):
        self.file_path = file_path
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        """Carga tokens desde archivo"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error cargando sync tokens: {e}")
        return {}
    
    def _save_tokens(self):
        """Guarda tokens en archivo"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.tokens, f, indent=2)
        except Exception as e:
            print(f"❌ Error guardando sync tokens: {e}")
    
    def get_sync_token(self, calendar_id):
        """Obtiene el sync token para un calendario"""
        return self.tokens.get(calendar_id)
    
    def set_sync_token(self, calendar_id, sync_token):
        """Establece el sync token para un calendario"""
        self.tokens[calendar_id] = sync_token
        self._save_tokens()
        print(f"💾 Sync token guardado para {calendar_id}: {sync_token[:20] if sync_token else 'None'}")
    
    def clear_sync_token(self, calendar_id):
        """Limpia el sync token para un calendario (fuerza sincronización completa)"""
        if calendar_id in self.tokens:
            del self.tokens[calendar_id]
            self._save_tokens()
            print(f"🗑️  Sync token limpiado para {calendar_id}")
    
    def get_all_calendars(self):
        """Obtiene lista de todos los calendarios con sync tokens"""
        return list(self.tokens.keys())
    
    def print_status(self):
        """Muestra el estado de todos los sync tokens"""
        print(f"\n📊 Estado de Sync Tokens:")
        for calendar_id, token in self.tokens.items():
            status = "✅ Activo" if token else "❌ Sin token"
            print(f"  📅 {calendar_id}: {status}")
            if token:
                print(f"     Token: {token[:30]}...") 