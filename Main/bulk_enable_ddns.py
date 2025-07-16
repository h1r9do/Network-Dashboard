#!/usr/bin/env python3
"""
Bulk Enable DDNS for Meraki MX Devices
Enables DDNS for all store networks (not tagged with 'hub')
"""

import os
import sys
import time
import re
from dotenv import load_dotenv
import meraki

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
api_key = os.getenv('MERAKI_API_KEY')

if not api_key:
    print('Error: MERAKI_API_KEY not found in environment')
    sys.exit(1)

dashboard = meraki.DashboardAPI(api_key, suppress_logging=True)

def get_store_networks():
    """Get all store networks (not tagged with 'hub')"""
    print('Getting organization networks...')
    
    # Get target organization
    orgs = dashboard.organizations.getOrganizations()
    target_org = None
    for org in orgs:
        if 'DTC-Store-Inventory-All' in org['name']:
            target_org = org
            break
    
    if not target_org:
        print('Error: Target organization not found')
        return []
    
    # Get all networks
    networks = dashboard.organizations.getOrganizationNetworks(target_org['id'])
    store_networks = []
    
    for network in networks:
        network_tags = network.get('tags', [])
        network_name = network['name']
        
        # Skip hub-tagged networks
        if any('hub' in tag.lower() for tag in network_tags):
            continue
        
        # Check if network name looks like a store (3 letters followed by space and numbers)
        if re.match(r'^[A-Z]{2,3}\s+\d+$', network_name):
            store_networks.append(network)
    
    return store_networks

def enable_ddns_batch(networks, start_index=0, batch_size=50):
    """Enable DDNS for a batch of networks"""
    print(f'Processing networks {start_index} to {start_index + batch_size}...')
    
    enabled_count = 0
    already_enabled_count = 0
    errors = []
    
    end_index = min(start_index + batch_size, len(networks))
    
    for i in range(start_index, end_index):
        network = networks[i]
        network_id = network['id']
        network_name = network['name']
        
        try:
            # Check current DDNS status
            settings = dashboard.appliance.getNetworkApplianceSettings(network_id)
            ddns_settings = settings.get('dynamicDns', {})
            
            current_enabled = ddns_settings.get('enabled', False)
            current_url = ddns_settings.get('url', '')
            
            if current_enabled:
                already_enabled_count += 1
                print(f'  {i+1:3d}. {network_name:10s} - ALREADY ENABLED')
            else:
                # Generate prefix from network name (lowercase, replace space with dash)
                prefix = network_name.lower().replace(' ', '-')
                
                response = dashboard.appliance.updateNetworkApplianceSettings(
                    network_id,
                    dynamicDns={
                        'enabled': True,
                        'prefix': prefix
                    }
                )
                
                enabled_count += 1
                new_url = response.get('dynamicDns', {}).get('url', 'N/A')
                print(f'  {i+1:3d}. {network_name:10s} - ENABLED -> {new_url}')
            
        except Exception as e:
            errors.append(f'{network_name}: {str(e)}')
            print(f'  {i+1:3d}. {network_name:10s} - ERROR: {str(e)}')
        
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
    return enabled_count, already_enabled_count, errors

def main():
    print('=== Bulk DDNS Enablement for Meraki MX Devices ===')
    print()
    
    # Get all store networks
    store_networks = get_store_networks()
    print(f'Found {len(store_networks)} store networks (excluding hub-tagged)')
    print()
    
    # Process in batches
    batch_size = 50
    total_enabled = 0
    total_already_enabled = 0
    total_errors = []
    
    for start_index in range(0, len(store_networks), batch_size):
        enabled, already_enabled, errors = enable_ddns_batch(
            store_networks, start_index, batch_size
        )
        
        total_enabled += enabled
        total_already_enabled += already_enabled
        total_errors.extend(errors)
        
        print(f'Batch summary: {enabled} enabled, {already_enabled} already enabled, {len(errors)} errors')
        print()
        
        # Longer delay between batches
        if start_index + batch_size < len(store_networks):
            print('Waiting 10 seconds before next batch...')
            time.sleep(10)
    
    print('=== Final Summary ===')
    print(f'Total networks processed: {len(store_networks)}')
    print(f'Newly enabled: {total_enabled}')
    print(f'Already enabled: {total_already_enabled}')
    print(f'Errors: {len(total_errors)}')
    
    if total_errors:
        print()
        print('Errors encountered:')
        for error in total_errors:
            print(f'  - {error}')

if __name__ == '__main__':
    main()