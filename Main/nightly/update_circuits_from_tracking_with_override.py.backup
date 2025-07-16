#!/usr/bin/env python3
"""
Update circuits from DSR tracking CSV file - Enhanced version with manual override support
This script respects the manual_override flag to prevent overwriting manually managed circuits
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values
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
    return f"{site_name}|{site_id}|{circuit_purpose}"

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
            SELECT fingerprint, site_name, circuit_purpose 
            FROM circuits 
            WHERE manual_override = TRUE
        """)
        manual_override_circuits = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        logger.info(f"Found {len(manual_override_circuits)} circuits with manual override protection")
        
        # Prepare data for upsert
        circuit_data = []
        history_data = []
        skipped_count = 0
        seen_fingerprints = set()  # Track fingerprints to avoid duplicates
        duplicate_count = 0
        
        for _, row in df.iterrows():
            # Create fingerprint
            fingerprint = create_fingerprint(row)
            
            # Validate fingerprint
            if not fingerprint or fingerprint == "||" or fingerprint.count('|') != 2:
                logger.error(f"Invalid fingerprint generated for site {row.get('site_name')}, ID {row.get('site_id')}")
                continue
                
            # Skip duplicates within the same CSV
            if fingerprint in seen_fingerprints:
                duplicate_count += 1
                continue
            seen_fingerprints.add(fingerprint)
            
            # Check if this circuit has manual override protection
            if fingerprint in manual_override_circuits:
                site_name, purpose = manual_override_circuits[fingerprint]
                logger.info(f"Skipping {site_name} ({purpose}) - manual override protection active")
                skipped_count += 1
                continue
            
            # Prepare circuit data
            record_data = (
                row.get('record_number'),
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
                current_time,  # created_at
                current_time,  # updated_at
                'csv_import',  # data_source
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
            )
            
            circuit_data.append(record_data)
            
            # Prepare history data
            history_record = (
                row.get('site_name'),
                row.get('site_id'),
                row.get('circuit_purpose'),
                row.get('status'),
                row.get('provider_name'),
                float(row.get('billing_monthly_cost', 0)) if pd.notna(row.get('billing_monthly_cost')) else None,
                row.get('ip_address_start'),
                normalize_speed(row.get('details_ordered_service_speed')),
                parse_date(row.get('milestone_service_activated')),
                current_time.date(),
                current_time
            )
            
            history_data.append(history_record)
        
        # Perform upsert with manual override check
        circuit_upsert_sql = """
        INSERT INTO circuits (
            record_number, site_name, site_id, circuit_purpose, status, substatus,
            provider_name, details_service_speed, details_ordered_service_speed,
            billing_monthly_cost, ip_address_start, date_record_updated,
            milestone_service_activated, milestone_enabled, assigned_to, sctask,
            created_at, updated_at, data_source, address_1, city, state, zipcode,
            primary_contact_name, primary_contact_email, billing_install_cost,
            target_enablement_date, details_provider, details_provider_phone,
            billing_account, fingerprint, last_csv_file
        ) VALUES %s
        ON CONFLICT (site_name, circuit_purpose) DO UPDATE SET
            record_number = EXCLUDED.record_number,
            status = EXCLUDED.status,
            substatus = EXCLUDED.substatus,
            provider_name = EXCLUDED.provider_name,
            details_service_speed = EXCLUDED.details_service_speed,
            details_ordered_service_speed = EXCLUDED.details_ordered_service_speed,
            billing_monthly_cost = EXCLUDED.billing_monthly_cost,
            ip_address_start = EXCLUDED.ip_address_start,
            date_record_updated = EXCLUDED.date_record_updated,
            milestone_service_activated = EXCLUDED.milestone_service_activated,
            milestone_enabled = EXCLUDED.milestone_enabled,
            address_1 = EXCLUDED.address_1,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            zipcode = EXCLUDED.zipcode,
            primary_contact_name = EXCLUDED.primary_contact_name,
            primary_contact_email = EXCLUDED.primary_contact_email,
            billing_install_cost = EXCLUDED.billing_install_cost,
            details_provider = EXCLUDED.details_provider,
            details_provider_phone = EXCLUDED.details_provider_phone,
            billing_account = EXCLUDED.billing_account,
            last_csv_file = EXCLUDED.last_csv_file,
            data_source = EXCLUDED.data_source,
            updated_at = EXCLUDED.updated_at
        WHERE 
            circuits.manual_override IS NOT TRUE AND (
                circuits.status IS DISTINCT FROM EXCLUDED.status OR
                circuits.substatus IS DISTINCT FROM EXCLUDED.substatus OR
                circuits.provider_name IS DISTINCT FROM EXCLUDED.provider_name OR
                circuits.billing_monthly_cost IS DISTINCT FROM EXCLUDED.billing_monthly_cost OR
                circuits.ip_address_start IS DISTINCT FROM EXCLUDED.ip_address_start OR
                circuits.milestone_service_activated IS DISTINCT FROM EXCLUDED.milestone_service_activated OR
                circuits.milestone_enabled IS DISTINCT FROM EXCLUDED.milestone_enabled
            );
        
        -- Clear notes when circuit is enabled or cancelled
        UPDATE circuits 
        SET notes = NULL 
        WHERE fingerprint IN (
            SELECT fingerprint 
            FROM circuits 
            WHERE (
                status ILIKE '%%enabled%%' OR 
                status ILIKE '%%cancelled%%' OR 
                status ILIKE '%%canceled%%'
            )
            AND notes IS NOT NULL
        );
        """
        
        if circuit_data:
            execute_values(cursor, circuit_upsert_sql, circuit_data, page_size=1000)
            logger.info(f"Upserted {len(circuit_data)} circuit records ({skipped_count} skipped due to manual override, {duplicate_count} duplicates removed)")
        
        # Insert history records (including manually overridden circuits for tracking)
        # COMMENTED OUT - circuit_history table has different schema
        # history_insert_sql = """
        # INSERT INTO circuit_history (
        #     site_name, site_id, circuit_purpose, status, provider_name,
        #     billing_monthly_cost, ip_address_start, details_ordered_service_speed,
        #     milestone_service_activated, snapshot_date, created_at
        # ) VALUES %s
        # """
        
        # if history_data:
        #     execute_values(cursor, history_insert_sql, history_data, page_size=1000)
        #     logger.info(f"Inserted {len(history_data)} history records")
        
        # Update daily summaries
        summary_sql = """
        INSERT INTO daily_summaries (
            summary_date, total_circuits, enabled_count, ready_count,
            customer_action_count, construction_count, planning_count,
            csv_file_processed, processing_time_seconds, created_at
        )
        SELECT 
            CURRENT_DATE as summary_date,
            COUNT(*) as total_circuits,
            COUNT(*) FILTER (WHERE status ILIKE '%%enabled%%' OR status ILIKE '%%activated%%') as enabled_count,
            COUNT(*) FILTER (WHERE status ILIKE '%%ready%%') as ready_count,
            COUNT(*) FILTER (WHERE status ILIKE '%%customer action%%') as customer_action_count,
            COUNT(*) FILTER (WHERE status ILIKE '%%construction%%') as construction_count,
            COUNT(*) FILTER (WHERE status ILIKE '%%planning%%') as planning_count,
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
        """
        
        cursor.execute(summary_sql, (csv_filename, current_time))
        
        # Commit transaction
        conn.commit()
        logger.info("Database update completed successfully")
        
        # Check for duplicates after import
        cursor.execute("""
            SELECT site_id, COUNT(*) as cnt
            FROM circuits
            GROUP BY site_id
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 10
        """)
        
        duplicate_results = cursor.fetchall()
        if duplicate_results:
            logger.warning(f"WARNING: Found site_ids with duplicates after import!")
            for site_id, count in duplicate_results:
                logger.warning(f"  Site ID '{site_id}' has {count} records")
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM circuits WHERE updated_at >= %s AND manual_override IS NOT TRUE", (current_time,))
        updated_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM circuits WHERE created_at >= %s", (current_time,))
        new_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM circuits WHERE manual_override = TRUE")
        protected_count = cursor.fetchone()[0]
        
        logger.info(f"Statistics: {new_count} new circuits, {updated_count} updated circuits, {protected_count} protected circuits, {skipped_count} skipped updates")
        
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