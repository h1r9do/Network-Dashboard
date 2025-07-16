#!/usr/bin/env python3
"""
Final Fixed Database-Integrated Nightly Enablement Processor
Uses record_number as the unique identifier for circuits
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone, timedelta
import pandas as pd
import glob

# Add parent directory to path for imports
sys.path.insert(0, '/usr/local/bin/Main')
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

def process_csv_file(file_path):
    """Process a single CSV file and return circuit data by record_number"""
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
        
        # Create circuit records BY RECORD NUMBER (unique identifier)
        circuits_by_record = {}
        
        for _, row in df.iterrows():
            record_number = str(row.get('record_number', '')).strip()
            if not record_number or record_number == 'nan':
                # Skip records without record_number
                continue
                
            # Store the row data for this record_number
            circuits_by_record[record_number] = {
                'record_number': record_number,
                'site_id': str(row.get('Site ID', '')).strip(),
                'site_name': str(row.get('Site Name', '')).strip(),
                'circuit_purpose': str(row.get('Circuit Purpose', '')).strip(),
                'status': str(row.get('status', '')).strip(),
                'provider_name': str(row.get('provider_name', '')).strip(),
                'service_speed': str(row.get('details_service_speed', '')).strip(),
                'monthly_cost': row.get('billing_monthly_cost', 0),
                'assigned_to': str(row.get('SCTASK Assignee', '')).strip(),
                'sctask': str(row.get('SCTASK Number', '')).strip(),
                'file_date': file_date
            }
        
        return circuits_by_record, file_date
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None, None

def detect_enablements(conn):
    """Detect circuits that transitioned from Ready for Enablement to Enabled by record_number"""
    cursor = conn.cursor()
    
    try:
        # Get all CSV files in chronological order
        csv_dir = "/var/www/html/circuitinfo"
        csv_files = glob.glob(f"{csv_dir}/tracking_data_*.csv")
        
        # Filter out dedup files and other non-standard files
        csv_files = [f for f in csv_files if '_dedup' not in f and 'sample' not in f.lower()]
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
        cursor.execute("DELETE FROM ready_queue_daily WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'")
        
        for csv_file in csv_files:
            circuits_by_record, file_date = process_csv_file(csv_file)
            
            if circuits_by_record is None:
                continue
            
            daily_enablements = 0
            daily_ready_count = 0
            
            # Count ready for enablement circuits
            for record_number, circuit in circuits_by_record.items():
                status_lower = circuit['status'].lower()
                if 'ready for enablement' in status_lower:
                    daily_ready_count += 1
            
            # Check each circuit for Ready -> Enabled transition
            for record_number, circuit in circuits_by_record.items():
                current_status = circuit['status'].lower()
                
                # Check if this circuit transitioned from Ready to Enabled
                if record_number in previous_circuits:
                    prev_status = previous_circuits[record_number]['status'].lower()
                    
                    # Specific check: was "ready for enablement" and now "enabled" (but not "ready for enablement")
                    if ('ready for enablement' in prev_status and 
                        'enabled' in current_status and 
                        'ready for enablement' not in current_status):
                        
                        # This is a true Ready->Enabled transition!
                        daily_enablements += 1
                        
                        # Get assigned_to from circuits table using record_number
                        cursor.execute("""
                            SELECT assigned_to FROM circuits 
                            WHERE record_number = %s 
                            LIMIT 1
                        """, (record_number,))
                        result = cursor.fetchone()
                        assigned_to = result[0] if result and result[0] else circuit.get('assigned_to', '')
                        
                        # Insert into daily_enablements with record_number
                        cursor.execute("""
                            INSERT INTO daily_enablements (
                                date, record_number, site_id, site_name, circuit_purpose, provider_name,
                                service_speed, monthly_cost, previous_status, current_status,
                                assigned_to, sctask, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (date, record_number) DO UPDATE SET
                                site_id = EXCLUDED.site_id,
                                site_name = EXCLUDED.site_name,
                                circuit_purpose = EXCLUDED.circuit_purpose,
                                provider_name = EXCLUDED.provider_name,
                                service_speed = EXCLUDED.service_speed,
                                monthly_cost = EXCLUDED.monthly_cost,
                                previous_status = EXCLUDED.previous_status,
                                current_status = EXCLUDED.current_status,
                                assigned_to = EXCLUDED.assigned_to,
                                sctask = EXCLUDED.sctask,
                                created_at = NOW()
                        """, (
                            file_date,
                            record_number,
                            circuit['site_id'],
                            circuit['site_name'],
                            circuit['circuit_purpose'],
                            circuit['provider_name'],
                            circuit['service_speed'],
                            circuit['monthly_cost'],
                            previous_circuits[record_number]['status'],
                            circuit['status'],
                            assigned_to,
                            circuit['sctask']
                        ))
                        
                        total_enablements += 1
                        
                        if daily_enablements <= 3:  # Log first few examples
                            logger.info(f"  Example: {record_number} ({circuit['site_name']}) changed from '{prev_status}' to '{current_status}'")
            
            # Store daily summary
            cursor.execute("""
                INSERT INTO enablement_summary (
                    summary_date, daily_count, created_at
                ) VALUES (%s, %s, NOW())
                ON CONFLICT (summary_date) DO UPDATE SET
                    daily_count = EXCLUDED.daily_count,
                    created_at = NOW()
            """, (file_date, daily_enablements))
            
            # Store ready queue count
            cursor.execute("""
                INSERT INTO ready_queue_daily (
                    summary_date, ready_count, created_at
                ) VALUES (%s, %s, NOW())
                ON CONFLICT (summary_date) DO UPDATE SET
                    ready_count = EXCLUDED.ready_count,
                    created_at = NOW()
            """, (file_date, daily_ready_count))
            
            logger.info(f"Date {file_date}: {daily_enablements} Ready->Enabled transitions, {daily_ready_count} ready")
            
            # Update previous circuits for next iteration
            previous_circuits = circuits_by_record
        
        # IMPORTANT: Commit the enablement data BEFORE calculating trends
        conn.commit()
        logger.info(f"Total Ready->Enabled transitions processed: {total_enablements}")
        
        # Now calculate trends in a separate transaction
        calculate_trends_safe(conn)
        
        return True
        
    except Exception as e:
        logger.error(f"Error detecting enablements: {e}")
        import traceback
        logger.error(traceback.format_exc())
        conn.rollback()
        return False
    finally:
        cursor.close()

def calculate_trends_safe(conn):
    """Calculate weekly and monthly trends with proper error handling"""
    cursor = conn.cursor()
    try:
        # Use ON CONFLICT to handle duplicates gracefully
        logger.info("Calculating enablement trends...")
        
        # Calculate weekly trends with ON CONFLICT
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
            ON CONFLICT (period_type, period_start) DO UPDATE SET
                enablement_count = EXCLUDED.enablement_count,
                period_end = EXCLUDED.period_end,
                created_at = NOW()
        """)
        
        # Calculate monthly trends with ON CONFLICT
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
            ON CONFLICT (period_type, period_start) DO UPDATE SET
                enablement_count = EXCLUDED.enablement_count,
                period_end = EXCLUDED.period_end,
                created_at = NOW()
        """)
        
        conn.commit()
        logger.info("Trends calculated successfully")
        
    except Exception as e:
        logger.error(f"Error calculating trends: {e}")
        # Don't let trend calculation errors affect the main data
        conn.rollback()
        # This is non-critical, so we continue
    finally:
        cursor.close()

def create_enablement_tables(conn):
    """Create enablement tables if they don't exist"""
    cursor = conn.cursor()
    
    try:
        # Create tables with proper conflict constraints
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_enablements (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                record_number VARCHAR(50),
                site_id VARCHAR(50),
                site_name VARCHAR(100),
                circuit_purpose VARCHAR(50),
                provider_name VARCHAR(100),
                service_speed VARCHAR(50),
                monthly_cost NUMERIC(10,2),
                previous_status VARCHAR(100),
                current_status VARCHAR(100),
                assigned_to VARCHAR(100),
                sctask VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(date, record_number)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enablement_summary (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE NOT NULL,
                daily_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ready_queue_daily (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE NOT NULL,
                ready_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enablement_trends (
                id SERIAL PRIMARY KEY,
                period_type VARCHAR(20) NOT NULL,
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                enablement_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(period_type, period_start)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_enablements_date ON daily_enablements(date);
            CREATE INDEX IF NOT EXISTS idx_daily_enablements_record ON daily_enablements(record_number);
            CREATE INDEX IF NOT EXISTS idx_enablement_summary_date ON enablement_summary(summary_date);
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
    logger.info("Starting FINAL nightly enablement processing (using record_number)")
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create tables if needed
        create_enablement_tables(conn)
        
        # Process enablement data
        success = detect_enablements(conn)
        
        if success:
            logger.info("Final enablement processing completed successfully")
        else:
            logger.error("Final enablement processing failed")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)