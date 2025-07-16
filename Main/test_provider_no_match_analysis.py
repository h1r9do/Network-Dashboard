#!/usr/bin/env python3
"""
Test script to analyze NO MATCH cases between DSR and ARIN data
Includes parsed Meraki notes to understand discrepancies
"""

import os
import sys
import csv
import re
from datetime import datetime
from thefuzz import fuzz
import psycopg2

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Provider mapping from the enrichment scripts
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
    "mediacom/boi": "Mediacom",
    "mediacom": "Mediacom",
    "centurylink": "CenturyLink",
    "frontier": "Frontier",
    "windstream": "Windstream",
    "lumen": "Lumen",
    "brightspeed": "Brightspeed",
    "optimum": "Optimum",
    "altice": "Optimum",
    "cable one": "Cable One",
    "cableone": "Cable One",
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

def normalize_provider_for_matching(provider):
    """Normalize provider for matching purposes"""
    if not provider:
        return ""
    
    # Convert to lowercase and strip
    provider = str(provider).lower().strip()
    
    # Remove common prefixes and suffixes
    provider = re.sub(r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\\s+', '', provider)
    provider = re.sub(r'\s*(?:extended\s+cable|dsl|fiber|adi|workpace|broadband\s+ii)\s*', '', provider)
    provider = re.sub(r'[^\w\s&/-]', ' ', provider)
    provider = re.sub(r'\s+', ' ', provider).strip()
    
    return provider

def parse_raw_notes(raw_notes):
    """Parse the 'notes' field to extract WAN provider labels and speeds."""
    if not raw_notes or not raw_notes.strip():
        return ""
    
    # FIX: Convert literal \\n strings to actual newlines BEFORE processing
    if '\\n' in raw_notes and '\n' not in raw_notes:
        raw_notes = raw_notes.replace('\\n', '\n')
    
    # Replace actual newlines with | for single-line display
    text = raw_notes.replace('\n', ' | ')
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def get_canonical_provider(provider):
    """Get canonical provider name from mapping"""
    if not provider:
        return provider
    
    provider_lower = provider.lower().strip()
    
    # Check exact matches first
    for key, value in PROVIDER_MAPPING.items():
        if key == provider_lower:
            return value
    
    # Check partial matches
    for key, value in PROVIDER_MAPPING.items():
        if key in provider_lower or provider_lower in key:
            return value
    
    return provider

def fuzzy_match_providers(dsr_provider, arin_provider):
    """
    Perform fuzzy matching between DSR and ARIN providers
    Returns: (match_status, match_score, reason)
    """
    if not dsr_provider or not arin_provider:
        return "No Match", 0, "Missing provider data"
    
    # Normalize both providers
    dsr_norm = normalize_provider_for_matching(dsr_provider)
    arin_norm = normalize_provider_for_matching(arin_provider)
    
    # Get canonical names
    dsr_canonical = get_canonical_provider(dsr_provider)
    arin_canonical = get_canonical_provider(arin_provider)
    
    # Special cases for known matches
    special_matches = {
        ('mediacom', 'mediacom communications'): True,
        ('at&t', 'at&t'): True,
        ('att', 'at&t'): True,
        ('centurylink', 'lumen'): True,
        ('charter', 'charter communications'): True,
        ('cox', 'cox communications'): True,
        ('comcast', 'comcast cable'): True,
        ('verizon', 'verizon business'): True,
        ('frontier', 'frontier communications'): True,
        ('windstream', 'windstream communications'): True,
    }
    
    # Check special matches
    for (dsr_key, arin_key), should_match in special_matches.items():
        if dsr_key in dsr_norm and arin_key in arin_norm and should_match:
            return "Match", 100, f"Special case: {dsr_key} <-> {arin_key}"
    
    # Check if canonical names match
    if dsr_canonical and arin_canonical and dsr_canonical.lower() == arin_canonical.lower():
        return "Match", 95, f"Canonical match: {dsr_canonical}"
    
    # Direct normalized match
    if dsr_norm == arin_norm:
        return "Match", 100, "Direct normalized match"
    
    # Fuzzy matching on normalized strings
    score1 = fuzz.ratio(dsr_norm, arin_norm)
    score2 = fuzz.partial_ratio(dsr_norm, arin_norm)
    score3 = fuzz.token_sort_ratio(dsr_norm, arin_norm)
    
    # Take the best score
    best_score = max(score1, score2, score3)
    
    # Determine match status
    if best_score >= 80:
        return "Match", best_score, f"Fuzzy match (scores: {score1}, {score2}, {score3})"
    elif best_score >= 60:
        return "Possible Match", best_score, f"Low confidence (scores: {score1}, {score2}, {score3})"
    else:
        return "No Match", best_score, f"Low similarity (scores: {score1}, {score2}, {score3})"

def main():
    print("Starting NO MATCH provider analysis with Meraki notes...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query to get DSR circuits with corresponding ARIN and Meraki notes data
    query = """
        WITH dsr_circuits AS (
            SELECT 
                c.site_name,
                c.site_id,
                c.circuit_purpose,
                c.provider_name as dsr_provider,
                c.details_ordered_service_speed as dsr_speed,
                c.billing_monthly_cost as dsr_cost,
                c.ip_address_start as dsr_ip
            FROM circuits c
            WHERE c.status = 'Enabled'
            AND c.provider_name IS NOT NULL
            AND c.provider_name != ''
            ORDER BY c.site_name, c.circuit_purpose
        ),
        meraki_data AS (
            SELECT DISTINCT ON (network_name)
                network_name,
                device_notes,
                wan1_ip,
                wan1_arin_provider,
                wan1_provider_label,
                wan1_speed_label,
                wan2_ip,
                wan2_arin_provider,
                wan2_provider_label,
                wan2_speed_label
            FROM meraki_inventory
            WHERE device_model LIKE 'MX%'
            ORDER BY network_name, last_updated DESC
        )
        SELECT 
            d.site_name,
            d.site_id,
            d.circuit_purpose,
            d.dsr_provider,
            d.dsr_speed,
            d.dsr_cost,
            d.dsr_ip,
            CASE 
                WHEN d.dsr_ip = m.wan1_ip THEN 'WAN1'
                WHEN d.dsr_ip = m.wan2_ip THEN 'WAN2'
                ELSE 'Unknown'
            END as wan_port,
            CASE 
                WHEN d.dsr_ip = m.wan1_ip THEN m.wan1_arin_provider
                WHEN d.dsr_ip = m.wan2_ip THEN m.wan2_arin_provider
                ELSE NULL
            END as arin_provider,
            m.device_notes,
            m.wan1_provider_label,
            m.wan1_speed_label,
            m.wan2_provider_label,
            m.wan2_speed_label,
            m.wan1_ip,
            m.wan1_arin_provider,
            m.wan2_ip,
            m.wan2_arin_provider
        FROM dsr_circuits d
        LEFT JOIN meraki_data m ON d.site_name = m.network_name
        ORDER BY d.site_name, d.circuit_purpose
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Prepare CSV output - only no matches
    output_file = f'/tmp/provider_no_match_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write headers
        writer.writerow([
            'Site Name',
            'Site ID',
            'Circuit Purpose',
            'DSR Provider',
            'ARIN Provider',
            'Match Status',
            'Match Score',
            'DSR Speed',
            'DSR Cost',
            'Meraki Notes (Parsed)',  # Column J
            'WAN1 Notes Provider',
            'WAN1 Notes Speed',
            'WAN2 Notes Provider', 
            'WAN2 Notes Speed',
            'DSR IP',
            'Matched WAN Port',
            'WAN1 IP',
            'WAN1 ARIN Provider',
            'WAN2 IP',
            'WAN2 ARIN Provider'
        ])
        
        # Process each circuit - only write no matches
        no_match_count = 0
        
        for row in results:
            site_name = row[0]
            site_id = row[1]
            circuit_purpose = row[2]
            dsr_provider = row[3]
            dsr_speed = row[4]
            dsr_cost = row[5]
            dsr_ip = row[6]
            wan_port = row[7]
            arin_provider = row[8]
            device_notes = row[9]
            wan1_notes_provider = row[10]
            wan1_notes_speed = row[11]
            wan2_notes_provider = row[12]
            wan2_notes_speed = row[13]
            wan1_ip = row[14]
            wan1_arin = row[15]
            wan2_ip = row[16]
            wan2_arin = row[17]
            
            # If we don't have a direct IP match, try to match by provider
            if wan_port == 'Unknown' and arin_provider is None:
                # Try to match against WAN1
                if wan1_arin:
                    match_status1, score1, reason1 = fuzzy_match_providers(dsr_provider, wan1_arin)
                else:
                    match_status1, score1, reason1 = "No Match", 0, "No WAN1 ARIN data"
                
                # Try to match against WAN2
                if wan2_arin:
                    match_status2, score2, reason2 = fuzzy_match_providers(dsr_provider, wan2_arin)
                else:
                    match_status2, score2, reason2 = "No Match", 0, "No WAN2 ARIN data"
                
                # Use the better match
                if score1 >= score2:
                    arin_provider = wan1_arin
                    match_status, match_score, match_reason = match_status1, score1, reason1
                    if match_status == "Match":
                        wan_port = "WAN1 (Provider Match)"
                else:
                    arin_provider = wan2_arin
                    match_status, match_score, match_reason = match_status2, score2, reason2
                    if match_status == "Match":
                        wan_port = "WAN2 (Provider Match)"
            else:
                # We have a direct match, analyze it
                match_status, match_score, match_reason = fuzzy_match_providers(dsr_provider, arin_provider)
            
            # Only write no matches
            if match_status == "No Match":
                no_match_count += 1
                
                # Parse device notes to single line
                parsed_notes = parse_raw_notes(device_notes) if device_notes else ""
                
                # Write row
                writer.writerow([
                    site_name,
                    site_id,
                    circuit_purpose,
                    dsr_provider,
                    arin_provider if arin_provider else "",
                    match_status,
                    match_score,
                    dsr_speed,
                    f"${dsr_cost:.2f}" if dsr_cost else "",
                    parsed_notes,  # Column J - Meraki Notes
                    wan1_notes_provider if wan1_notes_provider else "",
                    wan1_notes_speed if wan1_notes_speed else "",
                    wan2_notes_provider if wan2_notes_provider else "",
                    wan2_notes_speed if wan2_notes_speed else "",
                    dsr_ip if dsr_ip else "",
                    wan_port,
                    wan1_ip if wan1_ip else "",
                    wan1_arin if wan1_arin else "",
                    wan2_ip if wan2_ip else "",
                    wan2_arin if wan2_arin else ""
                ])
    
    cursor.close()
    conn.close()
    
    # Print summary
    print(f"\nAnalysis complete!")
    print(f"Total NO MATCH cases: {no_match_count}")
    print(f"\nResults saved to: {output_file}")
    
    # Show first few examples with notes
    print("\nShowing first 5 no-match cases with their Meraki notes:")
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if count >= 5:
                break
            print(f"\n{row['Site Name']} ({row['Site ID']}):")
            print(f"  DSR: {row['DSR Provider']}")
            print(f"  ARIN: {row['ARIN Provider']}")
            print(f"  Notes: {row['Meraki Notes (Parsed)'][:100]}..." if len(row['Meraki Notes (Parsed)']) > 100 else f"  Notes: {row['Meraki Notes (Parsed)']}")
            print(f"  WAN1 Notes: {row['WAN1 Notes Provider']} ({row['WAN1 Notes Speed']})")
            print(f"  WAN2 Notes: {row['WAN2 Notes Provider']} ({row['WAN2 Notes Speed']})")
            count += 1

if __name__ == "__main__":
    main()