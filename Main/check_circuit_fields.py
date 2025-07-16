#!/usr/bin/env python3
"""
Check all fields in the circuits table for CAL 24 to identify possible DSR/non-DSR indicators
"""

import psycopg2

def check_circuit_fields():
    """Check all fields for CAL 24 circuits"""
    conn = psycopg2.connect("postgresql://dsruser:dsrpass123@localhost:5432/dsrcircuits")
    cur = conn.cursor()
    
    print("Checking all fields for CAL 24 circuits...")
    print("="*80)
    
    # First get column names
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'circuits' 
        ORDER BY ordinal_position
    """)
    columns = [row[0] for row in cur.fetchall()]
    
    # Query all data for CAL 24
    cur.execute("""
        SELECT * FROM circuits 
        WHERE site_name = 'CAL 24' AND status = 'Enabled'
        ORDER BY circuit_purpose
    """)
    
    circuits = cur.fetchall()
    
    print(f"\nFound {len(circuits)} enabled circuits for CAL 24")
    print(f"Columns in circuits table: {len(columns)}")
    print("-"*80)
    
    # Display each circuit with all fields
    for i, circuit in enumerate(circuits):
        print(f"\n📍 Circuit {i+1}:")
        for j, value in enumerate(circuit):
            if value is not None and value != '':
                print(f"   {columns[j]}: {value}")
    
    # Check for DSR-related fields
    print("\n\nLooking for DSR/non-DSR indicators in field names...")
    print("-"*80)
    
    dsr_related_columns = []
    for col in columns:
        if any(term in col.lower() for term in ['dsr', 'discount', 'tire', 'corporate', 'store', 'provided']):
            dsr_related_columns.append(col)
    
    if dsr_related_columns:
        print(f"Found potential DSR-related columns: {', '.join(dsr_related_columns)}")
        
        # Check values in these columns for CAL 24
        for col in dsr_related_columns:
            cur.execute(f"""
                SELECT DISTINCT {col} 
                FROM circuits 
                WHERE site_name = 'CAL 24' AND {col} IS NOT NULL
            """)
            values = cur.fetchall()
            if values:
                print(f"\n{col} values for CAL 24: {[v[0] for v in values]}")
    else:
        print("No obvious DSR-related column names found")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_circuit_fields()