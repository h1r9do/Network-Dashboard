#!/usr/bin/env python3
"""
Sync confirmed enriched circuit data back to circuits table for non-DSR circuits
This ensures manually confirmed data persists in the circuits table
"""

import psycopg2
from psycopg2.extras import execute_batch
import logging
from datetime import datetime
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection(config):
    """Get database connection from config"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', config.SQLALCHEMY_DATABASE_URI)
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

def sync_enriched_to_circuits(conn):
    """
    Sync confirmed enriched data back to circuits table for non-DSR circuits
    This preserves manually edited data from the web interface
    """
    cursor = conn.cursor()
    
    try:
        # Find non-DSR circuits that need updating
        cursor.execute("""
            WITH dsr_sites AS (
                -- Sites that have DSR Primary circuits (these are protected)
                SELECT DISTINCT site_name 
                FROM circuits 
                WHERE circuit_purpose = 'Primary' 
                AND status = 'Enabled'
                AND provider_name NOT LIKE '%Unknown%'
                AND provider_name IS NOT NULL
                AND provider_name != ''
            )
            SELECT 
                c.record_number,
                c.site_name,
                c.circuit_purpose,
                c.provider_name as current_provider,
                c.details_service_speed as current_speed,
                CASE 
                    WHEN c.circuit_purpose = 'Primary' THEN e.wan1_provider
                    ELSE e.wan2_provider
                END as enriched_provider,
                CASE 
                    WHEN c.circuit_purpose = 'Primary' THEN e.wan1_speed
                    ELSE e.wan2_speed
                END as enriched_speed,
                CASE 
                    WHEN c.circuit_purpose = 'Primary' THEN e.wan1_confirmed
                    ELSE e.wan2_confirmed
                END as is_confirmed
            FROM circuits c
            JOIN enriched_circuits e ON c.site_name = e.network_name
            WHERE c.status = 'Enabled'
            AND c.manual_override IS NOT TRUE
            AND c.site_name NOT IN (SELECT site_name FROM dsr_sites)
            AND (
                -- Only update if enriched data is confirmed
                (c.circuit_purpose = 'Primary' AND e.wan1_confirmed = TRUE) OR
                (c.circuit_purpose = 'Secondary' AND e.wan2_confirmed = TRUE)
            )
        """)
        
        updates_to_make = []
        
        for row in cursor.fetchall():
            record_number = row[0]
            site_name = row[1]
            purpose = row[2]
            current_provider = row[3] or ''
            current_speed = row[4] or ''
            enriched_provider = row[5] or ''
            enriched_speed = row[6] or ''
            
            # Check if update is needed
            provider_changed = current_provider.strip() != enriched_provider.strip()
            speed_changed = current_speed.strip() != enriched_speed.strip()
            
            if provider_changed or speed_changed:
                updates_to_make.append({
                    'record_number': record_number,
                    'provider': enriched_provider,
                    'speed': enriched_speed,
                    'site': site_name,
                    'purpose': purpose
                })
        
        if updates_to_make:
            logger.info(f"Found {len(updates_to_make)} non-DSR circuits to update from enriched data")
            
            # Perform batch update
            update_query = """
                UPDATE circuits 
                SET provider_name = %(provider)s,
                    details_service_speed = %(speed)s,
                    updated_at = NOW(),
                    data_source = 'enriched_sync'
                WHERE record_number = %(record_number)s
                AND manual_override IS NOT TRUE
            """
            
            execute_batch(cursor, update_query, updates_to_make)
            
            conn.commit()
            
            # Log updates
            for update in updates_to_make[:10]:  # Show first 10
                logger.info(f"Updated {update['site']} ({update['purpose']}): "
                          f"Provider='{update['provider']}', Speed='{update['speed']}'")
            
            if len(updates_to_make) > 10:
                logger.info(f"... and {len(updates_to_make) - 10} more")
            
            return len(updates_to_make)
        else:
            logger.info("No non-DSR circuits need updating from enriched data")
            return 0
            
    except Exception as e:
        logger.error(f"Error syncing enriched to circuits: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def main():
    """Main function to run as standalone or be called from nightly script"""
    from config import Config
    
    logger.info("=== Starting Enriched to Circuits Sync ===")
    logger.info("Syncing confirmed non-DSR circuit data back to circuits table")
    
    try:
        conn = get_db_connection(Config)
        updates_made = sync_enriched_to_circuits(conn)
        conn.close()
        
        logger.info(f"=== Sync Complete: {updates_made} circuits updated ===")
        return updates_made
        
    except Exception as e:
        logger.error(f"Error during sync: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()