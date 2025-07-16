#!/usr/bin/env python3
"""
Compare Excel data with current database schema and suggest changes
"""
import pandas as pd
import psycopg2
import sys
import os
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
    print("Comparing Excel columns with database schema...\n")
    
    # Read Excel file
    excel_path = "/var/www/html/meraki-data/RE - Targeted Opening Dates - 20250702.xlsx"
    df = pd.read_excel(excel_path, skiprows=3)
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)
    
    # Get database schema
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'new_stores'
        ORDER BY ordinal_position
    """)
    
    db_columns = cursor.fetchall()
    db_column_names = [col[0] for col in db_columns]
    
    print("CURRENT DATABASE COLUMNS:")
    print("-" * 50)
    for col_name, data_type, max_len in db_columns:
        print(f"  {col_name:<30} {data_type}({max_len})" if max_len else f"  {col_name:<30} {data_type}")
    
    print("\n\nEXCEL COLUMNS vs DATABASE MAPPING:")
    print("-" * 80)
    print(f"{'Excel Column':<20} {'DB Column':<25} {'Status':<15} {'Notes':<20}")
    print("-" * 80)
    
    # Map Excel columns to database columns
    mapping = {
        'Store #': 'site_name',
        'SAP #': 'sap_number',
        'DBA': 'dba',
        'Region': 'region',
        'Address': 'address', 
        'City': 'city',
        'State': 'state',
        'Zip': 'zip',
        'Project Status': 'project_status',
        'TOD': 'target_opening_date',
        'Store Concept': 'store_concept',
        'Unit Capacity': 'unit_capacity'
    }
    
    for excel_col in df.columns:
        db_col = mapping.get(excel_col, '')
        if db_col in db_column_names:
            if db_col == 'site_name' and excel_col == 'Store #':
                status = "✓ Exists"
                note = "Already mapped"
            else:
                status = "✓ Exists"
                note = "Ready to populate"
        else:
            status = "✗ Missing"
            note = "Not mapped"
        
        print(f"{excel_col:<20} {db_col:<25} {status:<15} {note:<20}")
    
    print("\n\nRECOMMENDED ACTIONS:")
    print("-" * 50)
    print("1. Remove the extra columns I just added (except sap_number)")
    print("   - store_number (redundant with site_name)")
    print("   - address, dba, zip, store_concept, unit_capacity")
    print("\n2. Keep these existing columns:")
    print("   - site_name (maps to Store #)")
    print("   - region, city, state (already exist)")
    print("   - project_status (already exists)")
    print("   - target_opening_date (already exists)")
    print("\n3. Only add this one missing column:")
    print("   - sap_number (for SAP #)")
    
    # Check sample data mapping
    print("\n\nSAMPLE DATA PREVIEW:")
    print("-" * 50)
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        print(f"\nRow {i+1}:")
        print(f"  Store #: {row['Store #']} → site_name")
        print(f"  SAP #: {row['SAP #']} → sap_number (NEW)")
        print(f"  City: {row['City']} → city (existing)")
        print(f"  State: {row['State']} → state (existing)")
        print(f"  Region: {row['Region']} → region (existing)")
        print(f"  TOD: {row['TOD']} → target_opening_date (existing)")
        print(f"  Project Status: {row['Project Status']} → project_status (existing)")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()