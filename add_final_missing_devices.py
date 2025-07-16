#!/usr/bin/env python3
"""
Add the final 3 missing devices to the nightly script
"""

# Read the current script
with open('/usr/local/bin/Main/nightly_snmp_inventory_collection.py', 'r') as f:
    content = f.read()

# Find where to add the devices - after the missing_nexus devices
insertion_point = content.find('missing_nexus = [')
if insertion_point != -1:
    # Find the end of the missing_nexus array
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'missing_nexus = [' in line:
            # Find the end of this array
            j = i + 1
            while j < len(lines) and ']' not in lines[j]:
                j += 1
            # Insert after the closing bracket
            if j < len(lines):
                # Add the final missing devices
                new_devices = [
                    '',
                    '            # Add final missing devices from sessions.txt analysis',
                    '            final_missing_devices = [',
                    '                {"hostname": "MDF-3130-O3-ENC1-A", "ip": "10.0.255.94", "credential": "DTC4nmgt", "device_type": "Network Device"},',
                    '                {"hostname": "FW-9400-01", "ip": "192.168.255.12", "credential": "DT_Network_SNMPv3", "device_type": "HQ Firewall"},',
                    '                {"hostname": "FW-9400-02", "ip": "192.168.255.13", "credential": "DT_Network_SNMPv3", "device_type": "HQ Firewall"}',
                    '            ]',
                    ''
                ]
                
                # Insert the new devices
                for k, new_line in enumerate(new_devices):
                    lines.insert(j + 1 + k, new_line)
                
                # Add the loop to include these devices
                loop_code = [
                    '            # Add final missing devices to the collection',
                    '            for missing_device in final_missing_devices:',
                    '                devices.append({',
                    '                    \'hostname\': missing_device[\'hostname\'],',
                    '                    \'ip\': missing_device[\'ip\'],',
                    '                    \'credential\': missing_device[\'credential\'],',
                    '                    \'credential_type\': \'v3\' if missing_device[\'credential\'] == \'DT_Network_SNMPv3\' else \'v2c\',',
                    '                    \'device_type\': missing_device[\'device_type\'],',
                    '                    \'status\': \'active\',',
                    '                    \'source\': \'final_missing_devices\'',
                    '                })',
                    '            ',
                ]
                
                # Add the loop after the device list
                for k, loop_line in enumerate(loop_code):
                    lines.insert(j + 1 + len(new_devices) + k, loop_line)
                
                break
    
    # Rejoin the lines
    new_content = '\n'.join(lines)
    
    # Write the updated script
    with open('/usr/local/bin/Main/nightly_snmp_inventory_collection_final.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Added final 3 missing devices to nightly script:")
    print("  • MDF-3130-O3-ENC1-A (10.0.255.94) - Network Device")
    print("  • FW-9400-01 (192.168.255.12) - HQ Firewall")
    print("  • FW-9400-02 (192.168.255.13) - HQ Firewall")
    print()
    print("📋 FINAL SUMMARY:")
    print("✅ Collection should now be complete for all valid devices in sessions.txt")
    print("⏳ Dallas/Atlanta devices will work as of Friday")
    print("🗑️ Invalid 8000V devices excluded")
    print("🎯 Ready for comprehensive SNMP collection!")
    
else:
    print("Could not find insertion point in script")