#!/usr/bin/env python3
"""
Prueba simple del sistema de detección de cambios.
"""

import sys
import time
from pathlib import Path

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from sync_logic import generate_content_hash, detect_real_change
from sync_state_manager import SyncStateManager, get_sync_state, update_sync_state


def test_simple_detection():
    """Prueba simple de detección de cambios."""
    print("=== Prueba Simple de Detección ===")
    
    # Eliminar archivo si existe
    test_file = Path("config/test_simple_sync_state.json")
    if test_file.exists():
        test_file.unlink()
    
    # Crear instancia del gestor de estado
    manager = SyncStateManager("config/test_simple_sync_state.json")
    
    item_id = "simple_item_123"
    event_id = "simple_event_456"
    content_hash = "test_hash_123"
    
    # 1. Primera vez (debe ser cambio real)
    print("\n1. Primera detección (sin estado previo)")
    is_real = detect_real_change(item_id, event_id, content_hash, "monday")
    print(f"   Resultado: {'Real' if is_real else 'Eco'}")
    print(f"   Esperado: Real")
    assert is_real, "Primera detección debe ser cambio real"
    
    # Actualizar estado después de la primera detección
    update_sync_state(
        item_id, event_id,
        monday_content_hash=content_hash,
        sync_direction="monday_to_google",
        monday_update_time=time.time()
    )
    
    # 2. Segunda vez con mismo hash (debe ser eco)
    print("\n2. Segunda detección (mismo hash)")
    is_real = detect_real_change(item_id, event_id, content_hash, "monday")
    print(f"   Resultado: {'Real' if is_real else 'Eco'}")
    print(f"   Esperado: Eco")
    assert not is_real, "Segunda detección con mismo hash debe ser eco"
    
    # 3. Tercera vez con hash diferente (debe ser cambio real)
    print("\n3. Tercera detección (hash diferente)")
    new_hash = "test_hash_456"
    is_real = detect_real_change(item_id, event_id, new_hash, "monday")
    print(f"   Resultado: {'Real' if is_real else 'Eco'}")
    print(f"   Esperado: Real")
    assert is_real, "Detección con hash diferente debe ser cambio real"
    
    print("\n✅ Prueba simple completada exitosamente!")


if __name__ == "__main__":
    try:
        test_simple_detection()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
