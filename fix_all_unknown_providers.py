#!/usr/bin/env python3
"""Fix all Unknown ARIN providers using the EXACT working logic from clean_ip_network_cache.py"""

import sys
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import time
import requests
import re
import ipaddress
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection, KNOWN_IPS
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Company normalization map FROM THE WORKING SCRIPT
COMPANY_NAME_MAP = {
    "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises, LLC", "AT&T Broadband", "IPAdmin-ATT Internet Services", "AT&T Communications", "AT&T Business"],
    "Charter Communications": ["Charter Communications LLC", "Charter Communications Inc", "Charter Communications, LLC"],
    "Comcast": ["Comcast Cable Communications, LLC", "Comcast Communications", "Comcast Cable", "Comcast Corporation"],
    "Cox Communications": ["Cox Communications Inc.", "Cox Communications", "Cox Communications Group"],
    "CenturyLink": ["CenturyLink Communications", "CenturyLink", "Lumen Technologies"],
    "Frontier Communications": ["Frontier Communications Corporation", "Frontier Communications", "Frontier Communications Inc."],
    "Level 3": ["Level 3 Parent, LLC", "Level 3 Communications", "Level3"],
    "Verizon": ["Verizon Communications", "Verizon Internet", "Verizon Business", "Verizon Wireless"],
    "Metronet": ["Metronet", "Metronet Fiber"],
    "AT&T Internet": ["AT&T Internet"]
}

def normalize_company_name(name):
    """Normalize company names - FROM WORKING SCRIPT"""
    for company, variations in COMPANY_NAME_MAP.items():
        for variant in variations:
            if variant.lower() in name.lower():
                return company
    return name

def clean_company_name(name):
    """Clean company name - FROM WORKING SCRIPT"""
    return re.sub(r"^Private Customer -\s*", "", name).strip()

def looks_like_personal(name):
    """Check if name looks personal - FROM WORKING SCRIPT"""
    personal_keywords = ["Mr.", "Ms.", "Dr.", "Mrs.", "Miss"]
    if any(keyword in name for keyword in personal_keywords):
        return True
    if len(name.split()) == 2:
        return True
    return False

def collect_org_entities(entity_list):
    """Collect org entities with dates - EXACT LOGIC FROM WORKING SCRIPT"""
    org_candidates = []
    for entity in entity_list:
        vcard = entity.get("vcardArray")
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
                if not looks_like_personal(name):
                    latest_date = None
                    for event in entity.get("events", []):
                        action = event.get("eventAction", "").lower()
                        if action in ("registration", "last changed"):
                            date_str = event.get("eventDate")
                            if date_str:
                                try:
                                    dt = datetime.fromisoformat(date_str)
                                except Exception:
                                    try:
                                        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
                                    except Exception:
                                        continue
                                if latest_date is None or dt > latest_date:
                                    latest_date = dt
                    if latest_date is None:
                        latest_date = datetime.min
                    org_candidates.append((name, latest_date))
        sub_entities = entity.get("entities", [])
        if sub_entities:
            org_candidates.extend(collect_org_entities(sub_entities))
    return org_candidates

def get_provider_from_rdap(ip):
    """Get provider using EXACT working logic"""
    try:
        # Check if private
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private:
            return "Private IP"
        
        # Check Verizon range
        if ipaddress.IPv4Address("166.80.0.0") <= ip_obj <= ipaddress.IPv4Address("166.80.255.255"):
            return "Verizon Business"
        
        # Check known IPs
        if ip in KNOWN_IPS:
            return KNOWN_IPS[ip]
        
        # Fetch RDAP data
        rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
        response = requests.get(rdap_url, timeout=10)
        response.raise_for_status()
        rdap_data = response.json()
        
        # Get entities and find organizations
        entities = rdap_data.get("entities", [])
        if not entities:
            return "Unknown"
        
        # Collect orgs with dates
        orgs = collect_org_entities(entities)
        if not orgs:
            return "Unknown"
        
        # Sort by date (newest first) - THIS IS THE KEY!
        orgs.sort(key=lambda x: x[1], reverse=True)
        
        # Get the best (newest) org name
        best_name = orgs[0][0]
        clean_name = clean_company_name(best_name)
        normalized_name = normalize_company_name(clean_name)
        
        return normalized_name
        
    except Exception as e:
        logger.error(f"Error looking up {ip}: {e}")
        return "Unknown"

def update_all_unknown():
    """Update all Unknown providers"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get count first
    cursor.execute("""
        SELECT COUNT(*)
        FROM meraki_inventory
        WHERE device_model LIKE 'MX%'
        AND (
            (wan1_arin_provider = 'Unknown' 
             AND wan1_ip NOT LIKE '192.168%' 
             AND wan1_ip NOT LIKE '10.%' 
             AND wan1_ip NOT LIKE '172.%'
             AND wan1_ip NOT LIKE '169.254%' 
             AND wan1_ip != '')
            OR
            (wan2_arin_provider = 'Unknown' 
             AND wan2_ip NOT LIKE '192.168%' 
             AND wan2_ip NOT LIKE '10.%' 
             AND wan2_ip NOT LIKE '172.%'
             AND wan2_ip NOT LIKE '169.254%' 
             AND wan2_ip != '')
        )
    """)
    
    total_count = cursor.fetchone()[0]
    logger.info(f"Found {total_count} devices with Unknown providers to update")
    
    # Process in batches
    batch_size = 50
    offset = 0
    total_updated = 0
    
    while offset < total_count:
        cursor.execute("""
            SELECT device_serial, network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
            FROM meraki_inventory
            WHERE device_model LIKE 'MX%%'
            AND (
                (wan1_arin_provider = 'Unknown' 
                 AND wan1_ip NOT LIKE '192.168%%' 
                 AND wan1_ip NOT LIKE '10.%%' 
                 AND wan1_ip NOT LIKE '172.%%'
                 AND wan1_ip NOT LIKE '169.254%%' 
                 AND wan1_ip != '')
                OR
                (wan2_arin_provider = 'Unknown' 
                 AND wan2_ip NOT LIKE '192.168%%' 
                 AND wan2_ip NOT LIKE '10.%%' 
                 AND wan2_ip NOT LIKE '172.%%'
                 AND wan2_ip NOT LIKE '169.254%%' 
                 AND wan2_ip != '')
            )
            ORDER BY device_serial
            LIMIT %s OFFSET %s
        """, (batch_size, offset))
        
        devices = cursor.fetchall()
        if not devices:
            break
        
        logger.info(f"Processing batch {offset//batch_size + 1} ({len(devices)} devices)...")
        
        updates = []
        rdap_cache_updates = []
        
        for serial, network, wan1_ip, wan2_ip, wan1_provider, wan2_provider in devices:
            wan1_new = wan1_provider
            wan2_new = wan2_provider
            updated = False
            
            # Check WAN1
            if wan1_ip and wan1_provider == 'Unknown' and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.', '169.254']):
                wan1_new = get_provider_from_rdap(wan1_ip)
                if wan1_new != 'Unknown':
                    logger.info(f"{network}: WAN1 {wan1_ip} → {wan1_new}")
                    updated = True
                    rdap_cache_updates.append((wan1_ip, wan1_new))
            
            # Check WAN2
            if wan2_ip and wan2_provider == 'Unknown' and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.', '169.254']):
                wan2_new = get_provider_from_rdap(wan2_ip)
                if wan2_new != 'Unknown':
                    logger.info(f"{network}: WAN2 {wan2_ip} → {wan2_new}")
                    updated = True
                    rdap_cache_updates.append((wan2_ip, wan2_new))
            
            if updated:
                updates.append((wan1_new, wan2_new, datetime.now(), serial))
            
            # Rate limit
            if len(updates) % 10 == 0:
                time.sleep(1)
        
        # Batch update
        if updates:
            execute_values(cursor, """
                UPDATE meraki_inventory AS m
                SET wan1_arin_provider = data.wan1_provider,
                    wan2_arin_provider = data.wan2_provider,
                    last_updated = data.updated
                FROM (VALUES %s) AS data(wan1_provider, wan2_provider, updated, serial)
                WHERE m.device_serial = data.serial
            """, updates)
            
            # Update RDAP cache
            if rdap_cache_updates:
                execute_values(cursor, """
                    INSERT INTO rdap_cache (ip_address, provider_name)
                    VALUES %s
                    ON CONFLICT (ip_address) DO UPDATE SET
                        provider_name = EXCLUDED.provider_name,
                        last_queried = NOW()
                """, rdap_cache_updates)
            
            conn.commit()
            total_updated += len(updates)
            logger.info(f"Updated {len(updates)} devices. Total updated: {total_updated}")
        
        offset += batch_size
        
        # Progress
        logger.info(f"Progress: {min(offset, total_count)}/{total_count} ({min(offset, total_count)/total_count*100:.1f}%)")
    
    cursor.close()
    conn.close()
    
    logger.info(f"\nComplete! Updated {total_updated} devices")

if __name__ == "__main__":
    logger.info("Starting fix for Unknown ARIN providers using WORKING logic...")
    update_all_unknown()