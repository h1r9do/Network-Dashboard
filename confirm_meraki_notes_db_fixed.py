"""
Database version of confirm_meraki_notes.py with extensive logging and push tracking
Works with PostgreSQL database instead of JSON files
"""

import os
import json
import re
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import jsonify, current_app
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                logger.warning(f"Rate limit hit, backing off for {wait_time} seconds")
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
            logger.error(f"API update error: {e}")
            if hasattr(response, 'status_code'):
                logger.error(f"Response status: {response.status_code}")
                if response.status_code == 429:
                    wait_time = backoff_factor * (2 ** attempt) + (attempt * 0.1)
                    logger.warning(f"Rate limit hit, backing off for {wait_time} seconds")
                    time.sleep(wait_time)
            if attempt == max_retries - 1:
                return {"error": str(e)}
            else:
                time.sleep(backoff_factor * (2 ** attempt))
    return {"error": "Max retries exceeded"}

def determine_provider_speed(site_name):
    """Get provider and speed from database for a specific site"""
    logger.info(f"Determining provider/speed for site: {site_name}")
    session = Session()
    try:
        # Get primary (WAN1) and secondary (WAN2) circuits
        result = session.execute(text("""
            SELECT 
                CASE 
                    WHEN LOWER(circuit_purpose) IN ('primary', 'primary internet') THEN 'wan1'
                    WHEN LOWER(circuit_purpose) IN ('secondary', 'secondary internet', 'backup') THEN 'wan2'
                    ELSE 'unknown'
                END as wan_type,
                provider_name,
                details_ordered_service_speed,
                billing_monthly_cost,
                status,
                ip_address_start
            FROM circuits 
            WHERE LOWER(site_name) = LOWER(:site_name)
                AND LOWER(status) = 'enabled'
                AND LOWER(circuit_purpose) IN ('primary', 'secondary', 'primary internet', 'secondary internet', 'backup')
            ORDER BY 
                CASE LOWER(circuit_purpose)
                    WHEN 'primary' THEN 1
                    WHEN 'primary internet' THEN 2
                    WHEN 'secondary' THEN 3
                    WHEN 'secondary internet' THEN 4
                    WHEN 'backup' THEN 5
                END
        """), {'site_name': site_name})
        
        circuits = result.fetchall()
        logger.info(f"Found {len(circuits)} circuits for {site_name}")
        
        wan1_data = {}
        wan2_data = {}
        
        for wan_type, provider, speed, cost, status, ip in circuits:
            logger.info(f"Circuit: WAN={wan_type}, Provider={provider}, Speed={speed}, Status={status}")
            if wan_type == 'wan1' and not wan1_data:
                wan1_data = {
                    'provider': provider or '',
                    'speed': speed or '',
                    'cost': cost or 0,
                    'ip': ip or ''
                }
            elif wan_type == 'wan2' and not wan2_data:
                wan2_data = {
                    'provider': provider or '',
                    'speed': speed or '',
                    'cost': cost or 0,
                    'ip': ip or ''
                }
        
        return {
            'wan1': wan1_data,
            'wan2': wan2_data
        }
        
    except Exception as e:
        logger.error(f"Error determining provider/speed: {e}")
        return {'wan1': {}, 'wan2': {}}
    finally:
        session.close()


def get_meraki_notes(site_name):
    """Get current Meraki device notes and parsed provider data for a site"""
    logger.info(f"Getting Meraki notes for: {site_name}")
    session = Session()
    try:
        # Get device serial, notes AND parsed labels from meraki_inventory
        result = session.execute(text("""
            SELECT device_serial, device_notes,
                   wan1_provider_label, wan1_speed_label,
                   wan2_provider_label, wan2_speed_label
            FROM meraki_inventory
            WHERE LOWER(network_name) = LOWER(:site_name)
            AND device_model LIKE 'MX%'
            ORDER BY last_updated DESC
            LIMIT 1
        """), {'site_name': site_name})
        
        device_data = result.fetchone()
        if not device_data:
            return {"raw_notes": "No device found in Meraki inventory"}
        
        device_serial, raw_notes, wan1_provider, wan1_speed, wan2_provider, wan2_speed = device_data
        
        return {
            "raw_notes": raw_notes or 'No notes set on device',
            "wan1_provider_notes": wan1_provider or '',
            "wan1_speed_notes": wan1_speed or '',
            "wan2_provider_notes": wan2_provider or '',
            "wan2_speed_notes": wan2_speed or ''
        }
        
    except Exception as e:
        logger.error(f"Error getting Meraki notes: {e}")
        return {"raw_notes": f"Error retrieving Meraki notes: {str(e)}"}
    finally:
        session.close()

def get_csv_data(site_name):
    """Get CSV tracking data for a site - ENABLED CIRCUITS ONLY"""
    session = Session()
    try:
        # Get ENABLED circuit data from database 
        result = session.execute(text("""
            SELECT 
                site_name, date_record_updated, circuit_purpose, status, 
                provider_name, details_ordered_service_speed, billing_monthly_cost
            FROM circuits
            WHERE LOWER(site_name) = LOWER(:site_name)
                AND LOWER(status) = 'enabled'
            ORDER BY 
                CASE LOWER(circuit_purpose)
                    WHEN 'primary' THEN 1
                    WHEN 'primary internet' THEN 2  
                    WHEN 'secondary' THEN 3
                    WHEN 'secondary internet' THEN 4
                    WHEN 'backup' THEN 5
                    ELSE 6
                END
        """), {'site_name': site_name})
        
        circuits = result.fetchall()
        csv_data = []
        
        for circuit in circuits:
            csv_data.append({
                "Site Name": circuit[0] or '',
                "Date": circuit[1].strftime('%Y-%m-%d') if circuit[1] else '',
                "DSR Circuit Purpose": circuit[2] or '',
                "Status": circuit[3] or '',
                "Provider Name": circuit[4] or '',
                "Speed": circuit[5] or '',
                "Price": f"${float(circuit[6]):.2f}" if circuit[6] else '$0.00'
            })
        
        return csv_data
        
    except Exception as e:
        logger.error(f"Error getting CSV data: {e}")
        return [{"error": f"Error retrieving tracking data: {str(e)}"}]
    finally:
        session.close()

def get_arin_data(site_name):
    """Get ARIN/IP information for a site from meraki_inventory"""
    session = Session()
    try:
        # Get IP addresses, ARIN providers, and parsed notes data from meraki_inventory table
        result = session.execute(text("""
            SELECT wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider,
                   wan1_provider_label, wan1_provider_comparison,
                   wan2_provider_label, wan2_provider_comparison
            FROM meraki_inventory
            WHERE LOWER(network_name) = LOWER(:site_name)
            AND device_model LIKE 'MX%'
            ORDER BY last_updated DESC
            LIMIT 1
        """), {'site_name': site_name})
        
        meraki_data = result.fetchone()
        if meraki_data:
            # Return IPs, ARIN providers, and comparison data from meraki_inventory
            return {
                'wan1_ip': meraki_data[0] or 'N/A',
                'wan1_arin_provider': meraki_data[1] or 'N/A',
                'wan2_ip': meraki_data[2] or 'N/A', 
                'wan2_arin_provider': meraki_data[3] or 'N/A',
                'wan1_provider_label': meraki_data[4] or '',
                'wan1_comparison': meraki_data[5] or '',
                'wan2_provider_label': meraki_data[6] or '',
                'wan2_comparison': meraki_data[7] or ''
            }
        else:
            # Fallback to circuits table
            result = session.execute(text("""
                SELECT ip_address_start, provider_name, circuit_purpose
                FROM circuits 
                WHERE LOWER(site_name) = LOWER(:site_name)
                AND ip_address_start IS NOT NULL
                ORDER BY 
                    CASE LOWER(circuit_purpose)
                        WHEN 'primary' THEN 1
                        WHEN 'secondary' THEN 2
                        ELSE 3
                    END
            """), {'site_name': site_name})
            
            circuits = result.fetchall()
            arin_data = {
                'wan1_ip': 'N/A',
                'wan1_arin_provider': 'N/A', 
                'wan2_ip': 'N/A',
                'wan2_arin_provider': 'N/A'
            }
            
            for ip, provider, purpose in circuits:
                if purpose and 'primary' in purpose.lower() and arin_data['wan1_ip'] == 'N/A':
                    arin_data['wan1_ip'] = ip or 'N/A'
                    arin_data['wan1_arin_provider'] = provider or 'N/A'
                elif purpose and ('secondary' in purpose.lower() or 'backup' in purpose.lower()) and arin_data['wan2_ip'] == 'N/A':
                    arin_data['wan2_ip'] = ip or 'N/A'
                    arin_data['wan2_arin_provider'] = provider or 'N/A'
            
            return arin_data
            
    except Exception as e:
        logger.error(f"Error getting ARIN data: {e}")
        return {
            'wan1_ip': 'N/A',
            'wan1_arin_provider': 'N/A',
            'wan2_ip': 'N/A', 
            'wan2_arin_provider': 'N/A'
        }
    finally:
        session.close()

def confirm_site(site_name):
    """Get circuit confirmation data for a site with all required modal data"""
    logger.info(f"Confirming site: {site_name}")
    session = Session()
    try:
        # Get enriched circuit data
        result = session.execute(text("""
            SELECT 
                wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
                wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed,
                last_updated, pushed_to_meraki, pushed_date
            FROM enriched_circuits
            WHERE LOWER(network_name) = LOWER(:site_name)
        """), {'site_name': site_name})
        
        enriched = result.fetchone()
        
        # Get additional data for modal
        meraki_notes = get_meraki_notes(site_name)
        csv_data = get_csv_data(site_name)
        arin_data = get_arin_data(site_name)
        
        # Get DSR data from circuits
        circuit_data = determine_provider_speed(site_name)
        
        if enriched:
            logger.info(f"Found enriched data for {site_name}")
            logger.info(f"WAN1: {enriched[0]} / {enriched[1]} / Confirmed: {enriched[3]}")
            logger.info(f"WAN2: {enriched[4]} / {enriched[5]} / Confirmed: {enriched[7]}")
            logger.info(f"Already pushed: {enriched[9]}, Push date: {enriched[10]}")
            
            # Get costs from circuit_data
            wan1_cost = circuit_data.get('wan1', {}).get('monthly_cost', '$0.00')
            wan2_cost = circuit_data.get('wan2', {}).get('monthly_cost', '$0.00')
            
            response = {
                "success": True,
                "site_name": site_name,
                "wan1": {
                    "provider": enriched[0] or '',
                    "speed": enriched[1] or '',
                    "monthly_cost": wan1_cost,
                    "circuit_role": enriched[2] or 'Primary',
                    "confirmed": enriched[3] or False
                },
                "wan2": {
                    "provider": enriched[4] or '',
                    "speed": enriched[5] or '',
                    "monthly_cost": wan2_cost,
                    "circuit_role": enriched[6] or 'Secondary',
                    "confirmed": enriched[7] or False
                },
                "already_pushed": enriched[9] or False,
                "pushed_date": enriched[10].isoformat() if enriched[10] else None
            }
        else:
            logger.warning(f"No enriched data found for {site_name}, using circuits data")
            response = {
                "success": True,
                "site_name": site_name,
                "wan1": circuit_data.get('wan1', {}),
                "wan2": circuit_data.get('wan2', {}),
                "already_pushed": False,
                "pushed_date": None
            }
        
        # Add modal data
        response.update({
            "raw_notes": meraki_notes.get("raw_notes", ""),
            "wan1_provider_notes": meraki_notes.get("wan1_provider_notes", ""),
            "wan1_speed_notes": meraki_notes.get("wan1_speed_notes", ""),
            "wan2_provider_notes": meraki_notes.get("wan2_provider_notes", ""),
            "wan2_speed_notes": meraki_notes.get("wan2_speed_notes", ""),
            "wan1_provider_dsr": circuit_data.get('wan1', {}).get('provider', ''),
            "wan1_speed_dsr": circuit_data.get('wan1', {}).get('speed', ''),
            "wan2_provider_dsr": circuit_data.get('wan2', {}).get('provider', ''),
            "wan2_speed_dsr": circuit_data.get('wan2', {}).get('speed', ''),
            "csv_data": csv_data,
            **arin_data  # Add ARIN data (wan1_ip, wan1_provider, wan2_ip, wan2_provider)
        })
        
        return response
            
    except Exception as e:
        logger.error(f"Error in confirm_site: {e}")
        return {"error": str(e)}
    finally:
        session.close()

def reset_confirmation(site_name):
    """Reset confirmation status for a site"""
    logger.info(f"Resetting confirmation for site: {site_name}")
    session = Session()
    try:
        # Reset confirmation and push status
        session.execute(text("""
            UPDATE enriched_circuits
            SET wan1_confirmed = FALSE,
                wan2_confirmed = FALSE,
                pushed_to_meraki = FALSE,
                pushed_date = NULL,
                last_updated = CURRENT_TIMESTAMP
            WHERE LOWER(network_name) = LOWER(:site_name)
        """), {'site_name': site_name})
        
        session.commit()
        logger.info(f"Successfully reset confirmation for {site_name}")
        
        return {"success": True, "message": f"Reset confirmation for {site_name}"}
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error in reset_confirmation: {e}")
        return {"error": str(e)}
    finally:
        session.close()

def push_to_meraki(sites):
    """Push confirmed circuits to Meraki devices"""
    logger.info(f"Starting push_to_meraki for {len(sites)} sites")
    session = Session()
    results = []
    
    try:
        for site_name in sites:
            logger.info(f"\nProcessing site: {site_name}")
            
            # Get enriched circuit data and check if already pushed
            result = session.execute(text("""
                SELECT 
                    wan1_provider, wan1_speed, wan2_provider, wan2_speed,
                    wan1_confirmed, wan2_confirmed, pushed_to_meraki, pushed_date,
                    last_updated
                FROM enriched_circuits
                WHERE LOWER(network_name) = LOWER(:site_name)
            """), {'site_name': site_name})
            
            enriched = result.fetchone()
            
            if not enriched:
                logger.warning(f"No enriched data found for {site_name}")
                results.append({"site": site_name, "error": "No enriched circuit data found"})
                continue
            
            # No longer checking if already pushed - always push when requested
            
            # Check if confirmed
            if not enriched[4] and not enriched[5]:  # Neither WAN confirmed
                logger.warning(f"No confirmed circuits for {site_name}")
                results.append({"site": site_name, "error": "No confirmed circuits"})
                continue
            
            # Get device serial from meraki_inventory
            result = session.execute(text("""
                SELECT device_serial
                FROM meraki_inventory
                WHERE LOWER(network_name) = LOWER(:site_name)
                AND device_model LIKE 'MX%'
                LIMIT 1
            """), {'site_name': site_name})
            
            device_data = result.fetchone()
            if not device_data or not device_data[0]:
                logger.error(f"No device serial found for {site_name}")
                results.append({"site": site_name, "error": "No device serial found"})
                continue
            
            device_serial = device_data[0]
            logger.info(f"Found device serial: {device_serial}")
            
            # Build notes string in the correct format:
            # WAN 1
            # Provider
            # Speed
            # WAN 2
            # Provider
            # Speed
            notes_parts = []
            if enriched[4] and enriched[0] and enriched[1]:  # wan1_confirmed
                notes_parts.extend([
                    "WAN 1",
                    enriched[0],  # Provider
                    enriched[1]   # Speed
                ])
                logger.info(f"Adding WAN1: Provider={enriched[0]}, Speed={enriched[1]}")
            if enriched[5] and enriched[2] and enriched[3]:  # wan2_confirmed
                notes_parts.extend([
                    "WAN 2",
                    enriched[2],  # Provider
                    enriched[3]   # Speed
                ])
                logger.info(f"Adding WAN2: Provider={enriched[2]}, Speed={enriched[3]}")
            
            if not notes_parts:
                logger.warning(f"No valid circuit data to push for {site_name}")
                results.append({"site": site_name, "error": "No valid circuit data to push"})
                continue
            
            notes = "\n".join(notes_parts)
            logger.info(f"Final notes for {site_name}: {notes}")
            
            # Update device notes via Meraki API
            device_url = f"{BASE_URL}/devices/{device_serial}"
            logger.info(f"Updating Meraki device at: {device_url}")
            
            update_result = make_api_update(device_url, {"notes": notes})
            
            if "error" in update_result:
                logger.error(f"Meraki API error for {site_name}: {update_result['error']}")
                results.append({"site": site_name, "error": update_result["error"]})
            else:
                logger.info(f"Successfully pushed to Meraki for {site_name}")
                results.append({"site": site_name, "success": True, "notes": notes})
                
                # Update pushed status in database
                session.execute(text("""
                    UPDATE enriched_circuits
                    SET pushed_to_meraki = TRUE,
                        pushed_date = CURRENT_TIMESTAMP,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE LOWER(network_name) = LOWER(:site_name)
                """), {'site_name': site_name})
                
                logger.info(f"Updated push status in database for {site_name}")
        
        session.commit()
        
        success_count = len([r for r in results if r.get("success")])
        already_pushed_count = len([r for r in results if r.get("already_pushed")])
        
        logger.info(f"\nPush to Meraki complete:")
        logger.info(f"Total sites: {len(sites)}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Already pushed: {already_pushed_count}")
        logger.info(f"Failed: {len(sites) - success_count - already_pushed_count}")
        
        return {
            "success": True,
            "results": results,
            "total": len(sites),
            "successful": success_count,
            "already_pushed": already_pushed_count
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error in push_to_meraki: {e}")
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