#!/usr/bin/env python3
"""
Find and fix provider mismatches between enriched_circuits and ARIN data
Creates backup for easy rollback
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
BACKUP_FILE = f"/usr/local/bin/Main/provider_mismatch_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def get_db_session():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def normalize_provider(provider):
    """Normalize provider names for comparison"""
    if not provider:
        return ''
    
    p = str(provider).upper().strip()
    
    # Skip cell/private/unknown
    if any(x in p for x in ['CELL', 'PRIVATE', 'UNKNOWN', 'N/A']):
        return p
    
    # Normalize common variations
    mappings = {
        'AT&T': ['AT&T BROADBAND', 'ATT ', 'AT&T ENTERPRISES'],
        'SPECTRUM': ['CHARTER', 'SPECTRUM'],
        'COMCAST': ['COMCAST'],
        'VERIZON': ['VERIZON BUSINESS', 'VERIZON FIOS'],
        'COX': ['COX COMMUNICATIONS', 'COX BUSINESS'],
        'CENTURYLINK': ['CENTURYLINK', 'LEVEL 3', 'LUMEN', 'QWEST'],
        'FRONTIER': ['FRONTIER'],
        'ALTICE': ['ALTICE', 'OPTIMUM', 'SUDDENLINK'],
        'WINDSTREAM': ['WINDSTREAM']
    }
    
    for standard, patterns in mappings.items():
        for pattern in patterns:
            if pattern in p:
                return standard
    
    return p

def backup_current_data(session):
    """Backup current enriched_circuits data"""
    print("📦 Creating backup...")
    
    result = session.execute(text("""
        SELECT network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed
        FROM enriched_circuits
        ORDER BY network_name
    """))
    
    backup_data = []
    for row in result:
        backup_data.append({
            'network_name': row[0],
            'wan1_provider': row[1],
            'wan1_speed': row[2],
            'wan2_provider': row[3],
            'wan2_speed': row[4]
        })
    
    with open(BACKUP_FILE, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Backed up {len(backup_data)} records to: {BACKUP_FILE}")
    return len(backup_data)

def restore_from_backup():
    """Restore from backup file"""
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file not found: {BACKUP_FILE}")
        return False
    
    print(f"\n🔄 Restoring from backup: {BACKUP_FILE}")
    
    session = get_db_session()
    try:
        with open(BACKUP_FILE, 'r') as f:
            backup_data = json.load(f)
        
        restored_count = 0
        for record in backup_data:
            session.execute(text("""
                UPDATE enriched_circuits
                SET wan1_provider = :wan1_provider,
                    wan1_speed = :wan1_speed,
                    wan2_provider = :wan2_provider,
                    wan2_speed = :wan2_speed,
                    last_updated = CURRENT_TIMESTAMP
                WHERE network_name = :network_name
            """), record)
            restored_count += 1
        
        session.commit()
        print(f"✅ Restored {restored_count} records from backup")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error restoring from backup: {e}")
        return False
    finally:
        session.close()

def find_and_fix_mismatches():
    """Find and fix provider mismatches"""
    session = get_db_session()
    
    try:
        # First create backup
        backup_current_data(session)
        
        print("\n🔍 Finding provider mismatches between enriched_circuits and ARIN data...")
        
        # Find mismatches
        result = session.execute(text("""
            SELECT 
                ec.network_name,
                ec.wan1_provider as ec_wan1_provider,
                ec.wan1_speed as ec_wan1_speed,
                mi.wan1_arin_provider as arin_wan1_provider,
                mi.wan1_provider_label as meraki_wan1_label,
                ec.wan2_provider as ec_wan2_provider,
                ec.wan2_speed as ec_wan2_speed,
                mi.wan2_arin_provider as arin_wan2_provider,
                mi.wan2_provider_label as meraki_wan2_label
            FROM enriched_circuits ec
            JOIN meraki_inventory mi ON ec.network_name = mi.network_name
            WHERE mi.device_model LIKE 'MX%'
            ORDER BY ec.network_name
        """))
        
        mismatches = []
        for row in result:
            wan1_mismatch = False
            wan2_mismatch = False
            
            # Check WAN1
            if row[3] and row[3] not in ['Private IP', 'Unknown']:  # ARIN WAN1 exists
                ec_norm = normalize_provider(row[1])
                arin_norm = normalize_provider(row[3])
                if ec_norm != arin_norm and arin_norm not in ['PRIVATE IP', 'UNKNOWN']:
                    wan1_mismatch = True
            
            # Check WAN2
            if row[7] and row[7] not in ['Private IP', 'Unknown']:  # ARIN WAN2 exists
                ec_norm = normalize_provider(row[5])
                arin_norm = normalize_provider(row[7])
                if ec_norm != arin_norm and arin_norm not in ['PRIVATE IP', 'UNKNOWN']:
                    wan2_mismatch = True
            
            if wan1_mismatch or wan2_mismatch:
                mismatches.append({
                    'network_name': row[0],
                    'wan1_mismatch': wan1_mismatch,
                    'ec_wan1': row[1],
                    'arin_wan1': row[3],
                    'label_wan1': row[4],
                    'wan2_mismatch': wan2_mismatch,
                    'ec_wan2': row[5],
                    'arin_wan2': row[7],
                    'label_wan2': row[8]
                })
        
        print(f"\n📊 Found {len(mismatches)} sites with provider mismatches\n")
        
        if not mismatches:
            print("No mismatches found!")
            return True
        
        # Show first 10 mismatches
        print("First 10 mismatches:")
        for i, m in enumerate(mismatches[:10]):
            print(f"\n{m['network_name']}:")
            if m['wan1_mismatch']:
                print(f"  WAN1: EC='{m['ec_wan1']}' vs ARIN='{m['arin_wan1']}'")
            if m['wan2_mismatch']:
                print(f"  WAN2: EC='{m['ec_wan2']}' vs ARIN='{m['arin_wan2']}'")
        
        if len(mismatches) > 10:
            print(f"\n... and {len(mismatches) - 10} more")
        
        # For non-interactive mode, just show what would be fixed
        print(f"\n📋 To fix these mismatches, run with --fix flag")
        print(f"📋 To restore from backup, run with --restore flag")
        
        # Check if --fix flag was provided
        if len(sys.argv) > 1 and sys.argv[1] == '--fix':
            print("\n✅ Fix mode enabled, proceeding...")
        else:
            print("\n❌ Exiting without changes (use --fix to apply)")
            return True
        
        # Apply fixes
        print("\n🔧 Applying fixes...")
        fixed_count = 0
        
        for m in mismatches:
            updates = {}
            
            if m['wan1_mismatch'] and m['arin_wan1']:
                updates['wan1_provider'] = m['arin_wan1']
                # Also update from label if available
                if m['label_wan1']:
                    updates['wan1_provider'] = m['label_wan1']
            
            if m['wan2_mismatch'] and m['arin_wan2']:
                updates['wan2_provider'] = m['arin_wan2']
                # Also update from label if available
                if m['label_wan2']:
                    updates['wan2_provider'] = m['label_wan2']
            
            if updates:
                set_clause = ', '.join([f"{k} = :{k}" for k in updates.keys()])
                sql = f"""
                    UPDATE enriched_circuits
                    SET {set_clause}, last_updated = CURRENT_TIMESTAMP
                    WHERE network_name = :network_name
                """
                
                params = {'network_name': m['network_name']}
                params.update(updates)
                
                session.execute(text(sql), params)
                fixed_count += 1
                
                if fixed_count % 50 == 0:
                    print(f"  Fixed {fixed_count} sites...")
        
        session.commit()
        
        print(f"\n✅ Fixed {fixed_count} sites")
        print(f"📄 Backup saved to: {BACKUP_FILE}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        response = input("\nDo you want to restore from backup? (y/n): ")
        if response.lower() == 'y':
            restore_from_backup()
        
        return False
    finally:
        session.close()

def main():
    print(f"\n{'='*80}")
    print(f"Provider Mismatch Fix - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # Check if running with --restore flag
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        return restore_from_backup()
    
    return find_and_fix_mismatches()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)