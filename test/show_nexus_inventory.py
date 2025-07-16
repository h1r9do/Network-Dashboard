#!/usr/bin/env python3
"""
Show comprehensive Nexus 5K/2K inventory from database
"""

import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def show_nexus_inventory():
    """Display comprehensive Nexus 5K/2K inventory"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("🔧 NEXUS 5K/2K COMPREHENSIVE INVENTORY")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Get all Nexus 5K switches
    nexus_5k_switches = [
        ('HQ-56128P-01', '10.0.255.111', 'AZ-Scottsdale-HQ-Corp'),
        ('HQ-56128P-02', '10.0.255.112', 'AZ-Scottsdale-HQ-Corp'),
        ('AL-5000-01', '10.101.145.125', 'AZ-Alameda-DC'),
        ('AL-5000-02', '10.101.145.126', 'AZ-Alameda-DC')
    ]
    
    total_fex = 0
    
    for hostname, ip, site in nexus_5k_switches:
        print(f"\n📡 {hostname}")
        print(f"   Site: {site}")
        print(f"   IP: {ip}")
        
        # Get device info from datacenter_inventory
        cursor.execute("""
            SELECT model, serial_number, software_version
            FROM datacenter_inventory
            WHERE hostname = %s AND mgmt_ip = %s
            LIMIT 1
        """, (hostname, ip))
        
        device_info = cursor.fetchone()
        if device_info:
            model, serial, version = device_info
            print(f"   Model: {model}")
            print(f"   Serial: {serial}")
            print(f"   Version: {version}")
        
        # Get FEX modules from relationships table
        cursor.execute("""
            SELECT fex_number, fex_description, fex_model, fex_serial, fex_state
            FROM nexus_fex_relationships
            WHERE parent_hostname = %s
            ORDER BY fex_number
        """, (hostname,))
        
        fex_modules = cursor.fetchall()
        
        print(f"\n   N2K FEX Modules: {len(fex_modules)}")
        for fex_num, desc, model, serial, state in fex_modules:
            print(f"   └─ FEX {fex_num}: {desc}")
            print(f"      Model: {model}")
            print(f"      Serial: {serial}")
            print(f"      State: {state}")
            total_fex += 1
        
        # Get chassis blades (modules)
        cursor.execute("""
            SELECT cb.module_number, cb.card_type, cb.model, cb.ports
            FROM chassis_blades cb
            JOIN datacenter_inventory di ON cb.device_id = di.id
            WHERE di.hostname = %s
            ORDER BY cb.module_number
        """, (hostname,))
        
        modules = cursor.fetchall()
        if modules:
            print(f"\n   Chassis Modules: {len(modules)}")
            for mod_num, card_type, model, ports in modules[:5]:  # Show first 5
                print(f"   └─ Slot {mod_num}: {card_type} ({model}) - {ports} ports")
            if len(modules) > 5:
                print(f"   └─ ... and {len(modules) - 5} more modules")
        
        # Get SFP count
        cursor.execute("""
            SELECT COUNT(DISTINCT sf.id) as sfp_count
            FROM sfp_modules sf
            JOIN datacenter_inventory di ON sf.device_id = di.id
            WHERE di.hostname = %s
        """, (hostname,))
        
        sfp_count = cursor.fetchone()[0]
        if sfp_count > 0:
            print(f"\n   SFP Modules: {sfp_count}")
    
    print(f"\n📊 SUMMARY")
    print("="*80)
    print(f"Total Nexus 5K switches: 4")
    print(f"Total N2K FEX modules: {total_fex}")
    print(f"  • HQ Data Center: 2 Nexus 5K switches")
    print(f"  • Alameda Data Center: 2 Nexus 5K switches")
    
    # Show last collection times
    print(f"\n📅 LAST COLLECTION TIMES:")
    cursor.execute("""
        SELECT da.hostname, da.last_successful_access
        FROM device_access da
        WHERE da.hostname IN ('HQ-56128P-01', 'HQ-56128P-02', 'AL-5000-01', 'AL-5000-02')
        ORDER BY da.hostname
    """)
    
    for hostname, last_access in cursor.fetchall():
        if last_access:
            print(f"   {hostname}: {last_access.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"   {hostname}: Never collected")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    show_nexus_inventory()