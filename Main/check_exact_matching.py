#!/usr/bin/env python3
"""
Check exact matching between database site_name and Excel Store #
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
    
    # Get all Store # values from Excel
    excel_stores = []
    for _, row in df.iterrows():
        store = str(row['Store #']).strip() if pd.notna(row['Store #']) else ''
        if store:
            excel_stores.append(store)
    
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all site_name values from database
    cursor.execute("SELECT site_name FROM new_stores WHERE is_active = true ORDER BY site_name")
    db_stores = [row[0] for row in cursor.fetchall()]
    
    print("DATABASE site_name values that don't match Excel Store #:")
    print("=" * 60)
    
    for db_store in db_stores:
        # Try exact match
        if db_store not in excel_stores:
            # Try case-insensitive match
            found = False
            for excel_store in excel_stores:
                if db_store.upper() == excel_store.upper():
                    print(f"Case mismatch: DB='{db_store}' Excel='{excel_store}'")
                    found = True
                    break
            
            if not found:
                print(f"NOT FOUND: '{db_store}'")
    
    print("\n\nEXCEL Store # values that don't match database site_name:")
    print("=" * 60)
    
    db_stores_upper = [s.upper() for s in db_stores]
    for excel_store in excel_stores:
        if excel_store.upper() not in db_stores_upper:
            print(f"NOT FOUND: '{excel_store}'")
    
    # Check specific problem stores
    print("\n\nChecking specific stores:")
    print("=" * 60)
    problem_stores = ['AZP 67', 'FLS 13507', 'PAP 13325', 'STORE #', 'UTS 12973']
    
    for store in problem_stores:
        print(f"\nChecking '{store}':")
        # Check if it exists in Excel (case insensitive)
        excel_matches = [e for e in excel_stores if e.upper() == store.upper()]
        if excel_matches:
            print(f"  Found in Excel as: {excel_matches}")
        else:
            print(f"  NOT in Excel")
            # Check for partial matches
            partial = [e for e in excel_stores if store in e.upper() or e.upper() in store]
            if partial:
                print(f"  Partial matches: {partial}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()