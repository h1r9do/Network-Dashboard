#!/usr/bin/env python3
"""
Update zero cost circuits in the circuits table using data from master JSON
Only updates non-cell/satellite circuits where provider matches
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
JSON_FILE = "/var/www/html/circuitinfo/master_circuit_data_20250701_150111.json"
BACKUP_FILE = f"/usr/local/bin/Main/circuit_cost_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def get_db_session():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def normalize_provider_name(provider):
    """Normalize provider names for comparison"""
    if not provider or str(provider).lower() == 'nan':
        return ""
    
    provider = str(provider).strip().upper()
    
    # Common normalizations
    replacements = {
        'AT&T BROADBAND II': 'AT&T',
        'CHARTER COMMUNICATIONS': 'SPECTRUM',
        'CHARTER': 'SPECTRUM',
        'COX BUSINESS/BOI': 'COX',
        'VERIZON BUSINESS': 'VERIZON',
        'CENTURYLINK': 'CENTURYLINK'
    }
    
    for old, new in replacements.items():
        if old in provider:
            return new
    
    return provider

def is_cell_or_satellite(speed):
    """Check if speed indicates cell or satellite service"""
    if not speed or str(speed).lower() == 'nan':
        return False
    speed_lower = str(speed).lower()
    return 'cell' in speed_lower or 'satellite' in speed_lower

def main():
    print(f"\n{'='*80}")
    print(f"Update Zero Cost Circuits from Master - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Load master circuit JSON data
    print(f"Loading master circuit data from: {JSON_FILE}")
    with open(JSON_FILE, 'r') as f:
        master_data = json.load(f)
    
    # Create lookup dictionary by store name
    master_lookup = {}
    for record in master_data:
        store = record.get('Store')
        if store:
            master_lookup[store.upper()] = record
    
    print(f"Loaded {len(master_lookup)} stores from master list\n")
    
    session = get_db_session()
    
    try:
        # First, backup current data
        print("Creating backup of current circuit costs...")
        result = session.execute(text("""
            SELECT site_name, circuit_purpose, billing_monthly_cost
            FROM circuits
            WHERE status = 'Enabled'
            ORDER BY site_name, circuit_purpose
        """))
        
        backup_data = []
        for row in result:
            backup_data.append({
                'site_name': row[0],
                'circuit_purpose': row[1],
                'billing_monthly_cost': float(row[2]) if row[2] else 0
            })
        
        with open(BACKUP_FILE, 'w') as f:
            json.dump(backup_data, f, indent=2)
        print(f"✅ Backed up {len(backup_data)} records to: {BACKUP_FILE}\n")
        
        # Find circuits with $0 cost
        print("Finding circuits with $0.00 cost...")
        result = session.execute(text("""
            SELECT site_name, circuit_purpose, provider_name, 
                   details_ordered_service_speed, billing_monthly_cost
            FROM circuits
            WHERE status = 'Enabled'
            AND (billing_monthly_cost = 0 OR billing_monthly_cost IS NULL)
            ORDER BY site_name, circuit_purpose
        """))
        
        zero_cost_circuits = []
        for row in result:
            # Skip cell/satellite circuits
            if not is_cell_or_satellite(row[3]):
                zero_cost_circuits.append({
                    'site_name': row[0],
                    'circuit_purpose': row[1],
                    'provider_name': row[2],
                    'speed': row[3],
                    'current_cost': row[4] or 0
                })
        
        print(f"Found {len(zero_cost_circuits)} non-cell/satellite circuits with $0.00 cost\n")
        
        # Update circuits where we find matching data
        updated_count = 0
        
        for circuit in zero_cost_circuits:
            site_name = circuit['site_name'].upper() if circuit['site_name'] else ''
            
            if site_name in master_lookup:
                master = master_lookup[site_name]
                
                # Normalize provider names
                circuit_provider = normalize_provider_name(circuit['provider_name'])
                
                # Check if primary or secondary
                is_primary = 'primary' in (circuit['circuit_purpose'] or '').lower()
                
                if is_primary:
                    master_provider = normalize_provider_name(master.get('Active A Circuit Carrier'))
                    master_cost = master.get('MRC')
                else:
                    master_provider = normalize_provider_name(master.get('Active B Circuit Carrier'))
                    master_cost = master.get('MRC3')
                
                # Update if providers match and we have a non-zero cost
                if (circuit_provider == master_provider and 
                    master_cost and master_cost != 0):
                    
                    print(f"Updating {circuit['site_name']} {circuit['circuit_purpose']}: "
                          f"${circuit['current_cost']:.2f} → ${master_cost:.2f}")
                    
                    session.execute(text("""
                        UPDATE circuits
                        SET billing_monthly_cost = :cost,
                            date_record_updated = CURRENT_TIMESTAMP
                        WHERE site_name = :site_name
                        AND circuit_purpose = :purpose
                        AND status = 'Enabled'
                    """), {
                        'cost': master_cost,
                        'site_name': circuit['site_name'],
                        'purpose': circuit['circuit_purpose']
                    })
                    
                    updated_count += 1
        
        # Commit changes
        session.commit()
        
        print(f"\n{'='*80}")
        print(f"Summary: Updated {updated_count} circuits with cost data from master list")
        print(f"Backup saved to: {BACKUP_FILE}")
        print(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)