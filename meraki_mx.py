import os
import json
import requests
import re
import time
import ipaddress
from dotenv import load_dotenv
from datetime import datetime, timezone
from fuzzywuzzy import fuzz

# Load environment variables (Meraki API key, etc.)
load_dotenv('/usr/local/bin/meraki.env')

# Configuration constants
ORG_NAME = "DTC-Store-Inventory-All"
BASE_URL = "https://api.meraki.com/api/v1"
DATA_DIR = "/var/www/html/meraki-data"
os.makedirs(DATA_DIR, exist_ok=True)  # ensure data directory exists

# File paths
INVENTORY_FILE = os.path.join(DATA_DIR, 'mx_inventory_live.json')
IP_CACHE_FILE = os.path.join(DATA_DIR, 'ip_lookup_cache.json')
MISSING_LOG_FILE = os.path.join(DATA_DIR, 'missing_data_log.txt')

# Initialize output JSON file
with open(INVENTORY_FILE, 'w') as f:
    json.dump([], f)

# Load API key from environment
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

# Known static IP-to-provider mappings (overrides for specific IPs)
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
    "65.103.195.249": "CenturyLink",
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

# Updated provider keywords for accurate mapping
PROVIDER_KEYWORDS = {
    'spectrum': 'charter communications',
    'charter': 'charter communications',
    'at&t': 'at&t',
    'att': 'at&t',
    'comcast': 'comcast',
    'verizon': 'verizon business',
    'vz': 'verizon business',
    'cox': 'cox communications',
    'yelcot': 'yelcot telephone company',
    'ritter': 'ritter communications',
    'conway': 'conway corporation',
    'altice': 'optimum',
    'brightspeed': 'level 3',
    'clink': 'centurylink',
    'lumen': 'centurylink',
    'c spire': 'c spire fiber',
    'orbitelcomm': 'orbitel communications, llc',
    'sparklight': 'cable one, inc.',
    'lightpath': 'optimum',
    'vzg': 'verizon business',
    'digi': 'verizon business',  # Maps 'DIGI' to 'verizon business'
    'centurylink': 'centurylink',
    'mediacom': 'mediacom communications corporation',
    'frontier': 'frontier communications',
    'cable one': 'cable one, inc.',
    'qwest': 'centurylink',
    'cox business': 'cox communications',
    'consolidatedcomm': 'consolidated communications, inc.',  # Maps 'DSR ConsolidatedComm' to ARIN provider
    'consolidated': 'consolidated communications, inc.'  # Handles variations
}

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
            print(f"🔑 Requesting {url}")
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 429:  # rate limit
                delay = 2 ** attempt
                print(f"⏳ Rate limited. Backing off for {delay}s...")
                time.sleep(delay)
                continue
            resp.raise_for_status()
            time.sleep(1)  # ensure at most 1 request per second to Meraki
            return resp.json()
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"⚠️ Failed to fetch {url} after {max_retries} attempts: {e}")
                return []
            time.sleep(2 ** attempt)  # Exponential backoff
    return []

def append_to_json_file(filename, device_entry):
    """Append device entry to JSON file, ensuring proper formatting."""
    data = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []
    data.append(device_entry)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

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
    print(f"Comparing ARIN='{normalized_arin}' with Canonical WAN='{canonical_wan}' (from '{wan_label}'): similarity={similarity}")
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
        if len(statuses) < 1000:
            break
        params['startingAfter'] = statuses[-1]['serial']
        print(f"📡 Fetched {len(statuses)} devices, total so far: {len(all_statuses)}")
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
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, speed_str
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

def fetch_json(url, context):
    """Fetch JSON data from a URL with error handling."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ Error fetching JSON from {url} for {context}: {e}")
        return None

def parse_arin_response(rdap_data):
    """Parse the ARIN RDAP response to extract the provider name."""
    return rdap_data.get('network', {}).get('name', 'Unknown')

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
        print(f"⚠️ Invalid IP address format: {ip}")
        missing_set.add(ip)
        return "Unknown"
    if ip in KNOWN_IPS:
        provider = KNOWN_IPS[ip]
        cache[ip] = provider
        return provider
    if ip_addr.is_private:
        return "Unknown"
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        return "Unknown"
    return parse_arin_response(rdap_data)

def main():
    print("🔍 Starting Meraki MX Inventory collection...")
    org_id = get_organization_id()
    print(f"🏢 Using Organization ID: {org_id}")
    
    ip_cache = {}
    if os.path.exists(IP_CACHE_FILE):
        with open(IP_CACHE_FILE, 'r') as f:
            ip_cache = json.load(f)
    
    missing_ips = set()
    
    print("📡 Fetching uplink status for all MX devices...")
    uplink_statuses = get_organization_uplink_statuses(org_id)
    print(f"✅ Retrieved uplink info for {len(uplink_statuses)} devices")
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
    print(f"🌐 Found {len(networks)} networks in organization")
    
    for net in networks:
        net_name = (net.get('name') or "").strip()
        net_id = net.get('id')
        devices = get_devices(net_id)
        for device in devices:
            model = device.get('model', '')
            if model.startswith("MX"):
                serial = device.get('serial')
                # Fetch device-specific details to get tags
                device_details = get_device_details(serial)
                tags = device_details.get('tags', []) if device_details else []
                
                # Debug statement to verify tags
                print(f"Device {serial} tags: {tags}")
                
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
                
                print(f"    WAN1: IP={wan1_ip}, Label='{wan1_label}', Provider={wan1_provider}, Speed={wan1_speed}, Match: {wan1_comparison}")
                print(f"    WAN2: IP={wan2_ip}, Label='{wan2_label}', Provider={wan2_provider}, Speed={wan2_speed}, Match: {wan2_comparison}")
                
                device_entry = {
                    "network_id": net_id,
                    "device_tags": tags,  # Changed to device_tags for clarity
                    "network_name": net_name,
                    "device_serial": serial,
                    "device_model": model,
                    "device_name": device.get('name', ''),
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
                    "providers_flipped": None,
                    "raw_notes": raw_notes,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                append_to_json_file(INVENTORY_FILE, device_entry)
                print(f"✅ Processed device {serial} in network '{net_name}'")
                # rate-limit courtesy
                time.sleep(0.2)
    
    try:
        with open(IP_CACHE_FILE, 'w') as cf:
            json.dump(ip_cache, cf, indent=2)
    except Exception as e:
        print(f"⚠️ Error writing IP cache: {e}")
    
    try:
        with open(MISSING_LOG_FILE, 'w') as lf:
            for ip in sorted(missing_ips):
                lf.write(f"{ip}\n")
    except Exception as e:
        print(f"⚠️ Error writing missing data log: {e}")
    
    print(f"✅ Completed inventory. Data saved to {INVENTORY_FILE}")

if __name__ == "__main__":
    main()