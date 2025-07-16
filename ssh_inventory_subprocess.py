#\!/usr/bin/env python3
"""
SSH Inventory Collector using subprocess and sshpass
===================================================

This script connects to network devices via SSH using sshpass
and collects inventory data with rate limiting.
"""

import subprocess
import time
import json
import logging
from datetime import datetime, timedelta
import sys
import os
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Configuration
SSH_USERNAME = "mbambic"
SSH_PASSWORD = 'Aud\!o\!994'
SSH_TIMEOUT = 30  # seconds
CONNECTION_DELAY = 2  # seconds between connections
MAX_FAILURES_PER_WINDOW = 5  # max failures allowed
FAILURE_WINDOW = 300  # 5 minutes in seconds

# Track failures per device
failure_tracker = defaultdict(list)

class SSHInventoryCollector:
    def __init__(self):
        self.current_device = None
        
    def check_failure_rate(self, device_ip):
        """Check if we've exceeded the failure rate for this device"""
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=FAILURE_WINDOW)
        
        # Remove old failures outside the window
        failure_tracker[device_ip] = [
            fail_time for fail_time in failure_tracker[device_ip]
            if fail_time > window_start
        ]
        
        # Check if we've hit the limit
        if len(failure_tracker[device_ip]) >= MAX_FAILURES_PER_WINDOW:
            logger.warning(f"Rate limit hit for {device_ip}. Total failures: {len(failure_tracker[device_ip])}")
            return False
        
        return True
    
    def record_failure(self, device_ip):
        """Record a connection failure"""
        failure_tracker[device_ip].append(datetime.now())
        logger.warning(f"Recorded failure for {device_ip}. Total failures in window: {len(failure_tracker[device_ip])}")
    
    def execute_ssh_command(self, hostname, ip_address, command):
        """Execute a command via SSH using sshpass"""
        
        # Check failure rate before attempting
        if not self.check_failure_rate(ip_address):
            return None, "Rate limit exceeded"
        
        try:
            # Build SSH command
            ssh_cmd = [
                'sshpass', '-p', SSH_PASSWORD,
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                '-o', 'ServerAliveInterval=5',
                '-o', 'ServerAliveCountMax=3',
                f'{SSH_USERNAME}@{ip_address}',
                command
            ]
            
            logger.info(f"Executing on {hostname} ({ip_address}): {command}")
            
            # Execute command
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=SSH_TIMEOUT
            )
            
            if result.returncode == 0:
                return result.stdout, None
            else:
                error_msg = result.stderr or f"Command failed with return code {result.returncode}"
                # Check for login failures
                if "Login Failed" in error_msg or "Authentication" in error_msg:
                    self.record_failure(ip_address)
                return None, error_msg
                
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout on {hostname} ({ip_address})")
            return None, "Command timeout"
            
        except Exception as e:
            logger.error(f"SSH error for {hostname} ({ip_address}): {str(e)}")
            self.record_failure(ip_address)
            return None, str(e)
    
    def collect_inventory(self, hostname, ip_address):
        """Collect inventory information from the device"""
        
        self.current_device = hostname
        inventory_data = {
            'hostname': hostname,
            'ip_address': ip_address,
            'collection_timestamp': datetime.now().isoformat(),
            'commands': {}
        }
        
        # Define inventory commands
        commands = {
            'hostname': 'show hostname',
            'version': 'show version',
            'inventory': 'show inventory',
            'modules': 'show module',
            'interfaces': 'show interface status  < /dev/null |  head -50',  # Limit output
            'transceivers': 'show interface transceiver | head -50'  # Limit output
        }
        
        # Execute each command
        for cmd_name, command in commands.items():
            output, error = self.execute_ssh_command(hostname, ip_address, command)
            
            if output:
                inventory_data['commands'][cmd_name] = output
                logger.info(f"Successfully collected {cmd_name} from {hostname}")
            else:
                inventory_data['commands'][cmd_name] = f"Error: {error}"
                logger.warning(f"Failed to collect {cmd_name} from {hostname}: {error}")
            
            # Delay between commands
            time.sleep(1)
        
        return inventory_data

def test_devices():
    """Test connection to a few devices"""
    
    # Test devices
    test_devices = [
        {"hostname": "AL-5000-01", "ip": "10.101.145.125"},
        {"hostname": "AL-5000-02", "ip": "10.101.145.126"},
        {"hostname": "2960-CX-Series-NOC", "ip": "10.0.255.10"}
    ]
    
    collector = SSHInventoryCollector()
    results = []
    
    for device in test_devices:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {device['hostname']} ({device['ip']})")
        logger.info(f"{'='*60}")
        
        inventory = collector.collect_inventory(device['hostname'], device['ip'])
        results.append(inventory)
        
        # Save individual result
        filename = f"/tmp/inventory_{device['hostname']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(inventory, f, indent=2)
            logger.info(f"Saved inventory to {filename}")
        except Exception as e:
            logger.error(f"Failed to save inventory: {e}")
        
        # Delay between devices
        time.sleep(5)
    
    # Save combined results
    combined_file = f"/tmp/inventory_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(combined_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\nSaved combined inventory to {combined_file}")
    except Exception as e:
        logger.error(f"Failed to save combined inventory: {e}")
    
    return results

def main():
    """Main function"""
    logger.info("Starting SSH Inventory Collector (subprocess version)")
    
    # Check if sshpass is available
    try:
        subprocess.run(['which', 'sshpass'], check=True, capture_output=True)
    except:
        logger.error("sshpass is not installed. Please install it first: sudo yum install sshpass")
        return
    
    results = test_devices()
    
    # Summary
    success_count = sum(1 for r in results if any(v and not v.startswith("Error:") for v in r['commands'].values()))
    logger.info(f"\nCompleted. Success: {success_count}/{len(results)}")

if __name__ == "__main__":
    main()
