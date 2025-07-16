#\!/usr/bin/env python3
"""
SSH with pexpect for slow typing support
"""

import pexpect
import time
import sys

def slow_send(session, text, delay=0.5):
    """Send text character by character with delay"""
    print(f"[SLOW TYPING] Sending '{text}' with {delay}s delay per char")
    for char in text:
        session.send(char)
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def main():
    host = "10.44.158.41"
    username = "mbambic"
    password = "Aud\!o\!994"
    
    print(f"Connecting to {host}...")
    
    try:
        # Start SSH session
        ssh = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {username}@{host}')
        ssh.logfile = sys.stdout.buffer  # Show all output
        
        # Wait for password prompt
        i = ssh.expect(['password:', 'Password:', pexpect.TIMEOUT], timeout=30)
        
        if i == 2:
            print("Timeout waiting for password prompt")
            return 1
            
        print("\n[PASSWORD PROMPT DETECTED]")
        time.sleep(1)
        
        # Send password VERY slowly
        slow_send(ssh, password, delay=0.5)
        ssh.sendline('')  # Send enter
        
        # Wait for prompt or failure
        i = ssh.expect(['#', '>', '$', 'denied', 'failed', pexpect.TIMEOUT], timeout=30)
        
        if i in [0, 1, 2]:
            print("\n[SUCCESS] Logged in\!")
            
            # Try a command
            ssh.sendline('show version')
            ssh.expect(['#', '>', '$'], timeout=10)
            
            ssh.sendline('exit')
            
        else:
            print("\n[FAILED] Login failed")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF < /dev/null
