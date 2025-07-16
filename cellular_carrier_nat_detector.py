#!/usr/bin/env python3
"""
Cellular Carrier Detection via NAT Public IP Analysis
Uses Meraki uplink status to find public IPs that private IPs NAT to
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
import psycopg2
from psycopg2.extras import execute_values
import logging

# Add the test directory to path for imports
sys.path.append('/usr/local/bin/test')
from config import Config

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/cellular-nat-detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)

def create_cellular_detection_table():
    """Create table to store cellular detection results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cellular_carrier_detection (
            id SERIAL PRIMARY KEY,
            network_name VARCHAR(255) NOT NULL,
            device_serial VARCHAR(255) NOT NULL,
            wan_interface VARCHAR(10) NOT NULL,
            private_ip VARCHAR(45) NOT NULL,
            public_ip VARCHAR(45),
            detected_carrier VARCHAR(255),
            detection_method VARCHAR(255),
            confidence_score INTEGER,
            arin_provider VARCHAR(255),
            analysis_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(device_serial, wan_interface)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Created cellular_carrier_detection table")

def make_meraki_request(url, method='GET', data=None):
    """Make authenticated request to Meraki API"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            logger.warning(f"Rate limited, waiting {retry_after} seconds")
            time.sleep(retry_after)
            return make_meraki_request(url, method, data)
        
        if response.status_code != 200:
            logger.error(f"API request failed: {response.status_code} - {response.text[:200]}")
            return None
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Meraki API request failed: {e}")
        return None

def get_arin_provider(ip_address):
    """Get provider information from ARIN RDAP API"""
    if not ip_address or ip_address == 'nan':
        return None
    
    try:
        # Skip private IPs
        if ipaddress.ip_address(ip_address).is_private:
            return None
        
        # ARIN RDAP lookup
        url = f"https://rdap.arin.net/registry/ip/{ip_address}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Try to get organization name
            if 'entities' in data:
                for entity in data['entities']:
                    if 'vcardArray' in entity:
                        for vcard_item in entity['vcardArray']:
                            if isinstance(vcard_item, list):
                                for item in vcard_item:
                                    if isinstance(item, list) and len(item) >= 4 and item[0] == 'fn':
                                        return item[3]
            
            # Fallback to network name
            if 'name' in data:
                return data['name']
        
        return None
        
    except Exception as e:
        logger.warning(f"ARIN lookup failed for {ip_address}: {e}")
        return None

def get_device_uplink_status(network_id, device_serial):
    """Get device uplink status including public IPs"""
    url = f"{BASE_URL}/devices/{device_serial}/appliance/uplinks/statuses"
    
    data = make_meraki_request(url)
    if not data:
        return {}
    
    # Create mapping of interface to public IP
    uplinks = {}
    for uplink in data:
        interface = uplink.get('interface', '')
        public_ip = uplink.get('publicIp')
        status = uplink.get('status', '')
        
        if interface and public_ip:
            uplinks[interface] = {
                'public_ip': public_ip,
                'status': status,
                'provider': uplink.get('provider', ''),
                'ip': uplink.get('ip', '')
            }
    
    return uplinks

def detect_carrier_from_arin(arin_provider):
    """Detect carrier from ARIN provider name"""
    if not arin_provider:
        return None, 0
    
    arin_lower = arin_provider.lower()
    
    # Verizon patterns
    if any(term in arin_lower for term in ['verizon', 'cellco', 'vzw', 'mci']):
        return 'VERIZON', 95
    
    # AT&T patterns
    if any(term in arin_lower for term in ['at&t', 'att ', 'sbcis', 'mobility', 'att-']):
        return 'AT&T', 95
    
    # T-Mobile patterns
    if any(term in arin_lower for term in ['t-mobile', 'tmobile', 'tmus', 'metropcs']):
        return 'T-MOBILE', 95
    
    # Sprint patterns (now T-Mobile)
    if any(term in arin_lower for term in ['sprint', 'spcsdns']):
        return 'SPRINT/T-MOBILE', 95
    
    # Charter/Spectrum patterns
    if any(term in arin_lower for term in ['charter', 'spectrum']):
        return 'CHARTER', 90
    
    # Comcast patterns
    if any(term in arin_lower for term in ['comcast']):
        return 'COMCAST', 90
    
    return None, 0

def analyze_device_uplinks(network_name, device_serial, network_id, wan1_ip, wan2_ip):
    """Analyze device uplinks to detect cellular carriers"""
    logger.info(f"Analyzing uplinks for {network_name} ({device_serial})")
    
    # Get uplink status
    uplinks = get_device_uplink_status(network_id, device_serial)
    if not uplinks:
        logger.warning(f"No uplink data available for {network_name}")
        return []
    
    results = []
    
    # Check WAN1
    if wan1_ip and is_private_ip(wan1_ip):
        wan1_data = uplinks.get('wan1', {})
        public_ip = wan1_data.get('public_ip')
        
        analysis_data = {
            'private_ip': wan1_ip,
            'public_ip': public_ip,
            'uplink_status': wan1_data.get('status'),
            'provider_from_api': wan1_data.get('provider')
        }
        
        carrier = None
        confidence = 0
        arin_provider = None
        
        if public_ip:
            # Get ARIN data
            arin_provider = get_arin_provider(public_ip)
            if arin_provider:
                analysis_data['arin_provider'] = arin_provider
                carrier, confidence = detect_carrier_from_arin(arin_provider)
        
        results.append({
            'network_name': network_name,
            'device_serial': device_serial,
            'wan_interface': 'wan1',
            'private_ip': wan1_ip,
            'public_ip': public_ip,
            'detected_carrier': carrier,
            'detection_method': 'arin_public_ip' if carrier else None,
            'confidence_score': confidence,
            'arin_provider': arin_provider,
            'analysis_data': json.dumps(analysis_data)
        })
    
    # Check WAN2
    if wan2_ip and is_private_ip(wan2_ip):
        wan2_data = uplinks.get('wan2', {})
        public_ip = wan2_data.get('public_ip')
        
        analysis_data = {
            'private_ip': wan2_ip,
            'public_ip': public_ip,
            'uplink_status': wan2_data.get('status'),
            'provider_from_api': wan2_data.get('provider')
        }
        
        carrier = None
        confidence = 0
        arin_provider = None
        
        if public_ip:
            # Get ARIN data
            arin_provider = get_arin_provider(public_ip)
            if arin_provider:
                analysis_data['arin_provider'] = arin_provider
                carrier, confidence = detect_carrier_from_arin(arin_provider)
        
        results.append({
            'network_name': network_name,
            'device_serial': device_serial,
            'wan_interface': 'wan2',
            'private_ip': wan2_ip,
            'public_ip': public_ip,
            'detected_carrier': carrier,
            'detection_method': 'arin_public_ip' if carrier else None,
            'confidence_score': confidence,
            'arin_provider': arin_provider,
            'analysis_data': json.dumps(analysis_data)
        })
    
    return results

def get_private_ip_devices():
    """Get devices with private IPs that need analysis"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get devices with private IPs
    cursor.execute("""
        SELECT DISTINCT
            mi.network_name,
            mi.device_serial,
            mi.network_id,
            mi.wan1_ip,
            mi.wan2_ip
        FROM meraki_inventory mi
        WHERE mi.device_model LIKE 'MX%'
        AND mi.device_serial IS NOT NULL
        AND mi.network_id IS NOT NULL
        AND (
            (mi.wan1_ip IS NOT NULL AND 
             (mi.wan1_ip LIKE '192.168.%' OR mi.wan1_ip LIKE '10.%' OR mi.wan1_ip LIKE '172.%'))
            OR
            (mi.wan2_ip IS NOT NULL AND 
             (mi.wan2_ip LIKE '192.168.%' OR mi.wan2_ip LIKE '10.%' OR mi.wan2_ip LIKE '172.%'))
        )
        AND NOT EXISTS (
            SELECT 1 FROM cellular_carrier_detection ccd
            WHERE ccd.device_serial = mi.device_serial
        )
        ORDER BY mi.network_name
        LIMIT 10  -- Start with 10 for testing
    """)
    
    devices = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return devices

def store_detection_results(results):
    """Store carrier detection results in database"""
    if not results:
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for result in results:
        cursor.execute("""
            INSERT INTO cellular_carrier_detection (
                network_name, device_serial, wan_interface, private_ip, public_ip,
                detected_carrier, detection_method, confidence_score, arin_provider,
                analysis_data
            ) VALUES (
                %(network_name)s, %(device_serial)s, %(wan_interface)s, %(private_ip)s, %(public_ip)s,
                %(detected_carrier)s, %(detection_method)s, %(confidence_score)s, %(arin_provider)s,
                %(analysis_data)s
            ) ON CONFLICT (device_serial, wan_interface) DO UPDATE SET
                private_ip = EXCLUDED.private_ip,
                public_ip = EXCLUDED.public_ip,
                detected_carrier = EXCLUDED.detected_carrier,
                detection_method = EXCLUDED.detection_method,
                confidence_score = EXCLUDED.confidence_score,
                arin_provider = EXCLUDED.arin_provider,
                analysis_data = EXCLUDED.analysis_data,
                created_at = CURRENT_TIMESTAMP
        """, result)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"Stored {len(results)} carrier detection results")

def is_private_ip(ip_str):
    """Check if IP is private"""
    try:
        return ipaddress.ip_address(ip_str).is_private
    except:
        return False

def main():
    """Main function to detect cellular carriers via NAT analysis"""
    logger.info("=== Starting NAT-based Cellular Carrier Detection ===")
    
    if not MERAKI_API_KEY:
        logger.error("MERAKI_API_KEY not found in environment")
        return
    
    # Create table if it doesn't exist
    create_cellular_detection_table()
    
    # Get devices to analyze
    devices = get_private_ip_devices()
    logger.info(f"Found {len(devices)} devices with private IPs to analyze")
    
    if not devices:
        logger.info("No devices with private IPs need analysis")
        return
    
    total_results = []
    carriers_found = {}
    
    for i, (network_name, device_serial, network_id, wan1_ip, wan2_ip) in enumerate(devices, 1):
        logger.info(f"Processing device {i}/{len(devices)}: {network_name}")
        
        try:
            results = analyze_device_uplinks(network_name, device_serial, network_id, wan1_ip, wan2_ip)
            
            if results:
                total_results.extend(results)
                store_detection_results(results)
                
                # Log findings
                for r in results:
                    if r['detected_carrier']:
                        logger.info(f"  {r['wan_interface']}: {r['private_ip']} → {r['public_ip']} = {r['detected_carrier']} "
                                  f"(confidence: {r['confidence_score']}%)")
                        carriers_found[r['detected_carrier']] = carriers_found.get(r['detected_carrier'], 0) + 1
                    else:
                        logger.info(f"  {r['wan_interface']}: {r['private_ip']} → {r['public_ip']} = Unable to detect carrier")
                        if r['arin_provider']:
                            logger.info(f"    ARIN provider: {r['arin_provider']}")
            
        except Exception as e:
            logger.error(f"Error analyzing {network_name}: {e}")
        
        # Rate limiting
        time.sleep(1)
    
    # Summary
    logger.info(f"\n=== Carrier Detection Summary ===")
    logger.info(f"Total devices analyzed: {len(devices)}")
    logger.info(f"Total results: {len(total_results)}")
    
    if carriers_found:
        logger.info(f"\nCarriers detected:")
        for carrier, count in sorted(carriers_found.items()):
            logger.info(f"  {carrier}: {count}")
    
    logger.info(f"\n=== NAT-based Cellular Carrier Detection Complete ===")

if __name__ == "__main__":
    main()