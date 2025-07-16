#!/usr/bin/env python3
"""
Update database with Non-DSR circuits including correct costs, speeds, and providers
"""

import psycopg2
from datetime import datetime

def update_non_dsr_circuits():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    # Non-DSR circuits data from the user's list
    non_dsr_data = [
        ('AZK 01', 'Frontier', '1.0G x 1.0G', 1200.00),
        ('AZN 04', 'AT&T', '20.0M x 20.0M', 830.78),
        ('AZP 41', 'AT&T', '20.0M x 20.0M', 830.78),
        ('CAL 17', 'Frontier', '500.0M x 500.0M', 830.00),
        ('CAL 20', 'Frontier', '500.0M x 500.0M', 830.00),
        ('CAL 24', 'Frontier', '500.0M x 500.0M', 830.00),
        ('CAL 29', 'Frontier', '500.0M x 500.0M', 830.00),
        ('CAN 16', 'Frontier', '500.0M x 500.0M', 830.00),
        ('CAO 01', 'AT&T', '20.0M x 20.0M', 561.78),
        ('CAS 35', 'Frontier', '500.0M x 500.0M', 830.00),
        ('CAS 40', 'Frontier', '500.0M x 500.0M', 1000.00),
        ('CAS 41', 'Frontier', '500.0M x 500.0M', 830.00),
        ('CAS 46', 'AT&T', '20.0M x 20.0M', 561.78),
        ('COD 41', 'Lumen', '300.0M x 300.0M', 1145.00),
        ('GAA 43', 'AT&T', '100.0M x 100.0M', 830.78),
        ('MOO 04', 'Brightspeed', '300.0M x 300.0M', 1009.00),
        ('MOS 02', 'AT&T', '20.0M x 20.0M', 433.00),  # This is WAN 2
        ('TXA 12', 'Frontier', '20.0M x 20.0M', 400.00),
    ]
    
    print("=== UPDATING NON-DSR CIRCUITS ===\n")
    
    try:
        # Start transaction
        conn.autocommit = False
        
        updated_count = 0
        inserted_count = 0
        
        for site_name, provider, speed, cost in non_dsr_data:
            print(f"Processing {site_name} - {provider}...")
            
            # First, check if a Non-DSR record already exists
            cursor.execute("""
                SELECT id FROM circuits 
                WHERE site_name = %s AND provider_name = %s AND data_source = 'Non-DSR'
            """, (site_name, provider))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE circuits SET
                        details_ordered_service_speed = %s,
                        billing_monthly_cost = %s,
                        circuit_purpose = 'Primary',
                        status = 'Enabled',
                        updated_at = NOW()
                    WHERE id = %s
                """, (speed, cost, existing[0]))
                updated_count += 1
                print(f"  ✓ Updated existing record ID {existing[0]}")
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO circuits (
                        site_name, 
                        provider_name, 
                        details_ordered_service_speed,
                        billing_monthly_cost,
                        circuit_purpose,
                        status,
                        data_source,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                """, (site_name, provider, speed, cost, 'Primary', 'Enabled', 'Non-DSR'))
                inserted_count += 1
                print(f"  ✓ Inserted new record")
        
        # Commit all changes
        conn.commit()
        print(f"\n✅ SUCCESS:")
        print(f"   Records updated: {updated_count}")
        print(f"   Records inserted: {inserted_count}")
        print(f"   Total processed: {len(non_dsr_data)}")
        
        # Verify the updates
        print(f"\n=== VERIFICATION ===")
        cursor.execute("""
            SELECT 
                site_name, 
                provider_name, 
                details_ordered_service_speed, 
                billing_monthly_cost
            FROM circuits 
            WHERE site_name = ANY(%s) AND data_source = 'Non-DSR'
            ORDER BY site_name, provider_name
        """, ([item[0] for item in non_dsr_data],))
        
        results = cursor.fetchall()
        print(f"{'Site':<8} {'Provider':<15} {'Speed':<15} {'Cost':<10}")
        print("-" * 50)
        for row in results:
            cost_str = f"${row[3]:.2f}" if row[3] else "$0.00"
            print(f"{row[0]:<8} {row[1]:<15} {row[2]:<15} {cost_str:<10}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_non_dsr_circuits()