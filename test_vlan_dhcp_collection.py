#!/usr/bin/env python3
"""
Test VLAN/DHCP/IP Collection Script
==================================

Test script to collect VLAN, DHCP, and IP configuration data from 10 Meraki sites.
This script will help determine the data structure needed for database integration.

Based on the existing nightly_meraki_db.py patterns but focused on network configuration data.
"""

import requests
import json
import time
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add the test directory to path for imports (following nightly script pattern)
sys.path.append('/usr/local/bin/test')
from config import Config

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/test_vlan_dhcp_collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Meraki API Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
MERAKI_BASE_URL = 'https://api.meraki.com/api/v1'
ORGANIZATION_ID = "436883"  # DTC-Store-Inventory-All

HEADERS = {
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
    'Content-Type': 'application/json'
}

# Test sites - limiting to 10 sites for testing
TEST_SITES = [
    "AZP 05", "AZP 01", "ALB 01", "CAL W01", "COX 01", 
    "NEO 07", "MNM W01", "INI W01", "MOSW 01", "CAN W02"
]

def make_api_request(url, delay=0.3):
    """Make API request with rate limiting and error handling"""
    time.sleep(delay)
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 429:
            logger.warning("Rate limit hit, waiting 60 seconds...")
            time.sleep(60)
            response = requests.get(url, headers=HEADERS, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {url}: {e}")
        return None

def get_organization_networks():
    """Get all networks in the organization"""
    logger.info("Fetching all networks...")
    url = f"{MERAKI_BASE_URL}/organizations/{ORGANIZATION_ID}/networks"
    return make_api_request(url)

def get_network_devices(network_id):
    """Get devices for a specific network"""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/devices"
    return make_api_request(url)

def get_network_vlans(network_id):
    """Get VLAN configurations for a network"""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/appliance/vlans"
    return make_api_request(url)

def get_network_dhcp_settings(network_id):
    """Get DHCP settings for a network"""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/appliance/dhcp"
    return make_api_request(url)

def get_network_static_routes(network_id):
    """Get static routes for a network"""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/appliance/staticRoutes"
    return make_api_request(url)

def get_network_firewall_rules(network_id):
    """Get L3 firewall rules for a network"""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    return make_api_request(url)

def get_network_wan_settings(network_id):
    """Get WAN port settings for a network"""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/appliance/ports"
    return make_api_request(url)

def get_network_uplink_status(network_id):
    """Get uplink status for a network"""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/appliance/uplinks/statuses"
    return make_api_request(url)

def collect_network_configuration(network):
    """Collect comprehensive network configuration data"""
    logger.info(f"Collecting configuration for network: {network['name']}")
    
    network_id = network['id']
    network_name = network['name']
    
    config_data = {
        'network_id': network_id,
        'network_name': network_name,
        'network_type': network.get('type', ''),
        'timezone': network.get('timeZone', ''),
        'tags': network.get('tags', []),
        'collection_timestamp': datetime.now().isoformat(),
        'devices': [],
        'vlans': [],
        'dhcp_settings': None,
        'static_routes': [],
        'firewall_rules': [],
        'wan_settings': [],
        'uplink_status': []
    }
    
    # Get devices
    devices = get_network_devices(network_id)
    if devices:
        # Filter for MX devices (firewalls/security appliances)
        mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
        config_data['devices'] = mx_devices
        logger.info(f"Found {len(mx_devices)} MX devices in {network_name}")
    
    # Get VLAN configurations
    vlans = get_network_vlans(network_id)
    if vlans:
        config_data['vlans'] = vlans
        logger.info(f"Found {len(vlans)} VLANs in {network_name}")
    
    # Get DHCP settings
    dhcp_settings = get_network_dhcp_settings(network_id)
    if dhcp_settings:
        config_data['dhcp_settings'] = dhcp_settings
        logger.info(f"Retrieved DHCP settings for {network_name}")
    
    # Get static routes
    static_routes = get_network_static_routes(network_id)
    if static_routes:
        config_data['static_routes'] = static_routes
        logger.info(f"Found {len(static_routes)} static routes in {network_name}")
    
    # Get firewall rules
    firewall_rules = get_network_firewall_rules(network_id)
    if firewall_rules:
        config_data['firewall_rules'] = firewall_rules
        logger.info(f"Found {len(firewall_rules)} firewall rules in {network_name}")
    
    # Get WAN settings
    wan_settings = get_network_wan_settings(network_id)
    if wan_settings:
        config_data['wan_settings'] = wan_settings
        logger.info(f"Retrieved WAN settings for {network_name}")
    
    # Get uplink status
    uplink_status = get_network_uplink_status(network_id)
    if uplink_status:
        config_data['uplink_status'] = uplink_status
        logger.info(f"Retrieved uplink status for {network_name}")
    
    return config_data

def main():
    """Main function to test VLAN/DHCP data collection"""
    logger.info("Starting VLAN/DHCP collection test...")
    logger.info(f"Testing {len(TEST_SITES)} sites: {', '.join(TEST_SITES)}")
    
    # Get all networks
    all_networks = get_organization_networks()
    if not all_networks:
        logger.error("Failed to retrieve networks")
        return
    
    logger.info(f"Total networks available: {len(all_networks)}")
    
    # Filter for test sites
    test_networks = []
    for network in all_networks:
        if network['name'] in TEST_SITES:
            test_networks.append(network)
    
    logger.info(f"Found {len(test_networks)} test networks")
    
    # Collect configuration data
    all_config_data = []
    
    for network in test_networks:
        try:
            config_data = collect_network_configuration(network)
            all_config_data.append(config_data)
            logger.info(f"Successfully collected data for {network['name']}")
        except Exception as e:
            logger.error(f"Error collecting data for {network['name']}: {e}")
            continue
    
    # Save to JSON file
    output_file = '/tmp/vlan_dhcp_test_data.json'
    try:
        with open(output_file, 'w') as f:
            json.dump(all_config_data, f, indent=2, default=str)
        logger.info(f"Data saved to {output_file}")
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("COLLECTION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total networks processed: {len(all_config_data)}")
        
        for config in all_config_data:
            logger.info(f"\nNetwork: {config['network_name']}")
            logger.info(f"  - Devices: {len(config['devices'])}")
            logger.info(f"  - VLANs: {len(config['vlans'])}")
            logger.info(f"  - DHCP Settings: {'Yes' if config['dhcp_settings'] else 'No'}")
            logger.info(f"  - Static Routes: {len(config['static_routes'])}")
            logger.info(f"  - Firewall Rules: {len(config['firewall_rules'])}")
            logger.info(f"  - WAN Settings: {len(config['wan_settings'])}")
            logger.info(f"  - Uplink Status: {len(config['uplink_status'])}")
        
        logger.info(f"\nFull data available in: {output_file}")
        
    except Exception as e:
        logger.error(f"Error saving data to file: {e}")

if __name__ == "__main__":
    main()