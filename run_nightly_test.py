#!/usr/bin/env python3
"""Run nightly script for just a few stores to test"""

import os
import sys
import subprocess

# Set environment to only process NYB stores
os.environ['TEST_MODE'] = 'NYB'

# Run the fixed nightly script
print("Running nightly_meraki_db.py with the network_id fix...")
print("This will only process NYB stores as a test...")

# Import and run directly
sys.path.insert(0, '/usr/local/bin/Main')
import nightly_meraki_db

# Temporarily modify the script to only process NYB networks
original_main = nightly_meraki_db.main

def test_main():
    """Modified main that only processes NYB networks"""
    import logging
    logger = logging.getLogger('nightly_meraki_db')
    
    logger.info("Starting TEST MODE - NYB networks only")
    
    # Call original main but we'll modify the network processing
    try:
        org_id = nightly_meraki_db.get_organization_id()
        logger.info(f"Using Organization ID: {org_id}")
        
        conn = nightly_meraki_db.get_db_connection()
        
        # Load IP cache
        ip_cache = {}
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address, provider_name FROM rdap_cache")
        for ip, provider in cursor.fetchall():
            ip_cache[ip] = provider
        cursor.close()
        
        missing_ips = set()
        
        # Get uplink statuses
        logger.info("Fetching uplink status for all MX devices...")
        uplink_statuses = nightly_meraki_db.get_organization_uplink_statuses(org_id)
        logger.info(f"Retrieved uplink info for {len(uplink_statuses)} devices")
        
        # Build uplink dictionary
        uplink_dict = {}
        for status in uplink_statuses:
            serial = status.get('serial')
            uplinks = status.get('uplinks', [])
            uplink_dict[serial] = {}
            for uplink in uplinks:
                interface = uplink.get('interface', '').lower()
                if interface in ['wan1', 'wan2']:
                    uplink_dict[serial][interface] = {
                        'ip': uplink.get('ip', ''),
                        'assignment': uplink.get('ipAssignedBy', '')
                    }
        
        # Get all networks
        networks = nightly_meraki_db.get_all_networks(org_id)
        
        # Filter for NYB only
        nyb_networks = [net for net in networks if net.get('name', '').startswith('NYB')]
        logger.info(f"Processing {len(nyb_networks)} NYB networks only")
        
        devices_processed = 0
        
        for net in nyb_networks:
            net_name = (net.get('name') or "").strip()
            net_id = net.get('id')
            devices = nightly_meraki_db.get_devices(net_id)
            
            for device in devices:
                model = device.get('model', '')
                if model.startswith("MX"):
                    serial = device.get('serial')
                    device_details = nightly_meraki_db.get_device_details(serial)
                    tags = device_details.get('tags', []) if device_details else []
                    
                    wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
                    wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
                    wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
                    wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')
                    
                    raw_notes = device.get('notes', '') or ''
                    wan1_label, wan1_speed, wan2_label, wan2_speed = nightly_meraki_db.parse_raw_notes(raw_notes)
                    
                    wan1_provider = None
                    wan2_provider = None
                    wan1_comparison = None
                    wan2_comparison = None
                    
                    if wan1_ip:
                        wan1_provider = nightly_meraki_db.get_provider_for_ip(wan1_ip, ip_cache, missing_ips)
                        wan1_comparison = nightly_meraki_db.compare_providers(wan1_provider, wan1_label)
                    
                    if wan2_ip:
                        wan2_provider = nightly_meraki_db.get_provider_for_ip(wan2_ip, ip_cache, missing_ips)
                        wan2_comparison = nightly_meraki_db.compare_providers(wan2_provider, wan2_label)
                    
                    device_entry = {
                        "network_id": net_id,  # THIS IS THE FIX
                        "network_name": net_name,
                        "device_serial": serial,
                        "device_model": model,
                        "device_name": device.get('name', ''),
                        "device_tags": tags,
                        "wan1": {
                            "provider_label": wan1_label,
                            "speed": wan1_speed,
                            "ip": wan1_ip,
                            "assignment": wan1_assign,
                            "provider": wan1_provider,
                            "provider_comparison": wan1_comparison
                        },
                        "wan2": {
                            "provider_label": wan2_label,
                            "speed": wan2_speed,
                            "ip": wan2_ip,
                            "assignment": wan2_assign,
                            "provider": wan2_provider,
                            "provider_comparison": wan2_comparison
                        },
                        "raw_notes": raw_notes
                    }
                    
                    if nightly_meraki_db.store_device_in_db(device_entry, conn):
                        devices_processed += 1
                        logger.info(f"Processed device {serial} in network '{net_name}' with WAN1 IP: {wan1_ip}, WAN2 IP: {wan2_ip}")
                    
                    nightly_meraki_db.time.sleep(0.2)
        
        conn.commit()
        conn.close()
        
        logger.info(f"TEST MODE Complete. Processed {devices_processed} devices")
        return True
        
    except Exception as e:
        logger.error(f"Error in test mode: {e}")
        return False

# Run test
if __name__ == "__main__":
    success = test_main()
    print(f"\nTest {'succeeded' if success else 'failed'}")
    
    # Check results
    if success:
        print("\nChecking database for results...")
        os.system("python3 check_db_ips.py")