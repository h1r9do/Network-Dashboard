#\!/usr/bin/env python3
"""
SSH Connection Test with Slow Typing for Discount Tire Infrastructure
=====================================================================

Tests SSH connection to specific device using slow typing mechanism
to handle legacy devices that may have input buffer limitations.
"""

import paramiko
import time
import sys
import socket
from datetime import datetime

class SlowTypeSSHClient:
    def __init__(self, host, username, password, port=22, debug=True):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.debug = debug
        self.client = None
        self.shell = None
        
    def log(self, message):
        """Log message with timestamp"""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def slow_type(self, text, delay=0.1):
        """Type text slowly with specified delay between characters"""
        self.log(f"Slow typing: {text[:20]}... (delay={delay}s)")
        for char in text:
            self.shell.send(char)
            time.sleep(delay)
        self.shell.send('\n')
        time.sleep(0.5)  # Wait after sending command
    
    def wait_for_prompt(self, timeout=10):
        """Wait for device prompt and return the output"""
        start_time = time.time()
        output = ""
        
        while time.time() - start_time < timeout:
            if self.shell.recv_ready():
                chunk = self.shell.recv(1024).decode('utf-8', errors='ignore')
                output += chunk
                self.log(f"Received: {repr(chunk[-50:])}")
                
                # Check for common prompts
                if any(prompt in chunk for prompt in ['>', '#', '$', ':', 'assword']):
                    break
            time.sleep(0.1)
        
        return output
    
    def connect(self):
        """Establish SSH connection with slow typing support"""
        try:
            self.log(f"Connecting to {self.host}:{self.port}")
            
            # Create SSH client
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
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
            
            self.log("SSH connection established")
            
            # Get interactive shell
            self.shell = self.client.invoke_shell()
            time.sleep(1)
            
            # Clear initial output
            initial_output = self.wait_for_prompt(5)
            self.log(f"Initial prompt: {initial_output[-100:]}")
            
            return True
            
        except Exception as e:
            self.log(f"Connection failed: {str(e)}")
            return False
    
    def execute_command(self, command, delay=0.05):
        """Execute command with slow typing"""
        try:
            self.log(f"Executing: {command}")
            
            # Clear any pending output
            if self.shell.recv_ready():
                self.shell.recv(4096)
            
            # Send command slowly
            self.slow_type(command, delay)
            
            # Get output
            output = self.wait_for_prompt(10)
            
            return output
            
        except Exception as e:
            self.log(f"Command execution failed: {str(e)}")
            return None
    
    def disconnect(self):
        """Close SSH connection"""
        try:
            if self.shell:
                self.shell.close()
            if self.client:
                self.client.close()
            self.log("Disconnected")
        except:
            pass

def test_device(host):
    """Test SSH connection to specific device"""
    print(f"\n{'='*60}")
    print(f"Testing SSH to {host}")
    print(f"{'='*60}\n")
    
    # Connection parameters
    username = "dt-net-ro"
    password = "Aud\!o\!994"
    
    # Create SSH client
    ssh = SlowTypeSSHClient(host, username, password)
    
    # Test connection
    if ssh.connect():
        print("\n[SUCCESS] Connection established\!")
        
        # Test some commands
        test_commands = [
            "show version",
            "show running-config  < /dev/null |  include hostname",
            "exit"
        ]
        
        for cmd in test_commands:
            print(f"\nTesting command: {cmd}")
            output = ssh.execute_command(cmd)
            if output:
                print(f"Output preview: {output[:200]}...")
        
        ssh.disconnect()
        return True
    else:
        print("\n[FAILED] Could not establish connection")
        return False

if __name__ == "__main__":
    # Test against specific host
    test_host = "10.44.158.41"
    
    print(f"SSH Slow Typing Test - {datetime.now()}")
    print(f"Target: {test_host}")
    
    # First test if host is reachable
    try:
        sock = socket.create_connection((test_host, 22), timeout=5)
        sock.close()
        print(f"[OK] Host {test_host} is reachable on port 22")
    except:
        print(f"[ERROR] Cannot reach {test_host} on port 22")
        sys.exit(1)
    
    # Run SSH test
    success = test_device(test_host)
    
    print(f"\n{'='*60}")
    print(f"Test Result: {'PASSED' if success else 'FAILED'}")
    print(f"{'='*60}")
    
    sys.exit(0 if success else 1)
