#!/usr/bin/env python3
"""
Script para activar las Notificaciones Push de Google Calendar
para todos los filmmakers configurados y el calendario maestro.

Este script registra webhooks de notificación push para cada calendario
de filmmaker y el calendario maestro, permitiendo recibir notificaciones 
en tiempo real cuando se creen, actualicen o eliminen eventos.

También crea un mapeo de canales para traducir channel_id a calendar_id.

Autor: Sistema de Sincronización Monday-Google
Fecha: 2025-01-27
"""

import os
import json
from dotenv import load_dotenv
import config
from google_calendar_service import get_calendar_service, register_google_push_notification

def load_channel_map():
    """
    Carga el mapeo de canales existente desde el archivo JSON.
    
    Returns:
        dict: Diccionario con el mapeo channel_id -> calendar_id
    """
    channel_map_file = "google_channel_map.json"
    
    if os.path.exists(channel_map_file):
        try:
            with open(channel_map_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error al cargar mapeo existente: {e}")
            return {}
    else:
        return {}

def save_channel_map(channel_map):
    """
    Guarda el mapeo de canales en el archivo JSON.
    
    Args:
        channel_map (dict): Diccionario con el mapeo channel_id -> calendar_id
    """
    channel_map_file = "google_channel_map.json"
    
    try:
        with open(channel_map_file, 'w', encoding='utf-8') as f:
            json.dump(channel_map, f, indent=2, ensure_ascii=False)
        print(f"✅ Mapeo de canales guardado en {channel_map_file}")
    except Exception as e:
        print(f"❌ Error al guardar mapeo de canales: {e}")

def register_calendar_notification(google_service, calendar_id, calendar_name, ngrok_url, channel_map):
    """
    Registra una notificación push para un calendario específico.
    
    Args:
        google_service: Servicio de Google Calendar
        calendar_id: ID del calendario
        calendar_name: Nombre descriptivo del calendario
        ngrok_url: URL base de ngrok
        channel_map: Diccionario del mapeo de canales
        
    Returns:
        tuple: (bool, str) - (éxito, channel_id si exitoso)
    """
    print(f"\n--- Registrando {calendar_name} ---")
    print(f"📅 Calendario: {calendar_id}")
    
    try:
        # Registrar la notificación push
        success, channel_id = register_google_push_notification(
            google_service, 
            calendar_id, 
            ngrok_url
        )
        
        if success and channel_id:
            print(f"✅ {calendar_name}: Notificación push registrada exitosamente")
            print(f"   Channel ID: {channel_id}")
            return True, channel_id
        else:
            print(f"❌ {calendar_name}: Error al registrar notificación push")
            return False, None
            
    except Exception as e:
        print(f"❌ {calendar_name}: Excepción al registrar notificación push: {e}")
        return False, None

def main():
    """
    Función principal que registra las notificaciones push para todos los calendarios.
    """
    print("🚀 Iniciando activación de notificaciones push de Google Calendar...")
    
    # 1. Cargar variables de entorno
    print("📋 Cargando variables de entorno...")
    load_dotenv()
    
    # 2. Obtener la URL pública de ngrok
    ngrok_url = os.getenv("NGROK_PUBLIC_URL")
    if not ngrok_url:
        print("❌ Error: NGROK_PUBLIC_URL no está definida en el archivo .env")
        print("   Asegúrate de que ngrok esté ejecutándose y la URL esté configurada.")
        return False
    
    print(f"✅ URL de ngrok obtenida: {ngrok_url}")
    
    # 3. Inicializar el servicio de Google Calendar
    print("🔧 Inicializando servicio de Google Calendar...")
    google_service = get_calendar_service()
    if not google_service:
        print("❌ Error: No se pudo inicializar el servicio de Google Calendar.")
        print("   Verifica que las credenciales estén configuradas correctamente.")
        return False
    
    print("✅ Servicio de Google Calendar inicializado correctamente.")
    
    # 4. Cargar mapeo de canales existente
    print("📋 Cargando mapeo de canales existente...")
    channel_map = load_channel_map()
    print(f"✅ Mapeo cargado: {len(channel_map)} canales existentes")
    
    # 5. Registrar notificación para el Calendario Máster
    print(f"\n👑 Registrando Calendario Máster...")
    master_success, master_channel_id = register_calendar_notification(
        google_service,
        config.MASTER_CALENDAR_ID,
        "Calendario Máster",
        ngrok_url,
        channel_map
    )
    
    if master_success and master_channel_id:
        channel_map[master_channel_id] = config.MASTER_CALENDAR_ID
    
    # 6. Registrar notificación para el Calendario de Eventos Sin Asignar
    print(f"\n📋 Registrando Calendario de Eventos Sin Asignar...")
    unassigned_success, unassigned_channel_id = register_calendar_notification(
        google_service,
        config.UNASSIGNED_CALENDAR_ID,
        "Calendario de Eventos Sin Asignar",
        ngrok_url,
        channel_map
    )
    
    if unassigned_success and unassigned_channel_id:
        channel_map[unassigned_channel_id] = config.UNASSIGNED_CALENDAR_ID
    
    # 7. Iterar sobre los perfiles de filmmakers
    print(f"\n📊 Procesando {len(config.FILMMAKER_PROFILES)} perfiles de filmmakers...")
    
    registros_exitosos = 0
    registros_fallidos = 0
    
    for i, perfil in enumerate(config.FILMMAKER_PROFILES, 1):
        filmmaker_name = perfil.get('monday_name', 'Desconocido')
        calendar_id = perfil.get('calendar_id')
        
        if not calendar_id:
            print(f"⚠️  {filmmaker_name}: No tiene calendar_id configurado. Saltando...")
            registros_fallidos += 1
            continue
        
        # Registrar notificación para este filmmaker
        success, channel_id = register_calendar_notification(
            google_service,
            calendar_id,
            filmmaker_name,
            ngrok_url,
            channel_map
        )
        
        if success and channel_id:
            channel_map[channel_id] = calendar_id
            registros_exitosos += 1
        else:
            registros_fallidos += 1
    
    # 8. Guardar el mapeo de canales actualizado
    print(f"\n💾 Guardando mapeo de canales...")
    save_channel_map(channel_map)
    
    # 9. Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE ACTIVACIÓN DE NOTIFICACIONES PUSH")
    print(f"{'='*60}")
    print(f"👑 Calendario Máster: {'✅ Registrado' if master_success else '❌ Falló'}")
    print(f"📋 Calendario Sin Asignar: {'✅ Registrado' if unassigned_success else '❌ Falló'}")
    print(f"✅ Registros exitosos: {registros_exitosos}")
    print(f"❌ Registros fallidos: {registros_fallidos}")
    print(f"📋 Total procesados: {len(config.FILMMAKER_PROFILES)}")
    print(f"🗺️  Canales mapeados: {len(channel_map)}")
    
    calendarios_totales = (1 if master_success else 0) + (1 if unassigned_success else 0) + registros_exitosos
    
    if calendarios_totales > 0:
        print(f"\n🎉 ¡Éxito! Se registraron notificaciones push para {calendarios_totales} calendarios.")
        print("   Los calendarios ahora recibirán notificaciones en tiempo real.")
        
        if registros_fallidos > 0:
            print(f"\n⚠️  Nota: {registros_fallidos} calendarios no pudieron ser registrados.")
            print("   Revisa los errores anteriores para más detalles.")
        
        return True
    else:
        print(f"\n❌ No se pudo registrar ninguna notificación push.")
        print("   Verifica la configuración y los errores anteriores.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        exit(1) 