from flask import Flask, request, jsonify
import json
import os
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service, get_recently_updated_events
from sync_logic import sincronizar_item_via_webhook, _obtener_item_id_por_google_event_id
from monday_api_handler import MondayAPIHandler

# Cargar variables de entorno
load_dotenv()

# Creamos la aplicación Flask
app = Flask(__name__)

# Inicializar servicios globales UNA SOLA VEZ
google_service_global = get_calendar_service()
monday_handler_global = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))

@app.route('/')
def home():
    """Endpoint de prueba para verificar que el servidor está vivo."""
    return "¡Hola! El servidor de sincronización Stupendastic está funcionando."

@app.route('/monday-webhook', methods=['POST'])
def handle_monday_webhook():
    """
    Este endpoint recibirá las notificaciones de Monday.com.
    Por ahora, solo registrará el evento y devolverá una respuesta.
    """
    # Monday envía un 'challenge' la primera vez que configuras un webhook.
    # Tenemos que responderlo para que Monday sepa que nuestra URL es válida.
    if 'challenge' in request.json:
        challenge = request.json['challenge']
        print(f"Recibido 'challenge' de Monday: {challenge}")
        return jsonify({'challenge': challenge})

    # Si no es un challenge, es una notificación de evento real.
    else:
        event_data = request.json['event']
        print("\n--- ¡Webhook de Monday Recibido! ---")
        # Imprimimos los datos del evento para ver qué nos llega
        print(json.dumps(event_data, indent=2))
        print("------------------------------------")
        
        # Extraer el ID del item que ha cambiado
        item_id = event_data.get('pulseId')
        
        # Comprobación de seguridad
        if item_id:
            print(f"-> [WEBHOOK MONDAY] Recibido cambio en item ID: {item_id}. Disparando sincronización...")
            
            # Llamar a nuestra función optimizada de sincronización para webhooks
            try:
                success = sincronizar_item_via_webhook(
                    item_id, 
                    monday_handler=monday_handler_global,
                    google_service=google_service_global
                )
                if success:
                    print(f"✅ Sincronización webhook completada exitosamente para item {item_id}")
                else:
                    print(f"❌ Error en sincronización webhook para item {item_id}")
            except Exception as e:
                print(f"❌ Error inesperado durante sincronización webhook: {e}")
        else:
            print("⚠️  No se pudo extraer el ID del item del webhook")
        
        # Le decimos a Monday que hemos recibido el evento correctamente.
        return jsonify({'message': 'Webhook recibido con éxito'}), 200


@app.route('/google-webhook', methods=['POST'])
def handle_google_webhook():
    """
    Este endpoint recibirá las notificaciones push de Google Calendar.
    Implementa la nueva lógica precisa para sincronización Google -> Monday.
    """
    print("\n--- ¡Notificación Push de Google Calendar Recibida! ---")
    
    # Imprimir las cabeceras de la petición
    print("Cabeceras de la petición:")
    for header, value in request.headers.items():
        print(f"  {header}: {value}")
    
    # Imprimir el cuerpo de la petición
    print("\nCuerpo de la petición:")
    body = request.data.decode('utf-8')
    print(body)
    print("------------------------------------")
    
    # Extraer información del evento cambiado
    try:
        # 1. Cargar el mapeo de canales
        channel_map_file = "google_channel_map.json"
        if not os.path.exists(channel_map_file):
            print("❌ Error: Archivo google_channel_map.json no encontrado")
            print("   Ejecuta init_google_notifications.py para crear el mapeo de canales")
            return '', 200
        
        try:
            with open(channel_map_file, 'r', encoding='utf-8') as f:
                channel_map = json.load(f)
            print(f"✅ Mapeo de canales cargado: {len(channel_map)} canales registrados")
        except Exception as e:
            print(f"❌ Error al cargar mapeo de canales: {e}")
            return '', 200
        
        # 2. Obtener el channel_id
        channel_id = request.headers.get('X-Goog-Channel-Id')
        if not channel_id:
            print("❌ No se pudo obtener el channel_id de X-Goog-Channel-Id")
            return '', 200
        
        print(f"📡 Channel ID detectado: {channel_id}")
        
        # 3. Buscar el calendar_id_real en el mapeo
        calendar_id_real = channel_map.get(channel_id)
        if not calendar_id_real:
            print(f"❌ Error: Channel ID '{channel_id}' no encontrado en el mapeo de canales")
            print(f"   Canales disponibles: {list(channel_map.keys())}")
            return '', 200
        
        print(f"📅 Calendar ID real encontrado: {calendar_id_real}")
        
        # 4. Nueva lógica precisa: obtener eventos realmente actualizados
        if google_service_global:
            try:
                # Obtener eventos actualizados recientemente (últimos 5 minutos)
                eventos_cambiados = get_recently_updated_events(google_service_global, calendar_id_real, minutes_ago=5)
                
                if not eventos_cambiados:
                    print("ℹ️  No se encontraron eventos actualizados recientemente")
                    return '', 200
                
                print(f"🔄 Procesando {len(eventos_cambiados)} eventos actualizados...")
                
                # 5. Iterar sobre cada evento cambiado
                for evento_cambiado_real in eventos_cambiados:
                    print(f"\n📋 Procesando evento: '{evento_cambiado_real.get('summary', 'Sin título')}'")
                    
                    # 6. Extraer master_event_id de extendedProperties
                    extended_props = evento_cambiado_real.get('extendedProperties', {})
                    private_props = extended_props.get('private', {})
                    master_event_id = private_props.get('master_event_id')
                    
                    if not master_event_id:
                        print(f"  ⚠️  Evento sin master_event_id, usando su propio ID: {evento_cambiado_real.get('id')}")
                        master_event_id = evento_cambiado_real.get('id')
                    
                    print(f"  🔍 Master Event ID: {master_event_id}")
                    
                    # 7. Encontrar el item_id de Monday correspondiente
                    item_id = _obtener_item_id_por_google_event_id(master_event_id, monday_handler_global)
                    
                    if item_id:
                        print(f"  ✅ Item de Monday encontrado: {item_id}")
                        
                        # 8. Sincronizar el item de Monday
                        try:
                            success = sincronizar_item_via_webhook(
                                item_id, 
                                monday_handler=monday_handler_global,
                                google_service=google_service_global
                            )
                            if success:
                                print(f"  ✅ Sincronización completada para item {item_id}")
                            else:
                                print(f"  ❌ Error en sincronización para item {item_id}")
                        except Exception as e:
                            print(f"  ❌ Error inesperado durante sincronización: {e}")
                    else:
                        print(f"  ❌ No se encontró item de Monday para master_event_id: {master_event_id}")
                
                print(f"\n✅ Procesamiento completado para {len(eventos_cambiados)} eventos")
                    
            except Exception as e:
                print(f"❌ Error al procesar eventos actualizados: {e}")
        else:
            print("❌ Servicio de Google Calendar no disponible")
            
    except Exception as e:
        print(f"❌ Error procesando webhook de Google: {e}")
    
    # Devolver una respuesta vacía con código 200 OK
    return '', 200

if __name__ == '__main__':
    # Esto permite ejecutar el servidor directamente desde el terminal
    # con 'python app.py'. El 'debug=True' es útil para el desarrollo.
    app.run(debug=True, port=6754) 