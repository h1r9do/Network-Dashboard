#!/usr/bin/env python3
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
api_key = os.getenv('MERAKI_API_KEY')

headers = {
    'X-Cisco-Meraki-API-Key': api_key,
    'Content-Type': 'application/json'
}

# Test updating tags for one device with the correct format
device_serial = 'Q2QN-LB6S-CYET'
url = f'https://api.meraki.com/api/v1/devices/{device_serial}'

# Try different tag formats
test_formats = [
    {'tags': 'Regional-Office'},  # Single string
    {'tags': ['Regional-Office']},  # List
    {'tags': 'RegionalOffice'},  # No hyphen
    {'tags': 'Regional Office'},  # Space instead of hyphen
]

for i, data in enumerate(test_formats):
    print(f'Test {i+1}: {data}')
    try:
        response = requests.put(url, headers=headers, json=data, timeout=30)
        print(f'Status: {response.status_code}')
        if response.status_code != 200:
            print(f'Error: {response.text}')
        else:
            print('Success!')
            # Check what was actually set
            get_response = requests.get(url, headers=headers)
            if get_response.status_code == 200:
                device_data = get_response.json()
                print(f'Tags now: {device_data.get("tags", [])}')
            break
    except Exception as e:
        print(f'Exception: {e}')
    print('')