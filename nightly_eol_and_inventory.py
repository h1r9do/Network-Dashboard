#!/usr/bin/env python3
"""
Combined nightly script for EOL tracking and inventory updates
Runs EOL tracker first, then enhanced inventory collection
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

# Setup logging
LOG_FILE = '/var/log/nightly-eol-and-inventory.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_path, description):
    """Run a Python script and capture output"""
    logger.info(f"Starting {description}...")
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"✓ {description} completed successfully in {duration:.1f} seconds")
            if result.stdout:
                logger.info(f"Output:\n{result.stdout}")
            return True
        else:
            logger.error(f"✗ {description} failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"Error output:\n{result.stderr}")
            if result.stdout:
                logger.error(f"Standard output:\n{result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {description} timed out after 2 hours")
        return False
    except Exception as e:
        logger.error(f"✗ {description} failed with exception: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("=" * 70)
    logger.info("Starting nightly EOL and inventory update")
    logger.info("=" * 70)
    
    overall_start = datetime.now()
    success = True
    
    # Define scripts to run in order
    scripts = [
        ('/usr/local/bin/Main/meraki_eol_tracker.py', 'EOL Tracker'),
        ('/usr/local/bin/Main/nightly_inventory_db_enhanced.py', 'Enhanced Inventory Collection')
    ]
    
    # Run each script
    for script_path, description in scripts:
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            success = False
            continue
        
        if not run_script(script_path, description):
            success = False
            # Continue with other scripts even if one fails
    
    # Summary
    total_duration = (datetime.now() - overall_start).total_seconds()
    logger.info("=" * 70)
    
    if success:
        logger.info(f"✓ All tasks completed successfully in {total_duration:.1f} seconds")
    else:
        logger.error(f"✗ Some tasks failed. Total duration: {total_duration:.1f} seconds")
    
    logger.info("=" * 70)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())