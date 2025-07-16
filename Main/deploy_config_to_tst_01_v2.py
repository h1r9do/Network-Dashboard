#!/usr/bin/env python3
"""
Deploy AZP 30 configuration to TST 01 with VLAN migration and NEO 07 firewall rules
Version 2 - Handles errors and dependencies
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import ipaddress

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# VLAN mapping table
VLAN_MAPPING = {
    1: 100,      # Data
    101: 200,    # Voice
    300: 300,    # AP Mgmt -> Net Mgmt (name change only)
    301: 301,    # Scanner
    801: 400,    # IOT -> IoT
    201: 410,    # Ccard
    800: 800,    # Guest
    803: 803,    # IoT Wireless
    900: 900,    # Mgmt
    802: 400     # IOT Network -> IoT (to be removed)
}

# IP changes for specific VLANs
IP_CHANGES = {
    400: {  # IOT (was 801)
        'old_subnet': '172.13.0.0/30',
        'new_subnet': '172.16.40.0/24',
        'new_appliance_ip': '172.16.40.1'
    },
    800: {  # Guest
        'old_subnet': '172.13.0.0/30',
        'new_subnet': '172.16.80.0/24',
        'new_appliance_ip': '172.16.80.1'
    }
}

# Test network prefix
TEST_NETWORK_PREFIX = '10.255.255'

def make_api_request(url, method='GET', data=None):
    """Make API request with error handling and rate limiting"""
    time.sleep(0.5)  # Basic rate limiting
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=HEADERS, timeout=30)
            
        if response.status_code == 429:
            print("Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return make_api_request(url, method, data)
            
        response.raise_for_status()
        
        if response.text:
            return response.json()
        return {}
        
    except Exception as e:
        print(f"Error {method} {url}: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def update_ip_for_test(ip_str):
    """Update IP address to use test network prefix"""
    if not ip_str or '/' not in ip_str:
        return ip_str
    
    try:
        ip_net = ipaddress.ip_network(ip_str, strict=False)
        if str(ip_net.network_address).startswith('10.'):
            # Replace first 3 octets with test prefix
            parts = str(ip_net.network_address).split('.')
            new_ip = f"{TEST_NETWORK_PREFIX}.{parts[3]}/{ip_net.prefixlen}"
            return new_ip
        return ip_str
    except:
        return ip_str

def update_appliance_ip_for_test(ip_str):
    """Update appliance IP to use test network prefix"""
    if not ip_str:
        return ip_str
    
    try:
        if ip_str.startswith('10.'):
            parts = ip_str.split('.')
            return f"{TEST_NETWORK_PREFIX}.{parts[3]}"
        return ip_str
    except:
        return ip_str

def map_vlan_in_cidr(cidr_str):
    """Map VLAN references in CIDR notation"""
    if not cidr_str or cidr_str in ['Any', 'any']:
        return cidr_str
    
    # Check if it's VLAN notation
    if cidr_str.startswith('VLAN(') and cidr_str.endswith(')'):
        vlan_str = cidr_str[5:-1]  # Extract VLAN number
        try:
            old_vlan = int(vlan_str.split(')')[0])
            new_vlan = VLAN_MAPPING.get(old_vlan, old_vlan)
            
            # Special case: VLAN 801 in firewall rules should map to 803
            if old_vlan == 801:
                new_vlan = 803
                
            return f'VLAN({new_vlan})' + vlan_str[len(str(old_vlan)):]
        except:
            return cidr_str
    
    return cidr_str

def create_group_policies(network_id, azp_group_policies):
    """Create group policies if they exist"""
    print("  Checking for group policies...")
    
    if not azp_group_policies:
        return
    
    for policy in azp_group_policies:
        if policy.get('groupPolicyId') == 100:  # The one causing issues
            print(f"    Creating group policy {policy['name']}...")
            
            policy_data = {
                'name': policy['name'],
                'scheduling': policy.get('scheduling'),
                'bandwidth': policy.get('bandwidth'),
                'firewallAndTrafficShaping': policy.get('firewallAndTrafficShaping'),
                'contentFiltering': policy.get('contentFiltering'),
                'splashAuthSettings': policy.get('splashAuthSettings', 'bypass'),
                'vlanTagging': policy.get('vlanTagging'),
                'bonjourForwarding': policy.get('bonjourForwarding')
            }
            
            url = f"{BASE_URL}/networks/{network_id}/groupPolicies"
            result = make_api_request(url, method='POST', data=policy_data)
            
            if result:
                print(f"      Created group policy: {policy['name']}")

def delete_existing_vlans(network_id):
    """Delete all existing VLANs except default"""
    print("  Deleting existing VLANs...")
    
    # Get current VLANs
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    current_vlans = make_api_request(url)
    
    if not current_vlans:
        return
    
    # Delete all non-default VLANs
    for vlan in current_vlans:
        vlan_id = vlan.get('id')
        if vlan_id != 1:  # Don't delete default VLAN
            print(f"    Deleting VLAN {vlan_id}")
            delete_url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/{vlan_id}"
            make_api_request(delete_url, method='DELETE')
            time.sleep(1)

def clean_vlan_data(vlan_data):
    """Remove fields that can't be set via API"""
    fields_to_remove = [
        'networkId', 'mask', 'groupPolicyId', 
        'templateVlanType', 'cidr'
    ]
    
    for field in fields_to_remove:
        vlan_data.pop(field, None)
    
    # Remove DHCP relay if it references IPs we don't have yet
    if vlan_data.get('dhcpHandling') == 'Relay DHCP to another server':
        vlan_data['dhcpHandling'] = 'Run a DHCP server'
        vlan_data.pop('dhcpRelayServerIps', None)
    
    return vlan_data

def create_vlans(network_id, vlans_config):
    """Create VLANs with migration rules applied"""
    print("  Creating VLANs with migration...")
    
    # First, update the default VLAN 1 to VLAN 100
    default_vlan = next((v for v in vlans_config if v['id'] == 1), None)
    if default_vlan:
        print("    Updating default VLAN 1 to VLAN 100...")
        vlan_data = default_vlan.copy()
        vlan_data['id'] = 100
        vlan_data['name'] = 'Data'
        
        # Update subnet for test network
        if vlan_data.get('subnet'):
            vlan_data['subnet'] = update_ip_for_test(vlan_data['subnet'])
        if vlan_data.get('applianceIp'):
            vlan_data['applianceIp'] = update_appliance_ip_for_test(vlan_data['applianceIp'])
        
        # Clean up
        vlan_data = clean_vlan_data(vlan_data)
        
        url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/1"
        result = make_api_request(url, method='PUT', data=vlan_data)
        if result:
            print(f"      Updated default VLAN to 100")
        time.sleep(1)
    
    # Create other VLANs
    for vlan in vlans_config:
        old_vlan_id = vlan['id']
        
        # Skip default VLAN (already updated) and VLAN 802
        if old_vlan_id == 1 or old_vlan_id == 802:
            continue
        
        # Map to new VLAN ID
        new_vlan_id = VLAN_MAPPING.get(old_vlan_id, old_vlan_id)
        
        print(f"    Creating VLAN {new_vlan_id} (was {old_vlan_id})...")
        
        vlan_data = vlan.copy()
        vlan_data['id'] = new_vlan_id
        
        # Update VLAN name for specific cases
        if new_vlan_id == 300:
            vlan_data['name'] = 'Net Mgmt'
        elif new_vlan_id == 400:
            vlan_data['name'] = 'IoT'
        
        # Apply IP changes for specific VLANs
        if new_vlan_id in IP_CHANGES:
            ip_config = IP_CHANGES[new_vlan_id]
            vlan_data['subnet'] = ip_config['new_subnet']
            vlan_data['applianceIp'] = ip_config['new_appliance_ip']
        else:
            # Update subnet for test network (10.x.x.x -> 10.255.255.x)
            if vlan_data.get('subnet'):
                vlan_data['subnet'] = update_ip_for_test(vlan_data['subnet'])
            if vlan_data.get('applianceIp'):
                vlan_data['applianceIp'] = update_appliance_ip_for_test(vlan_data['applianceIp'])
        
        # Clean up
        vlan_data = clean_vlan_data(vlan_data)
        
        url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
        result = make_api_request(url, method='POST', data=vlan_data)
        
        if result:
            print(f"      Created VLAN {new_vlan_id}")
        time.sleep(1)

def update_switch_ports(network_id, devices, azp_switch_config):
    """Update switch port configurations with VLAN mapping"""
    print("  Updating switch port configurations...")
    
    # Get current switches in TST 01
    tst_switches = [d for d in devices if d.get('model', '').startswith('MS')]
    
    if not tst_switches or not azp_switch_config.get('ports'):
        print("    No switches to configure")
        return
    
    # Get port configurations from AZP 30
    azp_ports_data = azp_switch_config['ports']
    
    # Find the first switch serial in AZP config
    first_serial = list(azp_ports_data.keys())[0]
    azp_ports_config = azp_ports_data[first_serial]['ports']
    
    for switch in tst_switches:
        serial = switch['serial']
        switch_name = switch.get('name', serial)
        print(f"    Configuring ports for {switch_name}...")
        
        # Apply port config from AZP 30
        for port_config in azp_ports_config:
            port_data = port_config.copy()
            
            # Map VLAN IDs
            if 'vlan' in port_data and port_data['vlan']:
                old_vlan = port_data['vlan']
                # Map 802 to 400
                if old_vlan == 802:
                    port_data['vlan'] = 400
                else:
                    port_data['vlan'] = VLAN_MAPPING.get(old_vlan, old_vlan)
            
            # Map allowed VLANs
            if 'allowedVlans' in port_data and port_data['allowedVlans']:
                allowed = port_data['allowedVlans']
                if allowed != 'all':
                    # Parse and map VLAN list
                    vlan_list = []
                    for vlan_range in allowed.split(','):
                        if '-' in vlan_range:
                            # Handle range
                            start, end = vlan_range.split('-')
                            start_mapped = VLAN_MAPPING.get(int(start), int(start))
                            end_mapped = VLAN_MAPPING.get(int(end), int(end))
                            vlan_list.append(f"{start_mapped}-{end_mapped}")
                        else:
                            # Single VLAN
                            old_vlan = int(vlan_range)
                            new_vlan = VLAN_MAPPING.get(old_vlan, old_vlan)
                            if old_vlan == 802:
                                new_vlan = 400
                            vlan_list.append(str(new_vlan))
                    
                    port_data['allowedVlans'] = ','.join(vlan_list)
            
            # Clean up fields
            for field in ['portId', 'linkNegotiationCapabilities', 'warnings', 'errors']:
                port_data.pop(field, None)
            
            # Apply to port
            port_number = port_config['portId']
            url = f"{BASE_URL}/devices/{serial}/switch/ports/{port_number}"
            result = make_api_request(url, method='PUT', data=port_data)
            
            if result:
                print(f"      Updated port {port_number}")

def apply_firewall_rules(network_id, neo_firewall_rules):
    """Apply firewall rules from NEO 07 with VLAN mapping"""
    print("  Applying firewall rules from NEO 07...")
    
    # First, ensure syslog is disabled on all rules
    mapped_rules = []
    for rule in neo_firewall_rules:
        new_rule = rule.copy()
        
        # Disable syslog (TST 01 doesn't have syslog server configured)
        new_rule['syslogEnabled'] = False
        
        # Map source CIDR VLANs
        if 'srcCidr' in new_rule:
            new_rule['srcCidr'] = map_vlan_in_cidr(new_rule['srcCidr'])
        
        # Map destination CIDR VLANs
        if 'destCidr' in new_rule:
            new_rule['destCidr'] = map_vlan_in_cidr(new_rule['destCidr'])
        
        mapped_rules.append(new_rule)
    
    # Apply rules
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    data = {'rules': mapped_rules}
    
    result = make_api_request(url, method='PUT', data=data)
    if result:
        print(f"    Applied {len(mapped_rules)} firewall rules")

def update_ssid_tagging(network_id):
    """Update SSID tagging for IoT Wireless to VLAN 803"""
    print("  Checking for wireless SSIDs...")
    
    # Get SSIDs
    url = f"{BASE_URL}/networks/{network_id}/wireless/ssids"
    ssids = make_api_request(url)
    
    if not ssids:
        print("    No wireless SSIDs found")
        return
    
    # Update IoT Wireless SSID
    for ssid in ssids:
        if 'IoT' in ssid.get('name', '') or 'iot' in ssid.get('name', '').lower():
            ssid_number = ssid['number']
            print(f"    Updating SSID {ssid['name']} to use VLAN 803...")
            
            ssid_data = {
                'defaultVlanId': 803
            }
            
            url = f"{BASE_URL}/networks/{network_id}/wireless/ssids/{ssid_number}"
            result = make_api_request(url, method='PUT', data=ssid_data)
            
            if result:
                print(f"      Updated SSID to use VLAN 803")

def apply_mx_settings(network_id, azp_appliance_config):
    """Apply other MX settings from AZP 30"""
    print("  Applying additional MX settings...")
    
    # Apply static routes
    if azp_appliance_config.get('staticRoutes'):
        print("    Applying static routes...")
        for route in azp_appliance_config['staticRoutes']:
            route_data = route.copy()
            # Update subnet if it's a 10.x network
            if route_data.get('subnet'):
                route_data['subnet'] = update_ip_for_test(route_data['subnet'])
            if route_data.get('gatewayIp'):
                route_data['gatewayIp'] = update_appliance_ip_for_test(route_data['gatewayIp'])
            
            # Remove fields that can't be set
            route_data.pop('staticRouteId', None)
            
            url = f"{BASE_URL}/networks/{network_id}/appliance/staticRoutes"
            make_api_request(url, method='POST', data=route_data)
    
    # Apply content filtering
    if azp_appliance_config.get('contentFiltering'):
        print("    Applying content filtering...")
        url = f"{BASE_URL}/networks/{network_id}/appliance/contentFiltering"
        cf_data = azp_appliance_config['contentFiltering'].copy()
        # Remove read-only fields
        cf_data.pop('categories', None)
        make_api_request(url, method='PUT', data=cf_data)
    
    # Apply traffic shaping
    if azp_appliance_config.get('trafficShaping'):
        print("    Applying traffic shaping...")
        url = f"{BASE_URL}/networks/{network_id}/appliance/trafficShaping"
        ts_data = azp_appliance_config['trafficShaping'].copy()
        make_api_request(url, method='PUT', data=ts_data)
    
    # Apply intrusion settings
    if azp_appliance_config.get('intrusion'):
        print("    Applying intrusion settings...")
        url = f"{BASE_URL}/networks/{network_id}/appliance/security/intrusion"
        intrusion_data = azp_appliance_config['intrusion'].copy()
        make_api_request(url, method='PUT', data=intrusion_data)
    
    # Apply malware settings
    if azp_appliance_config.get('malware'):
        print("    Applying malware settings...")
        url = f"{BASE_URL}/networks/{network_id}/appliance/security/malware"
        malware_data = azp_appliance_config['malware'].copy()
        make_api_request(url, method='PUT', data=malware_data)

def main():
    """Main deployment function"""
    print("Starting configuration deployment to TST 01...")
    print(f"Using test network prefix: {TEST_NETWORK_PREFIX}")
    
    try:
        # Load configurations
        print("\nLoading configuration files...")
        
        with open('azp_30_config.json', 'r') as f:
            azp_config = json.load(f)
        print("  Loaded AZP 30 configuration")
        
        with open('neo_07_config.json', 'r') as f:
            neo_config = json.load(f)
        print("  Loaded NEO 07 configuration")
        
        with open('tst_01_config.json', 'r') as f:
            tst_config = json.load(f)
        print("  Loaded TST 01 configuration")
        
        # Target network
        network_id = "L_3790904986339115852"  # TST 01
        print(f"\nTarget network: TST 01 (ID: {network_id})")
        
        # Get current devices
        devices = tst_config['devices']
        
        # Step 0: Create group policies if needed
        if azp_config['appliance'].get('groupPolicies'):
            create_group_policies(network_id, azp_config['appliance']['groupPolicies'])
        
        # Step 1: Delete existing VLANs
        delete_existing_vlans(network_id)
        
        # Step 2: Create VLANs with migration
        create_vlans(network_id, azp_config['appliance']['vlans'])
        
        # Step 3: Apply firewall rules from NEO 07
        apply_firewall_rules(network_id, neo_config['appliance']['l3FirewallRules'])
        
        # Step 4: Update switch ports
        update_switch_ports(network_id, devices, azp_config['switch'])
        
        # Step 5: Apply other MX settings
        apply_mx_settings(network_id, azp_config['appliance'])
        
        # Step 6: Update SSID tagging
        update_ssid_tagging(network_id)
        
        print("\n✅ Configuration deployment complete!")
        print("\nSummary of changes:")
        print("- Migrated VLANs with new IDs and IPs")
        print("- Applied firewall rules from NEO 07 with VLAN mapping")
        print("- Updated switch port configurations")
        print("- Applied MX settings from AZP 30")
        print("- Updated IoT Wireless SSID to use VLAN 803")
        
    except Exception as e:
        print(f"\n❌ Error during deployment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()