#!/usr/bin/env python3
"""
Migrate Policy Objects to DTC-Network-Engineering Organization
==============================================================

This script migrates the necessary policy objects from DTC-Store-Inventory-All (436883)
to DTC-Network-Engineering (3790904986339115010) so that firewall rules can reference them.

"""

import os
import sys
import json
import requests
import time
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Organization IDs
SOURCE_ORG_ID = "436883"  # DTC-Store-Inventory-All
TARGET_ORG_ID = "3790904986339115010"  # DTC-Network-Engineering

def make_api_request(url, method='GET', data=None):
    """Make API request with error handling"""
    time.sleep(0.5)  # Rate limiting
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
            
        response.raise_for_status()
        
        if response.text:
            return response.json()
        return {}
        
    except Exception as e:
        print(f"Error {method} {url}: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def get_policy_objects(org_id):
    """Get all policy objects from organization"""
    print(f"Getting policy objects from org {org_id}...")
    url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
    return make_api_request(url) or []

def get_policy_groups(org_id):
    """Get all policy groups from organization"""
    print(f"Getting policy groups from org {org_id}...")
    url = f"{BASE_URL}/organizations/{org_id}/policyObjects/groups"
    return make_api_request(url) or []

def create_policy_object(org_id, obj_data):
    """Create a policy object in the target organization"""
    url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
    return make_api_request(url, method='POST', data=obj_data)

def create_policy_group(org_id, group_data):
    """Create a policy group in the target organization"""
    url = f"{BASE_URL}/organizations/{org_id}/policyObjects/groups"
    return make_api_request(url, method='POST', data=group_data)

def main():
    """Main migration function"""
    print("Migrating Policy Objects for Firewall Rules")
    print("=" * 50)
    
    # Target objects and groups needed for firewall rules
    target_object_ids = [
        '3790904986339115064',  # Google_AndroidClients
        '3790904986339115065',  # Google_ClientServices  
        '3790904986339115066',  # Google_FireBaseRemoteConfig
        '3790904986339115067',  # Google_MTalk
        '3790904986339115074',  # Windows NTP Server IP
    ]
    
    target_group_ids = [
        '3790904986339115043',  # Outbound EPX
        '3790904986339115076',  # MS Teams Media IPs
        '3790904986339115077',  # Netrix nVX PBX IPs
    ]
    
    # Get source objects
    source_objects = get_policy_objects(SOURCE_ORG_ID)
    source_groups = get_policy_groups(SOURCE_ORG_ID)
    
    # Get target org existing objects to avoid duplicates
    target_objects = get_policy_objects(TARGET_ORG_ID)
    target_groups = get_policy_groups(TARGET_ORG_ID)
    
    existing_object_names = {obj['name'] for obj in target_objects}
    existing_group_names = {grp['name'] for grp in target_groups}
    
    print(f"\nSource org has {len(source_objects)} objects and {len(source_groups)} groups")
    print(f"Target org has {len(target_objects)} objects and {len(target_groups)} groups")
    
    # Track object ID mappings for groups
    object_id_mapping = {}
    
    # Step 1: Create individual policy objects
    print("\nStep 1: Creating policy objects...")
    for source_obj in source_objects:
        if str(source_obj['id']) in target_object_ids:
            # Check if already exists by name
            if source_obj['name'] in existing_object_names:
                print(f"  ⚠️  Object '{source_obj['name']}' already exists, skipping")
                # Find the existing object ID for mapping
                existing_obj = next((obj for obj in target_objects if obj['name'] == source_obj['name']), None)
                if existing_obj:
                    object_id_mapping[str(source_obj['id'])] = str(existing_obj['id'])
                continue
                
            # Create new object
            obj_data = {
                'name': source_obj['name'],
                'category': source_obj['category'],
                'type': source_obj['type'],
                'cidr': source_obj.get('cidr'),
                'fqdn': source_obj.get('fqdn'),
                'mask': source_obj.get('mask'),
                'ip': source_obj.get('ip')
            }
            
            # Remove None values
            obj_data = {k: v for k, v in obj_data.items() if v is not None}
            
            print(f"  Creating object: {source_obj['name']} ({source_obj['type']})")
            result = create_policy_object(TARGET_ORG_ID, obj_data)
            
            if result:
                new_id = str(result['id'])
                object_id_mapping[str(source_obj['id'])] = new_id
                print(f"    ✓ Created with ID: {new_id}")
            else:
                print(f"    ✗ Failed to create object")
    
    # We also need to get all dependent objects for groups
    print("\nGetting dependent objects for groups...")
    all_dependent_ids = set()
    
    # Collect all object IDs referenced by our target groups
    for source_group in source_groups:
        if str(source_group['id']) in target_group_ids:
            group_objects = source_group.get('objectIds', [])
            all_dependent_ids.update(str(obj_id) for obj_id in group_objects)
    
    print(f"  Found {len(all_dependent_ids)} dependent objects needed for groups")
    
    # Create dependent objects
    for source_obj in source_objects:
        if str(source_obj['id']) in all_dependent_ids:
            # Check if already exists or was already created
            if source_obj['name'] in existing_object_names or str(source_obj['id']) in object_id_mapping:
                if str(source_obj['id']) not in object_id_mapping:
                    # Find existing object ID
                    existing_obj = next((obj for obj in target_objects if obj['name'] == source_obj['name']), None)
                    if existing_obj:
                        object_id_mapping[str(source_obj['id'])] = str(existing_obj['id'])
                continue
                
            # Create dependent object
            obj_data = {
                'name': source_obj['name'],
                'category': source_obj['category'],
                'type': source_obj['type'],
                'cidr': source_obj.get('cidr'),
                'fqdn': source_obj.get('fqdn'),
                'mask': source_obj.get('mask'),
                'ip': source_obj.get('ip')
            }
            
            # Remove None values
            obj_data = {k: v for k, v in obj_data.items() if v is not None}
            
            print(f"  Creating dependent object: {source_obj['name']} ({source_obj['type']})")
            result = create_policy_object(TARGET_ORG_ID, obj_data)
            
            if result:
                new_id = str(result['id'])
                object_id_mapping[str(source_obj['id'])] = new_id
                print(f"    ✓ Created with ID: {new_id}")
            else:
                print(f"    ✗ Failed to create dependent object")
    
    # Step 2: Create policy groups
    print("\nStep 2: Creating policy groups...")
    group_id_mapping = {}
    
    for source_group in source_groups:
        if str(source_group['id']) in target_group_ids:
            # Check if already exists by name
            if source_group['name'] in existing_group_names:
                print(f"  ⚠️  Group '{source_group['name']}' already exists, skipping")
                existing_grp = next((grp for grp in target_groups if grp['name'] == source_group['name']), None)
                if existing_grp:
                    group_id_mapping[str(source_group['id'])] = str(existing_grp['id'])
                continue
                
            # Map object IDs to new IDs
            new_object_ids = []
            for old_obj_id in source_group.get('objectIds', []):
                new_obj_id = object_id_mapping.get(str(old_obj_id))
                if new_obj_id:
                    new_object_ids.append(new_obj_id)
                else:
                    print(f"    ⚠️  Warning: Could not map object ID {old_obj_id}")
            
            if not new_object_ids:
                print(f"  ✗ No valid object IDs for group {source_group['name']}, skipping")
                continue
                
            # Create group
            group_data = {
                'name': source_group['name'],
                'objectIds': new_object_ids
            }
            
            print(f"  Creating group: {source_group['name']} with {len(new_object_ids)} objects")
            result = create_policy_group(TARGET_ORG_ID, group_data)
            
            if result:
                new_id = str(result['id'])
                group_id_mapping[str(source_group['id'])] = new_id
                print(f"    ✓ Created with ID: {new_id}")
            else:
                print(f"    ✗ Failed to create group")
    
    # Summary
    print("\nMigration Summary:")
    print(f"  Objects created/mapped: {len(object_id_mapping)}")
    print(f"  Groups created/mapped: {len(group_id_mapping)}")
    
    # Save mapping for reference
    mapping_data = {
        'object_mappings': object_id_mapping,
        'group_mappings': group_id_mapping,
        'source_org': SOURCE_ORG_ID,
        'target_org': TARGET_ORG_ID
    }
    
    with open('policy_object_mappings.json', 'w') as f:
        json.dump(mapping_data, f, indent=2)
    
    print(f"\nMappings saved to: policy_object_mappings.json")
    print("\n✅ Policy object migration complete!")
    print("You can now apply the complete firewall rules template.")

if __name__ == "__main__":
    main()