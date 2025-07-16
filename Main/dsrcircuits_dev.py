"""
DEV VERSION - Complete development environment for DSR Circuits
Uses all _dev tables for safe testing and development
"""
from flask import Blueprint, render_template, jsonify, request, current_app
from sqlalchemy import text
from models import db
from datetime import datetime
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
dsrcircuits_dev_bp = Blueprint('dsrcircuits_dev', __name__)

@dsrcircuits_dev_bp.route('/dsrcircuits-dev')
def dsrcircuits_dev():
    """
    DEV VERSION - Main circuits data table page
    Uses all _dev tables for testing
    """
    import time
    start_time = time.time()
    
    try:
        # Load from dev view
        query = db.session.execute(text("""
            SELECT 
                network_name,
                wan1_provider,
                wan1_speed,
                wan1_cost,
                wan1_role,
                wan2_provider,
                wan2_speed,
                wan2_cost,
                wan2_role,
                total_cost,
                wan1_confirmed,
                wan2_confirmed,
                pushed_to_meraki,
                pushed_date,
                last_updated
            FROM v_enriched_circuits_complete_dev
            ORDER BY network_name
        """))
        
        circuits_data = []
        for row in query:
            circuit = {
                'site_name': row[0],
                'wan1_provider': row[1],
                'wan1_speed': row[2],
                'wan1_cost': float(row[3]) if row[3] else 0,
                'wan1_role': row[4],
                'wan2_provider': row[5],
                'wan2_speed': row[6],
                'wan2_cost': float(row[7]) if row[7] else 0,
                'wan2_role': row[8],
                'total_cost': float(row[9]) if row[9] else 0,
                'wan1_confirmed': row[10],
                'wan2_confirmed': row[11],
                'pushed_to_meraki': row[12],
                'pushed_date': row[13].strftime('%Y-%m-%d %H:%M') if row[13] else None,
                'last_updated': row[14].strftime('%Y-%m-%d %H:%M') if row[14] else None
            }
            
            # Set confirmation status
            if circuit['wan1_confirmed'] and circuit['wan2_confirmed']:
                circuit['confirmation_status'] = 'Confirmed'
            elif circuit['wan1_confirmed'] or circuit['wan2_confirmed']:
                circuit['confirmation_status'] = 'Partial'
            else:
                circuit['confirmation_status'] = 'Not Confirmed'
            
            circuits_data.append(circuit)
        
        # Convert to grouped_data format
        grouped_data = []
        for circuit in circuits_data:
            grouped_data.append({
                'network_name': circuit['site_name'],
                'wan1': {
                    'provider': circuit['wan1_provider'],
                    'speed': circuit['wan1_speed'],
                    'monthly_cost': circuit['wan1_cost'],
                    'circuit_role': circuit['wan1_role']
                },
                'wan2': {
                    'provider': circuit['wan2_provider'],
                    'speed': circuit['wan2_speed'],
                    'monthly_cost': circuit['wan2_cost'],
                    'circuit_role': circuit['wan2_role']
                }
            })
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"DSR Circuits DEV page loaded in {processing_time:.2f}ms with {len(circuits_data)} circuits")
        
        return render_template('dsrcircuits.html',
            grouped_data=grouped_data,
            meraki_functions_available=True,
            processing_time=f"{processing_time:.2f}ms",
            data_source="Dev Database"
        )
        
    except Exception as e:
        logger.error(f"Error in dsrcircuits dev: {str(e)}")
        processing_time = (time.time() - start_time) * 1000
        
        return render_template('dsrcircuits.html',
            grouped_data=[],
            meraki_functions_available=True,
            processing_time=f"{processing_time:.2f}ms",
            data_source="Error",
            error=str(e)
        )

@dsrcircuits_dev_bp.route('/confirm-dev/<site_name>', methods=['POST'])
def get_confirmation_popup_dev(site_name):
    """Get confirmation popup data for a site - DEV VERSION"""
    try:
        # Get enriched data from dev table
        enriched = db.session.execute(text("""
            SELECT 
                network_name,
                wan1_provider,
                wan1_speed,
                wan1_confirmed,
                wan2_provider,
                wan2_speed,
                wan2_confirmed,
                device_tags
            FROM enriched_circuits_dev
            WHERE network_name = :site_name
        """), {'site_name': site_name}).fetchone()
        
        # Get Meraki data from dev table
        meraki = db.session.execute(text("""
            SELECT 
                network_name,
                wan1_ip,
                wan2_ip,
                device_notes,
                device_serial
            FROM meraki_inventory_dev
            WHERE network_name = :site_name
        """), {'site_name': site_name}).fetchone()
        
        # Get DSR circuit data from dev table
        dsr_circuits = db.session.execute(text("""
            SELECT 
                provider_name,
                details_service_speed,
                circuit_purpose,
                ip_address_start,
                billing_monthly_cost
            FROM circuits_dev
            WHERE site_name = :site_name
            AND status = 'Enabled'
            ORDER BY circuit_purpose
        """), {'site_name': site_name}).fetchall()
        
        # Parse device notes properly
        def clean_provider_name(raw_notes, wan_num):
            """Extract clean provider name from raw notes"""
            if not raw_notes:
                return None
            
            notes = raw_notes.replace('\\n', '\n')
            lines = notes.split('\n')
            
            wan_section = f"WAN {wan_num}"
            try:
                wan_index = lines.index(wan_section)
                if wan_index + 1 < len(lines):
                    provider = lines[wan_index + 1].strip()
                    provider = provider.replace('\\', '').replace('\n', '').strip()
                    return provider if provider and provider != '' else None
            except (ValueError, IndexError):
                pass
            
            return None
        
        raw_notes = meraki[3] if meraki else None
        
        # Format response
        response_data = {
            'site_name': site_name,
            'enriched_data': {
                'wan1_provider': enriched[1] if enriched else None,
                'wan1_speed': enriched[2] if enriched else None,
                'wan1_confirmed': enriched[3] if enriched else False,
                'wan2_provider': enriched[4] if enriched else None,
                'wan2_speed': enriched[5] if enriched else None,
                'wan2_confirmed': enriched[6] if enriched else False,
                'device_tags': enriched[7] if enriched else []
            } if enriched else None,
            'meraki_data': {
                'wan1_ip': meraki[1] if meraki else None,
                'wan2_ip': meraki[2] if meraki else None,
                'device_notes': meraki[3] if meraki else None,
                'device_serial': meraki[4] if meraki else None
            } if meraki else None,
            'wan1_provider_notes': clean_provider_name(raw_notes, 1),
            'wan2_provider_notes': clean_provider_name(raw_notes, 2),
            'wan1_provider_label': clean_provider_name(raw_notes, 1),
            'wan2_provider_label': clean_provider_name(raw_notes, 2),
            'raw_notes': raw_notes,
            'dsr_circuits': [{
                'provider': row[0],
                'speed': row[1],
                'purpose': row[2],
                'ip_address': row[3],
                'cost': float(row[4]) if row[4] else 0
            } for row in dsr_circuits]
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting dev confirmation data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dsrcircuits_dev_bp.route('/dev/run-enrichment', methods=['POST'])
def run_dev_enrichment():
    """Run enrichment process on dev tables"""
    try:
        import subprocess
        result = subprocess.run(['python3', '/tmp/nightly_enriched_dev.py'], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dsrcircuits_dev_bp.route('/dev/load-dsr', methods=['POST'])
def load_dev_dsr():
    """Load DSR data into dev tables"""
    try:
        data = request.get_json()
        csv_path = data.get('csv_path')
        
        import subprocess
        cmd = ['python3', '/tmp/nightly_dsr_pull_dev.py']
        if csv_path:
            cmd.append(csv_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500