#!/usr/bin/env python3
"""
Script para actualizar todas las referencias de rutas en los archivos
después de la reorganización del proyecto
"""
import os
import glob

def update_file_paths(file_path):
    """Actualiza las rutas en un archivo específico"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Actualizar referencias de google_channel_map.json
        content = content.replace('"google_channel_map.json"', '"config/channels/google_channel_map.json"')
        content = content.replace("'google_channel_map.json'", "'config/channels/google_channel_map.json'")
        content = content.replace('google_channel_map.json', 'config/channels/google_channel_map.json')
        
        # Actualizar referencias de google_channel_info*.json
        content = content.replace('"google_channel_info', '"config/channels/google_channel_info')
        content = content.replace("'google_channel_info", "'config/channels/google_channel_info")
        
        # Actualizar referencias de sync_tokens.json
        content = content.replace('"sync_tokens.json"', '"config/sync_tokens.json"')
        content = content.replace("'sync_tokens.json'", "'config/sync_tokens.json'")
        content = content.replace('sync_tokens.json', 'config/sync_tokens.json')
        
        # Actualizar referencias de token.json
        content = content.replace('"token.json"', '"config/token.json"')
        content = content.replace("'token.json'", "'config/token.json'")
        content = content.replace('token.json', 'config/token.json')
        
        # Actualizar referencias de webhooks_personales_info.json
        content = content.replace('"webhooks_personales_info.json"', '"config/webhooks/webhooks_personales_info.json"')
        content = content.replace("'webhooks_personales_info.json'", "'config/webhooks/webhooks_personales_info.json'")
        content = content.replace('webhooks_personales_info.json', 'config/webhooks/webhooks_personales_info.json')
        
        # Solo escribir si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Actualizado: {file_path}")
            return True
        else:
            print(f"ℹ️  Sin cambios: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error actualizando {file_path}: {e}")
        return False

def main():
    """Función principal"""
    print("🔄 ACTUALIZANDO REFERENCIAS DE RUTAS")
    print("=" * 50)
    
    # Archivos principales
    main_files = [
        'app.py',
        'sync_logic.py',
        'config.py',
        'monday_api_handler.py',
        'google_calendar_service.py',
        'sync_token_manager.py',
        'main.py',
        'monday_service.py'
    ]
    
    # Archivos de testing
    test_files = glob.glob('scripts/testing/*.py')
    legacy_files = glob.glob('scripts/legacy/*.py')
    utility_files = glob.glob('scripts/utilities/*.py')
    
    all_files = main_files + test_files + legacy_files + utility_files
    
    updated_count = 0
    total_count = 0
    
    for file_path in all_files:
        if os.path.exists(file_path):
            total_count += 1
            if update_file_paths(file_path):
                updated_count += 1
    
    print("=" * 50)
    print(f"📊 RESUMEN:")
    print(f"   - Archivos procesados: {total_count}")
    print(f"   - Archivos actualizados: {updated_count}")
    print(f"   - Archivos sin cambios: {total_count - updated_count}")
    print("✅ Actualización completada")

if __name__ == "__main__":
    main()
