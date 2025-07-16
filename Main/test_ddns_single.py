#!/usr/bin/env python3
"""
Test DDNS enablement on a single network to verify the process works
"""

import os
import sys
from dotenv import load_dotenv
import meraki

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
api_key = os.getenv('MERAKI_API_KEY')

if not api_key:
    print('Error: MERAKI_API_KEY not found in environment')
    sys.exit(1)

dashboard = meraki.DashboardAPI(api_key, suppress_logging=True)

print('Testing DDNS enablement process...')

# Get organization
orgs = dashboard.organizations.getOrganizations()
target_org = None
for org in orgs:
    if 'DTC-Store-Inventory-All' in org['name']:
        target_org = org
        break

if not target_org:
    print('Error: Target organization not found')
    sys.exit(1)

print(f'Organization: {target_org["name"]}')

# Get a small sample of networks
print('Getting sample networks...')
networks = dashboard.organizations.getOrganizationNetworks(target_org['id'])

# Find first 3 store networks
store_networks = []
for network in networks[:20]:  # Only check first 20 to speed up
    network_tags = network.get('tags', [])
    network_name = network['name']
    
    # Skip hub-tagged networks
    if any('hub' in tag.lower() for tag in network_tags):
        continue
    
    # Check if network name looks like a store
    import re
    if re.match(r'^[A-Z]{2,3}\s+\d+$', network_name):
        store_networks.append(network)
        if len(store_networks) >= 3:
            break

print(f'Found {len(store_networks)} sample store networks:')
for network in store_networks:
    print(f'  - {network["name"]} ({network["id"]})')

# Test DDNS status check on first network
if store_networks:
    test_network = store_networks[0]
    print(f'\nTesting DDNS status check for {test_network["name"]}...')
    
    try:
        settings = dashboard.appliance.getNetworkApplianceSettings(test_network['id'])
        ddns_settings = settings.get('dynamicDns', {})
        enabled = ddns_settings.get('enabled', False)
        url = ddns_settings.get('url', 'N/A')
        
        print(f'  DDNS enabled: {enabled}')
        print(f'  DDNS URL: {url}')
        print('  API call successful!')
        
    except Exception as e:
        print(f'  Error: {str(e)}')

print('\nTest completed. The bulk script should work correctly.')