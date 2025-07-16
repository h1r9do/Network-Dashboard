#!/usr/bin/env python3
"""Check 20 stores from mx_inventory_live.json to compare WAN IPs and provider information"""

import json
import os

# Load the mx_inventory_live.json file
json_file = '/var/www/html/meraki-data/mx_inventory_live.json'

if os.path.exists(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print("Store Name | WAN1 IP | WAN1 Provider | WAN2 IP | WAN2 Provider")
    print("-" * 80)
    
    count = 0
    for entry in data:
        if count >= 20:
            break
            
        wan1_data = entry.get('wan1', {})
        wan2_data = entry.get('wan2', {})
        
        # Only show stores that have at least one IP
        if wan1_data.get('ip') or wan2_data.get('ip'):
            store_name = entry.get('network_name', 'N/A')
            wan1_ip = wan1_data.get('ip', 'N/A')
            wan1_provider = wan1_data.get('provider', 'N/A')
            wan2_ip = wan2_data.get('ip', 'N/A')
            wan2_provider = wan2_data.get('provider', 'N/A')
            
            print(f"{store_name} | {wan1_ip} | {wan1_provider} | {wan2_ip} | {wan2_provider}")
            count += 1
    
    # Also check some known stores
    print("\n\nChecking specific stores (CAN 40, AZP 63, etc.):")
    print("-" * 80)
    
    specific_stores = ['CAN 40', 'AZP 63', 'CAL 01', 'ALB 03', 'AZT 10']
    
    for store in specific_stores:
        for entry in data:
            if entry.get('network_name') == store:
                wan1_data = entry.get('wan1', {})
                wan2_data = entry.get('wan2', {})
                
                wan1_ip = wan1_data.get('ip', 'N/A')
                wan1_provider = wan1_data.get('provider', 'N/A')
                wan2_ip = wan2_data.get('ip', 'N/A') 
                wan2_provider = wan2_data.get('provider', 'N/A')
                
                print(f"{store} | {wan1_ip} | {wan1_provider} | {wan2_ip} | {wan2_provider}")
                break
else:
    print(f"Error: {json_file} not found")