#!/usr/bin/env python3
"""
CORRECTED Database-Integrated Nightly Enablement Processor
Fixes the calculation logic to properly track:
1. Daily "Ready for Enablement" queue count
2. Actual enablements (Ready for Enablement → Enabled transitions)

Matches Site Name, Site ID, and Circuit Purpose for accurate tracking.
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone, timedelta
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
        logging.FileHandler('/var/log/nightly-enablement-db-corrected.log'),
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

def is_ready_for_enablement(status):
    """Check if status indicates ready for enablement"""
    if not status:
        return False
    
    status_lower = str(status).lower().strip()
    return 'ready for enablement' in status_lower

def is_enabled_status(status):
    """Check if a status indicates an enabled circuit"""
    if not status:
        return False
    
    enabled_keywords = [
        'enabled', 'service activated', 'activated',
        'enabled using existing broadband'
    ]
    
    status_lower = str(status).lower().strip()
    return any(keyword in status_lower for keyword in enabled_keywords)

def process_csv_file(file_path):
    """Process a single CSV file and return circuit data with proper key matching"""
    try:
        df = pd.read_csv(file_path, low_memory=False)
        logger.info(f"Processing {file_path}: {len(df)} rows")
        
        # Extract date from filename
        filename = os.path.basename(file_path)
        if 'sample_data' in filename:
            logger.warning(f"Skipping sample data file: {filename}")
            return None, None
        
        import re
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        file_date = date_match.group(1) if date_match else None
        
        if not file_date:
            logger.warning(f"Skipping file with invalid date: {filename}")
            return None, None
        
        # Create circuit records with proper key matching (Site Name, Site ID, Circuit Purpose)
        circuits = {}
        ready_count = 0
        
        for _, row in df.iterrows():
            site_name = str(row.get('Site Name', '')).strip()
            site_id = str(row.get('Site ID', '')).strip()  
            circuit_purpose = str(row.get('Circuit Purpose', '')).strip()
            status = str(row.get('status', '')).strip()
            
            # Skip rows without required fields
            if not site_name or not site_id or not circuit_purpose:
                continue
                
            # Create unique key for circuit tracking
            circuit_key = f"{site_name}||{site_id}||{circuit_purpose}"
            
            circuit = {
                'site_name': site_name,
                'site_id': site_id,
                'circuit_purpose': circuit_purpose,
                'status': status,
                'provider_name': str(row.get('provider_name', '')).strip(),
                'service_speed': str(row.get('details_service_speed', '')).strip(),
                'monthly_cost': row.get('billing_monthly_cost', 0),
                'file_date': file_date,
                'circuit_key': circuit_key
            }
            
            circuits[circuit_key] = circuit
            
            # Count ready for enablement circuits
            if is_ready_for_enablement(status):
                ready_count += 1
        
        logger.info(f"Date {file_date}: {len(circuits)} circuits, {ready_count} ready for enablement")
        return circuits, file_date, ready_count
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None, None, 0

def detect_enablements_corrected(conn):
    """Detect enablements using corrected logic"""
    cursor = conn.cursor()
    
    try:
        # Clear existing data to recalculate correctly
        cursor.execute("DELETE FROM circuit_enablements")
        cursor.execute("DELETE FROM enablement_summary")
        cursor.execute("DELETE FROM enablement_trends")
        
        # Get all CSV files in chronological order  
        csv_dir = "/var/www/html/circuitinfo"
        csv_files = glob.glob(f"{csv_dir}/tracking_data_*.csv")
        csv_files = [f for f in csv_files if 'sample_data' not in f]
        csv_files.sort()
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        previous_circuits = {}
        total_enablements = 0
        
        for csv_file in csv_files:
            circuits, file_date, ready_count = process_csv_file(csv_file)
            
            if circuits is None:
                continue
                
            daily_enablements = 0
            
            # Check each circuit against previous day for status changes
            for circuit_key, current_circuit in circuits.items():
                current_status = current_circuit['status']
                
                # Check if this circuit was ready for enablement previously and is now enabled
                if circuit_key in previous_circuits:
                    previous_status = previous_circuits[circuit_key]['status']
                    
                    # CORRECTED LOGIC: Count transitions from "Ready for Enablement" to "Enabled"
                    if (is_ready_for_enablement(previous_status) and 
                        is_enabled_status(current_status)):
                        
                        # This is a real enablement!
                        enablement_record = {
                            'site_name': current_circuit['site_name'],
                            'site_id': current_circuit['site_id'],
                            'circuit_purpose': current_circuit['circuit_purpose'],
                            'enablement_date': file_date,
                            'previous_status': previous_status,
                            'current_status': current_status,
                            'provider_name': current_circuit['provider_name'],
                            'service_speed': current_circuit['service_speed'],
                            'monthly_cost': current_circuit['monthly_cost'],
                            'detected_at': datetime.now(timezone.utc)
                        }
                        
                        # Insert enablement record
                        insert_sql = """
                            INSERT INTO circuit_enablements (
                                site_name, circuit_purpose, provider_name, enablement_date,
                                previous_status, current_status, service_speed, monthly_cost,
                                detected_at
                            ) VALUES (
                                %(site_name)s, %(circuit_purpose)s, %(provider_name)s, %(enablement_date)s,
                                %(previous_status)s, %(current_status)s, %(service_speed)s, %(monthly_cost)s,
                                %(detected_at)s
                            )
                            ON CONFLICT (site_name, circuit_purpose, provider_name, enablement_date) 
                            DO NOTHING
                        """
                        
                        cursor.execute(insert_sql, enablement_record)
                        daily_enablements += 1
                        total_enablements += 1
                        
                        logger.info(f"ENABLEMENT: {current_circuit['site_name']} - {current_circuit['circuit_purpose']} on {file_date}")
            
            # Store daily summary with CORRECTED meaning:
            # daily_count = actual enablements (transitions from ready → enabled)
            # Store ready_count separately for reporting
            cursor.execute("""
                INSERT INTO daily_enablements (
                    summary_date, enablement_count, ready_queue_count, created_at
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    enablement_count = EXCLUDED.enablement_count,
                    ready_queue_count = EXCLUDED.ready_queue_count
            """, (file_date, daily_enablements, ready_count, datetime.now(timezone.utc)))
            
            # Also update the existing enablement_summary table for backwards compatibility
            cursor.execute("""
                INSERT INTO enablement_summary (
                    summary_date, daily_count, created_at
                ) VALUES (%s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    daily_count = EXCLUDED.daily_count
            """, (file_date, daily_enablements, datetime.now(timezone.utc)))
            
            logger.info(f"Date {file_date}: {daily_enablements} enablements, {ready_count} ready for enablement")
            
            # Update previous_circuits for next iteration
            previous_circuits = circuits
        
        conn.commit()
        logger.info(f"CORRECTED processing complete: {total_enablements} total enablements found")
        return True
        
    except Exception as e:
        logger.error(f"Error in corrected enablement detection: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def create_corrected_tables(conn):
    """Create corrected enablement tracking tables"""
    cursor = conn.cursor()
    
    try:
        # Create new table for proper enablement tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_enablements (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE,
                enablement_count INTEGER DEFAULT 0,
                ready_queue_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Add site_id column to existing circuit_enablements if it doesn't exist
        try:
            cursor.execute("""
                ALTER TABLE circuit_enablements 
                ADD COLUMN IF NOT EXISTS site_id VARCHAR(50)
            """)
        except Exception as e:
            logger.warning(f"Could not add site_id column (may already exist): {e}")
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_enablements_date ON daily_enablements(summary_date);
        """)
        
        conn.commit()
        logger.info("Corrected enablement tables created/verified")
        
    except Exception as e:
        logger.error(f"Error creating corrected tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def main():
    """Main processing function with corrected logic"""
    logger.info("Starting CORRECTED database-integrated nightly enablement processing")
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create corrected tables
        create_corrected_tables(conn)
        
        # Process enablement data with corrected logic
        success = detect_enablements_corrected(conn)
        
        if success:
            logger.info("CORRECTED nightly enablement processing completed successfully")
        else:
            logger.error("CORRECTED nightly enablement processing failed")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in corrected main process: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)