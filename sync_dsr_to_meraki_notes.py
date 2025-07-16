#!/usr/bin/env python3
"""
Sync DSR circuit data to Meraki notes for sites where DSR has enabled circuits
but Meraki notes are missing that information
"""

import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = 'postgresql://dsruser:dsrpass123@localhost/dsrcircuits'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def main():
    """Sync DSR data to Meraki notes"""
    session = Session()
    
    try:
        print("🔍 Finding sites with DSR circuits not reflected in Meraki notes...")
        
        # Find mismatches
        result = session.execute(text('''
            WITH circuit_summary AS (
                SELECT 
                    site_name,
                    MAX(CASE WHEN circuit_purpose = 'Primary' AND status = 'Enabled' 
                             THEN provider_name END) as primary_provider,
                    MAX(CASE WHEN circuit_purpose = 'Primary' AND status = 'Enabled' 
                             THEN details_ordered_service_speed END) as primary_speed,
                    MAX(CASE WHEN circuit_purpose = 'Secondary' AND status = 'Enabled' 
                             THEN provider_name END) as secondary_provider,
                    MAX(CASE WHEN circuit_purpose = 'Secondary' AND status = 'Enabled' 
                             THEN details_ordered_service_speed END) as secondary_speed
                FROM circuits
                WHERE status = 'Enabled'
                GROUP BY site_name
            )
            SELECT 
                cs.site_name,
                cs.primary_provider,
                cs.primary_speed,
                cs.secondary_provider,
                cs.secondary_speed,
                mi.device_notes,
                mi.wan1_provider_label,
                mi.wan2_provider_label
            FROM circuit_summary cs
            JOIN meraki_inventory mi ON cs.site_name = mi.network_name
            WHERE (
                (cs.primary_provider IS NOT NULL AND (mi.wan1_provider_label IS NULL OR mi.wan1_provider_label = ''))
                OR
                (cs.secondary_provider IS NOT NULL AND (mi.wan2_provider_label IS NULL OR mi.wan2_provider_label = ''))
            )
            AND cs.site_name NOT LIKE '%Test%'
            AND cs.site_name NOT LIKE '%Lab%'
            AND cs.site_name NOT LIKE '%Voice%'
            ORDER BY cs.site_name
        '''))
        
        sites_to_fix = result.fetchall()
        print(f"📊 Found {len(sites_to_fix)} sites needing sync")
        
        if len(sites_to_fix) == 0:
            print("✅ All sites are in sync!")
            return
        
        # Show examples
        print("\n📋 Examples of sites needing sync:")
        for i, (site, p_prov, p_speed, s_prov, s_speed, notes, w1_label, w2_label) in enumerate(sites_to_fix[:5]):
            print(f"\n{site}:")
            print(f"  DSR Primary: {p_prov} / {p_speed}")
            print(f"  DSR Secondary: {s_prov} / {s_speed}")
            print(f"  Current WAN1 label: '{w1_label}'")
            print(f"  Current WAN2 label: '{w2_label}'")
            print(f"  Current notes: {repr(notes[:50])}...")
        
        # Fix each site
        fixed_count = 0
        print("\n🔄 Syncing DSR data to Meraki notes...")
        
        for site, p_prov, p_speed, s_prov, s_speed, current_notes, w1_label, w2_label in sites_to_fix:
            try:
                # Build new notes
                notes_parts = []
                new_w1_provider = w1_label or ''
                new_w1_speed = ''
                new_w2_provider = w2_label or ''
                new_w2_speed = ''
                
                # Add WAN 1 if we have primary circuit from DSR
                if p_prov and not w1_label:
                    notes_parts.extend(['WAN 1', p_prov, p_speed or ''])
                    new_w1_provider = p_prov
                    new_w1_speed = p_speed or ''
                elif current_notes and 'WAN 1' in current_notes:
                    # Keep existing WAN 1 from notes
                    lines = current_notes.split('\\n') if '\\n' in current_notes else current_notes.split('\n')
                    wan1_idx = -1
                    for i, line in enumerate(lines):
                        if line.strip().upper() == 'WAN 1':
                            wan1_idx = i
                            break
                    if wan1_idx >= 0:
                        notes_parts.append('WAN 1')
                        if wan1_idx + 1 < len(lines):
                            notes_parts.append(lines[wan1_idx + 1])
                        if wan1_idx + 2 < len(lines) and lines[wan1_idx + 2].upper() != 'WAN 2':
                            notes_parts.append(lines[wan1_idx + 2])
                
                # Add WAN 2 from current notes or DSR secondary
                if s_prov and not w2_label:
                    notes_parts.extend(['WAN 2', s_prov, s_speed or ''])
                    new_w2_provider = s_prov
                    new_w2_speed = s_speed or ''
                elif current_notes and 'WAN 2' in current_notes:
                    # Keep existing WAN 2 from notes
                    lines = current_notes.split('\\n') if '\\n' in current_notes else current_notes.split('\n')
                    wan2_idx = -1
                    for i, line in enumerate(lines):
                        if line.strip().upper() == 'WAN 2':
                            wan2_idx = i
                            break
                    if wan2_idx >= 0:
                        notes_parts.append('WAN 2')
                        if wan2_idx + 1 < len(lines):
                            notes_parts.append(lines[wan2_idx + 1])
                            new_w2_provider = lines[wan2_idx + 1] if not new_w2_provider else new_w2_provider
                        if wan2_idx + 2 < len(lines):
                            notes_parts.append(lines[wan2_idx + 2])
                            new_w2_speed = lines[wan2_idx + 2] if not new_w2_speed else new_w2_speed
                
                if notes_parts:
                    # Create new notes with actual newlines
                    new_notes = '\n'.join(notes_parts)
                    
                    # Update the database
                    session.execute(text('''
                        UPDATE meraki_inventory
                        SET device_notes = :notes,
                            wan1_provider_label = :w1p,
                            wan1_speed_label = :w1s,
                            wan2_provider_label = :w2p,
                            wan2_speed_label = :w2s,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE network_name = :site
                    '''), {
                        'notes': new_notes,
                        'w1p': new_w1_provider,
                        'w1s': new_w1_speed,
                        'w2p': new_w2_provider,
                        'w2s': new_w2_speed,
                        'site': site
                    })
                    
                    if fixed_count % 20 == 0:
                        print(f"  ✅ Fixed {fixed_count} sites...")
                        session.commit()
                    
                    fixed_count += 1
                    
                    # Log significant changes
                    print(f"  📝 {site}: Added WAN1: {new_w1_provider} / {new_w1_speed}")
                    
            except Exception as e:
                print(f"  ❌ Error fixing {site}: {e}")
        
        # Final commit
        session.commit()
        
        print(f"\n✅ Successfully synced {fixed_count} sites")
        
        # Verify
        result = session.execute(text('''
            SELECT COUNT(*) FROM meraki_inventory 
            WHERE device_notes IS NOT NULL 
            AND (wan1_provider_label IS NULL OR wan1_provider_label = '')
            AND device_notes NOT LIKE '%Test%'
        '''))
        remaining = result.fetchone()[0]
        print(f"📊 Sites still with empty WAN1 labels: {remaining}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()