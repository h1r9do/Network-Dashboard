#!/usr/bin/env python3
"""Bulk update Unknown ARIN providers with resume capability"""

import sys
import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import time
import json
import argparse
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_provider_for_ip, get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

PROGRESS_FILE = '/tmp/bulk_update_progress.json'

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'last_serial': None, 'processed': 0, 'updated': 0}

def update_providers_batch(batch_size=100, resume=False):
    """Update Unknown providers in batches"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Load progress if resuming
    progress = load_progress() if resume else {'last_serial': None, 'processed': 0, 'updated': 0}
    
    
    cache = {}
    missing_set = set()
    total_updated = progress['updated']
    total_processed = progress['processed']
    
    try:
        while True:
            # Build query for each iteration
            base_query = """
                SELECT device_serial, network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
                FROM meraki_inventory
                WHERE device_model LIKE %s
                AND (
                    (wan1_arin_provider = 'Unknown' 
                     AND wan1_ip NOT LIKE %s 
                     AND wan1_ip NOT LIKE %s 
                     AND wan1_ip NOT LIKE %s
                     AND wan1_ip NOT LIKE %s 
                     AND wan1_ip <> '')
                    OR
                    (wan2_arin_provider = 'Unknown' 
                     AND wan2_ip NOT LIKE %s 
                     AND wan2_ip NOT LIKE %s 
                     AND wan2_ip NOT LIKE %s
                     AND wan2_ip NOT LIKE %s 
                     AND wan2_ip <> '')
                )
            """
            
            params = ['MX%', '192.168%', '10.%', '172.%', '169.254%', 
                      '192.168%', '10.%', '172.%', '169.254%']
            
            if progress['last_serial']:
                base_query += " AND device_serial > %s"
                params.append(progress['last_serial'])
            
            base_query += " ORDER BY device_serial LIMIT %s"
            params.append(batch_size)
            
            cursor.execute(base_query, params)
            devices = cursor.fetchall()
            
            if not devices:
                logger.info("No more devices to process!")
                break
            
            logger.info(f"Processing batch of {len(devices)} devices...")
            
            updates = []
            rdap_cache_updates = []
            
            for serial, network, wan1_ip, wan2_ip, wan1_provider, wan2_provider in devices:
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
                
                total_processed += 1
                progress['last_serial'] = serial
                
                # Rate limit every 10 lookups
                if total_processed % 10 == 0:
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
                total_updated += len(updates)
            
            # Update RDAP cache
            if rdap_cache_updates:
                execute_values(cursor, """
                    INSERT INTO rdap_cache (ip_address, provider_name)
                    VALUES %s
                    ON CONFLICT (ip_address) DO UPDATE SET
                        provider_name = EXCLUDED.provider_name,
                        last_queried = NOW()
                """, rdap_cache_updates)
                conn.commit()
            
            # Save progress
            progress['processed'] = total_processed
            progress['updated'] = total_updated
            save_progress(progress)
            
            logger.info(f"Progress: Processed {total_processed}, Updated {total_updated}")
            
            # Update last_serial in progress for next iteration
            # The query will be rebuilt with proper params on next loop iteration
            
            # If we got fewer devices than batch size, we're done
            if len(devices) < batch_size:
                break
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted! Progress saved.")
        logger.info(f"Processed: {total_processed}, Updated: {total_updated}")
        logger.info("Run with --resume to continue from where you left off.")
    except Exception as e:
        import traceback
        logger.error(f"Error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.info(f"Progress saved. Processed: {total_processed}, Updated: {total_updated}")
    finally:
        cursor.close()
        conn.close()
    
    return total_processed, total_updated

def main():
    parser = argparse.ArgumentParser(description='Bulk update Unknown ARIN providers')
    parser.add_argument('-b', '--batch-size', type=int, default=100, help='Batch size (default: 100)')
    parser.add_argument('-r', '--resume', action='store_true', help='Resume from last position')
    parser.add_argument('-c', '--clear', action='store_true', help='Clear progress and start fresh')
    
    args = parser.parse_args()
    
    if args.clear and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        logger.info("Progress cleared.")
    
    logger.info("Starting bulk ARIN provider update...")
    if args.resume:
        logger.info("Resuming from previous progress...")
    
    processed, updated = update_providers_batch(args.batch_size, args.resume)
    
    logger.info(f"\nComplete! Total processed: {processed}, Total updated: {updated}")
    
    # Clean up progress file if complete
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    main()