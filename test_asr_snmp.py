#!/usr/bin/env python3
"""
Test ASR SNMP Collection - Simplified version
Only tests the 3 ASR routers with DT_Network_SNMPv3 credentials
"""
import json
import subprocess
import time
from datetime import datetime
import os
import sys
import logging
from subprocess import TimeoutExpired

# Add the directory containing our modules to the path
sys.path.append('/usr/local/bin/Main')

# Import our custom modules
from credential_manager import SNMPCredentialManager

# Set correct database credentials
os.environ['DB_USER'] = 'dsruser'
os.environ['DB_PASSWORD'] = 'dsrpass123'
os.environ['DB_NAME'] = 'dsrcircuits'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

def collect_entity_mib(device, credentials):
    """Collect ENTITY-MIB data from device - EXACT COPY from main script"""
    name = device['hostname']
    ip = device['ip']
    cred_name = device['credential']
    
    logger.info(f"Processing {name} ({ip}) with {cred_name}")
    
    result = {
        "device_name": name,
        "ip": ip,
        "credential": cred_name,
        "timestamp": datetime.now().isoformat(),
        "status": "failed",
        "entity_data": {},
        "collection_method": "standard"
    }
    
    if 'device_type' in device:
        result['device_type'] = device['device_type']
    
    # Get credential
    cred = credentials.get(cred_name)
    if not cred:
        result['error'] = f"Credential not found: {cred_name}"
        return result
    
    # Build SNMP commands - EXACT COPY
    if cred['type'] == 'SNMPv2c':
        snmp_base = f"snmpwalk -v2c -c {cred['community']} -t 10 {ip}"
        sys_cmd = f"snmpget -v2c -c {cred['community']} -t 10 {ip} 1.3.6.1.2.1.1.1.0"
    elif cred['type'] == 'SNMPv3':
        snmp_base = (f"snmpwalk -v3 -u {cred['user']} -l authPriv "
                     f"-a {cred['auth_protocol']} -A '{cred['auth_password']}' "
                     f"-x {cred['priv_protocol']} -X '{cred['priv_password']}' "
                     f"-t 10 {ip}")
        sys_cmd = (f"snmpget -v3 -u {cred['user']} -l authPriv "
                   f"-a {cred['auth_protocol']} -A '{cred['auth_password']}' "
                   f"-x {cred['priv_protocol']} -X '{cred['priv_password']}' "
                   f"-t 10 {ip} 1.3.6.1.2.1.1.1.0")
    else:
        result['error'] = f"Unsupported credential type: {cred['type']}"
        return result
    
    # Log the command (redacted)
    if cred['type'] == 'SNMPv3':
        cmd_redacted = sys_cmd.replace(cred['auth_password'], '[AUTH_PASS]').replace(cred['priv_password'], '[PRIV_PASS]')
        logger.info(f"SNMP command: {cmd_redacted}")
    
    # Test connectivity
    sys_desc = run_snmp_command(sys_cmd, timeout=15)
    if not sys_desc:
        result['error'] = "No SNMP response"
        # Try to get more details
        try:
            test_result = subprocess.run(sys_cmd, shell=True, capture_output=True, text=True, timeout=15)
            logger.error(f"SNMP stderr: {test_result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("SNMP command timed out after 15 seconds")
        except Exception as e:
            logger.error(f"SNMP error: {str(e)}")
        return result
    
    result['system_description'] = sys_desc
    
    # Collect ENTITY-MIB
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
                if ".47.1.1.1.1." in oid_part:
                    parts = oid_part.split(".")
                    attr_idx = parts[-2]
                    entity_idx = parts[-1]
                    
                    if entity_idx not in entities:
                        entities[entity_idx] = {}
                    
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
    
    logger.info(f"Completed {name}: {len(entities)} entities")
    return result

def main():
    """Test only ASR routers"""
    logger.info("="*60)
    logger.info("ASR ROUTER SNMP TEST")
    logger.info("="*60)
    
    # ASR routers to test - EXACT from main script
    asr_devices = [
        {"hostname": "FP-DAL-ASR1001-01", "ip": "10.42.255.16", "credential": "DT_Network_SNMPv3", "device_type": "Dallas Router"},
        {"hostname": "FP-DAL-ASR1001-02", "ip": "10.42.255.26", "credential": "DT_Network_SNMPv3", "device_type": "Dallas Router"},
        {"hostname": "FP-ATL-ASR1001", "ip": "10.43.255.16", "credential": "DT_Network_SNMPv3", "device_type": "Atlanta Router"}
    ]
    
    # Load credentials from database
    logger.info("Loading credentials from database...")
    credential_manager = SNMPCredentialManager()
    credentials = credential_manager.get_all_credentials()
    credential_manager.close_db()
    
    if not credentials:
        logger.error("No credentials found in database")
        return
    
    logger.info(f"Loaded {len(credentials)} credentials")
    
    # Test each ASR router
    results = []
    for device in asr_devices:
        logger.info("-"*40)
        result = collect_entity_mib(device, credentials)
        results.append(result)
        
        if result['status'] == 'success':
            logger.info(f"✅ SUCCESS: {device['hostname']}")
            logger.info(f"   Entities collected: {result['entity_count']}")
        else:
            logger.error(f"❌ FAILED: {device['hostname']}")
            logger.error(f"   Error: {result.get('error', 'Unknown')}")
    
    # Save results
    output_file = f"/tmp/asr_snmp_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("="*60)
    logger.info(f"Results saved to: {output_file}")
    logger.info("="*60)

if __name__ == "__main__":
    main()