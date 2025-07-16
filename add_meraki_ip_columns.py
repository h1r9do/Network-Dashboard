#!/usr/bin/env python3
"""
Add IP address and ARIN columns to meraki_inventory table
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

def add_ip_columns():
    """Add IP address and ARIN columns to meraki_inventory table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Add IP columns
        logger.info("Adding IP address columns to meraki_inventory table...")
        
        alter_statements = [
            "ALTER TABLE meraki_inventory ADD COLUMN IF NOT EXISTS wan1_ip VARCHAR(45)",
            "ALTER TABLE meraki_inventory ADD COLUMN IF NOT EXISTS wan2_ip VARCHAR(45)",
            "ALTER TABLE meraki_inventory ADD COLUMN IF NOT EXISTS wan1_assignment VARCHAR(20)",
            "ALTER TABLE meraki_inventory ADD COLUMN IF NOT EXISTS wan2_assignment VARCHAR(20)",
            "ALTER TABLE meraki_inventory ADD COLUMN IF NOT EXISTS wan1_arin_provider VARCHAR(100)",
            "ALTER TABLE meraki_inventory ADD COLUMN IF NOT EXISTS wan2_arin_provider VARCHAR(100)",
            "ALTER TABLE meraki_inventory ADD COLUMN IF NOT EXISTS wan1_provider_comparison VARCHAR(20)",
            "ALTER TABLE meraki_inventory ADD COLUMN IF NOT EXISTS wan2_provider_comparison VARCHAR(20)"
        ]
        
        for stmt in alter_statements:
            cursor.execute(stmt)
            logger.info(f"Executed: {stmt}")
        
        # Add indexes for performance
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_meraki_inventory_wan1_ip ON meraki_inventory(wan1_ip)",
            "CREATE INDEX IF NOT EXISTS idx_meraki_inventory_wan2_ip ON meraki_inventory(wan2_ip)"
        ]
        
        for stmt in index_statements:
            cursor.execute(stmt)
            logger.info(f"Executed: {stmt}")
        
        conn.commit()
        logger.info("Successfully added IP columns to meraki_inventory table")
        
        # Verify columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'meraki_inventory' 
            AND column_name LIKE 'wan%'
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        logger.info("Current WAN columns in meraki_inventory:")
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

def create_rdap_cache_table():
    """Create RDAP cache table for storing ARIN lookup results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        logger.info("Creating RDAP cache table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rdap_cache (
                id SERIAL PRIMARY KEY,
                ip_address VARCHAR(45) UNIQUE NOT NULL,
                provider_name VARCHAR(200),
                rdap_response JSONB,
                last_queried TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rdap_cache_ip ON rdap_cache(ip_address);
            CREATE INDEX IF NOT EXISTS idx_rdap_cache_provider ON rdap_cache(provider_name);
            CREATE INDEX IF NOT EXISTS idx_rdap_cache_last_queried ON rdap_cache(last_queried);
        """)
        
        conn.commit()
        logger.info("Successfully created RDAP cache table")
        
    except Exception as e:
        logger.error(f"Error creating RDAP cache table: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

def main():
    """Main function"""
    logger.info("Starting database schema update for ARIN integration...")
    
    # Add IP columns
    if not add_ip_columns():
        logger.error("Failed to add IP columns")
        return False
    
    # Create RDAP cache table
    if not create_rdap_cache_table():
        logger.error("Failed to create RDAP cache table")
        return False
    
    logger.info("Database schema update completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)