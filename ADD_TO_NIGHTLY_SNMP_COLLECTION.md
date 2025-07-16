# Additional 192.168.x.x Devices for SNMP Collection

## Summary
The following devices need to be added to the nightly SNMP collection script (`nightly_snmp_inventory_collection.py`). They have been added to the `device_snmp_credentials` table but need to be included in the script's device list.

## Code to Add

Add this section after the `dmz_dia_devices` list in the `load_device_list()` function:

```python
# Add additional 192.168.x.x devices
additional_192_devices = [
    {"hostname": "HQ-NET-4-01", "ip": "192.168.4.1", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-4-02", "ip": "192.168.4.2", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-5-01", "ip": "192.168.5.1", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-5-02", "ip": "192.168.5.2", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-12-01", "ip": "192.168.12.1", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-12-02", "ip": "192.168.12.2", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-13-01", "ip": "192.168.13.1", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "HQ-NET-13-02", "ip": "192.168.13.2", "credential": "DT_Network_SNMPv3", "device_type": "HQ Network Device"},
    {"hostname": "AL-NET-200-10", "ip": "192.168.200.10", "credential": "DT_Network_SNMPv3", "device_type": "Alameda Network Device"},
    {"hostname": "AL-NET-200-11", "ip": "192.168.200.11", "credential": "DT_Network_SNMPv3", "device_type": "Alameda Network Device"}
]
```

Then add this loop after the `dmz_dia_devices` loop:

```python
for additional_device in additional_192_devices:
    devices.append({
        'hostname': additional_device['hostname'],
        'ip': additional_device['ip'],
        'credential': additional_device['credential'],
        'credential_type': 'v3',
        'device_type': additional_device['device_type'],
        'status': 'active',
        'source': 'manually_added_192_devices'
    })
```

## IP-to-Site Mappings Updated

The following IP ranges have been mapped in `nightly_snmp_inventory_web_format_v2.py`:

- `192.168.4.x` → AZ-Scottsdale-HQ-Corp
- `192.168.5.x` → AZ-Scottsdale-HQ-Corp  
- `192.168.12.x` → AZ-Scottsdale-HQ-Corp
- `192.168.13.x` → AZ-Scottsdale-HQ-Corp
- `192.168.200.x` → AZ-Alameda-DC

## Database Updates

- 10 devices added to `device_snmp_credentials` table
- All configured with SNMPv3 using `DT_Network_SNMPv3` username
- Sites updated in `inventory_web_format` for existing devices with these IPs

## Next Steps

1. Update `/usr/local/bin/Main/nightly_snmp_inventory_collection.py` with the code above
2. Run the nightly SNMP collection to gather inventory from these devices
3. The inventory will automatically appear in the web interface with correct site assignments