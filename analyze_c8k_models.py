#!/usr/bin/env python3
"""
Analyze C8K router models and SFP data from SNMP collection
"""
import json
import csv

def analyze_c8k_devices():
    # Load the latest SNMP collection data
    with open('/var/www/html/network-data/nightly_snmp_collection_20250708_154906.json', 'r') as f:
        data = json.load(f)
    
    c8k_devices = []
    
    for device in data['devices']:
        # Check if this is a C8K device by looking at entity data
        is_c8k = False
        chassis_info = None
        modules = []
        transceivers = []
        
        for entity_id, entity_data in device.get('entity_data', {}).items():
            # Check for C8K chassis
            if entity_data.get('class') == '3':  # Chassis class
                if 'C8' in entity_data.get('model_name', ''):
                    is_c8k = True
                    chassis_info = {
                        'description': entity_data.get('description', ''),
                        'model': entity_data.get('model_name', ''),
                        'serial': entity_data.get('serial_number', '')
                    }
            
            # Collect module information
            elif entity_data.get('class') == '9':  # Module class
                if entity_data.get('model_name', '').strip() and entity_data.get('model_name') != '""':
                    modules.append({
                        'description': entity_data.get('description', ''),
                        'model': entity_data.get('model_name', ''),
                        'name': entity_data.get('name', ''),
                        'serial': entity_data.get('serial_number', '')
                    })
            
            # Look for transceivers
            desc = entity_data.get('description', '').lower()
            name = entity_data.get('name', '').lower()
            if 'transceiver' in desc or 'transceiver' in name:
                transceivers.append({
                    'entity_id': entity_id,
                    'description': entity_data.get('description', ''),
                    'model': entity_data.get('model_name', ''),
                    'name': entity_data.get('name', ''),
                    'class': entity_data.get('class', '')
                })
        
        if is_c8k and chassis_info:
            c8k_devices.append({
                'hostname': device.get('device_name', ''),
                'ip': device.get('ip', ''),
                'chassis_model': chassis_info['model'],
                'chassis_serial': chassis_info['serial'],
                'chassis_description': chassis_info['description'],
                'module_count': len(modules),
                'transceiver_count': len(transceivers),
                'modules': modules,
                'transceivers': transceivers
            })
    
    # Write summary CSV
    with open('/usr/local/bin/c8k_models_summary.csv', 'w', newline='') as csvfile:
        fieldnames = ['hostname', 'ip', 'chassis_model', 'chassis_serial', 
                      'chassis_description', 'module_count', 'transceiver_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for device in c8k_devices:
            writer.writerow({
                'hostname': device['hostname'],
                'ip': device['ip'],
                'chassis_model': device['chassis_model'],
                'chassis_serial': device['chassis_serial'],
                'chassis_description': device['chassis_description'],
                'module_count': device['module_count'],
                'transceiver_count': device['transceiver_count']
            })
    
    # Write detailed JSON for further analysis
    with open('/usr/local/bin/c8k_detailed_analysis.json', 'w') as f:
        json.dump(c8k_devices, f, indent=2)
    
    print(f"Found {len(c8k_devices)} C8K devices")
    for device in c8k_devices:
        print(f"\n{device['hostname']} ({device['ip']})")
        print(f"  Chassis: {device['chassis_model']} - {device['chassis_serial']}")
        print(f"  Modules: {device['module_count']}")
        print(f"  Transceivers: {device['transceiver_count']}")
        
        # Show transceiver details
        if device['transceivers']:
            print(f"  Transceiver Details:")
            for t in device['transceivers']:
                print(f"    - {t['description']} (Class: {t['class']}, Model: {t['model']})")

if __name__ == "__main__":
    analyze_c8k_devices()