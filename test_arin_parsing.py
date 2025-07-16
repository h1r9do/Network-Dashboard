#!/usr/bin/env python3
"""Test ARIN parsing for CAN 24 IP"""

import requests
import json
import re
from datetime import datetime

def parse_arin_response_enhanced(rdap_data):
    """Parse ARIN response with same logic as nightly script"""
    
    def collect_org_entities(entities):
        """Recursively collect organization names with their latest event dates"""
        org_candidates = []
        
        for entity in entities:
            vcard = entity.get("vcardArray", [])
            if vcard and isinstance(vcard, list) and len(vcard) > 1:
                vcard_props = vcard[1]
                name = None
                kind = None
                
                for prop in vcard_props:
                    if len(prop) >= 4:
                        label = prop[0]
                        value = prop[3]
                        if label == "fn":
                            name = value
                        elif label == "kind":
                            kind = value
                
                # Only use organization entities, not person entities
                if name and kind == "org":
                    # Get the latest event date
                    latest_date = datetime.min
                    events = entity.get("events", [])
                    for event in events:
                        event_date_str = event.get("eventDate", "")
                        if event_date_str:
                            try:
                                event_date = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
                                if event_date > latest_date:
                                    latest_date = event_date
                            except:
                                pass
                    
                    org_candidates.append((name, latest_date))
        
        # Check sub-entities
        sub_entities = entity.get("entities", [])
        if sub_entities:
            org_candidates.extend(collect_org_entities(sub_entities))
        
        return org_candidates
    
    # First try network name directly
    network_name = rdap_data.get('name')
    print(f"Network name: {network_name}")
    
    # Get organization entities
    entities = rdap_data.get('entities', [])
    org_names = []
    if entities:
        org_names = collect_org_entities(entities)
        # Sort by date (newest first)
        org_names.sort(key=lambda x: x[1], reverse=True)
        print(f"Found {len(org_names)} org entities")
        for name, date in org_names:
            print(f"  - {name} (date: {date})")
    
    # Check if it's an AT&T network (SBC-*)
    if network_name and network_name.startswith('SBC-'):
        print("Network name starts with SBC-, returning AT&T")
        return 'AT&T'
    
    # If we have org names, use the first one (newest by date)
    if org_names:
        clean_name = org_names[0][0]  # Extract name from (name, date) tuple
        print(f"Using org name: {clean_name}")
        clean_name = re.sub(r"^Private Customer -\s*", "", clean_name).strip()
        
        # Apply known company normalizations
        company_map = {
            "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises, LLC", "AT&T Broadband", 
                     "IPAdmin-ATT Internet Services", "AT&T Communications", "AT&T Business"],
        }
        
        for company, variations in company_map.items():
            for variant in variations:
                if variant.lower() in clean_name.lower():
                    print(f"Found match for {company}")
                    return company
        
        return clean_name
    
    return 'Unknown'

# Test with CAN 24's IP
ip = "45.19.143.81"
print(f"Testing IP: {ip}\n")

response = requests.get(f"https://rdap.arin.net/registry/ip/{ip}")
if response.status_code == 200:
    data = response.json()
    result = parse_arin_response_enhanced(data)
    print(f"\nFinal result: {result}")
else:
    print(f"Error: {response.status_code}")