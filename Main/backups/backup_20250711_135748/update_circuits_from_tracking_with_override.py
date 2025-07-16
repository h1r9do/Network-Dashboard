#!/usr/bin/env python3
"""
Update circuits from DSR tracking CSV file - Enhanced version with manual override support
This script respects the manual_override flag to prevent overwriting manually managed circuits
Uses record_number as the primary identifier
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection from environment variables"""
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 5432)),
        database=os.environ.get('DB_NAME', 'dsrcircuits'),
        user=os.environ.get('DB_USER', 'dsruser'),
        password=os.environ.get('DB_PASSWORD', 'dsrpass123')
    )

def create_fingerprint(row):
    """Create a unique fingerprint for circuit identification"""
    site_name = str(row.get('site_name', '')).strip()
    site_id = str(row.get('site_id', '')).strip()
    circuit_purpose = str(row.get('circuit_purpose', '')).strip()
    return f"{site_name} < /dev/null | {site_id}|{circuit_purpose}"

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
    """Update circuits database from tracking CSV file with manual override support"""
    logger.info(f"Starting circuit update from CSV: {csv_file_path}")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path, low_memory=False)
        logger.info(f"Loaded {len(df)} records from CSV")
        
        # Clean column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current timestamp
        current_time = datetime.now()
        csv_filename = os.path.basename(csv_file_path)
        
        # First, ensure all existing records have fingerprints
        cursor.execute("""
            UPDATE circuits 
            SET fingerprint = site_name || '|' || site_id || '|' || circuit_purpose
            WHERE fingerprint IS NULL OR fingerprint = ''
        """)
        conn.commit()
        logger.info("Updated fingerprints for existing records")
        
        # Then, get all circuits with manual_override = TRUE
        cursor.execute("""
            SELECT record_number, site_name, circuit_purpose 
            FROM circuits 
            WHERE manual_override = TRUE AND record_number IS NOT NULL
        """)
        manual_override_circuits = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        logger.info(f"Found {len(manual_override_circuits)} circuits with manual override protection")
        
        # Track statistics
        updated_count = 0
        inserted_count = 0
        skipped_count = 0
        seen_record_numbers = set()  # Track record_numbers to avoid duplicates
        duplicate_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            # Skip if no record_number
            record_num = row.get('record_number')
            if pd.isna(record_num) or not record_num:
                logger.debug("Skipping row with no record_number")
                continue
                
            # Skip duplicates within the same CSV based on record_number
            if record_num in seen_record_numbers:
                duplicate_count += 1
                logger.debug(f"Skipping duplicate record_number: {record_num}")
                continue
            seen_record_numbers.add(record_num)
            
            # Check if this circuit has manual override protection
            if record_num in manual_override_circuits:
                site_name, purpose = manual_override_circuits[record_num]
                logger.info(f"Skipping {site_name} ({purpose}) - manual override protection active")
                skipped_count += 1
                continue
            
            # Create fingerprint
            fingerprint = create_fingerprint(row)
            
            # Validate fingerprint
            if not fingerprint or fingerprint == "||" or fingerprint.count(" < /dev/null | ") \!= 2:
                logger.error(f"Invalid fingerprint generated for record {record_num}")
                error_count += 1
                continue
            
            try:
                # Try to update existing record by record_number
                cursor.execute("""
                    UPDATE circuits SET
                        site_name = %s,
                        site_id = %s,
                        circuit_purpose = %s,
                        status = %s,
                        substatus = %s,
                        provider_name = %s,
                        details_service_speed = %s,
                        details_ordered_service_speed = %s,
                        billing_monthly_cost = %s,
                        ip_address_start = %s,
                        date_record_updated = %s,
                        milestone_service_activated = %s,
                        milestone_enabled = %s,
                        address_1 = %s,
                        city = %s,
                        state = %s,
                        zipcode = %s,
                        primary_contact_name = %s,
                        primary_contact_email = %s,
                        billing_install_cost = %s,
                        details_provider = %s,
                        details_provider_phone = %s,
                        billing_account = %s,
                        fingerprint = %s,
                        last_csv_file = %s,
                        data_source = %s,
                        updated_at = %s
                    WHERE record_number = %s AND manual_override IS NOT TRUE
                    AND (
                        status IS DISTINCT FROM %s OR
                        substatus IS DISTINCT FROM %s OR
                        provider_name IS DISTINCT FROM %s OR
                        billing_monthly_cost IS DISTINCT FROM %s OR
                        ip_address_start IS DISTINCT FROM %s OR
                        milestone_service_activated IS DISTINCT FROM %s OR
                        milestone_enabled IS DISTINCT FROM %s
                    )
                """, (
                    row.get('site_name'),
                    row.get('site_id'),
                    row.get('circuit_purpose'),
                    row.get('status'),
                    row.get('substatus'),
                    row.get('provider_name'),
                    normalize_speed(row.get('details_service_speed')),
                    normalize_speed(row.get('details_ordered_service_speed')),
                    float(row.get('billing_monthly_cost', 0)) if pd.notna(row.get('billing_monthly_cost')) else None,
                    row.get('ip_address_start'),
                    parse_date(row.get('date_record_updated')),
                    parse_date(row.get('milestone_service_activated')),
                    parse_date(row.get('milestone_enabled')),
                    row.get('address_1'),
                    row.get('city'),
                    row.get('state'),
                    row.get('zipcode'),
                    row.get('primary_contact_name'),
                    row.get('primary_contact_email'),
                    float(row.get('billing_install_cost', 0)) if pd.notna(row.get('billing_install_cost')) else None,
                    row.get('details_provider'),
                    row.get('details_provider_phone'),
                    row.get('billing_account'),
                    fingerprint,
                    csv_filename,
                    'csv_import',
                    current_time,
                    record_num,
                    # Values for WHERE clause comparison
                    row.get('status'),
                    row.get('substatus'),
                    row.get('provider_name'),
                    float(row.get('billing_monthly_cost', 0)) if pd.notna(row.get('billing_monthly_cost')) else None,
                    row.get('ip_address_start'),
                    parse_date(row.get('milestone_service_activated')),
                    parse_date(row.get('milestone_enabled'))
                ))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                else:
                    # No update made, check if record exists
                    cursor.execute("SELECT 1 FROM circuits WHERE record_number = %s", (record_num,))
                    if not cursor.fetchone():
                        # Insert new record
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
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            record_num,
                            row.get('site_name'),
                            row.get('site_id'),
                            row.get('circuit_purpose'),
                            row.get('status'),
                            row.get('substatus'),
                            row.get('provider_name'),
                            normalize_speed(row.get('details_service_speed')),
                            normalize_speed(row.get('details_ordered_service_speed')),
                            float(row.get('billing_monthly_cost', 0)) if pd.notna(row.get('billing_monthly_cost')) else None,
                            row.get('ip_address_start'),
                            parse_date(row.get('date_record_updated')),
                            parse_date(row.get('milestone_service_activated')),
                            parse_date(row.get('milestone_enabled')),
                            row.get('assigned_to'),
                            row.get('sctask'),
                            current_time,
                            current_time,
                            'csv_import',
                            row.get('address_1'),
                            row.get('city'),
                            row.get('state'),
                            row.get('zipcode'),
                            row.get('primary_contact_name'),
                            row.get('primary_contact_email'),
                            float(row.get('billing_install_cost', 0)) if pd.notna(row.get('billing_install_cost')) else None,
                            parse_date(row.get('target_enablement_date')),
                            row.get('details_provider'),
                            row.get('details_provider_phone'),
                            row.get('billing_account'),
                            fingerprint,
                            csv_filename
                        ))
                        inserted_count += 1
                        
            except Exception as e:
                logger.error(f"Error processing record {record_num}: {e}")
                error_count += 1
                conn.rollback()
                continue
                
        # Clear notes when circuit is enabled or cancelled
        cursor.execute("""
            UPDATE circuits 
            SET notes = NULL 
            WHERE (
                status ILIKE '%enabled%' OR 
                status ILIKE '%cancelled%' OR 
                status ILIKE '%canceled%'
            )
            AND notes IS NOT NULL
        """)
        
        # Update daily summaries
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
                EXTRACT(EPOCH FROM (NOW() - %s)) as processing_time_seconds,
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
        """, (csv_filename, current_time))
        
        # Commit all changes
        conn.commit()
        
        logger.info(f"Database update completed successfully")
        logger.info(f"Statistics: {inserted_count} new circuits, {updated_count} updated circuits")
        logger.info(f"{skipped_count} protected circuits skipped, {duplicate_count} duplicates removed")
        logger.info(f"{error_count} errors encountered")
        
        # Get final statistics
        cursor.execute("SELECT COUNT(*) FROM circuits WHERE manual_override = TRUE")
        protected_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM circuits")
        total_count = cursor.fetchone()[0]
        
        logger.info(f"Total circuits in database: {total_count} ({protected_count} protected)")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating circuits from CSV: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python update_circuits_from_tracking_with_override.py <csv_file_path>")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        sys.exit(1)
    
    success = update_circuits_from_csv(csv_file_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
