#!/usr/bin/env python3
"""
Test script to push a single batch of confirmed circuits
This helps verify the push process is working before running the full push
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import the push_to_meraki function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from confirm_meraki_notes_db_fixed import push_to_meraki

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits')

# Create database session
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def main():
    """Test push with a small batch"""
    session = Session()
    
    try:
        # Get 5 unpushed confirmed circuits for testing
        result = session.execute(text("""
            SELECT DISTINCT network_name
            FROM enriched_circuits
            WHERE (wan1_confirmed = TRUE OR wan2_confirmed = TRUE)
                AND (pushed_to_meraki IS NULL OR pushed_to_meraki = FALSE)
            ORDER BY network_name
            LIMIT 5
        """))
        
        test_sites = [row[0] for row in result.fetchall()]
        
        if not test_sites:
            logger.info("No unpushed confirmed circuits found for testing.")
            return
        
        logger.info(f"Testing push with {len(test_sites)} sites:")
        for site in test_sites:
            logger.info(f"  - {site}")
        
        logger.info("\nStarting test push...")
        result = push_to_meraki(test_sites)
        
        if result.get('success'):
            logger.info(f"\nTest push completed successfully!")
            logger.info(f"Successful: {result.get('successful', 0)}")
            logger.info(f"Already pushed: {result.get('already_pushed', 0)}")
            logger.info(f"Failed: {result.get('total', 0) - result.get('successful', 0) - result.get('already_pushed', 0)}")
        else:
            logger.error(f"Test push failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()