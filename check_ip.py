#!/usr/bin/env python3
"""Command-line tool to check ARIN provider for any IP address"""

import sys
import argparse
import ipaddress
import requests
import json
from datetime import datetime
import time
import re

# Import database config
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import parse_arin_response, KNOWN_IPS, get_db_connection
from psycopg2.extras import execute_values

def is_private_ip(ip):
    """Check if IP is private"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False

def check_rdap_cache(ip):
    """Check if IP is in RDAP cache"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT provider_name, last_queried
        FROM rdap_cache
        WHERE ip_address = %s
    """, (ip,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return result

def update_rdap_cache(ip, provider):
    """Update RDAP cache with new result"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO rdap_cache (ip_address, provider_name)
        VALUES (%s, %s)
        ON CONFLICT (ip_address) DO UPDATE SET
            provider_name = EXCLUDED.provider_name,
            last_queried = NOW()
    """, (ip, provider))
    
    conn.commit()
    cursor.close()
    conn.close()

def lookup_ip(ip_address, force=False, verbose=False):
    """Look up ARIN provider for an IP address"""
    
    # Validate IP
    try:
        ip_obj = ipaddress.ip_address(ip_address)
    except ValueError:
        print(f"Error: '{ip_address}' is not a valid IP address")
        return None
    
    print(f"\nChecking IP: {ip_address}")
    print("-" * 50)
    
    # Check if private
    if ip_obj.is_private:
        print(f"IP Type: Private (RFC1918)")
        print(f"Provider: N/A (Private IP)")
        return "Private IP"
    
    print(f"IP Type: Public")
    
    # Check Verizon Business range
    if ipaddress.IPv4Address("166.80.0.0") <= ip_obj <= ipaddress.IPv4Address("166.80.255.255"):
        print(f"Provider: Verizon Business (Special Range)")
        return "Verizon Business"
    
    # Check known IPs
    if ip_address in KNOWN_IPS:
        provider = KNOWN_IPS[ip_address]
        print(f"Provider: {provider} (Known IP)")
        return provider
    
    # Check cache unless forced
    if not force:
        cached = check_rdap_cache(ip_address)
        if cached:
            provider, last_checked = cached
            print(f"Provider: {provider} (Cached)")
            print(f"Last Checked: {last_checked}")
            return provider
    
    # Perform ARIN RDAP lookup
    print("Performing ARIN RDAP lookup...")
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip_address}"
    
    try:
        response = requests.get(rdap_url, timeout=10)
        response.raise_for_status()
        rdap_data = response.json()
        
        if verbose:
            print(f"\nRaw RDAP Response:")
            print(json.dumps(rdap_data, indent=2))
            print("\n")
        
        # Parse provider
        provider = parse_arin_response(rdap_data)
        
        # Show additional info if verbose
        if verbose and 'entities' in rdap_data:
            print("\nEntities found:")
            for entity in rdap_data['entities']:
                vcard = entity.get('vcardArray', [])
                if vcard and len(vcard) > 1:
                    for prop in vcard[1]:
                        if len(prop) >= 4 and prop[0] == 'fn':
                            kind = 'unknown'
                            for p in vcard[1]:
                                if len(p) >= 4 and p[0] == 'kind':
                                    kind = p[3]
                            print(f"  - {prop[3]} (kind: {kind})")
        
        print(f"\nProvider: {provider} (Fresh Lookup)")
        
        # Update cache
        update_rdap_cache(ip_address, provider)
        print("Cache updated")
        
        return provider
        
    except requests.exceptions.RequestException as e:
        print(f"Error performing RDAP lookup: {e}")
        return "Error"
    except Exception as e:
        print(f"Error parsing response: {e}")
        return "Error"

def check_database_ips(ip_address):
    """Check if this IP exists in the database and show its current provider"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check meraki_inventory
    cursor.execute("""
        SELECT network_name, device_serial, 
               CASE 
                   WHEN wan1_ip = %s THEN 'WAN1'
                   WHEN wan2_ip = %s THEN 'WAN2'
               END as interface,
               CASE 
                   WHEN wan1_ip = %s THEN wan1_arin_provider
                   WHEN wan2_ip = %s THEN wan2_arin_provider
               END as current_provider
        FROM meraki_inventory
        WHERE wan1_ip = %s OR wan2_ip = %s
    """, (ip_address, ip_address, ip_address, ip_address, ip_address, ip_address))
    
    results = cursor.fetchall()
    
    if results:
        print(f"\nFound in database:")
        for network, serial, interface, provider in results:
            print(f"  Network: {network}")
            print(f"  Device: {serial}")
            print(f"  Interface: {interface}")
            print(f"  Current Provider: {provider}")
    
    cursor.close()
    conn.close()
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Check ARIN provider for an IP address')
    parser.add_argument('ip', help='IP address to check')
    parser.add_argument('-f', '--force', action='store_true', help='Force fresh lookup (ignore cache)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output')
    parser.add_argument('-u', '--update', action='store_true', help='Update database if IP is found')
    
    args = parser.parse_args()
    
    # Look up the IP
    provider = lookup_ip(args.ip, force=args.force, verbose=args.verbose)
    
    # Check if in database
    db_results = check_database_ips(args.ip)
    
    # Update database if requested
    if args.update and db_results and provider and provider not in ['Error', 'Private IP']:
        print(f"\nUpdating database with provider: {provider}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for network, serial, interface, current_provider in db_results:
            if current_provider != provider:
                if interface == 'WAN1':
                    cursor.execute("""
                        UPDATE meraki_inventory
                        SET wan1_arin_provider = %s, last_updated = %s
                        WHERE device_serial = %s
                    """, (provider, datetime.now(), serial))
                else:
                    cursor.execute("""
                        UPDATE meraki_inventory
                        SET wan2_arin_provider = %s, last_updated = %s
                        WHERE device_serial = %s
                    """, (provider, datetime.now(), serial))
                
                print(f"  Updated {network} {interface}: {current_provider} → {provider}")
        
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()