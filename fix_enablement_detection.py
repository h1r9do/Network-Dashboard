#!/usr/bin/env python3
"""
Fix enablement detection logic - clear bad data and reprocess correctly
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime, timezone
import pandas as pd
import glob

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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

def clear_bad_data(conn):
    """Clear the incorrect enablement data"""
    cursor = conn.cursor()
    
    try:
        logger.info("Clearing incorrect enablement data...")
        
        # Clear enablement summary
        cursor.execute("DELETE FROM enablement_summary")
        
        # Clear circuit enablements
        cursor.execute("DELETE FROM circuit_enablements")
        
        # Clear enablement trends
        cursor.execute("DELETE FROM enablement_trends")
        
        conn.commit()
        logger.info("Bad data cleared successfully")
        
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def reprocess_enablements_correctly(conn):
    """Reprocess enablements with correct logic"""
    cursor = conn.cursor()
    
    try:
        # Get all CSV files in chronological order
        csv_dir = "/var/www/html/circuitinfo"
        csv_files = glob.glob(f"{csv_dir}/tracking_data_*.csv")
        csv_files.sort()
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        previous_day_data = {}
        total_enablements = 0
        
        for i, csv_file in enumerate(csv_files):
            try:
                # Extract date from filename
                filename = os.path.basename(csv_file)
                if 'sample_data' in filename:
                    logger.info(f"Skipping sample data file: {filename}")
                    continue
                
                import re
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
                if not date_match:
                    logger.warning(f"Cannot extract date from {filename}")
                    continue
                
                file_date = date_match.group(1)
                logger.info(f"Processing {filename} for date {file_date}")
                
                # Read CSV
                df = pd.read_csv(csv_file, low_memory=False)
                
                # Build current day circuit status lookup
                current_day_data = {}
                for _, row in df.iterrows():
                    site_name = str(row.get('Site Name', '')).strip()
                    circuit_purpose = str(row.get('Circuit Purpose', '')).strip()
                    provider_name = str(row.get('provider_name', '')).strip()
                    status = str(row.get('status', '')).strip()
                    
                    # Create unique key
                    circuit_key = f"{site_name}|{circuit_purpose}|{provider_name}"
                    
                    if circuit_key and site_name:  # Only include valid circuits
                        current_day_data[circuit_key] = {
                            'site_name': site_name,
                            'circuit_purpose': circuit_purpose,
                            'provider_name': provider_name,
                            'status': status,
                            'service_speed': str(row.get('details_service_speed', '')).strip(),
                            'monthly_cost': row.get('billing_monthly_cost', 0)
                        }
                
                # Count enablements by comparing with previous day
                daily_enablements = 0
                enablement_records = []
                
                if i > 0:  # Skip first file as we have no previous day to compare
                    for circuit_key, current_circuit in current_day_data.items():
                        current_status = current_circuit['status']
                        
                        # Check if circuit is currently enabled
                        if is_enabled_status(current_status):
                            # Check previous day status
                            if circuit_key in previous_day_data:
                                previous_status = previous_day_data[circuit_key]['status']
                                
                                # If was NOT enabled before but is NOW enabled = NEW ENABLEMENT
                                if not is_enabled_status(previous_status):
                                    enablement_records.append({
                                        'site_name': current_circuit['site_name'],
                                        'circuit_purpose': current_circuit['circuit_purpose'],
                                        'provider_name': current_circuit['provider_name'],
                                        'enablement_date': file_date,
                                        'previous_status': previous_status,
                                        'current_status': current_status,
                                        'service_speed': current_circuit['service_speed'],
                                        'monthly_cost': current_circuit['monthly_cost'],
                                        'detected_at': datetime.now(timezone.utc)
                                    })
                                    daily_enablements += 1
                            else:
                                # New circuit that's already enabled - count as enablement
                                enablement_records.append({
                                    'site_name': current_circuit['site_name'],
                                    'circuit_purpose': current_circuit['circuit_purpose'],
                                    'provider_name': current_circuit['provider_name'],
                                    'enablement_date': file_date,
                                    'previous_status': 'NEW',
                                    'current_status': current_status,
                                    'service_speed': current_circuit['service_speed'],
                                    'monthly_cost': current_circuit['monthly_cost'],
                                    'detected_at': datetime.now(timezone.utc)
                                })
                                daily_enablements += 1
                
                # Insert enablement records
                if enablement_records:
                    for record in enablement_records:
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
                        cursor.execute(insert_sql, record)
                
                # Store daily summary
                summary_sql = """
                    INSERT INTO enablement_summary (
                        summary_date, daily_count, created_at
                    ) VALUES (%s, %s, %s)
                    ON CONFLICT (summary_date) DO UPDATE SET
                        daily_count = EXCLUDED.daily_count
                """
                cursor.execute(summary_sql, (file_date, daily_enablements, datetime.now(timezone.utc)))
                
                logger.info(f"Date {file_date}: {daily_enablements} enablements (from {len(current_day_data)} total circuits)")
                total_enablements += daily_enablements
                
                # Update previous day data for next iteration
                previous_day_data = current_day_data
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
                continue
        
        # Calculate trends
        calculate_trends(cursor)
        
        conn.commit()
        logger.info(f"Reprocessing complete. Total enablements: {total_enablements}")
        
    except Exception as e:
        logger.error(f"Error in reprocessing: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def calculate_trends(cursor):
    """Calculate weekly and monthly trends"""
    try:
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
            GROUP BY DATE_TRUNC('week', summary_date::date)
            ON CONFLICT (period_type, period_start) DO UPDATE SET
                enablement_count = EXCLUDED.enablement_count,
                period_end = EXCLUDED.period_end
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
            GROUP BY DATE_TRUNC('month', summary_date::date)
            ON CONFLICT (period_type, period_start) DO UPDATE SET
                enablement_count = EXCLUDED.enablement_count,
                period_end = EXCLUDED.period_end
        """)
        
        logger.info("Trend calculations completed")
        
    except Exception as e:
        logger.error(f"Error calculating trends: {e}")

def main():
    """Main function"""
    logger.info("Starting enablement detection fix")
    
    try:
        conn = get_db_connection()
        
        # Clear bad data
        clear_bad_data(conn)
        
        # Reprocess correctly
        reprocess_enablements_correctly(conn)
        
        logger.info("Enablement detection fix completed successfully")
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)