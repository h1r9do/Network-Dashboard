#!/usr/bin/env python3
"""
Test Nexus inventory collection
"""

import paramiko
import time

def test_nexus_inventory():
    devices = [
        {'name': 'AL-5000-01', 'ip': '10.101.145.125'},
        {'name': 'AL-7000-01-ADMIN', 'ip': '10.101.145.123'}
    ]
    
    for device in devices:
        print(f"\n{'='*60}")
        print(f"Testing {device['name']} ({device['ip']})")
        print(f"{'='*60}")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Use mbambic@ip format
            ssh.connect(
                hostname=device['ip'],
                username=f"mbambic@{device['ip']}",
                password='Aud!o!994',
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            commands = [
                'show inventory',
                'show module', 
                'show fex',
                'show interface transceiver | include Eth'
            ]
            
            for cmd in commands:
                print(f"\n--- {cmd} ---")
                try:
                    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
                    output = stdout.read().decode('utf-8', errors='ignore')
                    
                    # Show first 30 lines
                    lines = output.split('\n')[:30]
                    for line in lines:
                        print(line)
                    
                    if len(output.split('\n')) > 30:
                        print(f"... ({len(output.split('\n'))} total lines)")
                    
                except Exception as e:
                    print(f"Error: {e}")
            
            ssh.close()
            
        except Exception as e:
            print(f"Connection failed: {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    test_nexus_inventory()