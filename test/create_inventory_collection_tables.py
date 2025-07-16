#!/usr/bin/env python3
"""
Create database tables for storing collected inventory
"""

import psycopg2
import logging

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def create_tables():
    """Create inventory collection tables"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Main collection tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_collections (
                id SERIAL PRIMARY KEY,
                collection_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total_devices INTEGER NOT NULL,
                successful_devices INTEGER NOT NULL,
                collection_type VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Collected chassis information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collected_chassis (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER REFERENCES inventory_collections(id),
                hostname VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                description TEXT,
                pid VARCHAR(100),
                vid VARCHAR(50),
                serial_number VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Collected modules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collected_modules (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER REFERENCES inventory_collections(id),
                hostname VARCHAR(255) NOT NULL,
                module_number VARCHAR(10),
                module_name VARCHAR(255),
                module_type VARCHAR(100),
                model VARCHAR(100),
                serial_number VARCHAR(100),
                status VARCHAR(50),
                ports INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Collected SFP/transceivers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collected_sfps (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER REFERENCES inventory_collections(id),
                hostname VARCHAR(255) NOT NULL,
                interface VARCHAR(100),
                sfp_type VARCHAR(100),
                vendor VARCHAR(100),
                part_number VARCHAR(100),
                serial_number VARCHAR(100),
                wavelength VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Collected FEX modules (Nexus 2K)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collected_fex_modules (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER REFERENCES inventory_collections(id),
                parent_hostname VARCHAR(255) NOT NULL,
                fex_number VARCHAR(10),
                fex_hostname VARCHAR(255),
                description TEXT,
                model VARCHAR(100),
                serial_number VARCHAR(100),
                extender_serial VARCHAR(100),
                state VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Power supplies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collected_power_supplies (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER REFERENCES inventory_collections(id),
                hostname VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                description TEXT,
                pid VARCHAR(100),
                serial_number VARCHAR(100),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Fan modules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collected_fans (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER REFERENCES inventory_collections(id),
                hostname VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                description TEXT,
                pid VARCHAR(100),
                serial_number VARCHAR(100),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Raw inventory data (for reference)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collected_raw_inventory (
                id SERIAL PRIMARY KEY,
                collection_id INTEGER REFERENCES inventory_collections(id),
                hostname VARCHAR(255) NOT NULL,
                command VARCHAR(255),
                output TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chassis_collection ON collected_chassis(collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chassis_hostname ON collected_chassis(hostname)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_modules_collection ON collected_modules(collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_modules_hostname ON collected_modules(hostname)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sfps_collection ON collected_sfps(collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sfps_hostname ON collected_sfps(hostname)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fex_collection ON collected_fex_modules(collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fex_parent ON collected_fex_modules(parent_hostname)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_power_collection ON collected_power_supplies(collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_power_hostname ON collected_power_supplies(hostname)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fans_collection ON collected_fans(collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fans_hostname ON collected_fans(hostname)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_collection ON collected_raw_inventory(collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_hostname ON collected_raw_inventory(hostname)")
        
        # Create views for easy querying
        cursor.execute("""
            CREATE OR REPLACE VIEW latest_inventory AS
            SELECT 
                cc.*,
                ic.collection_date
            FROM collected_chassis cc
            JOIN inventory_collections ic ON cc.collection_id = ic.id
            WHERE ic.id = (
                SELECT MAX(id) FROM inventory_collections 
                WHERE successful_devices > 0
            )
        """)
        
        cursor.execute("""
            CREATE OR REPLACE VIEW device_inventory_summary AS
            SELECT 
                COALESCE(cm.hostname, cs.hostname, cf.parent_hostname) as hostname,
                COUNT(DISTINCT cm.id) as module_count,
                COUNT(DISTINCT cs.id) as sfp_count,
                COUNT(DISTINCT cf.id) as fex_count,
                MAX(ic.collection_date) as last_collected
            FROM inventory_collections ic
            LEFT JOIN collected_modules cm ON ic.id = cm.collection_id
            LEFT JOIN collected_sfps cs ON ic.id = cs.collection_id
            LEFT JOIN collected_fex_modules cf ON ic.id = cf.collection_id
            WHERE cm.hostname IS NOT NULL 
               OR cs.hostname IS NOT NULL 
               OR cf.parent_hostname IS NOT NULL
            GROUP BY COALESCE(cm.hostname, cs.hostname, cf.parent_hostname)
        """)
        
        conn.commit()
        logging.info("✅ Created all inventory collection tables")
        
        # Show table info
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'collected_%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        logging.info(f"\n📊 Created {len(tables)} collection tables:")
        for table in tables:
            logging.info(f"   • {table[0]}")
        
    except Exception as e:
        logging.error(f"Table creation failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_tables()