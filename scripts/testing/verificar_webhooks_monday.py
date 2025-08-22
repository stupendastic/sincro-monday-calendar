#!/usr/bin/env python3
"""
Script para verificar los webhooks existentes en Monday.com
"""
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os
import requests
from dotenv import load_dotenv
import config

# Cargar variables de entorno
load_dotenv()

def verificar_webhooks_monday():
    """Verifica los webhooks existentes en Monday.com"""
    
    print("🔍 VERIFICANDO WEBHOOKS DE MONDAY.COM")
    print("=" * 60)
    
    # Headers para la API de Monday
    headers = {
        'Authorization': os.getenv('MONDAY_API_KEY'),
        'Content-Type': 'application/json'
    }
    
    # Query para obtener información del board
    query = '''
    query ($boardId: ID!) {
        boards(ids: [$boardId]) {
            id
            name
            webhooks {
                id
                event
            }
        }
    }
    '''
    
    variables = {
        'boardId': config.BOARD_ID_GRABACIONES
    }
    
    try:
        # Hacer la petición a Monday.com
        response = requests.post(
            'https://api.monday.com/v2',
            json={'query': query, 'variables': variables},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print(f"❌ Error en Monday.com: {data['errors']}")
                return False
            
            board_data = data['data']['boards'][0]
            print(f"✅ Board encontrado: {board_data['name']} (ID: {board_data['id']})")
            
            webhooks = board_data.get('webhooks', [])
            if webhooks:
                print(f"\n📋 Webhooks existentes ({len(webhooks)}):")
                for i, webhook in enumerate(webhooks, 1):
                    print(f"   {i}. ID: {webhook['id']} | Evento: {webhook['event']}")
            else:
                print(f"\nℹ️  No hay webhooks configurados")
            
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando webhooks: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 VERIFICADOR DE WEBHOOKS MONDAY.COM")
    print("=" * 60)
    
    success = verificar_webhooks_monday()
    
    if success:
        print("\n✅ Verificación completada")
    else:
        print("\n❌ ERROR EN LA VERIFICACIÓN")

if __name__ == "__main__":
    main()
