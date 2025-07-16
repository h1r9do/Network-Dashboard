#!/usr/bin/env python3
"""
Test script to verify private IP resolution for ALB 03
"""
import requests
import json
import socket
import sys
import os

# API Configuration
API_KEY = os.getenv('MERAKI_API_KEY', '5174c907a7d57dea6a0788617287c985cc80b3c1')
ORG_ID = '436883'

def is_private_ip(ip):
    """Check if IP is private"""
    if not ip:
        return False
    try:
        addr = socket.inet_aton(ip)
        # 10.0.0.0/8
        if addr[0] == 10:
            return True
        # 172.16.0.0/12
        if addr[0] == 172 and 16 <= addr[1] <= 31:
            return True
        # 192.168.0.0/16
        if addr[0] == 192 and addr[1] == 168:
            return True
        return False
    except:
        return False

def get_device_public_ip(serial, interface, api_key):
    """Get public IP for specific device interface"""
    url = f"https://api.meraki.com/api/v1/devices/{serial}/appliance/uplink"
    headers = {
        'X-Cisco-Meraki-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for uplink in data:
                if uplink.get('interface') == interface:
                    return uplink.get('publicIp')
    except Exception as e:
        print(f"Error getting public IP: {e}")
    return None

def get_arin_info(ip):
    """Get ISP info from ARIN RDAP"""
    if not ip or is_private_ip(ip):
        return "Private IP"
    
    try:
        url = f"https://rdap.arin.net/registry/ip/{ip}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Extract organization name
            entities = data.get('entities', [])
            for entity in entities:
                if 'roles' in entity and 'registrant' in entity['roles']:
                    handle = entity.get('handle', '')
                    if handle:
                        return handle
            return "Unknown Provider"
    except Exception as e:
        print(f"ARIN lookup error for {ip}: {e}")
    return "ARIN Error"

def test_alb03():
    """Test IP resolution for ALB 03"""
    print("=== Testing ALB 03 IP Resolution ===\n")
    
    # ALB 03 device serial
    device_serial = "Q2KY-FBAF-VTHH"
    
    # Get batch uplink data (what the main script gets)
    print("1. Getting batch uplink data...")
    url = f"https://api.meraki.com/api/v1/organizations/{ORG_ID}/appliance/uplink/statuses"
    headers = {
        'X-Cisco-Meraki-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            device_data = None
            for device in data:
                if device.get('serial') == device_serial:
                    device_data = device
                    break
            
            if device_data:
                wan1_ip = device_data.get('uplinks', [{}])[0].get('ip', '') if len(device_data.get('uplinks', [])) > 0 else ''
                wan2_ip = device_data.get('uplinks', [{}])[1].get('ip', '') if len(device_data.get('uplinks', [])) > 1 else ''
                
                print(f"   WAN1 IP from batch: {wan1_ip}")
                print(f"   WAN2 IP from batch: {wan2_ip}")
                
                # Test private IP detection and resolution
                print("\n2. Testing private IP detection...")
                if wan1_ip and is_private_ip(wan1_ip):
                    print(f"   WAN1 {wan1_ip} is PRIVATE - getting public IP...")
                    wan1_public = get_device_public_ip(device_serial, 'wan1', API_KEY)
                    print(f"   WAN1 public IP: {wan1_public}")
                    final_wan1 = wan1_public if wan1_public else wan1_ip
                else:
                    final_wan1 = wan1_ip
                    print(f"   WAN1 {wan1_ip} is public")
                
                if wan2_ip and is_private_ip(wan2_ip):
                    print(f"   WAN2 {wan2_ip} is PRIVATE - getting public IP...")
                    wan2_public = get_device_public_ip(device_serial, 'wan2', API_KEY)
                    print(f"   WAN2 public IP: {wan2_public}")
                    final_wan2 = wan2_public if wan2_public else wan2_ip
                else:
                    final_wan2 = wan2_ip
                    print(f"   WAN2 {wan2_ip} is public")
                
                # Test ARIN lookups
                print("\n3. Testing ARIN provider lookups...")
                if final_wan1:
                    wan1_provider = get_arin_info(final_wan1)
                    print(f"   WAN1 {final_wan1} → {wan1_provider}")
                
                if final_wan2:
                    wan2_provider = get_arin_info(final_wan2)
                    print(f"   WAN2 {final_wan2} → {wan2_provider}")
                
                # Summary
                print("\n=== FINAL RESULTS ===")
                print(f"Original WAN1: {wan1_ip} → Final WAN1: {final_wan1}")
                print(f"Original WAN2: {wan2_ip} → Final WAN2: {final_wan2}")
                print(f"WAN1 Provider: {wan1_provider if final_wan1 else 'None'}")
                print(f"WAN2 Provider: {wan2_provider if final_wan2 else 'None'}")
                
                # Test success
                if wan2_ip == "192.168.0.151" and final_wan2 != "192.168.0.151":
                    print("\n✅ SUCCESS: Private IP was resolved to public IP!")
                    return True
                else:
                    print("\n❌ ISSUE: Private IP resolution didn't work as expected")
                    return False
            else:
                print(f"Device {device_serial} not found in batch data")
                return False
        else:
            print(f"API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_alb03()