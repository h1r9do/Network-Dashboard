#!/usr/bin/env python3
"""
Test ARIN lookup using the same logic as the nightly script
"""
import requests
import ipaddress
from datetime import datetime

def fetch_json(url, context=""):
    """Helper to fetch JSON from URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching {context}: {e}")
    return None

def parse_arin_response(rdap_data):
    """Parse the ARIN RDAP response to extract the provider name."""
    
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
                
                if kind and kind.lower() == "org" and name:
                    # Skip personal names and common role names
                    if not any(keyword in name for keyword in ["Mr.", "Ms.", "Dr.", "Mrs.", "Miss"]):
                        if not any(indicator in name.lower() for indicator in ["admin", "technical", "abuse", "noc"]):
                            # Get the latest event date for this entity
                            latest_date = None
                            for event in entity.get("events", []):
                                date_str = event.get("eventDate", "")
                                if date_str:
                                    try:
                                        event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                                        if latest_date is None or event_date > latest_date:
                                            latest_date = event_date
                                    except:
                                        pass
                            
                            org_candidates.append((name, latest_date))
            
            # Check nested entities
            if "entities" in entity:
                nested_orgs = collect_org_entities(entity["entities"])
                org_candidates.extend(nested_orgs)
        
        return org_candidates
    
    # Try to find organization entities
    entities = rdap_data.get("entities", [])
    org_candidates = collect_org_entities(entities)
    
    # Sort by date (most recent first) and pick the best candidate
    org_candidates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
    
    if org_candidates:
        provider = org_candidates[0][0]
        
        # Clean up common corporate designations
        for suffix in [", LLC", " LLC", ", Inc.", " Inc.", " Corporation", " Corp.", " Company", " Co."]:
            if provider.endswith(suffix):
                provider = provider[:-len(suffix)]
        
        # Map common providers
        if "CELLCO-PART" in provider:
            provider = "Verizon Wireless"
        elif "MCICS" in provider:
            provider = "Verizon Wireless"
        
        return provider
    
    # Fallback to network name
    network_name = rdap_data.get("name", "")
    if network_name:
        return network_name
    
    return "Unknown"

def get_provider_for_ip(ip):
    """Determine the ISP provider name for a given IP address using RDAP."""
    try:
        ip_addr = ipaddress.ip_address(ip)
        
        # Special handling for 166.80.0.0/16 range
        if ipaddress.IPv4Address("166.80.0.0") <= ip_addr <= ipaddress.IPv4Address("166.80.255.255"):
            return "Verizon Business"
    except ValueError:
        return "Invalid IP"
    
    if ip_addr.is_private:
        return "Private IP"
    
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        return "Unknown"
    
    return parse_arin_response(rdap_data)

# Test the IPs
test_ips = [
    "66.190.127.170",    # WAN1 public
    "192.168.0.151",     # WAN2 private
    "166.168.184.98",    # DDNS resolved IP
    "166.248.19.127"     # Earlier mentioned Verizon IP
]

print("=== Testing ARIN Lookup Logic ===\n")

for ip in test_ips:
    provider = get_provider_for_ip(ip)
    print(f"{ip} → {provider}")