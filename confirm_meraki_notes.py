import os
import json
import csv
import glob
import re
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from flask import jsonify, request

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
ORG_NAME = "DTC-Store-Inventory-All"
DATA_DIR = "/var/www/html/meraki-data"
TRACKING_PATTERN = "/var/www/html/circuitinfo/tracking_data_*.csv"
LIVE_JSON = os.path.join(DATA_DIR, "mx_inventory_live.json")
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ENRICHED_FILE = os.path.join(DATA_DIR, f"mx_inventory_enriched_{datetime.now().strftime('%Y-%m-%d')}.json")

# API limits (Meraki allows ~1000 requests per 5 minutes)
MAX_REQUESTS = 900  # Buffer below 1000 to be safe
REQUEST_WINDOW = 300  # 5 minutes in seconds
REQUESTS = []  # Track timestamps of requests

# Provider keywords for validation
PROVIDER_KEYWORDS = {
    'spectrum': 'Charter Communications',
    'charter': 'Charter Communications',
    'at&t': 'AT&T',
    'att': 'AT&T',
    'comcast': 'Comcast',
    'verizon': 'Verizon Business',
    'vz': 'Verizon Business',
    'cox': 'Cox Communications',
    'yelcot': 'Yelcot Telephone Company',
    'ritter': 'Ritter Communications',
    'conway': 'Conway Corporation',
    'altice': 'Optimum',
    'brightspeed': 'Level 3',
    'clink': 'CenturyLink',
    'lumen': 'CenturyLink',
    'c spire': 'C Spire Fiber',
    'orbitelcomm': 'Orbitel Communications, LLC',
    'sparklight': 'Cable One, Inc.',
    'lightpath': 'Optimum',
    'vzg': 'Verizon Business',
    'digi': 'Verizon Business',
    'centurylink': 'CenturyLink',
    'mediacom': 'Mediacom Communications Corporation',
    'frontier': 'Frontier Communications',
    'cable one': 'Cable One, Inc.',
    'qwest': 'CenturyLink',
    'cox business': 'Cox Communications',
    'consolidatedcomm': 'Consolidated Communications, Inc.',
    'consolidated': 'Consolidated Communications, Inc.'
}

def get_headers():
    return {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

def clean_request_timestamps():
    global REQUESTS
    current_time = time.time()
    REQUESTS = [t for t in REQUESTS if current_time - t < REQUEST_WINDOW]

def make_api_request(url, params=None, max_retries=5, backoff_factor=1):
    headers = get_headers()
    for attempt in range(max_retries):
        clean_request_timestamps()
        if len(REQUESTS) >= MAX_REQUESTS:
            time.sleep(REQUEST_WINDOW / MAX_REQUESTS)  # Simple rate limit adjustment
            clean_request_timestamps()
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            REQUESTS.append(time.time())
            return response.json()
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:  # Too Many Requests
                wait_time = backoff_factor * (2 ** attempt) + (attempt * 0.1)  # Exponential backoff with jitter
                print(f"Rate limit hit, backing off for {wait_time} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            elif attempt == max_retries - 1:
                return {"error": str(e)}
            else:
                time.sleep(backoff_factor * (2 ** attempt))  # Backoff for other errors
    return {"error": "Max retries exceeded"}

def make_api_update(url, data, max_retries=5, backoff_factor=1):
    headers = get_headers()
    for attempt in range(max_retries):
        clean_request_timestamps()
        if len(REQUESTS) >= MAX_REQUESTS:
            time.sleep(REQUEST_WINDOW / MAX_REQUESTS)  # Simple rate limit adjustment
            clean_request_timestamps()
        
        try:
            response = requests.put(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            REQUESTS.append(time.time())
            return {"success": True}
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:  # Too Many Requests
                wait_time = backoff_factor * (2 ** attempt) + (attempt * 0.1)  # Exponential backoff with jitter
                print(f"Rate limit hit, backing off for {wait_time} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            elif attempt == max_retries - 1:
                return {"error": str(e)}
            else:
                time.sleep(backoff_factor * (2 ** attempt))  # Backoff for other errors
    return {"error": "Max retries exceeded"}

def normalize_string(s):
    if not s:
        return "UNKNOWN"
    return re.sub(r'\s+', ' ', s.strip()).upper()

def parse_raw_notes(raw_notes):
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    text = re.sub(r'\s+', ' ', raw_notes.strip())
    wan1_pattern = re.compile(r'(?:WAN1|WAN\s*1)\s*:?\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)
    speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
    
    def extract_provider_and_speed(segment):
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
            provider_name = segment[:match.start()].strip().replace('DSR ', '')
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, speed_str
        else:
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', segment).strip().replace('DSR ', '')
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

def get_latest_tracking_csv():
    tracking_files = sorted(glob.glob(TRACKING_PATTERN), key=os.path.getmtime, reverse=True)
    return tracking_files[0] if tracking_files else None

def get_tracking_data(site_name):
    latest_csv = get_latest_tracking_csv()
    if not latest_csv:
        return []
    data = []
    try:
        with open(latest_csv, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                if row.get('status', '').lower() != 'enabled':
                    continue
                if normalize_string(row['Site Name']) == normalize_string(site_name):
                    if row['Circuit Purpose'].capitalize() in ['Primary', 'Secondary']:
                        data.append({
                            'Site Name': row['Site Name'],
                            'date': row['date'],
                            'Circuit Purpose': row['Circuit Purpose'],
                            'status': row['status'],
                            'provider_name': row['provider_name'],
                            'milestone_service_activated': row['milestone_service_activated'],
                            'billing_monthly_cost': row['billing_monthly_cost'],
                            'details_provider_title': row['details_provider_title'],
                            'details_ordered_service_speed': row['details_ordered_service_speed'],
                            'service_effective_date': row['service_effective_date']
                        })
    except Exception as e:
        return [{"error": str(e)}]
    return data

def get_dsr_data(site_name):
    tracking_data = get_tracking_data(site_name)
    dsr_data = {}
    for row in tracking_data:
        if row['Circuit Purpose'].capitalize() == 'Primary':
            dsr_data['wan1'] = {
                'provider': row['provider_name'],
                'speed': row['details_ordered_service_speed']
            }
        elif row['Circuit Purpose'].capitalize() == 'Secondary':
            dsr_data['wan2'] = {
                'provider': row['provider_name'],
                'speed': row['details_ordered_service_speed']
            }
    return dsr_data

def get_meraki_notes(site_name):
    print(f"DEBUG: Starting get_meraki_notes for site: {site_name}")
    # Load mx_inventory_live.json for notes and ARIN data
    if not os.path.exists(LIVE_JSON):
        print(f"DEBUG: mx_inventory_live.json not found at {LIVE_JSON}")
        return {"error": f"Live JSON file not found at {LIVE_JSON}"}
    
    try:
        with open(LIVE_JSON, 'r') as f:
            live_data = json.load(f)
    except Exception as e:
        print(f"DEBUG: Error reading live JSON: {str(e)}")
        return {"error": f"Error reading live JSON: {str(e)}"}
    
    # Find the matching network entry
    matching_entry = next((entry for entry in live_data if normalize_string(entry.get('network_name', '')) == normalize_string(site_name)), None)
    if not matching_entry:
        print(f"DEBUG: No matching entry found for {site_name} in live JSON")
        return {"error": f"No matching entry found for site {site_name} in live JSON"}
    
    raw_notes = matching_entry.get('raw_notes', '')
    wan1_provider, wan1_speed, wan2_provider, wan2_speed = parse_raw_notes(raw_notes)
    print(f"DEBUG: Parsed notes - WAN1: {wan1_provider}, {wan1_speed}, WAN2: {wan2_provider}, {wan2_speed}")
    
    return {
        "raw_notes": raw_notes,
        "wan1_provider_notes": wan1_provider,
        "wan1_speed_notes": wan1_speed,
        "wan2_provider_notes": wan2_provider,
        "wan2_speed_notes": wan2_speed
    }

def update_enriched_json(site_name, data):
    try:
        with open(ENRICHED_FILE, 'r') as f:
            enriched_data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read enriched JSON: {str(e)}"}
    
    for site in enriched_data:
        if normalize_string(site['network_name']) == normalize_string(site_name):
            site['wan1']['provider'] = data.get('wan1_provider', site['wan1'].get('provider', ''))
            site['wan1']['speed'] = data.get('wan1_speed', site['wan1'].get('speed', ''))
            site['wan1']['confirmed'] = True
            site['wan2']['provider'] = data.get('wan2_provider', site['wan2'].get('provider', ''))
            site['wan2']['speed'] = data.get('wan2_speed', site['wan2'].get('speed', ''))
            site['wan2']['confirmed'] = True
            break
    else:
        return {"error": f"Site {site_name} not found in enriched JSON"}
    
    try:
        with open(ENRICHED_FILE, 'w') as f:
            json.dump(enriched_data, f, indent=2)
        return {"success": True}
    except Exception as e:
        return {"error": f"Failed to write enriched JSON: {str(e)}"}

def load_pushed_log():
    log_file = os.path.join(DATA_DIR, "pushed_sites_log.json")
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_pushed_log(log):
    log_file = os.path.join(DATA_DIR, "pushed_sites_log.json")
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)
    print(f"[Meraki Push] 🗂️  Log written to {log_file} ({len(log)} site(s))")

def remove_from_pushed_log(site_name):
    log = load_pushed_log()
    normalized_site = normalize_string(site_name)
    new_log = [site for site in log if normalize_string(site) != normalized_site]
    save_pushed_log(new_log)

def reset_confirmation(site_name):
    normalized_site = normalize_string(site_name)
    print(f"\n[Meraki Reset] Resetting confirmation for: {site_name} (normalized: {normalized_site})")

    if not os.path.exists(ENRICHED_FILE):
        print(f"[Meraki Reset] ❌ Enriched file not found: {ENRICHED_FILE}")
        return {"error": "Enriched file not found"}

    try:
        with open(ENRICHED_FILE, 'r') as f:
            enriched_data = json.load(f)
    except Exception as e:
        print(f"[Meraki Reset] ❌ Failed to load enriched file: {str(e)}")
        return {"error": f"Failed to load enriched file: {str(e)}"}

    reset_done = False
    for site in enriched_data:
        if normalize_string(site.get("network_name", "")) == normalized_site:
            site['wan1']['confirmed'] = False
            site['wan2']['confirmed'] = False
            reset_done = True
            print(f"[Meraki Reset] 🔄 Cleared confirmation flags for {site_name}")
            break

    if not reset_done:
        print(f"[Meraki Reset] ⚠️  Site {site_name} not found in enriched JSON")
        return {"error": f"Site {site_name} not found"}

    try:
        with open(ENRICHED_FILE, 'w') as f:
            json.dump(enriched_data, f, indent=2)
        print(f"[Meraki Reset] 💾 Saved updates to enriched file: {ENRICHED_FILE}")
    except Exception as e:
        print(f"[Meraki Reset] ❌ Failed to save enriched file: {str(e)}")
        return {"error": f"Failed to save enriched file: {str(e)}"}

    remove_from_pushed_log(site_name)
    print(f"[Meraki Reset] 🧹 Removed {site_name} from pushed_sites_log.json")

    return {"success": True, "message": f"Site {site_name} reset"}

def push_to_meraki():
    print("\n[Meraki Push] Starting push_to_meraki process")

    if not os.path.exists(LIVE_JSON) or not os.path.exists(ENRICHED_FILE):
        print(f"[Meraki Push] ❌ Missing files - Live JSON: {LIVE_JSON}, Enriched JSON: {ENRICHED_FILE}")
        return {"error": "Required JSON files not found"}

    try:
        with open(LIVE_JSON, 'r') as f:
            live_data = json.load(f)
        with open(ENRICHED_FILE, 'r') as f:
            enriched_data = json.load(f)
        print(f"[Meraki Push] Loaded {len(live_data)} live sites, {len(enriched_data)} enriched sites")
    except Exception as e:
        print(f"[Meraki Push] ❌ Error reading JSON files: {str(e)}")
        return {"error": f"Error reading JSON files: {str(e)}"}

    pushed_log = load_pushed_log()
    print(f"[Meraki Push] Loaded pushed_sites_log.json — {len(pushed_log)} site(s) recorded")

    updated_sites = []
    sites_to_add = []
    skipped_count = 0

    for enriched_site in enriched_data:
        site_name = enriched_site.get('network_name', 'UNKNOWN')
        if not (enriched_site.get('wan1', {}).get('confirmed') and enriched_site.get('wan2', {}).get('confirmed')):
            skipped_count += 1
            continue

        if any(normalize_string(site) == normalize_string(site_name) for site in pushed_log):
            skipped_count += 1
            continue

        live_entry = next((entry for entry in live_data if normalize_string(entry.get('network_name', '')) == normalize_string(site_name)), None)
        if not live_entry or not live_entry.get('device_serial'):
            skipped_count += 1
            continue

        device_serial = live_entry['device_serial']
        notes = (
            "WAN 1\n"
            f"{enriched_site['wan1']['provider']}\n"
            f"{enriched_site['wan1']['speed']}\n"
            "WAN 2\n"
            f"{enriched_site['wan2']['provider']}\n"
            f"{enriched_site['wan2']['speed']}"
        )

        url = f"{BASE_URL}/devices/{device_serial}"
        current_device = make_api_request(url)

        if isinstance(current_device, dict) and "error" in current_device:
            print(f"[Meraki Push] ⚠️  API error fetching device {site_name}: {current_device['error']}")
            skipped_count += 1
            continue

        if current_device.get('notes') == notes:
            print(f"[Meraki Push] ✅ {site_name} already matches notes — no update needed")
            print(f"[Meraki Push]   WAN1: {enriched_site['wan1']['provider']} | {enriched_site['wan1']['speed']}")
            print(f"[Meraki Push]   WAN2: {enriched_site['wan2']['provider']} | {enriched_site['wan2']['speed']}")
            sites_to_add.append(site_name)
        else:
            result = make_api_update(url, {"notes": notes})
            if result.get('success'):
                print(f"[Meraki Push] ✅ Updated notes for {site_name}")
                print(f"[Meraki Push]   WAN1: {enriched_site['wan1']['provider']} | {enriched_site['wan1']['speed']}")
                print(f"[Meraki Push]   WAN2: {enriched_site['wan2']['provider']} | {enriched_site['wan2']['speed']}")
                updated_sites.append({
                    'site_name': site_name,
                    'wan1_provider': enriched_site['wan1']['provider'],
                    'wan1_speed': enriched_site['wan1']['speed'],
                    'wan2_provider': enriched_site['wan2']['provider'],
                    'wan2_speed': enriched_site['wan2']['speed']
                })
                sites_to_add.append(site_name)
            else:
                print(f"[Meraki Push] ❌ Failed to update notes for {site_name}: {result.get('error', 'Unknown error')}")
                skipped_count += 1

    if sites_to_add:
        new_log = pushed_log + sites_to_add
        save_pushed_log(new_log)
        print(f"[Meraki Push] 📝 pushed_sites_log.json updated — total sites: {len(new_log)}")

    print(f"[Meraki Push] Summary: {len(updated_sites)} updated | {skipped_count} skipped")
    return {
        "success": True,
        "updated_sites": updated_sites,
        "skipped": skipped_count,
        "message": f"{len(updated_sites)} site(s) updated."
    }

def confirm_site(site_name, submit=False, data=None):
    normalized_site = normalize_string(site_name)
    print(f"\n[Meraki Confirm] Handling confirmation for: {site_name} (normalized: {normalized_site})")

    if not submit:
        # Fetch data for popup
        notes_data = get_meraki_notes(site_name)
        dsr_data = get_dsr_data(site_name)
        csv_data = get_tracking_data(site_name)

        if "error" in notes_data:
            notes_data["csv_data"] = csv_data
            return notes_data
        if csv_data and isinstance(csv_data[0], dict) and "error" in csv_data[0]:
            return csv_data[0]

        # Load mx_inventory_live.json for ARIN data
        arin_data = {}
        if os.path.exists(LIVE_JSON):
            try:
                with open(LIVE_JSON, 'r') as f:
                    live_data = json.load(f)
                live_entry = next((entry for entry in live_data if normalize_string(entry.get('network_name', '')) == normalize_string(site_name)), None)
                if live_entry:
                    arin_data = {
                        'wan1_ip': live_entry.get('wan1', {}).get('ip', 'N/A'),
                        'wan1_provider': live_entry.get('wan1', {}).get('provider', 'N/A'),
                        'wan2_ip': live_entry.get('wan2', {}).get('ip', 'N/A'),
                        'wan2_provider': live_entry.get('wan2', {}).get('provider', 'N/A')
                    }
            except Exception as e:
                print(f"DEBUG: Error reading ARIN data: {str(e)}")

        return {
            "raw_notes": notes_data.get("raw_notes", ""),
            "wan1_provider_notes": notes_data.get("wan1_provider_notes", ""),
            "wan1_speed_notes": notes_data.get("wan1_speed_notes", ""),
            "wan2_provider_notes": notes_data.get("wan2_provider_notes", ""),
            "wan2_speed_notes": notes_data.get("wan2_speed_notes", ""),
            "wan1_provider_dsr": dsr_data.get('wan1', {}).get('provider', ''),
            "wan1_speed_dsr": dsr_data.get('wan1', {}).get('speed', ''),
            "wan2_provider_dsr": dsr_data.get('wan2', {}).get('provider', ''),
            "wan2_speed_dsr": dsr_data.get('wan2', {}).get('speed', ''),
            "csv_data": csv_data,
            **arin_data  # Merge ARIN data into the response
        }

    else:
        # Handle confirmation with updated data
        if not data:
            return {"error": "No data provided for confirmation"}

        result = update_enriched_json(site_name, data)
        if result.get("success"):
            remove_from_pushed_log(site_name)
            print(f"[Meraki Confirm] ✅ {site_name} updated and removed from push log")
        return result