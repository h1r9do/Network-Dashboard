#!/usr/bin/env python3
"""
Fix Inventory Serial Numbers and Models
======================================

This script fixes two issues in the inventory_web_format table:
1. Serial numbers showing as "" (two quotes) - converts to empty string
2. Missing model numbers for standalone devices

Run this to immediately fix the display issues while we work on
fixing the root cause in the processing pipeline.
"""

import psycopg2
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Fix inventory serial numbers and models"""
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'dsrcircuits',
        'user': 'dsruser',
        'password': 'T3dC$gLp9'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        logging.info("Starting inventory data fixes...")
        
        # 1. Check current state
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN serial_number = '""' THEN 1 END) as quoted_serials,
                COUNT(CASE WHEN position = 'Standalone' AND (model IS NULL OR model = '') THEN 1 END) as standalone_no_model
            FROM inventory_web_format
        """)
        
        before_stats = cursor.fetchone()
        logging.info(f"Before fixes:")
        logging.info(f"  Total rows: {before_stats[0]}")
        logging.info(f"  Serial numbers with quotes: {before_stats[1]}")
        logging.info(f"  Standalone devices without models: {before_stats[2]}")
        
        # 2. Fix serial numbers - convert "" to empty string
        cursor.execute("""
            UPDATE inventory_web_format
            SET serial_number = ''
            WHERE serial_number = '""'
        """)
        serial_updates = cursor.rowcount
        logging.info(f"Fixed {serial_updates} serial numbers")
        
        # 3. Fix model numbers for modules from comprehensive_device_inventory
        # This requires looking up the original data
        cursor.execute("""
            WITH device_models AS (
                SELECT DISTINCT ON (c.hostname)
                    c.hostname,
                    jsonb_array_elements(c.physical_components->'chassis')->>'model_name' as model
                FROM comprehensive_device_inventory c
                WHERE c.physical_components IS NOT NULL
                AND jsonb_array_length(c.physical_components->'chassis') > 0
            )
            UPDATE inventory_web_format i
            SET model = COALESCE(
                dm.model,
                CASE 
                    WHEN i.hostname LIKE '%2960%' THEN 'WS-C2960X'
                    WHEN i.hostname LIKE '%3130%' THEN 'WS-CBS3130X'
                    WHEN i.hostname LIKE '%N5K%' THEN 'N5K-C5548UP'
                    WHEN i.hostname LIKE '%N7K%' THEN 'N7K-C7010'
                    ELSE i.model
                END
            )
            FROM device_models dm
            WHERE i.hostname = dm.hostname
            AND i.position = 'Standalone'
            AND (i.model IS NULL OR i.model = '')
        """)
        model_updates = cursor.rowcount
        logging.info(f"Fixed {model_updates} standalone device models")
        
        # 4. Check results
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN serial_number = '""' THEN 1 END) as quoted_serials,
                COUNT(CASE WHEN position = 'Standalone' AND (model IS NULL OR model = '') THEN 1 END) as standalone_no_model
            FROM inventory_web_format
        """)
        
        after_stats = cursor.fetchone()
        logging.info(f"\nAfter fixes:")
        logging.info(f"  Total rows: {after_stats[0]}")
        logging.info(f"  Serial numbers with quotes: {after_stats[1]}")
        logging.info(f"  Standalone devices without models: {after_stats[2]}")
        
        # 5. Show some examples of fixed data
        cursor.execute("""
            SELECT site, hostname, parent_hostname, position, model, serial_number
            FROM inventory_web_format
            WHERE serial_number = ''
            AND parent_hostname IS NOT NULL
            LIMIT 5
        """)
        
        logging.info("\nExample fixed records (components with empty serials):")
        for row in cursor.fetchall():
            logging.info(f"  Site: {row[0]}, Parent: {row[2]}, Position: {row[3]}, Model: {row[4]}")
        
        # Commit changes
        conn.commit()
        logging.info("\nAll fixes committed successfully!")
        
        # Additional statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT parent_hostname) as devices_with_components,
                COUNT(CASE WHEN hostname IS NOT NULL AND hostname != '' THEN 1 END) as master_devices,
                COUNT(CASE WHEN parent_hostname IS NOT NULL AND parent_hostname != '' THEN 1 END) as components
            FROM inventory_web_format
        """)
        
        stats = cursor.fetchone()
        logging.info(f"\nInventory statistics:")
        logging.info(f"  Master devices: {stats[1]}")
        logging.info(f"  Devices with components: {stats[0]}")
        logging.info(f"  Total components: {stats[2]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logging.error(f"Error fixing inventory data: {e}")
        raise

if __name__ == '__main__':
    main()