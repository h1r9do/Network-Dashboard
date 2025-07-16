#!/usr/bin/env python3
"""
Enhanced Meraki MX script with direct database integration
Collects Meraki data and stores directly in PostgreSQL database
"""

import os
import sys
import json
import requests
import re
import time
import ipaddress
from dotenv import load_dotenv
from datetime import datetime, timezone
from fuzzywuzzy import fuzz
import psycopg2
from psycopg2.extras import execute_values
import logging

# Add the test directory to path for imports
sys.path.append('/usr/local/bin/test')
from config import Config

# Get database URI from config
SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/meraki-mx-db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
ORG_NAME = "DTC-Store-Inventory-All"
BASE_URL = "https://api.meraki.com/api/v1"

# Load API key from environment
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

# Known static IP-to-provider mappings
KNOWN_IPS = {
    "63.228.128.81": "CenturyLink",
    "24.101.188.52": "Charter Communications",
    "198.99.82.203": "AT&T",
    "206.222.219.64": "Cogent Communications",
    "208.83.9.194": "CenturyLink",
    "195.252.240.66": "Deutsche Telekom",
    "209.66.104.34": "Verizon",
    "65.100.99.25": "CenturyLink",
    "69.130.234.114": "Comcast",
    "184.61.190.6": "Frontier Communications",
    "72.166.76.98": "Cox Communications",
    "98.6.198.210": "Charter Communications",
    "65.103.195.249": "CenturyLink",
    "100.88.182.60": "Verizon",
    "66.76.161.89": "Suddenlink Communications",
    "66.152.135.50": "EarthLink",
    "216.164.196.131": "RCN",
    "209.124.218.134": "IBM Cloud",
    "67.199.174.137": "Google",
    "184.60.134.66": "Frontier Communications",
    "24.144.4.162": "Conway Corporation",
    "199.38.125.142": "Ritter Communications",
    "69.195.29.6": "Ritter Communications",
    "69.171.123.138": "FAIRNET LLC",
    "63.226.59.241": "CenturyLink Communications, LLC",
    "24.124.116.54": "Midcontinent Communications",
    "50.37.227.70": "Ziply Fiber",
    "24.220.46.162": "Midcontinent Communications",
    "76.14.161.29": "Wave Broadband",
    "71.186.165.101": "Verizon Business",
    "192.190.112.119": "Lrm-Com, Inc.",
    "149.97.243.90": "Equinix, Inc.",
    "162.247.42.4": "HUNTER COMMUNICATIONS",
}

# Complete provider mapping from original nightly_enriched.py - AUTHORITATIVE SOURCE
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
    "yelcot telephone company": "Yelcot Communications",
    "yelcot communications": "Yelcot Communications",
    "ritter communications": "Ritter Communications",
    "- ritter comm": "Ritter Communications",
    "conway corporation": "Conway Corporation",
    "conway extended cable": "Conway Corporation",
    "dsr conway extended cable": "Conway Corporation",
    "altice": "Optimum",
    "altice west": "Optimum",
    "optimum": "Optimum",
    "frontier fios": "Frontier",
    "frontier metrofiber": "Frontier",
    "allo communications": "Allo Communications",
    "segra": "Segra",
    "mountain west technologies": "Mountain West Technologies",
    "c spire": "C Spire",
    "brightspeed": "Brightspeed",
    "century link": "CenturyLink",
    "centurylink": "CenturyLink",
    "clink fiber": "CenturyLink",
    "eb2-frontier fiber": "Frontier",
    "one ring networks": "One Ring Networks",
    "gtt ethernet": "GTT",
    "vexus": "Vexus",
    "sparklight": "Sparklight",
    "vista broadband": "Vista Broadband",
    "metronet": "Metronet",
    "rise broadband": "Rise Broadband",
    "lumos networks": "Lumos Networks",
    "point broadband": "Point Broadband",
    "gvtc communications": "GVTC Communications",
    "harris broadband": "Harris Broadband",
    "unite private networks": "Unite Private Networks",
    "pocketinet communications": "Pocketinet Communications",
    "eb2-ziply fiber": "Ziply Fiber",
    "astound": "Astound",
    "consolidated communications": "Consolidated Communications",
    "etheric networks": "Etheric Networks",
    "saddleback communications": "Saddleback Communications",
    "orbitel communications": "Orbitel Communications",
    "eb2-cableone cable": "Cable One",
    "cable one": "Cable One",
    "cableone": "Cable One",
    "transworld": "TransWorld",
    "mediacom/boi": "Mediacom",
    "mediacom": "Mediacom",
    "login": "Login",
    "livcom": "Livcom",
    "tds cable": "TDS Cable",
    "first digital": "Digi",
    "spanish fork community network": "Spanish Fork Community Network",
    "centracom": "Centracom",
    "eb2-lumen dsl": "Lumen",
    "lumen dsl": "Lumen",
    "eb2-centurylink dsl": "CenturyLink",
    "centurylink/qwest": "CenturyLink",
    "centurylink fiber plus": "CenturyLink",
    "lightpath": "Lightpath",
    "localtel": "LocalTel",
    "infowest inc": "Infowest",
    "eb2-windstream fiber": "Windstream",
    "gtt/esa2 adsl": "GTT",
    "zerooutages": "ZeroOutages",
    "fuse internet access": "Fuse Internet Access",
    "windstream communications llc": "Windstream",
    "frontier communications": "Frontier",
    "glenwood springs community broadband network": "Glenwood Springs Community Broadband Network",
    "unknown": "",
    "uniti fiber": "Uniti Fiber",
    "wideopenwest": "WideOpenWest",
    "wide open west": "WideOpenWest",
    "level 3": "Lumen",
    "plateau telecommunications": "Plateau Telecommunications",
    "d & p communications": "D&P Communications",
    "vzg": "VZW Cell",
}

def normalize_provider_original(provider, is_dsr=False):
    """EXACT normalization logic from nightly_enriched.py - AUTHORITATIVE SOURCE"""
    if not provider or str(provider).lower() in ['nan', 'unknown', '']:
        return ""
    
    # Step 1: Initial cleaning - remove IMEI, serial numbers, etc.
    provider_clean = re.sub(
        r'\s*(?:##.*##|\s*imei.*$|\s*kitp.*$|\s*sn.*$|\s*port.*$|\s*location.*$|\s*in\s+the\s+bay.*$|\s*up\s+front.*$|\s*under\s+.*$|\s*wireless\s+gateway.*$|\s*serial.*$|\s*poe\s+injector.*$|\s*supported\s+through.*$|\s*static\s+ip.*$|\s*subnet\s+mask.*$|\s*gateway\s+ip.*$|\s*service\s+id.*$|\s*circuit\s+id.*$|\s*ip\s+address.*$|\s*5g.*$|\s*currently.*$)',
        '', str(provider), flags=re.IGNORECASE
    ).strip()
    
    # Step 2: Prefix removal
    provider_clean = re.sub(
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workpace)\s*',
        '', provider_clean, flags=re.IGNORECASE
    ).strip()
    
    provider_lower = provider_clean.lower()
    
    # Step 3: Special provider detection (in order)
    if provider_lower.startswith('digi'):
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm')) and not is_dsr:
        return "VZW Cell"
    
    # Step 4: Fuzzy matching against provider mapping
    for key, value in PROVIDER_MAPPING.items():
        if fuzz.ratio(key, provider_lower) > 70:
            return value
    
    return provider_clean

def get_db_connection():
    """Get database connection using config"""
    import re
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', SQLALCHEMY_DATABASE_URI)
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

def get_headers(api_key):
    return {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }

def make_api_request(url, api_key, params=None, max_retries=5):
    """Make a GET request to the Meraki API with retries for rate limiting."""
    headers = get_headers(api_key)
    for attempt in range(max_retries):
        try:
            logger.debug(f"Requesting {url}")
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 429:  # rate limit
                delay = 2 ** attempt
                logger.warning(f"Rate limited. Backing off for {delay}s...")
                time.sleep(delay)
                continue
            resp.raise_for_status()
            time.sleep(1)  # ensure at most 1 request per second to Meraki
            return resp.json()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                return []
            time.sleep(2 ** attempt)
    return []

def normalize_provider(provider):
    """Normalize provider name by stripping extra spaces and converting to lowercase."""
    if provider:
        return re.sub(r'\s+', ' ', provider.strip()).lower()
    return ""

def get_canonical_provider(label):
    """Map the provider label from notes to a canonical provider name using keywords."""
    if not label:
        return "unknown"
    normalized_label = normalize_provider(label)
    for keyword, canonical in PROVIDER_KEYWORDS.items():
        if keyword in normalized_label:
            return canonical
    return normalized_label

def compare_providers(arin_provider, wan_label):
    """Compare ARIN provider and WAN provider after mapping to canonical names."""
    canonical_wan = get_canonical_provider(wan_label)
    normalized_arin = normalize_provider(arin_provider)
    
    if not canonical_wan or canonical_wan == "unknown":
        return "No match" if normalized_arin and normalized_arin != "unknown" else "Match"
    
    if canonical_wan == normalized_arin:
        return "Match"
    
    similarity = fuzz.ratio(canonical_wan, normalized_arin)
    return "Match" if similarity >= 80 else "No match"

def get_organization_id():
    """Look up the Meraki organization ID by name."""
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url, MERAKI_API_KEY)
    for org in orgs:
        if org.get("name") == ORG_NAME:
            return org.get("id")
    raise ValueError(f"Organization '{ORG_NAME}' not found")

def get_organization_uplink_statuses(org_id):
    """Retrieve WAN uplink statuses for all appliances in the organization."""
    all_statuses = []
    url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
    params = {'perPage': 1000, 'startingAfter': None}
    
    while True:
        statuses = make_api_request(url, MERAKI_API_KEY, params)
        if not statuses:
            break
        
        all_statuses.extend(statuses)
        logger.info(f"Fetched {len(statuses)} devices, total so far: {len(all_statuses)}")
        
        # Check if we got less than the requested amount (meaning we're at the end)
        if len(statuses) < params['perPage']:
            break
            
        # Get the last serial for pagination
        if statuses and 'serial' in statuses[-1]:
            params['startingAfter'] = statuses[-1]['serial']
        else:
            break
            
    return all_statuses

def get_all_networks(org_id):
    """Retrieve all networks in the organization."""
    all_networks = []
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    params = {'perPage': 1000, 'startingAfter': None}
    while True:
        networks = make_api_request(url, MERAKI_API_KEY, params)
        if not networks:
            break
        all_networks.extend(networks)
        if len(networks) < params['perPage']:
            break
        params['startingAfter'] = networks[-1]['id']
    return all_networks

def get_devices(network_id):
    """Retrieve devices in a given network."""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    return make_api_request(url, MERAKI_API_KEY)

def get_device_details(serial):
    """Retrieve the device record (including its tags)."""
    url = f"{BASE_URL}/devices/{serial}"
    return make_api_request(url, MERAKI_API_KEY)

def parse_raw_notes(raw_notes):
    """Parse the 'notes' field to extract WAN provider labels and speeds."""
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
            up_speed = float(match.group(1)); up_unit = match.group(2).upper()
            down_speed = float(match.group(3)); down_unit = match.group(4).upper()
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
            # Remove special prefixes like "NOT DSR"
            provider_name = re.sub(r'^(NOT\s+DSR|DSR)\s+', '', provider_name, flags=re.IGNORECASE)
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, speed_str
        else:
            provider_name = segment.strip()
            # Remove special prefixes
            provider_name = re.sub(r'^(NOT\s+DSR|DSR)\s+', '', provider_name, flags=re.IGNORECASE)
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
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

def fetch_json(url, context):
    """Fetch JSON data from a URL with error handling."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Error fetching JSON from {url} for {context}: {e}")
        return None

def parse_arin_response(rdap_data):
    """Parse the ARIN RDAP response to extract the provider name."""
    
    # Define the nested function to collect org entities with dates
    def collect_org_entities(entities):
        """Recursively collect organization names with their latest event dates"""
        from datetime import datetime
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
        # Sort by date (newest first) - this is the key fix
        org_names.sort(key=lambda x: x[1], reverse=True)
    
    # Special handling for CABLEONE - prefer the full company name from entities
    if network_name == 'CABLEONE' and org_names:
        for name, _ in org_names:  # Unpack tuple since org_names now contains (name, date) tuples
            if 'cable one' in name.lower():
                return "Cable One, Inc."  # Return normalized version
    
    # If we have org names, use the first one (newest by date)
    if org_names:
        # Get just the name from the tuple
        clean_name = org_names[0][0]  # Extract name from (name, date) tuple
        clean_name = re.sub(r"^Private Customer -\s*", "", clean_name).strip()
        
        # Apply known company normalizations
        company_map = {
            "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises, LLC", "AT&T Broadband", 
                     "IPAdmin-ATT Internet Services", "AT&T Communications", "AT&T Business"],
            "Charter Communications": ["Charter Communications LLC", "Charter Communications Inc", 
                                     "Charter Communications, LLC", "Charter Communications"],
            "Comcast": ["Comcast Cable Communications, LLC", "Comcast Communications", 
                        "Comcast Cable", "Comcast Corporation"],
            "Cox Communications": ["Cox Communications Inc.", "Cox Communications", "Cox Communications Group"],
            "CenturyLink": ["CenturyLink Communications", "CenturyLink", "Lumen Technologies", 
                            "Level 3 Parent, LLC", "Level 3 Communications", "Level3"],
            "Frontier Communications": ["Frontier Communications Corporation", "Frontier Communications", 
                                      "Frontier Communications Inc."],
            "Verizon": ["Verizon Communications", "Verizon Internet", "Verizon Business", "Verizon Wireless"],
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
        elif 'VERIZON' in network_name.upper():
            return 'Verizon'
        elif 'CENTURYLINK' in network_name.upper():
            return 'CenturyLink'
        elif 'FRONTIER' in network_name.upper():
            return 'Frontier Communications'
        elif 'CC04' in network_name:  # Charter network code
            return 'Charter Communications'
        else:
            # Return the network name as-is if no pattern matches
            return network_name
    
    return "Unknown"

def get_provider_for_ip(ip, cache, missing_set):
    """Determine the ISP provider name for a given IP address using cache or RDAP."""
    if ip in cache:
        return cache[ip]
    try:
        ip_addr = ipaddress.ip_address(ip)
        if ipaddress.IPv4Address("166.80.0.0") <= ip_addr <= ipaddress.IPv4Address("166.80.255.255"):
            provider = "Verizon Business"
            cache[ip] = provider
            return provider
    except ValueError:
        logger.warning(f"Invalid IP address format: {ip}")
        missing_set.add(ip)
        return "Unknown"
    
    if ip in KNOWN_IPS:
        provider = KNOWN_IPS[ip]
        cache[ip] = provider
        return provider
    
    if ip_addr.is_private:
        return "Private IP"
    
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        return "Unknown"
    
    provider = parse_arin_response(rdap_data)
    cache[ip] = provider
    return provider

def compare_providers(arin_provider, label_provider):
    """Compare ARIN provider with device notes provider using fuzzy matching"""
    if not arin_provider or not label_provider:
        return None
    
    if arin_provider in ["Unknown", "Private IP"]:
        return None
    
    # Normalize both providers
    arin_normalized = arin_provider.lower().strip()
    label_normalized = label_provider.lower().strip()
    
    # Use fuzzy matching
    score = fuzz.ratio(arin_normalized, label_normalized)
    
    # Check against known mappings
    for keyword, canonical in PROVIDER_MAPPING.items():
        if keyword in label_normalized:
            if canonical.lower() in arin_normalized:
                return "Match"
    
    # If fuzzy score is high enough, consider it a match
    if score >= 80:
        return "Match"
    else:
        return "No match"

def store_device_in_db(device_data, conn):
    """Store device data in database"""
    cursor = conn.cursor()
    
    try:
        # Store in meraki_inventory table with IP, ARIN data, and parsed notes
        insert_sql = """
        INSERT INTO meraki_inventory (
            organization_name, network_id, network_name, device_serial,
            device_model, device_name, device_tags, device_notes,
            wan1_ip, wan1_assignment, wan1_arin_provider, wan1_provider_comparison,
            wan1_provider_label, wan1_speed_label,
            wan2_ip, wan2_assignment, wan2_arin_provider, wan2_provider_comparison,
            wan2_provider_label, wan2_speed_label,
            last_updated
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (device_serial) DO UPDATE SET
            organization_name = EXCLUDED.organization_name,
            network_id = EXCLUDED.network_id,
            network_name = EXCLUDED.network_name,
            device_model = EXCLUDED.device_model,
            device_name = EXCLUDED.device_name,
            device_tags = EXCLUDED.device_tags,
            device_notes = EXCLUDED.device_notes,
            wan1_ip = EXCLUDED.wan1_ip,
            wan1_assignment = EXCLUDED.wan1_assignment,
            wan1_arin_provider = EXCLUDED.wan1_arin_provider,
            wan1_provider_comparison = EXCLUDED.wan1_provider_comparison,
            wan1_provider_label = EXCLUDED.wan1_provider_label,
            wan1_speed_label = EXCLUDED.wan1_speed_label,
            wan2_ip = EXCLUDED.wan2_ip,
            wan2_assignment = EXCLUDED.wan2_assignment,
            wan2_arin_provider = EXCLUDED.wan2_arin_provider,
            wan2_provider_comparison = EXCLUDED.wan2_provider_comparison,
            wan2_provider_label = EXCLUDED.wan2_provider_label,
            wan2_speed_label = EXCLUDED.wan2_speed_label,
            last_updated = EXCLUDED.last_updated
        """
        
        # Extract WAN data
        wan1_data = device_data.get("wan1", {})
        wan2_data = device_data.get("wan2", {})
        
        cursor.execute(insert_sql, (
            'DTC-Store-Inventory-All',  # Default org name
            device_data.get("network_id", ""),
            device_data["network_name"],
            device_data["device_serial"],
            device_data["device_model"],
            device_data["device_name"],
            device_data["device_tags"],
            device_data.get("raw_notes", ""),
            wan1_data.get("ip", ""),
            wan1_data.get("assignment", ""),
            wan1_data.get("provider", ""),
            wan1_data.get("provider_comparison", ""),
            wan1_data.get("provider_label", ""),
            wan1_data.get("speed", ""),
            wan2_data.get("ip", ""),
            wan2_data.get("assignment", ""),
            wan2_data.get("provider", ""),
            wan2_data.get("provider_comparison", ""),
            wan2_data.get("provider_label", ""),
            wan2_data.get("speed", ""),
            datetime.now(timezone.utc)
        ))
        
        # Also store ARIN data in RDAP cache
        for wan in ['wan1', 'wan2']:
            wan_data = device_data.get(wan, {})
            ip = wan_data.get("ip", "")
            provider = wan_data.get("provider", "")
            
            if ip and provider and provider != "Unknown":
                cursor.execute("""
                    INSERT INTO rdap_cache (ip_address, provider_name)
                    VALUES (%s, %s)
                    ON CONFLICT (ip_address) DO UPDATE SET
                        provider_name = EXCLUDED.provider_name,
                        last_queried = NOW()
                """, (ip, provider))
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Error storing device {device_data['device_serial']}: {e}")
        cursor.close()
        return False

def collect_firewall_rules(org_id, conn):
    """Collect firewall rules from template networks and store in database"""
    try:
        # Template networks to collect rules from
        template_networks = ["NEO 07"]  # Add more template networks as needed
        
        # Get all networks to find template networks
        networks = get_all_networks(org_id)
        template_network_ids = {}
        
        for network in networks:
            network_name = network.get('name', '').strip()
            if network_name in template_networks:
                template_network_ids[network_name] = network.get('id')
        
        logger.info(f"Found {len(template_network_ids)} template networks for firewall rules")
        
        rules_collected = 0
        
        for network_name, network_id in template_network_ids.items():
            logger.info(f"Collecting firewall rules from {network_name}")
            
            try:
                # Get L3 firewall rules
                url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
                headers = {"X-Cisco-Meraki-API-Key": MERAKI_API_KEY}
                
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    rules_data = response.json()
                    rules = rules_data.get('rules', [])
                    
                    # Clear existing rules for this network from today
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM firewall_rules WHERE network_name = %s AND DATE(last_synced) = CURRENT_DATE",
                        (network_name,)
                    )
                    
                    # Insert new rules
                    for i, rule in enumerate(rules):
                        cursor.execute("""
                            INSERT INTO firewall_rules (
                                network_id, network_name, rule_order, comment, policy,
                                protocol, src_port, src_cidr, dest_port, dest_cidr,
                                syslog_enabled, rule_type, is_template, template_source,
                                created_at, updated_at, last_synced
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                NOW(), NOW(), NOW()
                            )
                        """, (
                            network_id, network_name, i + 1,
                            rule.get('comment', ''), rule.get('policy', 'allow'),
                            rule.get('protocol', 'any'), rule.get('srcPort', 'Any'),
                            rule.get('srcCidr', 'Any'), rule.get('destPort', 'Any'),
                            rule.get('destCidr', 'Any'), rule.get('syslogEnabled', False),
                            'l3', True, network_name
                        ))
                        rules_collected += 1
                    
                    logger.info(f"Collected {len(rules)} L3 firewall rules from {network_name}")
                    
                else:
                    logger.error(f"Failed to get firewall rules from {network_name}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error collecting firewall rules from {network_name}: {e}")
                continue
            
            time.sleep(0.5)  # Rate limiting
        
        logger.info(f"Total firewall rules collected: {rules_collected}")
        return True
        
    except Exception as e:
        logger.error(f"Error in firewall rules collection: {e}")
        return False

def main():
    logger.info("Starting Meraki MX Inventory collection with database integration")
    
    try:
        org_id = get_organization_id()
        logger.info(f"Using Organization ID: {org_id}")
        
        # Get database connection
        conn = get_db_connection()
        
        # Load IP cache from database
        ip_cache = {}
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address, provider_name FROM rdap_cache")
        for ip, provider in cursor.fetchall():
            ip_cache[ip] = provider
        cursor.close()
        logger.info(f"Loaded {len(ip_cache)} IPs from RDAP cache")
        
        missing_ips = set()
        
        logger.info("Fetching uplink status for all MX devices...")
        uplink_statuses = get_organization_uplink_statuses(org_id)
        logger.info(f"Retrieved uplink info for {len(uplink_statuses)} devices")
        
        uplink_dict = {}
        for status in uplink_statuses:
            serial = status.get('serial')
            uplinks = status.get('uplinks', [])
            uplink_dict[serial] = {}
            for uplink in uplinks:
                interface = uplink.get('interface', '').lower()
                if interface in ['wan1', 'wan2']:
                    uplink_dict[serial][interface] = {
                        'ip': uplink.get('ip', ''),
                        'assignment': uplink.get('ipAssignedBy', '')
                    }
        
        networks = get_all_networks(org_id)
        networks.sort(key=lambda net: (net.get('name') or "").strip())
        logger.info(f"Found {len(networks)} networks in organization")
        
        # Process all networks (remove test limit)
        logger.info(f"Processing all {len(networks)} networks")
        
        devices_processed = 0
        
        for net in networks:
            net_name = (net.get('name') or "").strip()
            net_id = net.get('id')
            devices = get_devices(net_id)
            
            for device in devices:
                model = device.get('model', '')
                if model.startswith("MX"):
                    serial = device.get('serial')
                    device_details = get_device_details(serial)
                    tags = device_details.get('tags', []) if device_details else []
                    
                    wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
                    wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
                    wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
                    wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')
                    raw_notes = device.get('notes', '') or ''
                    wan1_label, wan1_speed, wan2_label, wan2_speed = parse_raw_notes(raw_notes)
                    
                    if wan1_ip:
                        wan1_provider = get_provider_for_ip(wan1_ip, ip_cache, missing_ips)
                        wan1_comparison = compare_providers(wan1_provider, wan1_label)
                    else:
                        wan1_provider = None
                        wan1_comparison = None
                    
                    if wan2_ip:
                        wan2_provider = get_provider_for_ip(wan2_ip, ip_cache, missing_ips)
                        wan2_comparison = compare_providers(wan2_provider, wan2_label)
                    else:
                        wan2_provider = None
                        wan2_comparison = None
                    
                    device_entry = {
                        "network_id": net_id,
                        "network_name": net_name,
                        "device_serial": serial,
                        "device_model": model,
                        "device_name": device.get('name', ''),
                        "device_tags": tags,
                        "wan1": {
                            "provider_label": wan1_label,
                            "speed": wan1_speed,
                            "ip": wan1_ip,
                            "assignment": wan1_assign,
                            "provider": wan1_provider,
                            "provider_comparison": wan1_comparison
                        },
                        "wan2": {
                            "provider_label": wan2_label,
                            "speed": wan2_speed,
                            "ip": wan2_ip,
                            "assignment": wan2_assign,
                            "provider": wan2_provider,
                            "provider_comparison": wan2_comparison
                        },
                        "raw_notes": raw_notes
                    }
                    
                    # Store in database
                    if store_device_in_db(device_entry, conn):
                        devices_processed += 1
                        logger.info(f"Processed device {serial} in network '{net_name}' with WAN1 IP: {wan1_ip}, WAN2 IP: {wan2_ip}")
                    
                    time.sleep(0.2)
        
        # Check for new stores that now have Meraki networks
        logger.info("Checking for new stores that now have Meraki networks...")
        try:
            cursor = conn.cursor()
            
            # Get all active new stores
            cursor.execute("""
                SELECT id, site_name 
                FROM new_stores 
                WHERE is_active = TRUE
            """)
            active_new_stores = cursor.fetchall()
            
            if active_new_stores:
                logger.info(f"Checking {len(active_new_stores)} active new stores against Meraki networks")
                
                # Get all network names (strip and uppercase for comparison)
                network_names_upper = set()
                for net in networks:
                    net_name = (net.get('name') or "").strip().upper()
                    if net_name:
                        network_names_upper.add(net_name)
                
                stores_found = 0
                for store_id, site_name in active_new_stores:
                    site_name_upper = site_name.upper()
                    
                    # Check if this store name appears in any network name
                    found_in_meraki = False
                    for net_name in network_names_upper:
                        if site_name_upper in net_name:
                            found_in_meraki = True
                            break
                    
                    if found_in_meraki:
                        # Update the store record - mark as found in Meraki
                        cursor.execute("""
                            UPDATE new_stores 
                            SET is_active = FALSE, 
                                meraki_network_found = TRUE, 
                                meraki_found_date = NOW(),
                                updated_at = NOW()
                            WHERE id = %s
                        """, (store_id,))
                        stores_found += 1
                        logger.info(f"New store '{site_name}' found in Meraki - deactivating from new stores list")
                
                if stores_found > 0:
                    logger.info(f"Deactivated {stores_found} new stores that now have Meraki networks")
                else:
                    logger.info("No new stores found in Meraki networks")
            else:
                logger.info("No active new stores to check")
                
        except Exception as e:
            logger.error(f"Error checking new stores: {e}")
        
        # Collect firewall rules from template networks
        logger.info("Starting firewall rules collection...")
        try:
            firewall_success = collect_firewall_rules(org_id, conn)
            if firewall_success:
                logger.info("Firewall rules collection completed successfully")
            else:
                logger.warning("Firewall rules collection encountered issues")
        except Exception as e:
            logger.error(f"Error collecting firewall rules: {e}")
        
        # Save IP cache to database for future use
        if ip_cache:
            logger.info(f"Saving {len(ip_cache)} IP lookups to RDAP cache")
            cursor = conn.cursor()
            for ip, provider in ip_cache.items():
                cursor.execute("""
                    INSERT INTO rdap_cache (ip_address, provider_name)
                    VALUES (%s, %s)
                    ON CONFLICT (ip_address) DO UPDATE SET
                        provider_name = EXCLUDED.provider_name,
                        last_queried = NOW()
                """, (ip, provider))
            cursor.close()
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info(f"Completed inventory. Processed {devices_processed} devices and stored in database")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)