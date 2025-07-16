#!/usr/bin/env python3
"""
Fix all parsing issues in meraki_inventory table
This will re-parse device_notes and update the parsed label columns
"""

import sys
import re
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = 'postgresql://dsruser:dsrpass123@localhost/dsrcircuits'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def parse_device_notes(notes):
    """Parse device notes into structured data"""
    if not notes:
        return {
            'wan1_provider': '',
            'wan1_speed': '',
            'wan2_provider': '',
            'wan2_speed': ''
        }
    
    # Handle both literal \n and actual newlines
    if '\\n' in notes:
        # Notes have literal \n characters
        lines = [line.strip() for line in notes.split('\\n') if line.strip()]
    else:
        # Notes have actual newlines
        lines = [line.strip() for line in notes.split('\n') if line.strip()]
    
    parsed = {
        'wan1_provider': '',
        'wan1_speed': '',
        'wan2_provider': '',
        'wan2_speed': ''
    }
    
    # Find WAN 1 and WAN 2 sections
    wan1_idx = -1
    wan2_idx = -1
    
    for i, line in enumerate(lines):
        if line.upper() == 'WAN 1':
            wan1_idx = i
        elif line.upper() == 'WAN 2':
            wan2_idx = i
    
    # Parse WAN 1
    if wan1_idx >= 0:
        # Provider is the line after WAN 1
        if wan1_idx + 1 < len(lines):
            provider = lines[wan1_idx + 1]
            # Clean up any 'n' characters at start/end
            provider = provider.strip('n ').strip()
            parsed['wan1_provider'] = provider
            
        # Speed is two lines after WAN 1
        if wan1_idx + 2 < len(lines):
            speed = lines[wan1_idx + 2]
            # Don't include if it's WAN 2
            if speed.upper() != 'WAN 2':
                speed = speed.strip('n ').strip()
                parsed['wan1_speed'] = speed
    
    # Parse WAN 2
    if wan2_idx >= 0:
        # Provider is the line after WAN 2
        if wan2_idx + 1 < len(lines):
            provider = lines[wan2_idx + 1]
            # Clean up any 'n' characters at start/end
            provider = provider.strip('n ').strip()
            parsed['wan2_provider'] = provider
            
        # Speed is two lines after WAN 2
        if wan2_idx + 2 < len(lines):
            speed = lines[wan2_idx + 2]
            speed = speed.strip('n ').strip()
            parsed['wan2_speed'] = speed
    
    return parsed

def main():
    """Fix all parsing issues"""
    session = Session()
    
    try:
        # First, let's see what we're dealing with
        print("🔍 Analyzing parsing issues...")
        
        # Find all sites with device notes but empty or problematic parsed labels
        result = session.execute(text("""
            SELECT network_name, device_notes, 
                   wan1_provider_label, wan1_speed_label,
                   wan2_provider_label, wan2_speed_label
            FROM meraki_inventory
            WHERE device_notes IS NOT NULL
            AND device_notes != ''
            AND (
                wan1_provider_label IS NULL OR 
                wan1_provider_label = '' OR 
                wan1_provider_label LIKE '%n' OR
                wan1_provider_label LIKE 'n%' OR
                wan2_provider_label IS NULL OR 
                wan2_provider_label = '' OR
                wan2_provider_label LIKE '%n' OR
                wan2_provider_label LIKE 'n%'
            )
            ORDER BY network_name
        """))
        
        sites_to_fix = result.fetchall()
        print(f"📊 Found {len(sites_to_fix)} sites with parsing issues")
        
        # Show examples
        print("\n📋 Examples of issues found:")
        for i, (network, notes, w1p, w1s, w2p, w2s) in enumerate(sites_to_fix[:5]):
            print(f"\n{network}:")
            print(f"  Current WAN1: '{w1p}' / '{w1s}'")
            print(f"  Current WAN2: '{w2p}' / '{w2s}'")
            print(f"  Raw notes: {repr(notes[:50])}...")
        
        # Proceed automatically
        if len(sites_to_fix) == 0:
            print("✅ No sites need fixing!")
            return
        
        # Fix each site
        fixed_count = 0
        errors = []
        
        print("\n🔄 Fixing sites...")
        for network, notes, old_w1p, old_w1s, old_w2p, old_w2s in sites_to_fix:
            try:
                # Parse the notes
                parsed = parse_device_notes(notes)
                
                # Update the database
                session.execute(text("""
                    UPDATE meraki_inventory
                    SET wan1_provider_label = :w1p,
                        wan1_speed_label = :w1s,
                        wan2_provider_label = :w2p,
                        wan2_speed_label = :w2s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE network_name = :network
                """), {
                    'w1p': parsed['wan1_provider'],
                    'w1s': parsed['wan1_speed'],
                    'w2p': parsed['wan2_provider'],
                    'w2s': parsed['wan2_speed'],
                    'network': network
                })
                
                # Show progress
                if fixed_count % 50 == 0:
                    print(f"  ✅ Fixed {fixed_count} sites...")
                    session.commit()  # Commit in batches
                
                # Log significant changes
                if (old_w1p != parsed['wan1_provider'] or 
                    old_w2p != parsed['wan2_provider']):
                    print(f"  📝 {network}: WAN1: '{old_w1p}' → '{parsed['wan1_provider']}', WAN2: '{old_w2p}' → '{parsed['wan2_provider']}'")
                
                fixed_count += 1
                
            except Exception as e:
                errors.append(f"{network}: {str(e)}")
                print(f"  ❌ Error fixing {network}: {e}")
        
        # Final commit
        session.commit()
        
        print(f"\n✅ Successfully fixed {fixed_count} sites")
        if errors:
            print(f"❌ {len(errors)} sites had errors:")
            for err in errors[:10]:
                print(f"  - {err}")
        
        # Verify the fix
        print("\n🔍 Verifying fixes...")
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM meraki_inventory 
            WHERE device_notes IS NOT NULL
            AND device_notes LIKE '%WAN 1%'
            AND (wan1_provider_label IS NULL OR wan1_provider_label = '')
        """))
        remaining = result.fetchone()[0]
        print(f"📊 Sites still with empty WAN1 labels: {remaining}")
        
        # Check for 'n' character issues
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM meraki_inventory 
            WHERE (wan1_provider_label LIKE '%n' OR wan1_provider_label LIKE 'n%'
                   OR wan2_provider_label LIKE '%n' OR wan2_provider_label LIKE 'n%')
        """))
        n_issues = result.fetchone()[0]
        print(f"📊 Sites still with 'n' character issues: {n_issues}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()