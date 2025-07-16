#!/usr/bin/env python3
"""
Download firewall rules for networks with specific location tags
"""

import os
import sys
import json
import requests
import time
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Get API key
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
if not MERAKI_API_KEY:
    print("Error: MERAKI_API_KEY not found in environment")
    sys.exit(1)

BASE_URL = 'https://api.meraki.com/api/v1'

# Location types to find
LOCATION_TYPES = [
    'Full-Service',
    'Warehouse',
    'Call-Center',
    'Regional-Office',
    'MDC'
]

def get_db_connection():
    """Get database connection"""
    import re
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def make_api_request(url, headers, max_retries=3):
    """Make API request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 429:  # Rate limited
                print(f"Rate limited, waiting 2 seconds...")
                time.sleep(2)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None

def find_networks_with_tags(conn):
    """Find networks with specific location tags from database"""
    cursor = conn.cursor()
    networks_by_tag = {}
    
    for tag in LOCATION_TYPES:
        # Query meraki_live_data which has network_id
        cursor.execute("""
            SELECT DISTINCT network_name, network_id, device_tags
            FROM meraki_live_data
            WHERE network_id IS NOT NULL 
            AND network_id <> ''
            AND device_tags LIKE %s
            AND device_tags NOT LIKE '%%hub%%'
            AND device_tags NOT LIKE '%%voice%%'  
            AND device_tags NOT LIKE '%%lab%%'
            ORDER BY network_name
            LIMIT 1
        """, (f'%{tag}%',))
        
        result = cursor.fetchone()
        if result:
            network_name, network_id, device_tags = result
            networks_by_tag[tag] = {
                'network_name': network_name,
                'network_id': network_id,
                'device_tags': device_tags
            }
            print(f"✅ Found network for {tag}: {network_name} (ID: {network_id})")
        else:
            print(f"❌ No network found for tag: {tag}")
    
    cursor.close()
    return networks_by_tag

def download_firewall_rules(network_id, network_name):
    """Download L3 firewall rules for a network"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    print(f"  Downloading rules from: {network_name}")
    
    rules_data = make_api_request(url, headers)
    if rules_data:
        rules = rules_data.get('rules', [])
        print(f"  Downloaded {len(rules)} rules")
        return rules
    else:
        print(f"  Failed to download rules")
        return None

def store_rules_in_database(conn, network_id, network_name, rules, tag):
    """Store firewall rules in database"""
    cursor = conn.cursor()
    
    try:
        # First, clear any existing rules for this network
        cursor.execute("""
            DELETE FROM firewall_rules 
            WHERE network_name = %s 
            AND template_source = %s
        """, (network_name, tag))
        
        # Insert rules
        for i, rule in enumerate(rules):
            cursor.execute("""
                INSERT INTO firewall_rules (
                    network_id, network_name, rule_order, comment, policy,
                    protocol, src_port, src_cidr, dest_port, dest_cidr,
                    syslog_enabled, rule_type, is_template, template_source,
                    created_at, updated_at, last_synced
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    NOW(), NOW(), NOW()
                )
            """, (
                network_id,
                network_name,
                i + 1,  # rule_order
                rule.get('comment', ''),
                rule.get('policy', 'allow'),
                rule.get('protocol', 'any'),
                rule.get('srcPort', 'Any'),
                rule.get('srcCidr', 'Any'),
                rule.get('destPort', 'Any'),
                rule.get('destCidr', 'Any'),
                rule.get('syslogEnabled', False),
                'l3',  # rule_type
                True,  # is_template
                tag,   # template_source (the location type)
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
        
        conn.commit()
        print(f"  ✅ Stored {len(rules)} rules in database as {tag} template")
        
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error storing rules: {e}")
    finally:
        cursor.close()

def main():
    print("=== Downloading Firewall Rules by Location Type ===\n")
    
    # Connect to database
    conn = get_db_connection()
    
    # Find networks with the required tags
    print("Step 1: Finding networks with location tags...")
    networks_by_tag = find_networks_with_tags(conn)
    
    if not networks_by_tag:
        print("\nNo networks found with the specified tags.")
        conn.close()
        return
    
    # Download and store rules for each network
    print("\nStep 2: Downloading firewall rules...")
    for tag, network_info in networks_by_tag.items():
        print(f"\n{tag}:")
        network_id = network_info['network_id']
        network_name = network_info['network_name']
        
        # Download rules
        rules = download_firewall_rules(network_id, network_name)
        
        if rules:
            # Store in database
            store_rules_in_database(conn, network_id, network_name, rules, tag)
            
            # Also save to JSON file for reference
            filename = f"/usr/local/bin/Main/{tag.lower().replace('-', '_')}_firewall_rules.json"
            with open(filename, 'w') as f:
                json.dump({
                    'network_name': network_name,
                    'network_id': network_id,
                    'tag': tag,
                    'rule_count': len(rules),
                    'rules': rules,
                    'downloaded_at': datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
            print(f"  Saved to: {filename}")
        
        # Rate limit between networks
        time.sleep(1)
    
    # Summary
    print("\n=== Summary ===")
    cursor = conn.cursor()
    for tag in LOCATION_TYPES:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM firewall_rules 
            WHERE template_source = %s
        """, (tag,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"{tag}: {count} rules stored")
    
    cursor.close()
    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()