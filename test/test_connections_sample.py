#!/usr/bin/env python3
"""
Test connections to a sample of devices to verify the approach
"""

import json
import sys
sys.path.append('/usr/local/bin/test')
from test_all_connections_with_snmp import *

def test_sample_connections():
    """Test just a few devices"""
    
    # Get devices from database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get a sample of devices - different types
        cursor.execute("""
            SELECT DISTINCT hostname, mgmt_ip, device_type, site, model
            FROM datacenter_inventory
            WHERE mgmt_ip IS NOT NULL AND mgmt_ip != ''
            AND (
                hostname LIKE '%5000%' OR  -- Nexus 5K
                hostname LIKE '%7000%' OR  -- Nexus 7K  
                hostname LIKE '%ASA%' OR   -- Firewall
                hostname LIKE '%2960%'     -- Switch
            )
            ORDER BY hostname
            LIMIT 10
        """)
        
        devices = []
        for hostname, mgmt_ip, device_type, site, model in cursor.fetchall():
            devices.append({
                'hostname': hostname,
                'ip': mgmt_ip,
                'device_type': device_type or 'Unknown',
                'site': site or 'Unknown',
                'model': model or 'Unknown'
            })
        
    finally:
        cursor.close()
        conn.close()
    
    logging.info(f"Testing {len(devices)} sample devices")
    
    # Test each device
    results = {}
    for device in devices:
        hostname = device['hostname']
        ip = device['ip']
        
        logging.info(f"\n{'='*60}")
        logging.info(f"Testing {hostname} ({ip})")
        logging.info(f"{'='*60}")
        
        # Test SSH
        ssh_success = False
        snmp_communities = []
        
        success, message, snmp_config = test_ssh_connection(
            hostname, ip, 'mbambic', 'Aud!o!994'
        )
        
        if success:
            ssh_success = True
            logging.info(f"✅ SSH successful")
            
            if snmp_config and snmp_config['communities']:
                snmp_communities = snmp_config['communities']
                logging.info(f"📡 SNMP communities found: {snmp_communities}")
                logging.info(f"📋 SNMP ACLs: {json.dumps(snmp_config['acls'], indent=2)}")
        else:
            logging.info(f"❌ SSH failed: {message}")
        
        # Test SNMP with found communities
        snmp_success = False
        working_community = None
        
        communities_to_try = snmp_communities + ['public', 'private']
        communities_to_try = list(dict.fromkeys(communities_to_try))  # Remove duplicates
        
        for community in communities_to_try:
            success, message = test_snmp_connection(hostname, ip, community)
            if success:
                snmp_success = True
                working_community = community
                source = 'device' if community in snmp_communities else 'default'
                logging.info(f"✅ SNMP successful with '{community}' (from {source})")
                break
        
        if not snmp_success:
            logging.info(f"❌ SNMP failed with all communities")
        
        # Store results
        results[hostname] = {
            'ip': ip,
            'ssh_works': ssh_success,
            'snmp_works': snmp_success,
            'snmp_community': working_community,
            'device_snmp_communities': snmp_communities
        }
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Hostname':<30} {'SSH':<5} {'SNMP':<5} {'Community':<20}")
    print(f"{'-'*30} {'-'*5} {'-'*5} {'-'*20}")
    
    for hostname, info in results.items():
        ssh = '✓' if info['ssh_works'] else '✗'
        snmp = '✓' if info['snmp_works'] else '✗'
        community = info['snmp_community'] or 'N/A'
        print(f"{hostname:<30} {ssh:<5} {snmp:<5} {community:<20}")
    
    # Save sample results
    output_file = '/var/www/html/meraki-data/device_connections_sample.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"\nSample results saved to: {output_file}")

if __name__ == "__main__":
    test_sample_connections()