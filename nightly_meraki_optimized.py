#!/usr/bin/env python3
"""
Optimized Meraki MX script with parallel processing and batch updates
Significant performance improvements over sequential version
"""

import os
import sys
import json
import requests
import re
import time
import ipaddress
from dotenv import load_dotenv
from datetime import datetime, timezone
from fuzzywuzzy import fuzz
import psycopg2
from psycopg2.extras import execute_values, execute_batch
import logging
import concurrent.futures
import threading
from collections import defaultdict

# Add the test directory to path for imports
sys.path.append('/usr/local/bin/test')
from config import Config

# Get database URI from config
SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/meraki-mx-optimized.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
ORG_NAME = "DTC-Store-Inventory-All"
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

# Performance settings
MAX_WORKERS = 10  # Parallel workers for API calls
BATCH_SIZE = 100  # Database batch update size
ARIN_WORKERS = 20  # Parallel workers for ARIN lookups

# Thread-safe caches
ip_cache = {}
cache_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {
    'api_calls': 0,
    'devices_processed': 0,
    'arin_lookups': 0,
    'cache_hits': 0
}

# Import the ARIN lookup functions from the main script
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import (
    KNOWN_IPS, PROVIDER_KEYWORDS, parse_arin_response, 
    normalize_provider, get_canonical_provider, compare_providers,
    parse_raw_notes, fetch_json
)

def increment_stat(stat_name, amount=1):
    """Thread-safe stat increment"""
    with stats_lock:
        stats[stat_name] += amount

def get_db_connection():
    """Get database connection using config"""
    import re
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def get_headers(api_key):
    return {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }

def make_api_request(url, api_key, params=None, max_retries=5):
    """Make a GET request to the Meraki API with retries for rate limiting."""
    increment_stat('api_calls')
    headers = get_headers(api_key)
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 429:  # rate limit
                delay = min(2 ** attempt, 30)  # Cap at 30 seconds
                logger.warning(f"Rate limited. Backing off for {delay}s...")
                time.sleep(delay)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                return []
            time.sleep(2 ** attempt)
    return []

def get_organization_id():
    """Look up the Meraki organization ID by name."""
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url, MERAKI_API_KEY)
    for org in orgs:
        if org.get("name") == ORG_NAME:
            return org.get("id")
    raise ValueError(f"Organization '{ORG_NAME}' not found")

def get_provider_for_ip_cached(ip):
    """Thread-safe cached IP provider lookup"""
    # Check cache first
    with cache_lock:
        if ip in ip_cache:
            increment_stat('cache_hits')
            return ip_cache[ip]
    
    # Check for private IPs
    try:
        ip_addr = ipaddress.ip_address(ip)
        if ip_addr.is_private:
            return "Unknown"
            
        # Special handling for Verizon range
        if ipaddress.IPv4Address("166.80.0.0") <= ip_addr <= ipaddress.IPv4Address("166.80.255.255"):
            provider = "Verizon Business"
            with cache_lock:
                ip_cache[ip] = provider
            return provider
    except ValueError:
        return "Unknown"
    
    # Check known IPs
    if ip in KNOWN_IPS:
        provider = KNOWN_IPS[ip]
        with cache_lock:
            ip_cache[ip] = provider
        return provider
    
    # Perform ARIN lookup
    increment_stat('arin_lookups')
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    
    if not rdap_data:
        return "Unknown"
    
    provider = parse_arin_response(rdap_data)
    
    # Cache the result
    with cache_lock:
        ip_cache[ip] = provider
    
    return provider

def process_device_batch(devices_data):
    """Process a batch of devices in parallel"""
    results = []
    
    # Use thread pool for ARIN lookups
    with concurrent.futures.ThreadPoolExecutor(max_workers=ARIN_WORKERS) as executor:
        # Prepare all IPs that need lookup
        ip_lookups = {}
        for device_data in devices_data:
            wan1_ip = device_data.get('wan1_ip', '')
            wan2_ip = device_data.get('wan2_ip', '')
            
            if wan1_ip and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
                ip_lookups[f"{device_data['serial']}_wan1"] = (wan1_ip, executor.submit(get_provider_for_ip_cached, wan1_ip))
            
            if wan2_ip and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
                ip_lookups[f"{device_data['serial']}_wan2"] = (wan2_ip, executor.submit(get_provider_for_ip_cached, wan2_ip))
        
        # Collect results
        for key, (ip, future) in ip_lookups.items():
            try:
                provider = future.result(timeout=10)
                serial, wan = key.split('_')
                
                # Find the device and update provider
                for device_data in devices_data:
                    if device_data['serial'] == serial:
                        if wan == 'wan1':
                            device_data['wan1_provider'] = provider
                        else:
                            device_data['wan2_provider'] = provider
                        break
            except Exception as e:
                logger.error(f"Error looking up {ip}: {e}")
    
    return devices_data

def batch_update_database(devices_batch, conn):
    """Perform batch database updates"""
    if not devices_batch:
        return
    
    cursor = conn.cursor()
    
    # Prepare data for batch update
    update_data = []
    cache_data = []
    
    for device in devices_batch:
        # Extract device data
        update_data.append((
            device.get('organization_name', 'DTC-Store-Inventory-All'),
            device.get('network_id', ''),
            device.get('network_name', ''),
            device.get('serial', ''),
            device.get('model', ''),
            device.get('name', ''),
            device.get('tags', []),
            device.get('wan1_ip', ''),
            device.get('wan1_assignment', ''),
            device.get('wan1_provider', ''),
            device.get('wan1_comparison', ''),
            device.get('wan2_ip', ''),
            device.get('wan2_assignment', ''),
            device.get('wan2_provider', ''),
            device.get('wan2_comparison', ''),
            datetime.now(timezone.utc)
        ))
        
        # Collect RDAP cache updates
        for wan in ['wan1', 'wan2']:
            ip = device.get(f'{wan}_ip', '')
            provider = device.get(f'{wan}_provider', '')
            if ip and provider and provider != 'Unknown':
                cache_data.append((ip, provider))
    
    # Batch insert/update devices
    execute_values(cursor, """
        INSERT INTO meraki_inventory (
            organization_name, network_id, network_name, device_serial,
            device_model, device_name, device_tags,
            wan1_ip, wan1_assignment, wan1_arin_provider, wan1_provider_comparison,
            wan2_ip, wan2_assignment, wan2_arin_provider, wan2_provider_comparison,
            last_updated
        ) VALUES %s
        ON CONFLICT (device_serial) DO UPDATE SET
            organization_name = EXCLUDED.organization_name,
            network_id = EXCLUDED.network_id,
            network_name = EXCLUDED.network_name,
            device_model = EXCLUDED.device_model,
            device_name = EXCLUDED.device_name,
            device_tags = EXCLUDED.device_tags,
            wan1_ip = EXCLUDED.wan1_ip,
            wan1_assignment = EXCLUDED.wan1_assignment,
            wan1_arin_provider = EXCLUDED.wan1_arin_provider,
            wan1_provider_comparison = EXCLUDED.wan1_provider_comparison,
            wan2_ip = EXCLUDED.wan2_ip,
            wan2_assignment = EXCLUDED.wan2_assignment,
            wan2_arin_provider = EXCLUDED.wan2_arin_provider,
            wan2_provider_comparison = EXCLUDED.wan2_provider_comparison,
            last_updated = EXCLUDED.last_updated
    """, update_data)
    
    # Batch update RDAP cache
    if cache_data:
        execute_values(cursor, """
            INSERT INTO rdap_cache (ip_address, provider_name)
            VALUES %s
            ON CONFLICT (ip_address) DO UPDATE SET
                provider_name = EXCLUDED.provider_name,
                last_queried = NOW()
        """, cache_data)
    
    cursor.close()
    increment_stat('devices_processed', len(devices_batch))

def main():
    logger.info("Starting Optimized Meraki MX Inventory collection")
    start_time = time.time()
    
    try:
        org_id = get_organization_id()
        logger.info(f"Using Organization ID: {org_id}")
        
        # Get database connection
        conn = get_db_connection()
        
        # Load existing RDAP cache
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address, provider_name FROM rdap_cache")
        with cache_lock:
            for ip, provider in cursor.fetchall():
                ip_cache[ip] = provider
        cursor.close()
        logger.info(f"Loaded {len(ip_cache)} IPs from RDAP cache")
        
        # Step 1: Get all uplink statuses in ONE API call
        logger.info("Fetching all uplink statuses (single API call)...")
        uplink_start = time.time()
        url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
        
        all_statuses = []
        params = {'perPage': 1000, 'startingAfter': None}
        
        while True:
            statuses = make_api_request(url, MERAKI_API_KEY, params)
            if not statuses:
                break
            all_statuses.extend(statuses)
            if len(statuses) < params['perPage']:
                break
            if statuses and 'serial' in statuses[-1]:
                params['startingAfter'] = statuses[-1]['serial']
            else:
                break
        
        uplink_time = time.time() - uplink_start
        logger.info(f"Retrieved uplink info for {len(all_statuses)} devices in {uplink_time:.1f}s")
        
        # Build uplink dictionary
        uplink_dict = {}
        for status in all_statuses:
            serial = status.get('serial')
            uplinks = status.get('uplinks', [])
            uplink_dict[serial] = {}
            for uplink in uplinks:
                interface = uplink.get('interface', '').lower()
                if interface in ['wan1', 'wan2']:
                    uplink_dict[serial][interface] = {
                        'ip': uplink.get('ip', ''),
                        'assignment': uplink.get('ipAssignedBy', '')
                    }
        
        # Step 2: Get all networks
        logger.info("Fetching all networks...")
        url = f"{BASE_URL}/organizations/{org_id}/networks"
        networks = []
        params = {'perPage': 1000, 'startingAfter': None}
        
        while True:
            batch = make_api_request(url, MERAKI_API_KEY, params)
            if not batch:
                break
            networks.extend(batch)
            if len(batch) < params['perPage']:
                break
            params['startingAfter'] = batch[-1]['id']
        
        networks.sort(key=lambda net: (net.get('name') or "").strip())
        logger.info(f"Found {len(networks)} networks")
        
        # Step 3: Get devices for all networks in parallel
        logger.info(f"Fetching devices from all networks using {MAX_WORKERS} workers...")
        devices_start = time.time()
        all_devices = []
        device_batch = []
        
        def get_network_devices(network):
            """Get devices for a single network"""
            net_id = network['id']
            net_name = network.get('name', '')
            
            url = f"{BASE_URL}/networks/{net_id}/devices"
            devices = make_api_request(url, MERAKI_API_KEY)
            
            mx_devices = []
            for device in devices:
                if device.get('model', '').startswith('MX'):
                    serial = device.get('serial')
                    
                    # Get uplink data
                    wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
                    wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
                    wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
                    wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')
                    
                    # Parse notes
                    raw_notes = device.get('notes', '') or ''
                    wan1_label, wan1_speed, wan2_label, wan2_speed = parse_raw_notes(raw_notes)
                    
                    device_data = {
                        'organization_name': 'DTC-Store-Inventory-All',
                        'network_id': net_id,
                        'network_name': net_name,
                        'serial': serial,
                        'model': device.get('model', ''),
                        'name': device.get('name', ''),
                        'tags': device.get('tags', []),
                        'wan1_ip': wan1_ip,
                        'wan1_assignment': wan1_assign,
                        'wan1_provider': '',
                        'wan1_comparison': '',
                        'wan1_label': wan1_label,
                        'wan1_speed': wan1_speed,
                        'wan2_ip': wan2_ip,
                        'wan2_assignment': wan2_assign,
                        'wan2_provider': '',
                        'wan2_comparison': '',
                        'wan2_label': wan2_label,
                        'wan2_speed': wan2_speed,
                        'raw_notes': raw_notes
                    }
                    mx_devices.append(device_data)
            
            return mx_devices
        
        # Process networks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_network = {executor.submit(get_network_devices, net): net for net in networks}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_network):
                network = future_to_network[future]
                try:
                    devices = future.result()
                    if devices:
                        device_batch.extend(devices)
                        
                        # Process batch when it reaches BATCH_SIZE
                        if len(device_batch) >= BATCH_SIZE:
                            # Process ARIN lookups for batch
                            processed_batch = process_device_batch(device_batch)
                            
                            # Update comparisons
                            for device in processed_batch:
                                if device.get('wan1_provider'):
                                    device['wan1_comparison'] = compare_providers(
                                        device['wan1_provider'], 
                                        device['wan1_label']
                                    ) or ''
                                if device.get('wan2_provider'):
                                    device['wan2_comparison'] = compare_providers(
                                        device['wan2_provider'], 
                                        device['wan2_label']
                                    ) or ''
                            
                            # Save to database
                            batch_update_database(processed_batch, conn)
                            device_batch = []
                            conn.commit()
                    
                    completed += 1
                    if completed % 50 == 0:
                        logger.info(f"Processed {completed}/{len(networks)} networks, {stats['devices_processed']} devices so far...")
                
                except Exception as e:
                    logger.error(f"Error processing network {network.get('name', 'Unknown')}: {e}")
        
        # Process remaining devices
        if device_batch:
            processed_batch = process_device_batch(device_batch)
            for device in processed_batch:
                if device.get('wan1_provider'):
                    device['wan1_comparison'] = compare_providers(
                        device['wan1_provider'], 
                        device['wan1_label']
                    ) or ''
                if device.get('wan2_provider'):
                    device['wan2_comparison'] = compare_providers(
                        device['wan2_provider'], 
                        device['wan2_label']
                    ) or ''
            batch_update_database(processed_batch, conn)
            conn.commit()
        
        devices_time = time.time() - devices_start
        logger.info(f"Device collection and processing completed in {devices_time:.1f}s")
        
        # Check for new stores that now have Meraki networks
        logger.info("Checking for new stores that now have Meraki networks...")
        try:
            cursor = conn.cursor()
            
            # Build set of network names for fast lookup
            network_names_upper = set()
            for net in networks:
                net_name = (net.get('name') or "").strip().upper()
                if net_name:
                    network_names_upper.add(net_name)
            
            # Get all active new stores
            cursor.execute("""
                SELECT id, site_name 
                FROM new_stores 
                WHERE is_active = TRUE
            """)
            active_new_stores = cursor.fetchall()
            
            if active_new_stores:
                stores_found = 0
                for store_id, site_name in active_new_stores:
                    site_name_upper = site_name.upper()
                    
                    # Check if this store name appears in any network name
                    if any(site_name_upper in net_name for net_name in network_names_upper):
                        cursor.execute("""
                            UPDATE new_stores 
                            SET is_active = FALSE, 
                                meraki_network_found = TRUE, 
                                meraki_found_date = NOW(),
                                updated_at = NOW()
                            WHERE id = %s
                        """, (store_id,))
                        stores_found += 1
                        logger.info(f"New store '{site_name}' found in Meraki - deactivating")
                
                if stores_found > 0:
                    logger.info(f"Deactivated {stores_found} new stores that now have Meraki networks")
                
        except Exception as e:
            logger.error(f"Error checking new stores: {e}")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        # Print statistics
        total_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("Collection Complete - Statistics:")
        logger.info(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        logger.info(f"  API calls: {stats['api_calls']}")
        logger.info(f"  Devices processed: {stats['devices_processed']}")
        logger.info(f"  ARIN lookups: {stats['arin_lookups']}")
        logger.info(f"  Cache hits: {stats['cache_hits']}")
        logger.info(f"  Cache hit rate: {stats['cache_hits']/(stats['arin_lookups']+stats['cache_hits'])*100:.1f}%" if stats['arin_lookups'] + stats['cache_hits'] > 0 else "N/A")
        logger.info(f"  Avg time per device: {total_time/stats['devices_processed']*1000:.0f}ms" if stats['devices_processed'] > 0 else "N/A")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)