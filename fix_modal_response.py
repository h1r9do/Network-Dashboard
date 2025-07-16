#!/usr/bin/env python3
"""
Fix the modal response format to match frontend expectations
"""

import re

def parse_notes_to_fields(raw_notes):
    """Parse raw notes into WAN1/WAN2 provider and speed fields"""
    if not raw_notes:
        return {
            'wan1_provider': '',
            'wan1_speed': '',
            'wan2_provider': '',
            'wan2_speed': ''
        }
    
    # Split by actual newlines
    lines = raw_notes.split('\n')
    
    wan1_provider = ''
    wan1_speed = ''
    wan2_provider = ''
    wan2_speed = ''
    current_wan = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.upper() == 'WAN 1':
            current_wan = 'wan1'
        elif line.upper() == 'WAN 2':
            current_wan = 'wan2'
        else:
            # Check if it's a speed pattern
            speed_pattern = re.compile(r'^\d+(?:\.\d+)?M?\s*x\s*\d+(?:\.\d+)?M?$|^Cell$|^Satellite$', re.IGNORECASE)
            if speed_pattern.match(line):
                # It's a speed
                if current_wan == 'wan1':
                    wan1_speed = line
                elif current_wan == 'wan2':
                    wan2_speed = line
            else:
                # It's a provider
                if current_wan == 'wan1' and not wan1_provider:
                    wan1_provider = line
                elif current_wan == 'wan2' and not wan2_provider:
                    wan2_provider = line
    
    return {
        'wan1_provider': wan1_provider,
        'wan1_speed': wan1_speed,
        'wan2_provider': wan2_provider,
        'wan2_speed': wan2_speed
    }

def format_modal_response(confirm_data):
    """Transform confirm_site response to match frontend expectations"""
    
    # Parse the raw notes
    raw_notes = confirm_data.get('meraki', {}).get('raw_notes', '')
    parsed_notes = parse_notes_to_fields(raw_notes)
    
    # Get DSR data
    tracking_data = confirm_data.get('tracking', [])
    wan1_dsr = next((t for t in tracking_data if t.get('Circuit Purpose') == 'Primary'), {})
    wan2_dsr = next((t for t in tracking_data if t.get('Circuit Purpose') == 'Secondary'), {})
    
    # Build formatted response
    formatted = {
        'site_name': confirm_data.get('site_name', ''),
        'raw_notes': raw_notes,
        'success': True,
        
        # WAN1 data
        'wan1': confirm_data.get('enriched', {}).get('wan1', {}),
        'wan1_ip': confirm_data.get('meraki', {}).get('wan1', {}).get('ip', ''),
        'wan1_arin_provider': confirm_data.get('meraki', {}).get('wan1', {}).get('provider', ''),
        'wan1_provider_notes': parsed_notes['wan1_provider'],
        'wan1_speed_notes': parsed_notes['wan1_speed'],
        'wan1_provider_dsr': wan1_dsr.get('provider_name', ''),
        'wan1_speed_dsr': wan1_dsr.get('speed', ''),
        'wan1_provider_label': confirm_data.get('meraki', {}).get('wan1', {}).get('provider_label', ''),
        
        # WAN2 data
        'wan2': confirm_data.get('enriched', {}).get('wan2', {}),
        'wan2_ip': confirm_data.get('meraki', {}).get('wan2', {}).get('ip', ''),
        'wan2_arin_provider': confirm_data.get('meraki', {}).get('wan2', {}).get('provider', ''),
        'wan2_provider_notes': parsed_notes['wan2_provider'],
        'wan2_speed_notes': parsed_notes['wan2_speed'],
        'wan2_provider_dsr': wan2_dsr.get('provider_name', ''),
        'wan2_speed_dsr': wan2_dsr.get('speed', ''),
        'wan2_provider_label': confirm_data.get('meraki', {}).get('wan2', {}).get('provider_label', ''),
        
        # Additional data
        'csv_data': [
            {
                'Site Name': t.get('site_name', confirm_data.get('site_name', '')),
                'DSR Circuit Purpose': t.get('Circuit Purpose', ''),
                'Provider Name': t.get('provider_name', ''),
                'Speed': t.get('speed', ''),
                'Price': f"${t.get('billing_monthly_cost', 0):.2f}" if isinstance(t.get('billing_monthly_cost'), (int, float)) else '$0.00',
                'Status': 'Enabled',
                'Date': ''
            } for t in tracking_data
        ],
        
        # Check if already pushed
        'already_pushed': confirm_data.get('enriched', {}).get('wan1', {}).get('confirmed', False) or 
                         confirm_data.get('enriched', {}).get('wan2', {}).get('confirmed', False),
    }
    
    # Add comparison logic
    wan1_arin = formatted['wan1_arin_provider'].lower() if formatted['wan1_arin_provider'] else ''
    wan1_notes = formatted['wan1_provider_notes'].lower() if formatted['wan1_provider_notes'] else ''
    formatted['wan1_comparison'] = 'Match' if wan1_arin and wan1_notes and wan1_arin in wan1_notes else 'No match'
    
    wan2_arin = formatted['wan2_arin_provider'].lower() if formatted['wan2_arin_provider'] else ''
    wan2_notes = formatted['wan2_provider_notes'].lower() if formatted['wan2_provider_notes'] else ''
    formatted['wan2_comparison'] = 'Match' if wan2_arin and wan2_notes and wan2_arin in wan2_notes else 'No match'
    
    return formatted

if __name__ == "__main__":
    # Test with example data
    test_data = {
        'site_name': 'AZP 14',
        'meraki': {
            'raw_notes': 'WAN 1\nCox Communications\n300.0M x 30.0M\nWAN 2\nVZW Cell\nCell',
            'wan1': {'ip': '70.175.28.153', 'provider': 'Cox Communications'},
            'wan2': {'ip': '166.253.101.116', 'provider': 'Verizon Business'}
        },
        'enriched': {
            'wan1': {'provider': 'Cox Communications', 'speed': '300.0M x 30.0M'},
            'wan2': {'provider': 'VZW Cell', 'speed': 'Cell'}
        },
        'tracking': [
            {'Circuit Purpose': 'Primary', 'provider_name': 'Cox Business/BOI', 'speed': '300.0M x 30.0M'}
        ]
    }
    
    result = format_modal_response(test_data)
    import json
    print(json.dumps(result, indent=2))