#!/usr/bin/env python3
"""
VLAN Migration API endpoints for DSR Circuits web interface
Handles network discovery, migration execution, and status tracking
"""

import os
import json
import time
import threading
import subprocess
from datetime import datetime
from flask import Blueprint, jsonify, request, session
import requests
from dotenv import load_dotenv
import sys
sys.path.append('/usr/local/bin/Main')
try:
    from models import db
    # For now, we'll skip database tracking until tables are created
    db_available = True
except ImportError:
    db_available = False

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
ORG_ID = '436883'  # DTC-Store-Inventory-All (production stores)

vlan_migration_bp = Blueprint('vlan_migration', __name__)

# Global migration jobs tracker
migration_jobs = {}

def get_meraki_networks():
    """Get all networks from database with detailed VLAN information"""
    try:
        # Use direct database connection instead of Flask SQLAlchemy
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="dsrcircuits",
            user="dsruser",
            password="dsrpass123"
        )
        cursor = conn.cursor()
        
        # Get networks with VLANs from database
        query = """
        WITH network_summary AS (
            SELECT 
                mi.network_id,
                mi.network_name,
                mi.device_tags,
                COUNT(DISTINCT nv.vlan_id) as vlan_count,
                -- Aggregate legacy VLANs
                STRING_AGG(DISTINCT 
                    CASE WHEN nv.vlan_id IN (1, 101, 201, 801) 
                    THEN nv.vlan_id::text 
                    END, ','
                ) as legacy_vlans_str,
                -- Get primary subnet for /16 calculation and /24 display
                MAX(CASE 
                    WHEN nv.vlan_id = 1 THEN nv.subnet 
                    WHEN nv.vlan_id = 100 THEN nv.subnet 
                    WHEN nv.vlan_id = 900 THEN nv.subnet 
                END) as primary_subnet,
                -- Get firewall rule count
                (SELECT COUNT(*) FROM firewall_rules fr WHERE fr.network_id = mi.network_id) as fw_rule_count
            FROM meraki_inventory mi
            LEFT JOIN network_vlans nv ON mi.network_id = nv.network_id
            WHERE mi.device_model LIKE 'MX%'
            GROUP BY mi.network_id, mi.network_name, mi.device_tags
            HAVING COUNT(DISTINCT nv.vlan_id) > 0
        )
        SELECT 
            ns.*,
            -- Get all VLANs with names
            ARRAY_AGG(
                json_build_object(
                    'id', nv.vlan_id::text,
                    'name', COALESCE(nv.name, 'VLAN_' || nv.vlan_id),
                    'subnet', nv.subnet
                ) ORDER BY nv.vlan_id
            ) as all_vlans
        FROM network_summary ns
        JOIN network_vlans nv ON ns.network_id = nv.network_id
        GROUP BY ns.network_id, ns.network_name, ns.device_tags, 
                 ns.vlan_count, ns.legacy_vlans_str, ns.primary_subnet, ns.fw_rule_count
        ORDER BY ns.network_name
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        migration_networks = []
        for row in rows:
            network_id, network_name, device_tags, vlan_count, legacy_vlans_str, primary_subnet, fw_rule_count, all_vlans = row
            
            # Process legacy VLANs
            legacy_vlans = []
            if legacy_vlans_str:
                legacy_vlans = [v.strip() for v in legacy_vlans_str.split(',') if v and v.strip()]
            
            # Calculate /16 and /24 subnets
            subnet_16 = None
            subnet_24 = None
            if primary_subnet:
                try:
                    subnet_parts = primary_subnet.split('.')
                    if len(subnet_parts) >= 2:
                        subnet_16 = f"{subnet_parts[0]}.{subnet_parts[1]}.0.0/16"
                    if len(subnet_parts) >= 3:
                        # Extract the /24 portion
                        subnet_24 = f"{subnet_parts[0]}.{subnet_parts[1]}.{subnet_parts[2]}.0/24"
                except:
                    pass
            
            # Parse tags (device_tags is already an array in DB)
            tags = []
            if device_tags:
                if isinstance(device_tags, list):
                    tags = device_tags
                elif isinstance(device_tags, str):
                    tags = [tag.strip() for tag in device_tags.split() if tag.strip()]
            
            # Determine migration status
            needs_migration = len(legacy_vlans) > 0
            
            # Create network info
            network_info = {
                'id': network_id,
                'name': network_name,
                'tags': tags,
                'subnet': primary_subnet,
                'subnet_16': subnet_16,
                'subnet_24': subnet_24,
                'legacy_vlans': legacy_vlans,
                'all_vlans': all_vlans,
                'vlan_count': vlan_count,
                'fw_rule_count': fw_rule_count or 0,
                'needs_migration': needs_migration,
                'timezone': 'US/Arizona',
                'last_migration': None,
                'status': 'legacy' if needs_migration else 'migrated'
            }
            
            migration_networks.append(network_info)
        
        cursor.close()
        conn.close()
        
        print(f"Successfully processed {len(migration_networks)} networks from database")
        return migration_networks
        
    except Exception as e:
        print(f"Error fetching networks from database: {e}")
        import traceback
        traceback.print_exc()
        return []

def run_migration_worker(job_id, network_ids):
    """Worker thread to run migration for multiple networks"""
    job = migration_jobs[job_id]
    job['status'] = 'running'
    job['start_time'] = datetime.now()
    
    try:
        for idx, network_id in enumerate(network_ids):
            # Update current network
            job['current_network'] = network_id
            job['current_index'] = idx
            
            # Get network name
            headers = {
                'X-Cisco-Meraki-API-Key': API_KEY,
                'Content-Type': 'application/json'
            }
            network_response = requests.get(
                f"https://api.meraki.com/api/v1/networks/{network_id}",
                headers=headers
            )
            network_name = "Unknown"
            if network_response.status_code == 200:
                network_name = network_response.json().get('name', 'Unknown')
            
            # Log migration start
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'phase': 'start',
                'network': network_name,
                'message': f"Starting migration for {network_name}"
            }
            job['console_logs'].append(log_entry)
            
            # Run the migration script
            cmd = [
                'python3',
                '/usr/local/bin/Main/vlan_migration_complete.py',
                '--network-id', network_id
            ]
            
            env = os.environ.copy()
            env['SKIP_CONFIRMATION'] = '1'  # Skip confirmation for automated runs
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            
            # Stream output
            for line in process.stdout:
                if line.strip():
                    # Parse migration script output
                    phase = 'execution'
                    if 'backup' in line.lower():
                        phase = 'backup'
                    elif 'clearing' in line.lower():
                        phase = 'clear'
                    elif 'migrating' in line.lower():
                        phase = 'migrate'
                    elif 'restoring' in line.lower():
                        phase = 'restore'
                    elif 'complete' in line.lower() or 'success' in line.lower():
                        phase = 'complete'
                    
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'phase': phase,
                        'network': network_name,
                        'message': line.strip()
                    }
                    job['console_logs'].append(log_entry)
            
            process.wait()
            
            # Check result
            if process.returncode == 0:
                job['networks_completed'].append({
                    'id': network_id,
                    'name': network_name,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Run validation
                validation_cmd = [
                    'python3',
                    '/usr/local/bin/Main/detailed_rule_comparison.py'
                ]
                
                val_process = subprocess.run(
                    validation_cmd,
                    capture_output=True,
                    text=True
                )
                
                if 'Match percentage: 100.0%' in val_process.stdout:
                    job['validation_results'].append({
                        'network': network_name,
                        'status': 'passed',
                        'details': 'Firewall rules match NEO 07 template 100%'
                    })
                else:
                    job['validation_results'].append({
                        'network': network_name,
                        'status': 'warning',
                        'details': val_process.stdout
                    })
            else:
                job['networks_completed'].append({
                    'id': network_id,
                    'name': network_name,
                    'status': 'failed',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Update progress
            job['progress'] = int(((idx + 1) / len(network_ids)) * 100)
            
    except Exception as e:
        job['status'] = 'failed'
        job['error'] = str(e)
        job['console_logs'].append({
            'timestamp': datetime.now().isoformat(),
            'phase': 'error',
            'network': 'System',
            'message': f"Migration failed: {str(e)}"
        })
    
    # Mark job complete
    job['status'] = 'completed'
    job['end_time'] = datetime.now()
    job['progress'] = 100
    
    # Save to database (skip for now until tables are created)
    if db_available:
        try:
            # We'll implement this once tables are created
            pass
        except Exception as e:
            print(f"Error saving migration history: {e}")

@vlan_migration_bp.route('/api/networks-for-migration', methods=['GET'])
def get_networks_for_migration():
    """Get all networks with migration eligibility information"""
    try:
        networks = get_meraki_networks()
        
        # Apply filters if provided
        subnet_filter = request.args.get('subnet_16')  # Filter by /16 subnet
        migration_filter = request.args.get('needs_migration')
        
        # Filter by /16 subnet if specified
        if subnet_filter and subnet_filter != 'all':
            # Handle comma-separated subnet list
            if ',' in subnet_filter:
                subnet_list = [s.strip() for s in subnet_filter.split(',')]
                networks = [n for n in networks if n.get('subnet_16') in subnet_list]
            else:
                networks = [n for n in networks if n.get('subnet_16') == subnet_filter]
        
        # Filter by migration status if specified
        if migration_filter == 'true':
            networks = [n for n in networks if n.get('needs_migration')]
        elif migration_filter == 'false':
            networks = [n for n in networks if not n.get('needs_migration')]
        
        # Get unique /16 subnets for filter dropdown
        all_networks = get_meraki_networks() if subnet_filter else networks
        subnet_16_list = list(set([n['subnet_16'] for n in all_networks if n.get('subnet_16')]))
        subnet_16_list.sort()
        
        # Get migration statistics
        migration_stats = {
            'total': len(networks),
            'needs_migration': len([n for n in networks if n.get('needs_migration')]),
            'already_migrated': len([n for n in networks if not n.get('needs_migration')])
        }
        
        return jsonify({
            'networks': networks,
            'subnet_16_list': subnet_16_list,
            'migration_stats': migration_stats,
            'filters_applied': {
                'subnet_16': subnet_filter,
                'needs_migration': migration_filter
            }
        })
        
    except Exception as e:
        print(f"Error in get_networks_for_migration: {e}")
        return jsonify({'error': str(e)}), 500

@vlan_migration_bp.route('/api/vlan-migration/start', methods=['POST'])
def start_migration():
    """Start migration process for selected networks"""
    try:
        data = request.json
        network_ids = data.get('network_ids', [])
        
        if not network_ids:
            return jsonify({'error': 'No networks selected'}), 400
        
        # TEST MODE: Control via environment variable
        TEST_MODE = os.getenv('VLAN_MIGRATION_TEST_MODE', 'true').lower() == 'true'
        if TEST_MODE:
            allowed_network = 'L_3790904986339115852'  # TST 01
            if len(network_ids) > 1 or network_ids[0] != allowed_network:
                return jsonify({
                    'error': 'Test Mode: Only TST 01 can be migrated. Set VLAN_MIGRATION_TEST_MODE=false for production',
                    'allowed_network': 'TST 01'
                }), 403
        
        # Create job ID
        job_id = f"migration_{int(time.time() * 1000)}"
        
        # Initialize job
        migration_jobs[job_id] = {
            'id': job_id,
            'status': 'initializing',
            'progress': 0,
            'networks_total': len(network_ids),
            'networks_completed': [],
            'current_network': None,
            'current_index': 0,
            'console_logs': [],
            'validation_results': [],
            'start_time': None,
            'end_time': None,
            'user': session.get('user', 'anonymous')
        }
        
        # Start worker thread
        thread = threading.Thread(
            target=run_migration_worker,
            args=(job_id, network_ids)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'networks_count': len(network_ids)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vlan_migration_bp.route('/api/vlan-migration/status/<job_id>', methods=['GET'])
def get_migration_status(job_id):
    """Get status of migration job"""
    if job_id not in migration_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = migration_jobs[job_id]
    
    # Get latest console logs
    since = request.args.get('since', 0, type=int)
    new_logs = job['console_logs'][since:]
    
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'networks_total': job['networks_total'],
        'networks_completed': len(job['networks_completed']),
        'current_network': job.get('current_network'),
        'console_logs': new_logs,
        'log_index': len(job['console_logs']),
        'validation_results': job.get('validation_results', []),
        'error': job.get('error')
    })

@vlan_migration_bp.route('/api/vlan-migration/validate', methods=['POST'])
def validate_migration():
    """Validate migration for specific networks"""
    try:
        data = request.json
        network_ids = data.get('network_ids', [])
        
        results = []
        for network_id in network_ids:
            # Run validation script
            cmd = [
                'python3',
                '/usr/local/bin/Main/detailed_rule_comparison.py',
                '--network-id', network_id
            ]
            
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if 'Match percentage: 100.0%' in process.stdout:
                results.append({
                    'network_id': network_id,
                    'status': 'passed',
                    'message': 'Migration validated successfully'
                })
            else:
                results.append({
                    'network_id': network_id,
                    'status': 'failed',
                    'message': process.stdout
                })
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vlan_migration_bp.route('/api/vlan-migration/history', methods=['GET'])
def get_migration_history():
    """Get migration history from database"""
    try:
        # Return empty history for now until database tables are created
        return jsonify({
            'history': []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vlan_migration_bp.route('/api/vlan-migration/rollback', methods=['POST'])
def rollback_migration():
    """Rollback a network to pre-migration state"""
    try:
        data = request.json
        network_id = data.get('network_id')
        backup_file = data.get('backup_file')
        
        if not network_id or not backup_file:
            return jsonify({'error': 'Missing network_id or backup_file'}), 400
        
        # Run rollback script
        cmd = [
            'python3',
            '/usr/local/bin/Main/restore_from_backup.py',
            '--network-id', network_id,
            '--backup-file', backup_file
        ]
        
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'Rollback completed successfully'
            })
        else:
            return jsonify({
                'status': 'failed',
                'error': process.stderr or process.stdout
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500