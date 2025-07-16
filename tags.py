"""
Tag Management Blueprint - View and update Meraki device tags
"""

from flask import Blueprint, render_template, request, jsonify
import psycopg2
import psycopg2.extras
import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from config import Config
import json

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

tags_bp = Blueprint('tags', __name__)

# Get API key
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'

def get_db_connection():
    """Get database connection"""
    import re
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
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

def make_api_request(url, method='GET', data=None, max_retries=3):
    """Make API request with retry logic"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    for attempt in range(max_retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 429:  # Rate limited
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response.json() if method == 'GET' else {'success': True}
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                return None if method == 'GET' else {'error': str(e)}
            time.sleep(2 ** attempt)

@tags_bp.route('/tags')
def tags_page():
    """Main tags management page"""
    return render_template('tags.html')

@tags_bp.route('/api/tags/inventory', methods=['GET'])
def get_tag_inventory():
    """Get all networks and their device tags from database"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Get all devices grouped by network
        cursor.execute("""
            SELECT 
                network_name,
                device_serial,
                device_name,
                device_model,
                device_tags,
                network_id,
                last_updated
            FROM meraki_inventory
            WHERE device_model LIKE 'MX%'
            ORDER BY network_name, device_serial
        """)
        
        devices = cursor.fetchall()
        
        # Group by network
        networks = {}
        for device in devices:
            network_name = device['network_name']
            if network_name not in networks:
                networks[network_name] = {
                    'network_name': network_name,
                    'network_id': device['network_id'],
                    'devices': []
                }
            
            # Parse tags - PostgreSQL array type
            tags = device['device_tags']
            if tags is None:
                tags = []
            elif isinstance(tags, list):
                tags = tags  # Already a list from PostgreSQL array
            elif isinstance(tags, str):
                # Fallback for string format
                try:
                    tags = json.loads(tags) if tags else []
                except:
                    tags = tags.split() if tags else []
            else:
                tags = []
            
            networks[network_name]['devices'].append({
                'device_serial': device['device_serial'],
                'device_name': device['device_name'],
                'model': device['device_model'],
                'tags': tags,
                'last_updated': device['last_updated'].isoformat() if device['last_updated'] else None
            })
        
        # Get unique tags
        all_tags = set()
        for network in networks.values():
            for device in network['devices']:
                all_tags.update(device['tags'])
        
        # Remove common non-location tags
        location_tags = [tag for tag in sorted(all_tags) 
                        if tag and tag not in ['hub', 'voice', 'lab', 'Hub', 'Voice', 'Lab']]
        
        return jsonify({
            'success': True,
            'networks': list(networks.values()),
            'available_tags': location_tags,
            'total_networks': len(networks),
            'total_devices': len(devices)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@tags_bp.route('/api/tags/device/<device_serial>', methods=['GET'])
def get_device_tags(device_serial):
    """Get current tags for a device from Meraki API"""
    url = f"{BASE_URL}/devices/{device_serial}"
    device_data = make_api_request(url)
    
    if device_data:
        tags = device_data.get('tags', [])
        if isinstance(tags, str):
            tags = tags.split() if tags else []
        
        return jsonify({
            'success': True,
            'device_serial': device_serial,
            'device_name': device_data.get('name'),
            'current_tags': tags,
            'model': device_data.get('model')
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to fetch device data'}), 500

@tags_bp.route('/api/tags/device/<device_serial>', methods=['PUT'])
def update_device_tags(device_serial):
    """Update tags for a single device"""
    data = request.get_json()
    tags = data.get('tags', [])
    
    # Convert list to space-separated string for Meraki API
    tags_string = ' '.join(tags) if tags else ''
    
    url = f"{BASE_URL}/devices/{device_serial}"
    result = make_api_request(url, method='PUT', data={'tags': tags_string})
    
    if result and result.get('success'):
        # Update database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE meraki_inventory 
                SET device_tags = %s, last_updated = NOW()
                WHERE device_serial = %s
            """, (tags, device_serial))  # Pass list directly for PostgreSQL array
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Tags updated for device {device_serial}',
                'tags': tags
            })
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'error': f'Database update failed: {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 500

@tags_bp.route('/api/tags/network/<network_name>', methods=['PUT'])
def update_network_tags(network_name):
    """Update tags for all devices in a network"""
    data = request.get_json()
    tags = data.get('tags', [])
    
    # Get all devices for this network
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT device_serial 
            FROM meraki_inventory 
            WHERE network_name = %s AND device_model LIKE 'MX%'
        """, (network_name,))
        
        devices = cursor.fetchall()
        
        if not devices:
            return jsonify({'success': False, 'error': 'No devices found for network'}), 404
        
        # Update each device
        success_count = 0
        error_count = 0
        errors = []
        
        tags_string = ' '.join(tags) if tags else ''
        
        for device_row in devices:
            device_serial = device_row[0]
            url = f"{BASE_URL}/devices/{device_serial}"
            result = make_api_request(url, method='PUT', data={'tags': tags_string})
            
            if result and result.get('success'):
                # Update database
                cursor.execute("""
                    UPDATE meraki_inventory 
                    SET device_tags = %s, last_updated = NOW()
                    WHERE device_serial = %s
                """, (tags, device_serial))  # Pass list directly for PostgreSQL array
                success_count += 1
            else:
                error_count += 1
                errors.append(f"{device_serial}: {result.get('error', 'Unknown error')}")
        
        conn.commit()
        
        return jsonify({
            'success': error_count == 0,
            'message': f'Updated {success_count} devices, {error_count} errors',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors,
            'tags': tags
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@tags_bp.route('/api/tags/bulk', methods=['PUT'])
def bulk_update_tags():
    """Update tags for multiple networks/devices"""
    data = request.get_json()
    updates = data.get('updates', [])  # List of {network_name, tags}
    
    success_count = 0
    error_count = 0
    results = []
    
    for update in updates:
        network_name = update.get('network_name')
        tags = update.get('tags', [])
        
        # Use the network update endpoint
        response = update_network_tags(network_name)
        result_data = response[0].get_json() if isinstance(response, tuple) else response.get_json()
        
        if result_data.get('success'):
            success_count += 1
            results.append({
                'network_name': network_name,
                'success': True,
                'message': result_data.get('message')
            })
        else:
            error_count += 1
            results.append({
                'network_name': network_name,
                'success': False,
                'error': result_data.get('error')
            })
    
    return jsonify({
        'success': error_count == 0,
        'total_success': success_count,
        'total_errors': error_count,
        'results': results
    })

@tags_bp.route('/api/tags/upload', methods=['POST'])
def upload_tags_csv():
    """Upload CSV file to bulk update tags"""
    try:
        import csv
        import io
        from werkzeug.utils import secure_filename
        
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'error': 'No CSV file provided'}), 400
        
        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be a CSV'}), 400
        
        # Read and parse CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.reader(stream)
        
        processed_count = 0
        success_count = 0
        error_count = 0
        results = []
        
        # Skip header and process rows
        header_skipped = False
        
        for row in csv_reader:
            # Skip empty rows and comments
            if not row or len(row) == 0 or (len(row) > 0 and row[0].strip().startswith('#')):
                continue
                
            # Skip header row
            if not header_skipped:
                header_skipped = True
                continue
            
            processed_count += 1
            
            # Parse CSV row - Handle both export format and simple format
            # Export format: Network Name, Device Serial, Device Name, Model, Current Tags, Action
            # Simple format: Network Name, Device Serial, Tags, Action
            
            if len(row) < 3:
                error_count += 1
                results.append({
                    'row': processed_count,
                    'error': 'Invalid row format - need at least Network Name, Device Serial, Tags'
                })
                continue
            
            network_name = row[0].strip()
            device_serial = row[1].strip() if len(row) > 1 and row[1].strip() else None
            
            # Determine format based on number of columns
            if len(row) >= 6:
                # Export format: Network Name, Device Serial, Device Name, Model, Current Tags, Action
                tags_str = row[4].strip() if len(row) > 4 else ''  # Column E (Current Tags)
                action = row[5].strip().upper() if len(row) > 5 else 'UPDATE'  # Column F (Action)
            else:
                # Simple format: Network Name, Device Serial, Tags, Action
                tags_str = row[2].strip() if len(row) > 2 else ''
                action = row[3].strip().upper() if len(row) > 3 else 'UPDATE'
            
            # Parse tags (comma-separated)
            tags = [tag.strip().strip('"') for tag in tags_str.split(',') if tag.strip()]
            
            try:
                if device_serial:
                    # Update specific device
                    update_result = update_device_tags_internal(device_serial, tags, action)
                else:
                    # Update all devices in network
                    update_result = update_network_tags_internal(network_name, tags, action)
                
                if update_result['success']:
                    success_count += 1
                    results.append({
                        'row': processed_count,
                        'network_name': network_name,
                        'device_serial': device_serial,
                        'tags': tags,
                        'success': True
                    })
                else:
                    error_count += 1
                    results.append({
                        'row': processed_count,
                        'network_name': network_name,
                        'device_serial': device_serial,
                        'error': update_result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                error_count += 1
                results.append({
                    'row': processed_count,
                    'network_name': network_name,
                    'device_serial': device_serial,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'total_processed': processed_count,
            'total_success': success_count,
            'total_errors': error_count,
            'message': f'CSV processing complete. {success_count} successful updates, {error_count} errors.',
            'results': results[:10]  # Return first 10 results for feedback
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'CSV upload failed: {str(e)}'
        }), 500

def update_device_tags_internal(device_serial, tags, action='UPDATE'):
    """Internal function to update device tags"""
    try:
        # Get current device info
        url = f"{BASE_URL}/devices/{device_serial}"
        response = make_api_request(url)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'Device not found: {device_serial}'}
        
        device_data = response.json()
        current_tags = device_data.get('tags', [])
        
        # Determine new tags based on action
        if action == 'ADD':
            # Add new tags to existing ones (avoid duplicates)
            new_tags = list(set(current_tags + tags))
        else:  # UPDATE
            # Replace all tags
            new_tags = tags
        
        # Update device
        update_url = f"{BASE_URL}/devices/{device_serial}"
        update_data = {'tags': new_tags}
        
        update_response = make_api_request(update_url, method='PUT', data=update_data)
        
        if update_response.status_code == 200:
            return {'success': True, 'tags': new_tags}
        else:
            return {'success': False, 'error': f'Failed to update device: {update_response.text}'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_network_tags_internal(network_name, tags, action='UPDATE'):
    """Internal function to update all devices in a network"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get all devices in the network
        cur.execute("""
            SELECT device_serial FROM meraki_inventory 
            WHERE network_name = %s AND device_serial IS NOT NULL
        """, (network_name,))
        
        devices = cur.fetchall()
        cur.close()
        conn.close()
        
        if not devices:
            return {'success': False, 'error': f'No devices found in network: {network_name}'}
        
        success_count = 0
        total_devices = len(devices)
        
        for device in devices:
            result = update_device_tags_internal(device['device_serial'], tags, action)
            if result['success']:
                success_count += 1
        
        return {
            'success': success_count > 0,
            'updated_devices': success_count,
            'total_devices': total_devices
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}