#\!/usr/bin/env python3
"""
SSH Connection Test with Slow Typing - Visual Output Version
============================================================
Shows real-time output as connection progresses
"""

import paramiko
import time
import sys
import socket
from datetime import datetime

class SlowTypeSSHClient:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.shell = None
        
    def slow_type(self, text, delay=0.1):
        """Type text slowly with visual feedback"""
        print(f"\n[TYPING] Sending command slowly (delay={delay}s per char):")
        print(f"[TYPING] Command: {text}")
        print("[TYPING] Progress: ", end='', flush=True)
        
        for i, char in enumerate(text):
            self.shell.send(char)
            print(char, end='', flush=True)
            time.sleep(delay)
            
        print(" [ENTER]", flush=True)
        self.shell.send('\n')
        time.sleep(0.5)
    
    def wait_for_prompt(self, timeout=10):
        """Wait for device prompt with visual output"""
        print(f"\n[WAITING] Looking for prompt (timeout={timeout}s)...")
        start_time = time.time()
        output = ""
        
        while time.time() - start_time < timeout:
            if self.shell.recv_ready():
                chunk = self.shell.recv(1024).decode('utf-8', errors='ignore')
                output += chunk
                
                # Show what we received
                print(f"\n[RECEIVED] {len(chunk)} bytes:")
                print("=" * 60)
                print(chunk)
                print("=" * 60)
                
                # Check for prompts
                if any(prompt in chunk for prompt in ['>', '#', '$', ':', 'assword']):
                    print(f"[PROMPT DETECTED] Found prompt indicator")
                    break
            else:
                print(".", end='', flush=True)
                
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        print(f"\n[TIMING] Waited {elapsed:.1f} seconds")
        return output
    
    def connect(self):
        """Establish SSH connection with visual feedback"""
        try:
            print(f"\n[CONNECTING] Initiating SSH to {self.host}:{self.port}")
            print(f"[CONNECTING] Username: {self.username}")
            print(f"[CONNECTING] Password: {'*' * len(self.password)}")
            
            # Create SSH client
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            print("[CONNECTING] Attempting connection...")
            
            # Connect
            self.client.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30,
                look_for_keys=False,
                allow_agent=False
            )
            
            print("[CONNECTED] SSH connection established\!")
            
            # Get interactive shell
            print("[SHELL] Opening interactive shell...")
            self.shell = self.client.invoke_shell()
            time.sleep(1)
            
            # Clear initial output
            print("[SHELL] Reading initial banner/prompt...")
            initial_output = self.wait_for_prompt(5)
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Connection failed: {str(e)}")
            print(f"[ERROR] Exception type: {type(e).__name__}")
            return False
    
    def execute_command(self, command, delay=0.05):
        """Execute command with visual feedback"""
        try:
            print(f"\n{'='*70}")
            print(f"[COMMAND] Preparing to execute: {command}")
            print(f"{'='*70}")
            
            # Clear any pending output
            if self.shell.recv_ready():
                print("[CLEARING] Clearing buffer...")
                cleared = self.shell.recv(4096)
                print(f"[CLEARED] {len(cleared)} bytes")
            
            # Send command slowly
            self.slow_type(command, delay)
            
            # Get output
            output = self.wait_for_prompt(10)
            
            return output
            
        except Exception as e:
            print(f"\n[ERROR] Command execution failed: {str(e)}")
            return None
    
    def disconnect(self):
        """Close SSH connection"""
        try:
            print("\n[DISCONNECTING] Closing connection...")
            if self.shell:
                self.shell.close()
            if self.client:
                self.client.close()
            print("[DISCONNECTED] Connection closed")
        except Exception as e:
            print(f"[ERROR] During disconnect: {e}")

def main():
    """Main test function"""
    host = "10.44.158.41"
    username = "mbambic"
    password = "Aud\!o\!994"
    
    print("="*70)
    print(f"SSH SLOW TYPING TEST - VISUAL OUTPUT")
    print(f"Time: {datetime.now()}")
    print(f"Target: {host}")
    print("="*70)
    
    # Test connectivity first
    print(f"\n[CONNECTIVITY] Testing if {host} is reachable on port 22...")
    try:
        sock = socket.create_connection((host, 22), timeout=5)
        sock.close()
        print(f"[CONNECTIVITY] ✓ Host is reachable")
    except Exception as e:
        print(f"[CONNECTIVITY] ✗ Cannot reach host: {e}")
        return 1
    
    # Create SSH client
    ssh = SlowTypeSSHClient(host, username, password)
    
    # Try to connect
    if ssh.connect():
        print("\n" + "="*70)
        print("[SUCCESS] CONNECTION ESTABLISHED\!")
        print("="*70)
        
        # Test commands
        test_commands = [
            ("show version", 0.05),
            ("show running-config  < /dev/null |  include hostname", 0.05),
            ("exit", 0.05)
        ]
        
        for cmd, delay in test_commands:
            input(f"\nPress ENTER to execute: {cmd}")
            ssh.execute_command(cmd, delay)
        
        ssh.disconnect()
        return 0
    else:
        print("\n" + "="*70)
        print("[FAILED] COULD NOT ESTABLISH CONNECTION")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
