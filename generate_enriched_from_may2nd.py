#!/usr/bin/env python3
"""
Generate Enriched JSON from May 2nd Raw Notes
Uses May 2nd raw notes as source with current DSR circuit matching
Excludes sites with circuit changes between May 2nd and today
"""

import os
import sys
import json
import re
import psycopg2
from datetime import datetime
from fuzzywuzzy import fuzz

# Add path for database utilities
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection

# Configuration
MAY_2ND_JSON = "/var/www/html/meraki-data/mx_inventory_live_20250502_033555.json"
CHANGED_SITES_FILE = "/tmp/sites_with_circuit_changes.txt"
OUTPUT_FILE = "/tmp/enriched_from_may2nd.json"
EXCLUDE_TAGS = {"hub", "lab", "voice", "hug"}

def load_changed_sites():
    """Load list of sites with circuit changes to exclude"""
    changed_sites = set()
    if os.path.exists(CHANGED_SITES_FILE):
        with open(CHANGED_SITES_FILE, 'r') as f:
            lines = f.readlines()
        for line in lines[4:]:  # Skip header lines
            site = line.strip()
            if site:
                changed_sites.add(site)
    return changed_sites

def get_current_device_tags(network_name):
    """Get current device tags from database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT device_tags
            FROM meraki_inventory 
            WHERE network_name = %s 
            AND device_model LIKE %s
            LIMIT 1
        """, (network_name, 'MX%'))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0]:
            return result[0]  # device_tags is stored as array
        return []
    except Exception as e:
        print(f"   ⚠️  Error getting tags for {network_name}: {e}")
        return []

def should_exclude_site(network_name):
    """Check if site should be excluded based on database tags"""
    # Get current tags from database
    device_tags = get_current_device_tags(network_name)
    
    # Check for excluded tags (same logic as nightly script)
    if device_tags and any(tag.lower() in ['hub', 'lab', 'voice'] for tag in device_tags):
        return True
        
    return False

def get_current_wan_ips(network_name):
    """Get current WAN IP assignments from database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT wan1_ip, wan2_ip 
            FROM meraki_inventory 
            WHERE network_name = %s 
            AND device_model LIKE %s
            LIMIT 1
        """, (network_name, 'MX%'))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and len(result) >= 2:
            return result[0] or "", result[1] or ""
        return "", ""
    except Exception as e:
        print(f"   ⚠️  Database error for {network_name}: {e}")
        return "", ""

def get_current_arin_providers(network_name):
    """Get current ARIN provider data from database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT wan1_arin_provider, wan2_arin_provider 
            FROM meraki_inventory 
            WHERE network_name = %s 
            AND device_model LIKE %s
            LIMIT 1
        """, (network_name, 'MX%'))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and len(result) >= 2:
            return result[0] or "", result[1] or ""
        return "", ""
    except Exception as e:
        print(f"   ⚠️  ARIN database error for {network_name}: {e}")
        return "", ""

def get_dsr_circuits_for_site(network_name):
    """Get current enabled DSR circuits for a site"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                provider_name,
                details_ordered_service_speed,
                circuit_purpose,
                ip_address_start
            FROM circuits
            WHERE site_name = %s
            AND status = 'Enabled'
            ORDER BY circuit_purpose
        """, (network_name,))
        
        circuits = []
        for row in cursor.fetchall():
            circuits.append({
                'provider': row[0],
                'speed': row[1], 
                'purpose': row[2],
                'ip': row[3]
            })
        
        cursor.close()
        conn.close()
        
        return circuits
    except Exception as e:
        print(f"   ⚠️  DSR circuit error for {network_name}: {e}")
        return []

def parse_raw_notes(raw_notes):
    """
    Parse raw notes using SEQUENTIAL logic:
    - First WAN entry = WAN1 (regardless of label)  
    - Second WAN entry = WAN2 (regardless of label)
    """
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    
    # Find all WAN entries (WAN1, WAN 1, WAN2, WAN 2, etc.)
    wan_pattern = re.compile(r'(?:WAN1|WAN\s*1|WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)
    wan_entries = re.split(wan_pattern, raw_notes)[1:]  # Skip first empty part
    
    speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
    
    def extract_provider_and_speed(segment):
        """Extract provider name and speed from text segment"""
        match = speed_pattern.search(segment)
        if match:
            up_speed = float(match.group(1))
            up_unit = match.group(2).upper()
            down_speed = float(match.group(3))
            down_unit = match.group(4).upper()
            
            # Convert G to M
            if up_unit in ['G', 'GB']:
                up_speed *= 1000
                up_unit = 'M'
            elif up_unit in ['M', 'MB']:
                up_unit = 'M'
                
            if down_unit in ['G', 'GB']:
                down_speed *= 1000
                down_unit = 'M'
            elif down_unit in ['M', 'MB']:
                down_unit = 'M'
            
            speed_str = f"{up_speed:.1f}{up_unit} x {down_speed:.1f}{down_unit}"
            provider_name = segment[:match.start()].strip()
            
            # Clean provider name - remove DSR prefix and clean special chars
            provider_name = re.sub(r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|--)\s+', '', provider_name, flags=re.IGNORECASE).strip()
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            
            return provider_name, speed_str
        else:
            # No speed found, entire segment is provider
            provider_name = re.sub(r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|--)\s+', '', segment, flags=re.IGNORECASE).strip()
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, ""
    
    # Extract WAN1 (first entry) and WAN2 (second entry)
    wan1_provider, wan1_speed = "", ""
    wan2_provider, wan2_speed = "", ""
    
    if len(wan_entries) >= 1:
        wan1_provider, wan1_speed = extract_provider_and_speed(wan_entries[0])
    
    if len(wan_entries) >= 2:
        wan2_provider, wan2_speed = extract_provider_and_speed(wan_entries[1])
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

def normalize_provider(provider):
    """Normalize provider names"""
    if not provider or str(provider).lower() in ['nan', 'null', '', 'unknown']:
        return ""
    
    provider_str = str(provider).strip()
    if not provider_str:
        return ""
    
    # Remove common prefixes and suffixes
    provider_clean = re.sub(
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workplace)\s*',
        '', provider_str, flags=re.IGNORECASE
    ).strip()
    
    provider_lower = provider_clean.lower()
    
    # Special provider detection
    if provider_lower.startswith('digi'):
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('spacex') or 'spacex' in provider_lower:
        return "Starlink"  # SpaceX Services, Inc. = Starlink
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm', 'vzg')):
        return "VZW Cell"
    
    return provider_clean

def match_dsr_circuit_by_ip(wan_ip, dsr_circuits):
    """Match DSR circuit by IP address (highest priority)"""
    if not wan_ip or not dsr_circuits:
        return None
    
    for circuit in dsr_circuits:
        if circuit['ip'] and str(circuit['ip']).strip() == str(wan_ip).strip():
            return circuit
    
    return None

def match_dsr_circuit_by_provider(provider_label, dsr_circuits):
    """Match DSR circuit by provider name (second priority)"""
    if not provider_label or not dsr_circuits:
        return None
    
    normalized_label = normalize_provider(provider_label).lower()
    if not normalized_label:
        return None
    
    for circuit in dsr_circuits:
        if circuit['provider']:
            normalized_dsr = normalize_provider(circuit['provider']).lower()
            score = fuzz.ratio(normalized_label, normalized_dsr)
            if score > 60:  # 60% threshold for matching
                return circuit
    
    return None

def reformat_speed(speed, provider):
    """Reformat speed with special cases"""
    provider_lower = str(provider).lower()
    
    # Cell providers always get "Cell" speed (even if speed is empty)
    if any(term in provider_lower for term in ['vzw cell', 'verizon cell', 'digi', 'inseego', 'vzw', 'vzg']):
        return "Cell"
    
    # Starlink always gets "Satellite" speed  
    if 'starlink' in provider_lower:
        return "Satellite"
    
    # If no speed provided, return empty
    if not speed:
        return ""
    
    # Standard speed format
    if re.match(r'^\d+(?:\.\d+)?[MG]?\s*x\s*\d+(?:\.\d+)?[MG]?$', str(speed), re.IGNORECASE):
        return speed
    
    return speed

def process_site(site_data, changed_sites):
    """Process a single site using May 2nd raw notes with current DSR matching"""
    network_name = site_data.get("network_name", "").strip()
    
    # Skip if network name is empty
    if not network_name:
        return None
    
    # Skip if site has circuit changes
    if network_name in changed_sites:
        print(f"⏭️  {network_name}: Skipping - has circuit changes since May 2nd")
        return None
    
    # Skip if excluded tags (check database tags)
    if should_exclude_site(network_name):
        print(f"⏭️  {network_name}: Skipping - excluded tag")
        return None
    
    print(f"🔄 Processing {network_name}")
    
    # Parse May 2nd raw notes
    raw_notes = site_data.get("raw_notes", "")
    wan1_provider_raw, wan1_speed_raw, wan2_provider_raw, wan2_speed_raw = parse_raw_notes(raw_notes)
    
    # Get current WAN IP assignments and ARIN data from database
    wan1_ip, wan2_ip = get_current_wan_ips(network_name)
    
    # Get current ARIN provider data
    wan1_arin, wan2_arin = get_current_arin_providers(network_name)
    
    # Get current DSR circuits
    dsr_circuits = get_dsr_circuits_for_site(network_name)
    
    # Match WAN1 to DSR circuits
    wan1_dsr = None
    if wan1_ip:
        wan1_dsr = match_dsr_circuit_by_ip(wan1_ip, dsr_circuits)
    if not wan1_dsr and wan1_provider_raw:
        wan1_dsr = match_dsr_circuit_by_provider(wan1_provider_raw, dsr_circuits)
    
    # Match WAN2 to DSR circuits (exclude already matched circuit)
    wan2_dsr = None
    remaining_circuits = [c for c in dsr_circuits if c != wan1_dsr] if wan1_dsr else dsr_circuits
    if wan2_ip:
        wan2_dsr = match_dsr_circuit_by_ip(wan2_ip, remaining_circuits)
    if not wan2_dsr and wan2_provider_raw:
        wan2_dsr = match_dsr_circuit_by_provider(wan2_provider_raw, remaining_circuits)
    
    # Determine final providers with correct priority: DSR > ARIN > Notes
    def is_valid_arin_provider(arin_provider):
        """Check if ARIN provider data is useful (not private IP, etc.)"""
        if not arin_provider:
            return False
        arin_lower = arin_provider.lower()
        # Exclude non-useful ARIN responses
        if any(term in arin_lower for term in ['private ip', 'unknown', 'unallocated', 'reserved']):
            return False
        return True
    
    if wan1_dsr:
        # Priority 1: DSR circuit match
        wan1_provider_final = wan1_dsr['provider']  # Use DSR name exactly
        wan1_speed_final = wan1_dsr['speed']
        wan1_confirmed = True
        wan1_role = wan1_dsr['purpose']
    elif is_valid_arin_provider(wan1_arin):
        # Priority 2: ARIN provider data (only if useful)
        wan1_provider_final = normalize_provider(wan1_arin)
        wan1_speed_final = reformat_speed("", wan1_provider_final)  # ARIN providers get standard speeds (Cell/Satellite)
        wan1_confirmed = False
        wan1_role = "Primary"
    else:
        # Priority 3: Parsed notes (includes when ARIN is "Private IP")
        wan1_provider_final = normalize_provider(wan1_provider_raw)
        wan1_speed_final = reformat_speed(wan1_speed_raw, wan1_provider_final)
        wan1_confirmed = False
        wan1_role = "Primary"
    
    if wan2_dsr:
        # Priority 1: DSR circuit match
        wan2_provider_final = wan2_dsr['provider']  # Use DSR name exactly
        wan2_speed_final = wan2_dsr['speed']
        wan2_confirmed = True
        wan2_role = wan2_dsr['purpose']
    elif is_valid_arin_provider(wan2_arin):
        # Priority 2: ARIN provider data (only if useful)
        wan2_provider_final = normalize_provider(wan2_arin)
        wan2_speed_final = reformat_speed("", wan2_provider_final)  # ARIN providers get standard speeds (Cell/Satellite)
        wan2_confirmed = False
        wan2_role = "Secondary"
    else:
        # Priority 3: Parsed notes (includes when ARIN is "Private IP")
        wan2_provider_final = normalize_provider(wan2_provider_raw)
        wan2_speed_final = reformat_speed(wan2_speed_raw, wan2_provider_final)
        wan2_confirmed = False
        wan2_role = "Secondary"
    
    # Build enriched site data  
    enriched_site = {
        "network_name": network_name,
        "device_tags": site_data.get("network_tags", []),
        "wan1": {
            "provider": wan1_provider_final,
            "speed": wan1_speed_final,
            "monthly_cost": "$0.00",
            "circuit_role": wan1_role,
            "confirmed": wan1_confirmed
        },
        "wan2": {
            "provider": wan2_provider_final,
            "speed": wan2_speed_final,
            "monthly_cost": "$0.00", 
            "circuit_role": wan2_role,
            "confirmed": wan2_confirmed
        },
        "source": "May 2nd raw notes + current DSR matching",
        "processed_at": datetime.now().isoformat()
    }
    
    # Log the processing
    dsr_info = f"{len(dsr_circuits)} DSR circuits"
    if wan1_dsr:
        dsr_info += f", WAN1→{wan1_dsr['provider']} (IP match)" if wan1_ip == wan1_dsr.get('ip') else f", WAN1→{wan1_dsr['provider']} (provider match)"
    if wan2_dsr:
        dsr_info += f", WAN2→{wan2_dsr['provider']} (IP match)" if wan2_ip == wan2_dsr.get('ip') else f", WAN2→{wan2_dsr['provider']} (provider match)"
    
    print(f"   ✅ {network_name}: WAN1={wan1_provider_final}, WAN2={wan2_provider_final} ({dsr_info})")
    
    return enriched_site

def main():
    """Main processing function"""
    print(f"🔍 Loading May 2nd raw notes from: {MAY_2ND_JSON}")
    
    # Load May 2nd data
    if not os.path.exists(MAY_2ND_JSON):
        print(f"❌ May 2nd JSON file not found: {MAY_2ND_JSON}")
        return
    
    with open(MAY_2ND_JSON, 'r') as f:
        may_data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(may_data, dict) and 'devices' in may_data:
        devices = may_data['devices']
    elif isinstance(may_data, list):
        devices = may_data
    else:
        print(f"❌ Unexpected JSON structure in {MAY_2ND_JSON}")
        return
    
    print(f"📊 Loaded {len(devices)} devices from May 2nd")
    
    # Load changed sites to exclude
    changed_sites = load_changed_sites()
    print(f"🚫 Excluding {len(changed_sites)} sites with circuit changes")
    
    # Process all sites
    enriched_output = []
    processed = 0
    skipped = 0
    
    for device in devices:
        result = process_site(device, changed_sites)
        if result:
            enriched_output.append(result)
            processed += 1
        else:
            skipped += 1
    
    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_output, f, indent=2)
    
    print(f"\n📋 SUMMARY:")
    print(f"   Total devices in May 2nd data: {len(devices)}")
    print(f"   Sites processed: {processed}")
    print(f"   Sites skipped: {skipped}")
    print(f"   Output written to: {OUTPUT_FILE}")
    print(f"\n✅ Enriched JSON generated successfully!")

if __name__ == "__main__":
    main()