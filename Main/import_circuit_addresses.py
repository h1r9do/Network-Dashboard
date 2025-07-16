#!/usr/bin/env python3
"""
Import address data from store list CSV into circuits table
Only updates empty address fields - does not overwrite existing data
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
import re

def get_db_connection():
    """Get database connection using config"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def analyze_data(df, cursor):
    """Analyze what data is available and what needs updating"""
    print("Analyzing store list data...")
    print(f"Total stores in CSV: {len(df)}")
    
    # Get unique store numbers from CSV
    csv_stores = set(df['storeNumber'].unique())
    
    # Get circuits with missing address data
    cursor.execute("""
        SELECT DISTINCT site_name, address_1, city, state, zipcode
        FROM circuits
        WHERE (address_1 IS NULL OR city IS NULL OR state IS NULL OR zipcode IS NULL)
        AND site_name IS NOT NULL
        ORDER BY site_name
    """)
    
    circuits_needing_addresses = cursor.fetchall()
    print(f"\nCircuits with missing address data: {len(circuits_needing_addresses)}")
    
    # Check how many can be matched
    can_be_updated = 0
    cannot_match = []
    
    for circuit in circuits_needing_addresses:
        site_name = circuit[0]
        if site_name in csv_stores:
            can_be_updated += 1
        else:
            cannot_match.append(site_name)
    
    print(f"Can be updated from CSV: {can_be_updated}")
    print(f"Cannot match to CSV: {len(cannot_match)}")
    
    if cannot_match and len(cannot_match) <= 20:
        print("\nSites not found in store list:")
        for site in sorted(cannot_match)[:20]:
            print(f"  - {site}")
        if len(cannot_match) > 20:
            print(f"  ... and {len(cannot_match) - 20} more")
    
    return circuits_needing_addresses

def import_addresses(df, cursor, conn):
    """Import address data into circuits table"""
    
    # Create a dictionary for quick lookup
    store_data = {}
    for _, row in df.iterrows():
        store_num = row['storeNumber']
        store_data[store_num] = {
            'address': row['address'] if pd.notna(row['address']) else None,
            'city': row['city'] if pd.notna(row['city']) else None,
            'state': row['stateProvince'] if pd.notna(row['stateProvince']) else None,
            'zip': row['zipPostalCode'] if pd.notna(row['zipPostalCode']) else None
        }
    
    # Get circuits that need updates
    cursor.execute("""
        SELECT id, site_name, address_1, city, state, zipcode
        FROM circuits
        WHERE site_name IS NOT NULL
        ORDER BY site_name
    """)
    
    circuits = cursor.fetchall()
    updates = []
    
    for circuit in circuits:
        circuit_id, site_name, curr_addr, curr_city, curr_state, curr_zip = circuit
        
        if site_name in store_data:
            store_info = store_data[site_name]
            
            # Only update if current value is NULL and store has data
            update_fields = []
            update_values = []
            
            if curr_addr is None and store_info['address']:
                update_fields.append('address_1 = %s')
                update_values.append(store_info['address'])
            
            if curr_city is None and store_info['city']:
                update_fields.append('city = %s')
                update_values.append(store_info['city'])
            
            if curr_state is None and store_info['state']:
                update_fields.append('state = %s')
                update_values.append(store_info['state'])
            
            if curr_zip is None and store_info['zip']:
                update_fields.append('zipcode = %s')
                update_values.append(store_info['zip'])
            
            if update_fields:
                update_values.extend([datetime.utcnow(), circuit_id])
                updates.append((update_fields, update_values, site_name))
    
    # Apply updates
    if updates:
        print(f"\nApplying {len(updates)} updates...")
        
        for update_fields, update_values, site_name in updates:
            query = f"""
                UPDATE circuits 
                SET {', '.join(update_fields)}, updated_at = %s
                WHERE id = %s
            """
            cursor.execute(query, update_values)
            
            if len(updates) <= 10:  # Show details for small updates
                print(f"  Updated {site_name}: {len(update_fields)} fields")
        
        conn.commit()
        print(f"✓ Successfully updated {len(updates)} circuits with address data")
    else:
        print("\nNo updates needed - all matching circuits already have address data")
    
    # Verify the update
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(address_1) as has_address,
               COUNT(city) as has_city,
               COUNT(state) as has_state,
               COUNT(zipcode) as has_zip
        FROM circuits
    """)
    
    result = cursor.fetchone()
    print(f"\nFinal circuit address statistics:")
    print(f"Total circuits: {result[0]}")
    print(f"With address: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"With city: {result[2]} ({result[2]/result[0]*100:.1f}%)")
    print(f"With state: {result[3]} ({result[3]/result[0]*100:.1f}%)")
    print(f"With ZIP: {result[4]} ({result[4]/result[0]*100:.1f}%)")

def main():
    try:
        # Read the store list CSV
        csv_path = "/var/www/html/meraki-data/store-list (4).csv"
        print(f"Reading store list from: {csv_path}")
        df = pd.read_csv(csv_path)
        
        # Filter to only stores (not offices or other types)
        df_stores = df[df['buildingType'] == 'Store'].copy()
        print(f"Found {len(df_stores)} stores (excluding offices and other building types)")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Analyze what needs updating
        circuits_needing_addresses = analyze_data(df_stores, cursor)
        
        if len(circuits_needing_addresses) > 0:
            # Confirm before proceeding
            print("\n" + "="*60)
            print("Ready to import address data for circuits with missing addresses.")
            print("This will ONLY update NULL/empty address fields.")
            print("Existing address data will NOT be overwritten.")
            print("="*60)
            
            # Proceed with import
            import_addresses(df_stores, cursor, conn)
        else:
            print("\nAll circuits already have complete address data!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())