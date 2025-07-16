#!/usr/bin/env python3
"""
Test limited Meraki collection to verify IP gathering
"""

import os
import sys
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main script
from nightly_meraki_db import (
    get_organization_id, get_organization_uplink_statuses, 
    get_db_connection, logger
)

def main():
    """Test limited collection"""
    try:
        org_id = get_organization_id()
        logger.info(f"Organization ID: {org_id}")
        
        # Get uplink statuses
        logger.info("Fetching uplink statuses...")
        uplink_statuses = get_organization_uplink_statuses(org_id)
        logger.info(f"Total uplink statuses: {len(uplink_statuses)}")
        
        # Check first 20 for IPs
        count_with_ips = 0
        for i, status in enumerate(uplink_statuses[:20]):
            network_name = status.get('networkName', '')
            serial = status.get('serial', '')
            uplinks = status.get('uplinks', [])
            
            has_ip = False
            for uplink in uplinks:
                if uplink.get('ip'):
                    has_ip = True
                    interface = uplink.get('interface')
                    ip = uplink.get('ip')
                    logger.info(f"{network_name} - {serial} - {interface}: {ip}")
            
            if has_ip:
                count_with_ips += 1
        
        logger.info(f"\nDevices with IPs: {count_with_ips} out of first 20")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()