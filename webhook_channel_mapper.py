#!/usr/bin/env python3
"""
Script de ejemplo para mostrar cómo usar el mapeo de canales
en el webhook de Google Calendar.

Este script demuestra cómo cargar el mapeo de canales y
traducir un channel_id a calendar_id.

Autor: Sistema de Sincronización Monday-Google
Fecha: 2025-01-27
"""

import json
import os

def load_channel_map():
    """
    Carga el mapeo de canales desde el archivo JSON.
    
    Returns:
        dict: Diccionario con el mapeo channel_id -> calendar_id
    """
    channel_map_file = "google_channel_map.json"
    
    if os.path.exists(channel_map_file):
        try:
            with open(channel_map_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error al cargar mapeo de canales: {e}")
            return {}
    else:
        print("⚠️  Archivo google_channel_map.json no encontrado")
        return {}

def get_calendar_id_from_channel(channel_id):
    """
    Obtiene el calendar_id correspondiente a un channel_id.
    
    Args:
        channel_id (str): ID del canal de Google
        
    Returns:
        str: ID del calendario correspondiente, o None si no se encuentra
    """
    channel_map = load_channel_map()
    return channel_map.get(channel_id)

def example_webhook_usage():
    """
    Ejemplo de cómo usar el mapeo en el webhook de Google.
    """
    print("🔍 Ejemplo de uso del mapeo de canales en webhook")
    print("=" * 50)
    
    # Simular un channel_id que llega en el webhook
    example_channel_id = "1ae9cb7b-1ea7-41ba-ae55-4d574d9e1c19"
    
    print(f"📡 Channel ID recibido en webhook: {example_channel_id}")
    
    # Obtener el calendar_id correspondiente
    calendar_id = get_calendar_id_from_channel(example_channel_id)
    
    if calendar_id:
        print(f"✅ Calendar ID encontrado: {calendar_id}")
        
        # Aquí podrías usar el calendar_id para obtener detalles del evento
        print(f"🔄 Ahora puedes usar {calendar_id} para obtener detalles del evento")
    else:
        print(f"❌ No se encontró calendar_id para channel_id: {example_channel_id}")
        print("   Verifica que el canal esté registrado en google_channel_map.json")

def show_channel_map():
    """
    Muestra el contenido actual del mapeo de canales.
    """
    print("🗺️  Contenido actual del mapeo de canales")
    print("=" * 50)
    
    channel_map = load_channel_map()
    
    if channel_map:
        print(f"📊 Total de canales mapeados: {len(channel_map)}")
        print()
        
        for channel_id, calendar_id in channel_map.items():
            print(f"📡 Channel ID: {channel_id}")
            print(f"📅 Calendar ID: {calendar_id}")
            print("-" * 30)
    else:
        print("📭 No hay canales mapeados")
        print("   Ejecuta init_google_notifications.py para crear el mapeo")

if __name__ == "__main__":
    print("🚀 Script de ejemplo: Mapeo de Canales de Google Calendar")
    print("=" * 60)
    
    # Mostrar el mapeo actual
    show_channel_map()
    print()
    
    # Ejemplo de uso en webhook
    example_webhook_usage() 