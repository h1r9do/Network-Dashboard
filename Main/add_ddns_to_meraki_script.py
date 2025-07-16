#!/usr/bin/env python3
"""
Add DDNS functionality to the Meraki nightly script
This will:
1. Add DDNS columns to the database
2. Create an updated version of the script that collects DDNS data
"""

import os
import psycopg2
from datetime import datetime

def add_ddns_columns():
    """Add DDNS columns to meraki_inventory table"""
    print("Adding DDNS columns to database...")
    
    # Database connection
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'meraki_inventory' 
            AND column_name IN ('ddns_enabled', 'ddns_url', 'wan1_public_ip', 'wan2_public_ip')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add missing columns
        columns_to_add = [
            ('ddns_enabled', 'BOOLEAN DEFAULT FALSE'),
            ('ddns_url', 'VARCHAR(255)'),
            ('wan1_public_ip', 'VARCHAR(45)'),  # For DDNS-resolved public IPs
            ('wan2_public_ip', 'VARCHAR(45)')   # For DDNS-resolved public IPs
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE meraki_inventory ADD COLUMN {column_name} {column_type}")
                print(f"  Added column: {column_name}")
            else:
                print(f"  Column already exists: {column_name}")
        
        conn.commit()
        print("Database columns added successfully!")
        
    except Exception as e:
        print(f"Error adding columns: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_updated_script():
    """Create updated version of nightly script with DDNS support"""
    print("\nCreating updated Meraki script with DDNS support...")
    
    # Read the current adaptive script (or original if adaptive doesn't exist)
    script_path = '/usr/local/bin/Main/nightly_meraki_db_adaptive.py'
    if not os.path.exists(script_path):
        script_path = '/usr/local/bin/Main/nightly/nightly_meraki_db.py'
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Add DDNS functions after the imports
    ddns_functions = '''
# DDNS Support Functions
def get_device_management_settings(serial, api_key):
    """Get device management interface settings including DDNS"""
    url = f"{BASE_URL}/devices/{serial}/managementInterface"
    try:
        settings = make_api_request(url, api_key)
        return settings if settings else {}
    except Exception as e:
        logger.debug(f"Could not get management settings for {serial}: {e}")
        return {}

def resolve_ddns_hostname(hostname, timeout=5):
    """Resolve DDNS hostname to IP address"""
    import socket
    if not hostname:
        return None
    try:
        socket.setdefaulttimeout(timeout)
        ip = socket.gethostbyname(hostname)
        logger.debug(f"DDNS resolved: {hostname} -> {ip}")
        return ip
    except Exception as e:
        logger.debug(f"DDNS resolution failed for {hostname}: {e}")
        return None
    finally:
        socket.setdefaulttimeout(None)

def construct_ddns_hostname(ddns_prefix, wan_number):
    """Construct WAN-specific DDNS hostname"""
    if not ddns_prefix:
        return None
    # Meraki DDNS format: prefix-wan#.dynamic-m.com
    if '.dynamic-m.com' in ddns_prefix:
        base = ddns_prefix.split('.dynamic-m.com')[0]
        return f"{base}-{wan_number}.dynamic-m.com"
    return f"{ddns_prefix}-{wan_number}.dynamic-m.com"

'''
    
    # Insert DDNS functions after the normalize_provider function
    insert_pos = content.find('def get_organization_id():')
    content = content[:insert_pos] + ddns_functions + '\n' + content[insert_pos:]
    
    # Update the main device processing loop
    # Find the device processing section
    device_loop_start = content.find('for device in devices:')
    device_entry_start = content.find('device_entry = {', device_loop_start)
    
    # Add DDNS collection before device_entry
    ddns_collection = '''
                    # Get DDNS settings for the device
                    mgmt_settings = get_device_management_settings(serial, MERAKI_API_KEY)
                    ddns_settings = mgmt_settings.get('ddnsHostnames', {})
                    ddns_enabled = ddns_settings.get('enabled', False)
                    ddns_prefix = ddns_settings.get('prefix', '') if ddns_enabled else ''
                    
                    # Initialize public IPs
                    wan1_public_ip = wan1_ip
                    wan2_public_ip = wan2_ip
                    
                    # If DDNS is enabled and we have private IPs, try to resolve
                    if ddns_enabled and ddns_prefix:
                        logger.info(f"DDNS enabled for {net_name}: {ddns_prefix}")
                        
                        # Check WAN1
                        if wan1_ip:
                            try:
                                ip_addr = ipaddress.ip_address(wan1_ip)
                                if ip_addr.is_private:
                                    wan1_ddns = construct_ddns_hostname(ddns_prefix, 1)
                                    resolved_ip = resolve_ddns_hostname(wan1_ddns)
                                    if resolved_ip and resolved_ip != wan1_ip:
                                        logger.info(f"{net_name} WAN1: Private IP {wan1_ip} -> Public IP {resolved_ip} via DDNS")
                                        wan1_public_ip = resolved_ip
                            except:
                                pass
                        
                        # Check WAN2
                        if wan2_ip:
                            try:
                                ip_addr = ipaddress.ip_address(wan2_ip)
                                if ip_addr.is_private:
                                    wan2_ddns = construct_ddns_hostname(ddns_prefix, 2)
                                    resolved_ip = resolve_ddns_hostname(wan2_ddns)
                                    if resolved_ip and resolved_ip != wan2_ip:
                                        logger.info(f"{net_name} WAN2: Private IP {wan2_ip} -> Public IP {resolved_ip} via DDNS")
                                        wan2_public_ip = resolved_ip
                            except:
                                pass
                    
                    # Use public IPs for ARIN lookups
                    if wan1_public_ip and wan1_public_ip != wan1_ip:
                        wan1_provider = get_provider_for_ip(wan1_public_ip, ip_cache, missing_ips)
                        wan1_provider = f"{wan1_provider} (via DDNS)"
                    elif wan1_ip:
                        wan1_provider = get_provider_for_ip(wan1_ip, ip_cache, missing_ips)
                        wan1_comparison = compare_providers(wan1_provider, wan1_label)
                    else:
                        wan1_provider = None
                        wan1_comparison = None
                    
                    if wan2_public_ip and wan2_public_ip != wan2_ip:
                        wan2_provider = get_provider_for_ip(wan2_public_ip, ip_cache, missing_ips)
                        wan2_provider = f"{wan2_provider} (via DDNS)"
                    elif wan2_ip:
                        wan2_provider = get_provider_for_ip(wan2_ip, ip_cache, missing_ips)
                        wan2_comparison = compare_providers(wan2_provider, wan2_label)
                    else:
                        wan2_provider = None
                        wan2_comparison = None
                    
'''
    
    # Replace the existing provider lookup section
    old_lookup_start = content.find('if wan1_ip:', device_loop_start)
    old_lookup_end = content.find('device_entry = {', old_lookup_start)
    
    content = content[:old_lookup_start] + ddns_collection + '                    ' + content[old_lookup_end:]
    
    # Update device_entry to include DDNS fields
    device_entry_end = content.find('"raw_notes": raw_notes', device_entry_start)
    ddns_fields = ''',
                        "ddns_enabled": ddns_enabled,
                        "ddns_url": ddns_prefix,
                        "wan1_public_ip": wan1_public_ip if wan1_public_ip != wan1_ip else None,
                        "wan2_public_ip": wan2_public_ip if wan2_public_ip != wan2_ip else None,
                        "raw_notes": raw_notes'''
    
    content = content[:device_entry_end] + ddns_fields + content[device_entry_end + len('"raw_notes": raw_notes'):]
    
    # Update store_device_in_db function to save DDNS data
    store_func_start = content.find('def store_device_in_db(device_data, conn):')
    insert_sql_start = content.find('INSERT INTO meraki_inventory (', store_func_start)
    
    # Find the column list and add DDNS columns
    columns_end = content.find(') VALUES (', insert_sql_start)
    old_columns = content[insert_sql_start:columns_end]
    new_columns = old_columns.replace(
        'last_updated',
        'ddns_enabled, ddns_url, wan1_public_ip, wan2_public_ip,\n            last_updated'
    )
    
    # Find the values list and add DDNS values
    values_start = content.find('(%s, %s, %s', columns_end)
    values_end = content.find(')', values_start)
    value_count = content[values_start:values_end].count('%s')
    new_value_count = value_count + 4
    new_values = '(' + ', '.join(['%s'] * new_value_count) + ')'
    
    # Update the INSERT statement
    content = content[:insert_sql_start] + new_columns + content[columns_end:values_start] + new_values + content[values_end:]
    
    # Update the execute parameters
    exec_params_start = content.find('cursor.execute(insert_sql, (', store_func_start)
    exec_params_end = content.find('))', exec_params_start)
    old_params = content[exec_params_start:exec_params_end]
    
    # Insert DDNS parameters before last_updated
    new_params = old_params.replace(
        'datetime.now(timezone.utc)',
        '''device_data.get("ddns_enabled", False),
            device_data.get("ddns_url", ""),
            device_data.get("wan1_public_ip"),
            device_data.get("wan2_public_ip"),
            datetime.now(timezone.utc)'''
    )
    content = content[:exec_params_start] + new_params + content[exec_params_end:]
    
    # Update the UPDATE SET clause
    update_set_start = content.find('ON CONFLICT (device_serial) DO UPDATE SET', store_func_start)
    update_set_end = content.find('last_updated = EXCLUDED.last_updated', update_set_start)
    
    ddns_updates = '''ddns_enabled = EXCLUDED.ddns_enabled,
            ddns_url = EXCLUDED.ddns_url,
            wan1_public_ip = EXCLUDED.wan1_public_ip,
            wan2_public_ip = EXCLUDED.wan2_public_ip,
            '''
    
    content = content[:update_set_end] + ddns_updates + content[update_set_end:]
    
    # Write the updated script
    output_path = '/usr/local/bin/Main/nightly_meraki_db_with_ddns.py'
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Created updated script at: {output_path}")
    return output_path

if __name__ == '__main__':
    print("=== Adding DDNS Support to Meraki Script ===")
    print(f"Started at: {datetime.now()}")
    
    # Step 1: Add database columns
    add_ddns_columns()
    
    # Step 2: Create updated script
    script_path = create_updated_script()
    
    print("\n=== Summary ===")
    print("1. Added DDNS columns to meraki_inventory table")
    print("2. Created updated script with DDNS support")
    print("\nTo deploy:")
    print(f"1. Test: sudo python3 {script_path}")
    print("2. If successful, replace production script:")
    print("   sudo cp /usr/local/bin/Main/nightly/nightly_meraki_db.py /usr/local/bin/Main/nightly/nightly_meraki_db.py.backup_no_ddns")
    print(f"   sudo cp {script_path} /usr/local/bin/Main/nightly/nightly_meraki_db.py")