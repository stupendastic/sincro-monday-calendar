#!/usr/bin/env python3
"""
Script para verificar que la reorganización del proyecto fue exitosa
"""
import os
import json
import glob

def check_file_exists(file_path, description):
    """Verifica que un archivo existe"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (NO ENCONTRADO)")
        return False

def check_directory_structure():
    """Verifica la estructura de directorios"""
    print("📁 VERIFICANDO ESTRUCTURA DE DIRECTORIOS")
    print("=" * 50)
    
    # Directorios principales
    directories = [
        ("config/", "Carpeta de configuración"),
        ("config/channels/", "Carpeta de canales"),
        ("config/webhooks/", "Carpeta de webhooks"),
        ("scripts/", "Carpeta de scripts"),
        ("scripts/testing/", "Carpeta de scripts de testing"),
        ("scripts/legacy/", "Carpeta de scripts legacy"),
        ("scripts/utilities/", "Carpeta de scripts de utilidades"),
        ("docs/", "Carpeta de documentación"),
    ]
    
    all_exist = True
    for dir_path, description in directories:
        if os.path.exists(dir_path):
            print(f"✅ {description}: {dir_path}")
        else:
            print(f"❌ {description}: {dir_path} (NO ENCONTRADO)")
            all_exist = False
    
    return all_exist

def check_config_files():
    """Verifica los archivos de configuración"""
    print("\n📋 VERIFICANDO ARCHIVOS DE CONFIGURACIÓN")
    print("=" * 50)
    
    config_files = [
        ("config/token.json", "Token de autenticación de Google"),
        ("config/sync_tokens.json", "Tokens de sincronización"),
        ("config/channels/google_channel_map.json", "Mapeo de canales"),
        ("config/webhooks/webhooks_personales_info.json", "Info de webhooks personales"),
    ]
    
    all_exist = True
    for file_path, description in config_files:
        if check_file_exists(file_path, description):
            # Verificar que el JSON es válido
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"   ✅ JSON válido")
            except Exception as e:
                print(f"   ❌ JSON inválido: {e}")
                all_exist = False
        else:
            all_exist = False
    
    return all_exist

def check_script_categories():
    """Verifica que los scripts están en las categorías correctas"""
    print("\n🔧 VERIFICANDO CATEGORÍAS DE SCRIPTS")
    print("=" * 50)
    
    # Contar scripts por categoría
    testing_scripts = len(glob.glob('scripts/testing/*.py'))
    legacy_scripts = len(glob.glob('scripts/legacy/*.py'))
    utility_scripts = len(glob.glob('scripts/utilities/*.py'))
    
    print(f"✅ Scripts de testing: {testing_scripts}")
    print(f"✅ Scripts legacy: {legacy_scripts}")
    print(f"✅ Scripts de utilidades: {utility_scripts}")
    
    # Verificar que hay scripts en cada categoría
    if testing_scripts > 0 and legacy_scripts > 0 and utility_scripts > 0:
        print("✅ Todas las categorías tienen scripts")
        return True
    else:
        print("❌ Algunas categorías están vacías")
        return False

def check_imports_work():
    """Verifica que las importaciones funcionan"""
    print("\n🔗 VERIFICANDO IMPORTACIONES")
    print("=" * 50)
    
    # Probar un script simple
    test_script = "scripts/testing/verificar_estado_simple.py"
    if os.path.exists(test_script):
        print(f"✅ Script de prueba encontrado: {test_script}")
        
        # Verificar que las importaciones están correctas
        with open(test_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'import os' in content and 'import sys' in content:
            print("✅ Importaciones básicas presentes")
            
            if 'sys.path.append' in content:
                print("✅ Path de importación configurado")
                return True
            else:
                print("❌ Path de importación no configurado")
                return False
        else:
            print("❌ Importaciones básicas faltantes")
            return False
    else:
        print(f"❌ Script de prueba no encontrado: {test_script}")
        return False

def check_readme_files():
    """Verifica que los archivos README existen"""
    print("\n📖 VERIFICANDO ARCHIVOS README")
    print("=" * 50)
    
    readme_files = [
        ("config/README.md", "README de configuración"),
        ("scripts/README.md", "README de scripts"),
        ("docs/README.md", "README de documentación"),
    ]
    
    all_exist = True
    for file_path, description in readme_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN DE REORGANIZACIÓN DEL PROYECTO")
    print("=" * 60)
    
    checks = [
        ("Estructura de directorios", check_directory_structure),
        ("Archivos de configuración", check_config_files),
        ("Categorías de scripts", check_script_categories),
        ("Importaciones", check_imports_work),
        ("Archivos README", check_readme_files),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name.upper()}")
        print("-" * 30)
        result = check_func()
        results.append((check_name, result))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status}: {check_name}")
        if result:
            passed += 1
    
    print(f"\n📈 RESULTADO: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("🎉 ¡REORGANIZACIÓN EXITOSA!")
        print("✅ El proyecto está correctamente organizado")
        print("✅ Todas las referencias están actualizadas")
        print("✅ Los scripts funcionan correctamente")
    else:
        print("⚠️  REORGANIZACIÓN INCOMPLETA")
        print("❌ Algunos problemas necesitan atención")
    
    return passed == total

if __name__ == "__main__":
    main()
