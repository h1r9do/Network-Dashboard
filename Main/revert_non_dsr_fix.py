#!/usr/bin/env python3
"""
Revert the Non-DSR circuits back to their original state
"""

import psycopg2

def revert_non_dsr_circuits():
    """Change circuits back from csv_import to Non-DSR"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Reverting circuits back to Non-DSR...")
    print("="*80)
    
    # First identify which circuits need to be reverted
    # These would be the ones that were Non-DSR before and don't have record numbers
    
    # List of sites that had Non-DSR circuits
    non_dsr_sites = [
        'AZK 01', 'AZN 04', 'AZP 41', 'AZP 47', 'CAL 17', 'CAL 20', 'CAL 24', 'CAL 29',
        'CAN_00', 'CAN 16', 'CAO 01', 'CAS_00', 'CAS 35', 'CAS 40', 'CAS 41', 'CAS 42',
        'CAS 46', 'COD 01', 'COD 03', 'COD 08', 'COD 09', 'COD 13', 'COD 41', 'Cog 02',
        'GAA 43', 'GAACALLCNTR', 'GAA W00', 'ILC_00', 'ILC 11', 'ILC 12', 'ILR 01',
        'INI_00', 'INW 02', 'KSK_00', 'MIF 05', 'MNM 02', 'MNM 03', 'MNM 09', 'MNM 11',
        'MNM 24', 'MNM 29', 'MOO 01', 'MOO 04', 'MOS 02', 'NCC_00', 'NMA_00', 'NMA 10',
        'ORP 01', 'ORP 05', 'TNN_00', 'TXA 12', 'TXH_00', 'TXH 25', 'TXH 28', 'TXH 44',
        'TXH 64', 'TXH 70', 'TXH 86', 'TXHT00', 'UTS 02', 'UTS 15', 'UTS 17', 'UTS 19',
        'UTS W01', 'UTS W02', 'VAF 01 - appliance', 'VAR 01', 'WAE 01', 'WAE 02',
        'WAS 09', 'WAS 11', 'WAS 14', 'WAS 23', 'WAS W00', 'WDTD 01'
    ]
    
    # For CAL 24 specifically, we know the Frontier $830 circuit was Non-DSR
    print("Reverting CAL 24 Frontier circuit...")
    cur.execute("""
        UPDATE circuits 
        SET data_source = 'Non-DSR',
            updated_at = NOW()
        WHERE site_name = 'CAL 24' 
        AND provider_name = 'Frontier'
        AND billing_monthly_cost = 830.00
    """)
    print(f"  Updated {cur.rowcount} CAL 24 circuit")
    
    # Revert other circuits that likely were Non-DSR
    # These are typically $0 cost circuits or specific providers
    print("\nReverting other Non-DSR circuits...")
    cur.execute("""
        UPDATE circuits 
        SET data_source = 'Non-DSR',
            updated_at = NOW()
        WHERE status = 'Enabled'
        AND site_name = ANY(%s)
        AND (
            billing_monthly_cost = 0 
            OR billing_monthly_cost IS NULL
            OR (site_name = 'AZK 01' AND provider_name = 'Frontier' AND billing_monthly_cost = 1250.00)
            OR (site_name = 'AZN 04' AND provider_name = 'AT&T' AND billing_monthly_cost = 830.78)
            OR (site_name = 'AZP 41' AND provider_name = 'AT&T' AND billing_monthly_cost = 830.78)
            OR (site_name = 'CAL 17' AND provider_name = 'Frontier' AND billing_monthly_cost = 830.00)
            OR (site_name = 'CAL 20' AND provider_name = 'Frontier' AND billing_monthly_cost = 830.00)
            OR (site_name = 'CAL 29' AND provider_name = 'Frontier' AND billing_monthly_cost = 830.00)
            OR (site_name = 'CAN 16' AND provider_name = 'Frontier' AND billing_monthly_cost = 830.00)
            OR (site_name = 'CAO 01' AND provider_name = 'AT&T' AND billing_monthly_cost = 561.78)
            OR (site_name = 'CAS 35' AND provider_name = 'Frontier' AND billing_monthly_cost = 830.00)
            OR (site_name = 'CAS 40' AND provider_name = 'Frontier' AND billing_monthly_cost = 1000.00)
            OR (site_name = 'CAS 41' AND provider_name = 'Frontier' AND billing_monthly_cost = 830.00)
            OR (site_name = 'CAS 46' AND provider_name = 'AT&T' AND billing_monthly_cost = 561.78)
            OR (site_name = 'COD 41' AND provider_name = 'Lumen' AND billing_monthly_cost = 1145.00)
            OR (site_name = 'GAA 43' AND provider_name = 'AT&T' AND billing_monthly_cost = 830.78)
            OR (site_name = 'MOO 04' AND provider_name = 'Brightspeed' AND billing_monthly_cost = 1009.00)
            OR (site_name = 'MOS 02' AND provider_name = 'AT&T' AND billing_monthly_cost = 433.00)
            OR (site_name = 'TXA 12' AND provider_name = 'Frontier' AND billing_monthly_cost = 400.00)
        )
    """, (non_dsr_sites,))
    
    rows_updated = cur.rowcount
    print(f"  Updated {rows_updated} circuits back to Non-DSR")
    
    # Verify the revert
    cur.execute("""
        SELECT COUNT(*) 
        FROM circuits 
        WHERE data_source = 'Non-DSR' AND status = 'Enabled'
    """)
    count = cur.fetchone()[0]
    print(f"\nTotal Non-DSR circuits after revert: {count}")
    
    # Check CAL 24 specifically
    print("\nCAL 24 circuits after revert:")
    cur.execute("""
        SELECT provider_name, billing_monthly_cost, data_source
        FROM circuits 
        WHERE site_name = 'CAL 24' AND status = 'Enabled'
        ORDER BY provider_name
    """)
    
    for row in cur.fetchall():
        print(f"  {row[0]} | ${row[1]} | {row[2]}")
    
    # Commit the changes
    conn.commit()
    print("\n✅ Revert completed and committed to database")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    revert_non_dsr_circuits()