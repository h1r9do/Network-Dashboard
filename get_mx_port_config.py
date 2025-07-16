#!/usr/bin/env python3
"""
Extract MX appliance port configuration from AZP 30 network
Network ID: L_650207196201635912
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
NETWORK_ID = "L_650207196201635912"
NETWORK_NAME = "AZP 30"

# Headers for API requests
headers = {
    "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
    "Content-Type": "application/json"
}

def get_mx_ports():
    """Get MX appliance port configuration"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/ports"
    
    print(f"Fetching MX port configuration for {NETWORK_NAME} (ID: {NETWORK_ID})")
    print(f"API URL: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        ports = response.json()
        print(f"\nSuccessfully retrieved {len(ports)} port configurations")
        
        # Save to file
        output_file = f"/usr/local/bin/mx_ports_azp30_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(ports, f, indent=2)
        print(f"\nPort configuration saved to: {output_file}")
        
        # Display port configurations
        print("\n" + "="*80)
        print("MX APPLIANCE PORT CONFIGURATION - AZP 30")
        print("="*80)
        
        for port in ports:
            print(f"\nPort {port.get('number', 'N/A')}:")
            print(f"  Enabled: {port.get('enabled', 'N/A')}")
            print(f"  Type: {port.get('type', 'N/A')}")
            print(f"  Drop Untagged Traffic: {port.get('dropUntaggedTraffic', 'N/A')}")
            print(f"  VLAN: {port.get('vlan', 'N/A')}")
            print(f"  Allowed VLANs: {port.get('allowedVlans', 'N/A')}")
            print(f"  Access Policy: {port.get('accessPolicy', 'N/A')}")
            
        return ports
        
    except requests.exceptions.RequestException as e:
        print(f"\nError fetching MX ports: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None

def get_appliance_vlans():
    """Get VLAN configuration for the appliance"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/vlans"
    
    print(f"\n\nFetching VLAN configuration for {NETWORK_NAME}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        vlans = response.json()
        print(f"Successfully retrieved {len(vlans)} VLAN configurations")
        
        # Save to file
        output_file = f"/usr/local/bin/mx_vlans_azp30_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(vlans, f, indent=2)
        print(f"VLAN configuration saved to: {output_file}")
        
        # Display VLAN configurations
        print("\n" + "="*80)
        print("VLAN CONFIGURATION - AZP 30")
        print("="*80)
        
        for vlan in vlans:
            print(f"\nVLAN {vlan.get('id', 'N/A')} - {vlan.get('name', 'N/A')}:")
            print(f"  Subnet: {vlan.get('subnet', 'N/A')}")
            print(f"  Appliance IP: {vlan.get('applianceIp', 'N/A')}")
            print(f"  Group Policy ID: {vlan.get('groupPolicyId', 'N/A')}")
            
            # DHCP settings
            dhcp_handling = vlan.get('dhcpHandling', 'N/A')
            print(f"  DHCP Handling: {dhcp_handling}")
            
            if dhcp_handling == 'Run a DHCP server':
                print(f"  DHCP Lease Time: {vlan.get('dhcpLeaseTime', 'N/A')}")
                print(f"  DHCP Boot Options Enabled: {vlan.get('dhcpBootOptionsEnabled', 'N/A')}")
                
                # DHCP options
                dhcp_options = vlan.get('dhcpOptions', [])
                if dhcp_options:
                    print("  DHCP Options:")
                    for option in dhcp_options:
                        print(f"    - Code {option.get('code', 'N/A')}: {option.get('type', 'N/A')} = {option.get('value', 'N/A')}")
                
                # Reserved IP ranges
                reserved_ranges = vlan.get('reservedIpRanges', [])
                if reserved_ranges:
                    print("  Reserved IP Ranges:")
                    for range_item in reserved_ranges:
                        print(f"    - {range_item.get('start', 'N/A')} to {range_item.get('end', 'N/A')} ({range_item.get('comment', 'N/A')})")
                
                # Fixed IP assignments
                fixed_ips = vlan.get('fixedIpAssignments', {})
                if fixed_ips:
                    print("  Fixed IP Assignments:")
                    for mac, details in fixed_ips.items():
                        print(f"    - {mac}: {details.get('ip', 'N/A')} ({details.get('name', 'N/A')})")
        
        return vlans
        
    except requests.exceptions.RequestException as e:
        print(f"\nError fetching VLANs: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None

def get_dhcp_settings():
    """Get appliance DHCP settings"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/settings"
    
    print(f"\n\nFetching appliance settings for {NETWORK_NAME}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        settings = response.json()
        
        # Save to file
        output_file = f"/usr/local/bin/mx_settings_azp30_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"Appliance settings saved to: {output_file}")
        
        # Display relevant settings
        print("\n" + "="*80)
        print("APPLIANCE SETTINGS - AZP 30")
        print("="*80)
        
        print(f"\nDeployment Mode: {settings.get('deploymentMode', 'N/A')}")
        print(f"Client Tracking Method: {settings.get('clientTrackingMethod', 'N/A')}")
        print(f"Dynamic DNS Enabled: {settings.get('dynamicDnsEnabled', 'N/A')}")
        
        if settings.get('dynamicDnsEnabled'):
            print(f"Dynamic DNS Prefix: {settings.get('dynamicDnsPrefix', 'N/A')}")
            print(f"Dynamic DNS URL: {settings.get('dynamicDnsUrl', 'N/A')}")
        
        return settings
        
    except requests.exceptions.RequestException as e:
        print(f"\nError fetching appliance settings: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None

def main():
    """Main function to extract all MX configuration"""
    print(f"Starting MX configuration extraction at {datetime.now()}")
    
    if not MERAKI_API_KEY:
        print("ERROR: MERAKI_API_KEY not found in environment variables")
        return
    
    # Get all configurations
    ports = get_mx_ports()
    vlans = get_appliance_vlans()
    settings = get_dhcp_settings()
    
    # Create consolidated report
    report = {
        "network_id": NETWORK_ID,
        "network_name": NETWORK_NAME,
        "timestamp": datetime.now().isoformat(),
        "ports": ports,
        "vlans": vlans,
        "settings": settings
    }
    
    # Save consolidated report
    report_file = f"/usr/local/bin/mx_complete_config_azp30_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n\nComplete configuration report saved to: {report_file}")
    print(f"Extraction completed at {datetime.now()}")

if __name__ == "__main__":
    main()