#!/usr/bin/env python3
"""
Update TST 01 DHCP configuration to match AZP 30
Generated: 2025-07-09 17:07:36
"""

import meraki
import os
import sys
from datetime import datetime

# API key should be set as environment variable
from dotenv import load_dotenv
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
if not API_KEY:
    print("Error: Please set MERAKI_API_KEY environment variable")
    sys.exit(1)

# Initialize Meraki dashboard
dashboard = meraki.DashboardAPI(API_KEY)

# Network IDs
TST_01_NETWORK_ID = "L_3790904986339115852"

# DHCP configuration updates
vlan_updates = {
    # VLAN 1 - Data: Change to DHCP relay mode
    1: {
        "dhcpHandling": "Relay DHCP to another server",
        "dhcpRelayServerIps": ["10.0.175.5", "10.101.175.5"]
    },
    
    # VLAN 101 - Voice: Update lease time, DNS, and add DHCP options
    101: {
        "dhcpLeaseTime": "12 hours",
        "dnsNameservers": "10.0.175.27\n10.101.175.28",
        "dhcpOptions": [
            {
                "code": "42",
                "type": "ip",
                "value": "10.0.130.102, 10.0.130.82, 10.101.130.228, 10.101.130.227"
            },
            {
                "code": "66",
                "type": "text",
                "value": "https://159357:68473900@config.tetravx.com/provision/us3/app/"
            },
            {
                "code": "150",
                "type": "ip",
                "value": "10.0.99.100, 10.101.99.102"
            }
        ]
    },
    
    # VLAN 201 - Ccard: Change to DHCP relay mode
    201: {
        "dhcpHandling": "Relay DHCP to another server",
        "dhcpRelayServerIps": ["10.0.175.5", "10.101.175.5", "10.0.130.30", "10.101.130.30"]
    },
    
    # VLAN 300 - AP Mgmt: Update DNS and add fixed IP assignments
    300: {
        "dnsNameservers": "10.0.175.27\n10.101.175.28",
        "fixedIpAssignments": {
            "00:18:0a:35:fe:2e": {
                "ip": "10.1.32.180",
                "name": "azp_30ap01"
            },
            "00:18:0a:81:04:4e": {
                "ip": "10.1.32.181",
                "name": "azp_30ap02"
            },
            "0c:8d:db:93:22:f6": {
                "ip": "10.1.32.182",
                "name": "azp_30ap03"
            },
            "98:18:88:b8:cc:67": {
                "ip": "10.1.32.188",
                "name": "azp_30sw01"
            },
            "98:18:88:b8:db:ec": {
                "ip": "10.1.32.189",
                "name": "azp_30sw02"
            },
            "e4:55:a8:16:00:29": {
                "ip": "10.1.32.186",
                "name": "azp_30ap11"
            },
            "e4:55:a8:16:00:6f": {
                "ip": "10.1.32.187",
                "name": "azp_30ap10"
            }
        }
    },
    
    # VLAN 301 - Scanner: Update DNS
    301: {
        "dnsNameservers": "10.0.175.27\n10.101.175.28"
    }
}

def update_vlans():
    """Update VLAN configurations"""
    print(f"Starting DHCP configuration update for TST 01 at {datetime.now()}")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for vlan_id, config in vlan_updates.items():
        try:
            print(f"\nUpdating VLAN {vlan_id}...")
            
            # Get current VLAN config
            current_vlan = dashboard.appliance.getNetworkApplianceVlan(
                TST_01_NETWORK_ID, vlan_id
            )
            print(f"  Current DHCP handling: {current_vlan.get('dhcpHandling', 'Not set')}")
            
            # Apply updates
            updated_vlan = dashboard.appliance.updateNetworkApplianceVlan(
                TST_01_NETWORK_ID, vlan_id, **config
            )
            
            print(f"  ✓ Successfully updated VLAN {vlan_id}")
            
            # Show what was updated
            for key, value in config.items():
                if key == 'dhcpOptions':
                    print(f"    - {key}: {len(value)} options configured")
                elif key == 'fixedIpAssignments':
                    print(f"    - {key}: {len(value)} assignments configured")
                else:
                    print(f"    - {key}: {value}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error updating VLAN {vlan_id}: {str(e)}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"Update Summary:")
    print(f"  - Successful updates: {success_count}")
    print(f"  - Failed updates: {error_count}")
    print(f"  - Total VLANs processed: {len(vlan_updates)}")
    
    return success_count, error_count

def verify_updates():
    """Verify the updates were applied correctly"""
    print("\n" + "=" * 60)
    print("Verifying DHCP configuration updates...")
    print("=" * 60)
    
    all_correct = True
    
    for vlan_id in vlan_updates.keys():
        try:
            vlan = dashboard.appliance.getNetworkApplianceVlan(
                TST_01_NETWORK_ID, vlan_id
            )
            
            print(f"\nVLAN {vlan_id} - {vlan['name']}:")
            print(f"  DHCP Handling: {vlan.get('dhcpHandling', 'Not set')}")
            
            if vlan.get('dhcpHandling') == 'Relay DHCP to another server':
                relay_servers = vlan.get('dhcpRelayServerIps', [])
                print(f"  Relay Servers: {', '.join(relay_servers) if relay_servers else 'None'}")
            
            if vlan.get('dhcpHandling') == 'Run a DHCP server':
                print(f"  Lease Time: {vlan.get('dhcpLeaseTime', 'Not set')}")
                dhcp_options = vlan.get('dhcpOptions', [])
                if dhcp_options:
                    print(f"  DHCP Options: {len(dhcp_options)} configured")
            
            print(f"  DNS Servers: {vlan.get('dnsNameservers', 'Not set')}")
            
            fixed_ips = vlan.get('fixedIpAssignments', {})
            if fixed_ips:
                print(f"  Fixed IP Assignments: {len(fixed_ips)} configured")
                
        except Exception as e:
            print(f"\nError verifying VLAN {vlan_id}: {str(e)}")
            all_correct = False
    
    return all_correct

def main():
    """Main function"""
    print("TST 01 DHCP Configuration Update Script")
    print("This will update TST 01 to match AZP 30 DHCP configuration")
    print()
    
    # Confirm before proceeding
    response = input("Do you want to proceed with the updates? (yes/no): ")
    if response.lower() != 'yes':
        print("Update cancelled.")
        return
    
    # Perform updates
    success, errors = update_vlans()
    
    if errors == 0:
        print("\n✓ All updates completed successfully!")
        
        # Verify updates
        print("\nWould you like to verify the updates?")
        response = input("Verify updates? (yes/no): ")
        if response.lower() == 'yes':
            if verify_updates():
                print("\n✓ All configurations verified successfully!")
            else:
                print("\n⚠ Some configurations may need manual verification")
    else:
        print(f"\n⚠ Completed with {errors} errors. Please check the failed VLANs manually.")

if __name__ == "__main__":
    main()
