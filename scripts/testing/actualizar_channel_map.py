#!/usr/bin/env python3
"""
Script para actualizar el mapeo de canales de Google Calendar
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import json
import os

def actualizar_channel_map():
    """Actualiza el mapeo de canales con el nuevo canal creado"""
    
    print("🔧 ACTUALIZANDO MAPEO DE CANALES DE GOOGLE CALENDAR")
    print("=" * 60)
    
    # Cargar información del canal actual
    try:
        with open('config/channels/google_channel_info.json', 'r') as f:
            channel_info = json.load(f)
        
        calendar_id = channel_info.get('calendar_id')
        resource_id = channel_info.get('resource_id')
        
        print(f"📅 Calendario: {calendar_id}")
        print(f"🆔 Resource ID: {resource_id}")
        
    except FileNotFoundError:
        print("❌ No se encontró google_channel_info.json")
        return False
    
    # Cargar el mapeo actual
    try:
        with open('config/channels/config/channels/google_channel_map.json', 'r') as f:
            channel_map = json.load(f)
        
        print(f"📋 Mapeo actual: {len(channel_map)} canales")
        
    except FileNotFoundError:
        print("❌ No se encontró config/channels/google_channel_map.json")
        return False
    
    # Añadir nuestro canal al mapeo
    channel_id = "stupendastic-sync-channel"
    
    if channel_id in channel_map:
        print(f"⚠️ Canal '{channel_id}' ya existe en el mapeo")
        print(f"   Valor actual: {channel_map[channel_id]}")
        print(f"   Nuevo valor: {calendar_id}")
        
        # Preguntar si actualizar
        response = input("¿Actualizar? (y/n): ").lower().strip()
        if response != 'y':
            print("❌ No se actualizó el mapeo")
            return False
    
    # Actualizar el mapeo
    channel_map[channel_id] = calendar_id
    
    # Guardar el mapeo actualizado
    try:
        with open('config/channels/config/channels/google_channel_map.json', 'w') as f:
            json.dump(channel_map, f, indent=2)
        
        print(f"✅ Mapeo actualizado exitosamente")
        print(f"   Canal '{channel_id}' → '{calendar_id}'")
        print(f"   Total de canales: {len(channel_map)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error guardando el mapeo: {e}")
        return False

def verificar_mapeo():
    """Verifica que el mapeo esté correcto"""
    
    print("\n🔍 VERIFICANDO MAPEO DE CANALES")
    print("-" * 40)
    
    try:
        with open('config/channels/config/channels/google_channel_map.json', 'r') as f:
            channel_map = json.load(f)
        
        channel_id = "stupendastic-sync-channel"
        
        if channel_id in channel_map:
            calendar_id = channel_map[channel_id]
            print(f"✅ Canal '{channel_id}' mapeado correctamente")
            print(f"   → {calendar_id}")
            return True
        else:
            print(f"❌ Canal '{channel_id}' no encontrado en el mapeo")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando mapeo: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 ACTUALIZADOR DE MAPEO DE CANALES")
    print("=" * 60)
    
    # Actualizar el mapeo
    success = actualizar_channel_map()
    
    if success:
        # Verificar que se actualizó correctamente
        verificar_mapeo()
        
        print("\n🎉 ¡MAPEO ACTUALIZADO!")
        print("=" * 40)
        print("✅ El webhook de Google Calendar debería funcionar ahora")
        print("✅ Prueba moviendo un evento en Google Calendar")
        print("✅ Observa los logs del servidor")
    else:
        print("\n❌ Error actualizando el mapeo")

if __name__ == "__main__":
    main()
