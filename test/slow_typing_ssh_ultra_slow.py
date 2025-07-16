#\!/usr/bin/env python3
"""
SSH Connection Test with ULTRA SLOW Typing
=========================================
For devices that require extremely slow typing
"""

import paramiko
import time
import sys
import socket
from datetime import datetime

class UltraSlowSSHClient:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.shell = None
        
    def ultra_slow_type(self, text, delay=0.5):
        """Type text VERY slowly"""
        print(f"\n[ULTRA SLOW TYPING] Delay: {delay}s per character")
        print(f"[TYPING] Text: {text}")
        print("[PROGRESS] ", end='', flush=True)
        
        for char in text:
            self.shell.send(char)
            print(char, end='', flush=True)
            time.sleep(delay)  # Much longer delay\!
            
        print(" [ENTER]", flush=True)
        self.shell.send('\n')
        time.sleep(1)  # Longer wait after enter
    
    def wait_for_prompt(self, timeout=15):
        """Wait for prompt with visual feedback"""
        print(f"\n[WAITING] Looking for prompt (timeout={timeout}s)...")
        start_time = time.time()
        output = ""
        last_data_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.shell.recv_ready():
                chunk = self.shell.recv(1024).decode('utf-8', errors='ignore')
                output += chunk
                last_data_time = time.time()
                
                print(f"\n[RECEIVED DATA]:")
                print("-" * 60)
                print(chunk)
                print("-" * 60)
                
                # Check for various prompts
                prompts = ['>', '#', '$', ':', 'assword', 'sername', 'ogin']
                for prompt in prompts:
                    if prompt in chunk.lower():
                        print(f"[PROMPT FOUND] Detected: '{prompt}'")
                        time.sleep(0.5)  # Give device time
                        return output
                        
            # If we haven't received data in 2 seconds, might be done
            elif time.time() - last_data_time > 2:
                print("\n[TIMEOUT] No data for 2 seconds, assuming prompt ready")
                break
                
            time.sleep(0.1)
        
        return output
    
    def connect_interactive(self):
        """Connect with interactive login handling"""
        try:
            print(f"\n[CONNECTING] SSH to {self.host}:{self.port}")
            
            # Create SSH client
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Create transport for manual authentication
            print("[TRANSPORT] Creating SSH transport...")
            transport = paramiko.Transport((self.host, self.port))
            transport.connect()
            
            # Get interactive shell first
            print("[SHELL] Opening interactive shell...")
            self.shell = transport.open_session()
            self.shell.get_pty()
            self.shell.invoke_shell()
            
            time.sleep(2)  # Wait for initial prompt
            
            # Read initial banner
            initial = self.wait_for_prompt(5)
            
            # Send username if prompted
            if 'ogin' in initial.lower() or 'sername' in initial.lower():
                print("\n[LOGIN] Username prompt detected, sending username...")
                self.ultra_slow_type(self.username, delay=0.3)
                
                # Wait for password prompt
                pwd_prompt = self.wait_for_prompt(10)
                
            # Send password
            print("\n[LOGIN] Sending password...")
            self.ultra_slow_type(self.password, delay=0.5)  # Extra slow for password\!
            
            # Wait for login result
            login_result = self.wait_for_prompt(10)
            
            if 'failed' in login_result.lower() or 'denied' in login_result.lower():
                print(f"\n[LOGIN FAILED] Authentication rejected")
                return False
            else:
                print(f"\n[LOGIN SUCCESS] Authentication successful\!")
                self.client = transport  # Store for later
                return True
                
        except Exception as e:
            print(f"\n[ERROR] Connection failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def execute_command(self, command, delay=0.3):
        """Execute command with ultra slow typing"""
        try:
            print(f"\n{'='*70}")
            print(f"[EXECUTING] Command: {command}")
            
            # Clear buffer
            if self.shell.recv_ready():
                self.shell.recv(4096)
            
            # Send command ultra slowly
            self.ultra_slow_type(command, delay)
            
            # Get output
            output = self.wait_for_prompt(15)
            
            return output
            
        except Exception as e:
            print(f"\n[ERROR] Command failed: {str(e)}")
            return None

def main():
    """Main test with ultra slow typing"""
    host = "10.44.158.41"
    username = "mbambic"
    password = "Aud\!o\!994"
    
    print("="*70)
    print("ULTRA SLOW SSH TYPING TEST")
    print(f"Time: {datetime.now()}")
    print(f"Target: {host}")
    print(f"Username: {username}")
    print("="*70)
    
    # Test connectivity
    print(f"\n[CONNECTIVITY] Testing {host}:22...")
    try:
        sock = socket.create_connection((host, 22), timeout=5)
        sock.close()
        print("[CONNECTIVITY] ✓ Host reachable")
    except Exception as e:
        print(f"[CONNECTIVITY] ✗ Cannot reach: {e}")
        return 1
    
    # Create client
    ssh = UltraSlowSSHClient(host, username, password)
    
    # Try to connect
    if ssh.connect_interactive():
        print("\n" + "="*70)
        print("CONNECTION ESTABLISHED\!")
        print("="*70)
        
        # Test a simple command
        input("\nPress ENTER to test 'show version' command...")
        ssh.execute_command("show version", delay=0.2)
        
        input("\nPress ENTER to exit...")
        ssh.execute_command("exit", delay=0.2)
        
        return 0
    else:
        print("\n" + "="*70)
        print("CONNECTION FAILED")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF < /dev/null
