#!/usr/bin/env python3
"""
Script para forzar la sincronización entre Monday.com y Google Calendar
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
from datetime import datetime
from dotenv import load_dotenv
from google_calendar_service import get_calendar_service
from monday_api_handler import MondayAPIHandler
from sync_logic import sincronizar_item_via_webhook
import config

# Cargar variables de entorno
load_dotenv()

def forzar_sincronizacion():
    """Fuerza la sincronización entre Monday.com y Google Calendar"""
    
    print("🔄 FORZANDO SINCRONIZACIÓN")
    print("=" * 60)
    
    # Obtener servicios
    google_service = get_calendar_service()
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    if not google_service:
        print("❌ No se pudo obtener el servicio de Google Calendar")
        return False
    
    if not monday_handler:
        print("❌ No se pudo obtener el servicio de Monday")
        return False
    
    try:
        # Item ID específico
        item_id = "9881971936"
        
        print(f"🔄 Forzando sincronización para item {item_id}...")
        
        # Usar la función de sincronización existente
        success = sincronizar_item_via_webhook(
            item_id=item_id,
            monday_handler=monday_handler,
            google_service=google_service
        )
        
        if success:
            print("✅ Sincronización forzada exitosa")
            print("🎯 Monday.com y Google Calendar deberían estar sincronizados")
        else:
            print("❌ Error en sincronización forzada")
        
        return success
        
    except Exception as e:
        print(f"❌ Error durante sincronización forzada: {e}")
        return False

def main():
    """Función principal"""
    print("🔄 FORZADOR DE SINCRONIZACIÓN")
    print("=" * 80)
    
    success = forzar_sincronizacion()
    
    if success:
        print("\n🎉 ¡SINCRONIZACIÓN FORZADA!")
        print("Verifica que Monday.com y Google Calendar están sincronizados")
    else:
        print("\n❌ ERROR EN SINCRONIZACIÓN FORZADA")

if __name__ == "__main__":
    main()
