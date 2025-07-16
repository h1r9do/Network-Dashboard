#!/usr/bin/env python3
"""
Reimport ALL DSR cost data from circuits table to enriched_circuits table
Creates a backup first for easy rollback if needed
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Database configuration
DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
BACKUP_FILE = f"/usr/local/bin/Main/cost_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def normalize_cost(cost):
    """Normalize cost to currency format"""
    if not cost or cost == 'nan' or cost is None:
        return '$0.00'
    
    try:
        cost_float = float(cost)
        return f'${cost_float:.2f}'
    except:
        return '$0.00'

def backup_current_costs(session):
    """Backup current cost data from enriched_circuits"""
    print("\n📦 Creating backup of current cost data...")
    
    result = session.execute(text("""
        SELECT network_name, wan1_monthly_cost, wan2_monthly_cost
        FROM enriched_circuits
        ORDER BY network_name
    """))
    
    backup_data = []
    for row in result:
        backup_data.append({
            'network_name': row[0],
            'wan1_monthly_cost': row[1],
            'wan2_monthly_cost': row[2]
        })
    
    with open(BACKUP_FILE, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Backed up {len(backup_data)} records to: {BACKUP_FILE}")
    return len(backup_data)

def restore_from_backup():
    """Restore cost data from backup file"""
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
                SET wan1_monthly_cost = :wan1_cost,
                    wan2_monthly_cost = :wan2_cost,
                    last_updated = CURRENT_TIMESTAMP
                WHERE network_name = :network_name
            """), {
                'network_name': record['network_name'],
                'wan1_cost': record['wan1_monthly_cost'] or '$0.00',
                'wan2_cost': record['wan2_monthly_cost'] or '$0.00'
            })
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

def reimport_all_costs():
    """Reimport all DSR costs from circuits table"""
    session = get_db_session()
    
    try:
        # First, create backup
        backup_count = backup_current_costs(session)
        
        print("\n🔄 Starting DSR cost reimport...")
        
        # Get all unique sites from enriched_circuits
        result = session.execute(text("""
            SELECT DISTINCT network_name
            FROM enriched_circuits
            ORDER BY network_name
        """))
        
        sites = [row[0] for row in result]
        print(f"Found {len(sites)} sites to process")
        
        updated_count = 0
        zero_cost_count = 0
        no_dsr_count = 0
        
        for site_name in sites:
            # Get cost data from circuits table (DSR source)
            result = session.execute(text("""
                SELECT circuit_purpose, billing_monthly_cost
                FROM circuits
                WHERE LOWER(site_name) = LOWER(:site_name) 
                AND status = 'Enabled'
                ORDER BY circuit_purpose
            """), {'site_name': site_name})
            
            dsr_costs = {}
            for row in result:
                purpose = row[0]
                cost = row[1]
                if purpose:
                    purpose_lower = purpose.lower()
                    if 'primary' in purpose_lower:
                        dsr_costs['wan1'] = normalize_cost(cost)
                    elif 'secondary' in purpose_lower or 'backup' in purpose_lower:
                        dsr_costs['wan2'] = normalize_cost(cost)
            
            if not dsr_costs:
                no_dsr_count += 1
                # Still update to $0.00 if no DSR data
                session.execute(text("""
                    UPDATE enriched_circuits
                    SET wan1_monthly_cost = '$0.00',
                        wan2_monthly_cost = '$0.00',
                        last_updated = CURRENT_TIMESTAMP
                    WHERE LOWER(network_name) = LOWER(:site_name)
                """), {'site_name': site_name})
                continue
            
            # Update enriched_circuits with DSR costs
            update_params = {'site_name': site_name}
            update_parts = []
            
            # Always set both costs, using $0.00 if not found in DSR
            wan1_cost = dsr_costs.get('wan1', '$0.00')
            wan2_cost = dsr_costs.get('wan2', '$0.00')
            
            update_parts.append("wan1_monthly_cost = :wan1_cost")
            update_parts.append("wan2_monthly_cost = :wan2_cost")
            update_params['wan1_cost'] = wan1_cost
            update_params['wan2_cost'] = wan2_cost
            
            if wan1_cost == '$0.00' and wan2_cost == '$0.00':
                zero_cost_count += 1
            
            update_sql = f"""
                UPDATE enriched_circuits
                SET {', '.join(update_parts)},
                    last_updated = CURRENT_TIMESTAMP
                WHERE LOWER(network_name) = LOWER(:site_name)
            """
            
            session.execute(text(update_sql), update_params)
            updated_count += 1
            
            if updated_count % 100 == 0:
                print(f"  Processed {updated_count} sites...")
        
        # Commit all changes
        session.commit()
        
        print(f"\n{'='*80}")
        print(f"Reimport Summary:")
        print(f"  Total sites processed: {len(sites)}")
        print(f"  Sites updated: {updated_count}")
        print(f"  Sites with no DSR data: {no_dsr_count}")
        print(f"  Sites with $0.00 costs: {zero_cost_count}")
        print(f"  Backup saved to: {BACKUP_FILE}")
        print(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error during reimport: {e}")
        import traceback
        traceback.print_exc()
        
        # Ask if user wants to restore from backup
        response = input("\nDo you want to restore from backup? (y/n): ")
        if response.lower() == 'y':
            restore_from_backup()
        
        return False
    finally:
        session.close()

def main():
    print(f"\n{'='*80}")
    print(f"DSR Cost Data Full Reimport - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # Check if running with --restore flag
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        # Find most recent backup
        import glob
        backups = sorted(glob.glob("/usr/local/bin/Main/cost_backup_*.json"))
        if backups:
            global BACKUP_FILE
            BACKUP_FILE = backups[-1]  # Most recent
            return restore_from_backup()
        else:
            print("❌ No backup files found")
            return False
    
    # Normal reimport
    return reimport_all_costs()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)