#!/usr/bin/env python3
"""
Setup device access for ALL devices in the inventory
Handles Nexus 7K VDCs as single physical devices
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

def identify_nexus_7k_physical_devices(cursor):
    """Identify Nexus 7K physical devices from VDCs"""
    
    # Nexus 7K VDCs have patterns like HQ-7000-01-ADMIN, HQ-7000-01-CORE, etc.
    # These are all the same physical device
    
    cursor.execute("""
        SELECT DISTINCT 
            CASE 
                WHEN hostname LIKE '%-7000-%-ADMIN' OR 
                     hostname LIKE '%-7000-%-CORE' OR 
                     hostname LIKE '%-7000-%-EDGE' OR 
                     hostname LIKE '%-7000-%-PCI' 
                THEN SUBSTRING(hostname FROM '^(.+-7000-\\d+)')
                ELSE hostname
            END as physical_device,
            mgmt_ip,
            hostname as vdc_name
        FROM datacenter_inventory
        WHERE hostname LIKE '%7000%'
        ORDER BY physical_device, hostname
    """)
    
    nexus_7k_devices = {}
    for physical, ip, vdc in cursor.fetchall():
        if physical not in nexus_7k_devices:
            nexus_7k_devices[physical] = {
                'vdcs': [],
                'mgmt_ip': ip
            }
        nexus_7k_devices[physical]['vdcs'].append(vdc)
        if ip:  # Update with non-null IP if found
            nexus_7k_devices[physical]['mgmt_ip'] = ip
    
    return nexus_7k_devices

def setup_all_device_access():
    """Setup device access for all devices"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Create physical device mapping table for VDCs
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
        
        # 1. Handle Nexus 7K devices specially
        nexus_7k_devices = identify_nexus_7k_physical_devices(cursor)
        
        logging.info(f"\n🔧 Found {len(nexus_7k_devices)} Nexus 7K physical devices:")
        for physical, info in nexus_7k_devices.items():
            logging.info(f"   {physical} with {len(info['vdcs'])} VDCs: {', '.join(info['vdcs'])}")
            
            # Add physical device access
            cursor.execute("""
                INSERT INTO device_access 
                (hostname, mgmt_ip, access_method, username, password, notes)
                VALUES (%s, %s, 'ssh', 'mbambic', 'Aud!o!994', %s)
                ON CONFLICT (hostname, mgmt_ip, access_method) DO UPDATE
                SET username = EXCLUDED.username,
                    password = EXCLUDED.password,
                    notes = EXCLUDED.notes,
                    updated_at = CURRENT_TIMESTAMP
            """, (physical, info['mgmt_ip'] or '', f"Nexus 7K with {len(info['vdcs'])} VDCs"))
            
            # Map VDCs to physical device
            for vdc in info['vdcs']:
                context = vdc.split('-')[-1]  # ADMIN, CORE, EDGE, PCI
                cursor.execute("""
                    INSERT INTO nexus_vdc_mapping 
                    (physical_hostname, vdc_hostname, vdc_context, mgmt_ip)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (vdc_hostname) DO UPDATE
                    SET physical_hostname = EXCLUDED.physical_hostname,
                        vdc_context = EXCLUDED.vdc_context,
                        mgmt_ip = EXCLUDED.mgmt_ip
                """, (physical, vdc, context, info['mgmt_ip']))
        
        # 2. Add all other devices with IPs (using a temp table to handle duplicates)
        cursor.execute("""
            CREATE TEMP TABLE temp_devices AS
            SELECT DISTINCT 
                CASE 
                    WHEN hostname LIKE '%-7000-%-ADMIN' OR 
                         hostname LIKE '%-7000-%-CORE' OR 
                         hostname LIKE '%-7000-%-EDGE' OR 
                         hostname LIKE '%-7000-%-PCI' 
                    THEN SUBSTRING(hostname FROM '^(.+-7000-\\d+)')
                    ELSE hostname
                END as device_hostname,
                mgmt_ip,
                device_type,
                site
            FROM datacenter_inventory
            WHERE mgmt_ip IS NOT NULL 
            AND mgmt_ip != ''
            AND hostname NOT LIKE '%7000%VDC%'  -- Skip VDCs, we handled them
        """)
        
        cursor.execute("""
            INSERT INTO device_access 
            (hostname, mgmt_ip, access_method, username, password, notes)
            SELECT DISTINCT 
                device_hostname,
                mgmt_ip, 
                'ssh', 
                'mbambic', 
                'Aud!o!994',
                CONCAT('Device Type: ', device_type, ', Site: ', site)
            FROM temp_devices
            WHERE NOT EXISTS (
                SELECT 1 FROM device_access da 
                WHERE da.hostname = temp_devices.device_hostname 
                AND da.mgmt_ip = temp_devices.mgmt_ip 
                AND da.access_method = 'ssh'
            )
        """)
        
        cursor.execute("DROP TABLE temp_devices")
        
        ssh_added = cursor.rowcount
        logging.info(f"✅ Added SSH access for {ssh_added} devices")
        
        # 3. Add SNMP as fallback for all devices
        snmp_communities = get_netdisco_snmp_communities()
        if snmp_communities:
            cursor.execute("""
                CREATE TEMP TABLE temp_snmp_devices AS
                SELECT DISTINCT 
                    CASE 
                        WHEN hostname LIKE '%-7000-%-ADMIN' OR 
                             hostname LIKE '%-7000-%-CORE' OR 
                             hostname LIKE '%-7000-%-EDGE' OR 
                             hostname LIKE '%-7000-%-PCI' 
                        THEN SUBSTRING(hostname FROM '^(.+-7000-\\d+)')
                        ELSE hostname
                    END as device_hostname,
                    mgmt_ip
                FROM datacenter_inventory
                WHERE mgmt_ip IS NOT NULL 
                AND mgmt_ip != ''
            """)
            
            cursor.execute("""
                INSERT INTO device_access 
                (hostname, mgmt_ip, access_method, snmp_community, snmp_version, notes)
                SELECT DISTINCT 
                    device_hostname,
                    mgmt_ip, 
                    'snmp', 
                    %s,
                    'v2c',
                    'SNMP fallback access'
                FROM temp_snmp_devices
                WHERE NOT EXISTS (
                    SELECT 1 FROM device_access da 
                    WHERE da.hostname = temp_snmp_devices.device_hostname 
                    AND da.mgmt_ip = temp_snmp_devices.mgmt_ip 
                    AND da.access_method = 'snmp'
                )
            """, (snmp_communities[0],))
            
            cursor.execute("DROP TABLE temp_snmp_devices")
            
            snmp_added = cursor.rowcount
            logging.info(f"✅ Added SNMP access for {snmp_added} devices")
        
        # 4. Special handling for known device types
        special_devices = [
            # Firewalls might need enable mode
            ("UPDATE device_access SET enable_password = password WHERE hostname LIKE '%PA%' OR hostname LIKE '%ASA%' OR hostname LIKE '%FW%'", "firewalls"),
            # Arista switches
            ("UPDATE device_access SET notes = CONCAT(notes, ', Arista Switch') WHERE hostname LIKE '%asa%' AND hostname NOT LIKE '%ASA%'", "Arista switches"),
            # Routers
            ("UPDATE device_access SET notes = CONCAT(notes, ', Router') WHERE hostname LIKE '%MPLS%' OR hostname LIKE '%gw%' OR hostname LIKE '%GW%'", "routers")
        ]
        
        for query, device_type in special_devices:
            cursor.execute(query)
            if cursor.rowcount > 0:
                logging.info(f"✅ Updated {cursor.rowcount} {device_type}")
        
        conn.commit()
        
        # Show summary
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT hostname) as unique_devices,
                COUNT(DISTINCT mgmt_ip) as unique_ips,
                COUNT(CASE WHEN access_method = 'ssh' THEN 1 END) as ssh_count,
                COUNT(CASE WHEN access_method = 'snmp' THEN 1 END) as snmp_count
            FROM device_access
        """)
        
        unique_devices, unique_ips, ssh_count, snmp_count = cursor.fetchone()
        
        print(f"\n📊 DEVICE ACCESS SUMMARY:")
        print(f"   Unique devices: {unique_devices}")
        print(f"   Unique IPs: {unique_ips}")
        print(f"   SSH access configured: {ssh_count}")
        print(f"   SNMP access configured: {snmp_count}")
        
        # Show device breakdown by type
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN notes LIKE '%Router%' THEN 'Routers'
                    WHEN notes LIKE '%Switch%' THEN 'Switches'
                    WHEN notes LIKE '%Firewall%' THEN 'Firewalls'
                    WHEN notes LIKE '%Nexus 5K%' THEN 'Nexus 5K'
                    WHEN notes LIKE '%Nexus 7K%' THEN 'Nexus 7K'
                    WHEN hostname LIKE '%PA%' THEN 'Palo Alto'
                    WHEN hostname LIKE '%ASA%' THEN 'Cisco ASA'
                    ELSE 'Other'
                END as device_category,
                COUNT(DISTINCT hostname) as count
            FROM device_access
            WHERE access_method = 'ssh'
            GROUP BY device_category
            ORDER BY count DESC
        """)
        
        print(f"\n📋 DEVICES BY CATEGORY:")
        for category, count in cursor.fetchall():
            print(f"   {category}: {count}")
        
        # Show sample devices
        cursor.execute("""
            SELECT hostname, mgmt_ip, access_method, 
                   CASE WHEN password IS NOT NULL THEN 'Yes' ELSE 'No' END as has_creds
            FROM device_access
            WHERE access_method = 'ssh'
            ORDER BY hostname
            LIMIT 10
        """)
        
        print(f"\n🔍 SAMPLE DEVICES:")
        for hostname, ip, method, has_creds in cursor.fetchall():
            print(f"   {hostname:30} | {ip:15} | {method:6} | Creds: {has_creds}")
        
    except Exception as e:
        logging.error(f"Setup failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_all_device_access()