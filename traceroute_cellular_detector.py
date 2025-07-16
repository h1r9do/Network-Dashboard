#!/usr/bin/env python3
"""
Traceroute-based Cellular Carrier Detection for Private IPs
Uses Meraki API traceroute to identify carriers by analyzing first 3 hops
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
        logging.FileHandler('/var/log/traceroute-cellular-detector.log'),
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
        'verizon-gni.net', 'cellco.net', 'verizon.net'
    ],
    'att': [
        'att.net', 'sbcglobal.net', 'att-inet.com', 'wireless.att.net',
        'attwireless.net', 'att.com'
    ],
    'tmobile': [
        't-mobile.com', 'tmobile.com', 'tmo.blackberry.net',
        'tmus.net', 'metropcs.net'
    ],
    'sprint': [
        'sprint.net', 'sprintspectrum.com', 'spcsdns.net',
        'sprint.com'
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

def run_traceroute(device_serial, wan_ip):
    """Run traceroute from Meraki device using WAN IP as source"""
    logger.info(f"Running traceroute from device {device_serial} with source {wan_ip}")
    
    # Try the live tools traceroute endpoint
    url = f"{BASE_URL}/devices/{device_serial}/liveTools/traceroute"
    
    data = {
        'target': '8.8.8.8',
        'sourceInterface': wan_ip
    }
    
    response = make_meraki_request(url, method='POST', data=data)
    
    if not response:
        logger.error(f"No response from traceroute API")
        return None
    
    if response.status_code == 404:
        logger.warning(f"Traceroute endpoint not found (404). Device may not support this feature.")
        return None
    
    if response.status_code != 201:
        logger.error(f"Failed to start traceroute: {response.status_code} - {response.text[:200]}")
        return None
    
    result = response.json()
    traceroute_id = result.get('tracerouteId')
    
    if not traceroute_id:
        logger.error(f"No traceroute ID returned")
        return None
    
    logger.info(f"Traceroute started with ID: {traceroute_id}")
    
    # Poll for results
    result_url = f"{BASE_URL}/devices/{device_serial}/liveTools/traceroute/{traceroute_id}"
    
    for attempt in range(30):  # Poll for up to 90 seconds
        time.sleep(3)
        
        response = make_meraki_request(result_url)
        if not response or response.status_code != 200:
            logger.error(f"Failed to get traceroute results: {response.status_code if response else 'No response'}")
            continue
        
        trace_result = response.json()
        status = trace_result.get('status')
        
        if status == 'complete':
            logger.info(f"Traceroute completed successfully")
            return trace_result
        elif status == 'failed':
            logger.error(f"Traceroute failed: {trace_result.get('error', 'Unknown error')}")
            return None
    
    logger.warning(f"Traceroute timed out after 90 seconds")
    return None

def analyze_traceroute_hops(trace_result):
    """Analyze traceroute hops to identify carrier"""
    if not trace_result or 'results' not in trace_result:
        return None, None, 0
    
    results = trace_result.get('results', {})
    hops = results.get('hops', [])
    
    if not hops:
        logger.warning("No hops found in traceroute results")
        return None, None, 0
    
    # Analyze first 3 hops
    hop_data = []
    for i, hop in enumerate(hops[:3], 1):
        hosts = hop.get('hosts', [])
        if hosts:
            for host in hosts:
                ip = host.get('ip', '')
                hostname = host.get('hostname', '')
                
                hop_data.append({
                    'hop': i,
                    'ip': ip,
                    'hostname': hostname
                })
                
                # Check hostname for carrier patterns
                if hostname and hostname != 'N/A':
                    hostname_lower = hostname.lower()
                    for carrier, patterns in CARRIER_DNS_PATTERNS.items():
                        for pattern in patterns:
                            if pattern in hostname_lower:
                                confidence = 95 if i == 1 else 85 if i == 2 else 75
                                logger.info(f"Detected {carrier.upper()} from hostname '{hostname}' at hop {i}")
                                return carrier.upper(), hop_data, confidence
    
    # If no carrier detected from hostnames, check IPs
    # This would require ARIN lookups which we'll skip for now
    logger.info("No carrier detected from hostnames in first 3 hops")
    return None, hop_data, 0

def get_private_ip_devices():
    """Get devices with private IPs that need analysis"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get one specific device for testing
    cursor.execute("""
        SELECT DISTINCT
            mi.network_name,
            mi.device_serial,
            mi.wan1_ip,
            mi.wan2_ip
        FROM meraki_inventory mi
        WHERE mi.device_model LIKE 'MX%'
        AND mi.device_serial IS NOT NULL
        AND mi.network_name = 'ALB 03'
        AND mi.device_serial = 'Q2KY-FBAF-VTHH'
    """)
    
    devices = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return devices

def analyze_device(network_name, device_serial, wan1_ip, wan2_ip):
    """Analyze a device's WAN interfaces for cellular carrier"""
    results = []
    
    # Check WAN1
    if wan1_ip and is_private_ip(wan1_ip):
        logger.info(f"Analyzing WAN1 for {network_name}: {wan1_ip}")
        trace_result = run_traceroute(device_serial, wan1_ip)
        
        if trace_result:
            carrier, hop_data, confidence = analyze_traceroute_hops(trace_result)
            
            result = {
                'network_name': network_name,
                'device_serial': device_serial,
                'wan_interface': 'wan1',
                'private_ip': wan1_ip,
                'public_ip': None,  # Could extract from traceroute if available
                'detected_carrier': carrier,
                'detection_method': 'traceroute_dns' if carrier else None,
                'confidence_score': confidence,
                'traceroute_hops': json.dumps(hop_data) if hop_data else None
            }
            results.append(result)
    
    # Check WAN2
    if wan2_ip and is_private_ip(wan2_ip):
        logger.info(f"Analyzing WAN2 for {network_name}: {wan2_ip}")
        trace_result = run_traceroute(device_serial, wan2_ip)
        
        if trace_result:
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
    
    return results

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
    
    logger.info(f"Stored {len(results)} carrier detection results")

def is_private_ip(ip_str):
    """Check if IP is private"""
    try:
        return ipaddress.ip_address(ip_str).is_private
    except:
        return False

def main():
    """Main function to detect cellular carriers via traceroute"""
    logger.info("=== Starting Traceroute-based Cellular Carrier Detection ===")
    
    if not MERAKI_API_KEY:
        logger.error("MERAKI_API_KEY not found in environment")
        return
    
    # Create table if it doesn't exist
    create_cellular_detection_table()
    
    # Get devices to analyze
    devices = get_private_ip_devices()
    logger.info(f"Found {len(devices)} devices to analyze")
    
    if not devices:
        logger.info("No devices found to analyze")
        return
    
    total_results = []
    
    for network_name, device_serial, wan1_ip, wan2_ip in devices:
        logger.info(f"Processing {network_name} ({device_serial})")
        
        try:
            results = analyze_device(network_name, device_serial, wan1_ip, wan2_ip)
            
            if results:
                total_results.extend(results)
                store_detection_results(results)
                
                # Log findings
                for r in results:
                    if r['detected_carrier']:
                        logger.info(f"  {r['wan_interface']}: Detected {r['detected_carrier']} "
                                  f"(confidence: {r['confidence_score']}%)")
                    else:
                        logger.info(f"  {r['wan_interface']}: Unable to detect carrier")
            
        except Exception as e:
            logger.error(f"Error analyzing {network_name}: {e}")
    
    # Summary
    logger.info(f"\n=== Carrier Detection Summary ===")
    logger.info(f"Total results: {len(total_results)}")
    
    logger.info(f"\n=== Traceroute Cellular Carrier Detection Complete ===")

if __name__ == "__main__":
    main()