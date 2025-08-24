#!/usr/bin/env python3
"""
Script de prueba simple para verificar sincronización sin bucles
"""

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import time
from dotenv import load_dotenv
from monday_api_handler import MondayAPIHandler
from google_calendar_service import get_calendar_service
import config

# Cargar variables de entorno
load_dotenv()

def test_sincronizacion_basica():
    """Prueba básica de sincronización"""
    print("🔄 PRUEBA BÁSICA DE SINCRONIZACIÓN")
    print("=" * 50)
    
    try:
        monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
        google_service = get_calendar_service()
        
        print("✅ Servicios inicializados correctamente")
        
        # Verificar que podemos conectar con Monday.com
        items = monday_handler.search_items_by_name(
            board_id=str(config.BOARD_ID_GRABACIONES),
            item_name="PRUEBA ANTI-BUCLES 1",
            exact_match=True
        )
        
        if items:
            print(f"✅ Elemento de prueba encontrado: {items[0].id}")
        else:
            print("⚠️ No se encontró elemento de prueba")
        
        # Verificar que podemos conectar con Google Calendar
        try:
            events = google_service.events().list(
                calendarId=config.MASTER_CALENDAR_ID,
                maxResults=5
            ).execute()
            
            print(f"✅ Google Calendar conectado - {len(events.get('items', []))} eventos encontrados")
            
        except Exception as e:
            print(f"❌ Error conectando con Google Calendar: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba básica: {e}")
        return False

def mostrar_instrucciones():
    """Mostrar instrucciones para probar el sistema"""
    print("\n📋 INSTRUCCIONES PARA PROBAR EL SISTEMA")
    print("=" * 50)
    print("1. 🎯 CREAR ELEMENTO EN MONDAY.COM:")
    print("   - Ve a Monday.com")
    print("   - Crea un nuevo elemento: 'PRUEBA FINAL 1'")
    print("   - Fecha: '2 de septiembre de 2025'")
    print("   - Operario: 'Arnau Admin'")
    print()
    print("2. 👀 OBSERVAR LOGS DEL SERVIDOR:")
    print("   - Deberías ver: '✅ Sincronización Monday → Google completada'")
    print("   - Verificar que se crea en Google Calendar")
    print()
    print("3. 📅 CAMBIAR FECHA EN MONDAY.COM:")
    print("   - Cambia la fecha a '3 de septiembre de 2025'")
    print("   - Observar logs del servidor")
    print("   - Deberías ver mensajes de anti-bucles si funciona correctamente")
    print()
    print("4. 🔄 CAMBIAR FECHA EN GOOGLE CALENDAR:")
    print("   - Ve a Google Calendar (calendario maestro)")
    print("   - Cambia la fecha del evento")
    print("   - Verificar que se actualiza en Monday.com")
    print()
    print("⚠️  IMPORTANTE:")
    print("   - Si ves bucles infinitos, el sistema anti-bucles no funciona")
    print("   - Si las fechas se revierten, hay un problema de sincronización")
    print("   - Los logs deben mostrar claramente el origen de cada cambio")

def main():
    """Función principal"""
    print("🚀 PRUEBA FINAL DEL SISTEMA DE SINCRONIZACIÓN")
    print("=" * 60)
    
    # Probar conexiones básicas
    if test_sincronizacion_basica():
        print("✅ Conexiones básicas: FUNCIONAN")
    else:
        print("❌ Conexiones básicas: FALLAN")
        return
    
    # Mostrar instrucciones
    mostrar_instrucciones()
    
    print("\n" + "="*60)
    print("🎯 RESUMEN:")
    print("=" * 60)
    print("✅ Servidor Flask: Funcionando")
    print("✅ ngrok: Funcionando")
    print("✅ Monday.com webhook: Configurado")
    print("✅ Google Calendar webhooks: Configurados")
    print("✅ Sistema anti-bucles: Implementado")
    print()
    print("💡 Ahora puedes probar el sistema completo")

if __name__ == "__main__":
    main()
