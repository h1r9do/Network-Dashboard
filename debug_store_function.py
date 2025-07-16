#!/usr/bin/env python3
"""Debug the store_device_in_db function directly"""

import os
import sys
import json
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nightly_meraki_db import get_db_connection

# Enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_store_device():
    """Test storing a device with IP data"""
    
    # Test data with IPs
    device_entry = {
        "network_id": "test_network_id",
        "network_name": "TEST NETWORK",
        "device_serial": "TEST-SERIAL-001",
        "device_model": "MX68",
        "device_name": "Test Device",
        "device_tags": ["test"],
        "wan1": {
            "provider_label": "AT&T",
            "speed": "100M x 100M",
            "ip": "208.105.133.178",
            "assignment": "static",
            "provider": "AT&T",
            "provider_comparison": "Match"
        },
        "wan2": {
            "provider_label": "Charter",
            "speed": "200M x 20M",
            "ip": "107.127.197.80",
            "assignment": "dhcp",
            "provider": "Charter Communications",
            "provider_comparison": "Match"
        },
        "raw_notes": "WAN1: AT&T 100M x 100M\\nWAN2: Charter 200M x 20M"
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if record exists
        cursor.execute("""
            SELECT wan1_ip, wan2_ip FROM meraki_inventory 
            WHERE device_serial = %s
        """, (device_entry["device_serial"],))
        
        existing = cursor.fetchone()
        if existing:
            logger.info(f"Existing record: WAN1={existing[0]}, WAN2={existing[1]}")
        
        # Now insert/update
        wan1_data = device_entry.get("wan1", {})
        wan2_data = device_entry.get("wan2", {})
        
        logger.info(f"WAN1 data: {wan1_data}")
        logger.info(f"WAN2 data: {wan2_data}")
        
        insert_sql = """
        INSERT INTO meraki_inventory (
            organization_name, network_id, network_name, device_serial,
            device_model, device_name, device_tags, 
            wan1_ip, wan1_assignment, wan1_arin_provider, wan1_provider_comparison,
            wan2_ip, wan2_assignment, wan2_arin_provider, wan2_provider_comparison,
            last_updated
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (device_serial) DO UPDATE SET
            organization_name = EXCLUDED.organization_name,
            network_id = EXCLUDED.network_id,
            network_name = EXCLUDED.network_name,
            device_model = EXCLUDED.device_model,
            device_name = EXCLUDED.device_name,
            device_tags = EXCLUDED.device_tags,
            wan1_ip = EXCLUDED.wan1_ip,
            wan1_assignment = EXCLUDED.wan1_assignment,
            wan1_arin_provider = EXCLUDED.wan1_arin_provider,
            wan1_provider_comparison = EXCLUDED.wan1_provider_comparison,
            wan2_ip = EXCLUDED.wan2_ip,
            wan2_assignment = EXCLUDED.wan2_assignment,
            wan2_arin_provider = EXCLUDED.wan2_arin_provider,
            wan2_provider_comparison = EXCLUDED.wan2_provider_comparison,
            last_updated = EXCLUDED.last_updated
        """
        
        values = (
            'DTC-Store-Inventory-All',
            device_entry.get("network_id", ""),
            device_entry["network_name"],
            device_entry["device_serial"],
            device_entry["device_model"],
            device_entry["device_name"],
            device_entry["device_tags"],
            wan1_data.get("ip", ""),
            wan1_data.get("assignment", ""),
            wan1_data.get("provider", ""),
            wan1_data.get("provider_comparison", ""),
            wan2_data.get("ip", ""),
            wan2_data.get("assignment", ""),
            wan2_data.get("provider", ""),
            wan2_data.get("provider_comparison", ""),
            datetime.now(timezone.utc)
        )
        
        logger.info(f"Values to insert: {values}")
        
        cursor.execute(insert_sql, values)
        
        # Verify what was stored
        cursor.execute("""
            SELECT wan1_ip, wan2_ip FROM meraki_inventory 
            WHERE device_serial = %s
        """, (device_entry["device_serial"],))
        
        result = cursor.fetchone()
        logger.info(f"After insert: WAN1={result[0]}, WAN2={result[1]}")
        
        conn.commit()
        
        # Clean up test record
        cursor.execute("DELETE FROM meraki_inventory WHERE device_serial = %s", (device_entry["device_serial"],))
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_store_device()