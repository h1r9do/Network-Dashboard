#!/usr/bin/env python3
"""
Check management interface data for device
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')

headers = {
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
    'Content-Type': 'application/json'
}

# Test device
device_serial = 'Q2KY-FBAF-VTHH'

url = f"https://api.meraki.com/api/v1/devices/{device_serial}/managementInterface"

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    print("Management Interface Data:")
    print(json.dumps(data, indent=2))