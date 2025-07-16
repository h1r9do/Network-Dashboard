#!/usr/bin/env python3
"""
Analyze Nexus 7K models and module data from SNMP collection
"""
import json
import csv

def analyze_nexus7k_devices():
    # Load the latest SNMP collection data
    with open('/var/www/html/network-data/nightly_snmp_collection_20250708_154906.json', 'r') as f:
        data = json.load(f)
    
    nexus7k_devices = []
    
    for device in data['devices']:
        # Check if this is a Nexus 7K device
        is_nexus7k = False
        chassis_info = None
        modules = []
        transceivers = []
        power_supplies = []
        fabric_modules = []
        
        # Look for Nexus 7K in hostname or entity data
        if '7000' in device.get('device_name', '') or 'N7K' in str(device.get('entity_data', {})):
            is_nexus7k = True
        
        for entity_id, entity_data in device.get('entity_data', {}).items():
            # Check for Nexus 7K chassis
            if entity_data.get('class') == '3':  # Chassis class
                if 'N7K' in entity_data.get('model_name', '') or '7000' in entity_data.get('description', ''):
                    is_nexus7k = True
                    chassis_info = {
                        'description': entity_data.get('description', ''),
                        'model': entity_data.get('model_name', ''),
                        'serial': entity_data.get('serial_number', ''),
                        'name': entity_data.get('name', '')
                    }
            
            # Collect module information
            elif entity_data.get('class') == '9':  # Module class
                model = entity_data.get('model_name', '').strip()
                desc = entity_data.get('description', '')
                
                # Categorize modules
                if model and model != '""':
                    module_data = {
                        'entity_id': entity_id,
                        'description': desc,
                        'model': model,
                        'name': entity_data.get('name', ''),
                        'serial': entity_data.get('serial_number', '')
                    }
                    
                    if 'FAB' in model or 'fabric' in desc.lower():
                        fabric_modules.append(module_data)
                    elif 'SUP' in model or 'supervisor' in desc.lower():
                        modules.append(module_data)  # Supervisors in main modules
                    else:
                        modules.append(module_data)
            
            # Look for power supplies
            elif entity_data.get('class') == '6':  # Power supply class
                if entity_data.get('model_name', '').strip() and entity_data.get('model_name') != '""':
                    power_supplies.append({
                        'entity_id': entity_id,
                        'description': entity_data.get('description', ''),
                        'model': entity_data.get('model_name', ''),
                        'name': entity_data.get('name', ''),
                        'serial': entity_data.get('serial_number', '')
                    })
            
            # Look for transceivers
            desc = entity_data.get('description', '').lower()
            name = entity_data.get('name', '').lower()
            model = entity_data.get('model_name', '').strip()
            if ('transceiver' in desc or 'transceiver' in name or 
                'sfp' in desc or 'qsfp' in desc or
                (model and any(x in model for x in ['GLC-', 'SFP-', 'QSFP-']))):
                if model and model != '""':
                    transceivers.append({
                        'entity_id': entity_id,
                        'description': entity_data.get('description', ''),
                        'model': model,
                        'name': entity_data.get('name', ''),
                        'class': entity_data.get('class', '')
                    })
        
        if is_nexus7k:
            nexus7k_devices.append({
                'hostname': device.get('device_name', ''),
                'ip': device.get('ip', ''),
                'chassis_info': chassis_info,
                'module_count': len(modules),
                'fabric_count': len(fabric_modules),
                'power_supply_count': len(power_supplies),
                'transceiver_count': len(transceivers),
                'modules': modules,
                'fabric_modules': fabric_modules,
                'power_supplies': power_supplies,
                'transceivers': transceivers
            })
    
    # Write summary CSV
    with open('/usr/local/bin/nexus7k_models_summary.csv', 'w', newline='') as csvfile:
        fieldnames = ['hostname', 'ip', 'chassis_model', 'chassis_serial', 
                      'chassis_description', 'module_count', 'fabric_count',
                      'power_supply_count', 'transceiver_count', 'supervisor_models',
                      'line_card_models']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for device in nexus7k_devices:
            # Extract supervisor and line card models
            supervisor_models = []
            line_card_models = []
            
            for module in device['modules']:
                if 'SUP' in module['model']:
                    supervisor_models.append(module['model'])
                else:
                    line_card_models.append(module['model'])
            
            writer.writerow({
                'hostname': device['hostname'],
                'ip': device['ip'],
                'chassis_model': device['chassis_info']['model'] if device['chassis_info'] else 'N/A',
                'chassis_serial': device['chassis_info']['serial'] if device['chassis_info'] else 'N/A',
                'chassis_description': device['chassis_info']['description'] if device['chassis_info'] else 'N/A',
                'module_count': device['module_count'],
                'fabric_count': device['fabric_count'],
                'power_supply_count': device['power_supply_count'],
                'transceiver_count': device['transceiver_count'],
                'supervisor_models': ', '.join(set(supervisor_models)),
                'line_card_models': ', '.join(set(line_card_models))
            })
    
    # Write detailed JSON for further analysis
    with open('/usr/local/bin/nexus7k_detailed_analysis.json', 'w') as f:
        json.dump(nexus7k_devices, f, indent=2)
    
    print(f"Found {len(nexus7k_devices)} Nexus 7K devices")
    for device in nexus7k_devices:
        print(f"\n{device['hostname']} ({device['ip']})")
        if device['chassis_info']:
            print(f"  Chassis: {device['chassis_info']['model']} - {device['chassis_info']['serial']}")
        else:
            print(f"  Chassis: No chassis info found")
        print(f"  Modules: {device['module_count']}")
        print(f"  Fabric Modules: {device['fabric_count']}")
        print(f"  Power Supplies: {device['power_supply_count']}")
        print(f"  Transceivers: {device['transceiver_count']}")
        
        # Show module details
        if device['modules']:
            print(f"  Module Details:")
            for m in device['modules'][:5]:  # Show first 5
                print(f"    - {m['model']}: {m['description']} (Serial: {m['serial']})")
            if len(device['modules']) > 5:
                print(f"    ... and {len(device['modules']) - 5} more modules")
        
        # Show transceiver models
        if device['transceivers']:
            unique_models = list(set([t['model'] for t in device['transceivers'] if t['model']]))
            print(f"  Transceiver Models: {', '.join(unique_models[:10])}")

if __name__ == "__main__":
    analyze_nexus7k_devices()