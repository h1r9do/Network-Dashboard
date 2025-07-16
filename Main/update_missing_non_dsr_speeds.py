#!/usr/bin/env python3
"""
Update missing Non-DSR circuit speeds in enriched_circuits table
Finds Non-DSR circuits with speeds in circuits table but missing in enriched_circuits table
"""

import psycopg2
import psycopg2.extras
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/update-non-dsr-speeds.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='T3dC$gLp9'
    )

def update_missing_speeds():
    """Update missing Non-DSR speeds in enriched_circuits table"""
    logger.info("=== Starting Non-DSR Speed Update for Enriched Circuits ===")
    logger.info(f"Timestamp: {datetime.now()}")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                
                # Find Non-DSR circuits with missing speeds in enriched table
                logger.info("Finding Non-DSR circuits with missing speeds in enriched table...")
                cursor.execute("""
                    SELECT 
                        c.site_name,
                        c.provider_name,
                        c.details_ordered_service_speed as circuit_speed,
                        e.wan1_speed as enriched_wan1_speed,
                        e.wan2_speed as enriched_wan2_speed,
                        e.wan1_provider,
                        e.wan2_provider
                    FROM circuits c
                    JOIN enriched_circuits e ON c.site_name = e.network_name
                    WHERE c.data_source = 'Non-DSR' 
                        AND c.details_ordered_service_speed IS NOT NULL 
                        AND c.details_ordered_service_speed <> ''
                        AND (
                            (c.provider_name = e.wan1_provider AND (e.wan1_speed IS NULL OR e.wan1_speed = '')) OR
                            (c.provider_name = e.wan2_provider AND (e.wan2_speed IS NULL OR e.wan2_speed = ''))
                        )
                    ORDER BY c.site_name
                """)
                
                circuits_to_update = cursor.fetchall()
                logger.info(f"Found {len(circuits_to_update)} circuits with missing speeds")
                
                if len(circuits_to_update) == 0:
                    logger.info("No circuits found that need speed updates")
                    return
                
                # Process each circuit
                updates_made = 0
                for circuit in circuits_to_update:
                    site_name = circuit['site_name']
                    provider_name = circuit['provider_name']
                    circuit_speed = circuit['circuit_speed']
                    wan1_provider = circuit['wan1_provider']
                    wan2_provider = circuit['wan2_provider']
                    wan1_speed = circuit['enriched_wan1_speed']
                    wan2_speed = circuit['enriched_wan2_speed']
                    
                    logger.info(f"Processing: {site_name} - {provider_name} ({circuit_speed})")
                    
                    # Determine which WAN to update
                    if provider_name == wan1_provider and (not wan1_speed or wan1_speed == ''):
                        # Update WAN1 speed
                        cursor.execute("""
                            UPDATE enriched_circuits 
                            SET wan1_speed = %s,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE network_name = %s
                        """, (circuit_speed, site_name))
                        
                        logger.info(f"  ✅ Updated WAN1 speed: {site_name} -> {circuit_speed}")
                        updates_made += 1
                        
                    elif provider_name == wan2_provider and (not wan2_speed or wan2_speed == ''):
                        # Update WAN2 speed
                        cursor.execute("""
                            UPDATE enriched_circuits 
                            SET wan2_speed = %s,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE network_name = %s
                        """, (circuit_speed, site_name))
                        
                        logger.info(f"  ✅ Updated WAN2 speed: {site_name} -> {circuit_speed}")
                        updates_made += 1
                    else:
                        logger.info(f"  ⚠️  No matching WAN found for {site_name} - {provider_name}")
                
                # Commit all changes
                conn.commit()
                logger.info(f"✅ Successfully updated {updates_made} enriched circuit records")
                logger.info("=== Non-DSR Speed Update Complete ===")
                
    except Exception as e:
        logger.error(f"Error during speed update: {e}")
        raise

def main():
    """Main function"""
    try:
        update_missing_speeds()
    except Exception as e:
        logger.error(f"Script failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()