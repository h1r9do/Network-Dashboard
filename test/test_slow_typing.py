#\!/usr/bin/env python3
"""
Test device connection with slow password typing
"""

import paramiko
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def slow_auth_connection(hostname, ip, username, password):
    """Connect with slow password typing simulation"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to device
        logger.info(f"Connecting to {hostname} ({ip})...")
        ssh.connect(
            ip,
            username=username,
            password=password,
            timeout=60,
            auth_timeout=60,
            banner_timeout=60,
            look_for_keys=False,
            allow_agent=False
        )
        
        logger.info("✅ SSH connection successful\!")
        
        # Wait 2 seconds then try command
        time.sleep(2)
        
        commands = [
            'show version  < /dev/null |  include Version',
            'show running-config | include snmp-server',
            'show ip access-lists'
        ]
        
        results = {}
        for cmd in commands:
            logger.info(f"Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            results[cmd] = {
                'output': output,
                'error': error
            }
            
            if output:
                logger.info(f"✅ Command successful: {len(output)} characters")
            if error:
                logger.warning(f"Command error: {error}")
            
            time.sleep(1)
        
        ssh.close()
        return True, results
        
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False, str(e)

def main():
    # Test one failed device
    hostname = 'EQX-CldTrst-8500-01'
    ip = '10.44.158.41'
    username = 'mbambic'
    password = 'Aud\!o\!994'
    
    logger.info("=" * 60)
    logger.info("TESTING SLOW AUTHENTICATION METHOD")
    logger.info("=" * 60)
    
    success, result = slow_auth_connection(hostname, ip, username, password)
    
    if success:
        logger.info(f"✅ SUCCESS - Connected to {hostname}")
        for cmd, data in result.items():
            if data['output']:
                logger.info(f"Command '{cmd}': {len(data['output'])} chars output")
                # Show first 100 chars of output
                preview = data['output'][:100].replace('\n', ' ')
                logger.info(f"Preview: {preview}...")
    else:
        logger.error(f"❌ FAILED - {result}")

if __name__ == "__main__":
    main()
