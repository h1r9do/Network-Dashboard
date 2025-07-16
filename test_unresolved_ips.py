#!/usr/bin/env python3
"""
Test ARIN lookups for unresolved IPs
"""

import requests
import time

test_ips = [
    ('TXHT00 - WAN1', '75.148.163.185'),
    ('NMAW00 - WAN1', '96.92.78.213'),
    ('AZP 20 - WAN1', '208.77.60.230'),
    ('AZP 25 - WAN1', '98.174.253.101'),
    ('AZP 25 - WAN2', '166.253.101.52')
]

print('Testing ARIN lookups for unresolved IPs:')
print('-' * 80)

for site_info, ip in test_ips:
    print(f'\n{site_info}: {ip}')
    try:
        rdap_url = f'https://rdap.arin.net/registry/ip/{ip}'
        response = requests.get(rdap_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            network_name = data.get('name', '')
            
            # Try to find org name in entities
            entities = data.get('entities', [])
            org_name = None
            
            for entity in entities:
                vcard = entity.get('vcardArray', [])
                if vcard and len(vcard) > 1:
                    for prop in vcard[1]:
                        if len(prop) >= 4 and prop[0] == 'fn' and prop[2] == 'text':
                            candidate = prop[3]
                            if 'org' in entity.get('roles', []):
                                org_name = candidate
                                break
            
            provider = org_name or network_name or 'No provider found'
            print(f'  ✅ ARIN lookup successful: {provider}')
            
            # Show more details
            if network_name:
                print(f'     Network: {network_name}')
            if org_name and org_name != network_name:
                print(f'     Organization: {org_name}')
                
        else:
            print(f'  ❌ HTTP {response.status_code}')
            
    except Exception as e:
        print(f'  ❌ Error: {type(e).__name__}: {str(e)}')
    
    time.sleep(0.5)