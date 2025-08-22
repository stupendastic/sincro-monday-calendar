import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Variables globales para servicios
google_service_global = None
monday_handler_global = None

# Sistema de cooldown SIMPLE
last_sync_times = {}
COOLDOWN_SECONDS = 15  # Solo 15 segundos de cooldown

def is_in_cooldown(item_id):
    """Cooldown simple y efectivo"""
    if not item_id:
        return False
    
    current_time = time.time()
    if item_id in last_sync_times:
        if current_time - last_sync_times[item_id] < COOLDOWN_SECONDS:
            return True
    
    last_sync_times[item_id] = current_time
    return False

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'google_service': google_service_global is not None,
        'monday_handler': monday_handler_global is not None
    })

@app.route('/monday-webhook', methods=['POST'])
def handle_monday_webhook():
    """Webhook de Monday.com SIMPLIFICADO"""
    try:
        data = request.get_json()
        print(f"📧 Webhook Monday recibido")
        
        # Manejar challenge
        if 'challenge' in data:
            return jsonify({'challenge': data['challenge']}), 200
        
        # Extraer información básica
        event_data = data.get('event', {})
        item_id = event_data.get('pulseId')
        event_type = event_data.get('type')
        
        if not item_id:
            print("❌ No item_id")
            return jsonify({'status': 'error'}), 200
        
        # Verificar cooldown SIMPLE
        if is_in_cooldown(item_id):
            print(f"⏰ Item {item_id} en cooldown - IGNORANDO")
            return jsonify({'status': 'ignored', 'reason': 'cooldown'}), 200
        
        # Solo procesar eventos relevantes
        if event_type in ['create_pulse', 'update_column_value']:
            print(f"🔄 Sincronizando item {item_id}")
            
            # Importar función de sincronización ORIGINAL (sin modificaciones)
            from sync_logic import sincronizar_item_especifico
            
            # Ejecutar sincronización SIMPLE
            success = sincronizar_item_especifico(
                item_id=item_id,
                monday_handler=monday_handler_global,
                google_service=google_service_global
            )
            
            status = 'success' if success else 'error'
            print(f"✅ Sincronización: {status}")
            return jsonify({'status': status}), 200
        else:
            print(f"ℹ️ Evento {event_type} ignorado")
            return jsonify({'status': 'ignored'}), 200
            
    except Exception as e:
        print(f"❌ Error en webhook Monday: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 200

@app.route('/google-webhook', methods=['POST'])
def handle_google_webhook():
    """Webhook de Google Calendar SIMPLIFICADO"""
    try:
        print(f"📧 Webhook Google recibido")
        
        # Extraer channel ID
        channel_id = request.headers.get('X-Goog-Channel-Id')
        if not channel_id:
            print("❌ No channel_id")
            return '', 200
        
        # Cargar mapeo de canales
        try:
            with open("config/channels/config/channels/google_channel_map.json", 'r') as f:
                channel_map = json.load(f)
        except FileNotFoundError:
            print("❌ No channel map")
            return '', 200
        
        # Buscar calendar_id
        calendar_id = channel_map.get(channel_id)
        if not calendar_id:
            print(f"❌ Channel {channel_id} no encontrado")
            return '', 200
        
        print(f"📅 Procesando calendario: {calendar_id[:20]}...")
        
        # Procesar eventos SIMPLE - sin cola, sin delays
        if google_service_global:
            try:
                from sync_logic import es_calendario_personal, sincronizar_desde_google_calendar, sincronizar_desde_calendario_personal
                
                # Obtener eventos recientes (sin sync token por simplicidad)
                events_result = google_service_global.events().list(
                    calendarId=calendar_id,
                    timeMin=datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat() + 'Z',
                    maxResults=10,
                    singleEvents=True,
                    orderBy='updated'
                ).execute()
                
                events = events_result.get('items', [])
                
                for evento in events[-3:]:  # Solo los últimos 3 eventos
                    event_id = evento.get('id')
                    
                    # Verificar cooldown SIMPLE
                    if is_in_cooldown(f"google_{event_id}"):
                        continue
                    
                    print(f"🔄 Sincronizando evento: {evento.get('summary', 'Sin título')}")
                    
                    if es_calendario_personal(calendar_id):
                        sincronizar_desde_calendario_personal(
                            evento_cambiado=evento,
                            calendar_id_origen=calendar_id,
                            google_service=google_service_global,
                            monday_handler=monday_handler_global
                        )
                    else:
                        sincronizar_desde_google_calendar(
                            evento_cambiado=evento,
                            google_service=google_service_global,
                            monday_handler=monday_handler_global
                        )
                    
                    print(f"✅ Evento sincronizado")
                    
            except Exception as e:
                print(f"❌ Error procesando eventos: {e}")
        
        return '', 200
        
    except Exception as e:
        print(f"❌ Error en webhook Google: {e}")
        return '', 200

if __name__ == '__main__':
    # Inicializar servicios
    print("🚀 Iniciando servidor SIMPLE...")
    
    try:
        from google_calendar_service import get_calendar_service
        google_service_global = get_calendar_service()
        print("✅ Google Calendar OK")
    except Exception as e:
        print(f"❌ Error Google Calendar: {e}")
        google_service_global = None
    
    try:
        from monday_api_handler import MondayAPIHandler
        monday_handler_global = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        print("✅ Monday API OK")
    except Exception as e:
        print(f"❌ Error Monday API: {e}")
        monday_handler_global = None
    
    print("✅ Servidor SIMPLE listo en puerto 6754")
    app.run(debug=True, port=6754)