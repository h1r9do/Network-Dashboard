#!/usr/bin/env python3
"""
Fix enablement data using correct logic:
1. Count "Ready for Enablement" circuits per day (queue size)
2. Count actual enablements (Ready → Enabled transitions)
"""

import pandas as pd
import psycopg2
import glob
import os
import sys
from datetime import datetime, timezone

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

def get_db_connection():
    """Get database connection using config"""
    import re
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

def analyze_csv_file(file_path):
    """Analyze a single CSV file for circuits"""
    try:
        df = pd.read_csv(file_path, low_memory=False)
        
        # Extract date from filename
        filename = os.path.basename(file_path)
        if 'sample_data' in filename:
            return None, None, 0, 0
            
        import re
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        file_date = date_match.group(1) if date_match else None
        
        if not file_date:
            return None, None, 0, 0
        
        circuits = {}
        ready_count = 0
        enabled_count = 0
        
        for _, row in df.iterrows():
            site_name = str(row.get('Site Name', '')).strip()
            site_id = str(row.get('Site ID', '')).strip()
            circuit_purpose = str(row.get('Circuit Purpose', '')).strip()
            status = str(row.get('status', '')).strip()
            
            if not site_name or not site_id or not circuit_purpose:
                continue
                
            # Create unique key (Site Name + Site ID + Circuit Purpose)
            key = f"{site_name}||{site_id}||{circuit_purpose}"
            
            circuits[key] = {
                'site_name': site_name,
                'site_id': site_id,
                'circuit_purpose': circuit_purpose,
                'status': status,
                'provider_name': str(row.get('provider_name', '')).strip(),
                'service_speed': str(row.get('details_service_speed', '')).strip(),
                'monthly_cost': row.get('billing_monthly_cost', 0)
            }
            
            # Count statuses correctly
            status_lower = status.lower()
            if 'ready for enablement' in status_lower:
                ready_count += 1
            elif any(word in status_lower for word in ['enabled', 'activated', 'service activated']):
                enabled_count += 1
        
        print(f"{file_date}: {len(circuits)} circuits, {ready_count} ready, {enabled_count} enabled")
        return circuits, file_date, ready_count, enabled_count
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None, 0, 0

def fix_enablement_data():
    """Fix enablement data using correct logic"""
    
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing incorrect data
        print("Clearing existing enablement data...")
        cursor.execute("DELETE FROM circuit_enablements")
        cursor.execute("DELETE FROM enablement_summary")
        cursor.execute("DELETE FROM enablement_trends")
        
        # Get all CSV files in chronological order
        csv_dir = "/var/www/html/circuitinfo"
        csv_files = glob.glob(f"{csv_dir}/tracking_data_*.csv")
        csv_files = [f for f in csv_files if 'sample_data' not in f]
        csv_files.sort()
        
        print(f"Processing {len(csv_files)} CSV files...")
        
        previous_circuits = {}
        total_enablements = 0
        
        for csv_file in csv_files:
            circuits, file_date, ready_count, enabled_count = analyze_csv_file(csv_file)
            
            if circuits is None:
                continue
            
            daily_enablements = 0
            
            # Check each circuit against previous day for enablement transitions
            if previous_circuits:  # Skip first day since no previous data
                for key, current_circuit in circuits.items():
                    if key in previous_circuits:
                        prev_status = previous_circuits[key]['status'].lower()
                        curr_status = current_circuit['status'].lower()
                        
                        # CORRECT LOGIC: Ready for Enablement → Enabled
                        if ('ready for enablement' in prev_status and 
                            any(word in curr_status for word in ['enabled', 'activated', 'service activated'])):
                            
                            # This is a real enablement!
                            enablement_record = (
                                current_circuit['site_name'],
                                current_circuit['circuit_purpose'], 
                                current_circuit['provider_name'],
                                file_date,
                                previous_circuits[key]['status'],
                                current_circuit['status'],
                                current_circuit['service_speed'],
                                current_circuit['monthly_cost'],
                                datetime.now(timezone.utc)
                            )
                            
                            cursor.execute("""
                                INSERT INTO circuit_enablements (
                                    site_name, circuit_purpose, provider_name, enablement_date,
                                    previous_status, current_status, service_speed, monthly_cost,
                                    detected_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (site_name, circuit_purpose, provider_name, enablement_date) 
                                DO NOTHING
                            """, enablement_record)
                            
                            daily_enablements += 1
                            total_enablements += 1
                            print(f"  ENABLEMENT: {current_circuit['site_name']} - {current_circuit['circuit_purpose']}")
            
            # Store CORRECTED daily summary
            # daily_count = actual enablements (transitions from ready → enabled)
            cursor.execute("""
                INSERT INTO enablement_summary (
                    summary_date, daily_count, created_at
                ) VALUES (%s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    daily_count = EXCLUDED.daily_count
            """, (file_date, daily_enablements, datetime.now(timezone.utc)))
            
            print(f"{file_date}: {daily_enablements} actual enablements, {ready_count} in ready queue")
            
            # Update previous_circuits for next iteration
            previous_circuits = circuits
        
        conn.commit()
        print(f"\nFIXED: {total_enablements} total actual enablements found")
        print("Enablement data has been corrected!")
        
    except Exception as e:
        print(f"Error fixing enablement data: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

if __name__ == "__main__":
    success = fix_enablement_data()
    print("✅ Success!" if success else "❌ Failed!")