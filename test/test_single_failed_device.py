#\!/usr/bin/env python3
"""
Test single failed device with improved connection handling
"""

import paramiko
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_device_connection():
    hostname = 'EQX-CldTrst-8500-01'
    ip = '10.44.158.41'
    username = 'mbambic'
    password = 'Aud\!o\!994'
    
    logger.info(f"Testing connection to {hostname} ({ip})")
    logger.info(f"Using credentials: {username}/{password}")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect with longer timeout and authentication parameters
        ssh.connect(
            ip, 
            username=username, 
            password=password, 
            timeout=30,
            auth_timeout=30,
            banner_timeout=30,
            look_for_keys=False,
            allow_agent=False
        )
        
        logger.info("SSH connection successful\!")
        
        # Try a simple command with delay
        time.sleep(2)
        stdin, stdout, stderr = ssh_client.exec_command('show version  < /dev/null |  include Version', timeout=30)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        logger.info(f"Command output: {output}")
        if error:
            logger.warning(f"Command error: {error}")
        
        ssh.close()
        return True, output
        
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    success, result = test_device_connection()
    print(f"Success: {success}")
    print(f"Result: {result}")
