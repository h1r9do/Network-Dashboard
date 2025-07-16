#!/usr/bin/env python3
"""
Test script to trace speed data corruption in nightly enrichment process
"""

import json
import psycopg2
import re
from datetime import datetime

# Copy the functions from nightly script to avoid import issues
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

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def test_speed_processing():
    """Test the speed processing for CAN_00"""
    results = {
        "test_time": datetime.now().isoformat(),
        "site": "CAN_00",
        "steps": []
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Step 1: Get DSR data
    print("Step 1: Getting DSR data from circuits table...")
    cursor.execute("""
        SELECT site_name, circuit_purpose, provider_name, 
               details_ordered_service_speed, ip_address_start
        FROM circuits 
        WHERE site_name = 'CAN00' AND status = 'Enabled'
        ORDER BY circuit_purpose
    """)
    
    dsr_data = []
    for row in cursor.fetchall():
        dsr_data.append({
            "site": row[0],
            "purpose": row[1],
            "provider": row[2],
            "speed_from_dsr": row[3],
            "ip": row[4]
        })
    
    results["steps"].append({
        "step": "1_dsr_data",
        "description": "Raw DSR data from circuits table",
        "data": dsr_data
    })
    
    # Step 2: Get Meraki notes
    print("Step 2: Getting Meraki device notes...")
    cursor.execute("""
        SELECT network_name, device_notes, wan1_ip, wan2_ip
        FROM meraki_inventory 
        WHERE network_name = 'CAN_00'
    """)
    
    meraki_row = cursor.fetchone()
    if meraki_row:
        notes = meraki_row[1]
        results["steps"].append({
            "step": "2_meraki_notes",
            "description": "Raw Meraki device notes",
            "data": {
                "network": meraki_row[0],
                "raw_notes": notes,
                "wan1_ip": meraki_row[2],
                "wan2_ip": meraki_row[3]
            }
        })
        
        # Step 3: Parse notes
        print("Step 3: Parsing Meraki notes...")
        wan1_provider, wan1_speed, wan2_provider, wan2_speed = parse_raw_notes(notes)
        results["steps"].append({
            "step": "3_parsed_notes",
            "description": "Parsed notes using parse_raw_notes()",
            "data": {
                "wan1_provider": wan1_provider,
                "wan1_speed": wan1_speed,
                "wan2_provider": wan2_provider,
                "wan2_speed": wan2_speed
            }
        })
    
    # Step 4: Test speed reformatting
    print("Step 4: Testing speed reformatting...")
    test_speeds = [
        ("300.0M x 30.0M", "Comcast"),
        ("300.0M x 300.0M", "AT&T"),
        ("250.0M x 25.0M", "Comcast Workplace"),
        ("Cell", "VZW Cell"),
        ("Satellite", "Starlink")
    ]
    
    reformat_results = []
    for speed, provider in test_speeds:
        reformatted = reformat_speed(speed, provider)
        reformat_results.append({
            "input_speed": speed,
            "provider": provider,
            "output_speed": reformatted
        })
    
    results["steps"].append({
        "step": "4_reformat_speed_test",
        "description": "Testing reformat_speed() function",
        "data": reformat_results
    })
    
    # Step 5: Simulate the enrichment logic
    print("Step 5: Simulating enrichment logic...")
    
    # Get DSR circuits for CAN00
    dsr_circuits = [
        {"provider": "Comcast Workplace", "speed": "300.0M x 30.0M", "purpose": "Primary", "ip": "96.81.183.205"},
        {"provider": "AT&T Broadband II", "speed": "300.0M x 300.0M", "purpose": "Secondary", "ip": "108.86.147.217"}
    ]
    
    # Simulate WAN1 processing
    wan1_dsr = dsr_circuits[0]  # Matched by IP
    wan1_speed_to_use = wan1_dsr['speed'] if wan1_dsr else wan1_speed
    wan1_speed_final = reformat_speed(wan1_speed_to_use, "Comcast")
    
    # Simulate WAN2 processing
    wan2_dsr = dsr_circuits[1]  # Matched by IP
    wan2_speed_to_use = wan2_dsr['speed'] if wan2_dsr else wan2_speed
    wan2_speed_final = reformat_speed(wan2_speed_to_use, "AT&T")
    
    results["steps"].append({
        "step": "5_enrichment_simulation",
        "description": "Simulating the enrichment process",
        "data": {
            "wan1": {
                "dsr_match": wan1_dsr,
                "speed_to_use": wan1_speed_to_use,
                "speed_final": wan1_speed_final
            },
            "wan2": {
                "dsr_match": wan2_dsr,
                "speed_to_use": wan2_speed_to_use,
                "speed_final": wan2_speed_final
            }
        }
    })
    
    # Step 6: Check current enriched_circuits
    print("Step 6: Checking current enriched_circuits table...")
    cursor.execute("""
        SELECT wan1_provider, wan1_speed, wan2_provider, wan2_speed
        FROM enriched_circuits 
        WHERE network_name = 'CAN_00'
    """)
    
    enriched_row = cursor.fetchone()
    if enriched_row:
        results["steps"].append({
            "step": "6_current_enriched",
            "description": "Current enriched_circuits table data",
            "data": {
                "wan1_provider": enriched_row[0],
                "wan1_speed": enriched_row[1],
                "wan2_provider": enriched_row[2],
                "wan2_speed": enriched_row[3]
            }
        })
    
    cursor.close()
    conn.close()
    
    # Summary
    results["summary"] = {
        "dsr_has_full_speed": all("x" in d["speed_from_dsr"] for d in dsr_data),
        "meraki_has_full_speed": "x" in wan1_speed and "x" in wan2_speed if 'wan1_speed' in locals() else False,
        "reformat_corrupts_speed": not any("x" in r["output_speed"] for r in reformat_results if "x" in r["input_speed"]),
        "enriched_missing_upload": enriched_row and "x" not in enriched_row[1] and "x" not in enriched_row[3] if enriched_row else False
    }
    
    return results

if __name__ == "__main__":
    print("Testing speed corruption in enrichment process...")
    results = test_speed_processing()
    
    # Write to JSON
    output_file = "/usr/local/bin/speed_corruption_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults written to: {output_file}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"DSR has full speed format: {results['summary']['dsr_has_full_speed']}")
    print(f"Meraki notes have full speed: {results['summary']['meraki_has_full_speed']}")
    print(f"reformat_speed() corrupts data: {results['summary']['reformat_corrupts_speed']}")
    print(f"Enriched table missing upload speed: {results['summary']['enriched_missing_upload']}")