#!/usr/bin/env python3
"""
Fix database to contain only current state of circuits (latest CSV only)
"""

import os
import sys
import pandas as pd
import psycopg2
import re
import glob
from datetime import datetime
from config import Config

def get_db_connection():
    """Get database connection"""
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

def get_latest_csv_file():
    """Get the latest tracking CSV file"""
    tracking_pattern = "/var/www/html/circuitinfo/tracking_data_*.csv"
    all_files = glob.glob(tracking_pattern)
    valid_pattern = re.compile(r'tracking_data_\d{4}-\d{2}-\d{2}\.csv$')
    
    exact_files = []
    for file_path in all_files:
        filename = os.path.basename(file_path)
        if valid_pattern.match(filename):
            try:
                date_str = filename.replace('tracking_data_', '').replace('.csv', '')
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                exact_files.append((file_path, file_date))
            except ValueError:
                continue
    
    if not exact_files:
        raise ValueError("No valid tracking files found")
    
    # Get the latest file
    exact_files.sort(key=lambda x: x[1])
    latest_file, latest_date = exact_files[-1]
    
    return latest_file, latest_date

def fix_current_state():
    """Replace all circuit data with only current state"""
    
    try:
        # Get latest CSV file
        latest_file, latest_date = get_latest_csv_file()
        print(f"📅 Using latest file: {os.path.basename(latest_file)} ({latest_date.strftime('%Y-%m-%d')})")
        
        # Read the CSV
        df = pd.read_csv(latest_file, low_memory=False)
        print(f"📊 Read {len(df)} records from CSV")
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear ALL existing circuit data (but preserve assignments)
        print("🗑️ Clearing existing circuit data...")
        cursor.execute("DELETE FROM circuits")
        conn.commit()
        print("✅ Cleared existing circuit data (assignments preserved)")
        
        # Process each record in the CSV
        inserted_count = 0
        for index, row in df.iterrows():
            if index % 1000 == 0:
                print(f"   Processing record {index}/{len(df)}...")
            
            # Extract key fields - Use site_name + site_id as unique key, not just site_name
            site_name = str(row.get('Site Name', '')).strip()
            site_id = str(row.get('Site ID', '')).strip()
            
            if not site_name or site_name.lower() == 'nan':
                continue
            
            # Skip records with empty Site ID as they may be duplicates/headers
            if not site_id or site_id.lower() == 'nan':
                continue
            circuit_purpose = str(row.get('Circuit Purpose', '')).strip()
            status = str(row.get('status', '')).strip()
            substatus = str(row.get('substatus', '')).strip()
            provider_name = str(row.get('provider_name', '')).strip()
            
            # Handle date_record_updated
            date_record_updated_str = str(row.get('date_record_updated', '')).strip()
            date_record_updated = None
            if date_record_updated_str and date_record_updated_str.lower() != 'nan':
                try:
                    date_record_updated = datetime.strptime(date_record_updated_str[:10], '%Y-%m-%d')
                except:
                    pass
            
            # Handle costs
            try:
                billing_monthly_cost = float(row.get('billing_monthly_cost', 0) or 0)
            except:
                billing_monthly_cost = None
            
            # Insert into database
            cursor.execute("""
                INSERT INTO circuits (
                    site_name, site_id, circuit_purpose, status, substatus, 
                    provider_name, details_ordered_service_speed, billing_monthly_cost,
                    ip_address_start, date_record_updated, assigned_to, sctask,
                    address_1, city, state, zipcode, primary_contact_name, primary_contact_email,
                    created_at, updated_at, data_source, last_csv_file
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                site_name, site_id, circuit_purpose, status, substatus,
                provider_name, str(row.get('details_ordered_service_speed', '')).strip(),
                billing_monthly_cost, str(row.get('ip_address_start', '')).strip(),
                date_record_updated, str(row.get('assigned_to', '')).strip(), str(row.get('sctask', '')).strip(),
                str(row.get('Address 1', '')).strip(), str(row.get('city', '')).strip(),
                str(row.get('state', '')).strip(), str(row.get('zipcode', '')).strip(),
                str(row.get('Primary Contact Name', '')).strip(), str(row.get('Primary Contact Email', '')).strip(),
                datetime.now(), datetime.now(), 'latest_csv_import', os.path.basename(latest_file)
            ))
            
            inserted_count += 1
        
        conn.commit()
        print(f"✅ Inserted {inserted_count} current circuit records")
        
        cursor.close()
        conn.close()
        
        print("🎉 Successfully updated database with current state only!")
        
    except Exception as e:
        print(f"❌ Error fixing current state: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_current_state()