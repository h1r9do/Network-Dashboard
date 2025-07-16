#!/usr/bin/env python3
"""
Monitor DDNS deployment progress
"""

import os
import time
import subprocess
from datetime import datetime

def check_process_status():
    """Check if the bulk deployment script is still running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'bulk_enable_ddns_optimized.py'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def get_log_tail(lines=10):
    """Get the last N lines from the deployment log"""
    try:
        if os.path.exists('ddns_deployment.log'):
            with open('ddns_deployment.log', 'r') as f:
                lines_list = f.readlines()
                return ''.join(lines_list[-lines:]) if lines_list else "Log file empty"
        else:
            return "Log file not found"
    except Exception as e:
        return f"Error reading log: {str(e)}"

def main():
    """Monitor deployment progress"""
    print('=== DDNS Deployment Monitor ===')
    print(f'Started monitoring at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    iteration = 0
    while True:
        iteration += 1
        is_running = check_process_status()
        
        print(f'Check #{iteration} - {datetime.now().strftime("%H:%M:%S")}')
        print(f'Process status: {"RUNNING" if is_running else "STOPPED"}')
        
        if os.path.exists('ddns_deployment.log'):
            file_size = os.path.getsize('ddns_deployment.log')
            print(f'Log file size: {file_size} bytes')
            
            if file_size > 0:
                print('Recent log output:')
                log_tail = get_log_tail(5)
                for line in log_tail.split('\n'):
                    if line.strip():
                        print(f'  {line}')
        else:
            print('Log file not created yet')
        
        print('-' * 50)
        
        if not is_running:
            print('Deployment process has stopped.')
            print('Final log output:')
            final_log = get_log_tail(20)
            print(final_log)
            break
        
        # Wait 30 seconds before next check
        time.sleep(30)

if __name__ == '__main__':
    main()