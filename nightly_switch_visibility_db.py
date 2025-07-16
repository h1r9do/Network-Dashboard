#!/usr/bin/env python3
"""
NIGHTLY SWITCH PORT VISIBILITY DATA COLLECTION
==============================================

Purpose:
    Automated collection of switch port client data from Meraki API
    Runs nightly to populate the switch_port_clients database table

Process:
    1. Connect to Meraki API using organization credentials
    2. Iterate through all networks in the organization
    3. For each network, get all switches (MS devices)
    4. For each switch, collect connected client information
    5. Update database with current port status
    6. Mark stale entries (not seen in 7 days)

Schedule:
    Runs nightly at 1:30 AM via cron
    
Log Output:
    /var/log/switch-visibility-db.log
"""

import os
import sys
import requests
import logging
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import re
import json
import time
from dotenv import load_dotenv

# Load environment variables from meraki.env
load_dotenv('/usr/local/bin/meraki.env')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/switch-visibility-db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Meraki API configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
MERAKI_BASE_URL = 'https://api.meraki.com/api/v1'
MERAKI_ORG_NAME = 'DTC-Store-Inventory-All'

def get_headers(api_key):
    """Get headers for Meraki API requests"""
    return {
        'X-Cisco-Meraki-API-Key': api_key,
        'Content-Type': 'application/json'
    }

def make_api_request(url, api_key, params=None, max_retries=5):
    """Make a GET request to the Meraki API with retries for rate limiting."""
    headers = get_headers(api_key)
    for attempt in range(max_retries):
        try:
            logger.debug(f"Requesting {url}")
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 429:  # rate limit
                delay = 2 ** attempt
                logger.warning(f"Rate limited. Backing off for {delay}s...")
                time.sleep(delay)
                continue
            resp.raise_for_status()
            time.sleep(0.5)  # Rate limiting - 2 requests per second max
            return resp.json()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                return []
            time.sleep(2 ** attempt)
    return []

def get_db_connection():
    """Get database connection"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
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

def get_mac_manufacturer(mac):
    """Get manufacturer from MAC address OUI"""
    if not mac:
        return 'Unknown'
    
    # Comprehensive OUI mapping based on actual data
    mac_prefixes = {
        # Most common from our data
        '48:25:67': 'Epson',
        'c8:1c:fe': 'SHARP',
        '74:5d:22': 'SHARP',
        'e8:80:88': 'Texas Instruments',
        'e4:55:a8': 'Dedicated Computing',
        '00:07:4d': 'Zebra Technologies',
        '6c:24:08': 'Texas Instruments',
        'e8:05:dc': 'D-Link',
        '10:1e:da': 'Zebra Technologies',
        'a4:60:11': 'Verifone',
        '0c:7b:c8': 'Hon Hai Precision',
        '88:a4:c2': 'Cisco Meraki',
        '2c:ff:65': 'Texas Instruments',
        '00:22:ee': 'Zebra Technologies',
        '60:95:32': 'Zebra Technologies',
        '78:8c:77': 'Lexmark',
        '90:2e:16': 'Cisco Meraki',
        'ec:64:c9': 'Texas Instruments',
        '30:c6:f7': 'Texas Instruments',
        '78:b8:d6': 'Zebra Technologies',
        # Additional common OUIs
        '00:18:0a': 'Cisco Meraki',
        '00:23:ac': 'Cisco',
        '00:0c:29': 'VMware',
        'f4:ce:46': 'Hewlett Packard',
        '00:50:56': 'VMware',
        '00:1b:21': 'Intel',
        '00:15:5d': 'Microsoft',
        '00:0d:3a': 'Microsoft',
        '00:17:88': 'Philips',
        '00:1a:a0': 'Dell',
        '00:21:9b': 'Dell',
        '00:22:19': 'Dell',
        '00:24:e8': 'Dell',
        '00:25:64': 'Dell',
        '98:90:96': 'Dell',
        'b0:83:fe': 'Dell',
        'd0:94:66': 'Dell',
        'f8:b1:56': 'Dell',
        'f8:bc:12': 'Dell',
        '5c:26:0a': 'HP',
        '3c:d9:2b': 'HP',
        '94:57:a5': 'HP',
        'fc:15:b4': 'HP',
        '70:5a:0f': 'HP',
        '00:1f:f3': 'Apple',
        '00:23:32': 'Apple',
        '00:25:4b': 'Apple',
        '3c:07:54': 'Apple',
        '60:03:08': 'Apple',
        '90:27:e4': 'Apple',
        'a8:20:66': 'Apple',
        'f0:18:98': 'Apple'
    }
    
    mac_lower = mac.lower()
    prefix = mac_lower[:8]
    
    return mac_prefixes.get(prefix, 'Unknown')

def get_organizations():
    """Get all organizations"""
    url = f'{MERAKI_BASE_URL}/organizations'
    return make_api_request(url, MERAKI_API_KEY)

def get_organization_id_by_name(org_name):
    """Get organization ID by name"""
    organizations = get_organizations()
    for org in organizations:
        if org['name'] == org_name:
            return org['id']
    logger.error(f"Organization '{org_name}' not found.")
    return None

def get_organization_networks(organization_id):
    """Get all networks for an organization with pagination"""
    networks = []
    per_page = 1000
    starting_after = None
    
    while True:
        params = {'perPage': per_page}
        if starting_after:
            params['startingAfter'] = starting_after
        
        url = f"{MERAKI_BASE_URL}/organizations/{organization_id}/networks"
        page_networks = make_api_request(url, MERAKI_API_KEY, params)
        
        if not page_networks:
            break
            
        networks.extend(page_networks)
        
        if len(page_networks) < per_page:
            break
            
        starting_after = page_networks[-1]['id']
    
    return networks

def get_network_devices(network_id):
    """Get all devices in a network"""
    url = f'{MERAKI_BASE_URL}/networks/{network_id}/devices'
    devices = make_api_request(url, MERAKI_API_KEY)
    if not devices:
        logger.warning(f"Failed to get devices for network {network_id}")
    return devices

def get_device_clients(serial):
    """Get clients connected to a device"""
    url = f'{MERAKI_BASE_URL}/devices/{serial}/clients'
    clients = make_api_request(url, MERAKI_API_KEY)
    if not clients:
        logger.warning(f"Failed to get clients for device {serial}")
    return clients

def process_switch_clients(conn, network_name, device, clients):
    """Process and store switch client data"""
    cursor = conn.cursor()
    processed_count = 0
    
    for client in clients:
        # Skip if no switchport info (wireless clients)
        if 'switchport' not in client:
            continue
        
        try:
            # Extract client data
            port_id = client.get('switchport', 'Unknown')
            hostname = client.get('description', client.get('dhcpHostname', ''))
            ip_address = client.get('ip', '')
            mac_address = client.get('mac', '')
            vlan = client.get('vlan', None)
            manufacturer = get_mac_manufacturer(mac_address)
            description = client.get('notes', '')
            
            # Insert or update the record
            cursor.execute("""
                INSERT INTO switch_port_clients 
                (store_name, switch_name, switch_serial, port_id, hostname, 
                 ip_address, mac_address, vlan, manufacturer, description, 
                 last_seen, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (switch_serial, port_id, mac_address) 
                DO UPDATE SET
                    store_name = EXCLUDED.store_name,
                    switch_name = EXCLUDED.switch_name,
                    hostname = EXCLUDED.hostname,
                    ip_address = EXCLUDED.ip_address,
                    vlan = EXCLUDED.vlan,
                    manufacturer = EXCLUDED.manufacturer,
                    description = EXCLUDED.description,
                    last_seen = NOW(),
                    updated_at = NOW()
            """, (
                network_name,
                device.get('name', ''),
                device['serial'],
                port_id,
                hostname,
                ip_address,
                mac_address,
                vlan,
                manufacturer,
                description
            ))
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing client {client.get('mac', 'unknown')}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    return processed_count

def mark_stale_entries(conn):
    """Mark entries as stale if not seen in 7 days"""
    cursor = conn.cursor()
    
    # For now, we'll just log old entries
    # In production, you might want to move them to an archive table
    cursor.execute("""
        SELECT COUNT(*) 
        FROM switch_port_clients 
        WHERE last_seen < NOW() - INTERVAL '7 days'
    """)
    
    stale_count = cursor.fetchone()[0]
    
    if stale_count > 0:
        logger.info(f"Found {stale_count} stale entries (not seen in 7 days)")
        
        # Optional: Delete very old entries (30+ days)
        cursor.execute("""
            DELETE FROM switch_port_clients 
            WHERE last_seen < NOW() - INTERVAL '30 days'
        """)
        deleted_count = cursor.rowcount
        
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} entries older than 30 days")
            conn.commit()

def main():
    """Main execution function"""
    start_time = time.time()
    logger.info("=== Starting Switch Port Visibility Collection ===")
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Get organization ID
        org_id = get_organization_id_by_name(MERAKI_ORG_NAME)
        if not org_id:
            logger.error(f"Organization '{MERAKI_ORG_NAME}' not found. Exiting.")
            return
        
        logger.info(f"Found organization: {MERAKI_ORG_NAME} (ID: {org_id})")
        
        # Get all networks
        networks = get_organization_networks(org_id)
        logger.info(f"Found {len(networks)} networks to process")
        
        # Process statistics
        total_switches = 0
        total_clients = 0
        networks_processed = 0
        
        # Process each network
        for network in networks:
            network_name = network['name']
            network_id = network['id']
            
            # Skip if network name suggests it's not a store
            if any(skip in network_name.lower() for skip in ['lab', 'test', 'demo', 'temp']):
                logger.debug(f"Skipping non-store network: {network_name}")
                continue
            
            logger.info(f"Processing network: {network_name}")
            
            # Get all devices in the network
            devices = get_network_devices(network_id)
            
            # Process only switches (MS devices)
            network_switches = 0
            network_clients = 0
            
            for device in devices:
                if 'MS' not in device.get('model', ''):
                    continue
                
                switch_name = device.get('name', device['serial'])
                logger.debug(f"  Processing switch: {switch_name} ({device['serial']})")
                
                # Get clients for this switch
                clients = get_device_clients(device['serial'])
                
                if clients:
                    # Process and store client data
                    processed = process_switch_clients(conn, network_name, device, clients)
                    network_clients += processed
                    logger.debug(f"    Found {processed} wired clients")
                
                network_switches += 1
                total_switches += 1
            
            if network_switches > 0:
                logger.info(f"  Processed {network_switches} switches with {network_clients} clients")
                networks_processed += 1
                total_clients += network_clients
        
        # Clean up old entries
        mark_stale_entries(conn)
        
        # Close database connection
        conn.close()
        
        # Final statistics
        elapsed_time = time.time() - start_time
        logger.info("=== Collection Complete ===")
        logger.info(f"Networks processed: {networks_processed}")
        logger.info(f"Total switches: {total_switches}")
        logger.info(f"Total clients: {total_clients}")
        logger.info(f"Execution time: {elapsed_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Fatal error in switch visibility collection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()