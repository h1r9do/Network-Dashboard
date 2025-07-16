#!/usr/bin/env python3
"""
Backup new_stores table and import missing data from Excel
WITHOUT overwriting existing TOD and project_status
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
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

def backup_table(cursor, conn):
    """Create a backup of the new_stores table"""
    backup_table_name = f"new_stores_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"Creating backup table: {backup_table_name}")
    
    # Create backup table with same structure
    cursor.execute(f"""
        CREATE TABLE {backup_table_name} AS 
        SELECT * FROM new_stores
    """)
    
    # Copy indexes
    cursor.execute(f"""
        CREATE INDEX ON {backup_table_name} (site_name);
        CREATE INDEX ON {backup_table_name} (is_active);
    """)
    
    conn.commit()
    
    # Get count
    cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
    count = cursor.fetchone()[0]
    
    print(f"✓ Backup created with {count} records")
    return backup_table_name

def compare_data(cursor):
    """Compare current database data with Excel data"""
    print("\nComparing current database with Excel file...")
    
    # Read Excel file
    excel_path = "/var/www/html/meraki-data/RE - Targeted Opening Dates - 20250702.xlsx"
    df = pd.read_excel(excel_path, skiprows=3)
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)
    
    # Get current database data
    cursor.execute("""
        SELECT site_name, sap_number, dba, address, city, state, zip, 
               region, project_status, target_opening_date, store_concept, unit_capacity
        FROM new_stores
        WHERE is_active = true
        ORDER BY site_name
    """)
    
    db_data = {}
    for row in cursor.fetchall():
        site_name = row[0]
        db_data[site_name] = {
            'sap_number': row[1],
            'dba': row[2],
            'address': row[3],
            'city': row[4],
            'state': row[5],
            'zip': row[6],
            'region': row[7],
            'project_status': row[8],
            'target_opening_date': row[9],
            'store_concept': row[10],
            'unit_capacity': row[11]
        }
    
    # Compare and show what will be updated
    updates_needed = []
    
    print("\nStores that will be updated:")
    print("-" * 100)
    print(f"{'Store':<10} {'Field':<20} {'Current DB Value':<30} {'Excel Value':<30}")
    print("-" * 100)
    
    for _, excel_row in df.iterrows():
        store_num = str(excel_row['Store #']).strip().upper()
        
        if store_num in db_data:
            db_row = db_data[store_num]
            store_updates = {'site_name': store_num}
            has_updates = False
            
            # Check each field (except TOD and project_status)
            fields_to_check = [
                ('sap_number', 'SAP #'),
                ('dba', 'DBA'),
                ('address', 'Address'),
                ('city', 'City'),
                ('state', 'State'),
                ('zip', 'Zip'),
                ('region', 'Region'),
                ('store_concept', 'Store Concept'),
                ('unit_capacity', 'Unit Capacity')
            ]
            
            for db_field, excel_field in fields_to_check:
                db_value = db_row[db_field]
                excel_value = excel_row[excel_field] if pd.notna(excel_row[excel_field]) else None
                
                # Convert to string for comparison
                if excel_value is not None:
                    excel_value = str(excel_value).strip()
                    if excel_value.lower() in ['nan', 'none', '']:
                        excel_value = None
                
                # Only update if DB value is empty/null and Excel has data
                if (db_value is None or db_value == '') and excel_value:
                    print(f"{store_num:<10} {db_field:<20} {str(db_value):<30} {str(excel_value):<30}")
                    store_updates[db_field] = excel_value
                    has_updates = True
            
            if has_updates:
                updates_needed.append(store_updates)
    
    print(f"\nTotal stores in DB: {len(db_data)}")
    print(f"Total stores in Excel: {len(df)}")
    print(f"Stores needing updates: {len(updates_needed)}")
    
    # Show stores in Excel but not in DB
    excel_stores = set(str(row['Store #']).strip().upper() for _, row in df.iterrows())
    db_stores = set(db_data.keys())
    new_stores = excel_stores - db_stores
    
    if new_stores:
        print(f"\nStores in Excel but NOT in database ({len(new_stores)}):")
        for store in sorted(new_stores):
            print(f"  - {store}")
    
    return updates_needed, df

def apply_updates(cursor, conn, updates_needed):
    """Apply the updates to the database"""
    if not updates_needed:
        print("\nNo updates needed!")
        return
    
    print(f"\nApplying {len(updates_needed)} updates...")
    
    for update in updates_needed:
        site_name = update.pop('site_name')
        
        # Build UPDATE query
        set_clauses = []
        values = []
        
        for field, value in update.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)
        
        if set_clauses:
            values.append(datetime.utcnow())  # updated_at
            values.append(site_name)  # WHERE clause
            
            query = f"""
                UPDATE new_stores 
                SET {', '.join(set_clauses)}, updated_at = %s
                WHERE site_name = %s
            """
            
            cursor.execute(query, values)
    
    conn.commit()
    print(f"✓ Successfully updated {len(updates_needed)} stores")

def main():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Step 1: Backup the table
        backup_table_name = backup_table(cursor, conn)
        
        # Step 2: Compare data
        updates_needed, excel_df = compare_data(cursor)
        
        # Step 3: Apply updates automatically (we have backup)
        if updates_needed:
            print("\n" + "="*50)
            print("Applying updates (backup already created)...")
            
            apply_updates(cursor, conn, updates_needed)
            
            # Verify updates
            print("\nVerifying updates...")
            cursor.execute("""
                SELECT COUNT(*) FROM new_stores 
                WHERE sap_number IS NOT NULL 
                OR dba IS NOT NULL 
                OR address IS NOT NULL
            """)
            count = cursor.fetchone()[0]
            print(f"✓ {count} stores now have additional data")
        else:
            print("\nNo updates needed - all fields are already populated or Excel doesn't have additional data.")
        
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