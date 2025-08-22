#!/usr/bin/env python3
"""
Script para limpiar webhooks existentes de Google Calendar
"""

import os
import json
import requests
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def limpiar_webhooks_existentes():
    """Limpiar todos los webhooks existentes"""
    print("🧹 LIMPIANDO WEBHOOKS EXISTENTES")
    print("=" * 40)
    
    try:
        google_service = get_calendar_service()
        if not google_service:
            print("❌ No se pudo inicializar el servicio de Google Calendar")
            return False
        
        # Lista de calendarios a limpiar
        calendarios = [config.MASTER_CALENDAR_ID]
        
        # Añadir calendarios personales
        for profile in config.FILMMAKER_PROFILES:
            if profile.get('calendar_id'):
                calendarios.append(profile['calendar_id'])
        
        for calendar_id in calendarios:
            print(f"📅 Limpiando webhooks de: {calendar_id}")
            
            try:
                # Obtener webhooks existentes
                response = google_service.events().watch(
                    calendarId=calendar_id,
                    body={
                        'id': 'temp-channel',
                        'type': 'web_hook',
                        'address': 'https://example.com/webhook'
                    }
                ).execute()
                
                # Detener el webhook temporal
                if response.get('id'):
                    google_service.channels().stop(body={
                        'id': response['id'],
                        'resourceId': response.get('resourceId')
                    }).execute()
                    print(f"✅ Webhook temporal detenido: {response['id']}")
                
            except Exception as e:
                if "channelIdNotUnique" in str(e):
                    print(f"⚠️  Webhook ya existe, intentando detener...")
                    # Intentar detener webhooks existentes
                    try:
                        google_service.channels().stop(body={
                            'id': 'stupendastic-sync-channel',
                            'resourceId': 'stupendastic-resource'
                        }).execute()
                        print(f"✅ Webhook existente detenido")
                    except:
                        print(f"⚠️  No se pudo detener webhook existente")
                else:
                    print(f"⚠️  Error limpiando {calendar_id}: {e}")
        
        # Limpiar archivo de mapeo
        try:
            os.remove("google_channel_map.json")
            print("✅ Archivo google_channel_map.json eliminado")
        except FileNotFoundError:
            print("ℹ️  Archivo google_channel_map.json no existía")
        
        print("✅ Limpieza completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 LIMPIEZA DE WEBHOOKS DE GOOGLE CALENDAR")
    print("=" * 50)
    
    if limpiar_webhooks_existentes():
        print("\n✅ LIMPIEZA COMPLETADA")
        print("💡 Ahora puedes ejecutar 'python3 configurar_webhooks_automatico.py'")
    else:
        print("\n❌ ERROR EN LA LIMPIEZA")

if __name__ == "__main__":
    main()
