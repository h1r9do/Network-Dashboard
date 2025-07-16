#!/usr/bin/env python3
"""
Update $0.00 costs in enriched_circuits table from master JSON
where providers match and it's not a cell/satellite circuit
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

def get_db_session():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def normalize_provider(provider):
    """Normalize provider names for matching"""
    if not provider or str(provider).strip() == '':
        return ''
    
    p = str(provider).upper().strip()
    
    # Map variations to standard names
    mappings = {
        'SPECTRUM': ['CHARTER', 'CHARTER COMMUNICATIONS'],
        'AT&T': ['AT&T BROADBAND II', 'ATT'],
        'COX': ['COX BUSINESS', 'COX COMMUNICATIONS', 'COX BUSINESS/BOI'],
        'VERIZON': ['VERIZON BUSINESS', 'VZ', 'VZG'],
        'COMCAST': ['COMCAST WORKPLACE'],
        'CENTURYLINK': ['CLINK', 'LUMEN', 'LEVEL 3', 'BRIGHTSPEED'],
        'DIGI': ['DIGI', 'VZW CELL', 'VERIZON WIRELESS']
    }
    
    for standard, variations in mappings.items():
        for var in variations:
            if var in p:
                return standard
    
    return p

def is_cell_satellite(speed):
    """Check if this is a cell or satellite service"""
    if not speed:
        return False
    s = str(speed).lower()
    return 'cell' in s or 'satellite' in s

def main():
    print(f"\n{'='*80}")
    print(f"Update Enriched Costs from Master JSON - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Load master JSON
    print("Loading master circuit data...")
    with open(JSON_FILE, 'r') as f:
        master_data = json.load(f)
    
    # Build lookup by store
    master_lookup = {}
    for record in master_data:
        store = record.get('Store')
        if store:
            master_lookup[store.upper()] = record
    
    print(f"Loaded {len(master_lookup)} stores from master list\n")
    
    session = get_db_session()
    
    try:
        # Find all enriched circuits with $0.00 costs
        print("Finding enriched circuits with $0.00 costs...")
        result = session.execute(text("""
            SELECT network_name, 
                   wan1_provider, wan1_speed, wan1_monthly_cost,
                   wan2_provider, wan2_speed, wan2_monthly_cost
            FROM enriched_circuits
            WHERE wan1_monthly_cost = '$0.00' OR wan2_monthly_cost = '$0.00'
            ORDER BY network_name
        """))
        
        circuits_to_check = []
        for row in result:
            circuits_to_check.append({
                'network_name': row[0],
                'wan1_provider': row[1],
                'wan1_speed': row[2],
                'wan1_cost': row[3],
                'wan2_provider': row[4],
                'wan2_speed': row[5],
                'wan2_cost': row[6]
            })
        
        print(f"Found {len(circuits_to_check)} circuits with $0.00 costs\n")
        
        # Update matching circuits
        updated_count = 0
        wan1_updates = 0
        wan2_updates = 0
        
        for circuit in circuits_to_check:
            site = circuit['network_name'].upper() if circuit['network_name'] else ''
            
            if site not in master_lookup:
                continue
            
            master = master_lookup[site]
            updates_needed = {}
            
            # Check WAN1
            if circuit['wan1_cost'] == '$0.00' and not is_cell_satellite(circuit['wan1_speed']):
                circuit_provider = normalize_provider(circuit['wan1_provider'])
                master_provider = normalize_provider(master.get('Active A Circuit Carrier', ''))
                master_cost = master.get('MRC')
                
                if circuit_provider == master_provider and master_cost and master_cost > 0:
                    updates_needed['wan1_monthly_cost'] = f'${float(master_cost):.2f}'
                    wan1_updates += 1
            
            # Check WAN2
            if circuit['wan2_cost'] == '$0.00' and not is_cell_satellite(circuit['wan2_speed']):
                circuit_provider = normalize_provider(circuit['wan2_provider'])
                master_provider = normalize_provider(master.get('Active B Circuit Carrier', ''))
                master_cost = master.get('MRC3')
                
                if circuit_provider == master_provider and master_cost and master_cost > 0:
                    updates_needed['wan2_monthly_cost'] = f'${float(master_cost):.2f}'
                    wan2_updates += 1
            
            # Apply updates
            if updates_needed:
                set_clause = ', '.join([f"{k} = :{k}" for k in updates_needed.keys()])
                sql = f"""
                    UPDATE enriched_circuits
                    SET {set_clause}, last_updated = CURRENT_TIMESTAMP
                    WHERE network_name = :network_name
                """
                
                params = {'network_name': circuit['network_name']}
                params.update(updates_needed)
                
                session.execute(text(sql), params)
                updated_count += 1
                
                print(f"Updated {circuit['network_name']}:")
                for field, value in updates_needed.items():
                    print(f"  {field}: $0.00 → {value}")
        
        session.commit()
        
        print(f"\n{'='*80}")
        print(f"Summary:")
        print(f"  Sites updated: {updated_count}")
        print(f"  WAN1 costs updated: {wan1_updates}")
        print(f"  WAN2 costs updated: {wan2_updates}")
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