#!/usr/bin/env python3
"""
Enhanced ARIN refresh functionality that handles sites without Meraki devices
This will be integrated into dsrcircuits_blueprint.py
"""

import requests
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def query_arin_rdap(ip):
    """Query ARIN RDAP API for provider information"""
    if not ip or ip == '0.0.0.0' or ip == 'N/A':
        return 'Unknown'
    
    try:
        # Validate IP format
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if not ip_pattern.match(ip):
            logger.warning(f"Invalid IP format: {ip}")
            return 'Unknown'
        
        arin_url = f"https://rdap.arin.net/registry/ip/{ip}"
        arin_response = requests.get(arin_url, timeout=10)
        
        if arin_response.status_code == 200:
            arin_data = arin_response.json()
            
            # Try multiple methods to extract provider name
            # Method 1: Check entities for organization name
            if 'entities' in arin_data:
                for entity in arin_data['entities']:
                    if 'vcardArray' in entity:
                        for vcard in entity['vcardArray'][1]:
                            if vcard[0] == 'fn':
                                provider = vcard[3]
                                # Clean up common provider names
                                provider = provider.replace(', Inc.', '')
                                provider = provider.replace(' Inc.', '')
                                provider = provider.replace(' LLC', '')
                                return provider
            
            # Method 2: Check name field
            if 'name' in arin_data:
                return arin_data['name']
            
            # Method 3: Check handle
            if 'handle' in arin_data:
                return arin_data['handle']
                
        elif arin_response.status_code == 404:
            logger.info(f"No ARIN record found for IP: {ip}")
            return 'Unknown'
        else:
            logger.warning(f"ARIN query failed with status {arin_response.status_code} for IP: {ip}")
            return 'Unknown'
            
    except requests.exceptions.Timeout:
        logger.error(f"ARIN query timeout for IP: {ip}")
        return 'Timeout'
    except Exception as e:
        logger.error(f"Error querying ARIN for IP {ip}: {e}")
        return 'Error'

def refresh_arin_data_enhanced(site_name, db, Circuit, MerakiInventory, EnrichedCircuits):
    """
    Enhanced ARIN refresh that handles multiple data sources
    Returns: dict with success status and data
    """
    result = {
        'success': False,
        'message': '',
        'wan1_ip': None,
        'wan1_arin_provider': None,
        'wan2_ip': None,
        'wan2_arin_provider': None,
        'source': None,
        'warnings': []
    }
    
    try:
        # Strategy 1: Try Meraki first (original approach)
        meraki_device = MerakiInventory.query.filter(
            db.func.lower(MerakiInventory.network_name) == db.func.lower(site_name)
        ).first()
        
        if meraki_device and meraki_device.device_serial:
            # Try to get fresh data from Meraki API
            wan1_ip, wan2_ip = get_meraki_uplink_ips(meraki_device.device_serial)
            
            if wan1_ip or wan2_ip:
                result['wan1_ip'] = wan1_ip
                result['wan2_ip'] = wan2_ip
                result['source'] = 'meraki_api'
            else:
                # Use existing data from database
                result['wan1_ip'] = meraki_device.wan1_ip
                result['wan2_ip'] = meraki_device.wan2_ip
                result['source'] = 'meraki_db'
                result['warnings'].append('Using cached Meraki data')
        
        # Strategy 2: Check enriched_circuits table
        if not result['wan1_ip'] and not result['wan2_ip']:
            enriched = EnrichedCircuits.query.filter(
                db.func.lower(EnrichedCircuits.site_name) == db.func.lower(site_name)
            ).first()
            
            if enriched:
                result['wan1_ip'] = enriched.wan1_public_ip or enriched.wan1_ip
                result['wan2_ip'] = enriched.wan2_public_ip or enriched.wan2_ip
                result['source'] = 'enriched_circuits'
                result['warnings'].append('No Meraki device found, using enriched circuits data')
        
        # Strategy 3: Check circuits table for Non-DSR circuits
        if not result['wan1_ip'] and not result['wan2_ip']:
            circuits = Circuit.query.filter(
                db.func.lower(Circuit.site_name) == db.func.lower(site_name),
                Circuit.source == 'Non-DSR'
            ).all()
            
            if circuits:
                for circuit in circuits:
                    if circuit.wan1_ip and not result['wan1_ip']:
                        result['wan1_ip'] = circuit.wan1_ip
                    if circuit.wan2_ip and not result['wan2_ip']:
                        result['wan2_ip'] = circuit.wan2_ip
                
                if result['wan1_ip'] or result['wan2_ip']:
                    result['source'] = 'non_dsr_circuits'
                    result['warnings'].append('Using Non-DSR circuit data')
        
        # Strategy 4: Manual IP entry fallback
        if not result['wan1_ip'] and not result['wan2_ip']:
            result['warnings'].append('No IP data found in any source. Manual entry may be required.')
            result['source'] = 'none'
        
        # Query ARIN for any IPs we found
        if result['wan1_ip']:
            result['wan1_arin_provider'] = query_arin_rdap(result['wan1_ip'])
        else:
            result['wan1_arin_provider'] = 'No IP'
            
        if result['wan2_ip']:
            result['wan2_arin_provider'] = query_arin_rdap(result['wan2_ip'])
        else:
            result['wan2_arin_provider'] = 'No IP'
        
        # Update database based on source
        if result['source'] == 'meraki_api' or result['source'] == 'meraki_db':
            if meraki_device:
                meraki_device.wan1_ip = result['wan1_ip']
                meraki_device.wan2_ip = result['wan2_ip']
                meraki_device.wan1_arin_provider = result['wan1_arin_provider']
                meraki_device.wan2_arin_provider = result['wan2_arin_provider']
                meraki_device.last_updated = datetime.utcnow()
        
        # Update enriched_circuits if we have data
        if result['wan1_ip'] or result['wan2_ip']:
            enriched = EnrichedCircuits.query.filter(
                db.func.lower(EnrichedCircuits.site_name) == db.func.lower(site_name)
            ).first()
            
            if enriched:
                if result['wan1_ip']:
                    enriched.wan1_ip = result['wan1_ip']
                    enriched.wan1_arin_provider = result['wan1_arin_provider']
                if result['wan2_ip']:
                    enriched.wan2_ip = result['wan2_ip']
                    enriched.wan2_arin_provider = result['wan2_arin_provider']
                enriched.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        result['success'] = True
        result['message'] = f'ARIN data refreshed from {result["source"]}'
        
        logger.info(f"Enhanced ARIN refresh for {site_name}: "
                   f"WAN1={result['wan1_ip']}({result['wan1_arin_provider']}), "
                   f"WAN2={result['wan2_ip']}({result['wan2_arin_provider']}), "
                   f"Source={result['source']}")
        
    except Exception as e:
        logger.error(f"Error in enhanced ARIN refresh for {site_name}: {e}")
        db.session.rollback()
        result['success'] = False
        result['message'] = str(e)
    
    return result

def get_meraki_uplink_ips(device_serial):
    """Get uplink IPs from Meraki API for a specific device"""
    # This would be implemented with actual Meraki API calls
    # For now, returning None to indicate no data
    return None, None