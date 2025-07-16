#!/usr/bin/env python3
"""
Populate ready queue data for reporting
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

def populate_ready_queue():
    """Populate ready queue data"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute("DELETE FROM ready_queue_daily")
        
        # Get all CSV files
        csv_dir = "/var/www/html/circuitinfo"
        csv_files = glob.glob(f"{csv_dir}/tracking_data_*.csv")
        csv_files = [f for f in csv_files if 'sample_data' not in f]
        csv_files.sort()
        
        for csv_file in csv_files:
            # Extract date from filename
            filename = os.path.basename(csv_file)
            import re
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            file_date = date_match.group(1) if date_match else None
            
            if not file_date:
                continue
                
            # Read CSV and count ready circuits
            df = pd.read_csv(csv_file, low_memory=False)
            ready_count = 0
            
            for _, row in df.iterrows():
                status = str(row.get('status', '')).strip().lower()
                if 'ready for enablement' in status:
                    ready_count += 1
            
            # Insert ready queue count
            cursor.execute("""
                INSERT INTO ready_queue_daily (summary_date, ready_count, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    ready_count = EXCLUDED.ready_count
            """, (file_date, ready_count, datetime.now(timezone.utc)))
            
            print(f"{file_date}: {ready_count} ready for enablement")
        
        conn.commit()
        print("Ready queue data populated!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

if __name__ == "__main__":
    populate_ready_queue()