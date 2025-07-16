#!/usr/bin/env python3
"""
Test enhanced provider matching using both ARIN data and Meraki notes
Shows how combining all data sources improves match rate
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

# Enhanced provider mapping based on our analysis
ENHANCED_PROVIDER_MAPPING = {
    # Rebrands
    "brightspeed": "centurylink",
    "sparklight": "cable one",
    "cincinnati bell": "altafiber",
    "lumen": "centurylink",
    
    # Business divisions
    "comcast workplace": "comcast",
    "comcast workplace cable": "comcast",
    "cox business/boi": "cox communications",
    "cox business boi": "cox communications",
    "cox business": "cox communications",
    "at&t broadband ii": "at&t",
    "at&t abf": "at&t",
    "at&t adi": "at&t",
    "verizon business": "verizon",
    
    # Brand names
    "spectrum": "charter communications",
    "charter": "charter communications",
    "altice west": "optimum",
    "lightpath": "optimum",
    
    # Known aliases
    "transworld": "fairnet llc",
    "yelcot communications": "yelcot telephone company",
    "orbitel communications": "orbitel communications, llc",
    "mediacom/boi": "mediacom",
    "centurylink/embarq": "centurylink",
    "centurylink/qwest": "centurylink",
    "allo communications": "allo communications llc",
    "starlink": "spacex services, inc.",
    "digi cellular": "digi",
    "verizon cell": "verizon",
    "cell": "verizon",
    
    # Service suffixes
    "centurylink fiber plus": "centurylink",
    "agg comcast": "comcast",
    "comcastagg comcast": "comcast",
    "comcastagg clink dsl": "centurylink",
    "wyyerd fiber": "wyyerd group llc",
}

def get_db_connection():
    """Get database connection using config"""
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

def normalize_provider_enhanced(provider):
    """Enhanced normalization that handles all edge cases"""
    if not provider:
        return ""
    
    # Convert to lowercase and strip
    provider = str(provider).lower().strip()
    
    # Handle EB2- prefix specially
    if provider.startswith('eb2-'):
        # Extract the actual provider name after EB2-
        provider = provider[4:]  # Remove 'eb2-'
        # Remove service type suffixes
        provider = re.sub(r'\s*(dsl|fiber|cable|kinetic)$', '', provider)
    
    # Remove other common prefixes
    provider = re.sub(r'^(dsr|agg|comcastagg|not\s+dsr|--|-)\s+', '', provider)
    
    # Remove service type suffixes and descriptors
    provider = re.sub(r'\s*(extended\s+cable|workplace|broadband\s+ii|fiber\s+plus|/boi|/embarq|/qwest|cable|dsl|fiber)$', '', provider)
    
    # Remove special characters but keep important ones
    provider = re.sub(r'[^\w\s&/-]', ' ', provider)
    provider = re.sub(r'\s+', ' ', provider).strip()
    
    return provider

def parse_notes_for_provider(raw_notes):
    """Extract provider information from Meraki notes"""
    if not raw_notes or not raw_notes.strip():
        return None, None
    
    # Fix literal \\n strings
    if '\\n' in raw_notes and '\n' not in raw_notes:
        raw_notes = raw_notes.replace('\\n', '\n')
    
    # Look for WAN1 and WAN2 patterns
    wan1_provider = None
    wan2_provider = None
    
    lines = raw_notes.split('\n')
    for line in lines:
        line = line.strip()
        
        # WAN1 pattern
        if 'wan1' in line.lower():
            # Extract provider name after WAN1
            match = re.search(r'wan1[:\s]*([^,\n]+)', line, re.IGNORECASE)
            if match:
                wan1_provider = match.group(1).strip()
        
        # WAN2 pattern
        elif 'wan2' in line.lower():
            # Extract provider name after WAN2
            match = re.search(r'wan2[:\s]*([^,\n]+)', line, re.IGNORECASE)
            if match:
                wan2_provider = match.group(1).strip()
    
    return wan1_provider, wan2_provider

def enhanced_match_providers(dsr_provider, arin_provider, notes_provider=None):
    """
    Enhanced matching that uses ARIN data, notes, and mapping table
    Returns: (match_status, match_score, reason, matched_source)
    """
    if not dsr_provider:
        return "No Match", 0, "Missing DSR provider", ""
    
    # Normalize all providers
    dsr_norm = normalize_provider_enhanced(dsr_provider)
    arin_norm = normalize_provider_enhanced(arin_provider) if arin_provider else ""
    notes_norm = normalize_provider_enhanced(notes_provider) if notes_provider else ""
    
    # Check mapping table first
    if dsr_norm in ENHANCED_PROVIDER_MAPPING:
        mapped_provider = ENHANCED_PROVIDER_MAPPING[dsr_norm]
        
        # Check against ARIN
        if arin_norm and (mapped_provider == arin_norm or arin_norm == mapped_provider):
            return "Match", 100, "Mapped match with ARIN", "ARIN (mapped)"
        
        # Check against notes
        if notes_norm and (mapped_provider == notes_norm or notes_norm == mapped_provider):
            return "Match", 95, "Mapped match with notes", "Notes (mapped)"
    
    # Direct match with ARIN
    if arin_norm and dsr_norm == arin_norm:
        return "Match", 100, "Direct match with ARIN", "ARIN"
    
    # Direct match with notes
    if notes_norm and dsr_norm == notes_norm:
        return "Match", 95, "Direct match with notes", "Notes"
    
    # Fuzzy match with ARIN
    if arin_norm:
        score1 = fuzz.ratio(dsr_norm, arin_norm)
        score2 = fuzz.partial_ratio(dsr_norm, arin_norm)
        score3 = fuzz.token_sort_ratio(dsr_norm, arin_norm)
        best_arin_score = max(score1, score2, score3)
        
        if best_arin_score >= 80:
            return "Match", best_arin_score, f"Fuzzy match with ARIN ({best_arin_score}%)", "ARIN (fuzzy)"
    
    # Fuzzy match with notes
    if notes_norm:
        score1 = fuzz.ratio(dsr_norm, notes_norm)
        score2 = fuzz.partial_ratio(dsr_norm, notes_norm)
        score3 = fuzz.token_sort_ratio(dsr_norm, notes_norm)
        best_notes_score = max(score1, score2, score3)
        
        if best_notes_score >= 80:
            return "Match", best_notes_score, f"Fuzzy match with notes ({best_notes_score}%)", "Notes (fuzzy)"
    
    # No match found
    return "No Match", 0, "No match found", ""

def main():
    print("Enhanced Provider Matching Analysis - Using ARIN + Meraki Notes")
    print("=" * 80)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query to get DSR circuits with ARIN and notes data
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
                wan2_ip,
                wan2_arin_provider,
                wan2_provider_label
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
            m.wan2_provider_label,
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
    
    # Prepare CSV output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'/usr/local/bin/Main/enhanced_provider_matching_{timestamp}.csv'
    
    # Statistics
    stats = {
        'total': 0,
        'matched': 0,
        'matched_arin': 0,
        'matched_notes': 0,
        'matched_mapping': 0,
        'no_match': 0
    }
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write headers
        writer.writerow([
            'Site Name',
            'Site ID',
            'Circuit Purpose',
            'DSR Provider',
            'ARIN Provider',
            'Notes Provider',
            'Match Status',
            'Match Score',
            'Match Source',
            'Match Reason',
            'DSR Speed',
            'DSR Cost'
        ])
        
        # Process each circuit
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
            wan1_label = row[10]
            wan2_label = row[11]
            wan1_ip = row[12]
            wan1_arin = row[13]
            wan2_ip = row[14]
            wan2_arin = row[15]
            
            stats['total'] += 1
            
            # Try to get provider from notes
            notes_provider = None
            if wan_port == 'WAN1' and wan1_label:
                notes_provider = wan1_label
            elif wan_port == 'WAN2' and wan2_label:
                notes_provider = wan2_label
            elif device_notes:
                # Parse notes for provider info
                wan1_notes, wan2_notes = parse_notes_for_provider(device_notes)
                if wan_port == 'WAN1' and wan1_notes:
                    notes_provider = wan1_notes
                elif wan_port == 'WAN2' and wan2_notes:
                    notes_provider = wan2_notes
            
            # If we don't have a direct IP match, try both WANs
            if wan_port == 'Unknown' and not arin_provider:
                # Try matching against both WANs
                match1 = enhanced_match_providers(dsr_provider, wan1_arin, wan1_label)
                match2 = enhanced_match_providers(dsr_provider, wan2_arin, wan2_label)
                
                # Use the better match
                if match1[1] >= match2[1] and match1[0] == "Match":
                    arin_provider = wan1_arin
                    notes_provider = wan1_label
                    status, score, reason, source = match1
                    wan_port = "WAN1 (Provider Match)"
                elif match2[0] == "Match":
                    arin_provider = wan2_arin
                    notes_provider = wan2_label
                    status, score, reason, source = match2
                    wan_port = "WAN2 (Provider Match)"
                else:
                    status, score, reason, source = match1 if match1[1] > match2[1] else match2
            else:
                # Normal matching
                status, score, reason, source = enhanced_match_providers(dsr_provider, arin_provider, notes_provider)
            
            # Update statistics
            if status == "Match":
                stats['matched'] += 1
                if 'ARIN' in source:
                    stats['matched_arin'] += 1
                elif 'Notes' in source:
                    stats['matched_notes'] += 1
                if 'mapped' in source:
                    stats['matched_mapping'] += 1
            else:
                stats['no_match'] += 1
            
            # Write row
            writer.writerow([
                site_name,
                site_id,
                circuit_purpose,
                dsr_provider,
                arin_provider if arin_provider else "",
                notes_provider if notes_provider else "",
                status,
                score,
                source,
                reason,
                dsr_speed,
                f"${dsr_cost:.2f}" if dsr_cost else ""
            ])
    
    cursor.close()
    conn.close()
    
    # Print summary
    print(f"\nAnalysis complete!")
    print(f"Total circuits analyzed: {stats['total']}")
    print(f"Matched: {stats['matched']} ({stats['matched']/stats['total']*100:.1f}%)")
    print(f"  - Via ARIN: {stats['matched_arin']}")
    print(f"  - Via Notes: {stats['matched_notes']}")
    print(f"  - Via Mapping: {stats['matched_mapping']}")
    print(f"No Match: {stats['no_match']} ({stats['no_match']/stats['total']*100:.1f}%)")
    
    print(f"\nResults saved to: {output_file}")
    
    # Show examples of matches via notes
    print("\nExample matches found via Meraki notes:")
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if 'Notes' in row['Match Source'] and count < 5:
                print(f"  {row['Site Name']}: {row['DSR Provider']} matched with '{row['Notes Provider']}' from notes")
                count += 1

if __name__ == "__main__":
    main()