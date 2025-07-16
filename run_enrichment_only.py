#!/usr/bin/env python3
"""
Run only the enrichment part of the combined script
This enriches the imported Meraki live data with DSR tracking data
"""

import os
import sys
sys.path.append('/usr/local/bin/Main')

from nightly_meraki_enriched_db import enrich_with_tracking_data, create_tables, Session

def main():
    session = Session()
    
    try:
        # Ensure tables exist
        create_tables(session)
        
        # Run enrichment
        enriched_count = enrich_with_tracking_data(session)
        
        print(f"Successfully enriched {enriched_count} networks")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()