#!/usr/bin/env python3
"""
Enhanced Nightly Enablement Processor V2
Tracks:
1. ALL circuits that become Enabled (regardless of previous status)
2. Daily count of circuits in "Ready for Enablement" status
3. Simple, clean logic focused on business needs
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime
import pandas as pd
import glob

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nightly-enablement-v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

def process_enablements():
    """Process daily enablement tracking with simplified logic"""
    
    logger.info("=" * 60)
    logger.info("Starting Nightly Enablement Processing V2")
    logger.info("=" * 60)
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get today's and yesterday's CSV files
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        
        today_csv = f"/var/www/html/circuitinfo/tracking_data_{today}.csv"
        yesterday_csv = f"/var/www/html/circuitinfo/tracking_data_{yesterday}.csv"
        
        if not os.path.exists(today_csv):
            logger.error(f"Today's CSV not found: {today_csv}")
            return False
            
        # Read today's data
        logger.info(f"Reading today's data: {today_csv}")
        df_today = pd.read_csv(today_csv, low_memory=False)
        
        # 1. Count circuits in "Ready for Enablement" status
        ready_circuits = df_today[df_today['status'].str.lower() == 'ready for enablement']
        ready_count = len(ready_circuits)
        logger.info(f"Ready for Enablement count: {ready_count}")
        
        # Update ready_queue_daily
        cursor.execute("""
            INSERT INTO ready_queue_daily (summary_date, ready_count, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (summary_date) DO UPDATE SET
                ready_count = EXCLUDED.ready_count,
                created_at = NOW()
        """, (today, ready_count))
        
        # 2. Count new enablements (circuits that became enabled today)
        enabled_today = {}
        for _, row in df_today.iterrows():
            site_id = str(row.get('Site ID', '')).strip()
            status = str(row.get('status', '')).lower().strip()
            
            if site_id and 'enabled' in status and 'ready' not in status:
                enabled_today[site_id] = {
                    'site_name': str(row.get('Site Name', '')).strip(),
                    'circuit_purpose': str(row.get('Circuit Purpose', '')).strip(),
                    'provider': str(row.get('provider_name', '')).strip(),
                    'status': str(row.get('status', '')).strip(),
                    'assigned_to': str(row.get('SCTASK Assignee', '')).strip(),
                    'sctask': str(row.get('SCTASK Number', '')).strip()
                }
        
        new_enablements = []
        
        # Compare with yesterday if available
        if os.path.exists(yesterday_csv):
            logger.info(f"Comparing with yesterday: {yesterday_csv}")
            df_yesterday = pd.read_csv(yesterday_csv, low_memory=False)
            
            # Get yesterday's enabled circuits
            enabled_yesterday = set()
            for _, row in df_yesterday.iterrows():
                site_id = str(row.get('Site ID', '')).strip()
                status = str(row.get('status', '')).lower().strip()
                
                if site_id and 'enabled' in status and 'ready' not in status:
                    enabled_yesterday.add(site_id)
            
            # Find new enablements
            for site_id, circuit_data in enabled_today.items():
                if site_id not in enabled_yesterday:
                    new_enablements.append((site_id, circuit_data))
                    
            logger.info(f"New enablements today: {len(new_enablements)}")
        else:
            logger.warning("Yesterday's CSV not found - counting all enabled as new")
            new_enablements = list(enabled_today.items())
        
        # Insert individual enablement records
        for site_id, circuit in new_enablements:
            cursor.execute("""
                INSERT INTO daily_enablements (
                    date, site_name, circuit_purpose, provider_name,
                    previous_status, current_status, assigned_to, sctask, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                today,
                circuit['site_name'],
                circuit['circuit_purpose'],
                circuit['provider'],
                'Not Enabled',
                circuit['status'],
                circuit['assigned_to'] or '',
                circuit['sctask'] or ''
            ))
            
            if len(new_enablements) <= 10:  # Log first 10
                logger.info(f"  - {circuit['site_name']} ({site_id})")
        
        # Update enablement summary
        cursor.execute("""
            INSERT INTO enablement_summary (summary_date, daily_count, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (summary_date) DO UPDATE SET
                daily_count = EXCLUDED.daily_count,
                created_at = NOW()
        """, (today, len(new_enablements)))
        
        # Commit all changes
        conn.commit()
        
        logger.info("=" * 60)
        logger.info(f"Processing complete: {ready_count} ready, {len(new_enablements)} new enablements")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in enablement processing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function"""
    success = process_enablements()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()