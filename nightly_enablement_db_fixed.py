#!/usr/bin/env python3
"""
Fixed Database-Integrated Nightly Enablement Processor
Correctly tracks only circuits changing from "Ready for Enablement" to "Enabled"
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
        logging.FileHandler('/var/log/nightly-enablement-db.log'),
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

def was_ready_for_enablement(status):
    """Check if a status was ready for enablement"""
    if not status:
        return False
    return 'ready for enablement' in str(status).lower().strip()

def is_enabled_status(status):
    """Check if a status indicates an enabled circuit (but not ready)"""
    if not status:
        return False
    
    status_lower = str(status).lower().strip()
    return 'enabled' in status_lower and 'ready for enablement' not in status_lower

def process_csv_file(file_path):
    """Process a single CSV file and return circuit data"""
    try:
        df = pd.read_csv(file_path, low_memory=False)
        logger.info(f"Processing {file_path}: {len(df)} rows")
        
        # Extract date from filename
        filename = os.path.basename(file_path)
        import re
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        file_date = date_match.group(1) if date_match else None
        
        if not file_date:
            logger.warning(f"Skipping file with invalid date: {filename}")
            return None, file_date
        
        # Create circuit records
        circuits = []
        for _, row in df.iterrows():
            circuit = {
                'site_name': str(row.get('Site Name', '')).strip(),
                'circuit_purpose': str(row.get('Circuit Purpose', '')).strip(),
                'status': str(row.get('status', '')).strip(),
                'provider_name': str(row.get('provider_name', '')).strip(),
                'service_speed': str(row.get('details_service_speed', '')).strip(),
                'monthly_cost': row.get('billing_monthly_cost', 0),
                'date_record_updated': str(row.get('date_record_updated', '')).strip(),
                'assigned_to': str(row.get('SCTASK Assignee', '')).strip(),  # Use correct column
                'sctask': str(row.get('SCTASK Number', '')).strip(),  # Use correct column
                'file_date': file_date
            }
            circuits.append(circuit)
        
        return circuits, file_date
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None, None

def detect_enablements(conn):
    """Detect circuits that transitioned from Ready for Enablement to Enabled"""
    cursor = conn.cursor()
    
    try:
        # Get all CSV files in chronological order
        csv_dir = "/var/www/html/circuitinfo"
        csv_files = glob.glob(f"{csv_dir}/tracking_data_*.csv")
        csv_files.sort()
        
        # Only process files from last 90 days
        cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        csv_files = [f for f in csv_files if f.split('tracking_data_')[1][:10] >= cutoff_date]
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        previous_circuits = {}
        total_enablements = 0
        
        # Clear existing data for reprocessing
        cursor.execute("DELETE FROM daily_enablements WHERE date >= CURRENT_DATE - INTERVAL '90 days'")
        cursor.execute("DELETE FROM enablement_summary WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'")
        
        for csv_file in csv_files:
            circuits, file_date = process_csv_file(csv_file)
            
            if circuits is None:
                continue
            
            daily_enablements = 0
            daily_ready_count = 0
            
            # Check each circuit against previous day
            for circuit in circuits:
                site_key = circuit['site_name']  # Use just site name as key
                current_status = circuit['status']
                
                # Count ready for enablement
                if was_ready_for_enablement(current_status):
                    daily_ready_count += 1
                
                # Check for Ready -> Enabled transition
                if site_key in previous_circuits:
                    previous_status = previous_circuits[site_key]['status']
                    
                    # Specific check: was "ready for enablement" and now "enabled"
                    if was_ready_for_enablement(previous_status) and is_enabled_status(current_status):
                        # This is a true Ready->Enabled transition!
                        daily_enablements += 1
                        
                        # Insert into daily_enablements with assignment info
                        cursor.execute("""
                            INSERT INTO daily_enablements (
                                date, site_name, circuit_purpose, provider_name,
                                service_speed, monthly_cost, previous_status, current_status,
                                assigned_to, sctask, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """, (
                            file_date,
                            circuit['site_name'],
                            circuit['circuit_purpose'],
                            circuit['provider_name'],
                            circuit['service_speed'],
                            circuit['monthly_cost'],
                            previous_status,
                            current_status,
                            circuit['assigned_to'],
                            circuit['sctask']
                        ))
                        
                        total_enablements += 1
            
            # Store daily summary
            cursor.execute("""
                INSERT INTO enablement_summary (
                    summary_date, daily_count, created_at
                ) VALUES (%s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    daily_count = EXCLUDED.daily_count,
                    created_at = EXCLUDED.created_at
            """, (file_date, daily_enablements, datetime.now(timezone.utc)))
            
            # Store ready queue count
            cursor.execute("""
                INSERT INTO ready_queue_daily (
                    summary_date, ready_count, created_at
                ) VALUES (%s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    ready_count = EXCLUDED.ready_count,
                    created_at = EXCLUDED.created_at
            """, (file_date, daily_ready_count, datetime.now(timezone.utc)))
            
            logger.info(f"Date {file_date}: {daily_enablements} Ready->Enabled transitions, {daily_ready_count} ready")
            
            # Update previous_circuits for next iteration
            previous_circuits = {}
            for circuit in circuits:
                previous_circuits[circuit['site_name']] = circuit
        
        # Calculate trends
        calculate_trends(cursor)
        
        conn.commit()
        logger.info(f"Total Ready->Enabled transitions processed: {total_enablements}")
        return True
        
    except Exception as e:
        logger.error(f"Error detecting enablements: {e}")
        import traceback
        logger.error(traceback.format_exc())
        conn.rollback()
        return False
    finally:
        cursor.close()

def calculate_trends(cursor):
    """Calculate weekly and monthly trends"""
    try:
        # Clear existing trends
        cursor.execute("DELETE FROM enablement_trends WHERE period_start >= CURRENT_DATE - INTERVAL '90 days'")
        
        # Calculate weekly trends
        cursor.execute("""
            INSERT INTO enablement_trends (
                period_type, period_start, period_end, enablement_count, created_at
            )
            SELECT 
                'weekly',
                DATE_TRUNC('week', summary_date::date),
                DATE_TRUNC('week', summary_date::date) + INTERVAL '6 days',
                SUM(daily_count),
                NOW()
            FROM enablement_summary 
            WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY DATE_TRUNC('week', summary_date::date)
        """)
        
        # Calculate monthly trends
        cursor.execute("""
            INSERT INTO enablement_trends (
                period_type, period_start, period_end, enablement_count, created_at
            )
            SELECT 
                'monthly',
                DATE_TRUNC('month', summary_date::date),
                DATE_TRUNC('month', summary_date::date) + INTERVAL '1 month' - INTERVAL '1 day',
                SUM(daily_count),
                NOW()
            FROM enablement_summary 
            WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY DATE_TRUNC('month', summary_date::date)
        """)
        
        logger.info("Trend calculations completed")
        
    except Exception as e:
        logger.error(f"Error calculating trends: {e}")

def create_enablement_tables(conn):
    """Create enablement tracking tables if they don't exist"""
    cursor = conn.cursor()
    
    try:
        # Ready queue daily tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ready_queue_daily (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE,
                ready_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Enablement trends
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enablement_trends (
                id SERIAL PRIMARY KEY,
                period_type VARCHAR(20),
                period_start DATE,
                period_end DATE,
                enablement_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(period_type, period_start)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ready_queue_date ON ready_queue_daily(summary_date);
            CREATE INDEX IF NOT EXISTS idx_trends_period ON enablement_trends(period_type, period_start);
        """)
        
        conn.commit()
        logger.info("Enablement tables created/verified")
        
    except Exception as e:
        logger.error(f"Error creating enablement tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def main():
    """Main processing function"""
    logger.info("Starting FIXED nightly enablement processing (Ready->Enabled only)")
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create tables if needed
        create_enablement_tables(conn)
        
        # Process enablement data
        success = detect_enablements(conn)
        
        if success:
            logger.info("Fixed enablement processing completed successfully")
        else:
            logger.error("Fixed enablement processing failed")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)