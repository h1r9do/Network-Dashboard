#!/usr/bin/env python3
"""Add missing provider label columns to meraki_inventory table"""

import sys
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_columns():
    """Add provider label columns for storing parsed notes data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Add columns for parsed notes data
        columns_to_add = [
            ("wan1_provider_label", "VARCHAR(255)"),
            ("wan1_speed_label", "VARCHAR(100)"),
            ("wan2_provider_label", "VARCHAR(255)"),
            ("wan2_speed_label", "VARCHAR(100)"),
            ("device_notes", "TEXT")
        ]
        
        for column_name, data_type in columns_to_add:
            try:
                cursor.execute(f"""
                    ALTER TABLE meraki_inventory 
                    ADD COLUMN IF NOT EXISTS {column_name} {data_type}
                """)
                logger.info(f"Added column {column_name}")
            except Exception as e:
                logger.warning(f"Column {column_name} might already exist: {e}")
        
        conn.commit()
        logger.info("Successfully added provider label columns")
        
        # Verify columns were added
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'meraki_inventory' 
            AND column_name LIKE '%label%'
            ORDER BY column_name
        """)
        
        logger.info("Provider label columns in table:")
        for row in cursor.fetchall():
            logger.info(f"  - {row[0]}")
            
    except Exception as e:
        logger.error(f"Error adding columns: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_columns()