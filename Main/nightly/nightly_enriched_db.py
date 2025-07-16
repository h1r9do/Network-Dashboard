#!/usr/bin/env python3
"""
COMPLETE Nightly Enriched Database Script with All Features:
- Preserves DSR data when ARIN providers match
- Preserves non-DSR circuits when nothing has changed
- Handles WAN1/WAN2 flipping detection
- Syncs confirmed enriched data back to circuits table for non-DSR circuits
- Only updates when actual changes are detected
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values, execute_batch
from datetime import datetime, timezone
import re
from thefuzz import fuzz

# Add current directory to path for imports
# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nightly-enriched-db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Provider mapping from legacy nightly_enriched.py
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
    "accelerated": "",  # Clean off
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
    "vzg": "VZW Cell",
}

def get_db_connection():
    """Get database connection using config"""
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

def normalize_provider_for_arin_match(provider):
    """Normalize provider for ARIN matching purposes"""
    if not provider:
        return ""
    
    provider = provider.lower()
    
    # Common mappings for ARIN matching
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

def providers_match_for_sync(dsr_provider, arin_provider):
    """Check if DSR and ARIN providers match well enough to sync DSR data"""
    if not dsr_provider or not arin_provider:
        return False
    
    dsr_norm = normalize_provider_for_arin_match(dsr_provider)
    arin_norm = normalize_provider_for_arin_match(arin_provider)
    
    return dsr_norm == arin_norm

def parse_raw_notes(raw_notes):
    """Parse raw notes - exact logic from legacy meraki_mx.py"""
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
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, speed_str
        else:
            # Check for cellular provider patterns ending with "Cell"
            if segment.strip().endswith(' Cell'):
                provider_name = segment.strip()[:-5].strip()  # Remove " Cell" from end
                return provider_name, "Cell"
            # Check for Starlink + Satellite pattern
            elif 'starlink' in segment.lower() and 'satellite' in segment.lower():
                return "Starlink", "Satellite"
            # Check for Verizon Business (likely cellular backup)
            elif 'verizon business' in segment.lower() and len(segment.strip()) < 20:
                return "Verizon Business", "Cell"
            # Check for VZ Gateway (Verizon cellular)
            elif 'vz gateway' in segment.lower() or 'vzg' in segment.lower():
                return "VZW Cell", "Cell"
            # Check for DIG/Digi cellular
            elif segment.strip().upper() in ['DIG', 'DIGI']:
                return "Digi", "Cell"
            # Check for Accelerated provider (cellular)
            elif 'accelerated' in segment.strip().lower():
                return "Accelerated", "Cell"
            # Check for Unknown secondary circuits (skip these)
            elif segment.strip().lower() in ['unknown']:
                return "", ""
            # Handle "Cell Cell" case specifically
            elif segment.strip().lower() == 'cell cell':
                return "VZW Cell", "Cell"
            else:
                provider_name = re.sub(r'[^\w\s.&|-]', ' ', segment).strip()
                provider_name = re.sub(r'\s+', ' ', provider_name).strip()
                return provider_name, ""
    
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

def normalize_provider_for_comparison(provider):
    """Normalize provider for comparison ONLY (not for display)"""
    if not provider or provider.lower() in ['nan', 'null', '', 'unknown']:
        return ""
    
    provider_str = str(provider).strip()
    if not provider_str:
        return ""
    
    provider_lower = provider_str.lower()
    
    # Remove common prefixes and suffixes for comparison
    provider_clean = re.sub(
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workpace)\s*',
        '', provider_lower, flags=re.IGNORECASE
    ).strip()
    
    # Check mapping
    for key, mapped_value in PROVIDER_MAPPING.items():
        if key in provider_clean:
            return mapped_value.lower()
    
    return provider_clean

def normalize_provider(provider, is_dsr=False):
    """Normalize provider - exact logic from legacy nightly_enriched.py"""
    if not provider or str(provider).lower() in ['nan', 'null', '', 'unknown']:
        return ""
    
    # Clean provider name
    provider_clean = re.sub(
        r'\s*(?:##.*##|\s*imei.*$|\s*kitp.*$|\s*sn.*$|\s*port.*$|\s*location.*$|\s*in\s+the\s+bay.*$|\s*up\s+front.*$|\s*under\s+.*$|\s*wireless\s+gateway.*$|\s*serial.*$|\s*poe\s+injector.*$|\s*supported\s+through.*$|\s*static\s+ip.*$|\s*subnet\s+mask.*$|\s*gateway\s+ip.*$|\s*service\s+id.*$|\s*circuit\s+id.*$|\s*ip\s+address.*$|\s*5g.*$|\s*currently.*$)',
        '', str(provider), flags=re.IGNORECASE
    ).strip()
    
    provider_clean = re.sub(r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workpace)\s*', '', provider_clean, flags=re.IGNORECASE).strip()
    
    provider_lower = provider_clean.lower()
    
    # Special cases from original nightly_enriched.py
    if provider_lower.startswith('digi'):
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm')) and not is_dsr:
        return "VZW Cell"
    if 'accelerated' in provider_lower:
        return "Accelerated"
    
    # Check fuzzy mapping
    for key, value in PROVIDER_MAPPING.items():
        if len(provider_lower) >= 3 and len(key) >= 3:
            # Use fuzzy matching for longer strings
            if fuzz.ratio(key, provider_lower) > 70:
                return value
        else:
            # Exact match for short strings
            if key == provider_lower:
                return value
    
    return provider_clean

def compare_providers(arin_provider, notes_provider):
    """Compare ARIN provider and notes provider - from meraki_mx.py"""
    # Normalize both for comparison
    norm_arin = normalize_provider_for_comparison(arin_provider)
    norm_notes = normalize_provider_for_comparison(notes_provider)
    
    if not norm_notes or norm_notes == "unknown":
        return "No match" if norm_arin and norm_arin != "unknown" else "Match"
    
    if norm_notes == norm_arin:
        return "Match"
    
    # Fuzzy match
    similarity = fuzz.ratio(norm_notes, norm_arin)
    return "Match" if similarity >= 80 else "No match"

def reformat_speed(speed_str, provider):
    """Reformat speed string - handle special cases"""
    if not speed_str or str(speed_str).lower() == 'nan':
        return ""
    
    # Special cases for cellular/satellite
    provider_lower = str(provider).lower()
    if provider_lower == 'cell' or any(term in provider_lower for term in ['vzw cell', 'verizon cell', 'digi', 'inseego']):
        return "Cell"
    if 'starlink' in provider_lower:
        return "Satellite"
    
    return str(speed_str).strip()

def get_dsr_circuits(conn):
    """Get all enabled DSR circuits with their IPs"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            site_name,
            provider_name,
            details_ordered_service_speed,
            circuit_purpose,
            ip_address_start,
            billing_monthly_cost
        FROM circuits
        WHERE status = 'Enabled'
        AND provider_name IS NOT NULL
        AND provider_name != ''
    """)
    
    circuits_by_site = {}
    for row in cursor.fetchall():
        site_name = row[0]
        if site_name not in circuits_by_site:
            circuits_by_site[site_name] = []
        
        circuits_by_site[site_name].append({
            'provider': row[1],
            'speed': row[2],
            'purpose': row[3],
            'ip': row[4],
            'cost': row[5]
        })
    
    cursor.close()
    return circuits_by_site

def match_dsr_circuit_by_ip(dsr_circuits, wan_ip):
    """Match DSR circuit by IP address - highest priority"""
    if not wan_ip or not dsr_circuits:
        return None
    
    for circuit in dsr_circuits:
        if circuit.get('ip') == wan_ip:
            return circuit
    
    return None

def match_dsr_circuit_by_provider(dsr_circuits, notes_provider):
    """Match DSR circuit by provider name - second priority"""
    if not notes_provider or not dsr_circuits:
        return None
    
    notes_norm = normalize_provider_for_comparison(notes_provider)
    if not notes_norm:
        return None
    
    best_match = None
    best_score = 0
    
    for circuit in dsr_circuits:
        dsr_norm = normalize_provider_for_comparison(circuit['provider'])
        
        # Exact match after normalization
        if notes_norm == dsr_norm:
            return circuit
        
        # Fuzzy match
        score = max(
            fuzz.ratio(notes_norm, dsr_norm),
            fuzz.partial_ratio(notes_norm, dsr_norm)
        )
        
        if score > 70 and score > best_score:  # Improved fuzzy matching threshold
            best_match = circuit
            best_score = score
    
    return best_match

def detect_wan_flip(dsr_circuits, wan1_ip, wan2_ip, wan1_arin, wan2_arin):
    """
    Detect if WAN1 and WAN2 are flipped based on DSR data
    Returns: (wan1_is_flipped, wan2_is_flipped)
    """
    primary_circuit = None
    secondary_circuit = None
    
    # Find Primary and Secondary circuits
    for circuit in dsr_circuits:
        if circuit['purpose'] == 'Primary':
            primary_circuit = circuit
        elif circuit['purpose'] == 'Secondary':
            secondary_circuit = circuit
    
    if not primary_circuit or not secondary_circuit:
        return False, False
    
    # Check multiple indicators for flipping
    flip_indicators = 0
    
    # Check 1: IP addresses
    if primary_circuit['ip'] and wan2_ip and primary_circuit['ip'] == wan2_ip:
        flip_indicators += 2  # Strong indicator
    if secondary_circuit['ip'] and wan1_ip and secondary_circuit['ip'] == wan1_ip:
        flip_indicators += 2  # Strong indicator
    
    # Check 2: ARIN providers
    if (wan1_arin and secondary_circuit['provider'] and 
        providers_match_for_sync(secondary_circuit['provider'], wan1_arin)):
        flip_indicators += 1
    if (wan2_arin and primary_circuit['provider'] and 
        providers_match_for_sync(primary_circuit['provider'], wan2_arin)):
        flip_indicators += 1
    
    # If we have strong evidence of flipping
    if flip_indicators >= 2:
        logger.info(f"WAN flip detected with confidence score: {flip_indicators}")
        return True, True
    
    return False, False

def determine_final_provider(notes_provider, arin_provider, comparison, dsr_circuit):
    """
    MODIFIED: Determine final provider with DSR-ARIN preservation logic
    1. If DSR match exists AND ARIN matches DSR, use DSR provider name EXACTLY
    2. If no DSR match, use comparison logic
    """
    if dsr_circuit:
        # DSR match found - check if ARIN also matches
        if arin_provider and providers_match_for_sync(dsr_circuit['provider'], arin_provider):
            # Both DSR and ARIN match - definitely use DSR
            return dsr_circuit['provider'], True  # confirmed = True
        else:
            # DSR match but ARIN doesn't match - still use DSR
            return dsr_circuit['provider'], True  # confirmed = True
    
    # No DSR match - use comparison logic and normalize
    if comparison == "No match":
        # Trust notes over ARIN when they don't match, but normalize
        return normalize_provider(notes_provider, is_dsr=False), False
    else:
        # Trust ARIN when it matches or no comparison
        return arin_provider, False

def is_bad_speed_format(speed):
    """Check if speed is in the bad format (e.g., '20.0 M' or '300 x 30')"""
    if not speed:
        return False
    # Check for pattern like "123.4 M" (number, space, M)
    if re.match(r'^\d+\.?\d*\s+M$', speed):
        return True
    # Check for pattern like "300 x 30" (missing units)
    if re.match(r'^\d+\s*x\s*\d+$', speed):
        return True
    return False

def has_source_data_changed(current_record, device_notes, wan1_ip, wan2_ip, wan1_arin, wan2_arin, dsr_circuits):
    """
    Check if any source data has changed that would require updating
    For non-DSR circuits, only update if Meraki data changes
    """
    # Parse current device notes
    current_wan1_notes, current_wan1_speed, current_wan2_notes, current_wan2_speed = parse_raw_notes(device_notes)
    
    # For non-DSR circuits, check if the Meraki notes or IPs have changed
    has_dsr = len(dsr_circuits) > 0
    
    if not has_dsr:
        # This is a non-DSR circuit - check if anything in Meraki has changed
        # We'll be conservative and only update if we detect actual changes
        
        # Compare normalized providers to avoid false positives
        current_wan1_norm = normalize_provider_for_comparison(current_record.get('wan1_provider', ''))
        current_wan2_norm = normalize_provider_for_comparison(current_record.get('wan2_provider', ''))
        
        new_wan1_norm = normalize_provider_for_comparison(current_wan1_notes)
        new_wan2_norm = normalize_provider_for_comparison(current_wan2_notes)
        
        # Check if providers have meaningfully changed
        if current_wan1_norm != new_wan1_norm or current_wan2_norm != new_wan2_norm:
            logger.debug(f"Non-DSR circuit provider changed: WAN1 '{current_wan1_norm}' -> '{new_wan1_norm}', WAN2 '{current_wan2_norm}' -> '{new_wan2_norm}'")
            return True
        
        # Check if speeds have changed (but ignore formatting differences)
        current_wan1_speed_str = str(current_record.get('wan1_speed', '')).strip()
        current_wan2_speed_str = str(current_record.get('wan2_speed', '')).strip()
        
        if current_wan1_speed_str != current_wan1_speed or current_wan2_speed_str != current_wan2_speed:
            logger.debug(f"Non-DSR circuit speed changed")
            return True
        
        # Check if ARIN data has changed
        # Note: We don't have stored ARIN data, so we can't compare
        # But if ARIN exists now and circuit is unconfirmed, that's not a change
        
        logger.debug(f"Non-DSR circuit unchanged, preserving existing data")
        return False
    
    # For DSR circuits, always process normally as they might need matching
    return True

def format_cost(cost):
    """Format cost to match legacy format"""
    if not cost or cost == 0:
        return "$0.00"
    
    try:
        cost_float = float(cost)
        return f"${cost_float:.2f}"
    except:
        return "$0.00"

def needs_update(current_record, new_data):
    """Check if a record needs updating"""
    # Force update if current speeds are in bad format
    if (is_bad_speed_format(current_record.get('wan1_speed')) or 
        is_bad_speed_format(current_record.get('wan2_speed'))):
        return True

    # Compare key fields
    fields_to_check = [
        ('wan1_provider', 'wan1_provider'),
        ('wan1_speed', 'wan1_speed'),
        ('wan1_circuit_role', 'wan1_circuit_role'),
        ('wan1_confirmed', 'wan1_confirmed'),
        ('wan2_provider', 'wan2_provider'),
        ('wan2_speed', 'wan2_speed'),
        ('wan2_circuit_role', 'wan2_circuit_role'),
        ('wan2_confirmed', 'wan2_confirmed')
    ]
    
    for db_field, new_field in fields_to_check:
        if str(current_record.get(db_field, '')).strip() != str(new_data.get(new_field, '')).strip():
            return True
    
    return False

def enrich_circuits(conn):
    """FINAL: Main enrichment process with complete preservation logic"""
    cursor = conn.cursor()
    
    # Get all DSR circuits
    logger.info("Loading DSR circuit data...")
    dsr_circuits_by_site = get_dsr_circuits(conn)
    logger.info(f"Loaded DSR circuits for {len(dsr_circuits_by_site)} sites")
    
    # Get current enriched circuits for comparison
    cursor.execute("""
        SELECT network_name, wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
               wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed
        FROM enriched_circuits
    """)
    
    current_enriched = {}
    for row in cursor.fetchall():
        current_enriched[row[0]] = {
            'wan1_provider': row[1],
            'wan1_speed': row[2],
            'wan1_circuit_role': row[3],
            'wan1_confirmed': row[4],
            'wan2_provider': row[5],
            'wan2_speed': row[6],
            'wan2_circuit_role': row[7],
            'wan2_confirmed': row[8]
        }
    
    logger.info(f"Found {len(current_enriched)} existing enriched records")
    
    # Get all MX devices from meraki_inventory
    cursor.execute("""
        SELECT DISTINCT ON (network_name)
            network_name,
            device_serial,
            device_model,
            device_tags,
            device_notes,
            wan1_ip,
            wan1_arin_provider,
            wan2_ip,
            wan2_arin_provider
        FROM meraki_inventory
        WHERE device_model LIKE 'MX%'
        ORDER BY network_name, device_serial
    """)
    
    devices = cursor.fetchall()
    logger.info(f"Processing {len(devices)} MX devices")
    
    updates_made = 0
    inserts_made = 0
    preserved_count = 0
    flip_detected_count = 0
    non_dsr_preserved = 0
    skipped_count = 0
    
    for device in devices:
        (network_name, device_serial, device_model, device_tags,
         device_notes, wan1_ip, wan1_arin, wan2_ip, wan2_arin) = device
        
        
        # Convert SpaceX to Starlink in ARIN data
        if wan1_arin and 'spacex' in wan1_arin.lower():
            wan1_arin = 'Starlink'
        if wan2_arin and 'spacex' in wan2_arin.lower():
            wan2_arin = 'Starlink'
        # Skip excluded tags and network names
        if device_tags and any(tag.lower() in ['hub', 'lab', 'voice', 'test'] for tag in device_tags):
            continue
            
        # Skip excluded network names
        network_lower = network_name.lower()
        if any(pattern in network_lower for pattern in ['hub', 'lab', 'voice', 'datacenter', 'test', 'store in a box', 'sib']):
            continue
            
        # Also check device notes for test indicators
        notes_lower = (device_notes or '').lower()
        if any(pattern in notes_lower for pattern in ['test store', 'test site', 'lab site', 'hub site', 'voice site']):
            continue
        
        # Get DSR circuits for this site
        dsr_circuits = dsr_circuits_by_site.get(network_name, [])
        
        # Get current record
        current_record = current_enriched.get(network_name, {})
        

        # Check if IPs have changed
        ip_changed = False
        if current_record:
            if (current_record.get('wan1_ip') != wan1_ip or 
                current_record.get('wan2_ip') != wan2_ip):
                ip_changed = True
        
        # If IPs haven't changed and we have valid ARIN data, skip entirely
        if not ip_changed and current_record:
            if (wan1_arin and wan1_arin not in ["Unknown", ""] and 
                wan2_arin and wan2_arin not in ["Unknown", ""]):
                # Only skip if speeds are in correct format
                if (not is_bad_speed_format(current_record.get('wan1_speed')) and
                    not is_bad_speed_format(current_record.get('wan2_speed'))):
                    skipped_count += 1
                    logger.debug(f"{network_name}: No IP changes, has valid ARIN data, and speeds are correct - skipping")
                    continue
        # Check if this is a non-DSR circuit and if source data has changed
        if not dsr_circuits and current_record:
            if not has_source_data_changed(current_record, device_notes, wan1_ip, wan2_ip, wan1_arin, wan2_arin, dsr_circuits):
                # Non-DSR circuit with no changes - preserve completely
                non_dsr_preserved += 1
                logger.debug(f"{network_name}: Non-DSR circuit unchanged, preserving")
                continue
        
        # Parse device notes
        wan1_notes, wan1_speed, wan2_notes, wan2_speed = parse_raw_notes(device_notes)
        
        # Compare ARIN vs notes
        wan1_comparison = compare_providers(wan1_arin, wan1_notes)
        wan2_comparison = compare_providers(wan2_arin, wan2_notes)
        
        # Check for WAN flipping
        wan1_flipped, wan2_flipped = detect_wan_flip(dsr_circuits, wan1_ip, wan2_ip, wan1_arin, wan2_arin)
        
        if wan1_flipped and wan2_flipped:
            flip_detected_count += 1
            logger.info(f"{network_name}: WAN flip detected - swapping matching logic")
            
            # If flipped, match WAN1 to Secondary and WAN2 to Primary
            wan1_dsr = None
            wan2_dsr = None
            
            # Look for Secondary circuit for WAN1
            for circuit in dsr_circuits:
                if circuit['purpose'] == 'Secondary':
                    if circuit.get('ip') == wan1_ip:
                        wan1_dsr = circuit
                        break
                    elif not wan1_dsr and providers_match_for_sync(circuit['provider'], wan1_arin):
                        wan1_dsr = circuit
            
            # Look for Primary circuit for WAN2
            for circuit in dsr_circuits:
                if circuit['purpose'] == 'Primary':
                    if circuit.get('ip') == wan2_ip:
                        wan2_dsr = circuit
                        break
                    elif not wan2_dsr and providers_match_for_sync(circuit['provider'], wan2_arin):
                        wan2_dsr = circuit
        else:
            # Normal matching - WAN1 to Primary, WAN2 to Secondary
            wan1_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan1_ip)
            if not wan1_dsr:
                wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_notes)
            # Improved fuzzy matching: Try ARIN provider if device notes fail
            if not wan1_dsr and wan1_arin:
                wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_arin)
                if wan1_dsr:
                    logger.info(f"{network_name}: WAN1 matched via ARIN fallback: {wan1_arin} → {wan1_dsr['provider']}")
            
            wan2_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan2_ip)
            if not wan2_dsr:
                wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_notes)
            # Improved fuzzy matching: Try ARIN provider if device notes fail
            if not wan2_dsr and wan2_arin:
                wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_arin)
                if wan2_dsr:
                    logger.info(f"{network_name}: WAN2 matched via ARIN fallback: {wan2_arin} → {wan2_dsr['provider']}")
        
        # PRESERVATION LOGIC: Check if we should preserve existing DSR data
        
        # For WAN1: Check for preservation with flip awareness
        wan1_preserve = False
        if current_record.get('wan1_confirmed') and current_record.get('wan1_provider'):
            # Check if current WAN1 matches either ARIN provider (considering flips)
            if wan1_arin and providers_match_for_sync(current_record.get('wan1_provider'), wan1_arin):
                wan1_preserve = True
            elif wan2_arin and providers_match_for_sync(current_record.get('wan1_provider'), wan2_arin):
                # Current WAN1 matches WAN2 ARIN - possible flip scenario
                wan1_preserve = True
                logger.debug(f"{network_name}: Preserving WAN1 despite possible flip")
        
        if wan1_preserve:
            wan1_provider = current_record.get('wan1_provider')
            wan1_speed_final = current_record.get('wan1_speed')
            wan1_role = current_record.get('wan1_circuit_role')
            wan1_confirmed = True
            preserved_count += 1
        else:
            # Determine final providers normally
            wan1_provider, wan1_confirmed = determine_final_provider(
                wan1_notes, wan1_arin, wan1_comparison, wan1_dsr
            )
            # Format speeds - prefer DSR speeds when available, fall back to Meraki notes
            wan1_speed_to_use = wan1_dsr['speed'] if wan1_dsr and wan1_dsr.get('speed') else wan1_speed
            wan1_speed_final = reformat_speed(wan1_speed_to_use, wan1_provider)
            wan1_role = wan1_dsr['purpose'] if wan1_dsr else ("Secondary" if wan1_flipped else "Primary")
            
            # Standardize provider to "Starlink" if speed is "Satellite"
            if wan1_speed_final == "Satellite":
                wan1_provider = "Starlink"
        
        # For WAN2: Check for preservation with flip awareness
        wan2_preserve = False
        if current_record.get('wan2_confirmed') and current_record.get('wan2_provider'):
            # Check if current WAN2 matches either ARIN provider (considering flips)
            if wan2_arin and providers_match_for_sync(current_record.get('wan2_provider'), wan2_arin):
                wan2_preserve = True
            elif wan1_arin and providers_match_for_sync(current_record.get('wan2_provider'), wan1_arin):
                # Current WAN2 matches WAN1 ARIN - possible flip scenario
                wan2_preserve = True
                logger.debug(f"{network_name}: Preserving WAN2 despite possible flip")
        
        if wan2_preserve:
            wan2_provider = current_record.get('wan2_provider')
            wan2_speed_final = current_record.get('wan2_speed')
            wan2_role = current_record.get('wan2_circuit_role')
            wan2_confirmed = True
            preserved_count += 1
        else:
            # Determine final providers normally
            wan2_provider, wan2_confirmed = determine_final_provider(
                wan2_notes, wan2_arin, wan2_comparison, wan2_dsr
            )
            # Format speeds - prefer DSR speeds when available, fall back to Meraki notes
            wan2_speed_to_use = wan2_dsr['speed'] if wan2_dsr and wan2_dsr.get('speed') else wan2_speed
            wan2_speed_final = reformat_speed(wan2_speed_to_use, wan2_provider)
            wan2_role = wan2_dsr['purpose'] if wan2_dsr else ("Primary" if wan2_flipped else "Secondary")
            
            # Standardize provider to "Starlink" if speed is "Satellite"
            if wan2_speed_final == "Satellite":
                wan2_provider = "Starlink"
        
        new_data = {
            'network_name': network_name,
            'wan1_provider': wan1_provider,
            'wan1_speed': wan1_speed_final,
            'wan1_circuit_role': wan1_role,
            'wan1_confirmed': wan1_confirmed,
            'wan1_ip': wan1_ip,
            'wan1_arin_org': wan1_arin,
            'wan2_provider': wan2_provider,
            'wan2_speed': wan2_speed_final,
            'wan2_circuit_role': wan2_role,
            'wan2_confirmed': wan2_confirmed,
            'wan2_ip': wan2_ip,
            'wan2_arin_org': wan2_arin,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        # Check if update is needed
        if network_name in current_enriched:
            if needs_update(current_enriched[network_name], new_data):
                # Update existing record
                cursor.execute("""
                    UPDATE enriched_circuits SET
                        wan1_provider = %s,
                        wan1_speed = %s,
                        wan1_circuit_role = %s,
                        wan1_confirmed = %s,
                        wan1_ip = %s,
                        wan1_arin_org = %s,
                        wan2_provider = %s,
                        wan2_speed = %s,
                        wan2_circuit_role = %s,
                        wan2_confirmed = %s,
                        wan2_ip = %s,
                        wan2_arin_org = %s,
                        last_updated = %s
                    WHERE network_name = %s
                """, (
                    new_data['wan1_provider'],
                    new_data['wan1_speed'],
                    new_data['wan1_circuit_role'],
                    new_data['wan1_confirmed'],
                    new_data['wan1_ip'],
                    new_data['wan1_arin_org'],
                    new_data['wan2_provider'],
                    new_data['wan2_speed'],
                    new_data['wan2_circuit_role'],
                    new_data['wan2_confirmed'],
                    new_data['wan2_ip'],
                    new_data['wan2_arin_org'],
                    new_data['last_updated'],
                    network_name
                ))
                updates_made += 1
                
                if wan1_preserve or wan2_preserve:
                    logger.debug(f"{network_name}: Preserved DSR-ARIN matched data")
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO enriched_circuits (
                    network_name, wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
                    wan1_ip, wan1_arin_org,
                    wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed,
                    wan2_ip, wan2_arin_org, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                network_name,
                new_data['wan1_provider'],
                new_data['wan1_speed'],
                new_data['wan1_circuit_role'],
                new_data['wan1_confirmed'],
                new_data['wan1_ip'],
                new_data['wan1_arin_org'],
                new_data['wan2_provider'],
                new_data['wan2_speed'],
                new_data['wan2_circuit_role'],
                new_data['wan2_confirmed'],
                new_data['wan2_ip'],
                new_data['wan2_arin_org'],
                new_data['last_updated']
            ))
            inserts_made += 1
    
    # Remove records for networks that no longer exist
    cursor.execute("""
        DELETE FROM enriched_circuits
        WHERE network_name NOT IN (
            SELECT DISTINCT network_name 
            FROM meraki_inventory 
            WHERE device_model LIKE 'MX%'
        )
    """)
    deleted_count = cursor.rowcount
    
    conn.commit()
    
    logger.info(f"Enrichment complete: {updates_made} updated, {inserts_made} inserted, {deleted_count} deleted")
    logger.info(f"Preserved {preserved_count} DSR-ARIN matched entries")
    logger.info(f"Preserved {non_dsr_preserved} non-DSR circuits (no changes detected)")
    logger.info(f"Skipped {skipped_count} sites with no changes and valid ARIN data")
    logger.info(f"Detected {flip_detected_count} sites with WAN flipping")
    
    cursor.close()

def sync_enriched_to_circuits(conn):
    """
    Sync confirmed enriched data back to circuits table for non-DSR circuits
    This preserves manually edited data from the web interface
    """
    cursor = conn.cursor()
    
    try:
        logger.info("Starting sync of enriched data back to circuits table for non-DSR circuits...")
        
        # Find non-DSR circuits that need updating
        cursor.execute("""
            WITH dsr_sites AS (
                -- Sites that have DSR Primary circuits (these are protected)
                SELECT DISTINCT site_name 
                FROM circuits 
                WHERE circuit_purpose = 'Primary' 
                AND status = 'Enabled'
                AND provider_name NOT LIKE '%Unknown%'
                AND provider_name IS NOT NULL
                AND provider_name != ''
            )
            SELECT 
                c.record_number,
                c.site_name,
                c.circuit_purpose,
                c.provider_name as current_provider,
                c.details_service_speed as current_speed,
                CASE 
                    WHEN c.circuit_purpose = 'Primary' THEN e.wan1_provider
                    ELSE e.wan2_provider
                END as enriched_provider,
                CASE 
                    WHEN c.circuit_purpose = 'Primary' THEN e.wan1_speed
                    ELSE e.wan2_speed
                END as enriched_speed,
                CASE 
                    WHEN c.circuit_purpose = 'Primary' THEN e.wan1_confirmed
                    ELSE e.wan2_confirmed
                END as is_confirmed
            FROM circuits c
            JOIN enriched_circuits e ON c.site_name = e.network_name
            WHERE c.status = 'Enabled'
            AND c.manual_override IS NOT TRUE
            AND c.site_name NOT IN (SELECT site_name FROM dsr_sites)
            AND (
                -- Only update if enriched data is confirmed
                (c.circuit_purpose = 'Primary' AND e.wan1_confirmed = TRUE) OR
                (c.circuit_purpose = 'Secondary' AND e.wan2_confirmed = TRUE)
            )
        """)
        
        updates_to_make = []
        
        for row in cursor.fetchall():
            record_number = row[0]
            site_name = row[1]
            purpose = row[2]
            current_provider = row[3] or ''
            current_speed = row[4] or ''
            enriched_provider = row[5] or ''
            enriched_speed = row[6] or ''
            
            # Check if update is needed
            provider_changed = current_provider.strip() != enriched_provider.strip()
            speed_changed = current_speed.strip() != enriched_speed.strip()
            
            if provider_changed or speed_changed:
                updates_to_make.append({
                    'record_number': record_number,
                    'provider': enriched_provider,
                    'speed': enriched_speed,
                    'site': site_name,
                    'purpose': purpose
                })
        
        if updates_to_make:
            logger.info(f"Found {len(updates_to_make)} non-DSR circuits to update from enriched data")
            
            # Perform batch update
            update_query = """
                UPDATE circuits 
                SET provider_name = %(provider)s,
                    details_service_speed = %(speed)s,
                    updated_at = NOW(),
                    data_source = 'enriched_sync'
                WHERE record_number = %(record_number)s
                AND manual_override IS NOT TRUE
            """
            
            execute_batch(cursor, update_query, updates_to_make)
            
            conn.commit()
            
            # Log updates
            for update in updates_to_make[:10]:  # Show first 10
                logger.info(f"Updated {update['site']} ({update['purpose']}): "
                          f"Provider='{update['provider']}', Speed='{update['speed']}'")
            
            if len(updates_to_make) > 10:
                logger.info(f"... and {len(updates_to_make) - 10} more")
            
            return len(updates_to_make)
        else:
            logger.info("No non-DSR circuits need updating from enriched data")
            return 0
            
    except Exception as e:
        logger.error(f"Error syncing enriched to circuits: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def main():
    """Main function"""
    logger.info("=== Starting COMPLETE Nightly Enriched Database Script ===")
    logger.info("Features: Full preservation + WAN flip detection + enriched->circuits sync")
    
    try:
        conn = get_db_connection()
        
        # Step 1: Enrich circuits with preservation logic
        enrich_circuits(conn)
        
        # Step 2: Sync confirmed enriched data back to circuits table for non-DSR circuits
        circuits_updated = sync_enriched_to_circuits(conn)
        logger.info(f"Synced {circuits_updated} non-DSR circuits from enriched data")
        
        conn.close()
        
        logger.info("=== All Processing Complete ===")
        
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()