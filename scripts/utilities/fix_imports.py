#!/usr/bin/env python3
"""
Script para arreglar las importaciones en los scripts de testing
después de la reorganización del proyecto
"""
import os
import glob
import sys

def fix_imports_in_file(file_path):
    """Arregla las importaciones en un archivo específico"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Añadir sys.path para que los scripts puedan importar desde el directorio raíz
        if 'import sys' not in content:
            # Buscar la primera línea de import
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    # Insertar sys.path antes de las importaciones
                    lines.insert(i, 'import os')
                    lines.insert(i+1, 'import sys')
                    lines.insert(i+2, 'sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))')
                    break
            content = '\n'.join(lines)
        
        # Solo escribir si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Importaciones arregladas: {file_path}")
            return True
        else:
            print(f"ℹ️  Sin cambios en importaciones: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error arreglando importaciones en {file_path}: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 ARREGLANDO IMPORTACIONES EN SCRIPTS")
    print("=" * 50)
    
    # Solo procesar scripts de testing
    test_files = glob.glob('scripts/testing/*.py')
    
    updated_count = 0
    total_count = 0
    
    for file_path in test_files:
        if os.path.exists(file_path):
            total_count += 1
            if fix_imports_in_file(file_path):
                updated_count += 1
    
    print("=" * 50)
    print(f"📊 RESUMEN:")
    print(f"   - Archivos procesados: {total_count}")
    print(f"   - Archivos actualizados: {updated_count}")
    print(f"   - Archivos sin cambios: {total_count - updated_count}")
    print("✅ Arreglo de importaciones completado")

if __name__ == "__main__":
    main()
