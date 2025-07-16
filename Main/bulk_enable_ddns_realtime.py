#!/usr/bin/env python3
"""
Real-time Bulk Enable DDNS for Meraki MX Devices
Provides immediate feedback and progress tracking
"""

import os
import sys
import time
import re
from dotenv import load_dotenv
import meraki
from datetime import datetime

# Force immediate output
class FlushingOutput:
    def __init__(self, file):
        self.file = file
    
    def write(self, data):
        self.file.write(data)
        self.file.flush()
    
    def flush(self):
        self.file.flush()

sys.stdout = FlushingOutput(sys.stdout)

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
api_key = os.getenv('MERAKI_API_KEY')

if not api_key:
    print('Error: MERAKI_API_KEY not found in environment')
    sys.exit(1)

print(f'[{datetime.now().strftime("%H:%M:%S")}] Initializing Meraki API...')
dashboard = meraki.DashboardAPI(api_key, suppress_logging=True)

def get_store_networks():
    """Get all store networks (not tagged with 'hub')"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Getting organization information...')
    
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
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Found organization: {target_org["name"]}')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Getting all networks...')
    
    # Get all networks
    networks = dashboard.organizations.getOrganizationNetworks(target_org['id'])
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Retrieved {len(networks)} total networks')
    
    store_networks = []
    hub_networks = []
    
    for i, network in enumerate(networks):
        if i % 100 == 0:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Processing network {i+1}/{len(networks)}...')
        
        network_tags = network.get('tags', [])
        network_name = network['name']
        
        # Check if hub-tagged
        if any('hub' in tag.lower() for tag in network_tags):
            hub_networks.append(network_name)
            continue
        
        # Check if network name looks like a store (3 letters followed by space and numbers)
        if re.match(r'^[A-Z]{2,3}\s+\d+$', network_name):
            store_networks.append(network)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Found {len(store_networks)} store networks, {len(hub_networks)} hub networks')
    return store_networks

def enable_ddns_batch(networks, start_index=0, batch_size=10):
    """Enable DDNS for a batch of networks"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] === BATCH {start_index//batch_size + 1} ===')
    print(f'Processing networks {start_index+1} to {min(start_index + batch_size, len(networks))}')
    
    enabled_count = 0
    already_enabled_count = 0
    errors = []
    
    end_index = min(start_index + batch_size, len(networks))
    
    for i in range(start_index, end_index):
        network = networks[i]
        network_id = network['id']
        network_name = network['name']
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}]   {i+1:3d}. {network_name:10s} - ', end='')
        
        try:
            # Check current DDNS status
            settings = dashboard.appliance.getNetworkApplianceSettings(network_id)
            ddns_settings = settings.get('dynamicDns', {})
            
            current_enabled = ddns_settings.get('enabled', False)
            
            if current_enabled:
                already_enabled_count += 1
                print('ALREADY ENABLED')
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
                print(f'ENABLED -> {new_url}')
            
        except Exception as e:
            errors.append(f'{network_name}: {str(e)}')
            print(f'ERROR: {str(e)}')
        
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Batch summary: {enabled_count} enabled, {already_enabled_count} already enabled, {len(errors)} errors')
    return enabled_count, already_enabled_count, errors

def main():
    """Main execution with real-time progress"""
    print('=== Real-time Bulk DDNS Enablement ===')
    print(f'Started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Get all store networks
    store_networks = get_store_networks()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Ready to process {len(store_networks)} store networks')
    
    # Process in batches
    batch_size = 10
    total_enabled = 0
    total_already_enabled = 0
    total_errors = []
    
    total_batches = (len(store_networks) + batch_size - 1) // batch_size
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Will process {total_batches} batches of {batch_size} networks each')
    
    for batch_num in range(total_batches):
        start_index = batch_num * batch_size
        
        enabled, already_enabled, errors = enable_ddns_batch(
            store_networks, start_index, batch_size
        )
        
        total_enabled += enabled
        total_already_enabled += already_enabled
        total_errors.extend(errors)
        
        # Progress update
        networks_processed = min((batch_num + 1) * batch_size, len(store_networks))
        progress_pct = (networks_processed / len(store_networks)) * 100
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Overall progress: {networks_processed}/{len(store_networks)} ({progress_pct:.1f}%)')
        
        # Break after first few batches for testing
        if batch_num >= 4:  # Process first 5 batches (50 networks) as a test
            print(f'[{datetime.now().strftime("%H:%M:%S")}] STOPPING AFTER 5 BATCHES FOR TESTING')
            break
        
        # Delay between batches
        if start_index + batch_size < len(store_networks) and batch_num < 4:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Waiting 10 seconds before next batch...')
            time.sleep(10)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] === SUMMARY ===')
    print(f'Networks processed: {min(50, len(store_networks))} of {len(store_networks)}')
    print(f'Newly enabled: {total_enabled}')
    print(f'Already enabled: {total_already_enabled}')
    print(f'Errors: {len(total_errors)}')
    
    if total_errors:
        print('Errors encountered:')
        for error in total_errors:
            print(f'  - {error}')

if __name__ == '__main__':
    main()