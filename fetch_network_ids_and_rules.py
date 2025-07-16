#!/usr/bin/env python3
"""
Fetch network IDs from Meraki API and download firewall rules for specific networks
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
ORG_NAME = "DTC-Store-Inventory-All"

# Networks to fetch rules for (based on what we found in database)
TARGET_NETWORKS = {
    'Warehouse': ['CAL W01', 'CAN W02', 'INI W01', 'MNM W01', 'MOSW 01'],
    'MDC': ['COX 01'],
    'Discount-Tire': ['ALB 01', 'AZP 01'],  # Common store type
}

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

def get_organization_id():
    """Get organization ID from Meraki API"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    orgs = make_api_request(f"{BASE_URL}/organizations", headers)
    if not orgs:
        return None
        
    for org in orgs:
        if org.get('name') == ORG_NAME:
            return org.get('id')
    
    # If exact match not found, try partial match
    for org in orgs:
        if 'DTC' in org.get('name', '') and 'Store' in org.get('name', ''):
            print(f"Using organization: {org.get('name')}")
            return org.get('id')
    
    return None

def get_all_networks(org_id):
    """Get all networks in organization"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    print("Fetching all networks...")
    all_networks = []
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    params = {'perPage': 1000, 'startingAfter': None}
    
    while True:
        if params['startingAfter']:
            networks = make_api_request(f"{url}?perPage={params['perPage']}&startingAfter={params['startingAfter']}", headers)
        else:
            networks = make_api_request(f"{url}?perPage={params['perPage']}", headers)
            
        if not networks:
            break
            
        all_networks.extend(networks)
        if len(networks) < params['perPage']:
            break
            
        params['startingAfter'] = networks[-1]['id']
        print(f"  Fetched {len(all_networks)} networks so far...")
    
    return all_networks

def download_firewall_rules(network_id, network_name):
    """Download L3 firewall rules for a network"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    print(f"  Downloading rules for: {network_name}")
    
    rules_data = make_api_request(url, headers)
    if rules_data:
        rules = rules_data.get('rules', [])
        print(f"  ✅ Downloaded {len(rules)} rules")
        return rules
    else:
        print(f"  ❌ Failed to download rules")
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
            ))
        
        conn.commit()
        print(f"  ✅ Stored {len(rules)} rules in database as {tag} template")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error storing rules: {e}")
        return False
    finally:
        cursor.close()

def main():
    print("=== Fetching Network IDs and Firewall Rules ===\n")
    
    # Connect to database
    conn = get_db_connection()
    
    # Get organization ID
    print("Step 1: Getting organization ID...")
    org_id = get_organization_id()
    if not org_id:
        print("❌ Failed to get organization ID")
        return
    print(f"✅ Organization ID: {org_id}")
    
    # Get all networks
    print("\nStep 2: Fetching all networks...")
    all_networks = get_all_networks(org_id)
    if not all_networks:
        print("❌ Failed to get networks")
        return
    print(f"✅ Found {len(all_networks)} networks")
    
    # Create lookup dictionary
    network_lookup = {net['name'].strip().upper(): net for net in all_networks}
    
    # Process each location type
    print("\nStep 3: Processing networks by location type...")
    rules_downloaded = {}
    
    for tag, network_names in TARGET_NETWORKS.items():
        print(f"\n{tag} networks:")
        tag_has_rules = False
        
        for network_name in network_names:
            network_name_upper = network_name.upper()
            if network_name_upper in network_lookup:
                network = network_lookup[network_name_upper]
                network_id = network['id']
                print(f"\n  Found: {network_name} (ID: {network_id})")
                
                # Download firewall rules
                rules = download_firewall_rules(network_id, network_name)
                
                if rules and len(rules) > 0:
                    # Store in database
                    if store_rules_in_database(conn, network_id, network_name, rules, tag):
                        tag_has_rules = True
                        
                        # Save to JSON file
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
                        print(f"  📄 Saved to: {filename}")
                        
                        # Only need one example per tag
                        if tag_has_rules:
                            rules_downloaded[tag] = network_name
                            break
                
                # Rate limit
                time.sleep(1)
            else:
                print(f"  ❌ Not found: {network_name}")
    
    # Summary
    print("\n=== Summary ===")
    cursor = conn.cursor()
    for tag in TARGET_NETWORKS.keys():
        cursor.execute("""
            SELECT COUNT(*) 
            FROM firewall_rules 
            WHERE template_source = %s
        """, (tag,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"✅ {tag}: {count} rules stored (from {rules_downloaded.get(tag, 'unknown')})")
        else:
            print(f"❌ {tag}: No rules found")
    
    # Update network IDs in meraki_inventory
    print("\n=== Updating Network IDs in Database ===")
    cursor = conn.cursor()
    update_count = 0
    
    for network in all_networks:
        cursor.execute("""
            UPDATE meraki_inventory 
            SET network_id = %s 
            WHERE network_name = %s 
            AND (network_id IS NULL OR network_id = '')
        """, (network['id'], network['name']))
        update_count += cursor.rowcount
    
    conn.commit()
    print(f"✅ Updated {update_count} network IDs in meraki_inventory table")
    
    cursor.close()
    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()