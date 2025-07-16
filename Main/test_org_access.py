#!/usr/bin/env python3
"""
Test script to check available organizations
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')

headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

print(f"API Key: {API_KEY[:6]}...")

# Get organizations
print("\nFetching organizations...")
url = "https://api.meraki.com/api/v1/organizations"
response = requests.get(url, headers=headers)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    orgs = response.json()
    print(f"Found {len(orgs)} organizations:")
    for org in orgs:
        print(f"  - {org['name']} (ID: {org['id']})")
else:
    print(f"Error: {response.text}")