#!/usr/bin/env python3
"""
Check the current status of confirmed circuits and their push status
Provides a summary before running the push_all_confirmed_circuits.py script
"""

import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits')

# Create database session
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def get_circuit_statistics():
    """Get comprehensive statistics about circuit confirmation and push status"""
    session = Session()
    try:
        # Total enriched circuits
        result = session.execute(text("SELECT COUNT(*) FROM enriched_circuits"))
        total_enriched = result.scalar()
        
        # Confirmed circuits (at least one WAN confirmed)
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE wan1_confirmed = TRUE OR wan2_confirmed = TRUE
        """))
        total_confirmed = result.scalar()
        
        # Both WANs confirmed
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE wan1_confirmed = TRUE AND wan2_confirmed = TRUE
        """))
        both_confirmed = result.scalar()
        
        # Only WAN1 confirmed
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE wan1_confirmed = TRUE AND (wan2_confirmed = FALSE OR wan2_confirmed IS NULL)
        """))
        wan1_only = result.scalar()
        
        # Only WAN2 confirmed
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE wan2_confirmed = TRUE AND (wan1_confirmed = FALSE OR wan1_confirmed IS NULL)
        """))
        wan2_only = result.scalar()
        
        # Already pushed to Meraki
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE pushed_to_meraki = TRUE
        """))
        already_pushed = result.scalar()
        
        # Confirmed but not pushed
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE (wan1_confirmed = TRUE OR wan2_confirmed = TRUE)
                AND (pushed_to_meraki IS NULL OR pushed_to_meraki = FALSE)
        """))
        ready_to_push = result.scalar()
        
        # Get recent push activity
        result = session.execute(text("""
            SELECT 
                DATE(pushed_date) as push_date,
                COUNT(*) as count
            FROM enriched_circuits
            WHERE pushed_to_meraki = TRUE
                AND pushed_date IS NOT NULL
            GROUP BY DATE(pushed_date)
            ORDER BY push_date DESC
            LIMIT 7
        """))
        recent_pushes = result.fetchall()
        
        return {
            'total_enriched': total_enriched,
            'total_confirmed': total_confirmed,
            'both_confirmed': both_confirmed,
            'wan1_only': wan1_only,
            'wan2_only': wan2_only,
            'already_pushed': already_pushed,
            'ready_to_push': ready_to_push,
            'recent_pushes': recent_pushes
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return None
    finally:
        session.close()

def get_sample_circuits(limit=10):
    """Get a sample of circuits ready to be pushed"""
    session = Session()
    try:
        result = session.execute(text("""
            SELECT 
                network_name,
                wan1_provider,
                wan1_speed,
                wan1_confirmed,
                wan2_provider,
                wan2_speed,
                wan2_confirmed
            FROM enriched_circuits
            WHERE (wan1_confirmed = TRUE OR wan2_confirmed = TRUE)
                AND (pushed_to_meraki IS NULL OR pushed_to_meraki = FALSE)
            ORDER BY network_name
            LIMIT :limit
        """), {'limit': limit})
        
        return result.fetchall()
        
    except Exception as e:
        logger.error(f"Error getting sample circuits: {e}")
        return []
    finally:
        session.close()

def main():
    """Main function to display circuit push status"""
    logger.info("=" * 70)
    logger.info("CIRCUIT PUSH STATUS REPORT")
    logger.info("=" * 70)
    logger.info(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    # Get statistics
    stats = get_circuit_statistics()
    
    if not stats:
        logger.error("Failed to retrieve statistics")
        return
    
    # Display overall statistics
    logger.info("OVERALL STATISTICS:")
    logger.info("-" * 30)
    logger.info(f"Total enriched circuits:     {stats['total_enriched']:,}")
    logger.info(f"Total confirmed circuits:    {stats['total_confirmed']:,}")
    logger.info(f"  - Both WANs confirmed:     {stats['both_confirmed']:,}")
    logger.info(f"  - Only WAN1 confirmed:     {stats['wan1_only']:,}")
    logger.info(f"  - Only WAN2 confirmed:     {stats['wan2_only']:,}")
    logger.info("")
    
    logger.info("PUSH STATUS:")
    logger.info("-" * 30)
    logger.info(f"Already pushed to Meraki:    {stats['already_pushed']:,}")
    logger.info(f"Ready to push:               {stats['ready_to_push']:,}")
    logger.info("")
    
    # Display recent push activity
    if stats['recent_pushes']:
        logger.info("RECENT PUSH ACTIVITY:")
        logger.info("-" * 30)
        for push_date, count in stats['recent_pushes']:
            logger.info(f"{push_date}: {count:,} circuits pushed")
        logger.info("")
    
    # Show sample of circuits ready to push
    if stats['ready_to_push'] > 0:
        logger.info("SAMPLE CIRCUITS READY TO PUSH:")
        logger.info("-" * 70)
        logger.info(f"{'Site Name':<30} {'WAN1':<20} {'WAN2':<20}")
        logger.info("-" * 70)
        
        samples = get_sample_circuits(10)
        for site, w1_prov, w1_speed, w1_conf, w2_prov, w2_speed, w2_conf in samples:
            wan1_info = f"{w1_prov} {w1_speed}" if w1_conf else "Not confirmed"
            wan2_info = f"{w2_prov} {w2_speed}" if w2_conf else "Not confirmed"
            logger.info(f"{site:<30} {wan1_info:<20} {wan2_info:<20}")
        
        if stats['ready_to_push'] > 10:
            logger.info(f"... and {stats['ready_to_push'] - 10} more circuits")
        logger.info("")
        
        # Calculate batches
        batch_size = 30
        total_batches = (stats['ready_to_push'] + batch_size - 1) // batch_size
        estimated_time = total_batches * 15  # ~15 seconds per batch
        
        logger.info("PUSH ESTIMATION:")
        logger.info("-" * 30)
        logger.info(f"Circuits to push:            {stats['ready_to_push']:,}")
        logger.info(f"Batch size:                  {batch_size}")
        logger.info(f"Total batches:               {total_batches}")
        logger.info(f"Estimated time:              ~{estimated_time // 60} minutes {estimated_time % 60} seconds")
        logger.info("")
        logger.info("To push all confirmed circuits, run:")
        logger.info("  python /usr/local/bin/Main/push_all_confirmed_circuits.py")
    else:
        logger.info("✓ No circuits pending push - all confirmed circuits have been pushed to Meraki!")
    
    logger.info("")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()