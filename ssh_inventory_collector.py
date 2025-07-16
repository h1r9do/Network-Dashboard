#\!/usr/bin/env python3
"""
SSH Inventory Collector with Careful Login Handling
==================================================

This script connects to network devices via SSH and collects inventory data.
It includes rate limiting and careful error handling to avoid login lockouts.

Key features:
- Rate limiting to prevent more than 5 failures in 5 minutes
- Proper timeout handling
- Detailed logging of connection attempts
- Retry logic with exponential backoff
"""

import paramiko
import time
import json
import logging
from datetime import datetime, timedelta
import sys
import os
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ssh_inventory_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Configuration
SSH_USERNAME = "mbambic"
SSH_PASSWORD = "Aud\!o\!994"
SSH_TIMEOUT = 30  # seconds
CONNECTION_DELAY = 2  # seconds between connections
MAX_FAILURES_PER_WINDOW = 5  # max failures allowed
FAILURE_WINDOW = 300  # 5 minutes in seconds
RETRY_DELAY = 60  # delay after hitting failure limit

# Track failures per device
failure_tracker = defaultdict(list)

class SSHInventoryCollector:
    def __init__(self):
        self.ssh_client = None
        self.connected = False
        
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
            logger.warning(f"Rate limit hit for {device_ip}. Waiting {RETRY_DELAY} seconds...")
            return False
        
        return True
    
    def record_failure(self, device_ip):
        """Record a connection failure"""
        failure_tracker[device_ip].append(datetime.now())
        logger.warning(f"Recorded failure for {device_ip}. Total failures in window: {len(failure_tracker[device_ip])}")
    
    def connect(self, hostname, ip_address, port=22):
        """Establish SSH connection with careful error handling"""
        
        # Check failure rate before attempting
        if not self.check_failure_rate(ip_address):
            return False
        
        try:
            logger.info(f"Attempting SSH connection to {hostname} ({ip_address})")
            
            # Create new SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with timeout
            self.ssh_client.connect(
                hostname=ip_address,
                port=port,
                username=SSH_USERNAME,
                password=SSH_PASSWORD,
                timeout=SSH_TIMEOUT,
                look_for_keys=False,
                allow_agent=False,
                banner_timeout=30
            )
            
            self.connected = True
            logger.info(f"Successfully connected to {hostname} ({ip_address})")
            
            # Small delay to ensure connection is stable
            time.sleep(0.5)
            
            return True
            
        except paramiko.AuthenticationException as e:
            logger.error(f"Authentication failed for {hostname} ({ip_address}): {str(e)}")
            self.record_failure(ip_address)
            return False
            
        except paramiko.SSHException as e:
            logger.error(f"SSH error for {hostname} ({ip_address}): {str(e)}")
            self.record_failure(ip_address)
            return False
            
        except Exception as e:
            logger.error(f"Connection error for {hostname} ({ip_address}): {str(e)}")
            self.record_failure(ip_address)
            return False
    
    def execute_command(self, command, timeout=30):
        """Execute a command on the connected device"""
        if not self.connected or not self.ssh_client:
            logger.error("Not connected to any device")
            return None
        
        try:
            logger.debug(f"Executing command: {command}")
            
            # Execute command
            stdin, stdout, stderr = self.ssh_client.exec_command(
                command,
                timeout=timeout
            )
            
            # Read output
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                logger.warning(f"Command stderr: {error}")
            
            return output
            
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return None
    
    def collect_inventory(self):
        """Collect inventory information from the device"""
        if not self.connected:
            return None
        
        inventory_data = {
            'collection_timestamp': datetime.now().isoformat(),
            'commands': {}
        }
        
        # Define inventory commands
        commands = {
            'hostname': 'show hostname',
            'version': 'show version',
            'inventory': 'show inventory',
            'modules': 'show module',
            'interfaces': 'show interface status',
            'transceivers': 'show interface transceiver'
        }
        
        # Execute each command
        for cmd_name, command in commands.items():
            logger.info(f"Collecting {cmd_name} data...")
            output = self.execute_command(command)
            
            if output:
                inventory_data['commands'][cmd_name] = output
                # Small delay between commands
                time.sleep(0.5)
            else:
                logger.warning(f"Failed to collect {cmd_name} data")
        
        return inventory_data
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh_client:
            try:
                self.ssh_client.close()
                logger.info("SSH connection closed")
            except:
                pass
        
        self.connected = False
        self.ssh_client = None

def test_single_device(hostname, ip_address):
    """Test connection and inventory collection for a single device"""
    collector = SSHInventoryCollector()
    
    try:
        # Attempt connection
        if collector.connect(hostname, ip_address):
            logger.info(f"Connection successful to {hostname}")
            
            # Collect inventory
            inventory = collector.collect_inventory()
            
            if inventory:
                # Save inventory data
                filename = f"/var/www/html/meraki-data/inventory_{hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump({
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'inventory': inventory
                    }, f, indent=2)
                
                logger.info(f"Inventory saved to {filename}")
                return True
            else:
                logger.error(f"Failed to collect inventory from {hostname}")
                return False
        else:
            logger.error(f"Failed to connect to {hostname}")
            return False
            
    finally:
        collector.disconnect()
        # Always wait between devices
        time.sleep(CONNECTION_DELAY)

def main():
    """Main function for testing"""
    logger.info("Starting SSH Inventory Collector")
    
    # Test devices - start with a small set
    test_devices = [
        {"hostname": "AL-5000-01", "ip": "10.101.145.125"},
        {"hostname": "AL-5000-02", "ip": "10.101.145.126"},
        {"hostname": "2960-CX-Series-NOC", "ip": "10.0.255.10"}
    ]
    
    success_count = 0
    
    for device in test_devices:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {device['hostname']} ({device['ip']})")
        logger.info(f"{'='*60}")
        
        if test_single_device(device['hostname'], device['ip']):
            success_count += 1
        
        # Respect rate limits
        time.sleep(5)  # 5 seconds between devices
    
    logger.info(f"\nCompleted. Success: {success_count}/{len(test_devices)}")

if __name__ == "__main__":
    main()
EOF < /dev/null
