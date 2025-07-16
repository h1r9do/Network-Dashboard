#!/usr/bin/env python3
"""
Check which stores are missing from Excel or have incomplete data
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
    # Read Excel file
    excel_path = "/var/www/html/meraki-data/RE - Targeted Opening Dates - 20250702.xlsx"
    df = pd.read_excel(excel_path, skiprows=3)
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)
    
    # Get all store names from Excel
    excel_stores = set(str(row['Store #']).strip().upper() for _, row in df.iterrows() if pd.notna(row['Store #']))
    
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all active stores from database
    cursor.execute("SELECT site_name FROM new_stores WHERE is_active = true ORDER BY site_name")
    db_stores = set(row[0] for row in cursor.fetchall())
    
    print("ANALYSIS:")
    print("=" * 60)
    print(f"Total stores in database: {len(db_stores)}")
    print(f"Total stores in Excel: {len(excel_stores)}")
    
    # Find stores in DB but not in Excel
    missing_from_excel = db_stores - excel_stores
    print(f"\nStores in DB but NOT in Excel ({len(missing_from_excel)}):")
    for store in sorted(missing_from_excel):
        print(f"  - {store}")
    
    # Find stores in Excel but not in DB
    missing_from_db = excel_stores - db_stores
    print(f"\nStores in Excel but NOT in DB ({len(missing_from_db)}):")
    for store in sorted(missing_from_db):
        print(f"  - {store}")
    
    # Check for stores with incomplete data in Excel
    print("\nStores in Excel with missing DBA:")
    for _, row in df.iterrows():
        store = str(row['Store #']).strip().upper()
        if store in db_stores and pd.isna(row.get('DBA')):
            print(f"  - {store}")
    
    # Check SAP numbers that are 0
    print("\nStores with SAP # = 0 in Excel:")
    for _, row in df.iterrows():
        store = str(row['Store #']).strip().upper()
        sap = str(row.get('SAP #', '')).strip()
        if store in db_stores and sap == '0':
            print(f"  - {store}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()