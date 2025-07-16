#!/usr/bin/env python3
"""
Clean up duplicate Non-DSR circuits, keeping the ones with correct costs
"""

import psycopg2

def cleanup_duplicate_non_dsr():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    print("=== CLEANING UP DUPLICATE NON-DSR CIRCUITS ===\n")
    
    # Sites that have duplicates based on the verification output
    duplicate_sites = [
        ('CAN 16', 'Frontier Communications'),  # Keep "Frontier", remove "Frontier Communications"
        ('CAS 35', 'Frontier Communications'),  # Keep "Frontier", remove "Frontier Communications"
        ('CAS 40', 'Frontier Communications'),  # Keep "Frontier", remove "Frontier Communications"
        ('CAS 41', 'Frontier Communications'),  # Keep "Frontier", remove "Frontier Communications"
        ('MOO 04', 'Level 3'),                 # Keep "Brightspeed", remove "Level 3"
    ]
    
    try:
        conn.autocommit = False
        deleted_count = 0
        
        for site_name, old_provider in duplicate_sites:
            print(f"Processing {site_name} - removing '{old_provider}'...")
            
            # First, show what we're about to delete
            cursor.execute("""
                SELECT id, provider_name, details_ordered_service_speed, billing_monthly_cost
                FROM circuits
                WHERE site_name = %s AND provider_name = %s AND data_source = 'Non-DSR'
            """, (site_name, old_provider))
            
            old_records = cursor.fetchall()
            for record in old_records:
                cost_str = f"${record[3]:.2f}" if record[3] else "$0.00"
                print(f"  Deleting ID {record[0]}: {record[1]} - {record[2]} - {cost_str}")
            
            # Delete the old records
            cursor.execute("""
                DELETE FROM circuits
                WHERE site_name = %s AND provider_name = %s AND data_source = 'Non-DSR'
            """, (site_name, old_provider))
            
            deleted_count += cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} records")
        
        # Commit the deletions
        conn.commit()
        print(f"\n✅ Cleanup complete:")
        print(f"   Total records deleted: {deleted_count}")
        
        # Verify the cleanup
        print(f"\n=== VERIFICATION ===")
        cursor.execute("""
            SELECT 
                site_name, 
                provider_name, 
                details_ordered_service_speed, 
                billing_monthly_cost
            FROM circuits 
            WHERE site_name IN ('CAN 16', 'CAS 35', 'CAS 40', 'CAS 41', 'MOO 04') 
            AND data_source = 'Non-DSR'
            ORDER BY site_name, provider_name
        """)
        
        results = cursor.fetchall()
        print(f"{'Site':<8} {'Provider':<15} {'Speed':<15} {'Cost':<10}")
        print("-" * 50)
        for row in results:
            cost_str = f"${row[3]:.2f}" if row[3] else "$0.00"
            print(f"{row[0]:<8} {row[1]:<15} {row[2]:<15} {cost_str:<10}")
        
        # Double-check for any remaining duplicates
        print(f"\n=== DUPLICATE CHECK ===")
        cursor.execute("""
            SELECT 
                site_name,
                COUNT(*) as count
            FROM circuits
            WHERE data_source = 'Non-DSR'
            GROUP BY site_name
            HAVING COUNT(*) > 1
            ORDER BY site_name
        """)
        
        remaining_dups = cursor.fetchall()
        if remaining_dups:
            print("Sites still with multiple Non-DSR records:")
            for dup in remaining_dups:
                print(f"  {dup[0]}: {dup[1]} records")
        else:
            print("✓ No duplicate Non-DSR records found")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    cleanup_duplicate_non_dsr()