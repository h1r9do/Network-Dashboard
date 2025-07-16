#!/usr/bin/env python3
"""
Update nightly script with all real devices from sessions.txt
"""

# Read the current script
with open('/usr/local/bin/Main/nightly_snmp_inventory_collection.py', 'r') as f:
    content = f.read()

# Find the current additional devices section and replace it
old_section = '''            # Add additional 192.168.x.x devices (real devices from sessions.txt)
            additional_192_devices = [
                # Note: 192.168.4/5/12/13 ranges mentioned but no specific devices found in sessions.txt
                # Adding generic entries for these ranges - update with actual device names when found
                {"hostname": "UNKNOWN-192-168-4-DEVICE", "ip": "192.168.4.1", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
                {"hostname": "UNKNOWN-192-168-5-DEVICE", "ip": "192.168.5.1", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
                {"hostname": "UNKNOWN-192-168-12-DEVICE", "ip": "192.168.12.1", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
                {"hostname": "UNKNOWN-192-168-13-DEVICE", "ip": "192.168.13.1", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
                # Real devices from sessions.txt
                {"hostname": "AL-DMZ-7010-01", "ip": "192.168.200.10", "credential": "DT_Network_SNMPv3", "device_type": "Alameda DMZ Firewall"},
                {"hostname": "AL-DMZ-7010-02", "ip": "192.168.200.11", "credential": "DT_Network_SNMPv3", "device_type": "Alameda DMZ Firewall"}
            ]'''

new_section = '''            # Add additional 192.168.x.x devices (real devices from sessions.txt)
            additional_192_devices = [
                # DMZ/CORP devices from sessions.txt
                {"hostname": "DMZ-7010-01", "ip": "192.168.255.4", "credential": "DT_Network_SNMPv3", "device_type": "HQ DMZ Firewall"},
                {"hostname": "DMZ-7010-02", "ip": "192.168.255.5", "credential": "DT_Network_SNMPv3", "device_type": "HQ DMZ Firewall"},
                {"hostname": "FW-9300-01", "ip": "192.168.255.12", "credential": "DT_Network_SNMPv3", "device_type": "HQ Firewall"},
                {"hostname": "FW-9300-02", "ip": "192.168.255.13", "credential": "DT_Network_SNMPv3", "device_type": "HQ Firewall"},
                # DMZ/ALAMEDA devices from sessions.txt
                {"hostname": "AL-DMZ-7010-01", "ip": "192.168.200.10", "credential": "DT_Network_SNMPv3", "device_type": "Alameda DMZ Firewall"},
                {"hostname": "AL-DMZ-7010-02", "ip": "192.168.200.11", "credential": "DT_Network_SNMPv3", "device_type": "Alameda DMZ Firewall"}
            ]'''

# Replace the device section
content = content.replace(old_section, new_section)

# Write the updated script
with open('/usr/local/bin/Main/nightly_snmp_inventory_collection_all_devices.py', 'w') as f:
    f.write(content)

print("Updated nightly script with all real devices from sessions.txt!")
print("Added devices:")
print("  • DMZ-7010-01 (192.168.255.4)")
print("  • DMZ-7010-02 (192.168.255.5)")
print("  • FW-9300-01 (192.168.255.12)")
print("  • FW-9300-02 (192.168.255.13)")
print("  • AL-DMZ-7010-01 (192.168.200.10)")
print("  • AL-DMZ-7010-02 (192.168.200.11)")