#!/usr/bin/env python3
"""
Corrected analysis removing devices that are already in the nightly script
"""

# Devices already in nightly script
already_in_script = [
    # Equinix devices
    "10.44.158.11", "10.44.158.12", "10.44.158.21", "10.44.158.22",
    "10.44.158.41", "10.44.158.42", "10.44.158.51", "10.44.158.52",
    "10.44.158.61", "10.44.158.62",
    # DMZ/DIA devices  
    "192.168.255.4", "192.168.255.5", "192.168.255.14", "192.168.255.15"
]

# Original missing devices list
original_missing = [
    {"hostname": "MDF-3130-O3-ENC1-A", "ip": "10.0.255.94", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "IDFCNF-3750-Stack", "ip": "10.0.255.66", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "EQX-CldTrst-8500-01", "ip": "10.44.158.41", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "EQX-CldTrst-8500-02", "ip": "10.44.158.42", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "EQX-ASH-CldTrst-8000V-01", "ip": "137.174.158.207", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "EQX-ASH-CldTrst-8000V-02", "ip": "142.215.54.203", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "EQX-SIL-CldTrst-8000V-01", "ip": "142.215.221.195", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "EQX-SIL-CldTrst-8000V-02", "ip": "142.215.221.197", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "FP-DAL-ASR1001-01", "ip": "10.42.255.16", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "FP-DAL-ASR1001-02", "ip": "10.42.255.26", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "HQ-ATT-DIA", "ip": "192.168.255.15", "credential": "DT_Network_SNMPv3", "credential_type": "v3"},
    {"hostname": "HQ-LUMEN-DIA", "ip": "192.168.255.14", "credential": "DT_Network_SNMPv3", "credential_type": "v3"},
    {"hostname": "EQX-EdgeDIA-8300-01", "ip": "10.44.158.51", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "EQX-EdgeDIA-8300-02", "ip": "10.44.158.52", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "DMZ-7010-01", "ip": "192.168.255.4", "credential": "DT_Network_SNMPv3", "credential_type": "v3"},
    {"hostname": "DMZ-7010-02", "ip": "192.168.255.5", "credential": "DT_Network_SNMPv3", "credential_type": "v3"},
    {"hostname": "FW-9400-01", "ip": "192.168.255.12", "credential": "DT_Network_SNMPv3", "credential_type": "v3"},
    {"hostname": "FW-9400-02", "ip": "192.168.255.13", "credential": "DT_Network_SNMPv3", "credential_type": "v3"},
    {"hostname": "EQX-MPLS-8300-01", "ip": "10.44.158.61", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "EQX-MPLS-8300-02", "ip": "10.44.158.62", "credential": "DTC4nmgt", "credential_type": "v2c"},
    {"hostname": "FP-ATL-ASR1001", "ip": "10.43.255.16", "credential": "DTC4nmgt", "credential_type": "v2c"},
]

# Filter out devices already in script
actual_missing = [device for device in original_missing if device['ip'] not in already_in_script]

print("🎯 CORRECTED ANALYSIS - ACTUAL MISSING DEVICES:")
print("="*80)
print(f"Total devices that are actually missing: {len(actual_missing)}")
print()

# Group by IP range
ip_ranges = {
    '10.0.': [],
    '10.42.': [],
    '10.43.': [],
    '192.168.': [],
    'external': []
}

for device in actual_missing:
    categorized = False
    for range_prefix, device_list in ip_ranges.items():
        if device['ip'].startswith(range_prefix):
            device_list.append(device)
            categorized = True
            break
    if not categorized:
        ip_ranges['external'].append(device)

# Display by category
for range_prefix, devices in ip_ranges.items():
    if devices:
        print(f"🔸 {range_prefix} range ({len(devices)} devices):")
        for device in devices:
            category = "Network Device"
            if 'FW' in device['hostname']:
                category = "Firewall"
            elif 'DIA' in device['hostname']:
                category = "DIA Router"
            elif 'ASR' in device['hostname']:
                category = "Router"
            elif 'DMZ' in device['hostname']:
                category = "DMZ/Firewall"
            elif 'EQX' in device['hostname']:
                category = "Equinix Device"
            
            print(f"  ❌ {device['hostname']:<30} {device['ip']:<16} {category} ({device['credential_type']})")
        print()

print("📝 CORRECTED CODE FOR ACTUALLY MISSING DEVICES:")
print("="*80)
print("# Add these to nightly_snmp_inventory_collection.py:")
print("actual_missing_devices = [")
for device in actual_missing:
    print(f'    {{"hostname": "{device["hostname"]}", "ip": "{device["ip"]}", "credential": "{device["credential"]}", "device_type": "Network Device"}},')
print("]")
print()

print("📊 SUMMARY:")
print(f"✅ Devices correctly identified as already in script: {len(already_in_script)}")
print(f"❌ Devices actually missing: {len(actual_missing)}")
print(f"🔄 Corrected missing percentage: {(len(actual_missing) / (94 - len(already_in_script)) * 100):.1f}%")