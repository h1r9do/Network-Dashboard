#!/usr/bin/env python3
"""Debug script to trace why IPs aren't being stored in meraki_inventory"""

import os
import sys
import json
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nightly_meraki_db import (
    get_organization_id, get_organization_uplink_statuses,
    get_all_networks, get_devices, get_device_details,
    store_device_in_db, get_db_connection
)

# Enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_ip_storage():
    """Debug why IPs aren't being stored"""
    
    try:
        org_id = get_organization_id()
        logger.info(f"Organization ID: {org_id}")
        
        # Get uplink statuses
        logger.info("Fetching uplink statuses...")
        uplink_statuses = get_organization_uplink_statuses(org_id)
        logger.info(f"Retrieved {len(uplink_statuses)} uplink statuses")
        
        # Debug: Show a sample uplink status
        if uplink_statuses:
            logger.info("Sample uplink status:")
            sample = uplink_statuses[0]
            logger.info(f"  Serial: {sample.get('serial')}")
            logger.info(f"  Network ID: {sample.get('networkId')}")
            logger.info(f"  Uplinks: {json.dumps(sample.get('uplinks', []), indent=2)}")
        
        # Build uplink dictionary
        uplink_dict = {}
        ip_count = 0
        
        for status in uplink_statuses:
            serial = status.get('serial')
            uplinks = status.get('uplinks', [])
            uplink_dict[serial] = {}
            
            for uplink in uplinks:
                interface = uplink.get('interface', '').lower()
                ip = uplink.get('ip', '')
                
                if interface in ['wan1', 'wan2'] and ip:
                    ip_count += 1
                    uplink_dict[serial][interface] = {
                        'ip': ip,
                        'assignment': uplink.get('ipAssignedBy', '')
                    }
                    logger.debug(f"Found IP for {serial} {interface}: {ip}")
        
        logger.info(f"Total IPs found in uplink data: {ip_count}")
        
        # Get networks and find a test network
        networks = get_all_networks(org_id)
        test_network = None
        
        for net in networks:
            if net.get('name', '').startswith('NYB 01'):
                test_network = net
                break
        
        if not test_network:
            logger.error("No NYB 01 network found for testing")
            return
        
        logger.info(f"Testing with network: {test_network['name']}")
        
        # Get devices in test network
        devices = get_devices(test_network['id'])
        mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
        
        logger.info(f"Found {len(mx_devices)} MX devices in network")
        
        if not mx_devices:
            logger.error("No MX devices found")
            return
        
        # Test with first MX device
        test_device = mx_devices[0]
        serial = test_device['serial']
        
        logger.info(f"\nTesting device {serial}:")
        logger.info(f"  Model: {test_device.get('model')}")
        logger.info(f"  Name: {test_device.get('name')}")
        
        # Check if this device has uplink data
        if serial in uplink_dict:
            logger.info(f"  Uplink data found:")
            for interface, data in uplink_dict[serial].items():
                logger.info(f"    {interface}: IP={data['ip']}, Assignment={data['assignment']}")
        else:
            logger.warning(f"  No uplink data found for serial {serial}")
        
        # Get device details
        device_details = get_device_details(serial)
        
        # Build device entry exactly as nightly_meraki_db.py does
        wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
        wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
        wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
        wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')
        
        logger.info(f"\nData to be stored:")
        logger.info(f"  WAN1 IP: '{wan1_ip}' (length: {len(wan1_ip)})")
        logger.info(f"  WAN1 Assignment: '{wan1_assign}'")
        logger.info(f"  WAN2 IP: '{wan2_ip}' (length: {len(wan2_ip)})")
        logger.info(f"  WAN2 Assignment: '{wan2_assign}'")
        
        device_entry = {
            "network_id": test_network['id'],
            "network_name": test_network['name'],
            "device_serial": serial,
            "device_model": test_device['model'],
            "device_name": test_device.get('name', ''),
            "device_tags": device_details.get('tags', []) if device_details else [],
            "wan1": {
                "provider_label": "",
                "speed": "",
                "ip": wan1_ip,
                "assignment": wan1_assign,
                "provider": None,
                "provider_comparison": None
            },
            "wan2": {
                "provider_label": "",
                "speed": "",
                "ip": wan2_ip,
                "assignment": wan2_assign,
                "provider": None,
                "provider_comparison": None
            },
            "raw_notes": test_device.get('notes', '') or ''
        }
        
        # Get database connection and attempt to store
        conn = get_db_connection()
        
        # First, check current data in database
        cursor = conn.cursor()
        cursor.execute("""
            SELECT wan1_ip, wan2_ip, last_updated
            FROM meraki_inventory
            WHERE device_serial = %s
        """, (serial,))
        
        existing = cursor.fetchone()
        if existing:
            logger.info(f"\nExisting database record:")
            logger.info(f"  WAN1 IP: '{existing[0]}' (NULL: {existing[0] is None})")
            logger.info(f"  WAN2 IP: '{existing[1]}' (NULL: {existing[1] is None})")
            logger.info(f"  Last Updated: {existing[2]}")
        else:
            logger.info(f"\nNo existing record for {serial}")
        
        cursor.close()
        
        # Now try to store
        logger.info("\nAttempting to store device...")
        success = store_device_in_db(device_entry, conn)
        
        if success:
            logger.info("Store operation reported success")
            
            # Verify what was actually stored
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wan1_ip, wan2_ip, wan1_assignment, wan2_assignment, last_updated
                FROM meraki_inventory
                WHERE device_serial = %s
            """, (serial,))
            
            result = cursor.fetchone()
            if result:
                logger.info(f"\nVerification - Data in database after store:")
                logger.info(f"  WAN1 IP: '{result[0]}' (NULL: {result[0] is None})")
                logger.info(f"  WAN2 IP: '{result[1]}' (NULL: {result[1] is None})")
                logger.info(f"  WAN1 Assignment: '{result[2]}'")
                logger.info(f"  WAN2 Assignment: '{result[3]}'")
                logger.info(f"  Last Updated: {result[4]}")
            
            cursor.close()
        else:
            logger.error("Store operation failed")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ip_storage()