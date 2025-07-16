#!/usr/bin/env python3
"""
Check ALB 01 and ALB 02 MX device notes from live Meraki API
Uses the same parsing logic as nightly_meraki_db.py
"""

import os
import sys
import re
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"

def make_api_request(url, api_key):
    """Make API request with retries."""
    headers = {"X-Cisco-Meraki-API-Key": api_key}
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"Rate limited, waiting {attempt + 1} seconds...")
                time.sleep(attempt + 1)
            else:
                print(f"API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Request error: {e}")
            return None
    return None

def get_organization_id():
    """Get the organization ID for DTC-Store-Inventory-All."""
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url, MERAKI_API_KEY)
    if orgs:
        for org in orgs:
            if org['name'] == "DTC-Store-Inventory-All":
                return org['id']
    return None

def get_networks(org_id, search_term):
    """Get networks matching search term."""
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    networks = make_api_request(url, MERAKI_API_KEY)
    matching = []
    if networks:
        for net in networks:
            if search_term.upper() in net['name'].upper():
                matching.append(net)
    return matching

def get_devices(network_id):
    """Get devices in a network."""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    return make_api_request(url, MERAKI_API_KEY)

def get_device_details(serial):
    """Get device details including notes."""
    url = f"{BASE_URL}/devices/{serial}"
    return make_api_request(url, MERAKI_API_KEY)

def get_uplink_status(serial):
    """Get uplink status for WAN IPs."""
    url = f"{BASE_URL}/devices/{serial}/appliance/uplinks/statuses"
    return make_api_request(url, MERAKI_API_KEY)

def parse_raw_notes(raw_notes):
    """Parse the 'notes' field to extract WAN provider labels and speeds - EXACT COPY from nightly script."""
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    text = re.sub(r'\s+', ' ', raw_notes.strip())
    wan1_pattern = re.compile(r'(?:WAN1|WAN\s*1)\s*:?\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)
    speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
    
    def extract_provider_and_speed(segment):
        """Helper to extract provider name and speed from a text segment."""
        match = speed_pattern.search(segment)
        if match:
            up_speed = float(match.group(1)); up_unit = match.group(2).upper()
            down_speed = float(match.group(3)); down_unit = match.group(4).upper()
            if up_unit in ['G', 'GB']:
                up_speed *= 1000
                up_unit = 'M'
            elif up_unit in ['M', 'MB']:
                up_unit = 'M'
            if down_unit in ['G', 'GB']:
                down_speed *= 1000
                down_unit = 'M'
            elif down_unit in ['M', 'MB']:
                down_unit = 'M'
            speed_str = f"{up_speed:.1f}M x {down_speed:.1f}M"
            provider_name = segment[:match.start()].strip()
            # Remove special prefixes like "NOT DSR"
            provider_name = re.sub(r'^(NOT\s+DSR|DSR)\s+', '', provider_name, flags=re.IGNORECASE)
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, speed_str
        else:
            provider_name = segment.strip()
            # Remove special prefixes
            provider_name = re.sub(r'^(NOT\s+DSR|DSR)\s+', '', provider_name, flags=re.IGNORECASE)
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, ""
    
    wan1_text = ""
    wan2_text = ""
    parts = re.split(wan1_pattern, text, maxsplit=1)
    if len(parts) > 1:
        after_wan1 = parts[1]
        wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
        wan1_text = wan2_split[0].strip()
        if len(wan2_split) > 1:
            wan2_text = wan2_split[1].strip()
    else:
        parts = re.split(wan2_pattern, text, maxsplit=1)
        if len(parts) > 1:
            wan2_text = parts[1].strip()
        else:
            wan1_text = text.strip()
    
    wan1_provider, wan1_speed = extract_provider_and_speed(wan1_text)
    wan2_provider, wan2_speed = extract_provider_and_speed(wan2_text)
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

def main():
    print(f"\n{'='*80}")
    print(f"ALB MX Device Notes Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Get organization
    org_id = get_organization_id()
    if not org_id:
        print("ERROR: Could not find DTC-Store-Inventory-All organization")
        return
    
    # Search for ALB networks
    for search_term in ["ALB 03", "ALB"]:
        print(f"\nSearching for networks containing '{search_term}'...")
        networks = get_networks(org_id, search_term)
        
        if not networks:
            print(f"  No networks found for '{search_term}'")
            continue
            
        for network in networks:
            print(f"\n  Network: {network['name']} (ID: {network['id']})")
            
            # Get devices
            devices = get_devices(network['id'])
            if not devices:
                print("    No devices found")
                continue
                
            # Find MX devices
            mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
            if not mx_devices:
                print("    No MX devices found")
                continue
                
            for device in mx_devices:
                serial = device['serial']
                print(f"\n    MX Device: {device.get('name', 'Unnamed')} ({device['model']})")
                print(f"    Serial: {serial}")
                
                # Get device details with notes
                details = get_device_details(serial)
                if not details:
                    print("      ERROR: Could not get device details")
                    continue
                
                raw_notes = details.get('notes', '') or ''
                print(f"\n    RAW NOTES:")
                print(f"      '{raw_notes}'")
                
                # Parse notes using same logic as nightly script
                wan1_provider, wan1_speed, wan2_provider, wan2_speed = parse_raw_notes(raw_notes)
                
                print(f"\n    PARSED OUTPUT:")
                print(f"      WAN1 Provider: '{wan1_provider}'")
                print(f"      WAN1 Speed: '{wan1_speed}'")
                print(f"      WAN2 Provider: '{wan2_provider}'")
                print(f"      WAN2 Speed: '{wan2_speed}'")
                
                # Get uplink status for IPs
                uplinks = get_uplink_status(serial)
                if uplinks:
                    print(f"\n    UPLINK STATUS:")
                    for uplink in uplinks:
                        if uplink.get('status') == 'active':
                            interface = uplink.get('interface', '')
                            ip = uplink.get('ip', 'No IP')
                            gateway = uplink.get('gateway', 'No Gateway')
                            print(f"      {interface}: IP={ip}, Gateway={gateway}")
                
                print(f"\n    DATABASE STORAGE PREVIEW:")
                print(f"      device_notes: '{raw_notes}'")
                print(f"      wan1_provider_label: '{wan1_provider}'")
                print(f"      wan1_speed_label: '{wan1_speed}'")
                print(f"      wan2_provider_label: '{wan2_provider}'")
                print(f"      wan2_speed_label: '{wan2_speed}'")
                
                print(f"\n    {'='*60}")

if __name__ == "__main__":
    main()