#!/usr/bin/env python3
"""
CORRECT Nightly Enriched Database Script
Implements exact legacy logic from meraki_mx.py + nightly_enriched.py
Reads device notes directly from Meraki API, not from files
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone
import re
from fuzzywuzzy import fuzz

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workpace)\s*',
        '', provider_lower, flags=re.IGNORECASE
    ).strip()
    
    # Check mapping
    for key, mapped_value in PROVIDER_MAPPING.items():
        if key in provider_clean:
            return mapped_value.lower()
    
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
    if not speed_str:
        return ""
    
    # Special cases for cellular/satellite
    provider_lower = str(provider).lower()
    if any(term in provider_lower for term in ['vzw cell', 'verizon cell', 'digi', 'inseego']):
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
        
        if score > 60 and score > best_score:
            best_match = circuit
            best_score = score
    
    return best_match

def determine_final_provider(notes_provider, arin_provider, comparison, dsr_circuit):
    """
    Determine final provider using exact legacy logic:
    1. If DSR match exists, use DSR provider name EXACTLY
    2. If no DSR match, use comparison logic
    """
    if dsr_circuit:
        # DSR match found - use exact DSR provider name
        return dsr_circuit['provider'], True  # confirmed = True
    
    # No DSR match - use comparison logic
    if comparison == "No match":
        # Trust notes over ARIN when they don't match
        return notes_provider, False
    else:
        # Trust ARIN when it matches or no comparison
        return arin_provider, False

def format_cost(cost):
    """Format cost to match legacy format"""
    if not cost or cost == 0:
        return "$0.00"
    
    try:
        cost_float = float(cost)
        return f"${cost_float:.2f}"
    except:
        return "$0.00"

def enrich_circuits(conn):
    """Main enrichment process using exact legacy logic"""
    cursor = conn.cursor()
    
    # Get all DSR circuits
    logger.info("Loading DSR circuit data...")
    dsr_circuits_by_site = get_dsr_circuits(conn)
    logger.info(f"Loaded DSR circuits for {len(dsr_circuits_by_site)} sites")
    
    # Get all MX devices from meraki_inventory
    cursor.execute("""
        SELECT 
            network_name,
            device_serial,
            device_model,
            device_tags,
            raw_notes,
            wan1_ip,
            wan1_arin_provider,
            wan2_ip,
            wan2_arin_provider
        FROM meraki_inventory
        WHERE device_model LIKE 'MX%'
        ORDER BY network_name
    """)
    
    devices = cursor.fetchall()
    logger.info(f"Processing {len(devices)} MX devices")
    
    enriched_data = []
    
    for device in devices:
        (network_name, device_serial, device_model, device_tags,
         raw_notes, wan1_ip, wan1_arin, wan2_ip, wan2_arin) = device
        
        # Skip excluded tags
        if device_tags and any(tag.lower() in ['hub', 'lab', 'voice'] for tag in device_tags):
            continue
        
        # Parse device notes
        wan1_notes, wan1_speed, wan2_notes, wan2_speed = parse_raw_notes(raw_notes)
        
        # Compare ARIN vs notes
        wan1_comparison = compare_providers(wan1_arin, wan1_notes)
        wan2_comparison = compare_providers(wan2_arin, wan2_notes)
        
        # Get DSR circuits for this site
        dsr_circuits = dsr_circuits_by_site.get(network_name, [])
        
        # Match DSR circuits by IP first, then by provider
        wan1_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan1_ip)
        if not wan1_dsr:
            wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_notes)
        
        wan2_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan2_ip)
        if not wan2_dsr:
            wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_notes)
        
        # Determine final providers
        wan1_provider, wan1_confirmed = determine_final_provider(
            wan1_notes, wan1_arin, wan1_comparison, wan1_dsr
        )
        wan2_provider, wan2_confirmed = determine_final_provider(
            wan2_notes, wan2_arin, wan2_comparison, wan2_dsr
        )
        
        # Format speeds
        wan1_speed_final = reformat_speed(wan1_speed, wan1_provider)
        wan2_speed_final = reformat_speed(wan2_speed, wan2_provider)
        
        # Get costs and roles
        wan1_cost = format_cost(wan1_dsr['cost'] if wan1_dsr else 0)
        wan2_cost = format_cost(wan2_dsr['cost'] if wan2_dsr else 0)
        
        wan1_role = wan1_dsr['purpose'] if wan1_dsr else "Primary"
        wan2_role = wan2_dsr['purpose'] if wan2_dsr else "Secondary"
        
        enriched_data.append({
            'network_name': network_name,
            'wan1_provider': wan1_provider,
            'wan1_speed': wan1_speed_final,
            'wan1_cost': wan1_cost,
            'wan1_role': wan1_role,
            'wan1_confirmed': wan1_confirmed,
            'wan2_provider': wan2_provider,
            'wan2_speed': wan2_speed_final,
            'wan2_cost': wan2_cost,
            'wan2_role': wan2_role,
            'wan2_confirmed': wan2_confirmed,
            'last_updated': datetime.now(timezone.utc).isoformat()
        })
        
        logger.debug(f"{network_name}: WAN1={wan1_provider} ({wan1_role}, confirmed={wan1_confirmed}), "
                    f"WAN2={wan2_provider} ({wan2_role}, confirmed={wan2_confirmed})")
    
    # Update enriched_circuits table
    if enriched_data:
        logger.info(f"Updating enriched_circuits table with {len(enriched_data)} records...")
        
        # Clear existing data
        cursor.execute("TRUNCATE TABLE enriched_circuits")
        
        # Insert new data
        insert_query = """
            INSERT INTO enriched_circuits (
                network_name, wan1_provider, wan1_speed, wan1_cost, wan1_role, wan1_confirmed,
                wan2_provider, wan2_speed, wan2_cost, wan2_role, wan2_confirmed, last_updated
            ) VALUES %s
        """
        
        values = [
            (d['network_name'], d['wan1_provider'], d['wan1_speed'], d['wan1_cost'], 
             d['wan1_role'], d['wan1_confirmed'], d['wan2_provider'], d['wan2_speed'], 
             d['wan2_cost'], d['wan2_role'], d['wan2_confirmed'], d['last_updated'])
            for d in enriched_data
        ]
        
        execute_values(cursor, insert_query, values)
        conn.commit()
        
        logger.info("Enriched circuits table updated successfully")
    
    cursor.close()

def main():
    """Main function"""
    logger.info("=== Starting Nightly Enriched Database Script (CORRECT) ===")
    logger.info("Using exact legacy logic: DSR priority, IP matching, provider preservation")
    
    try:
        conn = get_db_connection()
        enrich_circuits(conn)
        conn.close()
        
        logger.info("=== Enrichment Complete ===")
        
    except Exception as e:
        logger.error(f"Error during enrichment: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()