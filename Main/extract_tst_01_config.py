#!/usr/bin/env python3
"""
Extract complete configuration for TST 01 network in DTC-Network-Engineering org
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

def get_warm_spare(network_id):
    """Get warm spare configuration"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/warmSpare"
    return make_api_request(url) or {}

def get_connectivity_monitoring_destinations(network_id):
    """Get connectivity monitoring destinations"""
    url = f"{BASE_URL}/networks/{network_id}/appliance/connectivityMonitoringDestinations"
    return make_api_request(url) or {}

def get_dhcp_settings(network_id):
    """Get DHCP settings for all VLANs"""
    dhcp_settings = []
    vlans = get_vlans(network_id)
    
    for vlan in vlans:
        vlan_id = vlan.get('id')
        dhcp_settings.append({
            'vlanId': vlan_id,
            'vlanName': vlan.get('name'),
            'subnet': vlan.get('subnet'),
            'applianceIp': vlan.get('applianceIp'),
            'dhcpHandling': vlan.get('dhcpHandling'),
            'dhcpLeaseTime': vlan.get('dhcpLeaseTime'),
            'dhcpBootOptionsEnabled': vlan.get('dhcpBootOptionsEnabled'),
            'dhcpBootNextServer': vlan.get('dhcpBootNextServer'),
            'dhcpBootFilename': vlan.get('dhcpBootFilename'),
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

def get_switch_settings(network_id):
    """Get general switch settings"""
    url = f"{BASE_URL}/networks/{network_id}/switch/settings"
    return make_api_request(url) or {}

def get_switch_dhcp_server_policy(network_id):
    """Get switch DHCP server policy"""
    url = f"{BASE_URL}/networks/{network_id}/switch/dhcpServerPolicy"
    return make_api_request(url) or {}

def get_group_policies(network_id):
    """Get group policies"""
    url = f"{BASE_URL}/networks/{network_id}/groupPolicies"
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

def get_network_devices(network_id):
    """Get all devices in a network"""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    return make_api_request(url) or []

def get_device_management_interface(serial):
    """Get device management interface settings"""
    url = f"{BASE_URL}/devices/{serial}/managementInterface"
    return make_api_request(url) or {}

def main():
    """Main execution"""
    print("Starting TST 01 configuration extraction...")
    
    try:
        # TST 01 network details from previous check
        network_id = "L_3790904986339115852"
        network_name = "TST 01"
        org_id = "3790904986339115010"
        
        print(f"Extracting configuration for {network_name} (ID: {network_id})...")
        
        # Get network details
        url = f"{BASE_URL}/networks/{network_id}"
        network = make_api_request(url)
        
        config = {
            'extractionDate': datetime.now().isoformat(),
            'network': {
                'id': network_id,
                'name': network_name,
                'organizationId': org_id,
                'organizationName': 'DTC-Network-Engineering',
                'timeZone': network.get('timeZone', 'US/Arizona'),
                'tags': network.get('tags', []),
                'productTypes': network.get('productTypes', ['appliance', 'switch']),
                'enrollmentString': network.get('enrollmentString'),
                'notes': network.get('notes', ''),
                'isBoundToConfigTemplate': network.get('isBoundToConfigTemplate', False),
                'configTemplateId': network.get('configTemplateId')
            },
            'devices': [],
            'appliance': {},
            'switch': {},
            'monitoring': {}
        }
        
        # Get all devices
        print("  Getting devices...")
        devices = get_network_devices(network_id)
        
        # Add management interface settings for each device
        for device in devices:
            serial = device['serial']
            device['managementInterface'] = get_device_management_interface(serial)
        
        config['devices'] = devices
        
        # Separate devices by type
        mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
        ms_devices = [d for d in devices if d.get('model', '').startswith('MS')]
        
        print(f"  Found {len(mx_devices)} MX devices, {len(ms_devices)} MS devices")
        
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
                'warmSpare': get_warm_spare(network_id),
                'connectivityMonitoringDestinations': get_connectivity_monitoring_destinations(network_id),
                'dhcpSettings': get_dhcp_settings(network_id),
                'groupPolicies': get_group_policies(network_id)
            }
        
        # MS Switch Configuration
        if ms_devices:
            print("  Extracting MS switch configuration...")
            config['switch'] = {
                'settings': get_switch_settings(network_id),
                'stp': get_switch_stp_settings(network_id),
                'acls': get_switch_acls(network_id),
                'portSchedules': get_switch_port_schedules(network_id),
                'qosRules': get_switch_qos_rules(network_id),
                'stormControl': get_switch_storm_control(network_id),
                'mtu': get_switch_mtu(network_id),
                'dhcpServerPolicy': get_switch_dhcp_server_policy(network_id),
                'ports': {}
            }
            
            # Get port config for each switch
            for switch in ms_devices:
                serial = switch['serial']
                switch_name = switch.get('name', serial)
                print(f"    Getting port config for {switch_name}...")
                config['switch']['ports'][serial] = {
                    'deviceName': switch_name,
                    'model': switch.get('model'),
                    'ports': get_switch_ports(serial)
                }
        
        # Monitoring and Management
        print("  Extracting monitoring configuration...")
        config['monitoring'] = {
            'alerts': get_alerts_settings(network_id),
            'syslogServers': get_syslog_servers(network_id),
            'snmp': get_snmp_settings(network_id)
        }
        
        # Save to file
        filename = 'tst_01_config.json'
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\nConfiguration saved to {filename}")
        print(f"File size: {os.path.getsize(filename):,} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()