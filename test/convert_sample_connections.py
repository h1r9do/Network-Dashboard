#!/usr/bin/env python3
"""
Convert sample connections to full format
"""

import json

# Read sample
with open('/var/www/html/meraki-data/device_connections_sample.json', 'r') as f:
    sample = json.load(f)

# Convert to full format
full_format = {
    'generated': '2025-07-04T11:30:00',
    'total_devices': len(sample),
    'devices': {}
}

for hostname, info in sample.items():
    full_format['devices'][hostname] = {
        'hostname': hostname,
        'ip': info['ip'],
        'device_type': 'Switch',
        'site': 'Alameda' if info['ip'].startswith('10.101') else 'HQ',
        'model': 'Nexus' if '7000' in hostname or '5000' in hostname else 'Catalyst',
        'connections': []
    }
    
    if info['ssh_works']:
        full_format['devices'][hostname]['connections'].append({
            'method': 'ssh',
            'username': 'mbambic',
            'password': 'Aud!o!994',
            'port': 22,
            'status': 'success',
            'message': 'SSH connection successful'
        })
    
    if info['snmp_works'] and info['snmp_community']:
        full_format['devices'][hostname]['connections'].append({
            'method': 'snmp',
            'community': info['snmp_community'],
            'version': 'v2c',
            'status': 'success',
            'message': 'SNMP connection successful',
            'source': 'device'
        })

# Save
with open('/var/www/html/meraki-data/device_connections_sample_full.json', 'w') as f:
    json.dump(full_format, f, indent=2)

print("Converted to full format")