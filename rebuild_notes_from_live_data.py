#!/usr/bin/env python3
"""
Rebuild Corrected Notes from Live Meraki Data
Uses fresh live IPs and ARIN data, accommodates flipped circuits
"""

import json
import re
from datetime import datetime

# Configuration
LIVE_DATA_FILE = "/tmp/live_meraki_batch_50.json"
OUTPUT_FILE = "/tmp/corrected_notes_from_live.json"

def normalize_provider(provider):
    """Normalize provider names"""
    if not provider or str(provider).lower() in ['nan', 'null', '', 'unknown']:
        return ""
    
    provider_str = str(provider).strip()
    if not provider_str:
        return ""
    
    # Remove common prefixes and suffixes
    provider_clean = re.sub(
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|--)\s+|',
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

def reformat_speed(speed, provider):
    """Reformat speed with special cases"""
    provider_lower = str(provider).lower()
    
    # Cell providers always get "Cell" speed (even if speed is empty)
    if any(term in provider_lower for term in ['vzw cell', 'verizon cell', 'digi', 'inseego', 'vzw', 'vzg']):
        return "Cell"
    
    # Starlink always gets "Satellite" speed  
    if 'starlink' in provider_lower or 'spacex' in provider_lower:
        return "Satellite"
    
    # If no speed provided, return empty
    if not speed:
        return ""
    
    # Standard speed format
    if re.match(r'^\d+(?:\.\d+)?[MG]?\s*x\s*\d+(?:\.\d+)?[MG]?$', str(speed), re.IGNORECASE):
        return speed
    
    return speed

def is_valid_arin_provider(arin_provider):
    """Check if ARIN provider data is useful (not private IP, etc.)"""
    if not arin_provider:
        return False
    arin_lower = arin_provider.lower()
    # Exclude non-useful ARIN responses
    if any(term in arin_lower for term in ['private ip', 'unknown', 'unallocated', 'reserved', 'private customer', 'no ip']):
        return False
    return True

def determine_final_provider_and_speed(dsr_match, arin_provider):
    """Determine final provider and speed using priority: DSR > ARIN"""
    if dsr_match:
        # Priority 1: DSR circuit match (highest priority)
        return dsr_match['provider'], dsr_match['speed'], True, dsr_match['purpose']
    elif is_valid_arin_provider(arin_provider):
        # Priority 2: ARIN provider data (only if useful)
        normalized_provider = normalize_provider(arin_provider)
        speed = reformat_speed("", normalized_provider)  # ARIN providers get standard speeds (Cell/Satellite)
        return normalized_provider, speed, False, "Primary"  # Default role
    else:
        # No useful data
        return "", "", False, "Primary"

def format_circuit_notes(wan1_data, wan2_data):
    """Format circuit data into Meraki device notes"""
    notes_lines = []
    
    # WAN1 formatting
    if wan1_data.get('provider') or wan1_data.get('speed'):
        notes_lines.append("WAN 1")
        if wan1_data.get('provider'):
            notes_lines.append(wan1_data['provider'])
        if wan1_data.get('speed'):
            notes_lines.append(wan1_data['speed'])
    
    # WAN2 formatting
    if wan2_data.get('provider') or wan2_data.get('speed'):
        notes_lines.append("WAN 2")
        if wan2_data.get('provider'):
            notes_lines.append(wan2_data['provider'])
        if wan2_data.get('speed'):
            notes_lines.append(wan2_data['speed'])
    
    return "\n".join(notes_lines) if notes_lines else ""

def process_site(site_data):
    """Process a single site using live data"""
    network_name = site_data.get("network_name", "").strip()
    
    if not network_name:
        return None
    
    print(f"🔄 Processing {network_name}")
    
    # Get WAN data
    wan1_data = site_data.get('wan1', {})
    wan2_data = site_data.get('wan2', {})
    
    # Extract data for each WAN
    wan1_dsr = wan1_data.get('dsr_match')
    wan1_arin = wan1_data.get('arin_provider', '')
    wan2_dsr = wan2_data.get('dsr_match')
    wan2_arin = wan2_data.get('arin_provider', '')
    
    # Determine final providers and speeds with correct priority: DSR > ARIN
    wan1_provider_final, wan1_speed_final, wan1_confirmed, wan1_role = determine_final_provider_and_speed(wan1_dsr, wan1_arin)
    wan2_provider_final, wan2_speed_final, wan2_confirmed, wan2_role = determine_final_provider_and_speed(wan2_dsr, wan2_arin)
    
    # Set default roles if not from DSR
    if not wan1_confirmed:
        wan1_role = "Primary"
    if not wan2_confirmed:
        wan2_role = "Secondary"
    
    # Build enriched site data
    enriched_site = {
        "network_name": network_name,
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
        "source": "Live Meraki API + fresh ARIN data + DSR matching",
        "processed_at": datetime.now().isoformat()
    }
    
    # Format corrected notes
    corrected_notes = format_circuit_notes(enriched_site['wan1'], enriched_site['wan2'])
    enriched_site['corrected_notes'] = corrected_notes
    
    # Log the processing
    dsr_circuits = site_data.get('dsr_circuits', [])
    dsr_info = f"{len(dsr_circuits)} DSR circuits"
    if wan1_dsr:
        match_type = "IP match" if wan1_data.get('ip') == wan1_dsr.get('ip') else "match"
        dsr_info += f", WAN1→{wan1_dsr['provider']} ({match_type})"
    if wan2_dsr:
        match_type = "IP match" if wan2_data.get('ip') == wan2_dsr.get('ip') else "match"
        dsr_info += f", WAN2→{wan2_dsr['provider']} ({match_type})"
    
    # Check for flipped circuits
    flipped = ""
    if wan1_dsr and wan2_dsr:
        if wan1_dsr.get('purpose') == 'Secondary' and wan2_dsr.get('purpose') == 'Primary':
            flipped = " [FLIPPED CIRCUITS!]"
    
    print(f"   ✅ {network_name}: WAN1={wan1_provider_final}, WAN2={wan2_provider_final} ({dsr_info}){flipped}")
    
    return enriched_site

def main():
    """Main processing function"""
    print("🔄 Rebuilding Corrected Notes from Live Meraki Data")
    print("=" * 70)
    
    # Load live data
    if not os.path.exists(LIVE_DATA_FILE):
        print(f"❌ Live data file not found: {LIVE_DATA_FILE}")
        return
    
    with open(LIVE_DATA_FILE, 'r') as f:
        live_data = json.load(f)
    
    print(f"📊 Loaded {len(live_data)} sites from live data")
    
    # Process all sites
    corrected_notes_data = []
    
    for site_data in live_data:
        result = process_site(site_data)
        if result:
            corrected_notes_data.append(result)
    
    # Write output file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(corrected_notes_data, f, indent=2)
    
    # Analyze results
    print(f"\n📋 SUMMARY:")
    print(f"   Total sites processed: {len(corrected_notes_data)}")
    print(f"   Output written to: {OUTPUT_FILE}")
    
    # Count specific provider types
    starlink_sites = []
    cell_sites = []
    flipped_sites = []
    
    for entry in corrected_notes_data:
        notes = entry.get('corrected_notes', '')
        if 'starlink' in notes.lower():
            starlink_sites.append(entry['network_name'])
        if 'cell' in notes.lower():
            cell_sites.append(entry['network_name'])
        
        # Check for flipped circuits
        wan1_dsr = entry.get('wan1', {}).get('confirmed', False)
        wan2_dsr = entry.get('wan2', {}).get('confirmed', False)
        if wan1_dsr and wan2_dsr:
            wan1_role = entry.get('wan1', {}).get('circuit_role', '')
            wan2_role = entry.get('wan2', {}).get('circuit_role', '')
            if wan1_role == 'Secondary' and wan2_role == 'Primary':
                flipped_sites.append(entry['network_name'])
    
    print(f"\n📊 Provider Statistics:")
    print(f"   Starlink sites: {len(starlink_sites)}")
    if starlink_sites:
        print(f"   -> {', '.join(starlink_sites)}")
    print(f"   Cell provider sites: {len(cell_sites)}")
    print(f"   Sites with flipped circuits: {len(flipped_sites)}")
    if flipped_sites:
        print(f"   -> {', '.join(flipped_sites)}")
    
    print(f"\n✅ Corrected notes from live data generated successfully!")

if __name__ == "__main__":
    import os
    main()