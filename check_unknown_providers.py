#!/usr/bin/env python3
"""Check and update Unknown ARIN providers in database"""

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

def check_unknown_counts():
    """Check how many Unknown providers we have"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Count Unknown providers
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN wan1_arin_provider = 'Unknown' AND wan1_ip IS NOT NULL AND wan1_ip != '' THEN 1 ELSE 0 END) as wan1_unknown,
               SUM(CASE WHEN wan2_arin_provider = 'Unknown' AND wan2_ip IS NOT NULL AND wan2_ip != '' THEN 1 ELSE 0 END) as wan2_unknown
        FROM meraki_inventory
        WHERE device_model LIKE 'MX%'
    """)
    
    row = cursor.fetchone()
    total_devices = row[0]
    wan1_unknown = row[1]
    wan2_unknown = row[2]
    
    logger.info(f"Total MX devices: {total_devices}")
    logger.info(f"WAN1 Unknown providers: {wan1_unknown}")
    logger.info(f"WAN2 Unknown providers: {wan2_unknown}")
    
    # Count public IPs with Unknown
    cursor.execute("""
        SELECT COUNT(DISTINCT device_serial)
        FROM meraki_inventory
        WHERE device_model LIKE 'MX%'
        AND (
            (wan1_arin_provider = 'Unknown' 
             AND wan1_ip NOT LIKE '192.168%' 
             AND wan1_ip NOT LIKE '10.%' 
             AND wan1_ip NOT LIKE '172.%' 
             AND wan1_ip NOT LIKE '169.254%'
             AND wan1_ip != '')
            OR
            (wan2_arin_provider = 'Unknown' 
             AND wan2_ip NOT LIKE '192.168%' 
             AND wan2_ip NOT LIKE '10.%' 
             AND wan2_ip NOT LIKE '172.%'
             AND wan2_ip NOT LIKE '169.254%' 
             AND wan2_ip != '')
        )
    """)
    
    public_unknown = cursor.fetchone()[0]
    logger.info(f"Devices with public IPs showing Unknown: {public_unknown}")
    
    cursor.close()
    conn.close()
    
    return wan1_unknown, wan2_unknown, public_unknown

def update_all_unknown_providers(limit=None):
    """Update all Unknown providers with public IPs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all devices with Unknown providers and public IPs
    query = """
        SELECT device_serial, network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
        FROM meraki_inventory
        WHERE device_model LIKE 'MX%'
        AND (
            (wan1_arin_provider = 'Unknown' 
             AND wan1_ip NOT LIKE '192.168%' 
             AND wan1_ip NOT LIKE '10.%' 
             AND wan1_ip NOT LIKE '172.%'
             AND wan1_ip NOT LIKE '169.254%' 
             AND wan1_ip != '')
            OR
            (wan2_arin_provider = 'Unknown' 
             AND wan2_ip NOT LIKE '192.168%' 
             AND wan2_ip NOT LIKE '10.%' 
             AND wan2_ip NOT LIKE '172.%'
             AND wan2_ip NOT LIKE '169.254%' 
             AND wan2_ip != '')
        )
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    devices = cursor.fetchall()
    
    logger.info(f"Found {len(devices)} devices to update")
    
    cache = {}
    missing_set = set()
    updates = []
    rdap_cache_updates = []
    
    for i, (serial, network, wan1_ip, wan2_ip, wan1_provider, wan2_provider) in enumerate(devices):
        wan1_new = wan1_provider
        wan2_new = wan2_provider
        updated = False
        
        # Check WAN1
        if wan1_ip and wan1_provider == 'Unknown' and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.', '169.254']):
            wan1_new = get_provider_for_ip(wan1_ip, cache, missing_set)
            if wan1_new and wan1_new != 'Unknown':
                logger.info(f"{network}: WAN1 {wan1_ip} → {wan1_new}")
                updated = True
                rdap_cache_updates.append((wan1_ip, wan1_new))
        
        # Check WAN2
        if wan2_ip and wan2_provider == 'Unknown' and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.', '169.254']):
            wan2_new = get_provider_for_ip(wan2_ip, cache, missing_set)
            if wan2_new and wan2_new != 'Unknown':
                logger.info(f"{network}: WAN2 {wan2_ip} → {wan2_new}")
                updated = True
                rdap_cache_updates.append((wan2_ip, wan2_new))
        
        # Add to updates if we found providers
        if updated:
            updates.append((wan1_new, wan2_new, datetime.now(), serial))
        
        # Progress update and rate limiting
        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i + 1}/{len(devices)}")
            time.sleep(1)
    
    # Batch update database
    if updates:
        logger.info(f"Updating {len(updates)} devices in database...")
        execute_values(cursor, """
            UPDATE meraki_inventory AS m
            SET wan1_arin_provider = data.wan1_provider,
                wan2_arin_provider = data.wan2_provider,
                last_updated = data.updated
            FROM (VALUES %s) AS data(wan1_provider, wan2_provider, updated, serial)
            WHERE m.device_serial = data.serial
        """, updates)
        
        conn.commit()
        logger.info("Device updates complete!")
    
    # Update RDAP cache
    if rdap_cache_updates:
        logger.info(f"Updating {len(rdap_cache_updates)} entries in RDAP cache...")
        execute_values(cursor, """
            INSERT INTO rdap_cache (ip_address, provider_name)
            VALUES %s
            ON CONFLICT (ip_address) DO UPDATE SET
                provider_name = EXCLUDED.provider_name,
                last_queried = NOW()
        """, rdap_cache_updates)
        conn.commit()
    
    cursor.close()
    conn.close()
    
    return len(updates)

def main():
    """Main function"""
    logger.info("Checking Unknown ARIN providers...")
    
    # Check current counts
    wan1_unknown, wan2_unknown, public_unknown = check_unknown_counts()
    
    if public_unknown > 0:
        logger.info(f"\nUpdating {public_unknown} devices with public IPs showing Unknown...")
        
        # Update all unknown providers
        updated = update_all_unknown_providers()
        
        logger.info(f"\nUpdated {updated} devices")
        
        # Check counts again
        logger.info("\nFinal counts:")
        check_unknown_counts()
    else:
        logger.info("\nNo devices with public IPs showing Unknown providers!")

if __name__ == "__main__":
    main()