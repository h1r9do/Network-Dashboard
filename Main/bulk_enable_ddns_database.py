#!/usr/bin/env python3
"""
Database-driven Bulk DDNS Enablement
Uses complete network list from database instead of API pagination
"""

import os
import sys
import time
from dotenv import load_dotenv
import meraki
from datetime import datetime

# Database imports
sys.path.append('/usr/local/bin/test')
from config import Config
import psycopg2

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

print(f'[{datetime.now().strftime("%H:%M:%S")}] Initializing systems...')
dashboard = meraki.DashboardAPI(api_key, suppress_logging=True)

def get_networks_from_database():
    """Get all MX networks from database"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Connecting to database...')
    
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    cur = conn.cursor()
    
    # Get all MX store networks (exclude hub networks)
    query = '''
    SELECT DISTINCT network_id, network_name, device_serial, device_model
    FROM meraki_inventory 
    WHERE device_model LIKE 'MX%'
    AND network_name IS NOT NULL
    AND network_name NOT LIKE '%HUB%'
    AND network_name NOT LIKE '%hub%'
    ORDER BY network_name;
    '''
    
    cur.execute(query)
    results = cur.fetchall()
    
    networks = []
    for network_id, network_name, device_serial, device_model in results:
        networks.append({
            'id': network_id,
            'name': network_name,
            'serial': device_serial,
            'model': device_model
        })
    
    conn.close()
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Found {len(networks)} store networks in database')
    return networks

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
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}]   {i+1:4d}. {network_name:10s} - ', end='')
        
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
        time.sleep(0.3)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Batch summary: {enabled_count} enabled, {already_enabled_count} already enabled, {len(errors)} errors')
    return enabled_count, already_enabled_count, errors

def main():
    """Main execution using database-driven network list"""
    print('=== Database-driven Bulk DDNS Enablement ===')
    print(f'Started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Get all networks from database
    networks = get_networks_from_database()
    
    if not networks:
        print('Error: No networks found in database')
        sys.exit(1)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Ready to process {len(networks)} store networks')
    
    # Ask for confirmation for full deployment
    total_batches = (len(networks) + 9) // 10  # 10 networks per batch
    estimated_hours = (len(networks) * 0.5) / 60  # 0.5 seconds per network
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] This will process {total_batches} batches')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Estimated time: {estimated_hours:.1f} minutes')
    print()
    
    # For safety, limit to first 100 networks unless specifically requested
    PROCESS_LIMIT = 100
    if len(networks) > PROCESS_LIMIT:
        print(f'[{datetime.now().strftime("%H:%M:%S")}] SAFETY LIMIT: Processing first {PROCESS_LIMIT} networks only')
        print(f'[{datetime.now().strftime("%H:%M:%S")}] To process all {len(networks)}, modify PROCESS_LIMIT in script')
        networks = networks[:PROCESS_LIMIT]
    
    # Process in batches
    batch_size = 10
    total_enabled = 0
    total_already_enabled = 0
    total_errors = []
    
    total_batches = (len(networks) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_index = batch_num * batch_size
        
        enabled, already_enabled, errors = enable_ddns_batch(
            networks, start_index, batch_size
        )
        
        total_enabled += enabled
        total_already_enabled += already_enabled
        total_errors.extend(errors)
        
        # Progress update
        networks_processed = min((batch_num + 1) * batch_size, len(networks))
        progress_pct = (networks_processed / len(networks)) * 100
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Overall progress: {networks_processed}/{len(networks)} ({progress_pct:.1f}%)')
        
        # Delay between batches
        if start_index + batch_size < len(networks):
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Waiting 5 seconds before next batch...')
            time.sleep(5)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] === FINAL SUMMARY ===')
    print(f'Completed at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Networks processed: {len(networks)}')
    print(f'Newly enabled: {total_enabled}')
    print(f'Already enabled: {total_already_enabled}')
    print(f'Errors: {len(total_errors)}')
    print(f'Success rate: {((total_enabled + total_already_enabled) / len(networks) * 100):.1f}%')
    
    if total_errors:
        print()
        print('Errors encountered:')
        for error in total_errors:
            print(f'  - {error}')

if __name__ == '__main__':
    main()