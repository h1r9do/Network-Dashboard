#!/usr/bin/env python3
"""Enhanced ARIN refresh function to fix CAL 24 issue"""

def refresh_arin_data_enhanced(site_name):
    """Enhanced ARIN refresh with better error handling and data sources"""
    try:
        import requests
        import os
        from dotenv import load_dotenv
        from datetime import datetime
        from flask import jsonify
        from sqlalchemy import func
        
        # Get Meraki API key
        meraki_api_key = os.getenv('MERAKI_API_KEY')
        if not meraki_api_key:
            load_dotenv('/usr/local/bin/meraki.env')
            meraki_api_key = os.getenv('MERAKI_API_KEY')
            if not meraki_api_key:
                return jsonify({'success': False, 'error': 'Meraki API key not configured'}), 500
        
        # Get organization ID
        org_name = "DTC-Store-Inventory-All"
        headers = {
            'X-Cisco-Meraki-API-Key': meraki_api_key,
            'Content-Type': 'application/json'
        }
        
        orgs_response = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers, timeout=30)
        orgs_response.raise_for_status()
        org_id = None
        for org in orgs_response.json():
            if org.get('name') == org_name:
                org_id = org['id']
                break
        
        if not org_id:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Initialize result structure
        result = {
            'wan1_ip': None,
            'wan1_arin_provider': None,
            'wan2_ip': None,
            'wan2_arin_provider': None,
            'source': None,
            'warnings': []
        }
        
        # Strategy 1: Try to get device from database first
        from models import MerakiInventory, EnrichedCircuit, Circuit, db
        
        meraki_device = MerakiInventory.query.filter(
            func.lower(MerakiInventory.network_name) == func.lower(site_name)
        ).first()
        
        # If we have a Meraki device, try API first
        if meraki_device and meraki_device.device_serial:
            device_serial = meraki_device.device_serial
            
            # Try to get fresh data from API
            try:
                uplink_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/appliance/uplink/statuses"
                response = requests.get(uplink_url, headers=headers, timeout=30)
                response.raise_for_status()
                all_uplinks = response.json()
                
                # Find uplinks for our device
                found_in_api = False
                for device_status in all_uplinks:
                    if device_status.get('serial') == device_serial:
                        found_in_api = True
                        uplinks = device_status.get('uplinks', [])
                        for uplink in uplinks:
                            if uplink.get('interface') == 'wan1':
                                result['wan1_ip'] = uplink.get('publicIp') or uplink.get('ip')
                            elif uplink.get('interface') == 'wan2':
                                result['wan2_ip'] = uplink.get('publicIp') or uplink.get('ip')
                        result['source'] = 'meraki_api'
                        break
                
                if not found_in_api:
                    result['warnings'].append(f'Device {device_serial} not found in Meraki API uplink status')
                        
            except requests.exceptions.RequestException as e:
                result['warnings'].append(f'Meraki API error: {str(e)}')
            
            # Fallback to cached Meraki data if API failed or no data
            if not result['wan1_ip'] and not result['wan2_ip']:
                if meraki_device.wan1_ip or meraki_device.wan2_ip:
                    result['wan1_ip'] = meraki_device.wan1_ip
                    result['wan2_ip'] = meraki_device.wan2_ip
                    result['source'] = 'meraki_db'
                    result['warnings'].append('Using cached Meraki data')
        
        # Strategy 2: Check enriched_circuits table
        if not result['wan1_ip'] and not result['wan2_ip']:
            enriched = EnrichedCircuit.query.filter(
                func.lower(EnrichedCircuit.network_name) == func.lower(site_name)
            ).first()
            
            if enriched and (enriched.wan1_ip or enriched.wan2_ip):
                result['wan1_ip'] = enriched.wan1_ip
                result['wan2_ip'] = enriched.wan2_ip
                result['source'] = 'enriched_circuits'
                result['warnings'].append('No Meraki device found, using enriched circuits data')
        
        # Strategy 3: Check circuits table (using correct column name)
        if not result['wan1_ip'] and not result['wan2_ip']:
            circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(site_name)
            ).all()
            
            # Use ip_address_start column which exists in circuits table
            for circuit in circuits:
                if hasattr(circuit, 'ip_address_start') and circuit.ip_address_start and not result['wan1_ip']:
                    result['wan1_ip'] = circuit.ip_address_start
                    result['source'] = 'circuits_table'
                    result['warnings'].append('Using circuit table IP address')
                    break
        
        # If still no IPs found, provide detailed error
        if not result['wan1_ip'] and not result['wan2_ip']:
            error_details = []
            if meraki_device:
                error_details.append(f"Meraki device found (serial: {meraki_device.device_serial}) but no IP addresses")
            else:
                error_details.append("No Meraki device found for this site")
                
            # Check if site exists in any table
            circuit_count = Circuit.query.filter(func.lower(Circuit.site_name) == func.lower(site_name)).count()
            if circuit_count > 0:
                error_details.append(f"Found {circuit_count} circuit record(s)")
            else:
                error_details.append("No circuit records found")
            
            return jsonify({
                'success': False, 
                'error': f'No IP data found for {site_name}. {"; ".join(error_details)}',
                'warnings': result['warnings']
            }), 404
        
        # Query ARIN for provider information
        def query_arin_rdap(ip):
            if not ip or ip == '0.0.0.0':
                return 'Unknown'
            try:
                arin_url = f"https://rdap.arin.net/registry/ip/{ip}"
                arin_response = requests.get(arin_url, timeout=10)
                if arin_response.status_code == 200:
                    arin_data = arin_response.json()
                    # Extract organization name
                    if 'entities' in arin_data:
                        for entity in arin_data['entities']:
                            if 'vcardArray' in entity:
                                for vcard in entity['vcardArray'][1]:
                                    if vcard[0] == 'fn':
                                        return vcard[3]
                return 'Unknown'
            except Exception as e:
                return f'ARIN Error: {str(e)}'
        
        # Query ARIN for any IPs we found
        result['wan1_arin_provider'] = query_arin_rdap(result['wan1_ip']) if result['wan1_ip'] else 'No IP'
        result['wan2_arin_provider'] = query_arin_rdap(result['wan2_ip']) if result['wan2_ip'] else 'No IP'
        
        # Update database tables with new data
        try:
            # Update meraki_inventory if we have the device
            if meraki_device and result['source'] in ['meraki_api', 'meraki_db']:
                meraki_device.wan1_ip = result['wan1_ip']
                meraki_device.wan2_ip = result['wan2_ip']
                meraki_device.wan1_arin_provider = result['wan1_arin_provider']
                meraki_device.wan2_arin_provider = result['wan2_arin_provider']
                meraki_device.last_updated = datetime.utcnow()
            
            # Update enriched_circuits if we found IP data
            if result['wan1_ip'] or result['wan2_ip']:
                enriched = EnrichedCircuit.query.filter(
                    func.lower(EnrichedCircuit.network_name) == func.lower(site_name)
                ).first()
                
                if enriched:
                    if result['wan1_ip']:
                        enriched.wan1_ip = result['wan1_ip']
                        enriched.wan1_arin_org = result['wan1_arin_provider']
                    if result['wan2_ip']:
                        enriched.wan2_ip = result['wan2_ip']
                        enriched.wan2_arin_org = result['wan2_arin_provider']
                    enriched.last_updated = datetime.utcnow()
            
            db.session.commit()
            
        except Exception as db_error:
            result['warnings'].append(f'Database update failed: {str(db_error)}')
            db.session.rollback()
        
        # Log successful refresh
        print(f"Enhanced ARIN refresh for {site_name}: "
              f"WAN1={result['wan1_ip']}({result['wan1_arin_provider']}), "
              f"WAN2={result['wan2_ip']}({result['wan2_arin_provider']}), "
              f"Source={result['source']}")
        
        return jsonify({
            'success': True,
            'message': f'ARIN data refreshed successfully. Source: {result["source"]}',
            'wan1_ip': result['wan1_ip'] or 'N/A',
            'wan1_arin_provider': result['wan1_arin_provider'],
            'wan2_ip': result['wan2_ip'] or 'N/A',
            'wan2_arin_provider': result['wan2_arin_provider'],
            'source': result['source'],
            'warnings': result['warnings']
        })
        
    except Exception as e:
        print(f"Error in enhanced ARIN refresh for {site_name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Test this function with CAL 24
if __name__ == "__main__":
    print("This is the enhanced ARIN refresh function to fix CAL 24 issues")