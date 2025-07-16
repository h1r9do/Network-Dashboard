#!/usr/bin/env python3
"""
Complete Nightly Inventory Process
Runs both SNMP collection and web format processing in correct order
"""
import subprocess
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nightly_inventory_complete.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd, description):
    """Run a command and log the result"""
    logger.info(f"Starting: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Success: {description}")
            return True
        else:
            logger.error(f"❌ Failed: {description}")
            logger.error(f"Error: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Exception running {description}: {e}")
        return False

def main():
    """Run the complete nightly inventory process"""
    logger.info("="*60)
    logger.info("Starting Complete Nightly Inventory Process")
    logger.info("="*60)
    
    # Step 1: Run SNMP collection
    if not run_command(
        "cd /usr/local/bin/Main && python3 nightly_snmp_inventory_collection_final.py",
        "SNMP Collection"
    ):
        logger.error("SNMP collection failed, aborting")
        sys.exit(1)
    
    # Step 2: Run web format processing
    if not run_command(
        "cd /usr/local/bin/Main && python3 nightly_snmp_inventory_web_format_v2.py",
        "Web Format Processing"
    ):
        logger.error("Web format processing failed")
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("✅ Complete Nightly Inventory Process Successful")
    logger.info("="*60)

if __name__ == "__main__":
    main()