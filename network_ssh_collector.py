#!/usr/bin/env python3
"""
Network Device SSH Collector
============================

Connects to network devices and collects inventory data using SSH.
Handles interactive sessions and rate limiting.
"""

import subprocess
import os
import sys
import time
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration
SSH_USER = "mbambic"
SSH_PASS = "Aud!o!994"
RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_FAILURES = 5
DELAY_BETWEEN_COMMANDS = 1
DELAY_BETWEEN_DEVICES = 5

# Failure tracking
failure_tracker = defaultdict(list)

def log(message, level="INFO"):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {level} - {message}")

def check_rate_limit(ip_address):
    """Check if we can attempt connection to this IP"""
    current_time = datetime.now()
    window_start = current_time - timedelta(seconds=RATE_LIMIT_WINDOW)
    
    # Clean old failures
    failure_tracker[ip_address] = [
        fail_time for fail_time in failure_tracker[ip_address]
        if fail_time > window_start
    ]
    
    if len(failure_tracker[ip_address]) >= MAX_FAILURES:
        log(f"Rate limit reached for {ip_address}", "WARNING")
        return False
    
    return True

def record_failure(ip_address):
    """Record a connection failure"""
    failure_tracker[ip_address].append(datetime.now())
    log(f"Recorded failure for {ip_address}. Count: {len(failure_tracker[ip_address])}", "WARNING")

def execute_ssh_commands(hostname, ip_address, commands):
    """Execute multiple commands in a single SSH session"""
    
    if not check_rate_limit(ip_address):
        return None
    
    try:
        # Create a script to run all commands
        script_content = "#!/bin/bash\n"
        for cmd in commands:
            script_content += f"echo '===COMMAND:{cmd}==='\n"
            script_content += f"{cmd}\n"
            script_content += "echo '===END_COMMAND==='\n"
            script_content += f"sleep {DELAY_BETWEEN_COMMANDS}\n"
        
        # Use sshpass with SSH
        ssh_cmd = [
            'sshpass', '-p', SSH_PASS,
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            '-o', 'LogLevel=ERROR',
            '-t',  # Force pseudo-terminal allocation
            f'{SSH_USER}@{ip_address}',
            'bash', '-s'
        ]
        
        log(f"Connecting to {hostname} ({ip_address})")
        
        # Execute
        process = subprocess.Popen(
            ssh_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=script_content, timeout=60)
        
        if process.returncode != 0:
            if "Login Failed" in stderr or "Authentication" in stderr:
                record_failure(ip_address)
            log(f"SSH failed for {hostname}: {stderr}", "ERROR")
            return None
        
        # Parse output
        results = {}
        current_command = None
        current_output = []
        
        for line in stdout.split('\n'):
            if line.startswith('===COMMAND:'):
                if current_command:
                    results[current_command] = '\n'.join(current_output)
                current_command = line.replace('===COMMAND:', '').replace('===', '').strip()
                current_output = []
            elif line == '===END_COMMAND===':
                if current_command:
                    results[current_command] = '\n'.join(current_output)
                current_command = None
                current_output = []
            elif current_command and not line.startswith('WARNING!'):
                current_output.append(line)
        
        return results
        
    except subprocess.TimeoutExpired:
        log(f"Timeout connecting to {hostname}", "ERROR")
        record_failure(ip_address)
        return None
    except Exception as e:
        log(f"Error connecting to {hostname}: {str(e)}", "ERROR")
        record_failure(ip_address)
        return None

def collect_device_inventory(hostname, ip_address):
    """Collect inventory from a single device"""
    
    commands = [
        'terminal length 0',  # Disable paging
        'show version',
        'show inventory',
        'show module',
        'show interface status',
        'show interface transceiver'
    ]
    
    log(f"Collecting inventory from {hostname} ({ip_address})")
    
    results = execute_ssh_commands(hostname, ip_address, commands)
    
    if results:
        inventory = {
            'hostname': hostname,
            'ip_address': ip_address,
            'collection_time': datetime.now().isoformat(),
            'raw_outputs': results
        }
        
        # Save to file
        filename = f"/tmp/{hostname}_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(inventory, f, indent=2)
        
        log(f"Saved inventory to {filename}")
        return inventory
    else:
        log(f"Failed to collect inventory from {hostname}", "ERROR")
        return None

def main():
    """Main function"""
    log("Starting Network SSH Collector")
    
    # Test devices
    devices = [
        {"hostname": "AL-5000-01", "ip": "10.101.145.125"},
        {"hostname": "AL-5000-02", "ip": "10.101.145.126"},
        {"hostname": "2960-CX-Series-NOC", "ip": "10.0.255.10"}
    ]
    
    successful = 0
    
    for device in devices:
        result = collect_device_inventory(device['hostname'], device['ip'])
        if result:
            successful += 1
        
        # Delay between devices
        time.sleep(DELAY_BETWEEN_DEVICES)
    
    log(f"Collection complete. Success: {successful}/{len(devices)}")

if __name__ == "__main__":
    main()
