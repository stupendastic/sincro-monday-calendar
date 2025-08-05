import os
import requests
import json
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service, create_google_event, update_google_event, create_and_share_calendar, register_google_push_notification
from monday_service import get_monday_user_directory, get_single_item_details, update_monday_column, MONDAY_API_URL, HEADERS
from sync_logic import parse_monday_item, sincronizar_item_especifico, actualizar_fecha_en_monday

# Importamos nuestros módulos locales
import config  # Importa nuestro nuevo archivo de configuración
from google_calendar_service import get_calendar_service

# Carga las variables del archivo .env
load_dotenv()

def get_monday_board_items(board_id, column_ids):
    """Obtiene todos los elementos de un tablero usando paginación - VERSIÓN LIGERA para filtrar."""
    
    # 1. Inicializar variables
    all_items = []
    cursor = None
    
    # Solo necesitamos las columnas mínimas para filtrar: FechaGrab y Operario
    filter_columns = ["fecha56", "personas1"]  # IDs de FechaGrab y Operario
    ids_string = '", "'.join(filter_columns)

    # 2. Bucle infinito para paginación
    while True:
        # 3. Query LIGERA para filtrar - solo datos mínimos
        query = f"""
        query($cursor: String) {{
            boards(ids: {board_id}) {{
                items_page(limit: 100, cursor: $cursor) {{
                    items {{
                        id
                        name
                        column_values(ids: ["{ids_string}"]) {{
                            id
                            text
                            value
                            type
                        }}
                    }}
                    cursor
                }}
            }}
        }}
        """
        
        # Variables para la petición
        variables = {}
        if cursor:
            variables['cursor'] = cursor
            
        data = {'query': query, 'variables': variables}
        
        try:
            # 4a. Hacer llamada a la API
            response = requests.post(url=MONDAY_API_URL, json=data, headers=HEADERS)
            response.raise_for_status()
            response_data = response.json()
            
            # 4b. Añadir items de esta página a la lista
            items_page = response_data.get('data', {}).get('boards', [{}])[0].get('items_page', {})
            current_items = items_page.get('items', [])
            all_items.extend(current_items)
            
            # 4c. Extraer el nuevo cursor
            new_cursor = items_page.get('cursor')
            
            # 4d. Condición de salida
            if not new_cursor:
                break
                
            # 4e. Actualizar cursor para la siguiente iteración
            cursor = new_cursor
            
        except Exception as e:
            print(f"Error al obtener los elementos de Monday: {e}")
            return None
    
    # 5. Devolver la lista completa
    return {'data': {'boards': [{'items_page': {'items': all_items}}]}}





def parse_light_item_for_filtering(item):
    """Procesa un item ligero para extraer solo la información necesaria para filtrar."""
    
    parsed_item = {
        'id': item.get('id'),
        'name': item.get('name')
    }

    # Creamos un diccionario para acceder fácilmente a los valores por su ID
    column_values_by_id = {cv['id']: cv for cv in item['column_values']}

    # Solo procesamos las columnas necesarias para filtrar
    # FechaGrab
    fecha_col = column_values_by_id.get('fecha56')
    if fecha_col and fecha_col.get('value'):
        value_data = json.loads(fecha_col['value'])
        date_value = value_data.get('date')
        time_value = value_data.get('time')
        
        if time_value and time_value != 'null':
            parsed_item['fecha_inicio'] = f"{date_value}T{time_value}"
        else:
            parsed_item['fecha_inicio'] = date_value
    else:
        parsed_item['fecha_inicio'] = None

    # Operario
    operario_col = column_values_by_id.get('personas1')
    if operario_col:
        parsed_item['operario'] = operario_col.get('text')
        
        # Extraer email y IDs del operario
        if operario_col.get('value'):
            try:
                value_data = json.loads(operario_col['value'])
                persons = value_data.get('personsAndTeams', [])
                parsed_item['operario_email'] = persons[0].get('email') if persons else None
                
                # Extraer IDs de todos los operarios asignados
                operario_ids = []
                for person in persons:
                    if person.get('id'):
                        operario_ids.append(person['id'])
                parsed_item['operario_ids'] = operario_ids
            except (json.JSONDecodeError, KeyError):
                parsed_item['operario_email'] = None
                parsed_item['operario_ids'] = []
        else:
            parsed_item['operario_email'] = None
            parsed_item['operario_ids'] = []
    else:
        parsed_item['operario'] = None
        parsed_item['operario_email'] = None
        parsed_item['operario_ids'] = []

    return parsed_item

















def main():
    """Función principal de la aplicación."""
    print("Iniciando Sincronizador Stupendastic...")
    
    # 1. Inicializar contadores
    items_procesados = 0
    items_sincronizados = 0
    items_saltados = 0
    
    google_service = get_calendar_service()
    if not google_service or not MONDAY_API_KEY:
        print("Error en la inicialización de servicios. Abortando.")
        return

    print("✅ Servicios inicializados.")

    # 2. Obtener URL de ngrok para webhooks
    NGROK_URL = os.getenv("NGROK_PUBLIC_URL")
    if not NGROK_URL:
        print("⚠️  NGROK_PUBLIC_URL no está configurada en .env")
        print("   Los canales de notificación push no se registrarán.")
        print("   Añade NGROK_PUBLIC_URL=https://tu-url.ngrok.io a tu archivo .env")
    else:
        print(f"✅ URL de ngrok configurada: {NGROK_URL}")

    # 3. Obtener directorio de usuarios de Monday.com
    user_directory = get_monday_user_directory()
    if not user_directory:
        print("❌ Error al obtener directorio de usuarios. Abortando.")
        return

    print(f"Obteniendo datos del tablero: {config.BOARD_ID_GRABACIONES}...")
    monday_response = get_monday_board_items(config.BOARD_ID_GRABACIONES, config.COLUMN_IDS)

    if not monday_response:
        print("Error al obtener datos de Monday: No se recibió respuesta")
        return
    
    if 'errors' in monday_response:
        print("Error al obtener datos de Monday:", monday_response.get('errors'))
        return

    items = monday_response.get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
    print(f"Se encontraron {len(items)} elemento(s).")
    print("-" * 40)

    # PASO 1: Filtrar items ligeros para obtener información básica
    items_filtrados = []
    for item in items:
        item_ligero = parse_light_item_for_filtering(item)
        items_procesados += 1
        
        # Comprobamos si el item es apto (tiene fecha y un operario)
        operario_nombre = item_ligero.get('operario')
        operario_ids = item_ligero.get('operario_ids', [])
        
        if not operario_nombre or not item_ligero.get('fecha_inicio'):
            if not operario_nombre:
                print(f"-> Saltando '{item_ligero['name']}': No tiene operario asignado.")
            else:
                print(f"-> Saltando '{item_ligero['name']}': No tiene fecha asignada.")
            items_saltados += 1
            continue
        
        items_filtrados.append(item_ligero)

    print(f"Items aptos para procesamiento: {len(items_filtrados)}")
    print("-" * 40)

    # PASO 2: Iterar sobre cada perfil de filmmaker
    config_updated = False  # Variable para rastrear si se actualizó algún perfil
    
    for perfil in config.FILMMAKER_PROFILES:
        print(f"--- Procesando perfil para: {perfil['monday_name']} ---")
        
        # Traducir nombre del perfil a ID de usuario
        user_id = user_directory.get(perfil['monday_name'])
        if not user_id:
            print(f"❌ No se pudo encontrar el ID de usuario para '{perfil['monday_name']}' en Monday.com.")
            print(f"   Usuarios disponibles: {list(user_directory.keys())}")
            continue
        
        print(f"   -> ID de usuario encontrado: {user_id}")
        
        # Guardar el user_id en el perfil si no está ya guardado
        if perfil.get('monday_user_id') is None:
            perfil['monday_user_id'] = user_id
            config_updated = True
            print(f"   -> [NUEVO] ID de usuario guardado en perfil: {user_id}")
        elif perfil['monday_user_id'] != user_id:
            # Si el ID ha cambiado, actualizarlo
            old_id = perfil['monday_user_id']
            perfil['monday_user_id'] = user_id
            config_updated = True
            print(f"   -> [ACTUALIZADO] ID de usuario actualizado: {old_id} → {user_id}")
        else:
            print(f"   -> [CACHE] Usando ID de usuario en caché: {user_id}")
        
        # Verificar si el perfil tiene calendar_id configurado
        if perfil['calendar_id'] is None:
            print(f"-> [ACCIÓN] El perfil para {perfil['monday_name']} necesita un calendario. Creando ahora...")
            new_id = create_and_share_calendar(google_service, perfil['monday_name'], perfil['personal_email'])
            
            if new_id:
                # Actualizar el perfil en memoria
                perfil['calendar_id'] = new_id
                config_updated = True
                print(f"-> [ÉXITO] El perfil de {perfil['monday_name']} ha sido actualizado en memoria con el nuevo ID de calendario.")
            else:
                print(f"-> [ERROR] No se pudo crear el calendario para {perfil['monday_name']}. Saltando sincronización.")
                continue
        
        # REGISTRAR CANAL DE NOTIFICACIONES PUSH DE GOOGLE
        if NGROK_URL and perfil['calendar_id']:
            print(f"-> [NOTIFICACIONES] Registrando canal push para {perfil['monday_name']}...")
            push_success = register_google_push_notification(
                google_service, 
                perfil['calendar_id'], 
                NGROK_URL
            )
            if push_success:
                print(f"✅ Canal de notificaciones registrado para {perfil['monday_name']}")
            else:
                print(f"⚠️  No se pudo registrar canal de notificaciones para {perfil['monday_name']}")
        
        # PASO 3: Iterar sobre todos los items filtrados
        for item_ligero in items_filtrados:
            # Comprobar si el ID del usuario del perfil está en la lista de IDs de operarios del item
            operario_ids = item_ligero.get('operario_ids', [])
            if user_id in operario_ids:
                print(f"✅ Coincidencia encontrada para '{item_ligero['name']}' con {perfil['monday_name']} (ID: {user_id})")
                
                # Obtener detalles completos del item
                item_completo = get_single_item_details(item_ligero['id'])
                if not item_completo:
                    print(f"❌ Error al obtener detalles del item '{item_ligero['name']}'. Saltando...")
                    items_saltados += 1
                    continue
                
                # Procesar el item completo
                item_procesado = parse_monday_item(item_completo)
                calendar_id = perfil['calendar_id']
                google_event_id = item_procesado.get('google_event_id')
                
                print(f"Procesando '{item_procesado['name']}' para {perfil['monday_name']}...")
                
                # LÓGICA DE UPSERT
                if google_event_id:
                    # Si ya existe un ID de evento, actualizamos
                    print(f"-> [INFO] Item '{item_procesado['name']}' ya tiene evento. Actualizando...")
                    update_google_event(google_service, calendar_id, item_procesado)
                    items_sincronizados += 1
                else:
                    # Si no existe ID, creamos nuevo evento
                    print(f"-> [INFO] Item '{item_procesado['name']}' es nuevo. Creando...")
                    new_event_id = create_google_event(google_service, calendar_id, item_procesado)
                    
                    if new_event_id:
                        # Guardamos el ID del nuevo evento en Monday
                        print(f"> [DEBUG] Google devolvió el ID: {new_event_id}. Intentando guardarlo en Monday...")
                        update_monday_column(
                            item_procesado['id'], 
                            config.BOARD_ID_GRABACIONES, 
                            config.COL_GOOGLE_EVENT_ID, 
                            new_event_id
                        )
                        items_sincronizados += 1
                    else:
                        print(f"❌ Error al crear evento para '{item_procesado['name']}'")
                        items_saltados += 1
                
                print("-" * 20)
            else:
                # No hay coincidencia, continuar con el siguiente item
                continue

    # Mostrar información sobre actualizaciones de configuración
    if config_updated:
        print("\n" + "=" * 50)
        print("⚠️  CONFIGURACIÓN ACTUALIZADA")
        print("=" * 50)
        print("Se han creado nuevos calendarios o actualizado IDs de usuario durante esta ejecución.")
        print("Para hacer permanentes estos cambios, actualiza manualmente config.py")
        print("con los nuevos calendar_id y monday_user_id que se mostraron arriba.")
        print("=" * 50)

    # Guardar cambios en config.py si se actualizaron perfiles
    if config_updated:
        print("\n--- [GUARDANDO] Se han detectado cambios en la configuración. Escribiendo en config.py... ---")
        
        try:
            # Leer el contenido actual del archivo config.py
            with open('config.py', 'r', encoding='utf-8') as file:
                config_content = file.read()
            
            # Encontrar la línea donde empieza FILMMAKER_PROFILES
            lines = config_content.split('\n')
            new_lines = []
            in_filmmaker_profiles = False
            filmmaker_profiles_started = False
            
            for line in lines:
                if line.strip().startswith('FILMMAKER_PROFILES = ['):
                    # Marcar que hemos encontrado el inicio
                    filmmaker_profiles_started = True
                    in_filmmaker_profiles = True
                    new_lines.append(line)
                    continue
                
                if filmmaker_profiles_started and in_filmmaker_profiles:
                    # Si estamos dentro de FILMMAKER_PROFILES, saltamos las líneas hasta encontrar el final
                    if line.strip() == ']':
                        in_filmmaker_profiles = False
                        # Escribir la nueva lista de perfiles
                        new_lines.append('')
                        for i, perfil in enumerate(config.FILMMAKER_PROFILES):
                            if i == 0:
                                new_lines.append('    {')
                            else:
                                new_lines.append('    },')
                                new_lines.append('    {')
                            
                            new_lines.append(f'        "monday_name": "{perfil["monday_name"]}",')
                            new_lines.append(f'        "personal_email": "{perfil["personal_email"]}",')
                            
                            if perfil['calendar_id'] is None:
                                new_lines.append('        "calendar_id": None,')
                            else:
                                new_lines.append(f'        "calendar_id": "{perfil["calendar_id"]}",')
                            
                            if perfil.get('monday_user_id') is None:
                                new_lines.append('        "monday_user_id": None')
                            else:
                                new_lines.append(f'        "monday_user_id": "{perfil["monday_user_id"]}"')
                            
                            new_lines.append('    }')
                        new_lines.append(']')
                        continue
                    else:
                        # Saltar líneas dentro de FILMMAKER_PROFILES
                        continue
                
                # Si no estamos en FILMMAKER_PROFILES, añadir la línea tal como está
                new_lines.append(line)
            
            # Escribir el archivo actualizado
            with open('config.py', 'w', encoding='utf-8') as file:
                file.write('\n'.join(new_lines))
            
            print("✅ ¡Archivo config.py actualizado con los nuevos IDs de calendario y usuarios!")
            
        except Exception as e:
            print(f"❌ Error al actualizar config.py: {e}")
            print("Los cambios se mantienen solo en memoria. Actualiza manualmente config.py.")

    # Resumen detallado
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE SINCRONIZACIÓN")
    print("=" * 50)
    print(f"📋 Elementos procesados: {items_procesados}")
    print(f"✅ Eventos sincronizados: {items_sincronizados}")
    print(f"⏭️  Elementos saltados: {items_saltados}")
    print("=" * 50)

    print("\nProceso de sincronización terminado.")

if __name__ == "__main__":
    main()