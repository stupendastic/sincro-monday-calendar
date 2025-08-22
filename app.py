from flask import Flask, request, jsonify
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service, get_incremental_sync_events, compare_event_values
from sync_logic import sincronizar_item_via_webhook, _obtener_item_id_por_google_event_id, update_monday_date_column_v2
from monday_api_handler import MondayAPIHandler
from sync_token_manager import SyncTokenManager
import config

# Cargar variables de entorno
load_dotenv()

# Creamos la aplicación Flask
app = Flask(__name__)

# Inicializar servicios globales UNA SOLA VEZ
google_service_global = get_calendar_service()
monday_handler_global = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
sync_token_manager = SyncTokenManager()

# Configuración de sincronización inteligente con detección de automatización
SYNC_COOLDOWN = config.SYNC_COOLDOWN_SECONDS  # Cooldown desde config
AUTOMATION_DETECTION_WINDOW = config.AUTOMATION_DETECTION_WINDOW  # Ventana de detección
CONFLICT_RESOLUTION_WINDOW = config.CONFLICT_RESOLUTION_WINDOW  # Ventana de resolución de conflictos
last_sync_times = {}  # Cache de últimos tiempos de sincronización
sync_origin = {}  # Origen de la última sincronización por item

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
    
    # Verificar cooldown y origen de sincronización
    current_time = time.time()
    
    # Generar UUID único para este cambio
    change_uuid = str(uuid.uuid4())
    
    # Verificar cooldown solo si no tenemos un UUID único
    # El sistema de UUIDs maneja la detección de duplicados de forma más precisa
    if item_id in last_sync_times:
        time_since_last = current_time - last_sync_times[item_id]
        if time_since_last < SYNC_COOLDOWN:
            print(f"⚠️  Item {item_id} sincronizado recientemente ({time_since_last:.1f}s). Saltando...")
            return jsonify({'message': 'Sincronización en cooldown'}), 200
    
    # ACTUALIZAR last_sync_times INMEDIATAMENTE para prevenir bucles
    last_sync_times[item_id] = current_time
    
    # Verificar si el último cambio fue desde Google
    if sync_origin.get(item_id) == 'google':
        print(f"🔄 Último cambio fue desde Google. Sincronizando Monday → Google para item {item_id}")
    else:
        print(f"🔄 Sincronizando Monday → Google para item {item_id}")
    
    # Generar UUID único para este cambio
    change_uuid = str(uuid.uuid4())
    
    try:
        success = sincronizar_item_via_webhook(
            item_id, 
            monday_handler=monday_handler_global,
            google_service=google_service_global,
            change_uuid=change_uuid
        )
        
        if success:
            print(f"✅ Sincronización Monday → Google completada para item {item_id}")
            sync_origin[item_id] = 'monday'
        else:
            print(f"❌ Error en sincronización Monday → Google para item {item_id}")
            
    except Exception as e:
        print(f"❌ Error inesperado durante sincronización: {e}")
    
    return jsonify({'message': 'Webhook recibido con éxito'}), 200

@app.route('/google-webhook', methods=['POST'])
def handle_google_webhook():
    """
    Webhook de Google Calendar - Sincronización inteligente Google → Monday.
    """
    print("\n--- ¡Notificación Push de Google Calendar Recibida! ---")
    
    # Extraer información del evento cambiado
    try:
        # 1. Cargar el mapeo de canales
        channel_map_file = "config/channels/config/channels/google_channel_map.json"
        if not os.path.exists(channel_map_file):
            print("❌ Error: Archivo config/channels/google_channel_map.json no encontrado")
            return '', 200
        
        with open(channel_map_file, 'r', encoding='utf-8') as f:
            channel_map = json.load(f)
        
        # 2. Obtener el channel_id
        channel_id = request.headers.get('X-Goog-Channel-Id')
        if not channel_id:
            print("❌ No se pudo obtener el channel_id")
            return '', 200
        
        # 3. Buscar el calendar_id_real en el mapeo
        calendar_id_real = channel_map.get(channel_id)
        if not calendar_id_real:
            print(f"❌ Channel ID '{channel_id}' no encontrado en el mapeo")
            return '', 200
        
        print(f"📅 Calendar ID: {calendar_id_real}")
        
        # 4. Determinar si es el calendario maestro o un calendario personal
        is_master_calendar = calendar_id_real == config.MASTER_CALENDAR_ID
        is_personal_calendar = calendar_id_real in [profile.get('calendar_id') for profile in config.FILMMAKER_PROFILES if profile.get('calendar_id')]
        
        if is_master_calendar:
            print(f"🎯 Calendario MAESTRO detectado")
        elif is_personal_calendar:
            print(f"👤 Calendario PERSONAL detectado")
        else:
            print(f"⚠️  Calendario desconocido: {calendar_id_real}")
            return '', 200
        
        # 4. Obtener eventos actualizados usando sincronización incremental
        if google_service_global:
            try:
                # Obtener sync token actual para este calendario
                current_sync_token = sync_token_manager.get_sync_token(calendar_id_real)
                
                # Obtener eventos usando sincronización incremental
                eventos_cambiados, next_sync_token = get_incremental_sync_events(
                    google_service_global, 
                    calendar_id_real, 
                    current_sync_token
                )
                
                if not eventos_cambiados:
                    print("ℹ️  No se encontraron eventos actualizados recientemente")
                    return '', 200
                
                # Guardar el nuevo sync token
                if next_sync_token:
                    sync_token_manager.set_sync_token(calendar_id_real, next_sync_token)
                
                print(f"🔄 Procesando {len(eventos_cambiados)} eventos actualizados...")
                
                # 5. Procesar cada evento cambiado
                for evento_cambiado in eventos_cambiados:
                    event_id = evento_cambiado.get('id')
                    event_summary = evento_cambiado.get('summary', 'Sin título')
                    
                    print(f"📋 Procesando evento: '{event_summary}' (ID: {event_id})")
                    
                    # Verificar cooldown
                    current_time = time.time()
                    if event_id in last_sync_times:
                        time_since_last = current_time - last_sync_times[event_id]
                        if time_since_last < SYNC_COOLDOWN:
                            print(f"  ⚠️  Evento {event_id} procesado recientemente. Saltando...")
                            continue
                    
                    # ACTUALIZAR last_sync_times INMEDIATAMENTE para prevenir bucles
                    last_sync_times[event_id] = current_time
                    
                    # 6. Usar la función de sincronización apropiada según el tipo de calendario
                    try:
                        if is_master_calendar:
                            print(f"  🔄 Sincronizando desde calendario MAESTRO...")
                            
                            # Usar la función especializada para sincronización desde Google
                            from sync_logic import sincronizar_desde_google_calendar
                            
                            # Generar UUID único para este cambio
                            change_uuid = str(uuid.uuid4())
                            
                            success = sincronizar_desde_google_calendar(
                                evento_cambiado=evento_cambiado,
                                google_service=google_service_global,
                                monday_handler=monday_handler_global,
                                change_uuid=change_uuid
                            )
                            
                            if success:
                                print(f"  ✅ Sincronización desde calendario maestro completada")
                            else:
                                print(f"  ❌ Error en sincronización desde calendario maestro")
                                
                        elif is_personal_calendar:
                            print(f"  🔄 Sincronizando desde calendario PERSONAL...")
                            
                            # Usar la función especializada para sincronización desde calendario personal
                            from sync_logic import sincronizar_desde_calendario_personal
                            
                            success = sincronizar_desde_calendario_personal(
                                evento_cambiado=evento_cambiado,
                                calendar_id=calendar_id_real,
                                google_service=google_service_global,
                                monday_handler=monday_handler_global
                            )
                            
                            if success:
                                print(f"  ✅ Sincronización desde calendario personal completada")
                            else:
                                print(f"  ❌ Error en sincronización desde calendario personal")
                        else:
                            print(f"  ⚠️  Tipo de calendario no reconocido")
                            success = False
                            
                    except Exception as e:
                        print(f"  ❌ Error procesando sincronización: {e}")
                
                print(f"✅ Procesamiento completado para {len(eventos_cambiados)} eventos")
                    
            except Exception as e:
                print(f"❌ Error al procesar eventos actualizados: {e}")
        else:
            print("❌ Servicio de Google Calendar no disponible")
            
    except Exception as e:
        print(f"❌ Error procesando webhook de Google: {e}")
    
    return '', 200

if __name__ == '__main__':
    app.run(debug=True, port=6754) 