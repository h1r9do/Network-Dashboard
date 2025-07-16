#!/usr/bin/env python3
"""
Analyze which sites have single speed values (corrupted) vs full format
"""

import psycopg2
import re
from collections import defaultdict

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def analyze_speed_formats():
    """Analyze all speed formats in enriched_circuits table"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all enriched circuits data
    cursor.execute("""
        SELECT 
            network_name,
            wan1_provider,
            wan1_speed,
            wan2_provider,
            wan2_speed
        FROM enriched_circuits
        ORDER BY network_name
    """)
    
    single_speed_pattern = re.compile(r'^\d+\.?\d*\s*M$')  # Matches "300.0 M" or "300M"
    full_speed_pattern = re.compile(r'^\d+\.?\d*M?\s*x\s*\d+\.?\d*M?$')  # Matches "300.0M x 30.0M"
    
    corrupted_wan1 = []
    corrupted_wan2 = []
    both_corrupted = []
    statistics = defaultdict(int)
    
    print("=== ANALYZING SPEED FORMATS ===\n")
    
    for row in cursor.fetchall():
        network_name = row[0]
        wan1_provider = row[1] or ''
        wan1_speed = row[2] or ''
        wan2_provider = row[3] or ''
        wan2_speed = row[4] or ''
        
        wan1_corrupted = False
        wan2_corrupted = False
        
        # Check WAN1
        if wan1_speed:
            if wan1_speed in ['Cell', 'Satellite', '']:
                statistics['wan1_special'] += 1
            elif single_speed_pattern.match(wan1_speed):
                wan1_corrupted = True
                statistics['wan1_single_speed'] += 1
            elif full_speed_pattern.match(wan1_speed):
                statistics['wan1_full_format'] += 1
            else:
                statistics['wan1_other'] += 1
        else:
            statistics['wan1_empty'] += 1
        
        # Check WAN2
        if wan2_speed:
            if wan2_speed in ['Cell', 'Satellite', '']:
                statistics['wan2_special'] += 1
            elif single_speed_pattern.match(wan2_speed):
                wan2_corrupted = True
                statistics['wan2_single_speed'] += 1
            elif full_speed_pattern.match(wan2_speed):
                statistics['wan2_full_format'] += 1
            else:
                statistics['wan2_other'] += 1
        else:
            statistics['wan2_empty'] += 1
        
        # Track corrupted sites
        if wan1_corrupted and wan2_corrupted:
            both_corrupted.append({
                'network': network_name,
                'wan1': f"{wan1_provider}: {wan1_speed}",
                'wan2': f"{wan2_provider}: {wan2_speed}"
            })
        elif wan1_corrupted:
            corrupted_wan1.append({
                'network': network_name,
                'wan1': f"{wan1_provider}: {wan1_speed}",
                'wan2': f"{wan2_provider}: {wan2_speed}"
            })
        elif wan2_corrupted:
            corrupted_wan2.append({
                'network': network_name,
                'wan1': f"{wan1_provider}: {wan1_speed}",
                'wan2': f"{wan2_provider}: {wan2_speed}"
            })
    
    # Print statistics
    print("=== STATISTICS ===")
    print(f"Total sites analyzed: {cursor.rowcount}")
    print("\nWAN1 Speed Formats:")
    print(f"  - Single speed (corrupted): {statistics['wan1_single_speed']}")
    print(f"  - Full format (correct):    {statistics['wan1_full_format']}")
    print(f"  - Cell/Satellite:          {statistics['wan1_special']}")
    print(f"  - Empty:                   {statistics['wan1_empty']}")
    print(f"  - Other:                   {statistics['wan1_other']}")
    
    print("\nWAN2 Speed Formats:")
    print(f"  - Single speed (corrupted): {statistics['wan2_single_speed']}")
    print(f"  - Full format (correct):    {statistics['wan2_full_format']}")
    print(f"  - Cell/Satellite:          {statistics['wan2_special']}")
    print(f"  - Empty:                   {statistics['wan2_empty']}")
    print(f"  - Other:                   {statistics['wan2_other']}")
    
    print(f"\n=== CORRUPTED SITES SUMMARY ===")
    print(f"Both WAN1 & WAN2 corrupted: {len(both_corrupted)}")
    print(f"Only WAN1 corrupted:        {len(corrupted_wan1)}")
    print(f"Only WAN2 corrupted:        {len(corrupted_wan2)}")
    print(f"TOTAL AFFECTED SITES:       {len(both_corrupted) + len(corrupted_wan1) + len(corrupted_wan2)}")
    
    # List sites with both corrupted
    if both_corrupted:
        print(f"\n=== SITES WITH BOTH WAN1 & WAN2 CORRUPTED ({len(both_corrupted)}) ===")
        for site in both_corrupted[:20]:  # Show first 20
            print(f"{site['network']}:")
            print(f"  WAN1: {site['wan1']}")
            print(f"  WAN2: {site['wan2']}")
        if len(both_corrupted) > 20:
            print(f"  ... and {len(both_corrupted) - 20} more")
    
    # List sites with only WAN1 corrupted
    if corrupted_wan1:
        print(f"\n=== SITES WITH ONLY WAN1 CORRUPTED ({len(corrupted_wan1)}) ===")
        for site in corrupted_wan1[:10]:  # Show first 10
            print(f"{site['network']}:")
            print(f"  WAN1: {site['wan1']} ❌")
            print(f"  WAN2: {site['wan2']} ✓")
        if len(corrupted_wan1) > 10:
            print(f"  ... and {len(corrupted_wan1) - 10} more")
    
    # List sites with only WAN2 corrupted
    if corrupted_wan2:
        print(f"\n=== SITES WITH ONLY WAN2 CORRUPTED ({len(corrupted_wan2)}) ===")
        for site in corrupted_wan2[:10]:  # Show first 10
            print(f"{site['network']}:")
            print(f"  WAN1: {site['wan1']} ✓")
            print(f"  WAN2: {site['wan2']} ❌")
        if len(corrupted_wan2) > 10:
            print(f"  ... and {len(corrupted_wan2) - 10} more")
    
    # Check for patterns
    print("\n=== PATTERN ANALYSIS ===")
    
    # Check if corruption is related to specific providers
    provider_corruption = defaultdict(lambda: {'total': 0, 'corrupted': 0})
    
    cursor.execute("""
        SELECT 
            wan1_provider,
            wan1_speed,
            wan2_provider,
            wan2_speed
        FROM enriched_circuits
        WHERE wan1_speed IS NOT NULL OR wan2_speed IS NOT NULL
    """)
    
    for row in cursor.fetchall():
        wan1_provider = row[0] or 'Unknown'
        wan1_speed = row[1] or ''
        wan2_provider = row[2] or 'Unknown'
        wan2_speed = row[3] or ''
        
        if wan1_speed and wan1_speed not in ['Cell', 'Satellite']:
            provider_corruption[wan1_provider]['total'] += 1
            if single_speed_pattern.match(wan1_speed):
                provider_corruption[wan1_provider]['corrupted'] += 1
        
        if wan2_speed and wan2_speed not in ['Cell', 'Satellite']:
            provider_corruption[wan2_provider]['total'] += 1
            if single_speed_pattern.match(wan2_speed):
                provider_corruption[wan2_provider]['corrupted'] += 1
    
    print("\nCorruption by Provider:")
    for provider, stats in sorted(provider_corruption.items(), key=lambda x: x[1]['corrupted'], reverse=True)[:10]:
        if stats['total'] > 0:
            percentage = (stats['corrupted'] / stats['total']) * 100
            print(f"  {provider}: {stats['corrupted']}/{stats['total']} ({percentage:.1f}%)")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_speed_formats()