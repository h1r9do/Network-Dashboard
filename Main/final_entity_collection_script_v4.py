#!/usr/bin/env python3
"""
Final parallel ENTITY-MIB collection script for all devices
Based on the 187 devices Excel file with proper credentials
Updated to include T1r3s4u for VG350 devices
Updated to include missing Nexus 5K/56K/7K devices
Updated with chunked collection for Nexus 56128P devices to handle timeouts
"""
import json
import subprocess
import multiprocessing
import time
from datetime import datetime
import os
import sys

# Output configuration
OUTPUT_DIR = "/var/www/html/network-data"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Credential definitions
CREDENTIALS = {
    "DTC4nmgt": {
        "type": "SNMPv2c",
        "community": "DTC4nmgt"
    },
    "cldDcPub": {
        "type": "SNMPv2c",
        "community": "cldDcPub"
    },
    "DiscoDev1": {
        "type": "SNMPv2c",
        "community": "DiscoDev1"
    },
    "T1r3s4u": {
        "type": "SNMPv2c",
        "community": "T1r3s4u"
    },
    "EQX_DC_SNMPv3": {
        "type": "SNMPv3",
        "user": "EQX_DC_SNMPv3",
        "auth_protocol": "SHA",
        "auth_password": "EQX_SNMP_Pass",
        "priv_protocol": "AES",
        "priv_password": "3s6v9y$ShVkYp3s6"
    },
    "DT_Network_SNMPv3": {
        "type": "SNMPv3",
        "user": "DT_Network_SNMPv3",
        "auth_protocol": "SHA",
        "auth_password": "AqpKrRWd%%lk9",
        "priv_protocol": "AES",
        "priv_password": "70t3TgQDH[J!J"
    }
}

# Missing critical devices to add
MISSING_NEXUS_DEVICES = [
    # Nexus 5K/56K Switches
    {"hostname": "HQ-56128P-01", "ip": "10.0.255.111", "credential": "DTC4nmgt", "device_type": "Nexus 56128P"},
    {"hostname": "HQ-56128P-02", "ip": "10.0.255.112", "credential": "DTC4nmgt", "device_type": "Nexus 56128P"},
    {"hostname": "AL-5000-01", "ip": "10.101.145.125", "credential": "DTC4nmgt", "device_type": "Nexus 5000"},
    {"hostname": "AL-5000-02", "ip": "10.101.145.126", "credential": "DTC4nmgt", "device_type": "Nexus 5000"},
    
    # Nexus 7K VDCs - HQ
    {"hostname": "HQ-7000-01-ADMIN", "ip": "10.0.145.123", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "HQ-7000-02-ADMIN", "ip": "10.0.145.124", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "HQ-7000-01-EDGE", "ip": "10.0.145.2", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    
    # Nexus 7K VDCs - AL
    {"hostname": "AL-7000-01-ADMIN", "ip": "10.101.145.123", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "AL-7000-02-ADMIN", "ip": "10.101.145.124", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "AL-7000-01-CORE", "ip": "10.101.255.244", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "AL-7000-02-CORE", "ip": "10.0.184.20", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "AL-7000-01-EDGE", "ip": "10.101.100.209", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "AL-7000-02-EDGE", "ip": "10.101.100.217", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "AL-7000-01-PCI", "ip": "10.101.100.189", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
    {"hostname": "AL-7000-02-PCI", "ip": "10.101.100.201", "credential": "DTC4nmgt", "device_type": "Nexus 7K VDC"},
]

# Friday devices to add
FRIDAY_DEVICES = [
    {"name": "FP-DAL-ASR1001-01", "ip": "10.42.255.16", "credential": "DTC4nmgt", "status": "friday"},
    {"name": "FP-DAL-ASR1001-02", "ip": "10.42.255.26", "credential": "DTC4nmgt", "status": "friday"},
    {"name": "FP-ATL-ASR1001", "ip": "10.43.255.16", "credential": "DTC4nmgt", "status": "friday"},
    {"name": "AL-DMZ-7010-01", "ip": "192.168.200.10", "credential": "DT_Network_SNMPv3", "status": "friday"},
    {"name": "AL-DMZ-7010-02", "ip": "192.168.200.11", "credential": "DT_Network_SNMPv3", "status": "friday"},
    {"name": "DMZ-7010-01", "ip": "192.168.255.4", "credential": "DT_Network_SNMPv3", "status": "friday"},
    {"name": "DMZ-7010-02", "ip": "192.168.255.5", "credential": "DT_Network_SNMPv3", "status": "friday"}
]

# Devices that require chunked collection (known problematic devices)
CHUNKED_COLLECTION_DEVICES = [
    "10.0.255.111",  # HQ-56128P-01
    "10.0.255.112"   # HQ-56128P-02
]

def load_devices():
    """Load devices from the filtered 187 devices file and add missing ones"""
    device_file = "/tmp/filtered_snmp_devices_187.json"
    
    try:
        # Try to read with sudo if needed
        result = subprocess.run(['sudo', 'cat', device_file], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            devices = data['devices']
        else:
            print(f"ERROR: Cannot read {device_file}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Update credentials for specific devices
    for device in devices:
        # Assign default credential if not present
        if 'credential' not in device:
            device['credential'] = 'DTC4nmgt'
            device['credential_type'] = 'v2c'
        
        # VG350 devices use T1r3s4u
        if device['hostname'].startswith('HQ-VG350'):
            device['credential'] = 'T1r3s4u'
            device['credential_type'] = 'v2c'
    
    # Add missing Nexus devices
    print(f"Adding {len(MISSING_NEXUS_DEVICES)} missing Nexus devices...")
    for nexus_device in MISSING_NEXUS_DEVICES:
        device = {
            'hostname': nexus_device['hostname'],
            'ip': nexus_device['ip'],
            'credential': nexus_device['credential'],
            'credential_type': 'v2c',
            'device_type': nexus_device.get('device_type', ''),
            'status': 'active',
            'source': 'manually_added_critical_infrastructure'
        }
        devices.append(device)
    
    # Add Friday devices
    for friday_device in FRIDAY_DEVICES:
        device = {
            'hostname': friday_device['name'],
            'ip': friday_device['ip'],
            'credential': friday_device['credential'],
            'credential_type': 'v3' if 'v3' in friday_device['credential'] else 'v2c',
            'status': friday_device['status']
        }
        devices.append(device)
    
    return devices

def run_snmp_command(cmd, timeout=30):
    """Run SNMP command with timeout"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

def run_snmp_walk(ip, community, oid, timeout=60):
    """Run specific SNMP walk for chunked collection"""
    cmd = f"snmpwalk -v2c -c {community} -t 10 {ip} {oid}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

def collect_entity_mib_chunked(device):
    """Collect ENTITY-MIB using chunked approach for problematic devices"""
    name = device['hostname']
    ip = device['ip']
    cred_name = device['credential']
    
    print(f"[{os.getpid()}] Processing {name} ({ip}) with CHUNKED method")
    
    result = {
        "device_name": name,
        "ip": ip,
        "credential": cred_name,
        "timestamp": datetime.now().isoformat(),
        "status": "failed",
        "entity_data": {},
        "collection_method": "chunked"
    }
    
    # Add device type if available
    if 'device_type' in device:
        result['device_type'] = device['device_type']
    
    # Get credential info
    cred = CREDENTIALS.get(cred_name)
    if not cred or cred['type'] != 'SNMPv2c':
        result['error'] = f"Chunked collection only supports SNMPv2c, got: {cred_name}"
        return result
    
    community = cred['community']
    
    # Test connectivity
    sys_cmd = f"snmpget -v2c -c {community} -t 10 {ip} 1.3.6.1.2.1.1.1.0"
    sys_result = subprocess.run(sys_cmd, shell=True, capture_output=True, text=True, timeout=15)
    if sys_result.returncode != 0:
        result['error'] = "No SNMP response"
        return result
    
    result['system_description'] = sys_result.stdout.strip()
    
    # Collect specific ENTITY-MIB attributes in chunks
    entity_attributes = {
        "2": "description",    # entPhysicalDescr
        "5": "class",          # entPhysicalClass
        "7": "name",           # entPhysicalName
        "11": "serial_number", # entPhysicalSerialNum
        "13": "model_name"     # entPhysicalModelName
    }
    
    entities = {}
    total_collected = 0
    
    for attr_num, attr_name in entity_attributes.items():
        oid = f"1.3.6.1.2.1.47.1.1.1.1.{attr_num}"
        
        output = run_snmp_walk(ip, community, oid, timeout=60)
        if not output:
            continue
        
        lines = output.splitlines()
        
        for line in lines:
            if "=" in line:
                try:
                    oid_part, value_part = line.split("=", 1)
                    # Extract entity index
                    if f".47.1.1.1.1.{attr_num}." in oid_part:
                        parts = oid_part.split(".")
                        entity_idx = parts[-1]
                        
                        if entity_idx not in entities:
                            entities[entity_idx] = {}
                        
                        # Clean value
                        value = value_part.strip()
                        if "STRING:" in value:
                            value = value.split("STRING:", 1)[1].strip().strip('"')
                        elif "INTEGER:" in value:
                            value = value.split("INTEGER:", 1)[1].strip()
                        
                        entities[entity_idx][attr_name] = value
                        total_collected += 1
                except:
                    continue
    
    result['entity_data'] = entities
    result['entity_count'] = len(entities)
    result['total_attributes_collected'] = total_collected
    result['status'] = 'success' if entities else 'failed'
    
    if not entities:
        result['error'] = "No entity data collected"
    
    print(f"[{os.getpid()}] Completed {name} (CHUNKED): {len(entities)} entities")
    return result

def collect_entity_mib(device):
    """Collect ENTITY-MIB data from a single device"""
    name = device['hostname']
    ip = device['ip']
    cred_name = device['credential']
    
    # Check if this device needs chunked collection
    if ip in CHUNKED_COLLECTION_DEVICES:
        return collect_entity_mib_chunked(device)
    
    print(f"[{os.getpid()}] Processing {name} ({ip}) with {cred_name}")
    
    result = {
        "device_name": name,
        "ip": ip,
        "credential": cred_name,
        "timestamp": datetime.now().isoformat(),
        "status": "failed",
        "entity_data": {},
        "collection_method": "standard"
    }
    
    # Add device type if available
    if 'device_type' in device:
        result['device_type'] = device['device_type']
    
    # Skip Friday devices unless specified
    if device.get('status') == 'friday':
        result['status'] = 'pending_friday'
        return result
    
    # Build SNMP command
    cred = CREDENTIALS.get(cred_name)
    if not cred:
        result['error'] = f"Unknown credential: {cred_name}"
        return result
    
    if cred['type'] == 'SNMPv2c':
        snmp_base = f"snmpwalk -v2c -c {cred['community']} -t 10 {ip}"
        sys_cmd = f"snmpget -v2c -c {cred['community']} -t 10 {ip} 1.3.6.1.2.1.1.1.0"
    elif cred['type'] == 'SNMPv3':
        snmp_base = (
            f"snmpwalk -v3 -u {cred['user']} -l authPriv "
            f"-a {cred['auth_protocol']} -A '{cred['auth_password']}' "
            f"-x {cred['priv_protocol']} -X '{cred['priv_password']}' "
            f"-t 10 {ip}"
        )
        sys_cmd = (
            f"snmpget -v3 -u {cred['user']} -l authPriv "
            f"-a {cred['auth_protocol']} -A '{cred['auth_password']}' "
            f"-x {cred['priv_protocol']} -X '{cred['priv_password']}' "
            f"-t 10 {ip} 1.3.6.1.2.1.1.1.0"
        )
    
    # Test connectivity
    sys_desc = run_snmp_command(sys_cmd, timeout=15)
    if not sys_desc:
        result['error'] = "No SNMP response"
        return result
    
    result['system_description'] = sys_desc
    
    # Collect ENTITY-MIB data
    entity_cmd = f"{snmp_base} 1.3.6.1.2.1.47.1.1.1"
    entity_output = run_snmp_command(entity_cmd, timeout=60)
    
    if not entity_output:
        result['error'] = "ENTITY-MIB timeout"
        return result
    
    if "No Such Object" in entity_output:
        result['error'] = "ENTITY-MIB not supported"
        return result
    
    # Parse ENTITY-MIB output
    entities = {}
    for line in entity_output.splitlines():
        if "=" in line:
            try:
                oid_part, value_part = line.split("=", 1)
                # Extract entity index and attribute
                if ".47.1.1.1.1." in oid_part:
                    parts = oid_part.split(".")
                    attr_idx = parts[-2]
                    entity_idx = parts[-1]
                    
                    if entity_idx not in entities:
                        entities[entity_idx] = {}
                    
                    # Map common attributes
                    attr_map = {
                        "2": "description",
                        "5": "class",
                        "7": "name",
                        "11": "serial_number",
                        "13": "model_name"
                    }
                    
                    if attr_idx in attr_map:
                        value = value_part.strip()
                        if "STRING:" in value:
                            value = value.split("STRING:", 1)[1].strip().strip('"')
                        elif "INTEGER:" in value:
                            value = value.split("INTEGER:", 1)[1].strip()
                        
                        entities[entity_idx][attr_map[attr_idx]] = value
            except:
                continue
    
    result['entity_data'] = entities
    result['entity_count'] = len(entities)
    result['status'] = 'success'
    
    print(f"[{os.getpid()}] Completed {name}: {len(entities)} entities")
    return result

def process_device_batch(device_batch, batch_id):
    """Process a batch of devices"""
    results = []
    for device in device_batch:
        try:
            result = collect_entity_mib(device)
            results.append(result)
        except Exception as e:
            print(f"[{os.getpid()}] Error processing {device['hostname']}: {e}")
            results.append({
                "device_name": device['hostname'],
                "ip": device['ip'],
                "status": "error",
                "error": str(e)
            })
    
    # Save batch results
    batch_file = f"{OUTPUT_DIR}/batch_{batch_id}_{TIMESTAMP}.json"
    with open(batch_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Loading devices from 187 devices file and adding missing critical devices...")
    devices = load_devices()
    
    active_devices = [d for d in devices if d.get('status') != 'friday']
    friday_devices = [d for d in devices if d.get('status') == 'friday']
    
    print(f"Total devices: {len(devices)}")
    print(f"Active devices to process: {len(active_devices)}")
    print(f"Friday devices (pending): {len(friday_devices)}")
    
    # Show devices that will use chunked collection
    chunked_devices = [d for d in active_devices if d['ip'] in CHUNKED_COLLECTION_DEVICES]
    if chunked_devices:
        print(f"Devices using chunked collection: {len(chunked_devices)}")
        for device in chunked_devices:
            print(f"  {device['hostname']} ({device['ip']})")
    
    # Count by credential
    cred_counts = {}
    for device in devices:
        cred = device['credential']
        cred_counts[cred] = cred_counts.get(cred, 0) + 1
    
    print("\nCredential distribution:")
    for cred, count in sorted(cred_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cred}: {count} devices")
    
    # Show Nexus device count
    nexus_count = len([d for d in devices if 'Nexus' in d.get('device_type', '')])
    if nexus_count > 0:
        print(f"\nNexus devices included: {nexus_count}")
    
    # Split active devices into batches
    num_processes = min(10, max(1, len(active_devices) // 5))
    batch_size = max(1, len(active_devices) // num_processes)
    device_batches = [active_devices[i:i + batch_size] for i in range(0, len(active_devices), batch_size)]
    
    print(f"\nStarting {len(device_batches)} parallel processes...")
    start_time = time.time()
    
    # Process in parallel
    with multiprocessing.Pool(processes=num_processes) as pool:
        tasks = []
        for i, batch in enumerate(device_batches):
            task = pool.apply_async(process_device_batch, (batch, i))
            tasks.append(task)
        
        all_results = []
        for task in tasks:
            batch_results = task.get()
            all_results.extend(batch_results)
    
    # Add Friday devices to results
    for device in friday_devices:
        all_results.append({
            "device_name": device['hostname'],
            "ip": device['ip'],
            "credential": device['credential'],
            "status": "pending_friday"
        })
    
    elapsed_time = time.time() - start_time
    
    # Summary
    summary = {
        "collection_info": {
            "timestamp": datetime.now().isoformat(),
            "script_version": "v4_with_chunked_collection",
            "total_devices": len(devices),
            "active_devices_processed": len(active_devices),
            "friday_devices_pending": len(friday_devices),
            "nexus_devices_added": len(MISSING_NEXUS_DEVICES),
            "chunked_devices": len(chunked_devices),
            "elapsed_time_seconds": round(elapsed_time, 2),
            "devices_per_second": round(len(active_devices) / elapsed_time, 2) if elapsed_time > 0 else 0
        },
        "results_summary": {
            "success": len([r for r in all_results if r['status'] == 'success']),
            "failed": len([r for r in all_results if r['status'] == 'failed']),
            "pending_friday": len([r for r in all_results if r['status'] == 'pending_friday']),
            "error": len([r for r in all_results if r['status'] == 'error']),
            "chunked_success": len([r for r in all_results if r.get('collection_method') == 'chunked' and r['status'] == 'success'])
        },
        "credential_summary": cred_counts,
        "devices": all_results
    }
    
    # Save final results
    final_output = f"{OUTPUT_DIR}/final_entity_collection_{TIMESTAMP}.json"
    with open(final_output, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*60)
    print("ENTITY-MIB COLLECTION COMPLETE")
    print("="*60)
    print(f"Total devices: {summary['collection_info']['total_devices']}")
    print(f"Successful: {summary['results_summary']['success']}")
    print(f"Failed: {summary['results_summary']['failed']}")
    print(f"Pending Friday: {summary['results_summary']['pending_friday']}")
    print(f"Errors: {summary['results_summary']['error']}")
    print(f"Chunked collection success: {summary['results_summary']['chunked_success']}")
    print(f"Elapsed time: {summary['collection_info']['elapsed_time_seconds']} seconds")
    print(f"Collection rate: {summary['collection_info']['devices_per_second']} devices/second")
    print(f"\nResults saved to: {final_output}")
    print(f"Batch files in: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()