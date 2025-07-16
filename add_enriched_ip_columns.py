#!/usr/bin/env python3
"""
Add IP address and ARIN columns to enriched_circuits table
"""

import psycopg2
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def add_enriched_ip_columns():
    """Add IP address and ARIN columns to enriched_circuits table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        logger.info("Adding IP address columns to enriched_circuits table...")
        
        alter_statements = [
            "ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS wan1_ip VARCHAR(45)",
            "ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS wan2_ip VARCHAR(45)",
            "ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS wan1_arin_org VARCHAR(200)",
            "ALTER TABLE enriched_circuits ADD COLUMN IF NOT EXISTS wan2_arin_org VARCHAR(200)"
        ]
        
        for stmt in alter_statements:
            cursor.execute(stmt)
            logger.info(f"Executed: {stmt}")
        
        conn.commit()
        logger.info("Successfully added IP columns to enriched_circuits table")
        
        # Verify columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'enriched_circuits' 
            AND column_name LIKE 'wan%'
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        logger.info("Current WAN columns in enriched_circuits:")
        for col in columns:
            logger.info(f"  - {col[0]}")
        
    except Exception as e:
        logger.error(f"Error adding columns: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

def main():
    """Main function"""
    logger.info("Adding IP columns to enriched_circuits table...")
    
    if not add_enriched_ip_columns():
        logger.error("Failed to add IP columns")
        return False
    
    logger.info("Database schema update completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)