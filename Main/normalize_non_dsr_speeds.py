#!/usr/bin/env python3
"""
Normalize G to M speeds for Non-DSR circuits
Converts Gbps values to Mbps for circuits with data_source = 'Non-DSR'
"""

import sys
import os
import re
import logging
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database libraries
import psycopg2
import psycopg2.extras

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='T3dC$gLp9'
    )

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/normalize-non-dsr-speeds.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def convert_g_to_m(value):
    """Convert G to M by multiplying by 1000"""
    if not value or value.strip() == '':
        return value
    
    value = str(value)
    if 'G' in value:
        # Pattern matches like: 1.0G, 10G, 1G, etc.
        value = re.sub(r'(\d+(?:\.\d+)?)G', lambda m: f"{float(m.group(1)) * 1000:.1f}M", value)
    return value

def normalize_non_dsr_speeds():
    """Normalize speeds for Non-DSR circuits"""
    logger.info("=== Starting Non-DSR Speed Normalization ===")
    logger.info(f"Timestamp: {datetime.now()}")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                
                # Find Non-DSR circuits with G speeds
                logger.info("Finding Non-DSR circuits with G speeds...")
                cursor.execute("""
                    SELECT id, site_name, circuit_purpose, provider_name, 
                           details_service_speed, details_ordered_service_speed
                    FROM circuits 
                    WHERE data_source = 'Non-DSR' 
                    AND (details_service_speed LIKE '%G%' OR details_ordered_service_speed LIKE '%G%')
                    ORDER BY site_name, circuit_purpose
                """)
                
                circuits_to_update = cursor.fetchall()
                logger.info(f"Found {len(circuits_to_update)} circuits with G speeds to normalize")
                
                if len(circuits_to_update) == 0:
                    logger.info("No circuits found that need speed normalization")
                    return
                
                # Process each circuit
                updates_made = 0
                for circuit in circuits_to_update:
                    circuit_id = circuit['id']
                    site_name = circuit['site_name']
                    purpose = circuit['circuit_purpose']
                    provider = circuit['provider_name']
                    service_speed = circuit['details_service_speed']
                    ordered_speed = circuit['details_ordered_service_speed']
                    
                    logger.info(f"Processing: {site_name} {purpose} ({provider})")
                    logger.info(f"  Current speeds: service='{service_speed}', ordered='{ordered_speed}'")
                    
                    # Convert speeds
                    new_service_speed = convert_g_to_m(service_speed)
                    new_ordered_speed = convert_g_to_m(ordered_speed)
                    
                    # Check if any changes were made
                    service_changed = new_service_speed != service_speed
                    ordered_changed = new_ordered_speed != ordered_speed
                    
                    if service_changed or ordered_changed:
                        logger.info(f"  New speeds: service='{new_service_speed}', ordered='{new_ordered_speed}'")
                        
                        # Update the database
                        cursor.execute("""
                            UPDATE circuits 
                            SET details_service_speed = %s,
                                details_ordered_service_speed = %s
                            WHERE id = %s
                        """, (new_service_speed, new_ordered_speed, circuit_id))
                        
                        updates_made += 1
                        logger.info(f"  ✅ Updated circuit {circuit_id}")
                    else:
                        logger.info(f"  ℹ️  No changes needed")
                
                # Commit all changes
                conn.commit()
                logger.info(f"✅ Successfully updated {updates_made} circuits")
                logger.info("=== Non-DSR Speed Normalization Complete ===")
                
    except Exception as e:
        logger.error(f"Error during speed normalization: {e}")
        raise

def main():
    """Main function"""
    try:
        normalize_non_dsr_speeds()
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()