#!/usr/bin/env python3
"""
Export Policy Objects Details
============================

This script exports the details of found policy objects in a format suitable for firewall rules.
"""

import json
import os
from datetime import datetime

def export_policy_objects():
    """Export policy objects details"""
    
    # Read the found objects
    with open('found_policy_objects.json', 'r') as f:
        found_objects = json.load(f)
    
    print("Policy Objects Found in DTC-Store-Inventory-All (436883):")
    print("=" * 60)
    
    objects = []
    groups = []
    
    for obj_id, info in found_objects.items():
        if info['type'] == 'object':
            objects.append(info)
        else:
            groups.append(info)
    
    print(f"\nNetwork Objects ({len(objects)}):")
    print("-" * 30)
    for obj in objects:
        data = obj['data']
        print(f"ID: {data['id']}")
        print(f"Name: {data['name']}")
        print(f"Type: {data['type']}")
        if data['type'] == 'cidr':
            print(f"CIDR: {data['cidr']}")
        elif data['type'] == 'fqdn':
            print(f"FQDN: {data['fqdn']}")
        elif data['type'] == 'ipAndMask':
            print(f"IP: {data['ip']}, Mask: {data['mask']}")
        print(f"Created: {data['createdAt']}")
        print(f"Updated: {data['updatedAt']}")
        print()
    
    print(f"Network Object Groups ({len(groups)}):")
    print("-" * 30)
    for group in groups:
        data = group['data']
        print(f"ID: {data['id']}")
        print(f"Name: {data['name']}")
        print(f"Category: {data['category']}")
        print(f"Object IDs: {data['objectIds']}")
        print(f"Network IDs: {len(data['networkIds'])} networks")
        print(f"Created: {data['createdAt']}")
        print(f"Updated: {data['updatedAt']}")
        print()
    
    # Create a summary for firewall rules
    print("Firewall Rule References:")
    print("=" * 30)
    print("Use these references in your firewall rules:")
    print()
    
    for obj_id, info in found_objects.items():
        if info['type'] == 'object':
            print(f"OBJ({obj_id}) - {info['data']['name']}")
        else:
            print(f"GRP({obj_id}) - {info['data']['name']}")
    
    # Export to a clean format
    clean_export = {
        'export_time': datetime.now().isoformat(),
        'organization': 'DTC-Store-Inventory-All (436883)',
        'objects': {},
        'groups': {}
    }
    
    for obj_id, info in found_objects.items():
        if info['type'] == 'object':
            clean_export['objects'][obj_id] = {
                'name': info['data']['name'],
                'type': info['data']['type'],
                'value': info['data'].get('cidr') or info['data'].get('fqdn') or f"{info['data'].get('ip', '')}/{info['data'].get('mask', '')}"
            }
        else:
            clean_export['groups'][obj_id] = {
                'name': info['data']['name'],
                'category': info['data']['category'],
                'objectIds': info['data']['objectIds']
            }
    
    with open('policy_objects_export.json', 'w') as f:
        json.dump(clean_export, f, indent=2)
    
    print(f"\nExported clean data to policy_objects_export.json")

if __name__ == "__main__":
    export_policy_objects()