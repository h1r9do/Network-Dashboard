#!/usr/bin/env python3
"""
Fix DSR timestamp to use correct column (updated_at)
"""

print("=== FIXING DSR TIMESTAMP TO USE UPDATED_AT COLUMN ===\n")

with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Replace the timestamp logic with correct column name
old_logic = '''        # Get DSR data last updated timestamp
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

new_logic = '''        # Get DSR data last updated timestamp from circuits table
        from datetime import datetime
        try:
            # Get the most recent updated_at from circuits table (when DSR data was last pulled)
            latest_dsr_update = db.session.execute(
                db.text("SELECT MAX(updated_at) FROM circuits WHERE updated_at IS NOT NULL")
            ).scalar()
            
            if latest_dsr_update:
                last_updated = latest_dsr_update.strftime("%B %d, %Y at %I:%M %p")
            else:
                # Fallback - check if we have any timestamp data
                last_updated = "DSR data timestamp unavailable"
        except Exception as e:
            print(f"Error getting DSR timestamp: {e}")
            last_updated = "Unable to determine DSR update time"'''

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    print("✅ Fixed timestamp logic to use circuits.updated_at column")
    
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(content)
else:
    print("❌ Could not find timestamp logic to replace")

print("\nLast updated will now show:")
print("- When DSR tracking CSV was last processed (circuits.updated_at)")
print("- Should show: July 09, 2025 at 03:12 PM")
print("- This reflects actual DSR data freshness, not page load time")