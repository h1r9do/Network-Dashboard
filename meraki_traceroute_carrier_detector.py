#!/usr/bin/env python3
"""
Meraki Traceroute-based Cellular Carrier Detection
Uses correct API endpoint with proper sourceInterface parameter
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
        logging.FileHandler('/var/log/meraki-traceroute-carrier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

# Known cellular carrier patterns from DNS names
CARRIER_DNS_PATTERNS = {
    'verizon': [
        'myvzw.com', 'verizonwireless.com', 'vzw.com', 'vzwnet.com',
        'verizon-gni.net', 'cellco.net', 'verizon.net', 'verizon-'
    ],
    'att': [
        'att.net', 'sbcglobal.net', 'att-inet.com', 'wireless.att.net',
        'attwireless.net', 'att.com', 'attens.com'
    ],
    'tmobile': [
        't-mobile.com', 'tmobile.com', 'tmo.blackberry.net',
        'tmus.net', 'metropcs.net', 'sprint.net'
    ]
}

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
            traceroute_hops JSONB,
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
        
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Meraki API request failed: {e}")
        return None

def run_traceroute(device_serial, source_ip, target='8.8.8.8'):
    """Run traceroute from Meraki device using specific source IP"""
    logger.info(f"Starting traceroute from device {device_serial} source {source_ip} to {target}")
    
    # Create traceroute request
    url = f"{BASE_URL}/devices/{device_serial}/liveTools/traceRoute"
    
    data = {
        'target': target,
        'sourceInterface': source_ip
    }
    
    response = make_meraki_request(url, method='POST', data=data)
    
    if not response:
        logger.error(f"No response from traceroute API")
        return None
    
    if response.status_code == 404:
        logger.error(f"Traceroute endpoint not found (404). URL: {url}")
        return None
    
    if response.status_code != 201:
        logger.error(f"Failed to start traceroute: {response.status_code} - {response.text[:200]}")
        return None
    
    try:
        result = response.json()
    except:
        logger.error(f"Failed to parse response: {response.text[:200]}")
        return None
    
    traceroute_id = result.get('traceRouteId')
    
    if not traceroute_id:
        logger.error(f"No traceroute ID returned. Response: {result}")
        return None
    
    logger.info(f"Traceroute started with ID: {traceroute_id}")
    
    # Poll for results
    result_url = f"{BASE_URL}/devices/{device_serial}/liveTools/traceRoute/{traceroute_id}"
    
    for attempt in range(40):  # Poll for up to 2 minutes
        time.sleep(3)
        
        response = make_meraki_request(result_url)
        if not response or response.status_code != 200:
            logger.error(f"Failed to get traceroute results: {response.status_code if response else 'No response'}")
            continue
        
        trace_result = response.json()
        status = trace_result.get('status')
        
        logger.debug(f"Traceroute status: {status}")
        
        if status == 'complete':
            logger.info(f"Traceroute completed successfully")
            return trace_result
        elif status == 'failed':
            error_msg = trace_result.get('error', 'Unknown error')
            logger.error(f"Traceroute failed: {error_msg}")
            logger.error(f"Full response: {json.dumps(trace_result, indent=2)}")
            return None
    
    logger.warning(f"Traceroute timed out after 2 minutes")
    return None

def analyze_traceroute_hops(trace_result):
    """Analyze traceroute hops to identify carrier"""
    if not trace_result or 'results' not in trace_result:
        logger.warning("No results in traceroute data")
        return None, None, 0
    
    hops = trace_result.get('results', [])
    
    if not hops:
        logger.warning("No hops found in traceroute results")
        return None, None, 0
    
    logger.info(f"Analyzing {len(hops)} hops")
    
    # Analyze first 5 hops (some cellular carriers show up in hop 3-4)
    hop_data = []
    for hop in hops[:5]:
        hop_num = hop.get('hop', 0)
        ip = hop.get('ip', '')
        
        if ip and ip != '*':
            hop_info = {
                'hop': hop_num,
                'ip': ip,
                'hostname': None,
                'carrier_detected': None
            }
            
            # Do reverse DNS lookup
            try:
                import socket
                hostname = socket.gethostbyaddr(ip)[0]
                hop_info['hostname'] = hostname
                logger.info(f"Hop {hop_num}: {ip} -> {hostname}")
                
                # Check hostname for carrier patterns
                hostname_lower = hostname.lower()
                for carrier, patterns in CARRIER_DNS_PATTERNS.items():
                    for pattern in patterns:
                        if pattern in hostname_lower:
                            confidence = 95 if hop_num <= 2 else 85 if hop_num <= 3 else 75
                            hop_info['carrier_detected'] = carrier.upper()
                            logger.info(f"Detected {carrier.upper()} from hostname '{hostname}' at hop {hop_num}")
                            return carrier.upper(), hop_data + [hop_info], confidence
                            
            except Exception as e:
                logger.debug(f"No reverse DNS for {ip}: {e}")
            
            hop_data.append(hop_info)
    
    # If no carrier detected from hostnames, log what we found
    logger.info("No carrier detected from hostnames in traceroute")
    for hop in hop_data:
        logger.info(f"  Hop {hop['hop']}: {hop['ip']} -> {hop.get('hostname', 'No PTR record')}")
    
    return None, hop_data, 0

def get_test_device():
    """Get ALB 03 device for testing"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            mi.network_name,
            mi.device_serial,
            mi.wan1_ip,
            mi.wan2_ip
        FROM meraki_inventory mi
        WHERE mi.network_name = 'ALB 03'
        AND mi.device_serial = 'Q2KY-FBAF-VTHH'
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return result

def is_private_ip(ip_str):
    """Check if IP is private"""
    try:
        return ipaddress.ip_address(ip_str).is_private
    except:
        return False

def main():
    """Main function to test traceroute on ALB 03"""
    logger.info("=== Starting Meraki Traceroute Carrier Detection Test ===")
    
    if not MERAKI_API_KEY:
        logger.error("MERAKI_API_KEY not found in environment")
        return
    
    # Create table if it doesn't exist
    create_cellular_detection_table()
    
    # Get ALB 03 device
    device = get_test_device()
    if not device:
        logger.error("Could not find ALB 03 device in database")
        return
    
    network_name, device_serial, wan1_ip, wan2_ip = device
    logger.info(f"Testing {network_name} ({device_serial})")
    logger.info(f"  WAN1: {wan1_ip}")
    logger.info(f"  WAN2: {wan2_ip}")
    
    results = []
    
    # Test WAN2 (private IP)
    if wan2_ip and is_private_ip(wan2_ip):
        logger.info(f"\nTesting traceroute from WAN2 private IP: {wan2_ip}")
        
        trace_result = run_traceroute(device_serial, wan2_ip)
        
        if trace_result:
            logger.info("Traceroute completed, analyzing results...")
            carrier, hop_data, confidence = analyze_traceroute_hops(trace_result)
            
            result = {
                'network_name': network_name,
                'device_serial': device_serial,
                'wan_interface': 'wan2',
                'private_ip': wan2_ip,
                'public_ip': None,
                'detected_carrier': carrier,
                'detection_method': 'traceroute_dns' if carrier else None,
                'confidence_score': confidence,
                'traceroute_hops': json.dumps(hop_data) if hop_data else None
            }
            
            results.append(result)
            
            if carrier:
                logger.info(f"✅ Successfully detected carrier: {carrier} (confidence: {confidence}%)")
            else:
                logger.info("❌ Could not detect carrier from traceroute")
                logger.info(f"Full traceroute result: {json.dumps(trace_result, indent=2)}")
        else:
            logger.error("Traceroute failed")
    
    # Store results
    if results:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for result in results:
            cursor.execute("""
                INSERT INTO cellular_carrier_detection (
                    network_name, device_serial, wan_interface, private_ip, public_ip,
                    detected_carrier, detection_method, confidence_score, traceroute_hops
                ) VALUES (
                    %(network_name)s, %(device_serial)s, %(wan_interface)s, %(private_ip)s, %(public_ip)s,
                    %(detected_carrier)s, %(detection_method)s, %(confidence_score)s, %(traceroute_hops)s
                ) ON CONFLICT (device_serial, wan_interface) DO UPDATE SET
                    private_ip = EXCLUDED.private_ip,
                    public_ip = EXCLUDED.public_ip,
                    detected_carrier = EXCLUDED.detected_carrier,
                    detection_method = EXCLUDED.detection_method,
                    confidence_score = EXCLUDED.confidence_score,
                    traceroute_hops = EXCLUDED.traceroute_hops,
                    created_at = CURRENT_TIMESTAMP
            """, result)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Stored {len(results)} results in database")
    
    logger.info("\n=== Traceroute Test Complete ===")

if __name__ == "__main__":
    main()