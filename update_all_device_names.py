#!/usr/bin/env python3
"""
Update database with all real device names from sessions.txt
"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def update_all_devices():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Clear existing entries for these IP ranges
        cursor.execute("""
            DELETE FROM device_snmp_credentials 
            WHERE ip_address::text LIKE '192.168.%'
        """)
        print(f"Cleared {cursor.rowcount} existing 192.168.x.x entries")
        
        # Add all real devices from sessions.txt
        devices = [
            ("DMZ-7010-01", "192.168.255.4", "HQ DMZ Firewall"),
            ("DMZ-7010-02", "192.168.255.5", "HQ DMZ Firewall"),
            ("FW-9300-01", "192.168.255.12", "HQ Firewall"),
            ("FW-9300-02", "192.168.255.13", "HQ Firewall"),
            ("AL-DMZ-7010-01", "192.168.200.10", "Alameda DMZ Firewall"),
            ("AL-DMZ-7010-02", "192.168.200.11", "Alameda DMZ Firewall")
        ]
        
        print("\nAdding real devices from sessions.txt:")
        
        for hostname, ip, device_type in devices:
            cursor.execute("""
                INSERT INTO device_snmp_credentials 
                (hostname, ip_address, snmp_version, snmp_v3_username, 
                 snmp_v3_auth_protocol, snmp_v3_priv_protocol, snmp_v3_security_level,
                 snmp_port, snmp_timeout, snmp_retries, working)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 161, 10, 3, false)
            """, (
                hostname,
                ip,
                "3",
                "DT_Network_SNMPv3",
                "SHA",
                "AES",
                "authPriv"
            ))
            print(f"✅ Added {hostname} ({ip}) - {device_type}")
        
        conn.commit()
        
        # Show final status
        cursor.execute("""
            SELECT hostname, ip_address, snmp_v3_username, working
            FROM device_snmp_credentials
            WHERE ip_address::text LIKE '192.168.%'
            ORDER BY ip_address
        """)
        
        print(f"\nFinal 192.168.x.x devices in database:")
        for row in cursor.fetchall():
            hostname, ip, username, working = row
            status = "✓" if working else "✗"
            print(f"  {status} {hostname:<20} {ip:<16} SNMPv3: {username}")
        
        print("\n🎯 Database updated with all real devices from sessions.txt!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_all_devices()