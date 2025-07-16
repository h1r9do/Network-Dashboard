#\!/usr/bin/env python3
"""
Enhanced update circuits from tracking CSV with detailed logging
Ensures database exactly matches tracking CSV data
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime
import pandas as pd
import re

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging with both file and console output
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler
file_handler = logging.FileHandler('/var/log/circuit-update-detailed.log')
file_handler.setFormatter(log_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_db_connection():
    """Get database connection from environment variables"""
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 5432)),
        database=os.environ.get('DB_NAME', 'dsrcircuits'),
        user=os.environ.get('DB_USER', 'dsruser'),
        password=os.environ.get('DB_PASSWORD', 'dsrpass123')
    )

def normalize_speed(speed_value):
    """Normalize speed values (convert G to M if needed)"""
    if pd.isna(speed_value) or speed_value == '':
        return None
    
    speed_str = str(speed_value)
    # Convert G to M
    if 'G' in speed_str:
        match = re.search(r'(\d+(?:\.\d+)?)G', speed_str)
        if match:
            gb_value = float(match.group(1))
            mb_value = gb_value * 1000
            speed_str = speed_str.replace(match.group(0), f"{mb_value:.0f}M")
    
    return speed_str

def parse_date(date_value):
    """Parse date strings to datetime objects"""
    if pd.isna(date_value) or date_value == '' or str(date_value) == '0000-00-00' or str(date_value) == '0000-00-00 00:00:00':
        return None
    
    # Check for invalid dates
    date_str = str(date_value)
    if date_str.startswith('0000-'):
        return None
    
    try:
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except:
        return None

def update_circuits_from_csv(csv_file_path):
    """Update circuits database from tracking CSV file with detailed logging"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting circuit update from CSV: {csv_file_path}")
    logger.info(f"Start time: {start_time}")
    logger.info("=" * 80)
    
    try:
        # Read CSV file
        logger.info("Reading CSV file...")
        df = pd.read_csv(csv_file_path, low_memory=False)
        logger.info(f"Loaded {len(df)} records from CSV")
        
        # Clean column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Connect to database
        logger.info("Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current timestamp
        current_time = datetime.now()
        csv_filename = os.path.basename(csv_file_path)
        
        # Track statistics
        stats = {
            'total_csv_records': len(df),
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'skipped_no_record_number': 0,
            'skipped_duplicate': 0,
            'skipped_manual_override': 0,
            'unchanged': 0,
            'errors': 0,
            'status_changes': []
        }
        
        # Get all manual override circuits
        cursor.execute("""
            SELECT record_number, site_name, status, manual_override 
            FROM circuits 
            WHERE record_number IS NOT NULL
        """)
        db_circuits = {row[0]: {'site_name': row[1], 'status': row[2], 'manual_override': row[3]} 
                      for row in cursor.fetchall()}
        logger.info(f"Found {len(db_circuits)} existing circuits in database")
        
        # Track unique records
        seen_record_numbers = set()
        
        logger.info("Processing CSV records...")
        for idx, row in df.iterrows():
            # Skip if no record_number
            record_num = row.get('record_number')
            if pd.isna(record_num) or not record_num:
                stats['skipped_no_record_number'] += 1
                continue
                
            # Skip duplicates within the same CSV
            if record_num in seen_record_numbers:
                stats['skipped_duplicate'] += 1
                continue
            seen_record_numbers.add(record_num)
            
            # Check manual override
            if record_num in db_circuits and db_circuits[record_num].get('manual_override'):
                logger.info(f"Skipping {record_num} ({db_circuits[record_num]['site_name']}) - manual override active")
                stats['skipped_manual_override'] += 1
                continue
            
            try:
                # Prepare data
                data = {
                    'record_number': record_num,
                    'site_name': row.get('site_name'),
                    'site_id': row.get('site_id'),
                    'circuit_purpose': row.get('circuit_purpose'),
                    'status': row.get('status'),
                    'substatus': row.get('substatus'),
                    'provider_name': row.get('provider_name'),
                    'details_service_speed': normalize_speed(row.get('details_service_speed')),
                    'details_ordered_service_speed': normalize_speed(row.get('details_ordered_service_speed')),
                    'billing_monthly_cost': float(row.get('billing_monthly_cost', 0)) if pd.notna(row.get('billing_monthly_cost')) else None,
                    'ip_address_start': row.get('ip_address_start'),
                    'date_record_updated': parse_date(row.get('date_record_updated')),
                    'milestone_service_activated': parse_date(row.get('milestone_service_activated')),
                    'milestone_enabled': parse_date(row.get('milestone_enabled')),
                    'address_1': row.get('address_1'),
                    'city': row.get('city'),
                    'state': row.get('state'),
                    'zipcode': row.get('zipcode'),
                    'primary_contact_name': row.get('primary_contact_name'),
                    'primary_contact_email': row.get('primary_contact_email'),
                    'billing_install_cost': float(row.get('billing_install_cost', 0)) if pd.notna(row.get('billing_install_cost')) else None,
                    'details_provider': row.get('details_provider'),
                    'details_provider_phone': row.get('details_provider_phone'),
                    'billing_account': row.get('billing_account'),
                    'target_enablement_date': parse_date(row.get('target_enablement_date')),
                    'fingerprint': f"{row.get('site_name')} < /dev/null | {row.get('site_id')}|{row.get('circuit_purpose')}",
                    'last_csv_file': csv_filename,
                    'data_source': 'csv_import',
                    'updated_at': current_time
                }
                
                # Check if record exists
                if record_num in db_circuits:
                    # Update existing record
                    old_status = db_circuits[record_num]['status']
                    new_status = data['status']
                    
                    # Log status changes
                    if old_status \!= new_status:
                        change_msg = f"{record_num} ({data['site_name']}): {old_status} → {new_status}"
                        logger.info(f"Status change: {change_msg}")
                        stats['status_changes'].append(change_msg)
                    
                    # Update record
                    cursor.execute("""
                        UPDATE circuits SET
                            site_name = %(site_name)s,
                            site_id = %(site_id)s,
                            circuit_purpose = %(circuit_purpose)s,
                            status = %(status)s,
                            substatus = %(substatus)s,
                            provider_name = %(provider_name)s,
                            details_service_speed = %(details_service_speed)s,
                            details_ordered_service_speed = %(details_ordered_service_speed)s,
                            billing_monthly_cost = %(billing_monthly_cost)s,
                            ip_address_start = %(ip_address_start)s,
                            date_record_updated = %(date_record_updated)s,
                            milestone_service_activated = %(milestone_service_activated)s,
                            milestone_enabled = %(milestone_enabled)s,
                            address_1 = %(address_1)s,
                            city = %(city)s,
                            state = %(state)s,
                            zipcode = %(zipcode)s,
                            primary_contact_name = %(primary_contact_name)s,
                            primary_contact_email = %(primary_contact_email)s,
                            billing_install_cost = %(billing_install_cost)s,
                            details_provider = %(details_provider)s,
                            details_provider_phone = %(details_provider_phone)s,
                            billing_account = %(billing_account)s,
                            fingerprint = %(fingerprint)s,
                            last_csv_file = %(last_csv_file)s,
                            data_source = %(data_source)s,
                            updated_at = %(updated_at)s
                        WHERE record_number = %(record_number)s
                        AND manual_override IS NOT TRUE
                    """, data)
                    
                    if cursor.rowcount > 0:
                        stats['updated'] += 1
                    else:
                        stats['unchanged'] += 1
                else:
                    # Insert new record
                    # Preserve assigned_to and sctask if they exist
                    data['assigned_to'] = row.get('assigned_to')
                    data['sctask'] = row.get('sctask')
                    data['created_at'] = current_time
                    
                    cursor.execute("""
                        INSERT INTO circuits (
                            record_number, site_name, site_id, circuit_purpose, status, substatus,
                            provider_name, details_service_speed, details_ordered_service_speed,
                            billing_monthly_cost, ip_address_start, date_record_updated,
                            milestone_service_activated, milestone_enabled, assigned_to, sctask,
                            created_at, updated_at, data_source, address_1, city, state, zipcode,
                            primary_contact_name, primary_contact_email, billing_install_cost,
                            target_enablement_date, details_provider, details_provider_phone,
                            billing_account, fingerprint, last_csv_file
                        ) VALUES (
                            %(record_number)s, %(site_name)s, %(site_id)s, %(circuit_purpose)s,
                            %(status)s, %(substatus)s, %(provider_name)s, %(details_service_speed)s,
                            %(details_ordered_service_speed)s, %(billing_monthly_cost)s, %(ip_address_start)s,
                            %(date_record_updated)s, %(milestone_service_activated)s, %(milestone_enabled)s,
                            %(assigned_to)s, %(sctask)s, %(created_at)s, %(updated_at)s, %(data_source)s,
                            %(address_1)s, %(city)s, %(state)s, %(zipcode)s, %(primary_contact_name)s,
                            %(primary_contact_email)s, %(billing_install_cost)s, %(target_enablement_date)s,
                            %(details_provider)s, %(details_provider_phone)s, %(billing_account)s,
                            %(fingerprint)s, %(last_csv_file)s
                        )
                    """, data)
                    
                    stats['inserted'] += 1
                    logger.info(f"Inserted new circuit: {record_num} ({data['site_name']})")
                    
            except Exception as e:
                logger.error(f"Error processing record {record_num}: {e}")
                stats['errors'] += 1
                conn.rollback()
                continue
                
            stats['processed'] += 1
            
            # Commit every 500 records
            if stats['processed'] % 500 == 0:
                conn.commit()
                logger.info(f"Progress: {stats['processed']}/{len(seen_record_numbers)} records processed")
        
        # Final commit
        conn.commit()
        
        # Clear notes for enabled/cancelled circuits
        logger.info("Clearing notes for enabled/cancelled circuits...")
        cursor.execute("""
            UPDATE circuits 
            SET notes = NULL 
            WHERE (status ILIKE '%enabled%' OR status ILIKE '%cancelled%' OR status ILIKE '%canceled%') 
            AND notes IS NOT NULL
        """)
        cleared_notes = cursor.rowcount
        
        # Update daily summary
        logger.info("Updating daily summary...")
        cursor.execute("""
            INSERT INTO daily_summaries (
                summary_date, total_circuits, enabled_count, ready_count,
                customer_action_count, construction_count, planning_count,
                csv_file_processed, processing_time_seconds, created_at
            )
            SELECT
                CURRENT_DATE as summary_date,
                COUNT(*) as total_circuits,
                COUNT(*) FILTER (WHERE status ILIKE '%enabled%' OR status ILIKE '%activated%') as enabled_count,
                COUNT(*) FILTER (WHERE status ILIKE '%ready%') as ready_count,
                COUNT(*) FILTER (WHERE status ILIKE '%customer action%') as customer_action_count,
                COUNT(*) FILTER (WHERE status ILIKE '%construction%') as construction_count,
                COUNT(*) FILTER (WHERE status ILIKE '%planning%') as planning_count,
                %s as csv_file_processed,
                %s as processing_time_seconds,
                NOW() as created_at
            FROM circuits
            ON CONFLICT (summary_date) DO UPDATE SET
                total_circuits = EXCLUDED.total_circuits,
                enabled_count = EXCLUDED.enabled_count,
                ready_count = EXCLUDED.ready_count,
                customer_action_count = EXCLUDED.customer_action_count,
                construction_count = EXCLUDED.construction_count,
                planning_count = EXCLUDED.planning_count,
                csv_file_processed = EXCLUDED.csv_file_processed,
                processing_time_seconds = EXCLUDED.processing_time_seconds,
                created_at = NOW()
        """, (csv_filename, int((datetime.now() - start_time).total_seconds())))
        
        conn.commit()
        
        # Log final statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("UPDATE COMPLETE - SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Total CSV records: {stats['total_csv_records']}")
        logger.info(f"Processed: {stats['processed']}")
        logger.info(f"Inserted: {stats['inserted']}")
        logger.info(f"Updated: {stats['updated']}")
        logger.info(f"Unchanged: {stats['unchanged']}")
        logger.info(f"Skipped (no record number): {stats['skipped_no_record_number']}")
        logger.info(f"Skipped (duplicate): {stats['skipped_duplicate']}")
        logger.info(f"Skipped (manual override): {stats['skipped_manual_override']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"Notes cleared: {cleared_notes}")
        logger.info(f"Status changes: {len(stats['status_changes'])}")
        
        if stats['status_changes']:
            logger.info("\nStatus Changes Detail:")
            for change in stats['status_changes'][:20]:  # Show first 20
                logger.info(f"  - {change}")
            if len(stats['status_changes']) > 20:
                logger.info(f"  ... and {len(stats['status_changes']) - 20} more changes")
        
        # Close database connection
        cursor.close()
        conn.close()
        
        logger.info("Circuit update completed successfully\!")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error in circuit update: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

def main():
    """Main function"""
    # Get CSV file from command line or use latest
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Find latest tracking file
        import glob
        tracking_files = glob.glob('/var/www/html/circuitinfo/tracking_data_*.csv')
        if tracking_files:
            csv_file = max(tracking_files, key=os.path.getmtime)
            logger.info(f"No CSV file specified, using latest: {csv_file}")
        else:
            logger.error("No tracking CSV files found\!")
            return 1
    
    # Check if file exists
    if not os.path.exists(csv_file):
        logger.error(f"CSV file not found: {csv_file}")
        return 1
    
    return update_circuits_from_csv(csv_file)

if __name__ == "__main__":
    sys.exit(main())
