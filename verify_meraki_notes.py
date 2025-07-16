#!/usr/bin/env python3
"""
Verify Meraki device notes format for a few sites
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"

def get_device_info(device_serial):
    """Get device info including notes"""
    url = f"{BASE_URL}/devices/{device_serial}"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error getting device {device_serial}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception getting device {device_serial}: {e}")
        return None

def main():
    # Test sites from the script output
    test_sites = [
        ("ALB 01", "Q2QN-84BN-W54P"),
        ("ALB 03", "Q2KY-FBAF-VTHH"), 
        ("AZC 01", "Q2QN-LH2X-36KV"),
        ("AZP 09", "Q2QN-7YNV-WVL8"),
        ("ARL 01", "Q2QN-CHM5-CN6Y")
    ]
    
    print("=== Verifying Meraki Device Notes Format ===\n")
    
    for site_name, device_serial in test_sites:
        print(f"--- {site_name} ({device_serial}) ---")
        device_info = get_device_info(device_serial)
        
        if device_info:
            notes = device_info.get('notes', '')
            if notes:
                print(f"✅ Current notes:")
                for line in notes.split('\n'):
                    print(f"  {line}")
                
                # Check format
                lines = notes.split('\n')
                if len(lines) >= 3:
                    if lines[0] == "WAN 1" and lines[1] and lines[2]:
                        print("✅ Correct multi-line format detected")
                    else:
                        print("⚠️  Format may not be correct")
                else:
                    print("⚠️  Not enough lines for proper format")
            else:
                print("❌ No notes found")
        else:
            print("❌ Could not retrieve device info")
        print()

if __name__ == "__main__":
    main()