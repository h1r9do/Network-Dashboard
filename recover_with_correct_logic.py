#!/usr/bin/env python3
"""
Complete recovery script implementing the exact logic from meraki_mx.py + nightly_enriched.py
Uses June 24th historical data as source of truth
"""

import json
import subprocess
import sys
import re
from datetime import datetime
from fuzzywuzzy import fuzz
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection, get_provider_for_ip, compare_providers, KNOWN_IPS
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Complete provider mapping from original nightly_enriched.py
PROVIDER_MAPPING = {
    "spectrum": "Charter Communications",
    "cox business/boi": "Cox Communications",
    "cox business boi | extended cable |": "Cox Communications",
    "cox business boi extended cable": "Cox Communications",
    "cox business": "Cox Communications",
    "comcast workplace": "Comcast",
    "comcast workplace cable": "Comcast",
    "agg comcast": "Comcast",
    "comcastagg clink dsl": "CenturyLink",
    "comcastagg comcast": "Comcast",
    "verizon cell": "Verizon",
    "cell": "Verizon",
    "verizon business": "Verizon",
    "accelerated": "",
    "digi": "Digi",
    "digi cellular": "Digi",
    "starlink": "Starlink",
    "inseego": "Inseego",
    "charter communications": "Charter Communications",
    "at&t broadband ii": "AT&T",
    "at&t abf": "AT&T",
    "at&t adi": "AT&T",
    "not dsr at&t | at&t adi |": "AT&T",
    "at&t": "AT&T",
    "cox communications": "Cox Communications",
    "comcast": "Comcast",
    "verizon": "Verizon",
    "yelcot telephone company": "Yelcot Communications",
    "yelcot communications": "Yelcot Communications",
    "ritter communications": "Ritter Communications",
    "- ritter comm": "Ritter Communications",
    "conway corporation": "Conway Corporation",
    "conway extended cable": "Conway Corporation",
    "dsr conway extended cable": "Conway Corporation",
    "altice": "Optimum",
    "altice west": "Optimum",
    "optimum": "Optimum",
    "frontier fios": "Frontier",
    "frontier metrofiber": "Frontier",
    "allo communications": "Allo Communications",
    "segra": "Segra",
    "mountain west technologies": "Mountain West Technologies",
    "c spire": "C Spire",
    "brightspeed": "Brightspeed",
    "century link": "CenturyLink",
    "centurylink": "CenturyLink",
    "clink fiber": "CenturyLink",
    "eb2-frontier fiber": "Frontier",
    "one ring networks": "One Ring Networks",
    "gtt ethernet": "GTT",
    "vexus": "Vexus",
    "sparklight": "Sparklight",
    "vista broadband": "Vista Broadband",
    "metronet": "Metronet",
    "rise broadband": "Rise Broadband",
    "lumos networks": "Lumos Networks",
    "point broadband": "Point Broadband",
    "gvtc communications": "GVTC Communications",
    "harris broadband": "Harris Broadband",
    "unite private networks": "Unite Private Networks",
    "pocketinet communications": "Pocketinet Communications",
    "eb2-ziply fiber": "Ziply Fiber",
    "astound": "Astound",
    "consolidated communications": "Consolidated Communications",
    "etheric networks": "Etheric Networks",
    "saddleback communications": "Saddleback Communications",
    "orbitel communications": "Orbitel Communications",
    "eb2-cableone cable": "Cable One",
    "cable one": "Cable One",
    "cableone": "Cable One",
    "transworld": "TransWorld",
    "mediacom/boi": "Mediacom",
    "mediacom": "Mediacom",
    "login": "Login",
    "livcom": "Livcom",
    "tds cable": "TDS Cable",
    "first digital": "Digi",
    "spanish fork community network": "Spanish Fork Community Network",
    "centracom": "Centracom",
    "eb2-lumen dsl": "Lumen",
    "lumen dsl": "Lumen",
    "eb2-centurylink dsl": "CenturyLink",
    "centurylink/qwest": "CenturyLink",
    "centurylink fiber plus": "CenturyLink",
    "lightpath": "Lightpath",
    "localtel": "LocalTel",
    "infowest inc": "Infowest",
    "eb2-windstream fiber": "Windstream",
    "gtt/esa2 adsl": "GTT",
    "zerooutages": "ZeroOutages",
    "fuse internet access": "Fuse Internet Access",
    "windstream communications llc": "Windstream",
    "frontier communications": "Frontier",
    "glenwood springs community broadband network": "Glenwood Springs Community Broadband Network",
    "unknown": "",
    "uniti fiber": "Uniti Fiber",
    "wideopenwest": "WideOpenWest",
    "wide open west": "WideOpenWest",
    "level 3": "Lumen",
    "plateau telecommunications": "Plateau Telecommunications",
    "d & p communications": "D&P Communications",
    "vzg": "VZW Cell",
}

def parse_raw_notes_original(raw_notes):
    """EXACT parsing logic from meraki_mx.py"""
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    
    text = re.sub(r'\s+', ' ', raw_notes.strip())
    wan1_pattern = re.compile(r'(?:WAN1|WAN\s*1)\s*:?\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)
    speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
    
    def extract_provider_and_speed(segment):
        """Helper to extract provider name and speed from a text segment."""
        match = speed_pattern.search(segment)
        if match:
            up_speed = float(match.group(1))
            up_unit = match.group(2).upper()
            down_speed = float(match.group(3))
            down_unit = match.group(4).upper()
            
            # Convert G/GB to M
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
            
            # Clean provider name (original logic)
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, speed_str
        else:
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', segment).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, ""
    
    # Text splitting logic from original
    wan1_text = ""
    wan2_text = ""
    parts = re.split(wan1_pattern, text, maxsplit=1)
    if len(parts) > 1:
        after_wan1 = parts[1]
        wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
        wan1_text = wan2_split[0].strip()
        if len(wan2_split) > 1:
            wan2_text = wan2_split[1].strip()
    else:
        parts = re.split(wan2_pattern, text, maxsplit=1)
        if len(parts) > 1:
            wan2_text = parts[1].strip()
        else:
            wan1_text = text.strip()
    
    wan1_provider, wan1_speed = extract_provider_and_speed(wan1_text)
    wan2_provider, wan2_speed = extract_provider_and_speed(wan2_text)
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

def normalize_provider_original(provider, is_dsr=False):
    """EXACT normalization logic from nightly_enriched.py"""
    if not provider or str(provider).lower() in ['nan', 'unknown', '']:
        return ""
    
    # Step 1: Initial cleaning - remove IMEI, serial numbers, etc.
    provider_clean = re.sub(
        r'\s*(?:##.*##|\s*imei.*$|\s*kitp.*$|\s*sn.*$|\s*port.*$|\s*location.*$|\s*in\s+the\s+bay.*$|\s*up\s+front.*$|\s*under\s+.*$|\s*wireless\s+gateway.*$|\s*serial.*$|\s*poe\s+injector.*$|\s*supported\s+through.*$|\s*static\s+ip.*$|\s*subnet\s+mask.*$|\s*gateway\s+ip.*$|\s*service\s+id.*$|\s*circuit\s+id.*$|\s*ip\s+address.*$|\s*5g.*$|\s*currently.*$)',
        '', str(provider), flags=re.IGNORECASE
    ).strip()
    
    # Step 2: Prefix removal
    provider_clean = re.sub(
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workpace)\s*',
        '', provider_clean, flags=re.IGNORECASE
    ).strip()
    
    provider_lower = provider_clean.lower()
    
    # Step 3: Special provider detection (in order)
    if provider_lower.startswith('digi'):
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm')) and not is_dsr:
        return "VZW Cell"
    
    # Step 4: Fuzzy matching against provider mapping
    for key, value in PROVIDER_MAPPING.items():
        if fuzz.ratio(key, provider_lower) > 70:
            return value
    
    return provider_clean

def determine_final_provider_original(notes_provider, arin_provider, comparison, dsr_provider=None, dsr_enabled=False):
    """Apply the original enrichment hierarchy"""
    
    # Step 1: DSR Priority - if we have enabled DSR data, that's highest priority
    if dsr_enabled and dsr_provider and dsr_provider.strip():
        return dsr_provider
    
    # Step 2: Comparison Logic
    if comparison == "No match" and notes_provider:
        # When ARIN doesn't match notes, trust the notes
        return notes_provider  # Already normalized
    elif arin_provider and arin_provider not in ["Unknown", "Private IP"]:
        # Use ARIN when it matches or when no notes
        return arin_provider
    elif notes_provider:
        # Fall back to notes
        return notes_provider  # Already normalized
    else:
        return "Unknown"

def reformat_speed_original(speed, provider):
    """EXACT speed formatting logic from nightly_enriched.py"""
    # Override speed for specific providers - EXACT MATCHING
    if provider in ["Inseego", "VZW Cell", "Digi", ""]:
        return "Cell"
    if provider == "Starlink":
        return "Satellite"
    if not speed or str(speed).lower() in ['cell', 'satellite', 'tbd', 'unknown', 'nan']:
        return str(speed) or "Unknown"
    
    # Format regular speeds with regex
    match = re.match(r'^([\d.]+)\s*(M|G|MB)\s*[xX]\s*([\d.]+)\s*(M|G|MB)$', str(speed), re.IGNORECASE)
    if match:
        download, d_unit, upload, u_unit = match.groups()
        try:
            download = float(download)
            upload = float(upload)
            return f"{download:.1f}{d_unit} x {upload:.1f}{u_unit}"
        except:
            return str(speed)
    return str(speed)

def main():
    logger.info("Starting recovery with correct original logic...")
    
    # Get historical data from June 24
    logger.info("Retrieving historical Meraki data from June 24...")
    cmd = "git -C /var/www/html/meraki-data show 019677c:mx_inventory_live.json"
    json_content = subprocess.check_output(cmd, shell=True).decode()
    historical_data = json.loads(json_content)
    logger.info(f"Found {len(historical_data)} devices in historical data")
    
    # Get enabled circuits from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT site_name, circuit_purpose, provider_name, status
        FROM circuits
        WHERE LOWER(status) = 'enabled'
    """)
    
    enabled_circuits = {}
    for site, purpose, provider, status in cursor.fetchall():
        if site not in enabled_circuits:
            enabled_circuits[site] = {}
        wan = 'wan1' if 'primary' in purpose.lower() else 'wan2'
        enabled_circuits[site][wan] = provider
    
    logger.info(f"Loaded {len(enabled_circuits)} sites with enabled circuits")
    
    # Process each device
    ip_cache = {}
    missing_ips = set()
    updated_count = 0
    
    for device in historical_data:
        network_name = device.get('network_name', '')
        device_serial = device.get('device_serial', '')
        raw_notes = device.get('raw_notes', '')
        
        if not device_serial or not device.get('device_model', '').startswith('MX'):
            continue
        
        # Step 1: Parse the historical notes using ORIGINAL logic
        wan1_label, wan1_speed_label, wan2_label, wan2_speed_label = parse_raw_notes_original(raw_notes)
        
        # Step 2: Normalize providers using ORIGINAL logic
        wan1_normalized = normalize_provider_original(wan1_label, is_dsr=False) if wan1_label else ""
        wan2_normalized = normalize_provider_original(wan2_label, is_dsr=False) if wan2_label else ""
        
        # Get IPs
        wan1_ip = device.get('wan1', {}).get('ip', '')
        wan2_ip = device.get('wan2', {}).get('ip', '')
        
        # Step 3: ARIN lookups
        wan1_arin = get_provider_for_ip(wan1_ip, ip_cache, missing_ips) if wan1_ip else "Unknown"
        wan2_arin = get_provider_for_ip(wan2_ip, ip_cache, missing_ips) if wan2_ip else "Unknown"
        
        # Step 4: Compare
        wan1_comparison = compare_providers(wan1_arin, wan1_normalized) if wan1_normalized else None
        wan2_comparison = compare_providers(wan2_arin, wan2_normalized) if wan2_normalized else None
        
        # Get DSR data
        site_enabled = network_name in enabled_circuits
        wan1_dsr = enabled_circuits.get(network_name, {}).get('wan1', '')
        wan2_dsr = enabled_circuits.get(network_name, {}).get('wan2', '')
        
        # Step 5: Determine final providers using ORIGINAL logic
        wan1_final = determine_final_provider_original(wan1_normalized, wan1_arin, wan1_comparison, wan1_dsr, site_enabled)
        wan2_final = determine_final_provider_original(wan2_normalized, wan2_arin, wan2_comparison, wan2_dsr, site_enabled)
        
        # Use EXACT speed formatting logic from original nightly_enriched.py
        wan1_speed_final = reformat_speed_original(wan1_speed_label, wan1_final)
        wan2_speed_final = reformat_speed_original(wan2_speed_label, wan2_final)
        
        # Update meraki_inventory
        cursor.execute("""
            UPDATE meraki_inventory
            SET device_notes = %s,
                wan1_provider_label = %s,
                wan1_speed_label = %s,
                wan2_provider_label = %s,
                wan2_speed_label = %s,
                wan1_provider_comparison = %s,
                wan2_provider_comparison = %s,
                last_updated = NOW()
            WHERE device_serial = %s
        """, (
            raw_notes,
            wan1_normalized,  # NORMALIZED label, not raw
            wan1_speed_label,
            wan2_normalized,  # NORMALIZED label, not raw
            wan2_speed_label,
            wan1_comparison,
            wan2_comparison,
            device_serial
        ))
        
        # Update enriched_circuits
        if cursor.rowcount > 0:
            cursor.execute("""
                UPDATE enriched_circuits
                SET wan1_provider = %s,
                    wan1_speed = %s,
                    wan2_provider = %s,
                    wan2_speed = %s,
                    last_updated = NOW()
                WHERE network_name = %s
            """, (
                wan1_final,
                wan1_speed_final,
                wan2_final,
                wan2_speed_final,
                network_name
            ))
            
            if cursor.rowcount > 0:
                updated_count += 1
                if updated_count % 50 == 0:
                    logger.info(f"Progress: Updated {updated_count} devices...")
                    
                # Log specific cases for verification
                if network_name == "CAL 17":
                    logger.info(f"CAL 17 Processing:")
                    logger.info(f"  Raw Notes: {raw_notes[:100]}...")
                    logger.info(f"  Step 1 Parse: WAN1='{wan1_label}', WAN2='{wan2_label}'")
                    logger.info(f"  Step 2 Normalize: WAN1='{wan1_normalized}', WAN2='{wan2_normalized}'")
                    logger.info(f"  Step 3 ARIN: WAN1='{wan1_arin}', WAN2='{wan2_arin}'")
                    logger.info(f"  Step 4 Compare: WAN1='{wan1_comparison}', WAN2='{wan2_comparison}'")
                    logger.info(f"  Step 5 Final: WAN1='{wan1_final}', WAN2='{wan2_final}'")
    
    # Update RDAP cache
    for ip, provider in ip_cache.items():
        if provider and provider not in ['Unknown', 'Private IP']:
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
    
    logger.info(f"Recovery complete! Updated {updated_count} devices with ORIGINAL LOGIC")
    logger.info(f"Updated {len(ip_cache)} RDAP cache entries")

if __name__ == "__main__":
    main()