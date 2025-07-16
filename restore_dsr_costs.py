#!/usr/bin/env python3
"""
Restore DSR cost data for sites that were incorrectly updated with $0.00
This script reads cost data from the circuits table (DSR source) and updates
the enriched_circuits table to restore the correct costs.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# List of affected sites from the logs
AFFECTED_SITES = [
    'ALB 01',
    'ALB 03', 
    'ALM 02',
    'ALM 03',
    'ALN 01',
    'AZP 19',
    'AZP 23',
    'AZP 47',
    'AZT 06',
    'GAACALLCNTR',
    'NVL 24',
    'WDTD 01'
]

# Database configuration
DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def normalize_cost(cost):
    """Normalize cost to currency format"""
    if not cost or cost == 'nan' or cost is None:
        return '$0.00'
    
    try:
        cost_float = float(cost)
        return f'${cost_float:.2f}'
    except:
        return '$0.00'

def main():
    print(f"\n{'='*80}")
    print(f"DSR Cost Data Restoration - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    session = get_db_session()
    
    try:
        restored_count = 0
        
        for site_name in AFFECTED_SITES:
            print(f"\nProcessing site: {site_name}")
            
            # Get cost data from circuits table (DSR source)
            result = session.execute(text("""
                SELECT circuit_purpose, billing_monthly_cost
                FROM circuits
                WHERE LOWER(site_name) = LOWER(:site_name) 
                AND status = 'Enabled'
                ORDER BY circuit_purpose
            """), {'site_name': site_name})
            
            dsr_costs = {}
            for row in result:
                purpose = row[0]
                cost = row[1]
                if purpose:
                    purpose_lower = purpose.lower()
                    if 'primary' in purpose_lower:
                        dsr_costs['wan1'] = normalize_cost(cost)
                    elif 'secondary' in purpose_lower or 'backup' in purpose_lower:
                        dsr_costs['wan2'] = normalize_cost(cost)
            
            if not dsr_costs:
                print(f"  ⚠️  No DSR cost data found for {site_name}")
                continue
            
            # Get current enriched data
            result = session.execute(text("""
                SELECT wan1_monthly_cost, wan2_monthly_cost
                FROM enriched_circuits
                WHERE LOWER(network_name) = LOWER(:site_name)
            """), {'site_name': site_name})
            
            current = result.fetchone()
            if not current:
                print(f"  ⚠️  No enriched circuit record found for {site_name}")
                continue
            
            current_wan1_cost = current[0] or '$0.00'
            current_wan2_cost = current[1] or '$0.00'
            
            # Update if costs are different
            update_needed = False
            update_parts = []
            
            if 'wan1' in dsr_costs and current_wan1_cost != dsr_costs['wan1']:
                update_parts.append(f"wan1_monthly_cost = :wan1_cost")
                update_needed = True
                print(f"  WAN1: {current_wan1_cost} → {dsr_costs['wan1']}")
            
            if 'wan2' in dsr_costs and current_wan2_cost != dsr_costs['wan2']:
                update_parts.append(f"wan2_monthly_cost = :wan2_cost")
                update_needed = True
                print(f"  WAN2: {current_wan2_cost} → {dsr_costs['wan2']}")
            
            if update_needed:
                # Build update query
                update_sql = f"""
                    UPDATE enriched_circuits
                    SET {', '.join(update_parts)},
                        last_updated = CURRENT_TIMESTAMP
                    WHERE LOWER(network_name) = LOWER(:site_name)
                """
                
                params = {'site_name': site_name}
                if 'wan1' in dsr_costs:
                    params['wan1_cost'] = dsr_costs['wan1']
                if 'wan2' in dsr_costs:
                    params['wan2_cost'] = dsr_costs['wan2']
                
                session.execute(text(update_sql), params)
                restored_count += 1
                print(f"  ✅ Cost data restored from DSR")
            else:
                print(f"  ✓ Costs already correct")
        
        # Commit all changes
        session.commit()
        
        print(f"\n{'='*80}")
        print(f"Summary: Restored cost data for {restored_count} sites")
        print(f"{'='*80}\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)