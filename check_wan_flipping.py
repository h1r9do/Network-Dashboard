#!/usr/bin/env python3
"""
Check for WAN1/WAN2 flipping in the database
Identifies sites where Primary circuit is on WAN2 and Secondary on WAN1
"""

import psycopg2
import psycopg2.extras
from config import Config
import re
from datetime import datetime

def normalize_provider(provider):
    """Normalize provider name for comparison"""
    if not provider:
        return ""
    
    provider = provider.lower()
    
    # Common mappings
    mappings = {
        'at&t': ['att', 'at&t enterprises', 'at & t'],
        'verizon': ['vzw', 'verizon business', 'vz'],
        'comcast': ['xfinity', 'comcast cable'],
        'centurylink': ['embarq', 'qwest', 'lumen'],
        'cox': ['cox business', 'cox communications'],
        'charter': ['spectrum'],
        'brightspeed': ['level 3']
    }
    
    # Check if provider contains any of these key terms
    for key, variants in mappings.items():
        if key in provider:
            return key
        for variant in variants:
            if variant in provider:
                return key
    
    # Return first word if no mapping found
    return provider.split()[0] if provider else ""

def providers_match(provider1, provider2):
    """Check if two providers match"""
    if not provider1 or not provider2:
        return False
    
    norm1 = normalize_provider(provider1)
    norm2 = normalize_provider(provider2)
    
    return norm1 == norm2

# Parse database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
if match:
    user, password, host, port, database = match.groups()
    
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== WAN Flipping Detection Report ===")
    print(f"Generated: {datetime.now()}")
    print()
    
    # Query to find potential flipped sites
    cursor.execute("""
        SELECT 
            e.network_name,
            e.wan1_provider as enriched_wan1_provider,
            e.wan2_provider as enriched_wan2_provider,
            e.wan1_circuit_role,
            e.wan2_circuit_role,
            m.wan1_ip,
            m.wan2_ip,
            m.wan1_arin_provider,
            m.wan2_arin_provider,
            c_primary.provider_name as dsr_primary_provider,
            c_primary.ip_address_start as dsr_primary_ip,
            c_secondary.provider_name as dsr_secondary_provider,
            c_secondary.ip_address_start as dsr_secondary_ip
        FROM enriched_circuits e
        JOIN meraki_inventory m ON e.network_name = m.network_name
        LEFT JOIN circuits c_primary ON e.network_name = c_primary.site_name 
            AND c_primary.circuit_purpose = 'Primary' 
            AND c_primary.status = 'Enabled'
        LEFT JOIN circuits c_secondary ON e.network_name = c_secondary.site_name 
            AND c_secondary.circuit_purpose = 'Secondary' 
            AND c_secondary.status = 'Enabled'
        WHERE m.device_model LIKE 'MX%'
        AND c_primary.provider_name IS NOT NULL
        AND c_secondary.provider_name IS NOT NULL
        ORDER BY e.network_name
    """)
    
    sites = cursor.fetchall()
    
    print(f"Analyzing {len(sites)} sites with both Primary and Secondary circuits...")
    print()
    
    flipped_sites = []
    suspicious_sites = []
    
    for site in sites:
        flip_indicators = 0
        reasons = []
        
        # Check 1: IP address mismatch
        if (site['dsr_primary_ip'] and site['wan2_ip'] and 
            site['dsr_primary_ip'] == site['wan2_ip']):
            flip_indicators += 2
            reasons.append("Primary DSR IP matches WAN2")
            
        if (site['dsr_secondary_ip'] and site['wan1_ip'] and 
            site['dsr_secondary_ip'] == site['wan1_ip']):
            flip_indicators += 2
            reasons.append("Secondary DSR IP matches WAN1")
        
        # Check 2: ARIN provider mismatch
        if (site['wan1_arin_provider'] and site['dsr_secondary_provider'] and
            providers_match(site['wan1_arin_provider'], site['dsr_secondary_provider'])):
            flip_indicators += 1
            reasons.append("WAN1 ARIN matches Secondary DSR provider")
            
        if (site['wan2_arin_provider'] and site['dsr_primary_provider'] and
            providers_match(site['wan2_arin_provider'], site['dsr_primary_provider'])):
            flip_indicators += 1
            reasons.append("WAN2 ARIN matches Primary DSR provider")
        
        # Check 3: Role assignment mismatch
        if site['wan1_circuit_role'] == 'Secondary' and site['wan2_circuit_role'] == 'Primary':
            flip_indicators += 1
            reasons.append("Roles already show as flipped")
        
        # Categorize findings
        if flip_indicators >= 3:
            flipped_sites.append({
                'site': site['network_name'],
                'score': flip_indicators,
                'reasons': reasons,
                'data': site
            })
        elif flip_indicators >= 1:
            suspicious_sites.append({
                'site': site['network_name'],
                'score': flip_indicators,
                'reasons': reasons,
                'data': site
            })
    
    # Report findings
    print(f"=== CONFIRMED FLIPPED SITES ({len(flipped_sites)}) ===")
    if flipped_sites:
        for item in sorted(flipped_sites, key=lambda x: x['score'], reverse=True):
            site = item['data']
            print(f"\nSite: {item['site']} (Confidence Score: {item['score']})")
            print(f"  Reasons: {', '.join(item['reasons'])}")
            print(f"  Current Assignment:")
            print(f"    WAN1: {site['enriched_wan1_provider']} ({site['wan1_circuit_role']})")
            print(f"    WAN2: {site['enriched_wan2_provider']} ({site['wan2_circuit_role']})")
            print(f"  DSR Circuits:")
            print(f"    Primary: {site['dsr_primary_provider']} - IP: {site['dsr_primary_ip']}")
            print(f"    Secondary: {site['dsr_secondary_provider']} - IP: {site['dsr_secondary_ip']}")
            print(f"  Meraki IPs:")
            print(f"    WAN1: {site['wan1_ip']} - ARIN: {site['wan1_arin_provider']}")
            print(f"    WAN2: {site['wan2_ip']} - ARIN: {site['wan2_arin_provider']}")
    else:
        print("  No confirmed flipped sites found")
    
    print(f"\n=== POSSIBLY FLIPPED SITES ({len(suspicious_sites)}) ===")
    if suspicious_sites:
        for item in sorted(suspicious_sites, key=lambda x: x['score'], reverse=True)[:10]:
            site = item['data']
            print(f"\nSite: {item['site']} (Confidence Score: {item['score']})")
            print(f"  Reasons: {', '.join(item['reasons'])}")
            print(f"  Current WAN1: {site['enriched_wan1_provider']} - DSR Secondary: {site['dsr_secondary_provider']}")
            print(f"  Current WAN2: {site['enriched_wan2_provider']} - DSR Primary: {site['dsr_primary_provider']}")
    else:
        print("  No suspicious sites found")
    
    # Summary statistics
    print(f"\n=== SUMMARY ===")
    print(f"Total sites analyzed: {len(sites)}")
    print(f"Confirmed flipped: {len(flipped_sites)}")
    print(f"Possibly flipped: {len(suspicious_sites)}")
    print(f"Correctly assigned: {len(sites) - len(flipped_sites) - len(suspicious_sites)}")
    
    # Export detailed findings
    if flipped_sites or suspicious_sites:
        import csv
        filename = f'/usr/local/bin/wan_flip_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Site Name', 'Confidence Score', 'Status', 'Reasons',
                'WAN1 Provider', 'WAN1 Role', 'WAN1 IP', 'WAN1 ARIN',
                'WAN2 Provider', 'WAN2 Role', 'WAN2 IP', 'WAN2 ARIN',
                'DSR Primary Provider', 'DSR Primary IP',
                'DSR Secondary Provider', 'DSR Secondary IP'
            ])
            
            for item in flipped_sites:
                site = item['data']
                writer.writerow([
                    item['site'], item['score'], 'FLIPPED', '; '.join(item['reasons']),
                    site['enriched_wan1_provider'], site['wan1_circuit_role'], 
                    site['wan1_ip'], site['wan1_arin_provider'],
                    site['enriched_wan2_provider'], site['wan2_circuit_role'],
                    site['wan2_ip'], site['wan2_arin_provider'],
                    site['dsr_primary_provider'], site['dsr_primary_ip'],
                    site['dsr_secondary_provider'], site['dsr_secondary_ip']
                ])
            
            for item in suspicious_sites:
                site = item['data']
                writer.writerow([
                    item['site'], item['score'], 'SUSPICIOUS', '; '.join(item['reasons']),
                    site['enriched_wan1_provider'], site['wan1_circuit_role'], 
                    site['wan1_ip'], site['wan1_arin_provider'],
                    site['enriched_wan2_provider'], site['wan2_circuit_role'],
                    site['wan2_ip'], site['wan2_arin_provider'],
                    site['dsr_primary_provider'], site['dsr_primary_ip'],
                    site['dsr_secondary_provider'], site['dsr_secondary_ip']
                ])
        
        print(f"\nDetailed report saved to: {filename}")
    
    conn.close()