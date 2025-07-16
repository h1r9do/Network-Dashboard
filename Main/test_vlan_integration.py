#!/usr/bin/env python3
"""
Test Enhanced Meraki MX script with VLAN/DHCP collection
Extends existing nightly_meraki_db.py with network configuration data
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
from psycopg2.extras import execute_values
import logging

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
        logging.FileHandler('/tmp/test_meraki_vlan_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
ORG_NAME = "DTC-Store-Inventory-All"
BASE_URL = "https://api.meraki.com/api/v1"

# Load API key from environment
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

# Test with limited networks
TEST_NETWORKS = ["AZP 05", "AZP 01", "NEO 07", "COX 01", "CAL W01"]

def get_db_connection():
    """Get database connection"""
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

def make_api_request(url, headers=None, delay=0.3):
    """Make API request with retry logic"""
    if headers is None:
        headers = {
            'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
            'Content-Type': 'application/json'
        }
    
    time.sleep(delay)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 429:
            logger.warning(f"Rate limit hit, waiting 60 seconds...")
            time.sleep(60)
            response = requests.get(url, headers=headers, timeout=30)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def get_organization_id():
    """Get organization ID by name"""
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url)
    
    if orgs:
        for org in orgs:
            if org['name'] == ORG_NAME:
                return org['id']
    return None

def get_all_networks(org_id):
    """Get all networks in organization"""
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    return make_api_request(url)

def get_network_vlans(network_id):
    """Get VLAN configurations for a network"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    return make_api_request(url)

def get_network_wan_ports(network_id):
    """Get WAN port settings for a network"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/ports"
    return make_api_request(url)

def get_network_static_routes(network_id):
    """Get static routes for a network"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/staticRoutes"
    return make_api_request(url)

def get_network_devices(network_id):
    """Get devices for a network"""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    return make_api_request(url)

def store_vlan_data(conn, network_id, network_name, vlans, collection_timestamp):
    """Store VLAN configuration data in database"""
    if not vlans:
        return
    
    cursor = conn.cursor()
    
    # Prepare VLAN data for insertion
    vlan_values = []
    dhcp_option_values = []
    
    for vlan in vlans:
        # Extract DHCP relay servers if present
        dhcp_relay_servers = None
        if 'dhcpRelayServerIps' in vlan and vlan['dhcpRelayServerIps']:
            dhcp_relay_servers = vlan['dhcpRelayServerIps']
        
        vlan_values.append((
            network_id,
            network_name,
            vlan.get('id'),
            vlan.get('name'),
            vlan.get('applianceIp'),
            vlan.get('subnet'),
            vlan.get('groupPolicyId'),
            vlan.get('dnsNameservers'),
            vlan.get('dhcpHandling'),
            vlan.get('dhcpLeaseTime'),
            vlan.get('dhcpBootOptionsEnabled', False),
            dhcp_relay_servers,
            vlan.get('interfaceId'),
            vlan.get('ipv6', {}).get('enabled', False),
            vlan.get('mandatoryDhcp', {}).get('enabled', False),
            json.dumps(vlan.get('reservedIpRanges', [])),
            json.dumps(vlan.get('fixedIpAssignments', {})),
            collection_timestamp
        ))
        
        # Process DHCP options if present
        if 'dhcpOptions' in vlan and vlan['dhcpOptions']:
            for option in vlan['dhcpOptions']:
                dhcp_option_values.append((
                    network_id,
                    vlan.get('id'),
                    option.get('code'),
                    option.get('type'),
                    option.get('value'),
                    collection_timestamp
                ))
    
    try:
        # Insert or update VLAN data
        insert_vlan_query = """
            INSERT INTO network_vlans (
                network_id, network_name, vlan_id, vlan_name, appliance_ip,
                subnet, group_policy_id, dns_nameservers, dhcp_handling,
                dhcp_lease_time, dhcp_boot_options_enabled, dhcp_relay_server_ips,
                interface_id, ipv6_enabled, mandatory_dhcp_enabled,
                reserved_ip_ranges, fixed_ip_assignments, collection_timestamp
            ) VALUES %s
            ON CONFLICT (network_id, vlan_id) DO UPDATE SET
                vlan_name = EXCLUDED.vlan_name,
                appliance_ip = EXCLUDED.appliance_ip,
                subnet = EXCLUDED.subnet,
                group_policy_id = EXCLUDED.group_policy_id,
                dns_nameservers = EXCLUDED.dns_nameservers,
                dhcp_handling = EXCLUDED.dhcp_handling,
                dhcp_lease_time = EXCLUDED.dhcp_lease_time,
                dhcp_boot_options_enabled = EXCLUDED.dhcp_boot_options_enabled,
                dhcp_relay_server_ips = EXCLUDED.dhcp_relay_server_ips,
                interface_id = EXCLUDED.interface_id,
                ipv6_enabled = EXCLUDED.ipv6_enabled,
                mandatory_dhcp_enabled = EXCLUDED.mandatory_dhcp_enabled,
                reserved_ip_ranges = EXCLUDED.reserved_ip_ranges,
                fixed_ip_assignments = EXCLUDED.fixed_ip_assignments,
                last_updated = EXCLUDED.collection_timestamp
        """
        
        execute_values(cursor, insert_vlan_query, vlan_values, template=None, page_size=100)
        
        # Delete existing DHCP options for this network (to handle removed options)
        if dhcp_option_values:
            cursor.execute("""
                DELETE FROM network_dhcp_options 
                WHERE network_id = %s AND collection_timestamp < %s
            """, (network_id, collection_timestamp))
            
            # Insert new DHCP options
            insert_dhcp_query = """
                INSERT INTO network_dhcp_options (
                    network_id, vlan_id, option_code, option_type, 
                    option_value, collection_timestamp
                ) VALUES %s
            """
            execute_values(cursor, insert_dhcp_query, dhcp_option_values)
        
        conn.commit()
        logger.info(f"Stored {len(vlan_values)} VLANs and {len(dhcp_option_values)} DHCP options for {network_name}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing VLAN data for {network_name}: {e}")
    finally:
        cursor.close()

def store_wan_port_data(conn, network_id, network_name, ports, collection_timestamp):
    """Store WAN port configuration data in database"""
    if not ports:
        return
    
    cursor = conn.cursor()
    
    # Prepare port data for insertion
    port_values = []
    
    for port in ports:
        port_values.append((
            network_id,
            network_name,
            port.get('number'),
            port.get('enabled', True),
            port.get('type'),
            port.get('dropUntaggedTraffic', False),
            port.get('vlan'),
            port.get('allowedVlans'),
            collection_timestamp
        ))
    
    try:
        # Insert or update WAN port data
        insert_port_query = """
            INSERT INTO network_wan_ports (
                network_id, network_name, port_number, enabled, port_type,
                drop_untagged_traffic, vlan_id, allowed_vlans, collection_timestamp
            ) VALUES %s
            ON CONFLICT (network_id, port_number) DO UPDATE SET
                enabled = EXCLUDED.enabled,
                port_type = EXCLUDED.port_type,
                drop_untagged_traffic = EXCLUDED.drop_untagged_traffic,
                vlan_id = EXCLUDED.vlan_id,
                allowed_vlans = EXCLUDED.allowed_vlans,
                last_updated = EXCLUDED.collection_timestamp
        """
        
        execute_values(cursor, insert_port_query, port_values)
        conn.commit()
        
        logger.info(f"Stored {len(port_values)} WAN port configurations for {network_name}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing WAN port data for {network_name}: {e}")
    finally:
        cursor.close()

def collect_network_configuration(conn, network, collection_timestamp):
    """Collect and store network configuration data"""
    network_id = network['id']
    network_name = network['name']
    
    logger.info(f"Collecting configuration for network: {network_name}")
    
    # Check if network has MX devices (firewalls)
    devices = get_network_devices(network_id)
    if not devices:
        logger.info(f"No devices found for {network_name}, skipping")
        return
    
    mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
    if not mx_devices:
        logger.info(f"No MX devices found for {network_name}, skipping")
        return
    
    # Collect VLAN configurations
    vlans = get_network_vlans(network_id)
    if vlans:
        logger.info(f"Found {len(vlans)} VLANs for {network_name}")
        store_vlan_data(conn, network_id, network_name, vlans, collection_timestamp)
    
    # Collect WAN port configurations
    wan_ports = get_network_wan_ports(network_id)
    if wan_ports:
        logger.info(f"Found {len(wan_ports)} WAN port configurations for {network_name}")
        store_wan_port_data(conn, network_id, network_name, wan_ports, collection_timestamp)
    
    # Static routes (for future use - not storing yet as test showed 0 routes)
    static_routes = get_network_static_routes(network_id)
    if static_routes:
        logger.info(f"Found {len(static_routes)} static routes for {network_name}")
        # TODO: Add static route storage if needed

def main():
    """Main function to test VLAN/DHCP collection integration"""
    logger.info("Starting enhanced Meraki collection with VLAN/DHCP data...")
    
    # Get organization ID
    org_id = get_organization_id()
    if not org_id:
        logger.error(f"Organization '{ORG_NAME}' not found")
        return
    
    logger.info(f"Found organization ID: {org_id}")
    
    # Get all networks
    all_networks = get_all_networks(org_id)
    if not all_networks:
        logger.error("Failed to retrieve networks")
        return
    
    logger.info(f"Total networks available: {len(all_networks)}")
    
    # Filter for test networks
    test_networks = [n for n in all_networks if n['name'] in TEST_NETWORKS]
    logger.info(f"Testing with {len(test_networks)} networks")
    
    # Connect to database
    conn = get_db_connection()
    collection_timestamp = datetime.now(timezone.utc)
    
    try:
        # Process each test network
        for network in test_networks:
            try:
                collect_network_configuration(conn, network, collection_timestamp)
            except Exception as e:
                logger.error(f"Error processing network {network['name']}: {e}")
                continue
        
        # Print summary
        cursor = conn.cursor()
        
        # VLAN summary
        cursor.execute("""
            SELECT COUNT(*) as vlan_count, 
                   COUNT(DISTINCT network_id) as network_count
            FROM network_vlans 
            WHERE collection_timestamp = %s
        """, (collection_timestamp,))
        vlan_result = cursor.fetchone()
        
        # DHCP options summary
        cursor.execute("""
            SELECT COUNT(*) as option_count,
                   COUNT(DISTINCT option_code) as unique_codes
            FROM network_dhcp_options
            WHERE collection_timestamp = %s
        """, (collection_timestamp,))
        dhcp_result = cursor.fetchone()
        
        # WAN ports summary
        cursor.execute("""
            SELECT COUNT(*) as port_count,
                   COUNT(DISTINCT network_id) as network_count
            FROM network_wan_ports
            WHERE collection_timestamp = %s
        """, (collection_timestamp,))
        port_result = cursor.fetchone()
        
        logger.info("\n" + "="*60)
        logger.info("COLLECTION SUMMARY")
        logger.info("="*60)
        logger.info(f"VLANs collected: {vlan_result[0]} across {vlan_result[1]} networks")
        logger.info(f"DHCP options collected: {dhcp_result[0]} ({dhcp_result[1]} unique codes)")
        logger.info(f"WAN ports collected: {port_result[0]} across {port_result[1]} networks")
        
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error during collection: {e}")
    finally:
        conn.close()
        logger.info("Collection complete!")

if __name__ == "__main__":
    main()