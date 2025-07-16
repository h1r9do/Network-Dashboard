#\!/usr/bin/env python3
import pty
import os
import time
import select
import sys

def slow_ssh():
    print("Starting SSH with slow typing support...")
    print("Target: 10.44.158.41")
    print("User: mbambic")
    print("-" * 60)
    
    master, slave = pty.openpty()
    
    pid = os.fork()
    if pid == 0:  # Child process
        os.close(master)
        os.dup2(slave, 0)
        os.dup2(slave, 1) 
        os.dup2(slave, 2)
        os.execvp("ssh", ["ssh", "-o", "StrictHostKeyChecking=no", "mbambic@10.44.158.41"])
    
    # Parent process
    os.close(slave)
    
    password = "Aud\!o\!994"
    password_sent = False
    buffer = b""
    
    while True:
        try:
            r, w, e = select.select([master], [], [], 0.1)
            
            if master in r:
                data = os.read(master, 1024)
                if data:
                    buffer += data
                    output = data.decode("utf-8", errors="ignore")
                    sys.stdout.write(output)
                    sys.stdout.flush()
                    
                    if not password_sent and b"password:" in buffer.lower():
                        print("\n[DETECTED PASSWORD PROMPT]")
                        print("[TYPING PASSWORD WITH 0.5s DELAY PER CHARACTER]")
                        time.sleep(1)
                        
                        # Type password VERY slowly
                        for i, char in enumerate(password):
                            os.write(master, char.encode())
                            if char == "\!":
                                print("\!", end="", flush=True)
                            else:
                                print("*", end="", flush=True)
                            time.sleep(0.5)  # 500ms per character
                        
                        print(" [SENDING ENTER]")
                        os.write(master, b"\n")
                        password_sent = True
                        time.sleep(1)
                        
                        # After password, wait a bit then send a test command
                        time.sleep(3)
                        print("\n[SENDING TEST COMMAND: show version]")
                        cmd = "show version"
                        for char in cmd:
                            os.write(master, char.encode())
                            print(char, end="", flush=True)
                            time.sleep(0.1)
                        print()
                        os.write(master, b"\n")
                        
                        # Wait for output then exit
                        time.sleep(5)
                        os.write(master, b"exit\n")
                else:
                    break
        except OSError:
            break
        
        # Check if child process exited
        try:
            pid_result, status = os.waitpid(pid, os.WNOHANG)
            if pid_result \!= 0:
                break
        except:
            break
    
    os.close(master)
    print("\n[SSH session ended]")

if __name__ == "__main__":
    slow_ssh()
