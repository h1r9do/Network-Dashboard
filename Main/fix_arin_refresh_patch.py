#!/usr/bin/env python3
"""
Patch to fix ARIN refresh functionality in dsrcircuits_blueprint.py
This adds enhanced ARIN lookup that handles sites without Meraki devices
"""

import re

def create_enhanced_refresh_arin_function():
    """Create the enhanced refresh ARIN function"""
    return '''@dsrcircuits_bp.route('/api/refresh-arin/<site_name>', methods=['POST'])
def refresh_arin_data(site_name):
    """Enhanced ARIN refresh that handles sites without Meraki devices"""
    try:
        import requests
        import os
        from datetime import datetime
        
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
        
        # Helper function to query ARIN
        def query_arin_rdap(ip):
            if not ip or ip == '0.0.0.0' or ip == 'N/A':
                return 'Unknown'
            try:
                # Validate IP format
                ip_pattern = re.compile(r'^(\\d{1,3}\\.){3}\\d{1,3}$')
                if not ip_pattern.match(ip):
                    return 'Unknown'
                    
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
                                        provider = vcard[3]
                                        # Clean up common suffixes
                                        provider = provider.replace(', Inc.', '')
                                        provider = provider.replace(' Inc.', '')
                                        provider = provider.replace(' LLC', '')
                                        return provider
                    # Fallback to name field
                    if 'name' in arin_data:
                        return arin_data['name']
                return 'Unknown'
            except:
                return 'Unknown'
        
        # Strategy 1: Try Meraki first
        meraki_device = MerakiInventory.query.filter(
            func.lower(MerakiInventory.network_name) == func.lower(site_name)
        ).first()
        
        if meraki_device and meraki_device.device_serial:
            # Get Meraki API key
            meraki_api_key = os.getenv('MERAKI_API_KEY')
            if not meraki_api_key:
                from dotenv import load_dotenv
                load_dotenv('/usr/local/bin/meraki.env')
                meraki_api_key = os.getenv('MERAKI_API_KEY')
            
            if meraki_api_key:
                # Try to get fresh data from Meraki API
                try:
                    # Get organization
                    org_name = "DTC-Store-Inventory-All"
                    headers = {
                        'X-Cisco-Meraki-API-Key': meraki_api_key,
                        'Content-Type': 'application/json'
                    }
                    
                    orgs_response = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers, timeout=30)
                    org_id = None
                    for org in orgs_response.json():
                        if org.get('name') == org_name:
                            org_id = org['id']
                            break
                    
                    if org_id:
                        # Get uplink statuses
                        uplink_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/appliance/uplink/statuses"
                        response = requests.get(uplink_url, headers=headers, timeout=30)
                        all_uplinks = response.json()
                        
                        # Find our device
                        for device_status in all_uplinks:
                            if device_status.get('serial') == meraki_device.device_serial:
                                uplinks = device_status.get('uplinks', [])
                                for uplink in uplinks:
                                    if uplink.get('interface') == 'wan1':
                                        result['wan1_ip'] = uplink.get('publicIp') or uplink.get('ip')
                                    elif uplink.get('interface') == 'wan2':
                                        result['wan2_ip'] = uplink.get('publicIp') or uplink.get('ip')
                                result['source'] = 'meraki_api'
                                break
                except:
                    pass
            
            # Fallback to database data
            if not result['wan1_ip'] and not result['wan2_ip']:
                result['wan1_ip'] = meraki_device.wan1_ip
                result['wan2_ip'] = meraki_device.wan2_ip
                result['source'] = 'meraki_db'
                result['warnings'].append('Using cached Meraki data')
        
        # Strategy 2: Check enriched_circuits table
        if not result['wan1_ip'] and not result['wan2_ip']:
            enriched = EnrichedCircuits.query.filter(
                func.lower(EnrichedCircuits.site_name) == func.lower(site_name)
            ).first()
            
            if enriched:
                result['wan1_ip'] = enriched.wan1_public_ip or enriched.wan1_ip
                result['wan2_ip'] = enriched.wan2_public_ip or enriched.wan2_ip
                result['source'] = 'enriched_circuits'
                result['warnings'].append('No Meraki device found, using enriched circuits data')
        
        # Strategy 3: Check circuits table for Non-DSR circuits
        if not result['wan1_ip'] and not result['wan2_ip']:
            circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(site_name)
            ).all()
            
            for circuit in circuits:
                if circuit.wan1_ip and not result['wan1_ip']:
                    result['wan1_ip'] = circuit.wan1_ip
                if circuit.wan2_ip and not result['wan2_ip']:
                    result['wan2_ip'] = circuit.wan2_ip
            
            if result['wan1_ip'] or result['wan2_ip']:
                result['source'] = 'circuits_table'
                result['warnings'].append('Using circuit table data')
        
        # If still no IPs found
        if not result['wan1_ip'] and not result['wan2_ip']:
            result['warnings'].append('No IP data found in any source')
            result['source'] = 'none'
            return jsonify({
                'success': False,
                'error': f'No device or circuit data found for {site_name}. This site may not have a Meraki device or may be a Non-DSR circuit without IP data.',
                'warnings': result['warnings']
            }), 404
        
        # Query ARIN for any IPs we found
        if result['wan1_ip']:
            result['wan1_arin_provider'] = query_arin_rdap(result['wan1_ip'])
        else:
            result['wan1_arin_provider'] = 'No IP'
            
        if result['wan2_ip']:
            result['wan2_arin_provider'] = query_arin_rdap(result['wan2_ip'])
        else:
            result['wan2_arin_provider'] = 'No IP'
        
        # Update appropriate database tables
        if result['source'] in ['meraki_api', 'meraki_db'] and meraki_device:
            meraki_device.wan1_ip = result['wan1_ip']
            meraki_device.wan2_ip = result['wan2_ip']
            meraki_device.wan1_arin_provider = result['wan1_arin_provider']
            meraki_device.wan2_arin_provider = result['wan2_arin_provider']
            meraki_device.last_updated = datetime.utcnow()
        
        # Always update enriched_circuits if we have data
        enriched = EnrichedCircuits.query.filter(
            func.lower(EnrichedCircuits.site_name) == func.lower(site_name)
        ).first()
        
        if enriched and (result['wan1_ip'] or result['wan2_ip']):
            if result['wan1_ip']:
                enriched.wan1_ip = result['wan1_ip']
                enriched.wan1_arin_provider = result['wan1_arin_provider']
            if result['wan2_ip']:
                enriched.wan2_ip = result['wan2_ip']
                enriched.wan2_arin_provider = result['wan2_arin_provider']
            enriched.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Enhanced ARIN refresh for {site_name}: "
                   f"WAN1={result['wan1_ip']}({result['wan1_arin_provider']}), "
                   f"WAN2={result['wan2_ip']}({result['wan2_arin_provider']}), "
                   f"Source={result['source']}")
        
        return jsonify({
            'success': True,
            'message': f'ARIN data refreshed from {result["source"]}',
            'wan1_ip': result['wan1_ip'] or 'N/A',
            'wan1_arin_provider': result['wan1_arin_provider'],
            'wan2_ip': result['wan2_ip'] or 'N/A',
            'wan2_arin_provider': result['wan2_arin_provider'],
            'source': result['source'],
            'warnings': result['warnings']
        })
        
    except Exception as e:
        logger.error(f"Error refreshing ARIN data for {site_name}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500'''

def apply_patch():
    """Apply the patch to dsrcircuits_blueprint.py"""
    
    # Read the current file
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
        content = f.read()
    
    # Find the existing refresh_arin_data function
    pattern = r'@dsrcircuits_bp\.route\(\'/api/refresh-arin/<site_name>\', methods=\[\'POST\'\]\)\ndef refresh_arin_data\(site_name\):.*?(?=@dsrcircuits_bp\.route|$)'
    
    # Replace with enhanced version
    enhanced_function = create_enhanced_refresh_arin_function()
    
    # Apply the replacement
    new_content = re.sub(pattern, enhanced_function + '\n\n', content, flags=re.DOTALL)
    
    # Backup the original
    import shutil
    from datetime import datetime
    backup_name = f'/usr/local/bin/Main/dsrcircuits_blueprint.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy('/usr/local/bin/Main/dsrcircuits_blueprint.py', backup_name)
    print(f"Created backup: {backup_name}")
    
    # Write the updated content
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(new_content)
    
    print("Successfully patched dsrcircuits_blueprint.py with enhanced ARIN refresh functionality")
    
    # Also add the necessary import if not present
    if 'import re' not in content:
        # Add import at the top
        lines = new_content.split('\n')
        import_index = None
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i
                break
        
        if import_index:
            lines.insert(import_index + 1, 'import re')
            new_content = '\n'.join(lines)
            
            with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
                f.write(new_content)
            print("Added 're' import to dsrcircuits_blueprint.py")

if __name__ == "__main__":
    apply_patch()