#!/usr/bin/env python3
"""
Fix missing imports by properly matching site_name to Store #
"""
import pandas as pd
import psycopg2
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

def main():
    print("Fixing missing imports by matching site_name to Store #...")
    
    # Read Excel file
    excel_path = "/var/www/html/meraki-data/RE - Targeted Opening Dates - 20250702.xlsx"
    df = pd.read_excel(excel_path, skiprows=3)
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)
    
    # Create a dictionary of Store # -> row data
    excel_data = {}
    for _, row in df.iterrows():
        store_num = str(row['Store #']).strip().upper()
        if pd.notna(row['Store #']) and store_num:
            excel_data[store_num] = row
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all stores that have missing data
    cursor.execute("""
        SELECT site_name, sap_number, dba, address, zip, store_concept, unit_capacity
        FROM new_stores 
        WHERE is_active = true 
        AND (sap_number IS NULL OR dba IS NULL OR address IS NULL OR zip IS NULL 
             OR store_concept IS NULL OR unit_capacity IS NULL)
        ORDER BY site_name
    """)
    
    stores_to_update = cursor.fetchall()
    print(f"\nFound {len(stores_to_update)} stores with missing data")
    
    updates_made = 0
    not_found_in_excel = []
    
    for store in stores_to_update:
        site_name = store[0]
        
        if site_name in excel_data:
            excel_row = excel_data[site_name]
            updates = []
            values = []
            
            # Check each field and update if missing
            if store[1] is None and pd.notna(excel_row.get('SAP #')):
                sap = str(excel_row['SAP #']).strip()
                if sap and sap != '0':  # Don't import 0 as SAP number
                    updates.append("sap_number = %s")
                    values.append(sap)
            
            if store[2] is None and pd.notna(excel_row.get('DBA')):
                dba = str(excel_row['DBA']).strip()
                if dba:
                    updates.append("dba = %s")
                    values.append(dba)
            
            if store[3] is None and pd.notna(excel_row.get('Address')):
                address = str(excel_row['Address']).strip()
                if address:
                    updates.append("address = %s")
                    values.append(address)
            
            if store[4] is None and pd.notna(excel_row.get('Zip')):
                zip_code = str(excel_row['Zip']).strip()
                if zip_code:
                    updates.append("zip = %s")
                    values.append(zip_code)
            
            if store[5] is None and pd.notna(excel_row.get('Store Concept')):
                concept = str(excel_row['Store Concept']).strip()
                if concept:
                    updates.append("store_concept = %s")
                    values.append(concept)
            
            if store[6] is None and pd.notna(excel_row.get('Unit Capacity')):
                capacity = str(excel_row['Unit Capacity']).strip()
                if capacity:
                    updates.append("unit_capacity = %s")
                    values.append(capacity)
            
            if updates:
                values.append(datetime.utcnow())  # updated_at
                values.append(site_name)  # WHERE clause
                
                query = f"""
                    UPDATE new_stores 
                    SET {', '.join(updates)}, updated_at = %s
                    WHERE site_name = %s
                """
                
                cursor.execute(query, values)
                updates_made += 1
                print(f"Updated {site_name}: {len(updates)} fields")
        else:
            not_found_in_excel.append(site_name)
    
    if not_found_in_excel:
        print(f"\nStores not found in Excel ({len(not_found_in_excel)}):")
        for store in not_found_in_excel:
            print(f"  - {store}")
    
    conn.commit()
    print(f"\n✓ Successfully updated {updates_made} stores")
    
    # Verify the update
    cursor.execute("""
        SELECT COUNT(*) as total, 
               COUNT(sap_number) as has_sap, 
               COUNT(dba) as has_dba, 
               COUNT(address) as has_address, 
               COUNT(zip) as has_zip, 
               COUNT(store_concept) as has_concept, 
               COUNT(unit_capacity) as has_capacity 
        FROM new_stores 
        WHERE is_active = true
    """)
    
    result = cursor.fetchone()
    print("\nFinal counts:")
    print(f"Total active stores: {result[0]}")
    print(f"With SAP number: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"With DBA: {result[2]} ({result[2]/result[0]*100:.1f}%)")
    print(f"With Address: {result[3]} ({result[3]/result[0]*100:.1f}%)")
    print(f"With ZIP: {result[4]} ({result[4]/result[0]*100:.1f}%)")
    print(f"With Store Concept: {result[5]} ({result[5]/result[0]*100:.1f}%)")
    print(f"With Unit Capacity: {result[6]} ({result[6]/result[0]*100:.1f}%)")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()