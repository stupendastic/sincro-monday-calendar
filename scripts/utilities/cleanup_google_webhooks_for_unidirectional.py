#!/usr/bin/env python3
"""
Cleanup Google Webhooks for Unidirectional Sync Migration

This script properly stops all Google Calendar webhook channels and prepares
the system for unidirectional Monday → Google synchronization.

Usage:
    python scripts/utilities/cleanup_google_webhooks_for_unidirectional.py
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from google_calendar_service import get_calendar_service


def stop_google_webhook_channel(service, channel_id, resource_id):
    """
    Stop a specific Google webhook channel.
    
    Args:
        service: Google Calendar service instance
        channel_id: Channel ID to stop
        resource_id: Resource ID for the channel
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"🔧 Stopping channel: {channel_id}")
        
        # Stop the webhook channel
        service.channels().stop(
            body={
                'id': channel_id,
                'resourceId': resource_id
            }
        ).execute()
        
        print(f"✅ Channel {channel_id} stopped successfully")
        return True
        
    except Exception as e:
        if "not found" in str(e).lower():
            print(f"ℹ️  Channel {channel_id} already stopped or not found")
            return True
        else:
            print(f"❌ Error stopping channel {channel_id}: {e}")
            return False


def cleanup_webhook_configurations():
    """
    Clean up webhook configuration files by disabling them.
    """
    print("\n📂 Cleaning up webhook configuration files...")
    
    disabled_files = []
    
    # List of files to disable
    config_files = [
        "config/channels/google_channel_map.json.DISABLED",
        "config/webhooks/webhooks_personales_info.json.DISABLED"
    ]
    
    for file_path in config_files:
        if os.path.exists(file_path):
            print(f"ℹ️  Already disabled: {file_path}")
        elif os.path.exists(file_path.replace('.DISABLED', '')):
            # File exists without .DISABLED suffix, already handled
            print(f"ℹ️  Previously disabled: {file_path}")
        
    # Disable any remaining channel info files
    channels_dir = "config/channels"
    if os.path.exists(channels_dir):
        for filename in os.listdir(channels_dir):
            if filename.startswith("google_channel_info_") and filename.endswith(".json"):
                if not filename.endswith(".DISABLED"):
                    original_path = os.path.join(channels_dir, filename)
                    disabled_path = original_path + ".DISABLED"
                    try:
                        os.rename(original_path, disabled_path)
                        disabled_files.append(disabled_path)
                        print(f"🔧 Disabled: {filename}")
                    except Exception as e:
                        print(f"⚠️  Could not disable {filename}: {e}")
    
    return disabled_files


def stop_all_webhooks():
    """
    Stop all active Google webhook channels.
    """
    print("🚀 Starting Google Webhook Cleanup for Unidirectional Sync")
    print("=" * 60)
    
    # Initialize Google Calendar service
    print("📡 Initializing Google Calendar service...")
    service = get_calendar_service()
    
    if not service:
        print("❌ Could not initialize Google Calendar service")
        return False
    
    print("✅ Google Calendar service initialized")
    
    # Read webhook configurations
    webhook_configs = []
    
    # Check for disabled webhook files
    disabled_webhook_file = "config/webhooks/webhooks_personales_info.json.DISABLED"
    if os.path.exists(disabled_webhook_file):
        print(f"📋 Reading disabled webhook config: {disabled_webhook_file}")
        try:
            with open(disabled_webhook_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                webhook_configs.extend(data.get('webhooks_personales', []))
        except Exception as e:
            print(f"⚠️  Error reading disabled webhook config: {e}")
    
    # Check for active webhook files (shouldn't exist after migration)
    active_webhook_file = "config/webhooks/webhooks_personales_info.json"
    if os.path.exists(active_webhook_file):
        print(f"⚠️  Found active webhook config (will disable): {active_webhook_file}")
        try:
            with open(active_webhook_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                webhook_configs.extend(data.get('webhooks_personales', []))
            
            # Disable the active file
            os.rename(active_webhook_file, active_webhook_file + ".DISABLED")
            print(f"🔧 Disabled active webhook config")
            
        except Exception as e:
            print(f"⚠️  Error processing active webhook config: {e}")
    
    if not webhook_configs:
        print("ℹ️  No webhook configurations found to clean up")
        return True
    
    # Stop each webhook channel
    print(f"\n🔧 Stopping {len(webhook_configs)} webhook channels...")
    
    successful_stops = 0
    failed_stops = 0
    
    for webhook in webhook_configs:
        channel_id = webhook.get('channel_id')
        resource_id = webhook.get('resource_id')
        calendar_name = webhook.get('calendar_name', 'Unknown')
        
        if not channel_id or not resource_id:
            print(f"⚠️  Incomplete webhook config for {calendar_name}")
            continue
        
        print(f"\n📅 Processing: {calendar_name}")
        
        success = stop_google_webhook_channel(service, channel_id, resource_id)
        if success:
            successful_stops += 1
        else:
            failed_stops += 1
    
    # Results summary
    print(f"\n📊 CLEANUP RESULTS:")
    print(f"✅ Successfully stopped: {successful_stops} channels")
    print(f"❌ Failed to stop: {failed_stops} channels")
    
    return failed_stops == 0


def create_migration_log():
    """
    Create a log file documenting the migration to unidirectional sync.
    """
    print("\n📝 Creating migration log...")
    
    log_entry = {
        "migration_type": "bidirectional_to_unidirectional",
        "migration_date": datetime.now().isoformat(),
        "changes_made": [
            "Stopped all Google Calendar webhook channels",
            "Disabled Google → Monday synchronization",
            "Disabled sync token management",
            "Renamed configuration files with .DISABLED suffix",
            "Removed Google webhook endpoint from app.py",
            "Removed incremental sync functions",
            "Added passive change monitoring system"
        ],
        "files_affected": [
            "app.py - Google webhook endpoint removed",
            "google_calendar_service.py - Incremental sync removed", 
            "sync_logic.py - Google → Monday functions removed",
            "sync_token_manager.py - File deleted",
            "config/sync_tokens.json - File deleted",
            "config/channels/google_channel_map.json - Disabled",
            "config/webhooks/webhooks_personales_info.json - Disabled"
        ],
        "new_files_added": [
            "google_change_monitor.py - Passive change detection",
            "config/channels/GOOGLE_WEBHOOKS_DISABLED.md - Documentation"
        ],
        "system_status": {
            "monday_to_google_sync": "ACTIVE",
            "google_to_monday_sync": "DISABLED", 
            "manual_change_monitoring": "ACTIVE",
            "webhook_channels": "STOPPED"
        }
    }
    
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "unidirectional_migration.json")
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Migration log saved: {log_file}")
        
    except Exception as e:
        print(f"⚠️  Error saving migration log: {e}")


def main():
    """
    Main cleanup function.
    """
    print("🔄 GOOGLE WEBHOOK CLEANUP FOR UNIDIRECTIONAL SYNC")
    print("=" * 60)
    print("This script will:")
    print("1. Stop all Google Calendar webhook channels")
    print("2. Disable webhook configuration files") 
    print("3. Create migration documentation")
    print("=" * 60)
    
    # Confirm with user
    response = input("\nProceed with cleanup? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cleanup cancelled by user")
        return
    
    # Step 1: Stop webhook channels
    print("\n📍 STEP 1: Stopping Google webhook channels...")
    webhook_success = stop_all_webhooks()
    
    # Step 2: Clean up configuration files
    print("\n📍 STEP 2: Cleaning up configuration files...")
    disabled_files = cleanup_webhook_configurations()
    
    # Step 3: Create migration log
    print("\n📍 STEP 3: Creating migration log...")
    create_migration_log()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 MIGRATION TO UNIDIRECTIONAL SYNC COMPLETE!")
    print("=" * 60)
    
    if webhook_success:
        print("✅ All Google webhook channels stopped successfully")
    else:
        print("⚠️  Some webhook channels may still be active")
    
    print(f"✅ Configuration files disabled: {len(disabled_files)}")
    print("✅ Migration log created")
    
    print("\nNEXT STEPS:")
    print("1. Configure Google calendars as read-only for users")
    print("2. Train users that Monday.com is the single source of truth")
    print("3. Use google_change_monitor.py to detect manual changes")
    print("4. Test Monday → Google synchronization")
    
    print(f"\n📋 System is now UNIDIRECTIONAL: Monday → Google only")
    print("📊 Use google_change_monitor.py to monitor for conflicts")


if __name__ == "__main__":
    main()