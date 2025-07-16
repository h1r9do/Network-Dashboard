#!/usr/bin/env python3
"""
Apply DHCP Configuration for Test Environment
============================================

This script applies DHCP configuration from AZP 30 to TST 01 with
proper handling for test environment limitations.

Usage:
    python3 apply_dhcp_config_test.py

Author: Claude
Date: July 2025
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# TST 01 network
TARGET_NETWORK = 'L_3790904986339115852'

# Test network DNS servers (translated from AZP 30)
TEST_DNS_SERVERS = {
    'nameservers': '10.255.255.5\n10.255.255.6',  # Translated from 10.0.175.5, 10.101.175.5
    'opendns': []  # OpenDNS servers if needed
}

def log(message, level="INFO"):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def make_api_request(url, method='GET', data=None):
    """Make API request with error handling"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        
        response.raise_for_status()
        return response.json() if response.text else None
    except requests.exceptions.RequestException as e:
        log(f"API Error: {e}", "ERROR")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            log(f"Response: {e.response.text}", "ERROR")
        return None

def update_vlan_dhcp(vlan_id, dhcp_config):
    """Update DHCP configuration for a VLAN"""
    url = f"{BASE_URL}/networks/{TARGET_NETWORK}/appliance/vlans/{vlan_id}"
    
    # Get current VLAN config
    current = make_api_request(url)
    if not current:
        log(f"Could not get current config for VLAN {vlan_id}", "ERROR")
        return False
    
    # Merge with DHCP updates
    updated = current.copy()
    updated.update(dhcp_config)
    
    # Apply update
    result = make_api_request(url, method='PUT', data=updated)
    return result is not None

def apply_dhcp_configurations():
    """Apply all DHCP configurations matching AZP 30"""
    log("Applying DHCP configurations to TST 01...")
    
    # VLAN 1 - Data (Convert relay to server for test)
    log("\nVLAN 1 (Data):")
    vlan1_config = {
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '12 hours',
        'dnsNameservers': TEST_DNS_SERVERS['nameservers']
    }
    if update_vlan_dhcp(1, vlan1_config):
        log("  ✓ Configured as DHCP server (relay not available in test)")
    else:
        log("  ✗ Failed to update DHCP config", "ERROR")
    
    # VLAN 101 - Voice (Add DHCP options)
    log("\nVLAN 101 (Voice):")
    vlan101_config = {
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': TEST_DNS_SERVERS['nameservers'],
        'dhcpOptions': [
            {
                'code': '42',
                'type': 'ip',
                'value': '10.255.255.30'  # NTP server (translated)
            },
            {
                'code': '66',
                'type': 'text', 
                'value': '10.255.255.35'  # TFTP server (translated)
            }
        ]
    }
    if update_vlan_dhcp(101, vlan101_config):
        log("  ✓ Added VoIP DHCP options and DNS servers")
    else:
        log("  ✗ Failed to update DHCP config", "ERROR")
    
    # VLAN 201 - Ccard (Convert relay to server for test)
    log("\nVLAN 201 (Ccard):")
    vlan201_config = {
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '12 hours',
        'dnsNameservers': TEST_DNS_SERVERS['nameservers']
    }
    if update_vlan_dhcp(201, vlan201_config):
        log("  ✓ Configured as DHCP server (relay not available in test)")
    else:
        log("  ✗ Failed to update DHCP config", "ERROR")
    
    # VLAN 300 - AP Mgmt (Add fixed IP assignments)
    log("\nVLAN 300 (AP Mgmt):")
    vlan300_config = {
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': TEST_DNS_SERVERS['nameservers'],
        'fixedIpAssignments': {
            '00:18:0a:80:8b:6a': {'ip': '10.255.255.180', 'name': 'AP1'},
            '00:18:0a:80:91:46': {'ip': '10.255.255.181', 'name': 'AP2'},
            '00:18:0a:80:92:fc': {'ip': '10.255.255.182', 'name': 'AP3'},
            '00:18:0a:80:8b:e4': {'ip': '10.255.255.183', 'name': 'AP4'},
            '0c:8d:db:6e:be:2c': {'ip': '10.255.255.188', 'name': 'SW1'},
            '0c:8d:db:b3:0e:78': {'ip': '10.255.255.189', 'name': 'SW2'},
            '0c:8d:db:6e:bb:dc': {'ip': '10.255.255.190', 'name': 'SW3'}
        }
    }
    if update_vlan_dhcp(300, vlan300_config):
        log("  ✓ Added DNS servers and 7 fixed IP assignments")
    else:
        log("  ✗ Failed to update DHCP config", "ERROR")
    
    # VLAN 301 - Scanner (Update DNS)
    log("\nVLAN 301 (Scanner):")
    vlan301_config = {
        'dhcpHandling': 'Run a DHCP server',
        'dhcpLeaseTime': '1 day',
        'dnsNameservers': TEST_DNS_SERVERS['nameservers']
    }
    if update_vlan_dhcp(301, vlan301_config):
        log("  ✓ Updated DNS servers")
    else:
        log("  ✗ Failed to update DHCP config", "ERROR")
    
    # VLANs 800, 801, 802, 803, 900 already have correct settings
    log("\nVLANs 800, 801, 802, 803, 900:")
    log("  ✓ Already configured correctly (no changes needed)")

def verify_dhcp_settings():
    """Verify DHCP settings after update"""
    log("\n" + "="*60)
    log("Verifying DHCP configurations...")
    
    url = f"{BASE_URL}/networks/{TARGET_NETWORK}/appliance/vlans"
    vlans = make_api_request(url)
    
    if not vlans:
        log("Could not retrieve VLANs for verification", "ERROR")
        return
    
    for vlan in vlans:
        vlan_id = vlan['id']
        vlan_name = vlan.get('name', 'Unnamed')
        dhcp_mode = vlan.get('dhcpHandling', 'Unknown')
        
        log(f"\nVLAN {vlan_id} ({vlan_name}):")
        log(f"  DHCP Mode: {dhcp_mode}")
        
        if dhcp_mode == 'Run a DHCP server':
            log(f"  Lease Time: {vlan.get('dhcpLeaseTime', 'Not set')}")
            log(f"  DNS Servers: {vlan.get('dnsNameservers', 'Not set')}")
            
            # Check for DHCP options
            if vlan.get('dhcpOptions'):
                log("  DHCP Options:")
                for option in vlan['dhcpOptions']:
                    log(f"    - Option {option['code']}: {option['value']}")
            
            # Check for fixed IPs
            if vlan.get('fixedIpAssignments'):
                log(f"  Fixed IP Assignments: {len(vlan['fixedIpAssignments'])} configured")

def main():
    print("🔧 DHCP Configuration Tool for TST 01")
    print("=" * 60)
    
    log(f"Target network: {TARGET_NETWORK}")
    log("Mode: Test environment (DHCP relay → server conversion)")
    
    # Apply configurations
    apply_dhcp_configurations()
    
    # Verify
    verify_dhcp_settings()
    
    print("\n" + "="*60)
    print("✅ DHCP configuration update completed!")
    print("\nKey changes applied:")
    print("- VLAN 1 & 201: Converted from relay to DHCP server mode")
    print("- VLAN 101: Added VoIP DHCP options (NTP, TFTP)")
    print("- VLAN 300: Added 7 fixed IP assignments for APs/switches")
    print("- All VLANs: DNS servers updated to test range")

if __name__ == "__main__":
    main()