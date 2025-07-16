#!/usr/bin/env python3
"""
Update ARIN resolution for unresolved IPs in the database
"""

import psycopg2
import requests
import json
import time
import logging
from datetime import datetime, timezone
import ipaddress

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_json(url, context=""):
    """Fetch JSON data from a URL with error handling."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout for {context}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error {e.response.status_code} for {context}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {context}: {type(e).__name__}: {e}")
        return None

def parse_arin_response(rdap_data):
    """Parse the ARIN RDAP response to extract the provider name."""
    from datetime import datetime
    
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
                                action = event.get("eventAction", "").lower()
                                if action in ("registration", "last changed"):
                                    date_str = event.get("eventDate")
                                    if date_str:
                                        try:
                                            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                        except:
                                            try:
                                                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
                                            except:
                                                continue
                                        if latest_date is None or dt > latest_date:
                                            latest_date = dt
                            
                            if latest_date is None:
                                latest_date = datetime.min.replace(tzinfo=timezone.utc)
                            
                            org_candidates.append((name, latest_date))
            
            # Check sub-entities
            sub_entities = entity.get("entities", [])
            if sub_entities:
                org_candidates.extend(collect_org_entities(sub_entities))
        
        return org_candidates
    
    # First try network name directly in response
    network_name = rdap_data.get('name')
    
    # Get organization entities
    entities = rdap_data.get('entities', [])
    org_names = []
    if entities:
        org_names = collect_org_entities(entities)
        # Sort by date (newest first)
        org_names.sort(key=lambda x: x[1], reverse=True)
    
    # Special handling for CABLEONE
    if network_name == 'CABLEONE' and org_names:
        for name, _ in org_names:
            if 'cable one' in name.lower():
                return "Cable One, Inc."
    
    # If we have org names, use the first one (newest by date)
    if org_names:
        # Get just the name from the tuple
        clean_name = org_names[0][0]
        clean_name = clean_name.replace("Private Customer -", "").strip()
        
        # Apply known company normalizations
        company_map = {
            "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises", "AT&T Broadband"],
            "Charter Communications": ["Charter Communications LLC", "Charter Communications Inc"],
            "Comcast": ["Comcast Cable Communications, LLC", "Comcast Communications", "Comcast Cable"],
            "Cox Communications": ["Cox Communications Inc.", "Cox Communications"],
            "CenturyLink": ["CenturyLink Communications", "CenturyLink", "Lumen Technologies"],
            "Frontier Communications": ["Frontier Communications Corporation", "Frontier Communications"],
            "Verizon": ["Verizon Communications", "Verizon Internet", "Verizon Business"],
            "Optimum": ["Optimum", "Altice USA", "Suddenlink Communications"],
            "Crown Castle": ["Crown Castle", "CROWN CASTLE"],
            "Cable One, Inc.": ["CABLE ONE, INC.", "Cable One, Inc.", "Cable One"],
        }
        
        for company, variations in company_map.items():
            for variant in variations:
                if variant.lower() in clean_name.lower():
                    return company
        
        return clean_name
    
    # If no org entities found, try to normalize the network name
    if network_name:
        # Check if it's an AT&T network (SBC-*)
        if network_name.startswith('SBC-'):
            return 'AT&T'
        # Check for other patterns
        elif 'CHARTER' in network_name.upper():
            return 'Charter Communications'
        elif 'COMCAST' in network_name.upper():
            return 'Comcast'
        elif 'COX' in network_name.upper():
            return 'Cox Communications'
        elif network_name:
            return network_name
    
    return "Unknown"

def update_arin_resolution():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    logger.info("=== UPDATING ARIN RESOLUTION ===")
    
    # Get all IP addresses that need ARIN resolution
    cursor.execute("""
        SELECT DISTINCT ip_address 
        FROM (
            SELECT wan1_ip as ip_address 
            FROM meraki_inventory 
            WHERE wan1_ip IS NOT NULL 
              AND wan1_ip != '' 
              AND wan1_ip != 'None'
              AND (wan1_arin_provider IS NULL OR wan1_arin_provider = '' OR wan1_arin_provider = 'Unknown')
            
            UNION
            
            SELECT wan2_ip as ip_address 
            FROM meraki_inventory 
            WHERE wan2_ip IS NOT NULL 
              AND wan2_ip != '' 
              AND wan2_ip != 'None'
              AND (wan2_arin_provider IS NULL OR wan2_arin_provider = '' OR wan2_arin_provider = 'Unknown')
        ) AS ips
        WHERE ip_address NOT IN (
            SELECT ip_address 
            FROM rdap_cache 
            WHERE provider_name != 'Unknown'
        )
        ORDER BY ip_address
    """)
    
    ips_to_resolve = cursor.fetchall()
    logger.info(f"Found {len(ips_to_resolve)} IPs needing ARIN resolution")
    
    successful = 0
    failed = 0
    
    for (ip,) in ips_to_resolve:
        # Check if it's a private IP
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                provider = "Private IP"
                logger.debug(f"{ip} is a private IP")
            else:
                # Special handling for Verizon Business range
                if ipaddress.IPv4Address("166.80.0.0") <= ip_obj <= ipaddress.IPv4Address("166.80.255.255"):
                    provider = "Verizon Business"
                else:
                    # Lookup via ARIN RDAP
                    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
                    logger.info(f"Looking up {ip}...")
                    
                    rdap_data = fetch_json(rdap_url, ip)
                    if rdap_data:
                        provider = parse_arin_response(rdap_data)
                        logger.info(f"  ✅ {ip} -> {provider}")
                        successful += 1
                        
                        # Store full RDAP response
                        cursor.execute("""
                            INSERT INTO rdap_cache (ip_address, provider_name, rdap_response, last_queried)
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT (ip_address) DO UPDATE SET
                                provider_name = EXCLUDED.provider_name,
                                rdap_response = EXCLUDED.rdap_response,
                                last_queried = NOW()
                        """, (ip, provider, json.dumps(rdap_data)))
                    else:
                        logger.warning(f"  ❌ Failed to lookup {ip}")
                        failed += 1
                        continue
            
            # Update meraki_inventory with the provider
            cursor.execute("""
                UPDATE meraki_inventory 
                SET wan1_arin_provider = %s 
                WHERE wan1_ip = %s
            """, (provider, ip))
            
            cursor.execute("""
                UPDATE meraki_inventory 
                SET wan2_arin_provider = %s 
                WHERE wan2_ip = %s
            """, (provider, ip))
            
            # Be nice to the API
            time.sleep(0.1)
            
        except ValueError as e:
            logger.error(f"Invalid IP address: {ip}")
            failed += 1
            continue
        
        # Commit every 50 IPs
        if (successful + failed) % 50 == 0:
            conn.commit()
            logger.info(f"Progress: {successful} successful, {failed} failed")
    
    # Final commit
    conn.commit()
    
    # Update enriched_circuits table as well
    logger.info("Updating enriched_circuits with ARIN data...")
    cursor.execute("""
        UPDATE enriched_circuits ec
        SET wan1_arin_org = mi.wan1_arin_provider
        FROM meraki_inventory mi
        WHERE ec.network_name = mi.network_name
          AND mi.wan1_arin_provider IS NOT NULL
          AND mi.wan1_arin_provider != 'Unknown'
    """)
    
    cursor.execute("""
        UPDATE enriched_circuits ec
        SET wan2_arin_org = mi.wan2_arin_provider
        FROM meraki_inventory mi
        WHERE ec.network_name = mi.network_name
          AND mi.wan2_arin_provider IS NOT NULL
          AND mi.wan2_arin_provider != 'Unknown'
    """)
    
    conn.commit()
    
    # Show final statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_ips,
            COUNT(CASE WHEN wan1_arin_provider IS NOT NULL AND wan1_arin_provider != '' AND wan1_arin_provider != 'Unknown' THEN 1 END) as wan1_resolved,
            COUNT(CASE WHEN wan2_arin_provider IS NOT NULL AND wan2_arin_provider != '' AND wan2_arin_provider != 'Unknown' THEN 1 END) as wan2_resolved
        FROM meraki_inventory
        WHERE (wan1_ip IS NOT NULL AND wan1_ip != '' AND wan1_ip != 'None')
           OR (wan2_ip IS NOT NULL AND wan2_ip != '' AND wan2_ip != 'None')
    """)
    
    stats = cursor.fetchone()
    
    logger.info(f"\n=== FINAL STATISTICS ===")
    logger.info(f"Total IPs processed: {successful + failed}")
    logger.info(f"Successful lookups: {successful}")
    logger.info(f"Failed lookups: {failed}")
    logger.info(f"WAN1 IPs resolved: {stats[1]}")
    logger.info(f"WAN2 IPs resolved: {stats[2]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    update_arin_resolution()