#!/usr/bin/env python3
"""
Setup device access for ALL devices - Fixed version
Handles duplicates and Nexus 7K VDCs properly
"""

import sys
import psycopg2
import logging
import yaml

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_netdisco_snmp_communities():
    """Get SNMP communities from Netdisco config"""
    try:
        with open('/home/netdisco/environments/deployment.yml', 'r') as f:
            config = yaml.safe_load(f)
        
        snmp_communities = []
        if 'snmp_comm' in config:
            if isinstance(config['snmp_comm'], list):
                snmp_communities = config['snmp_comm']
            else:
                snmp_communities = [config['snmp_comm']]
        
        return snmp_communities
    except Exception as e:
        logging.warning(f"Could not read Netdisco config: {e}")
        return ['public', 'private']  # Defaults

def setup_all_device_access():
    """Setup device access for all devices"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nexus_vdc_mapping (
                id SERIAL PRIMARY KEY,
                physical_hostname VARCHAR(255) NOT NULL,
                vdc_hostname VARCHAR(255) NOT NULL,
                vdc_context VARCHAR(50),
                mgmt_ip VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vdc_hostname)
            )
        """)
        
        logging.info("📊 Setting up device access for ALL devices...")
        
        # Get unique devices from datacenter_inventory
        cursor.execute("""
            WITH unique_devices AS (
                SELECT DISTINCT ON (hostname, mgmt_ip)
                    hostname,
                    mgmt_ip,
                    device_type,
                    site,
                    model
                FROM datacenter_inventory
                WHERE mgmt_ip IS NOT NULL AND mgmt_ip != ''
                ORDER BY hostname, mgmt_ip, id DESC
            )
            SELECT * FROM unique_devices
        """)
        
        all_devices = cursor.fetchall()
        logging.info(f"Found {len(all_devices)} unique devices with IPs")
        
        # Process devices
        ssh_count = 0
        nexus_7k_count = 0
        nexus_5k_count = 0
        
        for hostname, mgmt_ip, device_type, site, model in all_devices:
            # Handle Nexus 7K VDCs
            if '-7000-' in hostname and any(vdc in hostname for vdc in ['-ADMIN', '-CORE', '-EDGE', '-PCI']):
                # This is a VDC - extract physical device name
                physical_name = hostname.rsplit('-', 1)[0]  # Remove VDC context
                vdc_context = hostname.rsplit('-', 1)[1]    # Get context (ADMIN, CORE, etc)
                
                # Add physical device
                cursor.execute("""
                    INSERT INTO device_access 
                    (hostname, mgmt_ip, access_method, username, password, notes)
                    VALUES (%s, %s, 'ssh', 'mbambic', 'Aud!o!994', %s)
                    ON CONFLICT (hostname, mgmt_ip, access_method) DO NOTHING
                """, (physical_name, mgmt_ip, f'Nexus 7K with VDCs, Site: {site}'))
                
                # Map VDC to physical
                cursor.execute("""
                    INSERT INTO nexus_vdc_mapping 
                    (physical_hostname, vdc_hostname, vdc_context, mgmt_ip)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (vdc_hostname) DO NOTHING
                """, (physical_name, hostname, vdc_context, mgmt_ip))
                
                nexus_7k_count += 1
                
            # Handle Nexus 5K
            elif '5000' in hostname or '56128' in hostname or (model and '5K' in str(model)):
                cursor.execute("""
                    INSERT INTO device_access 
                    (hostname, mgmt_ip, access_method, username, password, notes)
                    VALUES (%s, %s, 'ssh', 'mbambic', 'Aud!o!994', %s)
                    ON CONFLICT (hostname, mgmt_ip, access_method) DO NOTHING
                """, (hostname, mgmt_ip, f'Nexus 5K, Site: {site}'))
                nexus_5k_count += 1
                
            # All other devices
            else:
                notes = f'Type: {device_type}, Site: {site}'
                if model:
                    notes += f', Model: {model}'
                
                cursor.execute("""
                    INSERT INTO device_access 
                    (hostname, mgmt_ip, access_method, username, password, notes)
                    VALUES (%s, %s, 'ssh', 'mbambic', 'Aud!o!994', %s)
                    ON CONFLICT (hostname, mgmt_ip, access_method) DO NOTHING
                """, (hostname, mgmt_ip, notes))
            
            ssh_count += 1
        
        logging.info(f"✅ Added SSH access for {ssh_count} devices")
        logging.info(f"   • Nexus 7K VDCs: {nexus_7k_count}")
        logging.info(f"   • Nexus 5K switches: {nexus_5k_count}")
        
        # Add SNMP as fallback
        snmp_communities = get_netdisco_snmp_communities()
        if snmp_communities:
            cursor.execute("""
                INSERT INTO device_access 
                (hostname, mgmt_ip, access_method, snmp_community, snmp_version, notes)
                SELECT DISTINCT
                    hostname,
                    mgmt_ip,
                    'snmp',
                    %s,
                    'v2c',
                    'SNMP fallback'
                FROM device_access
                WHERE access_method = 'ssh'
                ON CONFLICT (hostname, mgmt_ip, access_method) DO NOTHING
            """, (snmp_communities[0],))
            
            snmp_added = cursor.rowcount
            logging.info(f"✅ Added SNMP fallback for {snmp_added} devices")
        
        # Special device handling
        special_updates = [
            ("UPDATE device_access SET enable_password = password WHERE hostname LIKE '%PA%' OR hostname LIKE '%ASA%' OR hostname LIKE '%FW%'", "firewalls"),
            ("UPDATE device_access SET ssh_port = 8181 WHERE hostname LIKE '%WLC%'", "wireless controllers"),
        ]
        
        for query, device_type in special_updates:
            cursor.execute(query)
            if cursor.rowcount > 0:
                logging.info(f"✅ Updated {cursor.rowcount} {device_type}")
        
        conn.commit()
        
        # Show summary
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT hostname) as devices,
                COUNT(DISTINCT CASE WHEN access_method = 'ssh' THEN hostname END) as ssh_devices,
                COUNT(DISTINCT CASE WHEN access_method = 'snmp' THEN hostname END) as snmp_devices
            FROM device_access
        """)
        
        devices, ssh_devices, snmp_devices = cursor.fetchone()
        
        print(f"\n📊 DEVICE ACCESS SUMMARY:")
        print(f"   Total unique devices: {devices}")
        print(f"   SSH access: {ssh_devices}")
        print(f"   SNMP access: {snmp_devices}")
        
        # Show Nexus devices
        cursor.execute("""
            SELECT hostname, mgmt_ip, notes
            FROM device_access
            WHERE (notes LIKE '%Nexus 5K%' OR notes LIKE '%Nexus 7K%')
            AND access_method = 'ssh'
            ORDER BY hostname
        """)
        
        print(f"\n🔧 NEXUS SWITCHES:")
        for hostname, ip, notes in cursor.fetchall():
            print(f"   {hostname:25} | {ip:15} | {notes}")
        
        # Show VDC mappings
        cursor.execute("""
            SELECT physical_hostname, COUNT(*) as vdc_count
            FROM nexus_vdc_mapping
            GROUP BY physical_hostname
            ORDER BY physical_hostname
        """)
        
        vdc_mappings = cursor.fetchall()
        if vdc_mappings:
            print(f"\n📋 NEXUS 7K VDC MAPPINGS:")
            for physical, count in vdc_mappings:
                print(f"   {physical}: {count} VDCs")
        
        # Sample other devices
        cursor.execute("""
            SELECT hostname, mgmt_ip, 
                   CASE WHEN password IS NOT NULL THEN 'Yes' ELSE 'No' END as has_ssh,
                   CASE WHEN snmp_community IS NOT NULL THEN 'Yes' ELSE 'No' END as has_snmp
            FROM device_access
            WHERE notes NOT LIKE '%Nexus%'
            ORDER BY hostname
            LIMIT 10
        """)
        
        print(f"\n🔍 SAMPLE OTHER DEVICES:")
        for hostname, ip, has_ssh, has_snmp in cursor.fetchall():
            print(f"   {hostname:30} | {ip:15} | SSH: {has_ssh} | SNMP: {has_snmp}")
        
    except Exception as e:
        logging.error(f"Setup failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_all_device_access()