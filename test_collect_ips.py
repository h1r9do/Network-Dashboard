#!/usr/bin/env python3
"""
Test IP collection for a few sites
"""

import os
import sys
import requests
import psycopg2
from dotenv import load_dotenv
import logging

# Add the test directory to path for imports
sys.path.append('/usr/local/bin/test')

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
ORG_NAME = "DTC-Store-Inventory-All"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

def get_headers():
    return {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

def make_api_request(url):
    """Make a GET request to the Meraki API"""
    headers = get_headers()
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def get_organization_id():
    """Get the Organization ID"""
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url)
    if not orgs:
        raise ValueError("Failed to retrieve organizations")
    
    for org in orgs:
        if org.get("name") == ORG_NAME:
            return org.get("id")
    raise ValueError(f"Organization '{ORG_NAME}' not found")

def fetch_arin_data(ip):
    """Fetch ARIN data for an IP"""
    if not ip:
        return None
    
    try:
        # Check if it's a private IP
        import ipaddress
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private:
            return "Private Network"
    except:
        return None
    
    # Query ARIN RDAP
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    try:
        resp = requests.get(rdap_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get('network', {}).get('name', 'Unknown')
    except Exception as e:
        logger.error(f"ARIN lookup failed for {ip}: {e}")
        return "Unknown"

def main():
    logger.info("Starting IP collection test...")
    
    try:
        org_id = get_organization_id()
        logger.info(f"Organization ID: {org_id}")
        
        # Get uplink statuses
        url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
        logger.info("Fetching uplink statuses...")
        statuses = make_api_request(url)
        
        if not statuses:
            logger.error("Failed to get uplink statuses")
            return
        
        logger.info(f"Found {len(statuses)} devices with uplink data")
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Process first 10 devices with IPs
        count = 0
        for status in statuses[:50]:  # Check first 50 to find some with IPs
            network_name = status.get('networkName', '')
            serial = status.get('serial', '')
            
            if not network_name or not serial:
                continue
            
            uplinks = status.get('uplinks', [])
            wan1_ip = None
            wan2_ip = None
            wan1_arin = None
            wan2_arin = None
            
            for uplink in uplinks:
                interface = uplink.get('interface', '').lower()
                ip = uplink.get('ip')
                
                if interface == 'wan1' and ip:
                    wan1_ip = ip
                    wan1_arin = fetch_arin_data(ip)
                elif interface == 'wan2' and ip:
                    wan2_ip = ip
                    wan2_arin = fetch_arin_data(ip)
            
            if wan1_ip or wan2_ip:
                logger.info(f"\n{network_name} ({serial}):")
                if wan1_ip:
                    logger.info(f"  WAN1: {wan1_ip} -> {wan1_arin}")
                if wan2_ip:
                    logger.info(f"  WAN2: {wan2_ip} -> {wan2_arin}")
                
                # Update database
                cursor.execute("""
                    UPDATE meraki_inventory 
                    SET wan1_ip = %s, wan1_arin_provider = %s,
                        wan2_ip = %s, wan2_arin_provider = %s
                    WHERE device_serial = %s
                """, (wan1_ip, wan1_arin, wan2_ip, wan2_arin, serial))
                
                count += 1
                if count >= 10:
                    break
        
        conn.commit()
        logger.info(f"\nUpdated {count} devices with IP data")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()