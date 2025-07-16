#!/usr/bin/env python3
"""
Push all confirmed but not pushed circuits to Meraki in batches
Processes sites in batches of 30 to avoid API rate limits
"""

import os
import sys
import time
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import the push_to_meraki function from the existing module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from confirm_meraki_notes_db_fixed import push_to_meraki

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/push_all_confirmed_circuits.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Database configuration
DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits')

# Create database session
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# Batch configuration
BATCH_SIZE = 30
BATCH_DELAY = 10  # seconds between batches

def get_unpushed_confirmed_circuits():
    """Get all circuits that are confirmed but not yet pushed to Meraki"""
    session = Session()
    try:
        result = session.execute(text("""
            SELECT DISTINCT network_name
            FROM enriched_circuits
            WHERE (wan1_confirmed = TRUE OR wan2_confirmed = TRUE)
                AND (pushed_to_meraki IS NULL OR pushed_to_meraki = FALSE)
            ORDER BY network_name
        """))
        
        sites = [row[0] for row in result.fetchall()]
        logger.info(f"Found {len(sites)} confirmed circuits not yet pushed to Meraki")
        
        return sites
        
    except Exception as e:
        logger.error(f"Error fetching unpushed circuits: {e}")
        return []
    finally:
        session.close()

def get_circuit_details(sites):
    """Get circuit details for logging purposes"""
    session = Session()
    try:
        placeholders = ','.join([f':site{i}' for i in range(len(sites))])
        params = {f'site{i}': site for i, site in enumerate(sites)}
        
        result = session.execute(text(f"""
            SELECT 
                network_name,
                wan1_provider,
                wan1_speed,
                wan1_confirmed,
                wan2_provider,
                wan2_speed,
                wan2_confirmed
            FROM enriched_circuits
            WHERE network_name IN ({placeholders})
        """), params)
        
        details = {}
        for row in result.fetchall():
            details[row[0]] = {
                'wan1': f"{row[1]} {row[2]}" if row[3] else "Not confirmed",
                'wan2': f"{row[4]} {row[5]}" if row[6] else "Not confirmed"
            }
        
        return details
        
    except Exception as e:
        logger.error(f"Error fetching circuit details: {e}")
        return {}
    finally:
        session.close()

def process_batch(batch_sites, batch_number, total_batches):
    """Process a batch of sites"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing batch {batch_number}/{total_batches} ({len(batch_sites)} sites)")
    logger.info(f"{'='*60}")
    
    # Get circuit details for logging
    details = get_circuit_details(batch_sites)
    
    # Log sites in this batch
    for site in batch_sites:
        site_details = details.get(site, {})
        logger.info(f"  {site}: WAN1={site_details.get('wan1', 'Unknown')}, WAN2={site_details.get('wan2', 'Unknown')}")
    
    # Call push_to_meraki function
    logger.info(f"\nPushing batch {batch_number} to Meraki...")
    start_time = time.time()
    
    try:
        result = push_to_meraki(batch_sites)
        elapsed_time = time.time() - start_time
        
        if result.get('success'):
            successful = result.get('successful', 0)
            already_pushed = result.get('already_pushed', 0)
            failed = len(batch_sites) - successful - already_pushed
            
            logger.info(f"\nBatch {batch_number} completed in {elapsed_time:.2f} seconds:")
            logger.info(f"  - Successful: {successful}")
            logger.info(f"  - Already pushed: {already_pushed}")
            logger.info(f"  - Failed: {failed}")
            
            # Log individual results
            if 'results' in result:
                for site_result in result['results']:
                    site = site_result.get('site')
                    if site_result.get('success'):
                        logger.info(f"  ✓ {site}: Successfully pushed")
                    elif site_result.get('already_pushed'):
                        logger.info(f"  ⚠ {site}: Already pushed")
                    else:
                        logger.error(f"  ✗ {site}: {site_result.get('error', 'Unknown error')}")
            
            return {
                'successful': successful,
                'already_pushed': already_pushed,
                'failed': failed,
                'elapsed_time': elapsed_time
            }
        else:
            logger.error(f"Batch {batch_number} failed: {result.get('error', 'Unknown error')}")
            return {
                'successful': 0,
                'already_pushed': 0,
                'failed': len(batch_sites),
                'elapsed_time': elapsed_time
            }
            
    except Exception as e:
        logger.error(f"Exception processing batch {batch_number}: {e}")
        return {
            'successful': 0,
            'already_pushed': 0,
            'failed': len(batch_sites),
            'elapsed_time': time.time() - start_time
        }

def main():
    """Main function to process all confirmed circuits"""
    logger.info("Starting push of all confirmed circuits to Meraki")
    logger.info(f"Batch size: {BATCH_SIZE} sites")
    logger.info(f"Delay between batches: {BATCH_DELAY} seconds")
    
    # Get all unpushed confirmed circuits
    all_sites = get_unpushed_confirmed_circuits()
    
    if not all_sites:
        logger.info("No unpushed confirmed circuits found. Exiting.")
        return
    
    # Calculate number of batches
    total_batches = (len(all_sites) + BATCH_SIZE - 1) // BATCH_SIZE
    
    logger.info(f"\nTotal sites to process: {len(all_sites)}")
    logger.info(f"Total batches: {total_batches}")
    
    # Process statistics
    total_successful = 0
    total_already_pushed = 0
    total_failed = 0
    total_elapsed_time = 0
    
    # Process each batch
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(all_sites))
        batch_sites = all_sites[start_idx:end_idx]
        
        # Process the batch
        batch_result = process_batch(batch_sites, batch_num + 1, total_batches)
        
        # Update totals
        total_successful += batch_result['successful']
        total_already_pushed += batch_result['already_pushed']
        total_failed += batch_result['failed']
        total_elapsed_time += batch_result['elapsed_time']
        
        # Progress update
        processed = end_idx
        progress_pct = (processed / len(all_sites)) * 100
        logger.info(f"\nOverall progress: {processed}/{len(all_sites)} sites ({progress_pct:.1f}%)")
        logger.info(f"Running totals - Successful: {total_successful}, Already pushed: {total_already_pushed}, Failed: {total_failed}")
        
        # Wait between batches (except for the last batch)
        if batch_num < total_batches - 1:
            logger.info(f"\nWaiting {BATCH_DELAY} seconds before next batch...")
            time.sleep(BATCH_DELAY)
    
    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total sites processed: {len(all_sites)}")
    logger.info(f"Total successful pushes: {total_successful}")
    logger.info(f"Total already pushed: {total_already_pushed}")
    logger.info(f"Total failed: {total_failed}")
    logger.info(f"Total processing time: {total_elapsed_time:.2f} seconds")
    logger.info(f"Average time per batch: {total_elapsed_time/total_batches:.2f} seconds")
    
    # Check for any remaining unpushed circuits
    remaining = get_unpushed_confirmed_circuits()
    if remaining:
        logger.warning(f"\nWARNING: {len(remaining)} circuits still unpushed after processing")
        logger.warning("These sites may have had errors during processing:")
        for site in remaining[:10]:  # Show first 10
            logger.warning(f"  - {site}")
        if len(remaining) > 10:
            logger.warning(f"  ... and {len(remaining) - 10} more")
    else:
        logger.info("\n✓ All confirmed circuits have been successfully pushed to Meraki!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nScript interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)