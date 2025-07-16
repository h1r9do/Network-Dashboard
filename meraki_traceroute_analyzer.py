#!/usr/bin/env python3
"""
Meraki Traceroute Analyzer for Cellular Provider Detection
Uses Meraki API to run traceroutes from devices and analyze first 3 hops
to identify cellular carriers for private IPs
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
        logging.FileHandler('/var/log/meraki-traceroute-analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

# Target public IPs for traceroute (well-known, reliable targets)
TRACEROUTE_TARGETS = [
    "8.8.8.8",      # Google DNS
    "1.1.1.1",      # Cloudflare DNS
    "208.67.222.222" # OpenDNS
]

# Cellular carrier IP patterns (will expand as we discover more)
CARRIER_PATTERNS = {
    'verizon': ['verizon', 'vzw', 'cellco'],
    'att': ['att', 'cingular', 'mobility'],
    'tmobile': ['tmobile', 't-mobile', 'metropcs'],
    'sprint': ['sprint', 'spcsdns'],
    'cricket': ['cricket', 'aio']
}

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)

def create_traceroute_table():
    """Create table to store traceroute results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cellular_traceroute_analysis (
            id SERIAL PRIMARY KEY,
            network_name VARCHAR(255) NOT NULL,
            device_serial VARCHAR(255) NOT NULL,
            wan_interface VARCHAR(10) NOT NULL,  -- 'wan1' or 'wan2'
            private_ip VARCHAR(45) NOT NULL,
            target_ip VARCHAR(45) NOT NULL,
            hop1_ip VARCHAR(45),
            hop1_provider VARCHAR(255),
            hop2_ip VARCHAR(45), 
            hop2_provider VARCHAR(255),
            hop3_ip VARCHAR(45),
            hop3_provider VARCHAR(255),
            detected_carrier VARCHAR(255),
            confidence_score INTEGER,
            traceroute_raw TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(device_serial, wan_interface, private_ip)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Created cellular_traceroute_analysis table")

def make_meraki_request(url, method='GET', data=None):
    """Make authenticated request to Meraki API with rate limiting"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            logger.warning(f"Rate limited, waiting {retry_after} seconds")
            time.sleep(retry_after)
            return make_meraki_request(url, method, data)
            
        response.raise_for_status()
        return response.json() if response.content else {}
        
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
            return "Private IP"
            
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

def run_traceroute(device_serial, target_ip):
    """Run traceroute from Meraki device"""
    url = f"{BASE_URL}/devices/{device_serial}/liveTools/ping"
    
    # Use ping with traceroute option if available, otherwise we'll need to use a different approach
    # For now, let's try the ping tool and see what we get
    data = {
        "target": target_ip,
        "count": 3
    }
    
    # Start the ping tool
    result = make_meraki_request(url, method='POST', data=data)
    
    if not result or 'pingId' not in result:
        logger.error(f"Failed to start ping tool for device {device_serial}")
        return None
        
    ping_id = result['pingId']
    
    # Wait for completion and get results
    status_url = f"{BASE_URL}/devices/{device_serial}/liveTools/ping/{ping_id}"
    
    for attempt in range(30):  # Wait up to 30 seconds
        time.sleep(2)
        status_result = make_meraki_request(status_url)
        
        if status_result and status_result.get('status') == 'complete':
            return status_result
        elif status_result and status_result.get('status') == 'failed':
            logger.error(f"Ping tool failed for device {device_serial}")
            return None
            
    logger.warning(f"Ping tool timed out for device {device_serial}")
    return None

def analyze_network_path(device_serial, target_ip):
    """
    Analyze network path to identify carrier
    Since Meraki API doesn't have direct traceroute, we'll use creative methods
    """
    logger.info(f"Analyzing path from {device_serial} to {target_ip}")
    
    # Try ping tool first
    ping_result = run_traceroute(device_serial, target_ip)
    
    if not ping_result:
        return None
        
    # For now, return basic structure - we'll enhance this based on what data we get
    return {
        'target_ip': target_ip,
        'hop1_ip': None,
        'hop1_provider': None,
        'hop2_ip': None,
        'hop2_provider': None,
        'hop3_ip': None,
        'hop3_provider': None,
        'raw_data': ping_result
    }

def detect_carrier_from_hops(hop1_provider, hop2_provider, hop3_provider):
    """Detect cellular carrier from hop provider names"""
    providers = [p for p in [hop1_provider, hop2_provider, hop3_provider] if p]
    
    for provider in providers:
        provider_lower = provider.lower()
        
        for carrier, patterns in CARRIER_PATTERNS.items():
            if any(pattern in provider_lower for pattern in patterns):
                confidence = 90 if provider == hop1_provider else 70 if provider == hop2_provider else 50
                return carrier.upper(), confidence
                
    return "Unknown", 0

def get_private_ip_devices():
    """Get devices with private IPs that need traceroute analysis"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT
            mi.network_name,
            mi.device_serial,
            mi.wan1_ip,
            mi.wan2_ip
        FROM meraki_inventory mi
        WHERE mi.device_model LIKE 'MX%'
        AND mi.device_serial IS NOT NULL
        AND (
            (mi.wan1_ip IS NOT NULL AND 
             (mi.wan1_ip LIKE '192.168.%' OR mi.wan1_ip LIKE '10.%' OR mi.wan1_ip LIKE '172.%'))
            OR
            (mi.wan2_ip IS NOT NULL AND 
             (mi.wan2_ip LIKE '192.168.%' OR mi.wan2_ip LIKE '10.%' OR mi.wan2_ip LIKE '172.%'))
        )
        AND NOT EXISTS (
            SELECT 1 FROM cellular_traceroute_analysis cta
            WHERE cta.device_serial = mi.device_serial
            AND ((cta.wan_interface = 'wan1' AND cta.private_ip = mi.wan1_ip)
                 OR (cta.wan_interface = 'wan2' AND cta.private_ip = mi.wan2_ip))
        )
        ORDER BY mi.network_name
    """)
    
    devices = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return devices

def analyze_device_traceroutes(network_name, device_serial, wan1_ip, wan2_ip):
    """Analyze traceroutes for a device's WAN interfaces"""
    results = []
    
    # Analyze WAN1 if it's private
    if wan1_ip and is_private_ip(wan1_ip):
        logger.info(f"Analyzing WAN1 for {network_name} ({device_serial}): {wan1_ip}")
        
        for target_ip in TRACEROUTE_TARGETS:
            path_analysis = analyze_network_path(device_serial, target_ip)
            
            if path_analysis:
                # Get ARIN data for hops
                hop1_provider = get_arin_provider(path_analysis['hop1_ip']) if path_analysis['hop1_ip'] else None
                hop2_provider = get_arin_provider(path_analysis['hop2_ip']) if path_analysis['hop2_ip'] else None
                hop3_provider = get_arin_provider(path_analysis['hop3_ip']) if path_analysis['hop3_ip'] else None
                
                # Detect carrier
                carrier, confidence = detect_carrier_from_hops(hop1_provider, hop2_provider, hop3_provider)
                
                result = {
                    'network_name': network_name,
                    'device_serial': device_serial,
                    'wan_interface': 'wan1',
                    'private_ip': wan1_ip,
                    'target_ip': target_ip,
                    'hop1_ip': path_analysis['hop1_ip'],
                    'hop1_provider': hop1_provider,
                    'hop2_ip': path_analysis['hop2_ip'],
                    'hop2_provider': hop2_provider,
                    'hop3_ip': path_analysis['hop3_ip'],
                    'hop3_provider': hop3_provider,
                    'detected_carrier': carrier,
                    'confidence_score': confidence,
                    'traceroute_raw': json.dumps(path_analysis['raw_data'])
                }
                
                results.append(result)
                
            # Rate limiting between requests
            time.sleep(2)
    
    # Analyze WAN2 if it's private
    if wan2_ip and is_private_ip(wan2_ip):
        logger.info(f"Analyzing WAN2 for {network_name} ({device_serial}): {wan2_ip}")
        
        # Similar logic for WAN2
        for target_ip in TRACEROUTE_TARGETS:
            path_analysis = analyze_network_path(device_serial, target_ip)
            
            if path_analysis:
                hop1_provider = get_arin_provider(path_analysis['hop1_ip']) if path_analysis['hop1_ip'] else None
                hop2_provider = get_arin_provider(path_analysis['hop2_ip']) if path_analysis['hop2_ip'] else None
                hop3_provider = get_arin_provider(path_analysis['hop3_ip']) if path_analysis['hop3_ip'] else None
                
                carrier, confidence = detect_carrier_from_hops(hop1_provider, hop2_provider, hop3_provider)
                
                result = {
                    'network_name': network_name,
                    'device_serial': device_serial,
                    'wan_interface': 'wan2',
                    'private_ip': wan2_ip,
                    'target_ip': target_ip,
                    'hop1_ip': path_analysis['hop1_ip'],
                    'hop1_provider': hop1_provider,
                    'hop2_ip': path_analysis['hop2_ip'],
                    'hop2_provider': hop2_provider,
                    'hop3_ip': path_analysis['hop3_ip'],
                    'hop3_provider': hop3_provider,
                    'detected_carrier': carrier,
                    'confidence_score': confidence,
                    'traceroute_raw': json.dumps(path_analysis['raw_data'])
                }
                
                results.append(result)
                
            time.sleep(2)
    
    return results

def is_private_ip(ip_str):
    """Check if IP is private"""
    try:
        return ipaddress.ip_address(ip_str).is_private
    except:
        return False

def store_traceroute_results(results):
    """Store traceroute analysis results in database"""
    if not results:
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for result in results:
        cursor.execute("""
            INSERT INTO cellular_traceroute_analysis (
                network_name, device_serial, wan_interface, private_ip, target_ip,
                hop1_ip, hop1_provider, hop2_ip, hop2_provider, hop3_ip, hop3_provider,
                detected_carrier, confidence_score, traceroute_raw
            ) VALUES (
                %(network_name)s, %(device_serial)s, %(wan_interface)s, %(private_ip)s, %(target_ip)s,
                %(hop1_ip)s, %(hop1_provider)s, %(hop2_ip)s, %(hop2_provider)s, %(hop3_ip)s, %(hop3_provider)s,
                %(detected_carrier)s, %(confidence_score)s, %(traceroute_raw)s
            ) ON CONFLICT (device_serial, wan_interface, private_ip) DO UPDATE SET
                target_ip = EXCLUDED.target_ip,
                hop1_ip = EXCLUDED.hop1_ip,
                hop1_provider = EXCLUDED.hop1_provider,
                hop2_ip = EXCLUDED.hop2_ip,
                hop2_provider = EXCLUDED.hop2_provider,
                hop3_ip = EXCLUDED.hop3_ip,
                hop3_provider = EXCLUDED.hop3_provider,
                detected_carrier = EXCLUDED.detected_carrier,
                confidence_score = EXCLUDED.confidence_score,
                traceroute_raw = EXCLUDED.traceroute_raw
        """, result)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"Stored {len(results)} traceroute analysis results")

def main():
    """Main function to analyze cellular carriers via traceroute"""
    logger.info("=== Starting Cellular Traceroute Analysis ===")
    
    if not MERAKI_API_KEY:
        logger.error("MERAKI_API_KEY not found in environment")
        return
    
    # Create table if it doesn't exist
    create_traceroute_table()
    
    # Get devices with private IPs
    devices = get_private_ip_devices()
    logger.info(f"Found {len(devices)} devices with private IPs to analyze")
    
    if not devices:
        logger.info("No devices with private IPs need analysis")
        return
    
    total_results = []
    
    for i, (network_name, device_serial, wan1_ip, wan2_ip) in enumerate(devices, 1):
        logger.info(f"Processing device {i}/{len(devices)}: {network_name}")
        
        try:
            results = analyze_device_traceroutes(network_name, device_serial, wan1_ip, wan2_ip)
            
            if results:
                total_results.extend(results)
                store_traceroute_results(results)
                logger.info(f"Completed analysis for {network_name}: {len(results)} results")
            else:
                logger.warning(f"No results for {network_name}")
                
        except Exception as e:
            logger.error(f"Error analyzing {network_name}: {e}")
            
        # Rate limiting between devices
        time.sleep(5)
    
    logger.info(f"=== Completed Cellular Traceroute Analysis: {len(total_results)} total results ===")

if __name__ == "__main__":
    main()