#!/usr/bin/env python3
"""
Test-focused VLAN Migration API for TST 01 only
Includes reset to AZP 30 functionality
"""

import os
import json
import time
import threading
import subprocess
from datetime import datetime
from flask import Blueprint, jsonify, request
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
ORG_ID = '3790904986339115010'

# Test network configuration
TEST_NETWORK = {
    'id': 'L_3790904986339115852',
    'name': 'TST 01',
    'source_network_id': 'L_3790904986339114669',  # AZP 30
    'source_network_name': 'Legacy Config'
}

vlan_migration_test_bp = Blueprint('vlan_migration_test', __name__)

# Global job tracker
current_job = None

def run_reset_worker(job_id):
    """Worker thread to reset TST 01 to AZP 30 config"""
    global current_job
    current_job['status'] = 'running'
    current_job['start_time'] = datetime.now()
    
    try:
        # Add log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'reset',
            'message': f"Starting reset of {TEST_NETWORK['name']} to {TEST_NETWORK['source_network_name']} configuration"
        }
        current_job['console_logs'].append(log_entry)
        
        # Run the restore script with auto-confirm
        cmd = [
            'python3',
            '/usr/local/bin/Main/restore_azp30_to_tst01.py'
        ]
        
        env = os.environ.copy()
        env['SKIP_CONFIRMATION'] = '1'  # Set environment variable to skip confirmation
        
        # Also pipe 'yes' to stdin in case the script reads from stdin
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )
        
        # Send 'yes' to stdin
        process.stdin.write('yes\n')
        process.stdin.flush()
        process.stdin.close()
        
        # Stream output
        for line in process.stdout:
            if line.strip():
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'phase': 'reset',
                    'message': line.strip()
                }
                current_job['console_logs'].append(log_entry)
        
        process.wait()
        
        if process.returncode == 0:
            current_job['status'] = 'completed'
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'phase': 'complete',
                'message': f"✅ Successfully reset {TEST_NETWORK['name']} to {TEST_NETWORK['source_network_name']} configuration"
            }
            current_job['console_logs'].append(log_entry)
        else:
            current_job['status'] = 'failed'
            current_job['error'] = 'Reset script failed'
            
    except Exception as e:
        current_job['status'] = 'failed'
        current_job['error'] = str(e)
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'error',
            'message': f"Reset failed: {str(e)}"
        }
        current_job['console_logs'].append(log_entry)
    
    current_job['end_time'] = datetime.now()

def run_migration_worker(job_id):
    """Worker thread to run migration on TST 01"""
    global current_job
    current_job['status'] = 'running'
    current_job['start_time'] = datetime.now()
    
    try:
        # Migration start log
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'start',
            'message': f"Starting VLAN migration for {TEST_NETWORK['name']}"
        }
        current_job['console_logs'].append(log_entry)
        
        # Run the migration script with debug version
        cmd = [
            'python3',
            '/usr/local/bin/Main/vlan_migration_complete_debug.py',
            '--network-id', TEST_NETWORK['id']
        ]
        
        env = os.environ.copy()
        env['SKIP_CONFIRMATION'] = '1'
        
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
                # Determine phase from output
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
                    'message': line.strip()
                }
                current_job['console_logs'].append(log_entry)
        
        process.wait()
        
        if process.returncode == 0:
            current_job['status'] = 'validating'
            
            # Run validation
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'phase': 'validation',
                'message': "Running firewall rule validation..."
            }
            current_job['console_logs'].append(log_entry)
            
            val_cmd = [
                'python3',
                '/usr/local/bin/Main/detailed_rule_comparison.py'
            ]
            
            val_process = subprocess.run(
                val_cmd,
                capture_output=True,
                text=True
            )
            
            # Add validation output
            for line in val_process.stdout.splitlines():
                if line.strip():
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'phase': 'validation',
                        'message': line.strip()
                    }
                    current_job['console_logs'].append(log_entry)
            
            # Check validation result
            if 'Match percentage: 100.0%' in val_process.stdout:
                current_job['validation_status'] = 'passed'
                current_job['validation_details'] = 'Firewall rules match NEO 07 template 100%'
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'phase': 'complete',
                    'message': "✅ Migration completed successfully! Validation: PASSED (100% match)"
                }
            else:
                current_job['validation_status'] = 'warning'
                current_job['validation_details'] = val_process.stdout
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'phase': 'warning',
                    'message': "⚠️ Migration completed but validation shows differences"
                }
            
            current_job['console_logs'].append(log_entry)
            current_job['status'] = 'completed'
        else:
            current_job['status'] = 'failed'
            current_job['error'] = 'Migration script failed'
            
    except Exception as e:
        current_job['status'] = 'failed'
        current_job['error'] = str(e)
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'error',
            'message': f"Migration failed: {str(e)}"
        }
        current_job['console_logs'].append(log_entry)
    
    current_job['end_time'] = datetime.now()

@vlan_migration_test_bp.route('/api/vlan-migration-test/network-info', methods=['GET'])
def get_test_network_info():
    """Get TST 01 network information"""
    try:
        headers = {
            'X-Cisco-Meraki-API-Key': API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Get current VLANs
        vlan_url = f"https://api.meraki.com/api/v1/networks/{TEST_NETWORK['id']}/appliance/vlans"
        vlan_response = requests.get(vlan_url, headers=headers)
        
        vlans = []
        legacy_vlans = []
        if vlan_response.status_code == 200:
            vlans = vlan_response.json()
            legacy_vlans = [v for v in vlans if str(v['id']) in ['1', '101', '201', '801']]
        
        # Get firewall rules count
        fw_url = f"https://api.meraki.com/api/v1/networks/{TEST_NETWORK['id']}/appliance/firewall/l3FirewallRules"
        fw_response = requests.get(fw_url, headers=headers)
        
        rule_count = 0
        if fw_response.status_code == 200:
            rules = fw_response.json()
            rule_count = len(rules.get('rules', []))
        
        return jsonify({
            'network': {
                'id': TEST_NETWORK['id'],
                'name': TEST_NETWORK['name'],
                'vlans': vlans,
                'legacy_vlans': [v['id'] for v in legacy_vlans],
                'needs_migration': len(legacy_vlans) > 0,
                'firewall_rule_count': rule_count,
                'source_network': TEST_NETWORK['source_network_name']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vlan_migration_test_bp.route('/api/vlan-migration-test/reset', methods=['POST'])
def reset_test_network():
    """Reset TST 01 to AZP 30 configuration"""
    global current_job
    
    # Check if a job is already running
    if current_job and current_job['status'] in ['running', 'initializing']:
        return jsonify({'error': 'A job is already running'}), 400
    
    # Create new job
    job_id = f"reset_{int(time.time() * 1000)}"
    current_job = {
        'id': job_id,
        'type': 'reset',
        'status': 'initializing',
        'console_logs': [],
        'start_time': None,
        'end_time': None
    }
    
    # Start worker thread
    thread = threading.Thread(target=run_reset_worker, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': f'Resetting {TEST_NETWORK["name"]} to {TEST_NETWORK["source_network_name"]} configuration'
    })

@vlan_migration_test_bp.route('/api/vlan-migration-test/migrate', methods=['POST'])
def migrate_test_network():
    """Run migration on TST 01"""
    global current_job
    
    # Check if a job is already running
    if current_job and current_job['status'] in ['running', 'initializing']:
        return jsonify({'error': 'A job is already running'}), 400
    
    # Create new job
    job_id = f"migration_{int(time.time() * 1000)}"
    current_job = {
        'id': job_id,
        'type': 'migration',
        'status': 'initializing',
        'console_logs': [],
        'validation_status': None,
        'validation_details': None,
        'start_time': None,
        'end_time': None
    }
    
    # Start worker thread
    thread = threading.Thread(target=run_migration_worker, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': f'Starting VLAN migration for {TEST_NETWORK["name"]}'
    })

@vlan_migration_test_bp.route('/api/vlan-migration-test/status', methods=['GET'])
def get_job_status():
    """Get current job status"""
    global current_job
    
    if not current_job:
        return jsonify({'status': 'idle', 'message': 'No job running'})
    
    # Get new logs since last check
    since = request.args.get('since', 0, type=int)
    new_logs = current_job['console_logs'][since:]
    
    response = {
        'job_id': current_job['id'],
        'type': current_job['type'],
        'status': current_job['status'],
        'console_logs': new_logs,
        'log_index': len(current_job['console_logs']),
        'error': current_job.get('error')
    }
    
    if current_job['type'] == 'migration':
        response['validation_status'] = current_job.get('validation_status')
        response['validation_details'] = current_job.get('validation_details')
    
    if current_job.get('start_time') and current_job.get('end_time'):
        response['duration'] = str(current_job['end_time'] - current_job['start_time'])
    
    return jsonify(response)