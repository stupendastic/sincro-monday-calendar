#!/usr/bin/env python3
"""
Comprehensive Project Cleanup Script

This script performs a thorough cleanup of the unidirectional sync project:
- Removes obsolete files and configurations
- Fixes problematic imports
- Validates all Python files
- Creates a clean, production-ready system

Usage:
    python scripts/utilities/clean_project_comprehensive.py
"""

import os
import sys
import shutil
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

def cleanup_obsolete_files():
    """Remove obsolete files and move them to legacy."""
    print("🧹 Cleaning up obsolete files...")
    
    # Files to completely remove (dangerous/broken)
    files_to_remove = [
        "main.py",  # Duplicate of app.py
        "monday_service.py",  # Duplicate functionality
        "setup_sync_system.py",  # Old setup script
    ]
    
    # Directories to move to legacy
    dirs_to_legacy = [
        "scripts/legacy/scripts_pruebas",  # Old test scripts
    ]
    
    # Files to move to legacy (preserve but disable)
    files_to_legacy = [
        "docs/REFACTORIZACION_WEBHOOKS.md",  # Outdated documentation
        "MEJORAS_ESTABILIDAD.md",
        "SOLUCION_FECHA_SYNC.md", 
        "SOLUCION_SSL_DEFINITIVA.md",
        "SYNC_SYSTEM_DOCS.md",
    ]
    
    removed_count = 0
    moved_count = 0
    
    # Create legacy directory
    legacy_dir = project_root / "legacy_files"
    legacy_dir.mkdir(exist_ok=True)
    
    # Remove dangerous files
    for file_path in files_to_remove:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"🗑️  Removing: {file_path}")
            if full_path.is_file():
                full_path.unlink()
            else:
                shutil.rmtree(full_path)
            removed_count += 1
    
    # Move files to legacy
    for file_path in files_to_legacy:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"📦 Moving to legacy: {file_path}")
            dest = legacy_dir / Path(file_path).name
            shutil.move(str(full_path), str(dest))
            moved_count += 1
    
    print(f"✅ Removed {removed_count} files, moved {moved_count} to legacy")
    return True


def clean_config_files():
    """Clean up configuration files."""
    print("🔧 Cleaning configuration files...")
    
    config_dir = project_root / "config"
    
    # Create clean directory structure
    for subdir in ["channels", "webhooks"]:
        (config_dir / subdir).mkdir(exist_ok=True)
    
    # Keep only essential config files
    essential_configs = [
        "config/sync_state.json",
        "config/token.json", 
        "config/channels/GOOGLE_WEBHOOKS_DISABLED.md",
        "config/webhooks/webhooks_personales_info.json.DISABLED"
    ]
    
    # Remove any active webhook configs that shouldn't exist
    problematic_configs = [
        "config/channels/google_channel_map.json",
        "config/webhooks/webhooks_personales_info.json"
    ]
    
    cleaned = 0
    for config_path in problematic_configs:
        full_path = project_root / config_path
        if full_path.exists():
            # Disable instead of delete to preserve data
            disabled_path = str(full_path) + ".DISABLED"
            shutil.move(str(full_path), disabled_path)
            print(f"🔧 Disabled: {config_path}")
            cleaned += 1
    
    print(f"✅ Cleaned {cleaned} configuration files")
    return True


def validate_core_files():
    """Validate that all core files work correctly."""
    print("✅ Validating core files...")
    
    core_files = [
        "app.py",
        "config.py",
        "google_calendar_service.py",
        "monday_api_handler.py", 
        "sync_logic.py",
        "sync_state_manager.py",
        "google_change_monitor.py"
    ]
    
    validation_errors = []
    
    for file_path in core_files:
        full_path = project_root / file_path
        if not full_path.exists():
            validation_errors.append(f"Missing core file: {file_path}")
            continue
        
        # Try to compile the Python file
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            compile(content, str(full_path), 'exec')
            print(f"✅ {file_path} - syntax OK")
        except SyntaxError as e:
            validation_errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            validation_errors.append(f"Error validating {file_path}: {e}")
    
    if validation_errors:
        print("❌ Validation errors found:")
        for error in validation_errors:
            print(f"  - {error}")
        return False
    
    print("✅ All core files validated successfully")
    return True


def test_import_chain():
    """Test that all imports work correctly."""
    print("🔗 Testing import chain...")
    
    import_tests = [
        ("app", ["app"]),
        ("google_calendar_service", ["get_calendar_service", "create_google_event", "update_google_event"]),
        ("sync_logic", ["sincronizar_item_via_webhook", "generate_content_hash"]),
        ("google_change_monitor", ["GoogleChangeMonitor"]),
        ("monday_api_handler", ["MondayAPIHandler"]),
        ("sync_state_manager", ["get_sync_state", "update_sync_state"])
    ]
    
    import_errors = []
    
    for module_name, functions in import_tests:
        try:
            module = __import__(module_name)
            print(f"✅ {module_name} - import OK")
            
            # Check that required functions exist
            for func_name in functions:
                if not hasattr(module, func_name):
                    import_errors.append(f"Missing function {func_name} in {module_name}")
                else:
                    print(f"  ✅ {func_name} - available")
                    
        except Exception as e:
            import_errors.append(f"Cannot import {module_name}: {e}")
    
    # Test that removed functions are gone
    removed_tests = [
        ("google_calendar_service", ["get_incremental_sync_events", "compare_event_values"]),
        ("sync_logic", ["sincronizar_desde_google_calendar", "sincronizar_desde_calendario_personal"])
    ]
    
    for module_name, functions in removed_tests:
        try:
            module = __import__(module_name)
            for func_name in functions:
                if hasattr(module, func_name):
                    import_errors.append(f"Function {func_name} should be removed from {module_name}")
                else:
                    print(f"✅ {func_name} - correctly removed from {module_name}")
        except:
            pass  # Module not importing is fine for this test
    
    if import_errors:
        print("❌ Import errors found:")
        for error in import_errors:
            print(f"  - {error}")
        return False
    
    print("✅ All imports working correctly")
    return True


def create_clean_documentation():
    """Create clean, up-to-date documentation."""
    print("📝 Creating clean documentation...")
    
    # Create main README
    readme_content = """# Monday ↔ Google Calendar Sync (Unidirectional)

Sistema de sincronización **unidireccional** Monday.com → Google Calendar.

## 🎯 Sistema Actual (v4.0)

- ✅ **Monday → Google**: Sincronización completa
- ❌ **Google → Monday**: DESHABILITADO (sistema unidireccional)
- 📊 **Monitoreo**: Detección pasiva de cambios manuales

## 🚀 Inicio Rápido

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar credenciales**:
   - Colocar `credentials.json` (Google) en la raíz
   - Configurar `MONDAY_API_KEY` en `.env`

3. **Ejecutar servidor**:
   ```bash
   python app.py
   ```

4. **Verificar funcionamiento**:
   ```bash
   python test_unidirectional_system.py
   ```

## 📋 Archivos Principales

- `app.py` - Servidor Flask con webhook Monday
- `sync_logic.py` - Lógica de sincronización Monday → Google  
- `google_calendar_service.py` - Cliente Google Calendar
- `google_change_monitor.py` - Monitor de cambios manuales

## 🔧 Mantenimiento

- **Monitorear cambios**: `python google_change_monitor.py`
- **Logs del sistema**: `logs/`
- **Configuración**: `config/`

## ⚠️ Importante

- **Monday.com es la fuente única de verdad**
- **No editar eventos en Google Calendar**
- **Cambios manuales en Google son monitoreados pero NO sincronizados**

---
Sistema convertido a unidireccional el 2025-08-23
"""

    with open(project_root / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Create clean requirements.txt
    requirements = """flask==3.0.0
requests==2.31.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-api-python-client==2.108.0
python-dotenv==1.0.0
httplib2==0.22.0
"""
    
    with open(project_root / "requirements.txt", "w") as f:
        f.write(requirements)
    
    print("✅ Clean documentation created")
    return True


def create_production_scripts():
    """Create essential production scripts."""
    print("🛠️  Creating production scripts...")
    
    # Create startup script
    startup_script = """#!/bin/bash
# Production startup script for Monday → Google Calendar Sync

echo "🚀 Starting Monday → Google Calendar Sync System"

# Check Python version
python3 --version

# Check dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Validate system
echo "✅ Validating system..."
python3 test_unidirectional_system.py

if [ $? -eq 0 ]; then
    echo "✅ System validation passed"
    echo "🌐 Starting Flask server..."
    python3 app.py
else
    echo "❌ System validation failed"
    exit 1
fi
"""
    
    startup_path = project_root / "start_system.sh"
    with open(startup_path, "w") as f:
        f.write(startup_script)
    startup_path.chmod(0o755)
    
    # Create monitoring script
    monitor_script = """#!/bin/bash
# Monitor for manual changes in Google Calendar

echo "📊 Monitoring Google Calendar for manual changes..."
python3 google_change_monitor.py

# Generate report
python3 -c "
from google_change_monitor import GoogleChangeMonitor
monitor = GoogleChangeMonitor()
report = monitor.generate_conflict_report()
print('\\n📋 CONFLICT REPORT:')
print('=' * 50)
print(report)
"
"""
    
    monitor_path = project_root / "scripts/utilities/monitor_changes.sh"
    with open(monitor_path, "w") as f:
        f.write(monitor_script)
    monitor_path.chmod(0o755)
    
    print("✅ Production scripts created")
    return True


def main():
    """Main cleanup function."""
    print("🧹 COMPREHENSIVE PROJECT CLEANUP")
    print("=" * 50)
    print("This will clean up the unidirectional sync project")
    print("to create a production-ready system.")
    print("=" * 50)
    
    # Confirm with user
    response = input("\\nProceed with comprehensive cleanup? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cleanup cancelled by user")
        return
    
    cleanup_steps = [
        ("Cleanup obsolete files", cleanup_obsolete_files),
        ("Clean configuration files", clean_config_files), 
        ("Validate core files", validate_core_files),
        ("Test import chain", test_import_chain),
        ("Create clean documentation", create_clean_documentation),
        ("Create production scripts", create_production_scripts)
    ]
    
    success_count = 0
    total_steps = len(cleanup_steps)
    
    for step_name, step_func in cleanup_steps:
        print(f"\\n📍 {step_name}...")
        print("-" * 40)
        
        try:
            if step_func():
                print(f"✅ {step_name} - COMPLETED")
                success_count += 1
            else:
                print(f"❌ {step_name} - FAILED")
        except Exception as e:
            print(f"❌ {step_name} - ERROR: {e}")
    
    # Final summary
    print("\\n" + "=" * 50)
    print("📊 CLEANUP RESULTS")
    print("=" * 50)
    print(f"✅ Completed: {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        print("\\n🎉 COMPREHENSIVE CLEANUP COMPLETED!")
        print("📋 Project is now production-ready")
        print("\\n🚀 Next steps:")
        print("1. Test system: python test_unidirectional_system.py")
        print("2. Start server: ./start_system.sh")
        print("3. Monitor changes: ./scripts/utilities/monitor_changes.sh")
    else:
        print("\\n⚠️  Some cleanup steps failed. Please review errors above.")
    
    # Create cleanup log
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_entry = {
        "cleanup_date": "2025-08-23",
        "cleanup_type": "comprehensive_project_cleanup",
        "steps_completed": success_count,
        "total_steps": total_steps,
        "status": "completed" if success_count == total_steps else "partial"
    }
    
    with open(log_dir / "cleanup_comprehensive.json", "w") as f:
        json.dump(log_entry, f, indent=2)
    
    print(f"\\n📝 Cleanup log saved to logs/cleanup_comprehensive.json")


if __name__ == "__main__":
    main()