#!/usr/bin/env python3
"""
Fix Missing Policy Objects Script
=================================

This script identifies and migrates the missing policy objects that were 
not discovered in the original migration due to multiple objects in single rules.

Usage:
    python3 fix_missing_objects.py

Author: Claude
Date: July 2025
"""

import os
import json
import requests
import re
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

POLICY_SOURCE_ORG_ID = "436883"  # DTC-Store-Inventory-All
TARGET_ORG_ID = "3790904986339115010"  # Target organization

def make_api_request(url, method='GET', data=None):
    """Make API request with error handling"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Error: {e}")
        return None

def extract_all_object_references(firewall_rules):
    """Extract ALL object references including multiple objects in single rules"""
    object_refs = set()
    
    for rule in firewall_rules:
        src = rule.get('srcCidr', '')
        dst = rule.get('destCidr', '')
        
        # Use regex to find ALL OBJ() references in both fields
        obj_pattern = r'OBJ\((\d+)\)'
        
        # Find all objects in source
        src_objects = re.findall(obj_pattern, src)
        object_refs.update(src_objects)
        
        # Find all objects in destination  
        dst_objects = re.findall(obj_pattern, dst)
        object_refs.update(dst_objects)
    
    return list(object_refs)

def get_policy_objects(org_id):
    """Get policy objects from organization"""
    url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
    return make_api_request(url) or []

def create_policy_object(org_id, obj_data):
    """Create policy object"""
    url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
    return make_api_request(url, method='POST', data=obj_data)

def main():
    print("🔍 Discovering missing policy objects...")
    
    # Load firewall template
    with open('firewall_rules_template.json', 'r') as f:
        template = json.load(f)
    
    # Extract ALL object references properly
    all_object_refs = extract_all_object_references(template['rules'])
    print(f"📦 Found {len(all_object_refs)} total object references:")
    for obj_id in sorted(all_object_refs):
        print(f"   - {obj_id}")
    
    # Load existing mappings
    with open('migration_mappings_L_3790904986339115852_20250709_142121.json', 'r') as f:
        mappings = json.load(f)
    
    existing_objects = set(mappings['object_mappings'].keys())
    missing_objects = set(all_object_refs) - existing_objects
    
    print(f"\n🔍 Analysis:")
    print(f"   Existing mappings: {len(existing_objects)}")
    print(f"   Missing objects: {len(missing_objects)}")
    
    if missing_objects:
        print(f"\n❌ Missing object IDs:")
        for obj_id in sorted(missing_objects):
            print(f"   - {obj_id}")
        
        # Get source objects
        print(f"\n📥 Getting source objects from org {POLICY_SOURCE_ORG_ID}...")
        source_objects = get_policy_objects(POLICY_SOURCE_ORG_ID)
        
        # Get target objects
        print(f"📥 Getting target objects from org {TARGET_ORG_ID}...")
        target_objects = get_policy_objects(TARGET_ORG_ID)
        target_names = {obj['name'] for obj in target_objects}
        
        # Create missing objects
        print(f"\n🔧 Creating missing objects...")
        new_mappings = {}
        
        for source_obj in source_objects:
            if str(source_obj['id']) in missing_objects:
                print(f"\n📦 Processing: {source_obj['name']} (ID: {source_obj['id']})")
                
                # Check if already exists by name
                if source_obj['name'] in target_names:
                    existing_obj = next((obj for obj in target_objects if obj['name'] == source_obj['name']), None)
                    if existing_obj:
                        new_mappings[str(source_obj['id'])] = str(existing_obj['id'])
                        print(f"   ✓ Already exists with ID: {existing_obj['id']}")
                        continue
                
                # Create new object
                obj_data = {
                    'name': source_obj['name'],
                    'category': source_obj['category'],
                    'type': source_obj['type']
                }
                
                # Add type-specific data
                if source_obj['type'] == 'cidr':
                    obj_data['cidr'] = source_obj.get('cidr')
                elif source_obj['type'] == 'fqdn':
                    obj_data['fqdn'] = source_obj.get('fqdn')
                elif source_obj['type'] == 'ip':
                    obj_data['ip'] = source_obj.get('ip')
                
                print(f"   Creating: {obj_data}")
                result = create_policy_object(TARGET_ORG_ID, obj_data)
                
                if result:
                    new_mappings[str(source_obj['id'])] = str(result['id'])
                    print(f"   ✅ Created with ID: {result['id']}")
                else:
                    print(f"   ❌ Failed to create")
        
        # Update mappings file
        if new_mappings:
            mappings['object_mappings'].update(new_mappings)
            
            # Save updated mappings
            with open('migration_mappings_L_3790904986339115852_20250709_142121.json', 'w') as f:
                json.dump(mappings, f, indent=2)
            
            print(f"\n✅ Updated mappings file with {len(new_mappings)} new objects")
            print("📝 Updated mappings:")
            for old_id, new_id in new_mappings.items():
                print(f"   {old_id} → {new_id}")
        
        print(f"\n🔥 Now run the firewall test again:")
        print("python3 test_full_firewall_deployment.py")
    
    else:
        print("\n✅ No missing objects found!")

if __name__ == "__main__":
    main()