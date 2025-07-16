#!/usr/bin/env python3
"""
Fix last updated timestamp to show DSR data update time, not page refresh
"""

print("=== FIXING LAST UPDATED TO SHOW DSR DATA UPDATE TIME ===\n")

# First, let's check when the circuits table was last updated
import psycopg2
from datetime import datetime

try:
    conn = psycopg2.connect('host=localhost dbname=dsrcircuits user=dsruser password=dsrpass123')
    cur = conn.cursor()
    
    # Get the most recent last_updated timestamp from circuits table
    cur.execute("""
        SELECT MAX(last_updated) 
        FROM circuits 
        WHERE last_updated IS NOT NULL
    """)
    
    latest_dsr_update = cur.fetchone()[0]
    if latest_dsr_update:
        print(f"Latest DSR data update: {latest_dsr_update}")
    else:
        print("No last_updated timestamps found in circuits table")
        
    # Also check enriched_circuits table
    cur.execute("""
        SELECT MAX(last_updated) 
        FROM enriched_circuits 
        WHERE last_updated IS NOT NULL
    """)
    
    latest_enriched_update = cur.fetchone()[0]
    if latest_enriched_update:
        print(f"Latest enriched circuits update: {latest_enriched_update}")
        
    conn.close()
    
except Exception as e:
    print(f"Error checking database: {e}")

# Now update the blueprint to use DSR data timestamp instead of current time
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Replace the current timestamp logic with DSR data timestamp
old_timestamp = '''        # Get current timestamp for last updated display
        from datetime import datetime
        last_updated = datetime.now().strftime("%B %d, %Y at %I:%M %p")'''

new_timestamp = '''        # Get DSR data last updated timestamp
        from datetime import datetime
        try:
            # Get the most recent last_updated from circuits table
            latest_circuit_update = db.session.execute(
                db.text("SELECT MAX(last_updated) FROM circuits WHERE last_updated IS NOT NULL")
            ).scalar()
            
            if latest_circuit_update:
                last_updated = latest_circuit_update.strftime("%B %d, %Y at %I:%M %p")
            else:
                # Fallback to enriched_circuits if no circuits timestamp
                latest_enriched_update = db.session.execute(
                    db.text("SELECT MAX(last_updated) FROM enriched_circuits WHERE last_updated IS NOT NULL")
                ).scalar()
                
                if latest_enriched_update:
                    last_updated = latest_enriched_update.strftime("%B %d, %Y at %I:%M %p")
                else:
                    last_updated = "Unknown"
        except Exception as e:
            print(f"Error getting DSR timestamp: {e}")
            last_updated = "Data timestamp unavailable"'''

if old_timestamp in content:
    content = content.replace(old_timestamp, new_timestamp)
    print("✅ Updated timestamp logic to use DSR data update time")
    
    # Write the updated content
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(content)
else:
    print("❌ Could not find timestamp logic to replace")

print("\nLast updated timestamp now shows:")
print("- When DSR data was last pulled from tracking CSV")
print("- Falls back to enriched_circuits timestamp if needed")
print("- Shows 'Unknown' if no timestamps available")