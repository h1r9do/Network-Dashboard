"""
Database version of confirm_meraki_notes.py
Works with PostgreSQL database instead of JSON files
"""

import os
import json
import re
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from flask import jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
ORG_NAME = "DTC-Store-Inventory-All"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits')

# Create database session
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# API limits
MAX_REQUESTS = 900
REQUEST_WINDOW = 300
REQUESTS = []

# Provider keywords
PROVIDER_KEYWORDS = {
    'spectrum': 'Charter Communications',
    'charter': 'Charter Communications',
    'at&t': 'AT&T',
    'att': 'AT&T',
    'comcast': 'Comcast',
    'verizon': 'Verizon Business',
    'cox': 'Cox Communications',
    'centurylink': 'CenturyLink',
    'frontier': 'Frontier Communications',
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
            time.sleep(REQUEST_WINDOW / MAX_REQUESTS)
            clean_request_timestamps()
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            REQUESTS.append(time.time())
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(response, 'status_code') and response.status_code == 429:
                wait_time = backoff_factor * (2 ** attempt) + (attempt * 0.1)
                print(f"Rate limit hit, backing off for {wait_time} seconds")
                time.sleep(wait_time)
            elif attempt == max_retries - 1:
                return {"error": str(e)}
            else:
                time.sleep(backoff_factor * (2 ** attempt))
    return {"error": "Max retries exceeded"}

def make_api_update(url, data, max_retries=5, backoff_factor=1):
    headers = get_headers()
    for attempt in range(max_retries):
        clean_request_timestamps()
        if len(REQUESTS) >= MAX_REQUESTS:
            time.sleep(REQUEST_WINDOW / MAX_REQUESTS)
            clean_request_timestamps()
        
        try:
            response = requests.put(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            REQUESTS.append(time.time())
            return {"success": True}
        except requests.exceptions.RequestException as e:
            if hasattr(response, 'status_code') and response.status_code == 429:
                wait_time = backoff_factor * (2 ** attempt) + (attempt * 0.1)
                print(f"Rate limit hit, backing off for {wait_time} seconds")
                time.sleep(wait_time)
            elif attempt == max_retries - 1:
                return {"error": str(e)}
            else:
                time.sleep(backoff_factor * (2 ** attempt))
    return {"error": "Max retries exceeded"}

def normalize_string(s):
    if not s:
        return "UNKNOWN"
    return re.sub(r'\s+', ' ', s.strip()).upper()

def parse_raw_notes(raw_notes):
    """Parse device notes for WAN provider and speed info"""
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
            
            # Convert to M if needed
            if up_unit in ['G', 'GB']:
                up_speed *= 1000
                up_unit = 'M'
            if down_unit in ['G', 'GB']:
                down_speed *= 1000
                down_unit = 'M'
            
            speed_str = f"{up_speed:.1f}M x {down_speed:.1f}M"
            provider_name = segment[:match.start()].strip().replace('DSR ', '')
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            return provider_name, speed_str
        else:
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', segment).strip().replace('DSR ', '')
            return provider_name, ""
    
    # Extract WAN1 and WAN2 text
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

def get_organization_id():
    """Get Meraki organization ID"""
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url)
    for org in orgs:
        if org.get("name") == ORG_NAME:
            return org.get("id")
    return None

def confirm_site(site_name):
    """
    Confirm site circuit information from database
    Returns popup data for the confirmation dialog
    """
    session = Session()
    
    try:
        # Get enriched circuit data from database
        result = session.execute(text("""
            SELECT network_name, device_tags, 
                   wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
                   wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed,
                   pushed_to_meraki, pushed_date
            FROM enriched_circuits
            WHERE LOWER(network_name) = LOWER(:site_name)
        """), {'site_name': site_name})
        
        enriched_data = result.fetchone()
        
        if not enriched_data:
            return {"error": f"No enriched data found for {site_name}"}
        
        # Get Meraki inventory data with IP and ARIN info
        # Also join with enriched_circuits to get provider labels and speeds
        result = session.execute(text("""
            SELECT 
                mi.device_serial, mi.device_model, mi.device_name, mi.device_tags,
                mi.wan1_ip, mi.wan1_arin_provider, ec.wan1_provider, ec.wan1_speed,
                mi.wan2_ip, mi.wan2_arin_provider, ec.wan2_provider, ec.wan2_speed
            FROM meraki_inventory mi
            LEFT JOIN enriched_circuits ec ON mi.network_name = ec.network_name
            WHERE LOWER(mi.network_name) = LOWER(:site_name)
            AND mi.device_model LIKE 'MX%'
        """), {'site_name': site_name})
        
        meraki_data = result.fetchone()
        
        if not meraki_data:
            return {"error": f"No Meraki data found for {site_name}"}
        
        # Get ALL circuit data from circuits table only (DSR and Non-DSR)
        result = session.execute(text("""
            SELECT circuit_purpose, provider_name, details_ordered_service_speed, 
                   billing_monthly_cost, ip_address_start, data_source, 
                   details_service_speed, id, site_id
            FROM circuits
            WHERE LOWER(site_name) = LOWER(:site_name) 
            AND status = 'Enabled'
            AND provider_name IS NOT NULL 
            AND provider_name != 'NaN'
            AND provider_name != ''
            ORDER BY data_source, circuit_purpose
        """), {'site_name': site_name})
        
        tracking_data = []
        all_circuits = []
        for row in result:
            circuit_data = {
                'Circuit Purpose': row[0],
                'provider_name': row[1],
                'speed': row[2],
                'billing_monthly_cost': row[3],
                'ip_address_start': row[4],
                'data_source': row[5],
                'details_service_speed': row[6],
                'id': row[7]
            }
            tracking_data.append(circuit_data)
            
            # Add all valid circuits for the modal
            all_circuits.append({
                'id': row[7],
                'site_name': site_name,
                'site_id': row[8] or '',  # Use site_id from database
                'provider_name': row[1],
                'details_ordered_service_speed': row[2],
                'details_service_speed': row[6],
                'billing_monthly_cost': row[3],
                'status': 'Enabled',
                'data_source': row[5],
                'date_created': '2025-07-11'  # Default date
            })
        
        # Parse device tags
        device_tags = []
        if meraki_data[3]:  # device_tags from meraki_inventory
            try:
                device_tags = json.loads(meraki_data[3])
            except:
                device_tags = []
        
        # Fetch current device notes from Meraki API
        org_id = get_organization_id()
        current_notes = ''
        if org_id and meraki_data[0]:  # device_serial
            device_url = f"{BASE_URL}/devices/{meraki_data[0]}"
            device_info = make_api_request(device_url)
            current_notes = device_info.get('notes', '') if isinstance(device_info, dict) else ''
            raw_notes = current_notes
        else:
            raw_notes = ''
        
        # Smart matching: Match ARIN providers to circuit data
        wan1_arin = meraki_data[5] or ''  # wan1_arin_provider
        wan2_arin = meraki_data[9] or ''  # wan2_arin_provider
        
        wan1_circuit = None
        wan2_circuit = None
        wan1_cost = '$0.00'
        wan2_cost = '$0.00'
        
        # Match WAN1 ARIN provider to circuit data
        if wan1_arin:
            for track in tracking_data:
                if track['provider_name'] and (
                    wan1_arin.upper() in track['provider_name'].upper() or
                    track['provider_name'].upper() in wan1_arin.upper() or
                    # Handle common provider variations
                    ('FRONTIER' in wan1_arin.upper() and 'FRONTIER' in track['provider_name'].upper()) or
                    ('ALLO' in wan1_arin.upper() and 'ALLO' in track['provider_name'].upper()) or
                    ('COMCAST' in wan1_arin.upper() and 'COMCAST' in track['provider_name'].upper())
                ):
                    wan1_circuit = track
                    if track['billing_monthly_cost']:
                        try:
                            wan1_cost = f"${float(track['billing_monthly_cost']):.2f}"
                        except:
                            wan1_cost = '$0.00'
                    break
        
        # Match WAN2 ARIN provider to circuit data
        if wan2_arin:
            for track in tracking_data:
                if track['provider_name'] and track != wan1_circuit and (
                    wan2_arin.upper() in track['provider_name'].upper() or
                    track['provider_name'].upper() in wan2_arin.upper() or
                    # Handle common provider variations
                    ('FRONTIER' in wan2_arin.upper() and 'FRONTIER' in track['provider_name'].upper()) or
                    ('ALLO' in wan2_arin.upper() and 'ALLO' in track['provider_name'].upper()) or
                    ('COMCAST' in wan2_arin.upper() and 'COMCAST' in track['provider_name'].upper())
                ):
                    wan2_circuit = track
                    if track['billing_monthly_cost']:
                        try:
                            wan2_cost = f"${float(track['billing_monthly_cost']):.2f}"
                        except:
                            wan2_cost = '$0.00'
                    break
        
        # Fallback: if no ARIN match, use enriched data for remaining circuits
        if not wan1_circuit:
            wan1_provider = enriched_data[2] or ''
            if wan1_provider:
                for track in tracking_data:
                    if track['provider_name'] and wan1_provider.upper() in track['provider_name'].upper():
                        wan1_circuit = track
                        if track['billing_monthly_cost']:
                            try:
                                wan1_cost = f"${float(track['billing_monthly_cost']):.2f}"
                            except:
                                wan1_cost = '$0.00'
                        break
        
        if not wan2_circuit:
            wan2_provider = enriched_data[6] or ''
            if wan2_provider:
                for track in tracking_data:
                    if track['provider_name'] and track != wan1_circuit and wan2_provider.upper() in track['provider_name'].upper():
                        wan2_circuit = track
                        if track['billing_monthly_cost']:
                            try:
                                wan2_cost = f"${float(track['billing_monthly_cost']):.2f}"
                            except:
                                wan2_cost = '$0.00'
                        break
        
        # Remove CSV data - use database only
        csv_data = []
        
        # Build response in expected format for modal
        response_data = {
            'success': True,
            'site_name': site_name,
            'raw_notes': raw_notes,
            'csv_data': csv_data,
            'wan1': {
                'provider': enriched_data[2] or '',
                'speed': enriched_data[3] or '',
                'monthly_cost': wan1_cost,
                'circuit_role': enriched_data[4] or 'Primary',
                'confirmed': enriched_data[5] or False
            },
            'wan2': {
                'provider': enriched_data[6] or '',
                'speed': enriched_data[7] or '',
                'monthly_cost': wan2_cost,
                'circuit_role': enriched_data[8] or 'Secondary',
                'confirmed': enriched_data[9] or False
            },
            # Add comparison data for modal
            'wan1_ip': meraki_data[4] or '',
            'wan1_arin_provider': meraki_data[5] or '',
            'wan1_provider_label': meraki_data[6] or '',
            'wan1_provider_notes': enriched_data[2] or '',
            'wan1_provider_dsr': wan1_circuit['provider_name'] if wan1_circuit else '',
            'wan1_speed_notes': enriched_data[3] or '',
            'wan1_speed_dsr': wan1_circuit['speed'] if wan1_circuit else '',
            'wan1_comparison': 'Match' if meraki_data[5] and enriched_data[2] and meraki_data[5].upper() in enriched_data[2].upper() else 'No match',
            'wan2_ip': meraki_data[8] or '',
            'wan2_arin_provider': meraki_data[9] or '',
            'wan2_provider_label': meraki_data[10] or '',
            'wan2_provider_notes': enriched_data[6] or '',
            'wan2_provider_dsr': wan2_circuit['provider_name'] if wan2_circuit else '',
            'wan2_speed_notes': enriched_data[7] or '',
            'wan2_speed_dsr': wan2_circuit['speed'] if wan2_circuit else '',
            'wan2_comparison': 'Match' if meraki_data[9] and enriched_data[6] and meraki_data[9].upper() in enriched_data[6].upper() else 'No match',
            'already_pushed': enriched_data[10] if len(enriched_data) > 10 else False,
            'pushed_date': enriched_data[11].isoformat() if len(enriched_data) > 11 and enriched_data[11] else None,
            # Add all circuits from database for the enhanced modal
            'all_circuits': all_circuits
        }
        
        return response_data
        
    except Exception as e:
        print(f"Error in confirm_site: {e}")
        return {"error": str(e)}
    finally:
        session.close()

def reset_confirmation(site_name):
    """
    Reset confirmation status for a site in the database
    """
    session = Session()
    
    try:
        session.execute(text("""
            UPDATE enriched_circuits
            SET wan1_confirmed = FALSE,
                wan2_confirmed = FALSE,
                last_updated = CURRENT_TIMESTAMP
            WHERE LOWER(network_name) = LOWER(:site_name)
        """), {'site_name': site_name})
        
        session.commit()
        
        return {"success": True, "message": f"Reset confirmation for {site_name}"}
        
    except Exception as e:
        session.rollback()
        print(f"Error in reset_confirmation: {e}")
        return {"error": str(e)}
    finally:
        session.close()

def push_to_meraki(sites):
    """
    Push confirmed circuit data to Meraki device notes
    """
    session = Session()
    results = []
    
    try:
        for site_name in sites:
            # Get confirmed data from enriched_circuits
            result = session.execute(text("""
                SELECT wan1_provider, wan1_speed, wan2_provider, wan2_speed,
                       wan1_confirmed, wan2_confirmed
                FROM enriched_circuits
                WHERE LOWER(network_name) = LOWER(:site_name)
            """), {'site_name': site_name})
            
            enriched = result.fetchone()
            if not enriched:
                results.append({"site": site_name, "error": "No enriched data found"})
                continue
            
            # Only proceed if at least one WAN is confirmed
            if not enriched[4] and not enriched[5]:
                results.append({"site": site_name, "error": "No confirmed circuits"})
                continue
            
            # Get device serial from meraki_inventory
            result = session.execute(text("""
                SELECT device_serial
                FROM meraki_inventory
                WHERE LOWER(network_name) = LOWER(:site_name)
                AND device_model LIKE 'MX%'
            """), {'site_name': site_name})
            
            device_data = result.fetchone()
            if not device_data or not device_data[0]:
                results.append({"site": site_name, "error": "No device serial found"})
                continue
            
            device_serial = device_data[0]
            
            # Build notes string
            notes_parts = []
            if enriched[4] and enriched[0] and enriched[1]:  # wan1_confirmed
                notes_parts.append(f"WAN1: {enriched[0]} {enriched[1]}")
            if enriched[5] and enriched[2] and enriched[3]:  # wan2_confirmed
                notes_parts.append(f"WAN2: {enriched[2]} {enriched[3]}")
            
            if not notes_parts:
                results.append({"site": site_name, "error": "No valid circuit data to push"})
                continue
            
            notes = "\\n".join(notes_parts)
            
            # Update device notes via Meraki API
            device_url = f"{BASE_URL}/devices/{device_serial}"
            update_result = make_api_update(device_url, {"notes": notes})
            
            if "error" in update_result:
                results.append({"site": site_name, "error": update_result["error"]})
            else:
                results.append({"site": site_name, "success": True, "notes": notes})
                
                # Update confirmed status in database
                session.execute(text("""
                    UPDATE enriched_circuits
                    SET last_updated = CURRENT_TIMESTAMP
                    WHERE LOWER(network_name) = LOWER(:site_name)
                """), {'site_name': site_name})
        
        session.commit()
        
        return {
            "success": True,
            "results": results,
            "total": len(sites),
            "successful": len([r for r in results if r.get("success")])
        }
        
    except Exception as e:
        session.rollback()
        print(f"Error in push_to_meraki: {e}")
        return {"error": str(e)}
    finally:
        session.close()

# Dummy functions for compatibility
def load_pushed_log():
    return {}

def save_pushed_log(log):
    return True

def remove_from_pushed_log(site_name):
    return True