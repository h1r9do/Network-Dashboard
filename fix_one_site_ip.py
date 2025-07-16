#!/usr/bin/env python3
"""Quick fix to populate IP for one site"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nightly_meraki_db import (
    get_organization_id, get_organization_uplink_statuses,
    get_all_networks, get_devices, get_device_details,
    parse_raw_notes, get_provider_for_ip, compare_providers,
    store_device_in_db, get_db_connection
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_nyb01():
    """Fix NYB 01 IP data"""
    
    try:
        org_id = get_organization_id()
        
        # Get uplink statuses
        logger.info("Fetching uplink statuses...")
        uplink_statuses = get_organization_uplink_statuses(org_id)
        
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
        
        # Find NYB 01
        nyb01_net = None
        for net in networks:
            if net.get('name', '').strip() == 'NYB 01':
                nyb01_net = net
                break
        
        if not nyb01_net:
            logger.error("NYB 01 not found")
            return
        
        logger.info(f"Found NYB 01: {nyb01_net['id']}")
        
        # Get devices
        devices = get_devices(nyb01_net['id'])
        
        conn = get_db_connection()
        ip_cache = {}
        missing_ips = set()
        
        for device in devices:
            model = device.get('model', '')
            if model.startswith("MX"):
                serial = device.get('serial')
                logger.info(f"Processing MX device: {serial}")
                
                device_details = get_device_details(serial)
                tags = device_details.get('tags', []) if device_details else []
                
                wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
                wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
                wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
                wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')
                
                logger.info(f"WAN1 IP: {wan1_ip}, WAN2 IP: {wan2_ip}")
                
                raw_notes = device.get('notes', '') or ''
                wan1_label, wan1_speed, wan2_label, wan2_speed = parse_raw_notes(raw_notes)
                
                # Get ARIN providers
                wan1_provider = None
                wan2_provider = None
                
                if wan1_ip:
                    wan1_provider = get_provider_for_ip(wan1_ip, ip_cache, missing_ips)
                    logger.info(f"WAN1 ARIN: {wan1_provider}")
                
                if wan2_ip:
                    wan2_provider = get_provider_for_ip(wan2_ip, ip_cache, missing_ips)
                    logger.info(f"WAN2 ARIN: {wan2_provider}")
                
                device_entry = {
                    "network_id": nyb01_net['id'],
                    "network_name": nyb01_net['name'],
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
                    logger.info("Successfully stored device")
                    
                    # Verify
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
                        FROM meraki_inventory
                        WHERE device_serial = %s
                    """, (serial,))
                    result = cursor.fetchone()
                    if result:
                        logger.info(f"Verified in DB: WAN1 IP={result[0]}, WAN2 IP={result[1]}")
                        logger.info(f"                WAN1 ARIN={result[2]}, WAN2 ARIN={result[3]}")
                    cursor.close()
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_nyb01()