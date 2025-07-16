#!/usr/bin/env python3
"""
Analyze "Unspecified" SFPs to see if we can extract model info from descriptions
"""
import json

def analyze_unspecified_sfps():
    with open('/var/www/html/network-data/nightly_snmp_collection_20250708_154906.json', 'r') as f:
        data = json.load(f)
    
    unspecified_sfps = []
    all_sfp_descriptions = {}
    
    for device in data['devices']:
        for entity_id, entity in device.get('entity_data', {}).items():
            desc = entity.get('description', '')
            model = entity.get('model_name', '')
            serial = entity.get('serial_number', '').strip()
            
            # Look for SFP-like entities
            if (('SFP' in desc or 'BaseTX' in desc or 'BaseSX' in desc or 
                 'BaseLX' in desc or 'BaseT' in desc) and 
                entity.get('class') == '10' and serial and serial != '""'):
                
                # Track all descriptions for pattern analysis
                if desc not in all_sfp_descriptions:
                    all_sfp_descriptions[desc] = []
                all_sfp_descriptions[desc].append(model)
                
                if model == 'Unspecified':
                    unspecified_sfps.append({
                        'device': device.get('device_name', ''),
                        'description': desc,
                        'serial': serial,
                        'name': entity.get('name', '')
                    })
    
    print("=== SFP Description to Model Mapping ===")
    for desc, models in sorted(all_sfp_descriptions.items()):
        unique_models = list(set(models))
        print(f"\n{desc}:")
        for model in unique_models:
            count = models.count(model)
            print(f"  - {model} ({count} instances)")
    
    print(f"\n=== Unspecified SFPs ({len(unspecified_sfps)} total) ===")
    # Group by description
    by_desc = {}
    for sfp in unspecified_sfps:
        desc = sfp['description']
        if desc not in by_desc:
            by_desc[desc] = []
        by_desc[desc].append(sfp)
    
    for desc, sfps in sorted(by_desc.items()):
        print(f"\n{desc}: {len(sfps)} instances")
        for sfp in sfps[:3]:  # Show first 3
            print(f"  - {sfp['device']} - {sfp['name']} (Serial: {sfp['serial']})")
        if len(sfps) > 3:
            print(f"  ... and {len(sfps) - 3} more")

if __name__ == "__main__":
    analyze_unspecified_sfps()