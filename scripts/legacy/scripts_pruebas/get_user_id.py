#!/usr/bin/env python3
"""
Script para obtener el ID de usuario de Arnau Admin
"""

import os
import sys

# Añadir el directorio actual al path
sys.path.append('.')

from monday_api_handler import MondayAPIHandler
import sync_logic

def main():
    print("🔍 Obteniendo ID de usuario de Arnau Admin...")
    
    # Inicializar Monday handler
    monday_handler = MondayAPIHandler(api_token=os.getenv('MONDAY_API_KEY'))
    
    # Usar la función que ya funciona en sync_logic
    user_directory = sync_logic.get_monday_user_directory(monday_handler)
    
    if not user_directory:
        print("❌ No se pudo obtener el directorio de usuarios")
        return
    
    print(f"📋 Usuarios encontrados: {len(user_directory)}")
    
    # Buscar Arnau Admin
    arnau_id = user_directory.get('Arnau Admin')
    if arnau_id:
        print(f"✅ ID de Arnau Admin: {arnau_id}")
        
        # Mostrar todos los usuarios para referencia
        print("\n📋 Directorio completo de usuarios:")
        for name, user_id in user_directory.items():
            print(f"  - {name}: {user_id}")
    else:
        print("❌ Arnau Admin no encontrado en el directorio")
        print("\n📋 Usuarios disponibles:")
        for name, user_id in user_directory.items():
            print(f"  - {name}: {user_id}")

if __name__ == "__main__":
    main() 