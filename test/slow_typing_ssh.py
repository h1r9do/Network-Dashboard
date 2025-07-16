#\!/usr/bin/env python3
"""
SSH with slow password typing - test against 10.44.158.41
"""

import subprocess
import time
import sys
import select
import os
import pty

def slow_ssh_login(hostname, ip, username, password):
    """SSH with slow password typing"""
    print(f"Connecting to {hostname} ({ip}) with slow typing...")
    
    # Create SSH process with pseudo-terminal
    master, slave = pty.openpty()
    
    ssh_process = subprocess.Popen(
        ['ssh', f'{username}@{ip}'],
        stdin=slave,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    os.close(slave)  # Close slave end in parent
    
    output_buffer = ""
    
    try:
        while True:
            # Check if process is still running
            if ssh_process.poll() is not None:
                break
            
            # Read available output
            ready, _, _ = select.select([ssh_process.stdout, ssh_process.stderr], [], [], 0.1)
            
            for stream in ready:
                if stream == ssh_process.stdout:
                    chunk = stream.read(1024)
                    if chunk:
                        output_buffer += chunk
                        print(chunk, end='', flush=True)
                elif stream == ssh_process.stderr:
                    chunk = stream.read(1024)
                    if chunk:
                        print(f"STDERR: {chunk}", end='', flush=True)
            
            # Check for password prompt
            if "Password:" in output_buffer or "password:" in output_buffer:
                print(f"\n[DEBUG] Password prompt detected, waiting 1 second...")
                time.sleep(1)
                
                print(f"[DEBUG] Typing password slowly (0.1s per character)...")
                for i, char in enumerate(password):
                    os.write(master, char.encode())
                    print(f"[DEBUG] Sent character {i+1}/{len(password)}: '{char}'")
                    time.sleep(0.1)
                
                # Send enter
                os.write(master, b'\n')
                print(f"[DEBUG] Sent Enter key")
                
                # Clear the password prompt from buffer
                output_buffer = ""
                continue
            
            # Check for device prompt (successful login)
            if "#" in output_buffer or ">" in output_buffer:
                print(f"\n[SUCCESS] Device prompt detected\! Login successful.")
                
                # Send a test command
                test_cmd = "show version  < /dev/null |  include Version\n"
                print(f"[DEBUG] Sending test command: {test_cmd.strip()}")
                os.write(master, test_cmd.encode())
                
                # Wait for command output
                time.sleep(3)
                
                # Read command output
                ready, _, _ = select.select([ssh_process.stdout], [], [], 1)
                if ready:
                    cmd_output = ssh_process.stdout.read(2048)
                    if cmd_output:
                        print(f"[COMMAND OUTPUT]:\n{cmd_output}")
                
                # Send exit
                os.write(master, b'exit\n')
                break
            
            # Check for authentication failure
            if "Login Failed" in output_buffer or "Authentication failed" in output_buffer:
                print(f"\n[ERROR] Authentication failed")
                break
            
            time.sleep(0.1)
    
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
    
    finally:
        os.close(master)
        ssh_process.terminate()
        ssh_process.wait()
    
    print(f"[DEBUG] SSH session ended")

def main():
    print("=" * 60)
    print("SLOW TYPING SSH TEST")
    print("=" * 60)
    
    hostname = "EQX-CldTrst-8500-01"
    ip = "10.44.158.41"
    username = "mbambic"
    password = "Aud\!o\!994"
    
    print(f"Testing against: {hostname} ({ip})")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print("")
    
    slow_ssh_login(hostname, ip, username, password)

if __name__ == "__main__":
    main()
