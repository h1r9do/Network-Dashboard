#\!/usr/bin/env python3
"""
Ultra Slow SSH Connection Script
================================
For devices that require extremely slow typing
"""

import paramiko
import time
import sys
from datetime import datetime

class UltraSlowSSH:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.channel = None
        
    def connect(self):
        """Connect with manual authentication to control typing speed"""
        print(f"\n[CONNECTING] {self.host}:{self.port}")
        print(f"[INFO] Username: {self.username}")
        print(f"[INFO] Using ULTRA SLOW typing mode")
        
        try:
            # Create transport
            transport = paramiko.Transport((self.host, self.port))
            transport.connect()
            
            # Don't authenticate yet - we'll do it manually
            self.channel = transport.open_session()
            self.channel.get_pty()
            self.channel.invoke_shell()
            
            print("[SHELL] Interactive shell opened")
            time.sleep(2)  # Wait for banner
            
            # Read initial prompt
            output = self.read_until_prompt(timeout=5)
            print(f"[INITIAL OUTPUT]\n{output}")
            
            # Look for login prompt
            if 'login' in output.lower() or 'username' in output.lower():
                print("\n[LOGIN] Username prompt detected")
                self.slow_type_line(self.username, char_delay=0.3)
                time.sleep(1)
                output = self.read_until_prompt(timeout=5)
            
            # Send password VERY slowly
            print("\n[PASSWORD] Sending password with 0.5s delay per character...")
            print("[PASSWORD] Progress: ", end='', flush=True)
            
            for i, char in enumerate(self.password):
                self.channel.send(char)
                # Mask password output
                if char == '\!':
                    print('\!', end='', flush=True)
                else:
                    print('*', end='', flush=True)
                time.sleep(0.5)  # 500ms per character\!
            
            print(" [ENTER]")
            self.channel.send('\n')
            time.sleep(2)  # Wait after password
            
            # Check if login successful
            output = self.read_until_prompt(timeout=10)
            
            if 'failed' in output.lower() or 'denied' in output.lower():
                print(f"\n[FAILED] Authentication failed")
                print(f"[OUTPUT] {output}")
                return False
            else:
                print(f"\n[SUCCESS] Logged in successfully\!")
                self.transport = transport
                return True
                
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            return False
    
    def slow_type_line(self, text, char_delay=0.3):
        """Type a line very slowly"""
        print(f"[TYPING] '{text}' with {char_delay}s per char")
        print("[PROGRESS] ", end='', flush=True)
        
        for char in text:
            self.channel.send(char)
            print(char, end='', flush=True)
            time.sleep(char_delay)
        
        print(" [ENTER]")
        self.channel.send('\n')
        time.sleep(1)
    
    def read_until_prompt(self, timeout=10):
        """Read output until we see a prompt"""
        output = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.channel.recv_ready():
                chunk = self.channel.recv(1024).decode('utf-8', errors='ignore')
                output += chunk
                
                # Check for prompts
                if any(p in chunk for p in ['>', '#', '$', ':', 'password', 'Password']):
                    break
            
            time.sleep(0.1)
        
        return output
    
    def execute_command(self, command, char_delay=0.2):
        """Execute a command with slow typing"""
        print(f"\n[COMMAND] {command}")
        
        # Clear buffer
        if self.channel.recv_ready():
            self.channel.recv(4096)
        
        # Type command slowly
        self.slow_type_line(command, char_delay)
        
        # Get output
        output = self.read_until_prompt(timeout=10)
        print(f"[OUTPUT]\n{output}")
        
        return output
    
    def disconnect(self):
        """Close connection"""
        try:
            if self.channel:
                self.channel.close()
            if hasattr(self, 'transport'):
                self.transport.close()
            print("\n[DISCONNECTED]")
        except:
            pass

def main():
    """Test ultra slow SSH connection"""
    host = "10.44.158.41"
    username = "mbambic"
    password = "Aud\!o\!994"
    
    print("="*70)
    print("ULTRA SLOW SSH CONNECTION TEST")
    print(f"Time: {datetime.now()}")
    print(f"Target: {host}")
    print("="*70)
    
    # Create client
    ssh = UltraSlowSSH(host, username, password)
    
    # Try to connect
    if ssh.connect():
        # Test some commands
        print("\n" + "="*70)
        print("Testing commands...")
        print("="*70)
        
        ssh.execute_command("show version", char_delay=0.1)
        ssh.execute_command("show clock", char_delay=0.1)
        ssh.execute_command("exit", char_delay=0.1)
        
        ssh.disconnect()
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF < /dev/null
