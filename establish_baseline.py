#!/usr/bin/env python3
"""
Establish baseline for incremental enrichment script
"""

import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2

def establish_baseline():
    """Create baseline in change tracking table"""
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    cursor = conn.cursor()
    
    # Create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_change_tracking (
            network_name VARCHAR(255) PRIMARY KEY,
            last_device_notes_hash VARCHAR(64),
            last_wan1_ip VARCHAR(45),
            last_wan2_ip VARCHAR(45),
            last_enrichment_run TIMESTAMP,
            dsr_circuits_hash VARCHAR(64)
        )
    """)
    
    # Clear existing tracking data first
    cursor.execute("DELETE FROM enrichment_change_tracking")
    
    # Insert current state as baseline - use DISTINCT ON to handle duplicates
    cursor.execute("""
        INSERT INTO enrichment_change_tracking (
            network_name, 
            last_device_notes_hash, 
            last_wan1_ip, 
            last_wan2_ip, 
            last_enrichment_run,
            dsr_circuits_hash
        )
        SELECT DISTINCT ON (mi.network_name)
            mi.network_name,
            md5(mi.device_notes || COALESCE(mi.wan1_ip, '') || COALESCE(mi.wan2_ip, '')) as current_hash,
            mi.wan1_ip,
            mi.wan2_ip,
            CURRENT_TIMESTAMP,
            ''
        FROM meraki_inventory mi
        WHERE mi.device_model LIKE 'MX%'
        ORDER BY mi.network_name, mi.id
    """)
    
    cursor.execute("SELECT COUNT(*) FROM enrichment_change_tracking")
    count = cursor.fetchone()[0]
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Established baseline for {count} sites in change tracking table")
    print("✅ Next incremental run will only process actual changes")

if __name__ == "__main__":
    establish_baseline()