#!/usr/bin/env python3
"""
Script de prueba específico para verificar la función _obtener_item_id_por_google_event_id.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Importar módulos necesarios
import config
from monday_api_handler import MondayAPIHandler
from sync_logic import _obtener_item_id_por_google_event_id

# Cargar variables de entorno
load_dotenv()

def test_monday_query():
    """
    Prueba la función _obtener_item_id_por_google_event_id con diferentes casos.
    """
    print("🧪 PRUEBA DE CONSULTA A MONDAY.COM")
    print("=" * 50)
    
    # Inicializar Monday API Handler
    monday_handler = MondayAPIHandler(api_token=os.getenv("MONDAY_API_KEY"))
    
    # Casos de prueba
    test_cases = [
        "ijhp0rh2vj05dgl0v4llifid30",  # ID que aparece en los logs
        "23ehirmtgnsqm7duu5safhpo3g",   # Otro ID de los logs
        "6g15ksp5o3628akf2amn2bbgig",   # Otro ID de los logs
        "ehlicou1a1uh1bci0qpts01agk",   # Otro ID de los logs
    ]
    
    for i, google_event_id in enumerate(test_cases, 1):
        print(f"\n📋 PRUEBA {i}: Google Event ID = {google_event_id}")
        print("-" * 40)
        
        try:
            item_id = _obtener_item_id_por_google_event_id(google_event_id, monday_handler)
            
            if item_id:
                print(f"✅ ÉXITO: Item encontrado con ID {item_id}")
            else:
                print(f"ℹ️  No se encontró item para este Google Event ID")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n🎉 Pruebas completadas")

if __name__ == "__main__":
    test_monday_query() 