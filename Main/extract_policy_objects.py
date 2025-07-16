#!/usr/bin/env python3
"""
Extract and Migrate Meraki Policy Objects
=========================================

This script extracts policy objects (network objects and groups) from a production
Meraki organization and creates them in a development organization.

Usage:
    python3 extract_policy_objects.py

Author: System
Date: July 2025
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
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
PROD_ORG_ID = "3790904986339115010"  # DTC-Network-Engineering (contains the policy objects)
DEV_ORG_ID = "436883"  # DTC-Store-Inventory-All (target for migration)

# Policy objects to extract
REQUIRED_GROUPS = [
    "GRP(3790904986339115043)",
    "GRP(3790904986339115076)", 
    "GRP(3790904986339115077)"
]

REQUIRED_OBJECTS = [
    "OBJ(3790904986339115074)",
    "OBJ(3790904986339115064)",
    "OBJ(3790904986339115065)",
    "OBJ(3790904986339115066)",
    "OBJ(3790904986339115067)"
]

class PolicyObjectMigrator:
    def __init__(self):
        self.start_time = datetime.now()
        self.object_mapping = {}  # Maps old IDs to new IDs
        self.group_mapping = {}   # Maps old group IDs to new IDs
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
        
    def make_api_request(self, url, method='GET', data=None):
        """Make API request with rate limiting and error handling"""
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=HEADERS)
                
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                self.log(f"Rate limited. Waiting {retry_after} seconds...", "WARNING")
                time.sleep(retry_after)
                return self.make_api_request(url, method, data)
                
            response.raise_for_status()
            
            # Return JSON if available
            if response.text:
                return response.json()
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"API request failed: {e}", "ERROR")
            if hasattr(e, 'response') and e.response is not None:
                self.log(f"Response content: {e.response.text}", "ERROR")
            return None
            
    def get_policy_objects(self, org_id):
        """Get all policy objects from an organization"""
        self.log(f"Fetching policy objects from org {org_id}...")
        url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
        result = self.make_api_request(url)
        
        if result:
            self.log(f"Found {len(result)} policy objects")
            return result
        return []
        
    def get_policy_groups(self, org_id):
        """Get all policy object groups from an organization"""
        self.log(f"Fetching policy object groups from org {org_id}...")
        url = f"{BASE_URL}/organizations/{org_id}/policyObjects/groups"
        result = self.make_api_request(url)
        
        if result:
            self.log(f"Found {len(result)} policy object groups")
            return result
        return []
        
    def create_policy_object(self, org_id, object_data):
        """Create a policy object in the target organization"""
        url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
        
        # Clean up the object data
        create_data = {
            'name': object_data['name'],
            'category': object_data['category'],
            'type': object_data['type']
        }
        
        # Add type-specific fields
        if object_data['type'] == 'cidr':
            create_data['cidr'] = object_data['cidr']
        elif object_data['type'] == 'fqdn':
            create_data['fqdn'] = object_data['fqdn']
        elif object_data['type'] == 'ipAndMask':
            create_data['ip'] = object_data['ip']
            create_data['mask'] = object_data['mask']
            
        self.log(f"Creating policy object: {object_data['name']} ({object_data['type']})")
        result = self.make_api_request(url, method='POST', data=create_data)
        
        if result:
            self.log(f"  ✓ Created object with ID: {result['id']}")
            return result
        else:
            self.log(f"  ✗ Failed to create object", "ERROR")
            return None
            
    def create_policy_group(self, org_id, group_data, object_mapping):
        """Create a policy object group in the target organization"""
        url = f"{BASE_URL}/organizations/{org_id}/policyObjects/groups"
        
        # Translate object IDs in the group
        new_object_ids = []
        for obj_id in group_data.get('objectIds', []):
            if obj_id in object_mapping:
                new_object_ids.append(object_mapping[obj_id])
            else:
                self.log(f"  Warning: Object ID {obj_id} not found in mapping", "WARNING")
                
        create_data = {
            'name': group_data['name'],
            'category': group_data['category'],
            'objectIds': new_object_ids
        }
        
        self.log(f"Creating policy group: {group_data['name']}")
        self.log(f"  Original objects: {group_data.get('objectIds', [])}")
        self.log(f"  Mapped objects: {new_object_ids}")
        
        result = self.make_api_request(url, method='POST', data=create_data)
        
        if result:
            self.log(f"  ✓ Created group with ID: {result['id']}")
            return result
        else:
            self.log(f"  ✗ Failed to create group", "ERROR")
            return None
            
    def extract_required_objects(self, objects, required_ids):
        """Extract only the required objects from the full list"""
        extracted = []
        
        for req_id in required_ids:
            # Extract numeric ID from format like "OBJ(3790904986339115074)"
            numeric_id = req_id.split('(')[1].rstrip(')')
            
            # Find the object
            found = False
            for obj in objects:
                if str(obj['id']) == numeric_id:
                    extracted.append(obj)
                    found = True
                    self.log(f"  Found {req_id}: {obj['name']}")
                    break
                    
            if not found:
                self.log(f"  Warning: {req_id} not found", "WARNING")
                
        return extracted
        
    def migrate_policy_objects(self):
        """Main migration process"""
        self.log("Starting policy object migration...")
        self.log(f"Source org: {PROD_ORG_ID}")
        self.log(f"Target org: {DEV_ORG_ID}")
        
        # Step 1: Get all policy objects from production
        self.log("\nStep 1: Fetching production policy objects...")
        prod_objects = self.get_policy_objects(PROD_ORG_ID)
        prod_groups = self.get_policy_groups(PROD_ORG_ID)
        
        # Step 2: Extract required objects
        self.log("\nStep 2: Extracting required objects...")
        required_objects = self.extract_required_objects(prod_objects, REQUIRED_OBJECTS)
        required_groups = self.extract_required_objects(prod_groups, REQUIRED_GROUPS)
        
        # Save extracted objects for reference
        with open('extracted_policy_objects.json', 'w') as f:
            json.dump({
                'objects': required_objects,
                'groups': required_groups,
                'extraction_time': datetime.now().isoformat()
            }, f, indent=2)
        self.log(f"Saved extracted objects to extracted_policy_objects.json")
        
        # Step 3: Create objects in dev org
        self.log("\nStep 3: Creating objects in dev organization...")
        for obj in required_objects:
            new_obj = self.create_policy_object(DEV_ORG_ID, obj)
            if new_obj:
                self.object_mapping[str(obj['id'])] = str(new_obj['id'])
                
        # Step 4: Create groups in dev org
        self.log("\nStep 4: Creating groups in dev organization...")
        for group in required_groups:
            new_group = self.create_policy_group(DEV_ORG_ID, group, self.object_mapping)
            if new_group:
                self.group_mapping[str(group['id'])] = str(new_group['id'])
                
        # Step 5: Save mapping for firewall rules
        self.log("\nStep 5: Saving ID mappings...")
        mapping_data = {
            'object_mapping': self.object_mapping,
            'group_mapping': self.group_mapping,
            'migration_time': datetime.now().isoformat()
        }
        
        with open('policy_object_mapping.json', 'w') as f:
            json.dump(mapping_data, f, indent=2)
            
        self.log(f"Saved ID mappings to policy_object_mapping.json")
        
        # Summary
        self.log("\n" + "="*50)
        self.log("Migration Summary:")
        self.log(f"  Objects created: {len(self.object_mapping)}/{len(required_objects)}")
        self.log(f"  Groups created: {len(self.group_mapping)}/{len(required_groups)}")
        self.log(f"  Duration: {datetime.now() - self.start_time}")
        
        return mapping_data

def main():
    """Main entry point"""
    migrator = PolicyObjectMigrator()
    
    try:
        mapping = migrator.migrate_policy_objects()
        
        # Display mapping for use in firewall rules
        print("\n" + "="*50)
        print("Use these mappings to update firewall rules:")
        print("\nObject mappings:")
        for old_id, new_id in mapping['object_mapping'].items():
            print(f"  OBJ({old_id}) -> OBJ({new_id})")
            
        print("\nGroup mappings:")
        for old_id, new_id in mapping['group_mapping'].items():
            print(f"  GRP({old_id}) -> GRP({new_id})")
            
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()