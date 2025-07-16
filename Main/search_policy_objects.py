#!/usr/bin/env python3
"""
Search for Policy Objects Across Organizations
==============================================

This script searches for specific policy objects across all available organizations.
"""

import os
import sys
import json
import requests
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

# Target IDs to search for
TARGET_IDS = [
    "3790904986339115043",  # Group
    "3790904986339115076",  # Group
    "3790904986339115077",  # Group
    "3790904986339115074",  # Object
    "3790904986339115064",  # Object
    "3790904986339115065",  # Object
    "3790904986339115066",  # Object
    "3790904986339115067",  # Object
]

def make_api_request(url):
    """Make API request with error handling"""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def search_policy_objects():
    """Search for policy objects across all organizations"""
    print("Searching for policy objects across all organizations...")
    
    # Get all organizations
    orgs = make_api_request(f"{BASE_URL}/organizations")
    if not orgs:
        print("Failed to get organizations")
        return
    
    found_objects = {}
    
    for org in orgs:
        org_id = org['id']
        org_name = org['name']
        print(f"\nSearching in {org_name} ({org_id})...")
        
        # Search policy objects
        objects = make_api_request(f"{BASE_URL}/organizations/{org_id}/policyObjects")
        if objects:
            print(f"  Found {len(objects)} policy objects")
            for obj in objects:
                if str(obj['id']) in TARGET_IDS:
                    found_objects[obj['id']] = {
                        'type': 'object',
                        'org_id': org_id,
                        'org_name': org_name,
                        'data': obj
                    }
                    print(f"    ✓ FOUND OBJECT: {obj['id']} - {obj['name']}")
        
        # Search policy groups
        groups = make_api_request(f"{BASE_URL}/organizations/{org_id}/policyObjects/groups")
        if groups:
            print(f"  Found {len(groups)} policy object groups")
            for group in groups:
                if str(group['id']) in TARGET_IDS:
                    found_objects[group['id']] = {
                        'type': 'group',
                        'org_id': org_id,
                        'org_name': org_name,
                        'data': group
                    }
                    print(f"    ✓ FOUND GROUP: {group['id']} - {group['name']}")
    
    print(f"\n{'='*60}")
    print("SEARCH RESULTS:")
    print(f"{'='*60}")
    
    if found_objects:
        print(f"Found {len(found_objects)} out of {len(TARGET_IDS)} target objects:")
        for obj_id, info in found_objects.items():
            print(f"  {obj_id}: {info['data']['name']} ({info['type']}) in {info['org_name']}")
            
        # Save results
        with open('found_policy_objects.json', 'w') as f:
            json.dump(found_objects, f, indent=2)
        print(f"\nSaved results to found_policy_objects.json")
    else:
        print("No target objects found in any organization")
        
    print(f"\nMissing objects:")
    for target_id in TARGET_IDS:
        if target_id not in found_objects:
            print(f"  {target_id} - NOT FOUND")

if __name__ == "__main__":
    search_policy_objects()