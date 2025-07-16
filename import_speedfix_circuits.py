#!/usr/bin/env python3
"""
Import circuits from speedfix.csv:
1. Create new records in circuits table (like DSR circuits)
2. Fix speeds in enriched_circuits table
"""

import psycopg2
import pandas as pd
from datetime import datetime
import sys

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def import_speedfix_circuits():
    """Import circuits and fix speeds"""
    
    print("=== IMPORTING SPEED FIX CIRCUITS ===\n")
    
    # Read the speedfix CSV
    df = pd.read_csv('/tmp/speedfix.csv')
    print(f"Loaded {len(df)} circuits from speedfix.csv")
    
    # Filter only circuits that need fixing
    circuits_to_fix = df[df['needs_speed_fix'] == True]
    print(f"Found {len(circuits_to_fix)} circuits needing speed fixes\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Track results
    circuits_created = 0
    speeds_fixed = 0
    errors = []
    
    try:
        # Start transaction
        conn.autocommit = False
        
        print("STEP 1: Creating circuits in circuits table...\n")
        
        for idx, row in circuits_to_fix.iterrows():
            try:
                # Check if circuit already exists
                cursor.execute("""
                    SELECT id FROM circuits 
                    WHERE site_name = %s 
                    AND circuit_purpose = %s 
                    AND provider_name = %s
                    AND status = 'Enabled'
                """, (row['site_name'], row['circuit_purpose'], row['provider_name']))
                
                existing = cursor.fetchone()
                
                if not existing:
                    # Insert new circuit (like a DSR circuit but marked as Non-DSR)
                    cursor.execute("""
                        INSERT INTO circuits (
                            site_name,
                            circuit_purpose,
                            provider_name,
                            details_ordered_service_speed,
                            status,
                            billing_monthly_cost,
                            data_source,
                            created_at,
                            updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                        )
                        RETURNING id
                    """, (
                        row['site_name'],
                        row['circuit_purpose'],
                        row['provider_name'],
                        row['speed_corrected'],  # Use corrected speed
                        'Enabled',
                        0.00,  # Default cost for Non-DSR
                        'Non-DSR'  # Mark as Non-DSR circuit
                    ))
                    
                    circuit_id = cursor.fetchone()[0]
                    circuits_created += 1
                    print(f"✓ Created circuit ID {circuit_id}: {row['site_name']} - {row['provider_name']} ({row['circuit_purpose']})")
                else:
                    print(f"- Circuit already exists: {row['site_name']} - {row['provider_name']} ({row['circuit_purpose']})")
                    
            except Exception as e:
                error_msg = f"Error creating circuit for {row['site_name']}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
        
        print(f"\nCreated {circuits_created} new circuits in circuits table")
        
        # Step 2: Fix speeds in enriched_circuits
        print("\nSTEP 2: Fixing speeds in enriched_circuits table...\n")
        
        for idx, row in circuits_to_fix.iterrows():
            try:
                # Determine which WAN to update based on circuit_purpose
                if row['circuit_purpose'] == 'Primary':
                    wan_field = 'wan1_speed'
                else:
                    wan_field = 'wan2_speed'
                
                # Update enriched_circuits
                cursor.execute(f"""
                    UPDATE enriched_circuits
                    SET {wan_field} = %s,
                        last_updated = NOW()
                    WHERE (network_name = %s OR network_name = %s)
                    AND {wan_field} = %s
                """, (
                    row['speed_corrected'],
                    row['site_name'],
                    row['site_name'].replace(' ', '_'),
                    row['speed_original']
                ))
                
                if cursor.rowcount > 0:
                    speeds_fixed += 1
                    print(f"✓ Fixed speed for {row['site_name']} {row['wan_interface']}: '{row['speed_original']}' → '{row['speed_corrected']}'")
                else:
                    print(f"- No speed update needed for {row['site_name']} {row['wan_interface']}")
                    
            except Exception as e:
                error_msg = f"Error fixing speed for {row['site_name']}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
        
        print(f"\nFixed {speeds_fixed} speeds in enriched_circuits table")
        
        # Commit transaction
        conn.commit()
        print("\n✅ Transaction committed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Transaction rolled back due to error: {str(e)}")
        return False
    
    finally:
        # Show summary
        print("\n=== SUMMARY ===")
        print(f"Circuits created in circuits table: {circuits_created}")
        print(f"Speeds fixed in enriched_circuits: {speeds_fixed}")
        
        if errors:
            print(f"\nErrors encountered ({len(errors)}):")
            for error in errors[:10]:
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        
        # Verify the changes
        print("\n=== VERIFICATION ===")
        
        # Check a sample
        cursor.execute("""
            SELECT 
                c.id,
                c.site_name,
                c.circuit_purpose,
                c.provider_name,
                c.details_ordered_service_speed,
                c.data_source,
                ec.wan1_speed,
                ec.wan2_speed
            FROM circuits c
            JOIN enriched_circuits ec ON (
                ec.network_name = c.site_name OR 
                ec.network_name = REPLACE(c.site_name, ' ', '_')
            )
            WHERE c.data_source = 'Non-DSR'
            AND c.created_at >= NOW() - INTERVAL '1 hour'
            LIMIT 5
        """)
        
        print("\nSample of newly created circuits:")
        print("ID   | Site      | Purpose   | Provider            | Speed              | Enriched WAN1     | Enriched WAN2")
        print("-" * 110)
        
        for row in cursor.fetchall():
            print(f"{row[0]:<4} | {row[1]:<9} | {row[2]:<9} | {row[3]:<18} | {row[4]:<18} | {row[6]:<17} | {row[7]}")
        
        cursor.close()
        conn.close()
        
        return True

if __name__ == "__main__":
    if import_speedfix_circuits():
        print("\n✅ Import completed successfully!")
    else:
        print("\n❌ Import failed!")
        sys.exit(1)