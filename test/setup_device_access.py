#!/usr/bin/env python3
"""
Setup device access credentials in database
Initialize with known devices and their access methods
"""

import sys
import psycopg2
import logging

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def setup_device_access():
    """Setup device access table with known devices"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Create the device_access table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_access (
                id SERIAL PRIMARY KEY,
                hostname VARCHAR(255) NOT NULL,
                mgmt_ip VARCHAR(50) NOT NULL,
                access_method VARCHAR(20) NOT NULL,
                username VARCHAR(100),
                password VARCHAR(255),
                snmp_community VARCHAR(100),
                snmp_version VARCHAR(10),
                ssh_port INTEGER DEFAULT 22,
                enable_password VARCHAR(255),
                last_successful_access TIMESTAMP,
                last_failed_access TIMESTAMP,
                failure_count INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(hostname, mgmt_ip, access_method)
            )
        """)
        
        # Create FEX relationship table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nexus_fex_relationships (
                id SERIAL PRIMARY KEY,
                parent_hostname VARCHAR(255) NOT NULL,
                parent_ip VARCHAR(50),
                fex_number INTEGER NOT NULL,
                fex_description VARCHAR(255),
                fex_model VARCHAR(100),
                fex_serial VARCHAR(100),
                fex_state VARCHAR(50),
                ports INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(parent_hostname, fex_number)
            )
        """)
        
        # Add the 4 Nexus 5K switches with SSH credentials
        nexus_5k_devices = [
            ('HQ-56128P-01', '10.0.255.111', 'Nexus 5K at HQ'),
            ('HQ-56128P-02', '10.0.255.112', 'Nexus 5K at HQ'),
            ('AL-5000-01', '10.101.145.125', 'Nexus 5K at Alameda'),
            ('AL-5000-02', '10.101.145.126', 'Nexus 5K at Alameda')
        ]
        
        for hostname, ip, notes in nexus_5k_devices:
            cursor.execute("""
                INSERT INTO device_access 
                (hostname, mgmt_ip, access_method, username, password, notes)
                VALUES (%s, %s, 'ssh', 'mbambic', 'Aud!o!994', %s)
                ON CONFLICT (hostname, mgmt_ip, access_method) DO UPDATE
                SET username = EXCLUDED.username,
                    password = EXCLUDED.password,
                    notes = EXCLUDED.notes,
                    updated_at = CURRENT_TIMESTAMP
            """, (hostname, ip, notes))
            logging.info(f"Added SSH access for {hostname}")
        
        # Add other critical devices from datacenter inventory
        cursor.execute("""
            INSERT INTO device_access (hostname, mgmt_ip, access_method, username, password)
            SELECT DISTINCT hostname, mgmt_ip, 'ssh', 'mbambic', 'Aud!o!994'
            FROM datacenter_inventory
            WHERE mgmt_ip IS NOT NULL AND mgmt_ip != ''
            AND hostname IN (
                SELECT hostname FROM datacenter_inventory 
                WHERE device_type IN ('Router', 'Switch', 'Firewall')
                AND hostname IS NOT NULL
            )
            ON CONFLICT (hostname, mgmt_ip, access_method) DO NOTHING
        """)
        
        added = cursor.rowcount
        logging.info(f"Added {added} additional devices with SSH access")
        
        # Check if Netdisco SNMP config exists
        try:
            import yaml
            with open('/home/netdisco/environments/deployment.yml', 'r') as f:
                config = yaml.safe_load(f)
            
            snmp_communities = []
            if 'snmp_comm' in config:
                if isinstance(config['snmp_comm'], list):
                    snmp_communities = config['snmp_comm']
                else:
                    snmp_communities = [config['snmp_comm']]
            
            if snmp_communities:
                # Add SNMP as fallback for all devices
                cursor.execute("""
                    INSERT INTO device_access (hostname, mgmt_ip, access_method, snmp_community, snmp_version)
                    SELECT DISTINCT hostname, mgmt_ip, 'snmp', %s, 'v2c'
                    FROM datacenter_inventory
                    WHERE mgmt_ip IS NOT NULL AND mgmt_ip != ''
                    ON CONFLICT (hostname, mgmt_ip, access_method) DO NOTHING
                """, (snmp_communities[0],))
                
                snmp_added = cursor.rowcount
                logging.info(f"Added SNMP access for {snmp_added} devices")
        except Exception as e:
            logging.warning(f"Could not setup SNMP access: {e}")
        
        conn.commit()
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM device_access WHERE access_method = 'ssh'")
        ssh_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM device_access WHERE access_method = 'snmp'")
        snmp_count = cursor.fetchone()[0]
        
        logging.info(f"\n📊 Device Access Summary:")
        logging.info(f"   SSH devices: {ssh_count}")
        logging.info(f"   SNMP devices: {snmp_count}")
        
        # Show Nexus 5K devices
        cursor.execute("""
            SELECT hostname, mgmt_ip, access_method, notes
            FROM device_access
            WHERE hostname LIKE '%5000%' OR hostname LIKE '%56128%'
            ORDER BY hostname
        """)
        
        print("\n🔧 Nexus 5K Switches Configured:")
        for row in cursor.fetchall():
            print(f"   {row[0]:20} | {row[1]:15} | {row[2]:6} | {row[3]}")
        
    except Exception as e:
        logging.error(f"Setup failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_device_access()