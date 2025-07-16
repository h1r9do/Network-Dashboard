#!/usr/bin/env python3
"""Quick script to update Unknown ARIN providers"""

import sys
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import time
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_provider_for_ip, get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all devices with Unknown providers
    cursor.execute("""
        SELECT device_serial, network_name, wan1_ip, wan2_ip
        FROM meraki_inventory
        WHERE (wan1_arin_provider = 'Unknown' AND wan1_ip IS NOT NULL AND wan1_ip != '')
           OR (wan2_arin_provider = 'Unknown' AND wan2_ip IS NOT NULL AND wan2_ip != '')
        LIMIT 50
    """)
    
    devices = cursor.fetchall()
    logger.info(f"Found {len(devices)} devices with Unknown providers")
    
    cache = {}
    missing_set = set()
    updates = []
    
    for serial, network, wan1_ip, wan2_ip in devices:
        wan1_provider = None
        wan2_provider = None
        
        # Check WAN1
        if wan1_ip and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            wan1_provider = get_provider_for_ip(wan1_ip, cache, missing_set)
            if wan1_provider and wan1_provider != 'Unknown':
                logger.info(f"{network}: WAN1 {wan1_ip} → {wan1_provider}")
        
        # Check WAN2
        if wan2_ip and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            wan2_provider = get_provider_for_ip(wan2_ip, cache, missing_set)
            if wan2_provider and wan2_provider != 'Unknown':
                logger.info(f"{network}: WAN2 {wan2_ip} → {wan2_provider}")
        
        # Add to updates if we found providers
        if wan1_provider or wan2_provider:
            updates.append((
                wan1_provider if wan1_provider else 'Unknown',
                wan2_provider if wan2_provider else 'Unknown',
                datetime.now(),
                serial
            ))
        
        # Rate limit
        if len(updates) % 10 == 0:
            time.sleep(1)
    
    # Batch update
    if updates:
        logger.info(f"Updating {len(updates)} devices...")
        execute_values(cursor, """
            UPDATE meraki_inventory AS m
            SET wan1_arin_provider = CASE WHEN data.wan1_provider != 'Unknown' THEN data.wan1_provider ELSE m.wan1_arin_provider END,
                wan2_arin_provider = CASE WHEN data.wan2_provider != 'Unknown' THEN data.wan2_provider ELSE m.wan2_arin_provider END,
                last_updated = data.updated
            FROM (VALUES %s) AS data(wan1_provider, wan2_provider, updated, serial)
            WHERE m.device_serial = data.serial
        """, updates)
        
        conn.commit()
        logger.info("Update complete!")
    
    # Update RDAP cache
    if cache:
        cache_updates = [(ip, provider) for ip, provider in cache.items() if provider != 'Unknown']
        if cache_updates:
            execute_values(cursor, """
                INSERT INTO rdap_cache (ip_address, provider_name)
                VALUES %s
                ON CONFLICT (ip_address) DO UPDATE SET
                    provider_name = EXCLUDED.provider_name,
                    last_queried = NOW()
            """, cache_updates)
            conn.commit()
            logger.info(f"Updated {len(cache_updates)} entries in RDAP cache")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()