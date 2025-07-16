#!/usr/bin/env python3
"""
Analyze sessions.txt to find all IP addresses and compare with SNMP collection
"""
import re
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def extract_devices_from_sessions():
    """Extract all devices from sessions.txt"""
    devices = []
    
    try:
        with open('/var/www/html/meraki-data/bandwidth/sessions.txt', 'r') as f:
            content = f.read()
            
        # Find all SessionData entries
        pattern = r'<SessionData[^>]*SessionName="([^"]+)"[^>]*Host="([^"]+)"[^>]*>'
        matches = re.findall(pattern, content)
        
        for session_name, host in matches:
            # Filter for valid IP addresses
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host):
                devices.append({
                    'hostname': session_name,
                    'ip': host
                })
        
        return devices
        
    except Exception as e:
        print(f"Error reading sessions.txt: {e}")
        return []

def get_collected_devices():
    """Get devices currently in SNMP collection"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get devices from device_snmp_credentials
        cursor.execute("""
            SELECT hostname, ip_address
            FROM device_snmp_credentials
            ORDER BY ip_address
        """)
        
        snmp_devices = []
        for row in cursor.fetchall():
            hostname, ip = row
            snmp_devices.append({
                'hostname': hostname,
                'ip': str(ip)
            })
        
        # Get devices from comprehensive_device_inventory (recent collections)
        cursor.execute("""
            SELECT DISTINCT hostname, ip_address
            FROM comprehensive_device_inventory
            WHERE collection_timestamp >= NOW() - INTERVAL '30 days'
            ORDER BY ip_address
        """)
        
        collected_devices = []
        for row in cursor.fetchall():
            hostname, ip = row
            collected_devices.append({
                'hostname': hostname,
                'ip': str(ip)
            })
        
        return snmp_devices, collected_devices
        
    except Exception as e:
        print(f"Error querying database: {e}")
        return [], []
    finally:
        cursor.close()
        conn.close()

def analyze_missing_devices():
    """Main analysis function"""
    print("🔍 Analyzing sessions.txt vs SNMP collection...")
    print("="*80)
    
    # Get all devices from sessions.txt
    session_devices = extract_devices_from_sessions()
    print(f"📋 Found {len(session_devices)} devices in sessions.txt")
    
    # Get currently collected devices
    snmp_devices, collected_devices = get_collected_devices()
    print(f"🎯 Found {len(snmp_devices)} devices in SNMP credentials")
    print(f"📊 Found {len(collected_devices)} devices in recent collections")
    
    # Create sets for comparison
    session_ips = {d['ip'] for d in session_devices}
    snmp_ips = {d['ip'] for d in snmp_devices}
    collected_ips = {d['ip'] for d in collected_devices}
    
    # Find missing devices
    missing_from_snmp = session_ips - snmp_ips
    missing_from_collection = session_ips - collected_ips
    
    print(f"\n❌ Missing from SNMP credentials: {len(missing_from_snmp)} devices")
    print(f"❌ Missing from recent collections: {len(missing_from_collection)} devices")
    
    # Show detailed results
    if missing_from_snmp:
        print(f"\n{'='*80}")
        print("📋 DEVICES IN SESSIONS.TXT BUT NOT IN SNMP COLLECTION:")
        print("="*80)
        print(f"{'Hostname':<30} {'IP Address':<16} {'Category'}")
        print("-"*80)
        
        # Group by IP ranges for better analysis
        ip_ranges = {
            '10.0.': [],
            '10.101.': [],
            '10.44.': [],
            '10.41.': [],
            '10.42.': [],
            '10.43.': [],
            '192.168.': [],
            '172.16.': [],
            'other': []
        }
        
        for device in session_devices:
            if device['ip'] in missing_from_snmp:
                categorized = False
                for range_prefix, device_list in ip_ranges.items():
                    if device['ip'].startswith(range_prefix):
                        device_list.append(device)
                        categorized = True
                        break
                if not categorized:
                    ip_ranges['other'].append(device)
        
        # Display by category
        for range_prefix, devices in ip_ranges.items():
            if devices:
                print(f"\n🔸 {range_prefix}x.x range ({len(devices)} devices):")
                for device in sorted(devices, key=lambda x: x['ip']):
                    category = "Network Device"
                    if 'DMZ' in device['hostname']:
                        category = "DMZ/Firewall"
                    elif 'FW' in device['hostname']:
                        category = "Firewall"
                    elif 'DIA' in device['hostname']:
                        category = "DIA Router"
                    elif 'VG' in device['hostname']:
                        category = "Voice Gateway"
                    
                    print(f"  ❌ {device['hostname']:<28} {device['ip']:<16} {category}")
    
    # Show devices that are in SNMP but not in sessions.txt
    snmp_not_in_sessions = snmp_ips - session_ips
    if snmp_not_in_sessions:
        print(f"\n{'='*80}")
        print("⚠️  DEVICES IN SNMP COLLECTION BUT NOT IN SESSIONS.TXT:")
        print("="*80)
        for device in snmp_devices:
            if device['ip'] in snmp_not_in_sessions:
                print(f"  ⚠️  {device['hostname']:<28} {device['ip']}")
    
    # Summary and recommendations
    print(f"\n{'='*80}")
    print("📊 SUMMARY & RECOMMENDATIONS:")
    print("="*80)
    print(f"✅ Total devices in sessions.txt: {len(session_devices)}")
    print(f"✅ Currently in SNMP collection: {len(snmp_ips)}")
    print(f"❌ Missing from SNMP collection: {len(missing_from_snmp)}")
    print(f"🔄 Collection coverage: {((len(session_ips) - len(missing_from_snmp)) / len(session_ips) * 100):.1f}%")
    
    if missing_from_snmp:
        print(f"\n💡 NEXT STEPS:")
        print("1. Add missing devices to nightly_snmp_inventory_collection.py")
        print("2. Add missing devices to device_snmp_credentials table")
        print("3. Run SNMP collection to gather inventory")
        print("4. Update IP-to-site mappings as needed")
        
        # Generate code snippet for missing devices
        print(f"\n📝 CODE SNIPPET FOR MISSING DEVICES:")
        print("# Add to nightly_snmp_inventory_collection.py:")
        print("missing_devices = [")
        for device in session_devices:
            if device['ip'] in missing_from_snmp:
                credential = "DT_Network_SNMPv3" if device['ip'].startswith('192.168.') else "DTC4nmgt"
                cred_type = "v3" if device['ip'].startswith('192.168.') else "v2c"
                print(f'    {{"hostname": "{device["hostname"]}", "ip": "{device["ip"]}", "credential": "{credential}", "credential_type": "{cred_type}"}},')
        print("]")

if __name__ == "__main__":
    analyze_missing_devices()