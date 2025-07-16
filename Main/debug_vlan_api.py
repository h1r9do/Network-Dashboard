#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')

if not API_KEY:
    print("API_KEY not found in environment")
    exit(1)

headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

network_id = 'L_3790904986339115852'
vlan_url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/vlans"

print(f"API Key: {API_KEY[:6]}...")
print(f"URL: {vlan_url}")

response = requests.get(vlan_url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")