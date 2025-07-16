#!/usr/bin/env python3
"""
BETA TESTING VERSION: Full Production Merged Meraki + Enrichment Script
- Processes ALL networks/devices (full production scale)
- Includes API speed optimization from production script
- Writes to BETA tables for safe testing
- Extensive debugging and logging for analysis
- No impact on production data
"""

import os
import sys
import json
import requests
import re
import time
import ipaddress
import socket
import signal
from dotenv import load_dotenv
from datetime import datetime, timezone
from thefuzz import fuzz
import psycopg2
from psycopg2.extras import execute_values, execute_batch
import logging

# Add the test directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Get database URI from config
SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Setup logging with extensive debugging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for extensive logging
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/meraki-enriched-merged-beta.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Force stdout to be unbuffered for immediate output
sys.stdout = sys.__stdout__
sys.stdout.reconfigure(line_buffering=True)

# Configuration constants
ORG_NAME = "DTC-Store-Inventory-All"
BASE_URL = "https://api.meraki.com/api/v1"

# Load API key from environment
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

# BETA MODE - All table names have _beta suffix
BETA_MODE = True
logger.info("🧪 BETA MODE ENABLED - Writing to beta tables only")

def get_table_name(base_name):
    """Get table name with beta suffix for beta mode"""
    if BETA_MODE:
        return f"{base_name}_beta"
    return base_name

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
    "vzg": "VZW Cell",
}

def signal_handler(signum, frame):
    """Handle Ctrl-C gracefully"""
    logger.info(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

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
    """Enhanced API request with aggressive adaptive rate limiting for maximum speed"""
    headers = get_headers(api_key)
    
    # Adaptive rate limiting variables
    if not hasattr(make_api_request, 'current_delay'):
        make_api_request.current_delay = 0.05  # Start at 50ms
        make_api_request.successful_requests = 0
        make_api_request.rate_limited_count = 0
        make_api_request.last_speed_increase = time.time()
        make_api_request.consecutive_successes = 0
        logger.info(f"🚀 API rate limiter initialized: starting at {make_api_request.current_delay:.3f}s delay")
    
    for attempt in range(max_retries):
        try:
            # Use adaptive delay
            time.sleep(make_api_request.current_delay)
            
            if make_api_request.successful_requests % 100 == 0 and make_api_request.successful_requests > 0:
                logger.debug(f"📊 API Request #{make_api_request.successful_requests}: {url} (delay: {make_api_request.current_delay:.3f}s)")
            
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            
            if resp.status_code == 429:  # Rate limited
                make_api_request.rate_limited_count += 1
                make_api_request.consecutive_successes = 0
                old_delay = make_api_request.current_delay
                make_api_request.current_delay = min(2.0, make_api_request.current_delay * 1.5)
                logger.warning(f"⚠️ Rate limited! Backing off: {old_delay:.3f}s -> {make_api_request.current_delay:.3f}s")
                time.sleep(5)
                continue
            
            resp.raise_for_status()
            
            # Success! Track consecutive successes
            make_api_request.successful_requests += 1
            make_api_request.consecutive_successes += 1
            
            # Aggressive speed increases
            current_time = time.time()
            time_since_last_increase = current_time - make_api_request.last_speed_increase
            
            # Speed up every 30 seconds
            if time_since_last_increase >= 30:
                old_delay = make_api_request.current_delay
                make_api_request.current_delay = max(0.005, make_api_request.current_delay * 0.5)
                make_api_request.last_speed_increase = current_time
                logger.info(f"⚡ 30-second speed boost! {old_delay:.3f}s -> {make_api_request.current_delay:.3f}s (after {make_api_request.successful_requests} requests)")
            
            # Performance stats every 50 requests
            if make_api_request.successful_requests % 50 == 0:
                logger.info(f"📈 API Performance: {make_api_request.successful_requests} requests, "
                           f"Rate limited: {make_api_request.rate_limited_count} times, "
                           f"Current delay: {make_api_request.current_delay:.3f}s")
            
            return resp.json()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Keyboard interrupt received, exiting...")
            raise
        except Exception as e:
            make_api_request.consecutive_successes = 0
            if attempt == max_retries - 1:
                logger.error(f"❌ Failed to fetch {url} after {max_retries} attempts: {e}")
                return []
            time.sleep(2 ** attempt)
    return []

def normalize_provider(provider, is_dsr=True):
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
        logger.debug(f"🔍 Provider matched: Digi (from '{provider}')")
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        logger.debug(f"🔍 Provider matched: Starlink (from '{provider}')")
        return "Starlink"
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        logger.debug(f"🔍 Provider matched: Inseego (from '{provider}')")
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm')) and not is_dsr:
        logger.debug(f"🔍 Provider matched: VZW Cell (from '{provider}')")
        return "VZW Cell"
    
    # Step 4: Fuzzy matching against provider mapping
    for key, value in PROVIDER_MAPPING.items():
        if fuzz.ratio(key, provider_lower) > 70:
            logger.debug(f"🔍 Provider fuzzy matched: {value} (from '{provider}' -> '{key}')")
            return value
    
    logger.debug(f"🔍 Provider not matched, using cleaned: '{provider_clean}' (from '{provider}')")
    return provider_clean

def get_organization_id():
    """Get organization ID for DTC-Store-Inventory-All"""
    logger.info("🔍 Getting organization ID...")
    url = f"{BASE_URL}/organizations"
    data = make_api_request(url, MERAKI_API_KEY)
    
    for org in data:
        if org.get('name') == ORG_NAME:
            org_id = org.get('id')
            logger.info(f"✅ Found organization '{ORG_NAME}' with ID: {org_id}")
            return org_id
    
    logger.error(f"❌ Organization '{ORG_NAME}' not found")
    return None

def get_all_networks(org_id):
    """Get all networks in the organization"""
    logger.info("📡 Fetching all networks...")
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    networks = make_api_request(url, MERAKI_API_KEY)
    logger.info(f"📊 Found {len(networks)} total networks in organization")
    return networks

def get_devices(network_id):
    """Get devices for a specific network"""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    return make_api_request(url, MERAKI_API_KEY)

def get_device_details(serial):
    """Get device details including tags"""
    url = f"{BASE_URL}/devices/{serial}"
    return make_api_request(url, MERAKI_API_KEY)

def get_organization_uplink_statuses(org_id):
    """Get uplink statuses for all devices in organization"""
    logger.info("🌐 Fetching organization-wide uplink statuses...")
    url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
    statuses = make_api_request(url, MERAKI_API_KEY)
    logger.info(f"📊 Retrieved uplink info for {len(statuses)} devices")
    return statuses

def parse_raw_notes(raw_notes):
    """Parse raw notes - exact logic from legacy meraki_mx.py"""
    logger.debug(f"🔍 Parsing notes: '{raw_notes[:100]}...' (truncated)")
    
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
                
            speed_str = f"{up_speed:.0f}{up_unit} x {down_speed:.0f}{down_unit}"
            provider_part = segment[:match.start()].strip()
        else:
            speed_str = ""
            provider_part = segment.strip()
        
        # Clean up the provider part
        provider_part = re.sub(r'\s*\|\s*$', '', provider_part).strip()
        
        return provider_part, speed_str
    
    # Split by WAN patterns
    segments = []
    last_end = 0
    
    for match in re.finditer(r'(?:WAN[12]|WAN\s*[12])\s*:?\s*', text, re.IGNORECASE):
        if last_end < match.start():
            segments.append(('', text[last_end:match.start()]))
        segments.append((match.group(), ''))
        last_end = match.end()
    
    if last_end < len(text):
        if segments:
            segments[-1] = (segments[-1][0], text[last_end:])
        else:
            segments.append(('', text[last_end:]))
    
    # Process segments
    wan1_provider, wan1_speed = "", ""
    wan2_provider, wan2_speed = "", ""
    
    for header, content in segments:
        if re.search(r'WAN\s*1', header, re.IGNORECASE):
            wan1_provider, wan1_speed = extract_provider_and_speed(content)
        elif re.search(r'WAN\s*2', header, re.IGNORECASE):
            wan2_provider, wan2_speed = extract_provider_and_speed(content)
        elif not header and not wan1_provider:  # Unlabeled content
            wan1_provider, wan1_speed = extract_provider_and_speed(content)
    
    # Normalize provider names
    wan1_provider = normalize_provider(wan1_provider, is_dsr=False)
    wan2_provider = normalize_provider(wan2_provider, is_dsr=False)
    
    logger.debug(f"📝 Parsed - WAN1: {wan1_provider} @ {wan1_speed}, WAN2: {wan2_provider} @ {wan2_speed}")
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

def lookup_arin_provider(ip_address, cache=None, logger=None):
    """Lookup ISP provider using ARIN RDAP - exact logic from nightly_enriched.py"""
    if not ip_address or ip_address == "None":
        return ""
    
    # Check cache first
    if cache and ip_address in cache:
        logger.debug(f"🗂️ ARIN cache hit for {ip_address}: {cache[ip_address]}")
        return cache[ip_address]
    
    # Check static mappings
    if ip_address in KNOWN_IPS:
        provider = KNOWN_IPS[ip_address]
        if cache is not None:
            cache[ip_address] = provider
        logger.debug(f"🗂️ Static mapping hit for {ip_address}: {provider}")
        return provider
    
    # Skip special IP ranges
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            if cache is not None:
                cache[ip_address] = ""
            return ""
        
        # Skip 166.80.x.x range (known non-RDAP)
        if ip_address.startswith("166.80."):
            if cache is not None:
                cache[ip_address] = ""
            return ""
    except:
        return ""
    
    try:
        logger.debug(f"🌐 RDAP lookup for {ip_address}")
        rdap_url = f"https://rdap.arin.net/registry/ip/{ip_address}"
        response = requests.get(rdap_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract provider from entities
            entities = data.get('entities', [])
            for entity in entities:
                if 'roles' in entity and 'ISP' in entity.get('roles', []):
                    if 'vcardArray' in entity:
                        for vcard_entry in entity['vcardArray']:
                            if isinstance(vcard_entry, list):
                                for vcard_item in vcard_entry:
                                    if isinstance(vcard_item, list) and len(vcard_item) >= 4 and vcard_item[0] == 'fn':
                                        provider = str(vcard_item[3]).strip()
                                        if cache is not None:
                                            cache[ip_address] = provider
                                        logger.debug(f"✅ RDAP found provider for {ip_address}: {provider}")
                                        return provider
            
            # Fallback to handle field
            handle = data.get('handle', '')
            if handle:
                if cache is not None:
                    cache[ip_address] = handle
                logger.debug(f"📋 RDAP handle for {ip_address}: {handle}")
                return handle
                
        logger.debug(f"❌ No RDAP data for {ip_address}")
        if cache is not None:
            cache[ip_address] = ""
        return ""
        
    except Exception as e:
        logger.debug(f"❌ RDAP error for {ip_address}: {e}")
        if cache is not None:
            cache[ip_address] = ""
        return ""

def resolve_ddns_to_ip(ddns_hostname, logger=None):
    """Resolve DDNS hostname to IP address"""
    if not ddns_hostname:
        return None
    
    try:
        logger.debug(f"🔍 DNS lookup for DDNS: {ddns_hostname}")
        ip_address = socket.gethostbyname(ddns_hostname)
        logger.debug(f"✅ DDNS resolved {ddns_hostname} -> {ip_address}")
        return ip_address
    except Exception as e:
        logger.debug(f"❌ DDNS resolution failed for {ddns_hostname}: {e}")
        return None

def store_device_in_db(device_data, conn, logger=None):
    """Store device data in meraki_inventory_beta table"""
    try:
        table_name = get_table_name('meraki_inventory')
        
        # Now that constraints are added, use ON CONFLICT for efficiency
        insert_sql = f"""
        INSERT INTO {table_name} (
            organization_name, network_id, network_name, device_serial, device_model,
            device_name, device_tags, device_notes, wan1_ip, wan1_assignment, wan1_arin_provider, 
            wan1_provider_comparison, wan1_provider_label, wan1_speed_label,
            wan2_ip, wan2_assignment, wan2_arin_provider, wan2_provider_comparison,
            wan2_provider_label, wan2_speed_label, last_updated
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (device_serial) DO UPDATE SET
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
        
        cursor = conn.cursor()
        cursor.execute(insert_sql, (
            device_data['organization_name'],
            device_data['network_id'],
            device_data['network_name'],
            device_data['device_serial'],
            device_data['device_model'],
            device_data['device_name'],
            device_data['device_tags'],
            device_data['device_notes'],
            device_data['wan1_ip'],
            device_data['wan1_assignment'],
            device_data['wan1_arin_provider'],
            device_data['wan1_provider_comparison'],
            device_data['wan1_provider_label'],
            device_data['wan1_speed_label'],
            device_data['wan2_ip'],
            device_data['wan2_assignment'],
            device_data['wan2_arin_provider'],
            device_data['wan2_provider_comparison'],
            device_data['wan2_provider_label'],
            device_data['wan2_speed_label'],
            datetime.now()
        ))
        
        logger.debug(f"📝 Stored device {device_data['device_serial']} in {table_name}")
        
    except Exception as e:
        logger.error(f"❌ Failed to store device {device_data.get('device_serial', 'unknown')}: {e}")
        raise  # Re-raise to trigger rollback

def find_matching_circuit(device_data, dsr_circuits, logger=None):
    """Find matching DSR circuit for device - exact logic from nightly_enriched.py"""
    network_name = device_data['network_name']
    
    logger.debug(f"🔍 Finding DSR circuit match for {network_name}")
    
    # Try exact network name match first
    for circuit in dsr_circuits:
        if circuit['site_name'].lower() == network_name.lower():
            logger.debug(f"✅ Exact match found: {circuit['site_name']}")
            return circuit
    
    # Try fuzzy matching with 85% threshold
    best_match = None
    best_ratio = 0
    
    for circuit in dsr_circuits:
        ratio = fuzz.ratio(circuit['site_name'].lower(), network_name.lower())
        if ratio > 85 and ratio > best_ratio:
            best_ratio = ratio
            best_match = circuit
    
    if best_match:
        logger.debug(f"✅ Fuzzy match found: {best_match['site_name']} ({best_ratio}% match)")
        return best_match
    
    logger.debug(f"❌ No DSR circuit match found for {network_name}")
    return None

def detect_wan_flip(device_data, dsr_circuit, logger=None):
    """Detect if WAN cables have been physically swapped - exact logic from nightly_enriched.py"""
    if not device_data.get('wan1_arin_provider') or not device_data.get('wan2_arin_provider'):
        return False
    
    if not dsr_circuit.get('provider_name'):
        return False
    
    dsr_provider_norm = normalize_provider(dsr_circuit['provider_name'], is_dsr=True)
    wan1_arin_norm = normalize_provider(device_data['wan1_arin_provider'], is_dsr=False)
    wan2_arin_norm = normalize_provider(device_data['wan2_arin_provider'], is_dsr=False)
    
    logger.debug(f"🔍 WAN flip check - DSR: {dsr_provider_norm}, WAN1: {wan1_arin_norm}, WAN2: {wan2_arin_norm}")
    
    # Check if DSR provider matches WAN2 but not WAN1
    wan1_match = fuzz.ratio(dsr_provider_norm.lower(), wan1_arin_norm.lower()) > 70
    wan2_match = fuzz.ratio(dsr_provider_norm.lower(), wan2_arin_norm.lower()) > 70
    
    flip_detected = not wan1_match and wan2_match
    
    if flip_detected:
        logger.info(f"🔄 WAN FLIP DETECTED for {device_data['network_name']}: DSR provider '{dsr_provider_norm}' matches WAN2 '{wan2_arin_norm}' instead of WAN1 '{wan1_arin_norm}'")
    
    return flip_detected

def check_if_any_update_needed(device_data, existing_enriched, all_circuits, logger=None):
    """Check if ANY update is needed (MX inventory or enriched) based on IP or circuit changes"""
    network_name = device_data['network_name']
    
    # If no existing enriched data, we need to do full processing
    if not existing_enriched:
        logger.debug(f"🆕 No existing data for {network_name} - full processing needed")
        return True, "new_record"
    
    # Check if IP addresses have changed
    current_wan1_ip = device_data.get('wan1_ip')
    current_wan2_ip = device_data.get('wan2_ip')
    existing_wan1_ip = existing_enriched.get('wan1_ip')
    existing_wan2_ip = existing_enriched.get('wan2_ip')
    
    ip_changed = not (current_wan1_ip == existing_wan1_ip and current_wan2_ip == existing_wan2_ip)
    
    if ip_changed:
        # Check if IPs have just flipped (WAN1 ↔ WAN2)
        if (current_wan1_ip == existing_wan2_ip and current_wan2_ip == existing_wan1_ip and 
            current_wan1_ip is not None and current_wan2_ip is not None):
            logger.info(f"🔄 IP FLIP detected for {network_name}: WAN1 {existing_wan1_ip}->{current_wan1_ip}, WAN2 {existing_wan2_ip}->{current_wan2_ip}")
            return True, "ip_flip"
        
        # IPs have changed but not flipped - need full processing
        logger.info(f"🔍 IP CHANGE detected for {network_name}: WAN1 {existing_wan1_ip}->{current_wan1_ip}, WAN2 {existing_wan2_ip}->{current_wan2_ip}")
        return True, "ip_change"
    
    # No IP changes - check if circuit database has changed
    circuit_changed, circuit_change_reason = check_circuit_database_changes(
        network_name, existing_enriched, all_circuits, logger
    )
    
    if circuit_changed:
        logger.info(f"📋 CIRCUIT CHANGE detected for {network_name}: {circuit_change_reason}")
        return True, "circuit_change"
    
    # No changes detected
    logger.debug(f"⏭️ No changes for {network_name} - skipping ALL work (no IP or circuit changes)")
    return False, "no_changes"

def check_circuit_database_changes(network_name, existing_enriched, all_circuits, logger=None):
    """Check if circuit database has changes that should trigger enriched table update"""
    try:
        # Find current circuit data for this network
        matching_dsr_circuit = find_matching_circuit({'network_name': network_name}, all_circuits, logger)
        
        if matching_dsr_circuit:
            # Compare DSR circuit data with existing enriched data
            dsr_provider = normalize_provider(matching_dsr_circuit.get('provider_name', ''), is_dsr=True)
            dsr_speed = matching_dsr_circuit.get('speed', '')
            
            existing_wan1_provider = existing_enriched.get('wan1_provider', '')
            existing_wan1_speed = existing_enriched.get('wan1_speed', '')
            existing_wan2_provider = existing_enriched.get('wan2_provider', '') 
            existing_wan2_speed = existing_enriched.get('wan2_speed', '')
            
            # Check if DSR circuit is currently assigned to WAN1 (normal case)
            if existing_enriched.get('wan1_circuit_role') == 'Primary':
                if dsr_provider != existing_wan1_provider:
                    return True, f"DSR provider changed: {existing_wan1_provider} -> {dsr_provider}"
                if dsr_speed != existing_wan1_speed:
                    return True, f"DSR speed changed: {existing_wan1_speed} -> {dsr_speed}"
            
            # Check if DSR circuit is currently assigned to WAN2 (flipped case)
            elif existing_enriched.get('wan2_circuit_role') == 'Primary':
                if dsr_provider != existing_wan2_provider:
                    return True, f"DSR provider changed: {existing_wan2_provider} -> {dsr_provider}"
                if dsr_speed != existing_wan2_speed:
                    return True, f"DSR speed changed: {existing_wan2_speed} -> {dsr_speed}"
            
            # DSR circuit exists but not currently assigned - new circuit detected
            else:
                return True, f"New DSR circuit detected: {dsr_provider} @ {dsr_speed}"
        
        else:
            # No DSR circuit found - check if we previously had one
            existing_wan1_confirmed = existing_enriched.get('wan1_confirmed', False)
            existing_wan2_confirmed = existing_enriched.get('wan2_confirmed', False)
            
            if existing_wan1_confirmed or existing_wan2_confirmed:
                return True, "DSR circuit removed from database"
        
        # Could also check Non-DSR circuits, but DSR changes are most important
        return False, "no_circuit_changes"
        
    except Exception as e:
        logger.error(f"❌ Error checking circuit changes for {network_name}: {e}")
        return False, "error_checking_circuits"

def check_if_enriched_update_needed(device_data, existing_enriched, logger=None):
    """Check if enriched data needs updating based on IP changes"""
    network_name = device_data['network_name']
    
    # If no existing enriched data, we need to create it
    if not existing_enriched:
        logger.debug(f"🆕 No existing enriched data for {network_name} - creating new record")
        return True, "new_record"
    
    # Check if IP addresses have changed
    current_wan1_ip = device_data.get('wan1_ip')
    current_wan2_ip = device_data.get('wan2_ip')
    existing_wan1_ip = existing_enriched.get('wan1_ip')
    existing_wan2_ip = existing_enriched.get('wan2_ip')
    
    # If IPs are the same, no update needed
    if (current_wan1_ip == existing_wan1_ip and current_wan2_ip == existing_wan2_ip):
        logger.debug(f"⏭️ No IP changes for {network_name} - skipping enrichment update")
        return False, "no_changes"
    
    # Check if IPs have just flipped (WAN1 <-> WAN2)
    if (current_wan1_ip == existing_wan2_ip and current_wan2_ip == existing_wan1_ip and 
        current_wan1_ip is not None and current_wan2_ip is not None):
        logger.info(f"🔄 IP FLIP detected for {network_name}: WAN1 {existing_wan1_ip}->{current_wan1_ip}, WAN2 {existing_wan2_ip}->{current_wan2_ip}")
        return True, "ip_flip"
    
    # IPs have changed but not flipped - need full re-evaluation
    logger.info(f"🔍 IP CHANGE detected for {network_name}: WAN1 {existing_wan1_ip}->{current_wan1_ip}, WAN2 {existing_wan2_ip}->{current_wan2_ip}")
    return True, "ip_change"

def get_existing_enriched_data(network_name, conn, logger=None):
    """Get existing enriched data and IP data for a network"""
    try:
        enriched_table = get_table_name('enriched_circuits')
        meraki_table = get_table_name('meraki_inventory')
        cursor = conn.cursor()
        
        if logger:
            logger.debug(f"🔍 Querying {enriched_table} and {meraki_table} for network: {network_name}")
        
        # Get IP data from meraki_inventory and enriched data from enriched_circuits
        cursor.execute(f"""
            SELECT 
                e.network_name, 
                COALESCE(m.wan1_ip, e.wan1_ip) as wan1_ip,
                COALESCE(m.wan2_ip, e.wan2_ip) as wan2_ip,
                e.wan1_provider, e.wan1_speed, e.wan1_circuit_role, e.wan1_confirmed,
                e.wan2_provider, e.wan2_speed, e.wan2_circuit_role, e.wan2_confirmed, 
                e.wan1_arin_org, e.wan2_arin_org
            FROM {enriched_table} e
            LEFT JOIN {meraki_table} m ON e.network_name = m.network_name
            WHERE e.network_name = %s
        """, (network_name,))
        
        result = cursor.fetchone()
        if logger:
            logger.debug(f"🔍 Combined query result for {network_name}: wan1_ip={result[1] if result else None}, wan2_ip={result[2] if result else None}")
            
        if result:
            return {
                'network_name': result[0],
                'wan1_ip': result[1],
                'wan2_ip': result[2],
                'wan1_provider': result[3],
                'wan1_speed': result[4],
                'wan1_circuit_role': result[5],
                'wan1_confirmed': result[6],
                'wan2_provider': result[7],
                'wan2_speed': result[8],
                'wan2_circuit_role': result[9],
                'wan2_confirmed': result[10],
                'wan1_arin_org': result[11],
                'wan2_arin_org': result[12]
            }
        return None
        
    except Exception as e:
        logger.error(f"❌ Failed to get existing enriched data for {network_name}: {e}")
        raise  # Re-raise to trigger rollback

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

def handle_ip_flip(device_data, existing_enriched, logger=None):
    """Handle case where WAN IPs have flipped - swap the enriched data"""
    network_name = device_data['network_name']
    
    # Swap the existing enriched data to match the new IP layout
    enriched_data = {
        'network_name': network_name,
        'device_tags': device_data.get('device_tags', []),
        'wan1_ip': device_data.get('wan1_ip'),
        'wan2_ip': device_data.get('wan2_ip'),
        'wan1_arin_org': device_data.get('wan1_arin_provider', ''),
        'wan2_arin_org': device_data.get('wan2_arin_provider', ''),
        # Swap the providers and speeds to follow the IPs
        'wan1_provider': existing_enriched.get('wan2_provider', ''),
        'wan1_speed': existing_enriched.get('wan2_speed', ''),
        'wan1_circuit_role': existing_enriched.get('wan2_circuit_role', 'Secondary'),
        'wan1_confirmed': existing_enriched.get('wan2_confirmed', False),
        'wan2_provider': existing_enriched.get('wan1_provider', ''),
        'wan2_speed': existing_enriched.get('wan1_speed', ''),
        'wan2_circuit_role': existing_enriched.get('wan1_circuit_role', 'Primary'),
        'wan2_confirmed': existing_enriched.get('wan1_confirmed', False),
        'last_updated': datetime.now(),
        'created_at': datetime.now()
    }
    
    
    logger.info(f"🔄 IP FLIP: Swapped WAN data for {network_name} to follow IP layout")
    return enriched_data

def handle_circuit_change(device_data, existing_enriched, all_circuits, logger=None):
    """Handle case where circuit database has changed but IPs haven't"""
    network_name = device_data['network_name']
    
    # Start with existing enriched data (keep IPs, ARIN data, etc.)
    enriched_data = {
        'network_name': network_name,
        'device_tags': device_data.get('device_tags', []),
        'wan1_ip': existing_enriched.get('wan1_ip'),  # Keep existing IPs
        'wan2_ip': existing_enriched.get('wan2_ip'),  # Keep existing IPs  
        'wan1_arin_org': existing_enriched.get('wan1_arin_org', ''),
        'wan2_arin_org': existing_enriched.get('wan2_arin_org', ''),
        'last_updated': datetime.now(),
        'created_at': existing_enriched.get('created_at', datetime.now())
    }
    
    # Get updated circuit information
    matching_dsr_circuit = find_matching_circuit(device_data, all_circuits, logger)
    
    if matching_dsr_circuit:
        # DSR circuit found - update with new circuit data
        dsr_provider = normalize_provider(matching_dsr_circuit.get('provider_name', ''), is_dsr=True)
        dsr_speed = matching_dsr_circuit.get('speed', '')
        
        # Determine if this is currently a WAN1 or WAN2 assignment
        if existing_enriched.get('wan1_circuit_role') == 'Primary':
            # Update WAN1 with new DSR circuit data
            enriched_data.update({
                'wan1_provider': dsr_provider,
                'wan1_speed': dsr_speed,
                'wan1_circuit_role': 'Primary',
                'wan1_confirmed': True,
                'wan2_provider': existing_enriched.get('wan2_provider', ''),
                'wan2_speed': existing_enriched.get('wan2_speed', ''),
                'wan2_circuit_role': 'Secondary',
                'wan2_confirmed': existing_enriched.get('wan2_confirmed', False)
            })
            logger.info(f"📋 Updated WAN1 DSR circuit for {network_name}: {dsr_provider} @ {dsr_speed}")
        else:
            # Update WAN2 with new DSR circuit data (flipped case)
            enriched_data.update({
                'wan1_provider': existing_enriched.get('wan1_provider', ''),
                'wan1_speed': existing_enriched.get('wan1_speed', ''),
                'wan1_circuit_role': 'Secondary',
                'wan1_confirmed': existing_enriched.get('wan1_confirmed', False),
                'wan2_provider': dsr_provider,
                'wan2_speed': dsr_speed,
                'wan2_circuit_role': 'Primary',
                'wan2_confirmed': True
            })
            logger.info(f"📋 Updated WAN2 DSR circuit for {network_name}: {dsr_provider} @ {dsr_speed}")
    else:
        # No DSR circuit found - use device notes
        enriched_data.update({
            'wan1_provider': device_data.get('wan1_provider_label', ''),
            'wan1_speed': device_data.get('wan1_speed_label', ''),
            'wan1_circuit_role': 'Primary',
            'wan1_confirmed': False,
            'wan2_provider': device_data.get('wan2_provider_label', ''),
            'wan2_speed': device_data.get('wan2_speed_label', ''),
            'wan2_circuit_role': 'Secondary',
            'wan2_confirmed': False
        })
        logger.info(f"📋 No DSR circuit found for {network_name} - using device notes")
    
    return enriched_data

def find_circuit_for_provider(provider_name, all_circuits, logger=None):
    """Find a circuit that matches the provider name"""
    if not provider_name:
        return None
    
    provider_norm = normalize_provider(provider_name, is_dsr=False)
    
    # Try exact match first
    for circuit in all_circuits:
        circuit_provider_norm = normalize_provider(circuit.get('provider_name', ''), is_dsr=True)
        if circuit_provider_norm.lower() == provider_norm.lower():
            logger.debug(f"🎯 Exact provider match: {provider_name} -> {circuit['site_name']}")
            return circuit
    
    # Try fuzzy match
    best_match = None
    best_ratio = 0
    for circuit in all_circuits:
        circuit_provider_norm = normalize_provider(circuit.get('provider_name', ''), is_dsr=True)
        ratio = fuzz.ratio(circuit_provider_norm.lower(), provider_norm.lower())
        if ratio > 70 and ratio > best_ratio:
            best_ratio = ratio
            best_match = circuit
    
    if best_match:
        logger.debug(f"🎯 Fuzzy provider match ({best_ratio}%): {provider_name} -> {best_match['site_name']}")
        return best_match
    
    return None

def create_enriched_record_with_change_detection(device_data, existing_enriched, all_circuits, change_reason, logger=None):
    """Create enriched circuit record with smart change detection"""
    try:
        network_name = device_data['network_name']
        
        # Handle different change scenarios
        if change_reason == "ip_flip":
            return handle_ip_flip(device_data, existing_enriched, logger)
        
        elif change_reason == "circuit_change":
            return handle_circuit_change(device_data, existing_enriched, all_circuits, logger)
        
        elif change_reason == "ip_change" or change_reason == "new_record":
            # Full re-evaluation needed
            
            # Start with device data
            enriched_data = {
                'network_name': network_name,
                'device_tags': device_data.get('device_tags', []),
                'wan1_ip': device_data.get('wan1_ip'),
                'wan2_ip': device_data.get('wan2_ip'),
                'wan1_arin_org': device_data.get('wan1_arin_provider', ''),
                'wan2_arin_org': device_data.get('wan2_arin_provider', ''),
                'last_updated': datetime.now(),
                'created_at': datetime.now()
            }
            
            # Try to find matching DSR circuit by site name first
            matching_dsr_circuit = find_matching_circuit(device_data, all_circuits, logger)
            
            if matching_dsr_circuit:
                # DSR circuit found - use it for primary WAN
                dsr_provider = normalize_provider(matching_dsr_circuit.get('provider_name', ''), is_dsr=True)
                dsr_speed = matching_dsr_circuit.get('speed', '')
                
                # Check for WAN flip
                wan_flipped = detect_wan_flip(device_data, matching_dsr_circuit, logger)
                
                if wan_flipped:
                    # DSR circuit matches WAN2 better
                    enriched_data.update({
                        'wan1_provider': device_data.get('wan1_provider_label', ''),
                        'wan1_speed': device_data.get('wan1_speed_label', ''),
                        'wan1_circuit_role': 'Secondary',
                        'wan2_provider': dsr_provider,
                        'wan2_speed': dsr_speed,
                        'wan2_circuit_role': 'Primary',
                        'wan2_confirmed': True
                    })
                    
                    
                    logger.info(f"🔄 WAN FLIP: DSR circuit assigned to WAN2 for {network_name}")
                else:
                    # Normal DSR assignment to WAN1
                    enriched_data.update({
                        'wan1_provider': dsr_provider,
                        'wan1_speed': dsr_speed,
                        'wan1_circuit_role': 'Primary',
                        'wan1_confirmed': True,
                        'wan2_provider': device_data.get('wan2_provider_label', ''),
                        'wan2_speed': device_data.get('wan2_speed_label', ''),
                        'wan2_circuit_role': 'Secondary'
                    })
                    
                    
                    logger.debug(f"✅ DSR circuit assigned to WAN1 for {network_name}")
            
            else:
                # No DSR circuit found - try to find Non-DSR circuits by provider
                wan1_provider = device_data.get('wan1_provider_label', '')
                wan2_provider = device_data.get('wan2_provider_label', '')
                
                wan1_circuit = find_circuit_for_provider(wan1_provider, all_circuits, logger)
                wan2_circuit = find_circuit_for_provider(wan2_provider, all_circuits, logger)
                
                # Use device notes as base, enhanced with any found circuit data
                enriched_data.update({
                    'wan1_provider': wan1_provider,
                    'wan1_speed': wan1_circuit.get('speed', '') if wan1_circuit else device_data.get('wan1_speed_label', ''),
                    'wan1_circuit_role': 'Primary',
                    'wan1_confirmed': bool(wan1_circuit),
                    'wan2_provider': wan2_provider,
                    'wan2_speed': wan2_circuit.get('speed', '') if wan2_circuit else device_data.get('wan2_speed_label', ''),
                    'wan2_circuit_role': 'Secondary',
                    'wan2_confirmed': bool(wan2_circuit)
                })
                
                
                if wan1_circuit or wan2_circuit:
                    logger.info(f"🔍 Found Non-DSR circuits for {network_name}: WAN1={bool(wan1_circuit)}, WAN2={bool(wan2_circuit)}")
                else:
                    logger.debug(f"📝 No circuits found - using device notes for {network_name}")
            
            return enriched_data
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Failed to create enriched record for {network_name}: {e}")
        return None

def load_all_circuits(conn, logger=None):
    """Load all circuits (DSR and Non-DSR) from database for matching"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT site_name, provider_name, details_service_speed, status, circuit_purpose
            FROM circuits 
            WHERE status = 'Enabled'
            ORDER BY site_name, circuit_purpose
        """)
        
        circuits = []
        for row in cursor.fetchall():
            circuits.append({
                'site_name': row[0],
                'provider_name': row[1],
                'speed': row[2],
                'status': row[3],
                'circuit_purpose': row[4] or 'Primary'
            })
        
        logger.info(f"📊 Loaded {len(circuits)} enabled circuits (DSR + Non-DSR) for matching")
        return circuits
        
    except Exception as e:
        logger.error(f"❌ Failed to load circuits: {e}")
        return []

def store_enriched_circuit(enriched_data, conn, logger=None):
    """Store enriched circuit data in enriched_circuits_beta table"""
    try:
        table_name = get_table_name('enriched_circuits')
        
        # Now that constraints are added, use ON CONFLICT for efficiency  
        insert_sql = f"""
        INSERT INTO {table_name} (
            network_name, device_tags, wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
            wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed, wan1_ip, wan2_ip,
            wan1_arin_org, wan2_arin_org, last_updated, created_at, pushed_to_meraki
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (network_name) DO UPDATE SET
            device_tags = EXCLUDED.device_tags,
            wan1_provider = COALESCE(NULLIF({table_name}.wan1_provider, ''), EXCLUDED.wan1_provider),
            wan1_speed = COALESCE(NULLIF({table_name}.wan1_speed, ''), EXCLUDED.wan1_speed),
            wan1_circuit_role = EXCLUDED.wan1_circuit_role,
            wan2_provider = COALESCE(NULLIF({table_name}.wan2_provider, ''), EXCLUDED.wan2_provider),
            wan2_speed = COALESCE(NULLIF({table_name}.wan2_speed, ''), EXCLUDED.wan2_speed),
            wan2_circuit_role = EXCLUDED.wan2_circuit_role,
            wan1_ip = EXCLUDED.wan1_ip,
            wan2_ip = EXCLUDED.wan2_ip,
            wan1_arin_org = EXCLUDED.wan1_arin_org,
            wan2_arin_org = EXCLUDED.wan2_arin_org,
            last_updated = EXCLUDED.last_updated
        """
        
        cursor = conn.cursor()
        cursor.execute(insert_sql, (
            enriched_data['network_name'],
            enriched_data['device_tags'],
            enriched_data['wan1_provider'],
            enriched_data['wan1_speed'],
            enriched_data['wan1_circuit_role'],
            enriched_data.get('wan1_confirmed', False),
            enriched_data['wan2_provider'],
            enriched_data['wan2_speed'],
            enriched_data['wan2_circuit_role'],
            enriched_data.get('wan2_confirmed', False),
            enriched_data['wan1_ip'],
            enriched_data['wan2_ip'],
            enriched_data['wan1_arin_org'],
            enriched_data['wan2_arin_org'],
            enriched_data['last_updated'],
            enriched_data['created_at'],
            False  # pushed_to_meraki
        ))
        
        logger.debug(f"📝 Stored enriched circuit for {enriched_data['network_name']} in {table_name}")
        
    except Exception as e:
        logger.error(f"❌ Failed to store enriched circuit for {enriched_data.get('network_name', 'unknown')}: {e}")
        raise  # Re-raise to trigger rollback


def main():
    """Main execution function for beta testing"""
    logger.info("🧪 Starting BETA Merged Meraki + Enriched Script")
    logger.info(f"📝 Writing to BETA TABLES ONLY (suffix: _beta)")
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    start_time = time.time()
    processed_devices = 0
    enriched_devices = 0
    skipped_devices = 0
    ip_flips = 0
    ip_changes = 0
    new_records = 0
    circuit_changes = 0
    arin_cache = {}
    
    try:
        # Get database connection
        logger.info("🔌 Connecting to database...")
        conn = get_db_connection()
        conn.autocommit = False
        
        # Load all circuits (DSR + Non-DSR) for matching
        logger.info("📋 Loading all circuits for matching...")
        all_circuits = load_all_circuits(conn, logger)
        
        # Get organization ID
        org_id = get_organization_id()
        if not org_id:
            logger.error("❌ Could not get organization ID")
            return
        
        # Get all networks
        networks = get_all_networks(org_id)
        if not networks:
            logger.error("❌ No networks found")
            return
        
        # Get uplink statuses for all devices
        logger.info("🌐 Getting organization-wide uplink statuses...")
        uplink_statuses = get_organization_uplink_statuses(org_id)
        uplink_dict = {status.get('serial'): status for status in uplink_statuses}
        
        logger.info(f"🚀 Processing {len(networks)} networks for FULL BETA testing...")
        
        # Process each network
        for net_idx, network in enumerate(networks, 1):
            network_id = network.get('id')
            network_name = network.get('name', '')
            
            # Skip excluded networks
            if any(exclude in network_name.lower() for exclude in ['hub', 'lab', 'voice', 'test', 'template']):
                logger.debug(f"⏭️ Skipping excluded network: {network_name}")
                continue
            
            logger.info(f"🔍 Processing network {net_idx}/{len(networks)}: {network_name}")
            
            # Get devices for this network
            devices = get_devices(network_id)
            
            for device in devices:
                if device.get('model', '').startswith('MX'):
                    processed_devices += 1
                    
                    try:
                        # Get device details and uplink status
                        device_serial = device.get('serial')
                        device_details = get_device_details(device_serial)
                        uplink_status = uplink_dict.get(device_serial, {})
                        
                        logger.debug(f"📱 Processing MX device: {device_serial} in {network_name}")
                        
                        # Parse device notes
                        raw_notes = device_details.get('notes', '')
                        wan1_provider_label, wan1_speed_label, wan2_provider_label, wan2_speed_label = parse_raw_notes(raw_notes)
                        
                        # Get WAN IP addresses
                        wan1_ip = None
                        wan2_ip = None
                        wan1_assignment = None
                        wan2_assignment = None
                        
                        uplinks = uplink_status.get('uplinks', [])
                        for uplink in uplinks:
                            interface = uplink.get('interface')
                            if interface == 'wan1':
                                wan1_ip = uplink.get('ip')
                                wan1_assignment = uplink.get('ipAssignedBy', 'Unknown')
                            elif interface == 'wan2':
                                wan2_ip = uplink.get('ip')
                                wan2_assignment = uplink.get('ipAssignedBy', 'Unknown')
                        
                        # DDNS resolution for private IPs
                        ddns_enabled = False
                        ddns_url = None
                        wan1_public_ip = wan1_ip
                        wan2_public_ip = wan2_ip
                        
                        if wan1_ip and wan1_ip.startswith('192.168.'):
                            ddns_url = f"dtc{device_serial.lower()}.hopto.org"
                            resolved_ip = resolve_ddns_to_ip(ddns_url, logger)
                            if resolved_ip:
                                wan1_public_ip = resolved_ip
                                ddns_enabled = True
                        
                        # ARIN provider lookups
                        wan1_arin_provider = lookup_arin_provider(wan1_public_ip, arin_cache, logger)
                        wan2_arin_provider = lookup_arin_provider(wan2_public_ip, arin_cache, logger)
                        
                        # Calculate provider comparisons for meraki_inventory table
                        wan1_provider_comparison = compare_providers(wan1_arin_provider, wan1_provider_label)
                        wan2_provider_comparison = compare_providers(wan2_arin_provider, wan2_provider_label)
                        
                        # Create device data structure
                        device_data = {
                            'organization_name': ORG_NAME,
                            'network_id': network_id,
                            'network_name': network_name,
                            'device_serial': device_serial,
                            'device_model': device.get('model'),
                            'device_name': device.get('name'),
                            'device_tags': device_details.get('tags', []),
                            'wan1_ip': wan1_public_ip,  # Use resolved public IPs for change detection
                            'wan2_ip': wan2_public_ip,  # Use resolved public IPs for change detection
                            'wan1_assignment': wan1_assignment,
                            'wan2_assignment': wan2_assignment,
                            'wan1_arin_provider': wan1_arin_provider,
                            'wan2_arin_provider': wan2_arin_provider,
                            'wan1_provider_comparison': wan1_provider_comparison or '',
                            'wan2_provider_comparison': wan2_provider_comparison or '',
                            'wan1_provider_label': wan1_provider_label,
                            'wan1_speed_label': wan1_speed_label,
                            'wan2_provider_label': wan2_provider_label,
                            'wan2_speed_label': wan2_speed_label,
                            'device_notes': raw_notes,
                            'ddns_enabled': ddns_enabled,
                            'ddns_url': ddns_url
                        }
                        
                        # First check if ANY update is needed (IP or circuit change detection)
                        existing_enriched = get_existing_enriched_data(network_name, conn, logger)
                        needs_any_update, change_reason = check_if_any_update_needed(device_data, existing_enriched, all_circuits, logger)
                        
                        if needs_any_update:
                            # Store device in meraki_inventory_beta (only if IPs or MX data changed)
                            if change_reason in ["ip_flip", "ip_change", "new_record"]:
                                store_device_in_db(device_data, conn, logger)
                                logger.debug(f"📝 Updated MX inventory for {network_name} (reason: {change_reason})")
                            else:
                                logger.debug(f"⏭️ Skipping MX inventory update for {network_name} - only circuit data changed")
                            
                            # Handle enriched data based on change type
                            if change_reason == "ip_flip":
                                # IPs just flipped - swap existing enriched data assignments
                                logger.info(f"🔄 Handling IP flip for {network_name} - just swapping assignments")
                                enriched_data = create_enriched_record_with_change_detection(
                                    device_data, existing_enriched, all_circuits, change_reason, logger
                                )
                            elif change_reason == "circuit_change":
                                # Circuit data changed but IPs same - update enriched with new circuit data
                                logger.info(f"📋 Handling circuit change for {network_name} - updating enriched data")
                                enriched_data = create_enriched_record_with_change_detection(
                                    device_data, existing_enriched, all_circuits, change_reason, logger
                                )
                            else:
                                # New IPs or new record - do full circuit lookup  
                                logger.info(f"🔍 Handling new data for {network_name} - full processing")
                                enriched_data = create_enriched_record_with_change_detection(
                                    device_data, existing_enriched, all_circuits, change_reason, logger
                                )
                            
                            # Store enriched data if created successfully (applies to both flip and new IPs)
                            if enriched_data:
                                store_enriched_circuit(enriched_data, conn, logger)
                                enriched_devices += 1
                                
                                # Track change type statistics
                                if change_reason == "ip_flip":
                                    ip_flips += 1
                                elif change_reason == "ip_change":
                                    ip_changes += 1
                                elif change_reason == "new_record":
                                    new_records += 1
                                elif change_reason == "circuit_change":
                                    circuit_changes += 1
                                    
                                logger.debug(f"🔄 Updated enriched data for {network_name} (reason: {change_reason})")
                        else:
                            skipped_devices += 1
                            logger.debug(f"⏭️ Skipped ALL work for {network_name} - no IP changes detected")
                        
                        # Commit after each device for safety
                        conn.commit()
                        
                        # Progress logging every 10 devices
                        if processed_devices % 10 == 0:
                            elapsed = time.time() - start_time
                            rate = processed_devices / elapsed * 60  # devices per minute
                            logger.info(f"📊 Progress: {processed_devices} devices processed, {enriched_devices} enriched ({rate:.1f} devices/min)")
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing device {device.get('serial', 'unknown')}: {e}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        continue
        
        # Final statistics
        elapsed_time = time.time() - start_time
        logger.info(f"✅ BETA SCRIPT COMPLETED!")
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   • Total Networks: {len(networks)}")
        logger.info(f"   • MX Devices Processed: {processed_devices}")
        logger.info(f"   • Enriched Circuits Updated: {enriched_devices}")
        logger.info(f"   • Enriched Circuits Skipped: {skipped_devices}")
        logger.info(f"   • Change Types:")
        logger.info(f"     - New Records: {new_records}")
        logger.info(f"     - IP Changes: {ip_changes}")
        logger.info(f"     - IP Flips: {ip_flips}")
        logger.info(f"     - Circuit Changes: {circuit_changes}")
        logger.info(f"     - No Changes: {skipped_devices}")
        logger.info(f"   • ARIN Cache Entries: {len(arin_cache)}")
        logger.info(f"   • Total Runtime: {elapsed_time/60:.1f} minutes")
        logger.info(f"   • Processing Rate: {processed_devices/elapsed_time*60:.1f} devices/min")
        logger.info(f"   • Efficiency: {skipped_devices/processed_devices*100:.1f}% skipped (no changes)")
        logger.info(f"🧪 All data written to BETA TABLES (_beta suffix)")
        
    except KeyboardInterrupt:
        logger.info("🛑 Script interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("🔌 Database connection closed")

if __name__ == "__main__":
    main()