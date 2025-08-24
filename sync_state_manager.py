import json
import hashlib
import time
import os
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncStateManager:
    """
    Gestor del estado de sincronización entre Monday.com y Google Calendar.
    Almacena información persistente sobre el estado de cada sincronización
    para evitar bucles infinitos y optimizar las operaciones.
    """
    
    def __init__(self, state_file_path: str = "config/sync_state.json"):
        """
        Inicializa el gestor de estado de sincronización.
        
        Args:
            state_file_path: Ruta al archivo JSON donde se almacenará el estado
        """
        self.state_file_path = Path(state_file_path)
        self.lock = threading.RLock()  # Reentrant lock para permitir llamadas anidadas
        
        # Crear directorio si no existe
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar archivo si no existe
        if not self.state_file_path.exists():
            self._save_state({})
            logger.info(f"Archivo de estado creado en: {self.state_file_path}")
    
    def _load_state(self) -> Dict[str, Any]:
        """
        Carga el estado desde el archivo JSON.
        
        Returns:
            Diccionario con el estado actual
            
        Raises:
            Exception: Si hay error al cargar el archivo
        """
        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error al cargar estado, creando nuevo: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error inesperado al cargar estado: {e}")
            raise
    
    def _save_state(self, state: Dict[str, Any]) -> None:
        """
        Guarda el estado en el archivo JSON.
        
        Args:
            state: Diccionario con el estado a guardar
            
        Raises:
            Exception: Si hay error al guardar el archivo
        """
        try:
            # Crear backup temporal
            temp_file = self.state_file_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            # Mover archivo temporal a destino (operación atómica)
            temp_file.replace(self.state_file_path)
            
        except Exception as e:
            logger.error(f"Error al guardar estado: {e}")
            raise
    
    def _get_sync_key(self, item_id: str, event_id: str) -> str:
        """
        Genera la clave única para un par de sincronización.
        
        Args:
            item_id: ID del item en Monday.com
            event_id: ID del evento en Google Calendar
            
        Returns:
            Clave única para el par de sincronización
        """
        return f"{item_id}_{event_id}"
    
    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """
        Genera un hash del contenido para detectar cambios.
        
        Args:
            content: Diccionario con el contenido a hashear
            
        Returns:
            Hash SHA-256 del contenido serializado
        """
        # Ordenar el diccionario para consistencia
        sorted_content = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(sorted_content.encode('utf-8')).hexdigest()
    
    def get_sync_state(self, item_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de sincronización para un par item_id/event_id.
        
        Args:
            item_id: ID del item en Monday.com
            event_id: ID del evento en Google Calendar
            
        Returns:
            Diccionario con el estado de sincronización o None si no existe
        """
        with self.lock:
            try:
                state = self._load_state()
                sync_key = self._get_sync_key(item_id, event_id)
                return state.get(sync_key)
            except Exception as e:
                logger.error(f"Error al obtener estado de sincronización: {e}")
                return None
    
    def update_sync_state(
        self,
        item_id: str,
        event_id: str,
        monday_content_hash: Optional[str] = None,
        google_content_hash: Optional[str] = None,
        sync_direction: Optional[str] = None,
        monday_update_time: Optional[float] = None,
        google_update_time: Optional[float] = None
    ) -> bool:
        """
        Actualiza el estado de sincronización después de una operación exitosa.
        
        Args:
            item_id: ID del item en Monday.com
            event_id: ID del evento en Google Calendar
            monday_content_hash: Hash del contenido actual en Monday
            google_content_hash: Hash del contenido actual en Google
            sync_direction: Dirección de la sincronización ("monday_to_google" o "google_to_monday")
            monday_update_time: Timestamp de última actualización en Monday
            google_update_time: Timestamp de última actualización en Google
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        with self.lock:
            try:
                state = self._load_state()
                sync_key = self._get_sync_key(item_id, event_id)
                current_time = time.time()
                
                # Obtener estado actual o crear nuevo
                sync_state = state.get(sync_key, {
                    "last_monday_update": 0,
                    "last_google_update": 0,
                    "monday_content_hash": "",
                    "google_content_hash": "",
                    "sync_version": 0,
                    "last_sync_direction": "",
                    "last_sync_timestamp": 0
                })
                
                # Actualizar campos proporcionados
                if monday_content_hash is not None:
                    sync_state["monday_content_hash"] = monday_content_hash
                if google_content_hash is not None:
                    sync_state["google_content_hash"] = google_content_hash
                if sync_direction is not None:
                    sync_state["last_sync_direction"] = sync_direction
                if monday_update_time is not None:
                    sync_state["last_monday_update"] = monday_update_time
                if google_update_time is not None:
                    sync_state["last_google_update"] = google_update_time
                
                # Actualizar timestamp de sincronización y versión
                sync_state["last_sync_timestamp"] = current_time
                sync_state["sync_version"] += 1
                
                # Guardar estado actualizado
                state[sync_key] = sync_state
                self._save_state(state)
                
                logger.info(f"Estado de sincronización actualizado para {sync_key} (versión {sync_state['sync_version']})")
                return True
                
            except Exception as e:
                logger.error(f"Error al actualizar estado de sincronización: {e}")
                return False
    
    def is_change_needed(
        self,
        item_id: str,
        event_id: str,
        new_content_hash: str,
        source: str
    ) -> bool:
        """
        Determina si es necesario sincronizar basándose en el hash del contenido.
        
        Args:
            item_id: ID del item en Monday.com
            event_id: ID del evento en Google Calendar
            new_content_hash: Hash del contenido nuevo
            source: Fuente del cambio ("monday" o "google")
            
        Returns:
            True si se necesita sincronizar, False en caso contrario
        """
        with self.lock:
            try:
                sync_state = self.get_sync_state(item_id, event_id)
                if not sync_state:
                    logger.info(f"No existe estado previo para {item_id}_{event_id}, sincronización necesaria")
                    return True
                
                # Obtener hash actual según la fuente
                current_hash_key = f"{source}_content_hash"
                current_hash = sync_state.get(current_hash_key, "")
                
                # Comparar hashes
                if current_hash != new_content_hash:
                    logger.info(f"Cambio detectado en {source}: hash anterior={current_hash[:8]}..., nuevo={new_content_hash[:8]}...")
                    return True
                else:
                    logger.debug(f"No hay cambios en {source} para {item_id}_{event_id}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error al verificar si se necesita cambio: {e}")
                # En caso de error, asumir que se necesita sincronizar
                return True
    
    def cleanup_old_states(self, days_threshold: int = 30) -> int:
        """
        Limpia estados de sincronización más antiguos que el umbral especificado.
        
        Args:
            days_threshold: Número de días para considerar un estado como obsoleto
            
        Returns:
            Número de estados eliminados
        """
        with self.lock:
            try:
                state = self._load_state()
                current_time = time.time()
                threshold_time = current_time - (days_threshold * 24 * 3600)
                
                keys_to_remove = []
                for sync_key, sync_state in state.items():
                    last_sync = sync_state.get("last_sync_timestamp", 0)
                    if last_sync < threshold_time:
                        keys_to_remove.append(sync_key)
                
                # Eliminar estados obsoletos
                for key in keys_to_remove:
                    del state[key]
                
                if keys_to_remove:
                    self._save_state(state)
                    logger.info(f"Eliminados {len(keys_to_remove)} estados obsoletos (más de {days_threshold} días)")
                
                return len(keys_to_remove)
                
            except Exception as e:
                logger.error(f"Error al limpiar estados obsoletos: {e}")
                return 0
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del estado de sincronización.
        
        Returns:
            Diccionario con estadísticas del estado de sincronización
        """
        with self.lock:
            try:
                state = self._load_state()
                total_syncs = len(state)
                
                if total_syncs == 0:
                    return {
                        "total_syncs": 0,
                        "recent_syncs": 0,
                        "oldest_sync": None,
                        "newest_sync": None
                    }
                
                current_time = time.time()
                recent_syncs = 0
                timestamps = []
                
                for sync_state in state.values():
                    last_sync = sync_state.get("last_sync_timestamp", 0)
                    timestamps.append(last_sync)
                    
                    # Sincronizaciones en las últimas 24 horas
                    if current_time - last_sync < 24 * 3600:
                        recent_syncs += 1
                
                return {
                    "total_syncs": total_syncs,
                    "recent_syncs": recent_syncs,
                    "oldest_sync": datetime.fromtimestamp(min(timestamps)).isoformat() if timestamps else None,
                    "newest_sync": datetime.fromtimestamp(max(timestamps)).isoformat() if timestamps else None
                }
                
            except Exception as e:
                logger.error(f"Error al obtener estadísticas: {e}")
                return {}
    
    def reset_sync_state(self, item_id: str, event_id: str) -> bool:
        """
        Resetea el estado de sincronización para un par específico.
        
        Args:
            item_id: ID del item en Monday.com
            event_id: ID del evento en Google Calendar
            
        Returns:
            True si se reseteó correctamente, False en caso contrario
        """
        with self.lock:
            try:
                state = self._load_state()
                sync_key = self._get_sync_key(item_id, event_id)
                
                if sync_key in state:
                    del state[sync_key]
                    self._save_state(state)
                    logger.info(f"Estado de sincronización reseteado para {sync_key}")
                    return True
                else:
                    logger.warning(f"No existe estado de sincronización para {sync_key}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error al resetear estado de sincronización: {e}")
                return False
    
    def get_all_sync_keys(self) -> list:
        """
        Obtiene todas las claves de sincronización existentes.
        
        Returns:
            Lista de claves de sincronización
        """
        with self.lock:
            try:
                state = self._load_state()
                return list(state.keys())
            except Exception as e:
                logger.error(f"Error al obtener claves de sincronización: {e}")
                return []


# Instancia global del gestor de estado
sync_state_manager = SyncStateManager()


# Funciones de conveniencia para uso directo
def get_sync_state(item_id: str, event_id: str) -> Optional[Dict[str, Any]]:
    """Función de conveniencia para obtener estado de sincronización."""
    return sync_state_manager.get_sync_state(item_id, event_id)


def update_sync_state(
    item_id: str,
    event_id: str,
    monday_content_hash: Optional[str] = None,
    google_content_hash: Optional[str] = None,
    sync_direction: Optional[str] = None,
    monday_update_time: Optional[float] = None,
    google_update_time: Optional[float] = None
) -> bool:
    """Función de conveniencia para actualizar estado de sincronización."""
    return sync_state_manager.update_sync_state(
        item_id, event_id, monday_content_hash, google_content_hash,
        sync_direction, monday_update_time, google_update_time
    )


def is_change_needed(item_id: str, event_id: str, new_content_hash: str, source: str) -> bool:
    """Función de conveniencia para verificar si se necesita sincronizar."""
    return sync_state_manager.is_change_needed(item_id, event_id, new_content_hash, source)


def cleanup_old_states(days_threshold: int = 30) -> int:
    """Función de conveniencia para limpiar estados obsoletos."""
    return sync_state_manager.cleanup_old_states(days_threshold)


if __name__ == "__main__":
    # Ejemplo de uso y pruebas
    print("=== Pruebas del SyncStateManager ===")
    
    # Crear instancia
    manager = SyncStateManager()
    
    # Ejemplo de uso
    item_id = "12345"
    event_id = "google_event_67890"
    
    # Simular contenido
    monday_content = {"title": "Reunión importante", "date": "2024-01-15"}
    google_content = {"summary": "Reunión importante", "start": "2024-01-15T10:00:00Z"}
    
    # Generar hashes
    monday_hash = manager._generate_content_hash(monday_content)
    google_hash = manager._generate_content_hash(google_content)
    
    print(f"Hash Monday: {monday_hash[:16]}...")
    print(f"Hash Google: {google_hash[:16]}...")
    
    # Actualizar estado
    success = manager.update_sync_state(
        item_id, event_id,
        monday_content_hash=monday_hash,
        google_content_hash=google_hash,
        sync_direction="monday_to_google"
    )
    print(f"Estado actualizado: {success}")
    
    # Verificar si se necesita cambio
    needs_sync = manager.is_change_needed(item_id, event_id, monday_hash, "monday")
    print(f"¿Necesita sincronización? {needs_sync}")
    
    # Obtener estadísticas
    stats = manager.get_sync_statistics()
    print(f"Estadísticas: {stats}")
    
    print("=== Fin de pruebas ===")
