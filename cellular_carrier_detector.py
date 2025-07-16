#!/usr/bin/env python3
"""
Cellular Carrier Detection for Private IPs
Alternative approach using public IP analysis and pattern matching
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
        logging.FileHandler('/var/log/cellular-carrier-detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

# Known cellular IP patterns based on common private IP assignments
CELLULAR_IP_PATTERNS = {
    'verizon': {
        'private_ips': ['192.168.0.151', '192.168.2.122', '192.168.2.125', '192.168.2.139'],
        'public_ip_patterns': ['70.', '71.', '72.', '73.', '74.', '75.', '108.'],
        'dns_patterns': ['myvzw.com', 'verizonwireless.com', 'vzw']
    },
    'att': {
        'private_ips': ['192.168.1.75', '192.168.1.1'],
        'public_ip_patterns': ['107.', '108.', '166.', '12.'],
        'dns_patterns': ['att.net', 'sbcglobal.net', 'att-inet.com']
    },
    'tmobile': {
        'private_ips': ['192.168.2.185', '10.'],
        'public_ip_patterns': ['172.', '100.'],
        'dns_patterns': ['t-mobile.com', 'tmobile.com']
    }
}

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)

def create_carrier_detection_table():
    """Create table to store carrier detection results"""
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
            mac_address VARCHAR(17),
            mac_vendor VARCHAR(255),
            analysis_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(device_serial, wan_interface)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Created cellular_carrier_detection table")

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

def detect_carrier_from_private_ip(private_ip):
    """Detect carrier based on common private IP patterns"""
    for carrier, patterns in CELLULAR_IP_PATTERNS.items():
        if private_ip in patterns['private_ips']:
            return carrier.upper(), 80  # 80% confidence from IP pattern
    return None, 0

def detect_carrier_from_public_ip(public_ip, arin_provider):
    """Detect carrier from public IP and ARIN data"""
    if not public_ip:
        return None, 0
    
    # Check ARIN provider first
    if arin_provider:
        arin_lower = arin_provider.lower()
        if 'verizon' in arin_lower or 'cellco' in arin_lower:
            return 'VERIZON', 95
        elif 'at&t' in arin_lower or 'att ' in arin_lower:
            return 'AT&T', 95
        elif 't-mobile' in arin_lower or 'tmobile' in arin_lower:
            return 'T-MOBILE', 95
    
    # Check IP prefix patterns
    for carrier, patterns in CELLULAR_IP_PATTERNS.items():
        for prefix in patterns['public_ip_patterns']:
            if public_ip.startswith(prefix):
                return carrier.upper(), 60  # 60% confidence from IP prefix
    
    return None, 0

def get_mac_vendor(mac_address):
    """Look up MAC address vendor (OUI lookup)"""
    if not mac_address or len(mac_address) < 8:
        return None
        
    try:
        # Use macvendors.com API
        oui = mac_address.replace(':', '').replace('-', '')[:6]
        url = f"https://api.macvendors.com/{oui}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return response.text.strip()
        
        return None
        
    except Exception as e:
        logger.warning(f"MAC vendor lookup failed for {mac_address}: {e}")
        return None

def get_device_public_ip(network_id, device_serial):
    """Get the public IP that a private IP NATs to"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Try to get the device's public IP
    url = f"{BASE_URL}/networks/{network_id}/devices/{device_serial}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        device_data = response.json()
        # This might have the public IP
        return device_data.get('publicIp')
    
    return None

def analyze_private_ip_device(network_name, device_serial, network_id, wan_interface, private_ip):
    """Analyze a device with private IP to detect carrier"""
    logger.info(f"Analyzing {network_name} {wan_interface}: {private_ip}")
    
    analysis_data = {
        'private_ip': private_ip,
        'detection_attempts': []
    }
    
    # Method 1: Check private IP pattern
    carrier, confidence = detect_carrier_from_private_ip(private_ip)
    if carrier:
        analysis_data['detection_attempts'].append({
            'method': 'private_ip_pattern',
            'carrier': carrier,
            'confidence': confidence
        })
    
    # Method 2: Get public IP and analyze
    public_ip = get_device_public_ip(network_id, device_serial)
    if public_ip:
        analysis_data['public_ip'] = public_ip
        
        # Get ARIN data for public IP
        arin_provider = get_arin_provider(public_ip)
        if arin_provider:
            analysis_data['arin_provider'] = arin_provider
        
        # Detect carrier from public IP
        pub_carrier, pub_confidence = detect_carrier_from_public_ip(public_ip, arin_provider)
        if pub_carrier:
            analysis_data['detection_attempts'].append({
                'method': 'public_ip_analysis',
                'carrier': pub_carrier,
                'confidence': pub_confidence
            })
    
    # Method 3: MAC address vendor (if available)
    # Note: This would require additional API calls to get ARP table
    
    # Determine final carrier with highest confidence
    final_carrier = None
    final_confidence = 0
    detection_method = None
    
    for attempt in analysis_data['detection_attempts']:
        if attempt['confidence'] > final_confidence:
            final_carrier = attempt['carrier']
            final_confidence = attempt['confidence']
            detection_method = attempt['method']
    
    result = {
        'network_name': network_name,
        'device_serial': device_serial,
        'wan_interface': wan_interface,
        'private_ip': private_ip,
        'public_ip': public_ip,
        'detected_carrier': final_carrier,
        'detection_method': detection_method,
        'confidence_score': final_confidence,
        'arin_provider': arin_provider if 'arin_provider' in analysis_data else None,
        'mac_address': None,
        'mac_vendor': None,
        'analysis_data': json.dumps(analysis_data)
    }
    
    return result

def get_private_ip_devices():
    """Get devices with private IPs that need analysis"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
        LIMIT 20  -- Start with 20 for testing
    """)
    
    devices = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return devices

def store_carrier_detection_results(results):
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
                mac_address, mac_vendor, analysis_data
            ) VALUES (
                %(network_name)s, %(device_serial)s, %(wan_interface)s, %(private_ip)s, %(public_ip)s,
                %(detected_carrier)s, %(detection_method)s, %(confidence_score)s, %(arin_provider)s,
                %(mac_address)s, %(mac_vendor)s, %(analysis_data)s
            ) ON CONFLICT (device_serial, wan_interface) DO UPDATE SET
                private_ip = EXCLUDED.private_ip,
                public_ip = EXCLUDED.public_ip,
                detected_carrier = EXCLUDED.detected_carrier,
                detection_method = EXCLUDED.detection_method,
                confidence_score = EXCLUDED.confidence_score,
                arin_provider = EXCLUDED.arin_provider,
                mac_address = EXCLUDED.mac_address,
                mac_vendor = EXCLUDED.mac_vendor,
                analysis_data = EXCLUDED.analysis_data,
                created_at = CURRENT_TIMESTAMP
        """, result)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"Stored {len(results)} carrier detection results")

def main():
    """Main function to detect cellular carriers for private IPs"""
    logger.info("=== Starting Cellular Carrier Detection ===")
    
    if not MERAKI_API_KEY:
        logger.error("MERAKI_API_KEY not found in environment")
        return
    
    # Create table if it doesn't exist
    create_carrier_detection_table()
    
    # Get devices with private IPs
    devices = get_private_ip_devices()
    logger.info(f"Found {len(devices)} devices with private IPs to analyze")
    
    if not devices:
        logger.info("No devices with private IPs need analysis")
        return
    
    total_results = []
    
    for i, (network_name, device_serial, network_id, wan1_ip, wan2_ip) in enumerate(devices, 1):
        logger.info(f"Processing device {i}/{len(devices)}: {network_name}")
        
        results = []
        
        try:
            # Check WAN1
            if wan1_ip and is_private_ip(wan1_ip):
                result = analyze_private_ip_device(network_name, device_serial, network_id, 'wan1', wan1_ip)
                results.append(result)
            
            # Check WAN2
            if wan2_ip and is_private_ip(wan2_ip):
                result = analyze_private_ip_device(network_name, device_serial, network_id, 'wan2', wan2_ip)
                results.append(result)
            
            if results:
                total_results.extend(results)
                store_carrier_detection_results(results)
                
                # Log findings
                for r in results:
                    if r['detected_carrier']:
                        logger.info(f"  {r['wan_interface']}: Detected {r['detected_carrier']} "
                                  f"(confidence: {r['confidence_score']}%, method: {r['detection_method']})")
                    else:
                        logger.info(f"  {r['wan_interface']}: Unable to detect carrier")
                        
        except Exception as e:
            logger.error(f"Error analyzing {network_name}: {e}")
            
        # Rate limiting
        time.sleep(1)
    
    # Summary
    logger.info(f"\n=== Carrier Detection Summary ===")
    logger.info(f"Total devices analyzed: {len(devices)}")
    logger.info(f"Total results: {len(total_results)}")
    
    # Count carriers detected
    carrier_counts = {}
    for result in total_results:
        carrier = result.get('detected_carrier')
        if carrier:
            carrier_counts[carrier] = carrier_counts.get(carrier, 0) + 1
    
    logger.info(f"\nCarriers detected:")
    for carrier, count in sorted(carrier_counts.items()):
        logger.info(f"  {carrier}: {count}")
    
    logger.info(f"\n=== Cellular Carrier Detection Complete ===")

def is_private_ip(ip_str):
    """Check if IP is private"""
    try:
        return ipaddress.ip_address(ip_str).is_private
    except:
        return False

if __name__ == "__main__":
    main()