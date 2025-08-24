from flask import Flask, request, jsonify
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from sync_logic import (
    sincronizar_item_via_webhook, 
    _detectar_cambio_de_automatizacion,
    generate_content_hash
)
# Note: Google→Monday sync functions removed for unidirectional sync
from monday_api_handler import MondayAPIHandler
# Removed sync_token_manager - not needed for unidirectional sync
from sync_state_manager import get_sync_state, update_sync_state
import config

# Cargar variables de entorno
load_dotenv()

# Creamos la aplicación Flask
app = Flask(__name__)

# Inicializar servicios globales UNA SOLA VEZ
try:
    google_service_global = get_calendar_service()
    if google_service_global:
        print("✅ Servicio de Google Calendar inicializado correctamente")
    else:
        print("⚠️  Servicio de Google Calendar no disponible")
except Exception as e:
    print(f"❌ Error al inicializar Google Calendar: {e}")
    google_service_global = None

monday_handler_global = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
# Removed sync_token_manager - not needed for unidirectional sync

# Configuración del nuevo sistema anti-bucles
print("🚀 Inicializando sistema anti-bucles con sync_state_manager y detección de automatización")

@app.route('/')
def home():
    """Endpoint de prueba para verificar que el servidor está vivo."""
    return "¡Hola! El servidor de sincronización Stupendastic está funcionando."

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud para webhooks."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Stupendastic Sync Server',
        'version': '1.0.0'
    }), 200

# ============================================================================
# ENDPOINTS DE DEBUGGING
# ============================================================================

@app.route('/debug/sync-state/<item_id>', methods=['GET'])
def debug_sync_state(item_id):
    """Muestra el estado de sincronización para un item específico."""
    try:
        # Buscar todos los estados que contengan este item_id
        from sync_state_manager import get_all_sync_keys
        
        all_keys = get_all_sync_keys()
        item_states = {}
        
        for key in all_keys:
            if key.startswith(f"{item_id}_"):
                event_id = key.replace(f"{item_id}_", "")
                state = get_sync_state(item_id, event_id)
                if state:
                    item_states[event_id] = state
        
        if not item_states:
            return jsonify({
                'item_id': item_id,
                'message': 'No se encontró estado de sincronización para este item',
                'states': {}
            }), 200
        
        return jsonify({
            'item_id': item_id,
            'states': item_states,
            'total_states': len(item_states)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error obteniendo estado de sincronización: {str(e)}'
        }), 500

@app.route('/debug/last-syncs', methods=['GET'])
def debug_last_syncs():
    """Muestra las últimas 10 sincronizaciones."""
    try:
        from sync_state_manager import get_sync_statistics
        
        # Obtener estadísticas
        stats = get_sync_statistics()
        
        # Obtener todos los estados
        from sync_state_manager import get_all_sync_keys
        
        all_keys = get_all_sync_keys()
        all_states = []
        
        for key in all_keys:
            item_id, event_id = key.split('_', 1)
            state = get_sync_state(item_id, event_id)
            if state:
                all_states.append({
                    'key': key,
                    'item_id': item_id,
                    'event_id': event_id,
                    'state': state
                })
        
        # Ordenar por timestamp de última sincronización
        all_states.sort(
            key=lambda x: x['state'].get('last_sync_timestamp', 0),
            reverse=True
        )
        
        # Tomar los últimos 10
        last_syncs = all_states[:10]
        
        return jsonify({
            'statistics': stats,
            'last_syncs': last_syncs,
            'total_states': len(all_states)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error obteniendo últimas sincronizaciones: {str(e)}'
        }), 500

@app.route('/debug/clear-state/<item_id>', methods=['DELETE'])
def debug_clear_state(item_id):
    """Limpia el estado de sincronización para un item específico (para testing)."""
    try:
        from sync_state_manager import get_all_sync_keys, reset_sync_state
        
        # Buscar todos los estados que contengan este item_id
        all_keys = get_all_sync_keys()
        cleared_states = []
        
        for key in all_keys:
            if key.startswith(f"{item_id}_"):
                event_id = key.replace(f"{item_id}_", "")
                # Resetear estado específico
                reset_sync_state(item_id, event_id)
                cleared_states.append(event_id)
        
        if not cleared_states:
            return jsonify({
                'item_id': item_id,
                'message': 'No se encontraron estados para limpiar',
                'cleared_states': []
            }), 200
        
        return jsonify({
            'item_id': item_id,
            'message': f'Estado limpiado para {len(cleared_states)} eventos',
            'cleared_states': cleared_states
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error limpiando estado: {str(e)}'
        }), 500

@app.route('/debug/sync-monitor', methods=['GET'])
def debug_sync_monitor():
    """Endpoint para monitorear sincronizaciones en tiempo real."""
    try:
        # Crear monitor temporal para esta sesión
        from scripts.testing.test_sync_system import SyncMonitor
        
        # Por ahora, retornar información básica del sistema
        from sync_state_manager import get_sync_statistics
        
        stats = get_sync_statistics()
        
        return jsonify({
            'monitor_status': 'active',
            'statistics': stats,
            'timestamp': datetime.now().isoformat(),
            'message': 'Monitor de sincronización activo'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error en monitor de sincronización: {str(e)}'
        }), 500

@app.route('/webhook-test', methods=['GET', 'POST'])
def webhook_test():
    """Endpoint de prueba para verificar webhooks."""
    if request.method == 'GET':
        return jsonify({
            'message': 'Webhook test endpoint is working!',
            'timestamp': datetime.now().isoformat(),
            'method': 'GET'
        }), 200
    else:
        return jsonify({
            'message': 'Webhook test endpoint received POST!',
            'timestamp': datetime.now().isoformat(),
            'method': 'POST',
            'data': request.json if request.is_json else 'No JSON data'
        }), 200

@app.route('/monday-webhook', methods=['POST'])
def handle_monday_webhook():
    """
    Webhook de Monday.com - Sincronización inteligente Monday → Google.
    Usa el nuevo sistema anti-bucles con sync_state_manager y detección de automatización.
    """
    # Monday envía un 'challenge' la primera vez que configuras un webhook.
    if 'challenge' in request.json:
        challenge = request.json['challenge']
        print(f"Recibido 'challenge' de Monday: {challenge}")
        return jsonify({'challenge': challenge})

    # Si no es un challenge, es una notificación de evento real.
    event_data = request.json
    print("\n--- ¡Webhook de Monday Recibido! ---")
    print(json.dumps(event_data, indent=2))
    
    # Extraer el ID del item que ha cambiado
    # Monday.com puede enviar el webhook en diferentes formatos
    if 'pulseId' in event_data:
        # Formato directo
        item_id = event_data.get('pulseId')
    elif 'event' in event_data and 'pulseId' in event_data['event']:
        # Formato anidado
        item_id = event_data['event'].get('pulseId')
    else:
        item_id = None
    
    if not item_id:
        print("⚠️  No se pudo extraer el ID del item del webhook")
        return jsonify({'message': 'Webhook recibido sin item_id'}), 200
    
    print(f"🔄 Procesando webhook para item {item_id}")
    
    try:
        # 1. OBTENER DATOS DEL ITEM DE MONDAY
        from sync_logic import parse_monday_item
        
        # Obtener item específico de Monday usando el ID
        item_data = monday_handler_global.get_item_by_id(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_id=str(item_id),
            column_ids=[config.COL_GOOGLE_EVENT_ID, config.COL_FECHA, "personas1", "name"]
        )
        
        if not item_data:
            print(f"❌ No se pudo obtener datos del item {item_id}")
            return jsonify({'message': 'Item no encontrado'}), 200
        
        # Procesar item de Monday
        item_procesado = parse_monday_item(item_data)
        google_event_id = item_procesado.get('google_event_id')
        
        # No devolvemos aquí: si no hay Google Event ID, la lógica de sincronización lo creará
        if not google_event_id:
            print(f"⚠️  Item {item_id} no tiene Google Event ID asociado — se creará uno si corresponde")
        
        # 2. OBTENER ESTADO DE SINCRONIZACIÓN (solo si ya existe Google Event ID)
        sync_state = None
        if google_event_id:
            sync_state = get_sync_state(str(item_id), google_event_id)
        
        # 3. GENERAR HASH DEL CONTENIDO ACTUAL
        current_content = {
            'name': item_procesado.get('name', ''),
            'fecha_inicio': item_procesado.get('fecha_inicio', ''),
            'operario': item_procesado.get('operario', '')
        }
        current_hash = generate_content_hash(current_content)
        
        print(f"📊 Hash del contenido actual: {current_hash}")
        
        # 4. VERIFICAR SI ES UN ECO
        if sync_state and sync_state.get('monday_content_hash') == current_hash:
            print("🔄 Eco detectado - contenido idéntico, ignorando")
            return jsonify({'status': 'echo_ignored', 'message': 'Eco detectado'}), 200
        
        # 5. VERIFICAR SI FUE CAMBIO DE AUTOMATIZACIÓN
        if _detectar_cambio_de_automatizacion(str(item_id), monday_handler_global):
            print("🤖 Cambio de automatización detectado, ignorando")
            return jsonify({'status': 'automation_ignored', 'message': 'Cambio de automatización detectado'}), 200
        
        # 6. VERIFICAR SERVICIOS DISPONIBLES
        if not google_service_global:
            print("⚠️  Servicio de Google Calendar no disponible, omitiendo sincronización")
            return jsonify({
                'status': 'service_unavailable',
                'message': 'Servicio de Google Calendar no disponible'
            }), 200
        
        # 7. PROCEDER CON SINCRONIZACIÓN
        print(f"🚀 Iniciando sincronización Monday → Google para item {item_id}")
        
        success = sincronizar_item_via_webhook(
            item_id, 
            monday_handler=monday_handler_global,
            google_service=google_service_global,
            change_uuid=str(uuid.uuid4())
        )
        
        # 7. ACTUALIZAR ESTADO SI FUE EXITOSO
        if success:
            print(f"✅ Sincronización Monday → Google completada para item {item_id}")
            
            return jsonify({
                'status': 'success',
                'message': 'Sincronización completada',
                'item_id': item_id
            }), 200
        else:
            print(f"❌ Error en sincronización Monday → Google para item {item_id}")
            return jsonify({
                'status': 'error',
                'message': 'Error en sincronización'
            }), 200
            
    except Exception as e:
        print(f"❌ Error inesperado durante procesamiento del webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Error interno: {str(e)}'
        }), 200

# Google webhook endpoint REMOVED for unidirectional sync
# System now only supports Monday → Google synchronization

if __name__ == '__main__':
    app.run(debug=True, port=6754) 