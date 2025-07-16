#!/usr/bin/env python3
"""Align WAN1/WAN2 interfaces with DSR circuits using ARIN provider data"""

import csv
import subprocess
from datetime import datetime
from collections import defaultdict

print("=== WAN Interface Alignment Using ARIN Data ===\n")

# Provider name normalization mapping
PROVIDER_MAPPING = {
    # AT&T variations
    'at&t': ['at&t', 'att', 'at and t', 'at&t broadband', 'at&t broadband ii', 'at&t corp', 'at&t services'],
    # Spectrum/Charter variations
    'spectrum': ['spectrum', 'charter', 'charter communications', 'charter spectrum', 'twc', 'time warner'],
    # Comcast variations
    'comcast': ['comcast', 'comcast business', 'comcast workplace', 'comcast cable', 'xfinity'],
    # Cox variations
    'cox': ['cox', 'cox business', 'cox communications', 'cox business/boi'],
    # Verizon variations
    'verizon': ['verizon', 'vzw', 'verizon wireless', 'verizon business', 'vzb', 'mci'],
    # CenturyLink/Lumen variations
    'centurylink': ['centurylink', 'lumen', 'level 3', 'level3', 'qwest'],
    # Frontier variations
    'frontier': ['frontier', 'frontier communications', 'frontier fios'],
    # Windstream variations
    'windstream': ['windstream', 'windstream communications', 'paetec'],
    # T-Mobile variations
    'tmobile': ['t-mobile', 'tmobile', 't mobile', 'sprint'],
}

def normalize_provider(provider_name):
    """Normalize provider name for better matching"""
    if not provider_name:
        return None
    
    provider_lower = provider_name.lower().strip()
    
    # Check against mapping
    for normalized, variations in PROVIDER_MAPPING.items():
        for variation in variations:
            if variation in provider_lower:
                return normalized
    
    # If no match, return cleaned version
    return provider_lower.split()[0] if provider_lower else None

# Query to get all data for alignment analysis
query = """
WITH circuit_wan_analysis AS (
    SELECT 
        c.site_name,
        c.site_id,
        c.circuit_purpose,
        c.provider_name as dsr_provider,
        c.details_service_speed as dsr_speed,
        c.billing_monthly_cost as dsr_cost,
        c.ip_address_start as dsr_ip,
        -- WAN1 data
        ec.wan1_provider as meraki_wan1_provider,
        mi.wan1_ip,
        mi.wan1_arin_provider,
        -- WAN2 data
        ec.wan2_provider as meraki_wan2_provider,
        mi.wan2_ip,
        mi.wan2_arin_provider,
        -- Current matching
        CASE 
            WHEN LOWER(c.provider_name) = LOWER(ec.wan1_provider) THEN 'WAN1'
            WHEN LOWER(c.provider_name) = LOWER(ec.wan2_provider) THEN 'WAN2'
            ELSE 'No Match'
        END as current_match
    FROM circuits c
    LEFT JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
    LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    WHERE c.status = 'Enabled'
    AND c.data_source = 'csv_import'
    AND mi.network_name IS NOT NULL
    AND mi.device_tags @> ARRAY['Discount-Tire']::text[]
    ORDER BY c.site_name, c.circuit_purpose
)
SELECT * FROM circuit_wan_analysis;
"""

print("Querying database for alignment analysis...")
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-c', query],
    capture_output=True, text=True
)

if result.returncode != 0:
    print(f"Query error: {result.stderr}")
    exit(1)

# Parse results
circuits = []
for line in result.stdout.strip().split('\n'):
    if line:
        parts = line.split('\t')
        if len(parts) >= 13:
            circuits.append({
                'site_name': parts[0],
                'site_id': parts[1],
                'circuit_purpose': parts[2],
                'dsr_provider': parts[3],
                'dsr_speed': parts[4],
                'dsr_cost': parts[5],
                'dsr_ip': parts[6],
                'meraki_wan1_provider': parts[7],
                'wan1_ip': parts[8],
                'wan1_arin_provider': parts[9],
                'meraki_wan2_provider': parts[10],
                'wan2_ip': parts[11],
                'wan2_arin_provider': parts[12],
                'current_match': parts[13] if len(parts) > 13 else 'No Match'
            })

print(f"Analyzing {len(circuits)} circuits...")

# Analyze alignment
alignment_stats = {
    'total': len(circuits),
    'current_wan1_match': 0,
    'current_wan2_match': 0,
    'current_no_match': 0,
    'arin_suggested_wan1': 0,
    'arin_suggested_wan2': 0,
    'arin_confirmed_current': 0,
    'arin_suggests_switch': 0,
    'no_arin_data': 0
}

realignment_suggestions = []

for circuit in circuits:
    # Normalize provider names
    dsr_norm = normalize_provider(circuit['dsr_provider'])
    wan1_meraki_norm = normalize_provider(circuit['meraki_wan1_provider'])
    wan2_meraki_norm = normalize_provider(circuit['meraki_wan2_provider'])
    wan1_arin_norm = normalize_provider(circuit['wan1_arin_provider'])
    wan2_arin_norm = normalize_provider(circuit['wan2_arin_provider'])
    
    # Current match status
    if circuit['current_match'] == 'WAN1':
        alignment_stats['current_wan1_match'] += 1
    elif circuit['current_match'] == 'WAN2':
        alignment_stats['current_wan2_match'] += 1
    else:
        alignment_stats['current_no_match'] += 1
    
    # ARIN-based alignment suggestion
    arin_suggestion = None
    reason = ""
    
    if not wan1_arin_norm and not wan2_arin_norm:
        alignment_stats['no_arin_data'] += 1
        continue
    
    # Check if ARIN matches DSR provider
    wan1_arin_match = dsr_norm == wan1_arin_norm if (dsr_norm and wan1_arin_norm) else False
    wan2_arin_match = dsr_norm == wan2_arin_norm if (dsr_norm and wan2_arin_norm) else False
    
    if wan1_arin_match and not wan2_arin_match:
        arin_suggestion = 'WAN1'
        alignment_stats['arin_suggested_wan1'] += 1
        reason = f"ARIN WAN1 ({circuit['wan1_arin_provider']}) matches DSR ({circuit['dsr_provider']})"
    elif wan2_arin_match and not wan1_arin_match:
        arin_suggestion = 'WAN2'
        alignment_stats['arin_suggested_wan2'] += 1
        reason = f"ARIN WAN2 ({circuit['wan2_arin_provider']}) matches DSR ({circuit['dsr_provider']})"
    elif wan1_arin_match and wan2_arin_match:
        # Both match - use current assignment or speed to decide
        if circuit['current_match'] in ['WAN1', 'WAN2']:
            arin_suggestion = circuit['current_match']
            reason = "Both ARIN providers match DSR, keeping current assignment"
        else:
            arin_suggestion = 'WAN1'  # Default to WAN1
            reason = "Both ARIN providers match DSR, defaulting to WAN1"
    
    # Compare with current assignment
    if arin_suggestion:
        if arin_suggestion == circuit['current_match']:
            alignment_stats['arin_confirmed_current'] += 1
        else:
            alignment_stats['arin_suggests_switch'] += 1
            realignment_suggestions.append({
                **circuit,
                'arin_suggestion': arin_suggestion,
                'reason': reason,
                'confidence': 'High' if (wan1_arin_match ^ wan2_arin_match) else 'Medium'
            })

# Write results
output_file = f'/usr/local/bin/Main/wan_alignment_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
suggestions_file = f'/usr/local/bin/Main/wan_realignment_suggestions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

# Write full analysis
fieldnames = [
    'site_name', 'site_id', 'circuit_purpose', 'dsr_provider', 'dsr_speed', 'dsr_cost',
    'dsr_ip', 'meraki_wan1_provider', 'wan1_ip', 'wan1_arin_provider',
    'meraki_wan2_provider', 'wan2_ip', 'wan2_arin_provider', 'current_match',
    'normalized_dsr_provider', 'normalized_wan1_arin', 'normalized_wan2_arin',
    'wan1_arin_matches_dsr', 'wan2_arin_matches_dsr'
]

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for circuit in circuits:
        row = circuit.copy()
        row['normalized_dsr_provider'] = normalize_provider(circuit['dsr_provider'])
        row['normalized_wan1_arin'] = normalize_provider(circuit['wan1_arin_provider'])
        row['normalized_wan2_arin'] = normalize_provider(circuit['wan2_arin_provider'])
        
        dsr_norm = row['normalized_dsr_provider']
        wan1_arin_norm = row['normalized_wan1_arin']
        wan2_arin_norm = row['normalized_wan2_arin']
        
        row['wan1_arin_matches_dsr'] = 'Yes' if dsr_norm == wan1_arin_norm and dsr_norm else 'No'
        row['wan2_arin_matches_dsr'] = 'Yes' if dsr_norm == wan2_arin_norm and dsr_norm else 'No'
        
        writer.writerow(row)

# Write realignment suggestions
if realignment_suggestions:
    suggestion_fields = [
        'site_name', 'circuit_purpose', 'dsr_provider', 'current_match',
        'arin_suggestion', 'reason', 'confidence', 'wan1_arin_provider', 
        'wan2_arin_provider', 'meraki_wan1_provider', 'meraki_wan2_provider'
    ]
    
    with open(suggestions_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=suggestion_fields)
        writer.writeheader()
        
        for suggestion in realignment_suggestions:
            writer.writerow({k: suggestion.get(k, '') for k in suggestion_fields})

# Print summary
print(f"\n=== Alignment Analysis Summary ===")
print(f"Total circuits analyzed: {alignment_stats['total']}")
print(f"\nCurrent Meraki-based matching:")
print(f"- Matched to WAN1: {alignment_stats['current_wan1_match']}")
print(f"- Matched to WAN2: {alignment_stats['current_wan2_match']}")
print(f"- No match: {alignment_stats['current_no_match']}")
print(f"\nARIN-based analysis:")
print(f"- ARIN suggests WAN1: {alignment_stats['arin_suggested_wan1']}")
print(f"- ARIN suggests WAN2: {alignment_stats['arin_suggested_wan2']}")
print(f"- ARIN confirms current: {alignment_stats['arin_confirmed_current']}")
print(f"- ARIN suggests realignment: {alignment_stats['arin_suggests_switch']}")
print(f"- No ARIN data: {alignment_stats['no_arin_data']}")

print(f"\nFiles created:")
print(f"1. Full analysis: {output_file}")
print(f"2. Realignment suggestions: {suggestions_file} ({len(realignment_suggestions)} suggestions)")

# Show examples of suggested realignments
if realignment_suggestions:
    print(f"\n=== Example Realignment Suggestions (first 5) ===")
    for i, sugg in enumerate(realignment_suggestions[:5]):
        print(f"\n{i+1}. {sugg['site_name']} - {sugg['circuit_purpose']}")
        print(f"   DSR Provider: {sugg['dsr_provider']}")
        print(f"   Current: {sugg['current_match']} -> Suggested: {sugg['arin_suggestion']}")
        print(f"   Reason: {sugg['reason']}")
        print(f"   Confidence: {sugg['confidence']}")