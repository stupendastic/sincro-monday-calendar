from flask import Flask, request, jsonify
import json
import os
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from sync_logic import actualizar_fecha_en_monday, sincronizar_item_especifico

# Cargar variables de entorno
load_dotenv()

# Creamos la aplicación Flask
app = Flask(__name__)

# Inicializar el servicio de Google Calendar
google_service = get_calendar_service()

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
            
            # Llamar a nuestra función principal de sincronización
            try:
                success = sincronizar_item_especifico(item_id)
                if success:
                    print(f"✅ Sincronización completada exitosamente para item {item_id}")
                else:
                    print(f"❌ Error en sincronización para item {item_id}")
            except Exception as e:
                print(f"❌ Error inesperado durante sincronización: {e}")
        else:
            print("⚠️  No se pudo extraer el ID del item del webhook")
        
        # Le decimos a Monday que hemos recibido el evento correctamente.
        return jsonify({'message': 'Webhook recibido con éxito'}), 200


@app.route('/google-webhook', methods=['POST'])
def handle_google_webhook():
    """
    Este endpoint recibirá las notificaciones push de Google Calendar.
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
        # El resource_id en las cabeceras contiene información sobre el evento
        resource_id = request.headers.get('X-Goog-Resource-Id')
        resource_uri = request.headers.get('X-Goog-Resource-Uri')
        
        if resource_uri:
            # Extraer el event_id del resource_uri
            # El formato es: https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}
            import re
            event_match = re.search(r'/events/([^/]+)$', resource_uri)
            if event_match:
                event_id = event_match.group(1)
                print(f"🔄 Evento detectado: {event_id}")
                
                # Obtener los detalles actualizados del evento desde Google Calendar
                if google_service:
                    try:
                        # Buscar el evento en todos los calendarios configurados
                        import config
                        for perfil in config.FILMMAKER_PROFILES:
                            if perfil['calendar_id']:
                                try:
                                    event = google_service.events().get(
                                        calendarId=perfil['calendar_id'],
                                        eventId=event_id
                                    ).execute()
                                    
                                    # Extraer las fechas del evento
                                    start = event.get('start', {})
                                    end = event.get('end', {})
                                    
                                    if start and end:
                                        print(f"📅 Fechas del evento: {start} -> {end}")
                                        
                                        # Actualizar la fecha en Monday.com
                                        # Pasamos los diccionarios completos de Google Calendar
                                        success = actualizar_fecha_en_monday(
                                            event_id, 
                                            start, 
                                            end
                                        )
                                        
                                        if success:
                                            print(f"✅ Sincronización inversa completada para evento {event_id}")
                                        else:
                                            print(f"❌ Error en sincronización inversa para evento {event_id}")
                                        
                                        # Solo procesar el primer evento encontrado
                                        break
                                        
                                except Exception as e:
                                    # El evento no está en este calendario, continuar con el siguiente
                                    continue
                        else:
                            print(f"⚠️  Evento {event_id} no encontrado en ningún calendario configurado")
                            
                    except Exception as e:
                        print(f"❌ Error al obtener detalles del evento: {e}")
                else:
                    print("❌ Servicio de Google Calendar no disponible")
            else:
                print("❌ No se pudo extraer el event_id del resource_uri")
        else:
            print("⚠️  No se encontró X-Goog-Resource-Uri en las cabeceras")
            
    except Exception as e:
        print(f"❌ Error procesando webhook de Google: {e}")
    
    # Devolver una respuesta vacía con código 200 OK
    return '', 200

if __name__ == '__main__':
    # Esto permite ejecutar el servidor directamente desde el terminal
    # con 'python app.py'. El 'debug=True' es útil para el desarrollo.
    app.run(debug=True, port=6754) 