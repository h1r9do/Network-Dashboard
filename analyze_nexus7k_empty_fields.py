#!/usr/bin/env python3
"""
Analyze Nexus 7K empty fields and missing data
"""
import json

def analyze_empty_fields():
    with open('/var/www/html/network-data/nightly_snmp_collection_20250708_154906.json', 'r') as f:
        data = json.load(f)
    
    # Find a Nexus 7K device
    nexus7k = None
    for device in data['devices']:
        if 'AL-7000-01-ADMIN' in device.get('device_name', ''):
            nexus7k = device
            break
    
    if not nexus7k:
        print("No Nexus 7K found")
        return
    
    # Analyze empty fields
    total_entities = len(nexus7k['entity_data'])
    empty_model = 0
    empty_serial = 0
    empty_both = 0
    
    # Categorize by entity type
    by_class = {}
    empty_by_class = {}
    
    for entity_id, entity in nexus7k['entity_data'].items():
        entity_class = entity.get('class', 'unknown')
        desc = entity.get('description', '')
        model = entity.get('model_name', '')
        serial = entity.get('serial_number', '')
        
        # Count by class
        if entity_class not in by_class:
            by_class[entity_class] = []
            empty_by_class[entity_class] = []
        
        by_class[entity_class].append({
            'desc': desc,
            'model': model,
            'serial': serial
        })
        
        # Check for empty fields
        if model == '""' or not model:
            empty_model += 1
            empty_by_class[entity_class].append(desc)
        if serial == '""' or not serial:
            empty_serial += 1
        if (model == '""' or not model) and (serial == '""' or not serial):
            empty_both += 1
    
    print(f"Nexus 7K Analysis for {nexus7k['device_name']}:")
    print(f"Total entities: {total_entities}")
    print(f"Empty models: {empty_model} ({empty_model/total_entities*100:.1f}%)")
    print(f"Empty serials: {empty_serial} ({empty_serial/total_entities*100:.1f}%)")
    print(f"Empty both: {empty_both} ({empty_both/total_entities*100:.1f}%)")
    
    print("\nEntity Classes:")
    class_map = {
        '3': 'Chassis',
        '5': 'Container/Slot',
        '6': 'Power Supply',
        '7': 'Fan',
        '8': 'Sensor',
        '9': 'Module',
        '10': 'Port',
        '11': 'Stack'
    }
    
    for class_id in sorted(by_class.keys()):
        class_name = class_map.get(class_id, f'Class-{class_id}')
        total = len(by_class[class_id])
        empty = len(empty_by_class[class_id])
        print(f"\n{class_name} (Class {class_id}): {total} total, {empty} empty models")
        
        # Show examples of populated vs empty
        populated = [e for e in by_class[class_id] if e['model'] and e['model'] != '""']
        if populated:
            print(f"  Examples with model data:")
            for e in populated[:3]:
                print(f"    - {e['desc']}: {e['model']} (Serial: {e['serial']})")
        
        if empty_by_class[class_id]:
            print(f"  Examples with empty models:")
            for desc in empty_by_class[class_id][:5]:
                print(f"    - {desc}")

if __name__ == "__main__":
    analyze_empty_fields()