#!/usr/bin/env python3
"""
Extract complete Meraki network configurations for NEO 07 and AZP 30
Saves each network's complete config to separate JSON files
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

# Target networks
TARGET_NETWORKS = ["NEO 07", "AZP 30"]

def make_api_request(url, params=None):
    """Make API request with error handling and rate limiting"""
    time.sleep(0.5)  # Basic rate limiting
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 429:
            print("Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return make_api_request(url, params)
            
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_organization_id():
    """Get the organization ID"""
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url)
    
    # Look for DTC-Store-Inventory-All
    for org in orgs:
        if org.get("name") == "DTC-Store-Inventory-All":
            return org.get("id")
    
    raise ValueError("Organization not found")

def find_networks(org_id, network_names):
    """Find networks by name"""
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    networks = make_api_request(url)
    
    found_networks = {}
    for network in networks:
        name = network.get('name', '').strip()
        if name in network_names:
            found_networks[name] = network
            
    return found_networks

def get_network_devices(network_id):
    """Get all devices in a network"""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    return make_api_request(url) or []

def get_vlans(network_id):
    """Get VLAN configuration"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    return make_api_request(url) or []

def get_static_routes(network_id):
    """Get static routes"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/staticRoutes"
    return make_api_request(url) or []

def get_l3_firewall_rules(network_id):
    """Get L3 firewall rules"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    result = make_api_request(url)
    return result.get('rules', []) if result else []

def get_l7_firewall_rules(network_id):
    """Get L7 firewall rules"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l7FirewallRules"
    result = make_api_request(url)
    return result.get('rules', []) if result else []

def get_content_filtering(network_id):
    """Get content filtering settings"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/contentFiltering"
    return make_api_request(url) or {}

def get_traffic_shaping(network_id):
    """Get traffic shaping rules"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/trafficShaping"
    return make_api_request(url) or {}

def get_port_forwarding_rules(network_id):
    """Get port forwarding rules"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/portForwardingRules"
    result = make_api_request(url)
    return result.get('rules', []) if result else []

def get_one_to_one_nat_rules(network_id):
    """Get 1:1 NAT rules"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/oneToOneNatRules"
    result = make_api_request(url)
    return result.get('rules', []) if result else []

def get_site_to_site_vpn(network_id):
    """Get site-to-site VPN settings"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/vpn/siteToSiteVpn"
    return make_api_request(url) or {}

def get_intrusion_settings(network_id):
    """Get intrusion detection settings"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/security/intrusion"
    return make_api_request(url) or {}

def get_malware_settings(network_id):
    """Get malware protection settings"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/security/malware"
    return make_api_request(url) or {}

def get_uplink_settings(network_id):
    """Get uplink configuration"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/uplinks/settings"
    return make_api_request(url) or {}

def get_dhcp_settings(network_id):
    """Get DHCP settings for all VLANs"""
    dhcp_settings = []
    vlans = get_vlans(network_id)
    
    for vlan in vlans:
        vlan_id = vlan.get('id')
        # DHCP settings are included in VLAN response
        dhcp_settings.append({
            'vlanId': vlan_id,
            'dhcpHandling': vlan.get('dhcpHandling'),
            'dhcpLeaseTime': vlan.get('dhcpLeaseTime'),
            'dhcpBootOptionsEnabled': vlan.get('dhcpBootOptionsEnabled'),
            'dhcpOptions': vlan.get('dhcpOptions', []),
            'reservedIpRanges': vlan.get('reservedIpRanges', []),
            'fixedIpAssignments': vlan.get('fixedIpAssignments', {}),
            'dnsNameservers': vlan.get('dnsNameservers')
        })
    
    return dhcp_settings

def get_switch_ports(serial):
    """Get switch port configuration"""
    url = f"{BASE_URL}/devices/{serial}/switch/ports"
    return make_api_request(url) or []

def get_switch_stp_settings(network_id):
    """Get STP settings"""
    url = f"{BASE_URL}/networks/{network_id}/switch/stp"
    return make_api_request(url) or {}

def get_switch_acls(network_id):
    """Get switch ACLs"""
    url = f"{BASE_URL}/networks/{network_id}/switch/accessControlLists"
    return make_api_request(url) or {}

def get_switch_port_schedules(network_id):
    """Get switch port schedules"""
    url = f"{BASE_URL}/networks/{network_id}/switch/portSchedules"
    return make_api_request(url) or []

def get_switch_qos_rules(network_id):
    """Get switch QoS rules"""
    url = f"{BASE_URL}/networks/{network_id}/switch/qosRules"
    return make_api_request(url) or []

def get_switch_storm_control(network_id):
    """Get storm control settings"""
    url = f"{BASE_URL}/networks/{network_id}/switch/stormControl"
    return make_api_request(url) or {}

def get_switch_mtu(network_id):
    """Get MTU configuration"""
    url = f"{BASE_URL}/networks/{network_id}/switch/mtu"
    return make_api_request(url) or {}

def get_group_policies(network_id):
    """Get group policies"""
    url = f"{BASE_URL}/networks/{network_id}/groupPolicies"
    return make_api_request(url) or []

def get_wireless_ssids(network_id):
    """Get wireless SSIDs if any"""
    url = f"{BASE_URL}/networks/{network_id}/wireless/ssids"
    return make_api_request(url) or []

def get_alerts_settings(network_id):
    """Get network alerts configuration"""
    url = f"{BASE_URL}/networks/{network_id}/alerts/settings"
    return make_api_request(url) or {}

def get_syslog_servers(network_id):
    """Get syslog servers"""
    url = f"{BASE_URL}/networks/{network_id}/syslogServers"
    return make_api_request(url) or []

def get_snmp_settings(network_id):
    """Get SNMP settings"""
    url = f"{BASE_URL}/networks/{network_id}/snmp"
    return make_api_request(url) or {}

def extract_network_config(network):
    """Extract complete configuration for a network"""
    network_id = network['id']
    network_name = network['name']
    
    print(f"\nExtracting configuration for {network_name}...")
    
    config = {
        'extractionDate': datetime.now().isoformat(),
        'network': {
            'id': network_id,
            'name': network_name,
            'organizationId': network.get('organizationId'),
            'timeZone': network.get('timeZone'),
            'tags': network.get('tags', []),
            'productTypes': network.get('productTypes', []),
            'enrollmentString': network.get('enrollmentString'),
            'notes': network.get('notes')
        },
        'devices': [],
        'appliance': {},
        'switch': {},
        'wireless': {},
        'monitoring': {}
    }
    
    # Get all devices
    devices = get_network_devices(network_id)
    config['devices'] = devices
    
    # Separate devices by type
    mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
    ms_devices = [d for d in devices if d.get('model', '').startswith('MS')]
    mr_devices = [d for d in devices if d.get('model', '').startswith('MR')]
    
    print(f"  Found {len(mx_devices)} MX, {len(ms_devices)} MS, {len(mr_devices)} MR devices")
    
    # MX Appliance Configuration
    if mx_devices:
        print("  Extracting MX appliance configuration...")
        config['appliance'] = {
            'vlans': get_vlans(network_id),
            'staticRoutes': get_static_routes(network_id),
            'l3FirewallRules': get_l3_firewall_rules(network_id),
            'l7FirewallRules': get_l7_firewall_rules(network_id),
            'contentFiltering': get_content_filtering(network_id),
            'trafficShaping': get_traffic_shaping(network_id),
            'portForwardingRules': get_port_forwarding_rules(network_id),
            'oneToOneNatRules': get_one_to_one_nat_rules(network_id),
            'siteToSiteVpn': get_site_to_site_vpn(network_id),
            'intrusion': get_intrusion_settings(network_id),
            'malware': get_malware_settings(network_id),
            'uplinkSettings': get_uplink_settings(network_id),
            'dhcpSettings': get_dhcp_settings(network_id),
            'groupPolicies': get_group_policies(network_id)
        }
    
    # MS Switch Configuration
    if ms_devices:
        print("  Extracting MS switch configuration...")
        config['switch'] = {
            'stp': get_switch_stp_settings(network_id),
            'acls': get_switch_acls(network_id),
            'portSchedules': get_switch_port_schedules(network_id),
            'qosRules': get_switch_qos_rules(network_id),
            'stormControl': get_switch_storm_control(network_id),
            'mtu': get_switch_mtu(network_id),
            'ports': {}
        }
        
        # Get port config for each switch
        for switch in ms_devices:
            serial = switch['serial']
            print(f"    Getting port config for {switch.get('name', serial)}...")
            config['switch']['ports'][serial] = get_switch_ports(serial)
    
    # MR Wireless Configuration
    if mr_devices:
        print("  Extracting MR wireless configuration...")
        config['wireless'] = {
            'ssids': get_wireless_ssids(network_id)
        }
    
    # Monitoring and Management
    print("  Extracting monitoring configuration...")
    config['monitoring'] = {
        'alerts': get_alerts_settings(network_id),
        'syslogServers': get_syslog_servers(network_id),
        'snmp': get_snmp_settings(network_id)
    }
    
    return config

def save_config_to_file(config, filename):
    """Save configuration to JSON file"""
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {filename}")

def main():
    """Main execution"""
    print("Starting Meraki configuration extraction...")
    
    try:
        # Get organization
        org_id = get_organization_id()
        print(f"Using Organization ID: {org_id}")
        
        # Find target networks
        networks = find_networks(org_id, TARGET_NETWORKS)
        
        if not networks:
            print(f"No networks found matching: {TARGET_NETWORKS}")
            return
        
        print(f"Found {len(networks)} networks")
        
        # Extract configuration for each network
        for network_name, network in networks.items():
            config = extract_network_config(network)
            
            # Generate filename
            filename = network_name.lower().replace(' ', '_') + '_config.json'
            save_config_to_file(config, filename)
        
        print("\nConfiguration extraction complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()