#!/usr/bin/env python3
"""Test script to populate a few IP addresses in meraki_inventory"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nightly_meraki_db import (
    get_organization_id, get_organization_uplink_statuses, 
    get_all_networks, get_devices, get_device_details,
    parse_raw_notes, get_provider_for_ip, compare_providers,
    store_device_in_db, get_db_connection
)
import ipaddress
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test with just NYB stores
def test_nyb_stores():
    """Test populating IPs for NYB stores only"""
    
    try:
        org_id = get_organization_id()
        logger.info(f"Using Organization ID: {org_id}")
        
        # Get uplink statuses
        logger.info("Fetching uplink statuses...")
        uplink_statuses = get_organization_uplink_statuses(org_id)
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
        
        # Get networks
        networks = get_all_networks(org_id)
        logger.info(f"Found {len(networks)} networks")
        
        # Filter for NYB networks only
        nyb_networks = [net for net in networks if net.get('name', '').startswith('NYB')]
        logger.info(f"Found {len(nyb_networks)} NYB networks")
        
        # Get database connection
        conn = get_db_connection()
        ip_cache = {}
        missing_ips = set()
        
        devices_processed = 0
        
        for net in nyb_networks:
            net_name = (net.get('name') or "").strip()
            net_id = net.get('id')
            logger.info(f"\nProcessing network: {net_name}")
            
            devices = get_devices(net_id)
            
            for device in devices:
                model = device.get('model', '')
                if model.startswith("MX"):
                    serial = device.get('serial')
                    device_details = get_device_details(serial)
                    tags = device_details.get('tags', []) if device_details else []
                    
                    wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
                    wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
                    wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
                    wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')
                    
                    logger.info(f"Device {serial}:")
                    logger.info(f"  WAN1 IP: {wan1_ip}")
                    logger.info(f"  WAN2 IP: {wan2_ip}")
                    
                    raw_notes = device.get('notes', '') or ''
                    wan1_label, wan1_speed, wan2_label, wan2_speed = parse_raw_notes(raw_notes)
                    
                    # Get ARIN providers
                    wan1_provider = None
                    wan2_provider = None
                    
                    if wan1_ip:
                        wan1_provider = get_provider_for_ip(wan1_ip, ip_cache, missing_ips)
                        logger.info(f"  WAN1 ARIN Provider: {wan1_provider}")
                    
                    if wan2_ip:
                        wan2_provider = get_provider_for_ip(wan2_ip, ip_cache, missing_ips)
                        logger.info(f"  WAN2 ARIN Provider: {wan2_provider}")
                    
                    device_entry = {
                        "network_id": net_id,
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
                            "provider_comparison": None
                        },
                        "wan2": {
                            "provider_label": wan2_label,
                            "speed": wan2_speed,
                            "ip": wan2_ip,
                            "assignment": wan2_assign,
                            "provider": wan2_provider,
                            "provider_comparison": None
                        },
                        "raw_notes": raw_notes
                    }
                    
                    # Store in database
                    if store_device_in_db(device_entry, conn):
                        devices_processed += 1
                        logger.info(f"  ✓ Stored in database")
                    else:
                        logger.error(f"  ✗ Failed to store in database")
                    
                    time.sleep(0.5)  # Rate limit
        
        conn.close()
        logger.info(f"\nCompleted. Processed {devices_processed} devices")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nyb_stores()