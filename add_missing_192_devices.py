#!/usr/bin/env python3
"""
Add missing 192.168.x.x devices to SNMP collection
"""
import json
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

# Missing devices that need SNMP collection
missing_devices = [
    # 192.168.4.x - HQ devices
    {"hostname": "HQ-NET-4-01", "ip": "192.168.4.1", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-4-02", "ip": "192.168.4.2", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    
    # 192.168.5.x - HQ devices  
    {"hostname": "HQ-NET-5-01", "ip": "192.168.5.1", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-5-02", "ip": "192.168.5.2", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    
    # 192.168.12.x - HQ devices
    {"hostname": "HQ-NET-12-01", "ip": "192.168.12.1", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-12-02", "ip": "192.168.12.2", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    
    # 192.168.13.x - HQ devices
    {"hostname": "HQ-NET-13-01", "ip": "192.168.13.1", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-13-02", "ip": "192.168.13.2", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    
    # 192.168.200.x - Alameda devices
    {"hostname": "AL-NET-200-10", "ip": "192.168.200.10", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "Alameda Network Device"},
    {"hostname": "AL-NET-200-11", "ip": "192.168.200.11", "snmp_version": "3", "snmp_v3_username": "DT_Network_SNMPv3", "device_type": "Alameda Network Device"}
]

def check_and_add_devices():
    """Check if devices exist and add them to device_snmp_credentials if missing"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # First, check what SNMPv3 credentials we have for DT_Network_SNMPv3
        cursor.execute("""
            SELECT DISTINCT snmp_v3_auth_protocol, snmp_v3_priv_protocol, snmp_v3_security_level 
            FROM device_snmp_credentials 
            WHERE snmp_v3_username = 'DT_Network_SNMPv3'
            LIMIT 1
        """)
        
        v3_config = cursor.fetchone()
        if v3_config:
            auth_protocol, priv_protocol, security_level = v3_config
            print(f"Found SNMPv3 config: auth={auth_protocol}, priv={priv_protocol}, level={security_level}")
        else:
            # Use typical values if not found
            auth_protocol = 'SHA'
            priv_protocol = 'AES'
            security_level = 'authPriv'
            print("Using default SNMPv3 config")
        
        added_count = 0
        existing_count = 0
        
        for device in missing_devices:
            # Check if device already exists
            cursor.execute("""
                SELECT id FROM device_snmp_credentials
                WHERE ip_address = %s
            """, (device['ip'],))
            
            if cursor.fetchone():
                print(f"Device {device['hostname']} ({device['ip']}) already exists")
                existing_count += 1
            else:
                # Add device
                cursor.execute("""
                    INSERT INTO device_snmp_credentials 
                    (hostname, ip_address, snmp_version, snmp_v3_username, 
                     snmp_v3_auth_protocol, snmp_v3_priv_protocol, snmp_v3_security_level,
                     snmp_port, snmp_timeout, snmp_retries, working)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 161, 10, 3, false)
                """, (
                    device['hostname'],
                    device['ip'],
                    device['snmp_version'],
                    device['snmp_v3_username'],
                    auth_protocol,
                    priv_protocol,
                    security_level
                ))
                print(f"Added {device['hostname']} ({device['ip']}) to SNMP targets")
                added_count += 1
        
        conn.commit()
        print(f"\nSummary: Added {added_count} new devices, {existing_count} already existed")
        
        # Show current 192.168.x.x devices
        cursor.execute("""
            SELECT hostname, ip_address, snmp_version, snmp_v3_username, working
            FROM device_snmp_credentials
            WHERE ip_address::text LIKE '192.168.%'
            ORDER BY ip_address
        """)
        
        print("\nCurrent 192.168.x.x devices in SNMP collection:")
        for row in cursor.fetchall():
            hostname, ip, version, username, working = row
            status = "✓" if working else "✗"
            print(f"  {status} {hostname:<20} {ip:<16} v{version} user: {username or 'N/A'}")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def update_device_list_json():
    """Update the JSON file used by SNMP collection script"""
    json_file = "/tmp/filtered_snmp_devices_187.json"
    
    try:
        # Read existing file
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        existing_ips = {d['ip'] for d in data['devices']}
        added = 0
        
        # Add missing devices
        for device in missing_devices:
            if device['ip'] not in existing_ips:
                data['devices'].append({
                    'hostname': device['hostname'],
                    'ip': device['ip'],
                    'credential': 'DT_Network_SNMPv3',
                    'credential_type': 'v3',
                    'device_type': device['device_type'],
                    'status': 'active',
                    'source': 'manually_added_192_devices'
                })
                added += 1
        
        # Write updated file
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nUpdated {json_file} - added {added} devices")
        print(f"Total devices now: {len(data['devices'])}")
        
    except FileNotFoundError:
        print(f"\nWarning: {json_file} not found - devices should be added to nightly script directly")
    except Exception as e:
        print(f"\nError updating JSON file: {e}")

if __name__ == "__main__":
    print("Adding missing 192.168.x.x devices to SNMP collection...")
    print("=" * 60)
    
    # Add to database
    check_and_add_devices()
    
    # Try to update JSON file
    update_device_list_json()
    
    print("\nNote: The nightly_snmp_inventory_collection.py script should be updated")
    print("to include these devices in the 'additional_192_devices' section")