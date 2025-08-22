#!/usr/bin/env python3
"""
Script para limpiar canales obsoletos y actualizar el mapeo de canales
"""
import os
import json
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

def limpiar_canales_obsoletos():
    """Limpia canales obsoletos y actualiza el mapeo"""
    
    print("🧹 LIMPIANDO CANALES OBSOLETOS")
    print("=" * 50)
    
    load_dotenv()
    
    # Cargar el mapeo actual
    try:
        with open('google_channel_map.json', 'r', encoding='utf-8') as f:
            channel_map = json.load(f)
    except FileNotFoundError:
        print("❌ No se encontró google_channel_map.json")
        return
    
    print(f"📋 Canales en mapeo actual: {len(channel_map)}")
    
    # Obtener servicio de Google
    google_service = get_calendar_service()
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return
    
    # Lista de calendarios válidos
    calendarios_validos = [
        config.MASTER_CALENDAR_ID,
        config.UNASSIGNED_CALENDAR_ID
    ]
    
    # Añadir calendarios de filmmakers
    for profile in config.FILMMAKER_PROFILES:
        calendarios_validos.append(profile['calendar_id'])
    
    print(f"📅 Calendarios válidos: {len(calendarios_validos)}")
    
    # Limpiar canales obsoletos
    canales_a_eliminar = []
    canales_validos = {}
    
    for channel_id, calendar_id in channel_map.items():
        if calendar_id in calendarios_validos:
            canales_validos[channel_id] = calendar_id
            print(f"✅ Canal válido: {channel_id} -> {calendar_id}")
        else:
            canales_a_eliminar.append(channel_id)
            print(f"❌ Canal obsoleto: {channel_id} -> {calendar_id}")
    
    # Guardar mapeo limpio
    with open('google_channel_map.json', 'w', encoding='utf-8') as f:
        json.dump(canales_validos, f, indent=2)
    
    print(f"\n✅ Mapeo actualizado: {len(canales_validos)} canales válidos")
    print(f"🗑️  Canales eliminados: {len(canales_a_eliminar)}")
    
    if canales_a_eliminar:
        print("\n📋 Canales eliminados:")
        for channel_id in canales_a_eliminar:
            print(f"   - {channel_id}")

if __name__ == "__main__":
    limpiar_canales_obsoletos()
