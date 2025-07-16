#!/usr/bin/env python3
"""
Analyze DHCP Configuration from AZP 30
"""

import json

# Load AZP 30 config
with open('azp_30_config.json', 'r') as f:
    config = json.load(f)

vlans = config['appliance']['vlans']

print("AZP 30 DHCP Configuration Analysis:")
print("=" * 50)

for vlan in vlans:
    vlan_id = vlan['id']
    name = vlan['name']
    dhcp_handling = vlan.get('dhcpHandling', 'Not specified')
    dns_servers = vlan.get('dnsNameservers', 'Not specified')
    relay_servers = vlan.get('dhcpRelayServerIps', [])
    
    print(f"\nVLAN {vlan_id} ({name}):")
    print(f"  DHCP Handling: {dhcp_handling}")
    print(f"  DNS Servers: {dns_servers}")
    if relay_servers:
        print(f"  DHCP Relay Servers: {', '.join(relay_servers)}")

print("\n" + "=" * 50)
print("Summary:")

relay_vlans = [v for v in vlans if v.get('dhcpHandling') == 'Relay DHCP to another server']
server_vlans = [v for v in vlans if v.get('dhcpHandling') == 'Run a DHCP server']

print(f"\nVLANs using DHCP Relay ({len(relay_vlans)}):")
for vlan in relay_vlans:
    print(f"  VLAN {vlan['id']} ({vlan['name']})")

print(f"\nVLANs running DHCP Server ({len(server_vlans)}):")
for vlan in server_vlans:
    print(f"  VLAN {vlan['id']} ({vlan['name']})")