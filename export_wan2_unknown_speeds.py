#!/usr/bin/env python3
"""
Export WAN2 interfaces with unknown speed but AT&T or Verizon provider
"""

import sys
import csv
from datetime import datetime
sys.path.append('/usr/local/bin/Main')
from models import db, EnrichedCircuit, MerakiInventory
from dsrcircuits import app

def export_wan2_unknown_speeds():
    with app.app_context():
        # Query for WAN2 with unknown speed and AT&T or Verizon provider
        results = db.session.query(
            EnrichedCircuit.network_name,
            EnrichedCircuit.wan2_provider,
            EnrichedCircuit.wan2_speed,
            MerakiInventory.wan2_ip,
            MerakiInventory.wan2_arin_provider,
            MerakiInventory.device_tags
        ).join(
            MerakiInventory,
            EnrichedCircuit.network_name == MerakiInventory.network_name
        ).filter(
            # WAN2 speed is unknown
            db.or_(
                EnrichedCircuit.wan2_speed.ilike('%unknown%'),
                EnrichedCircuit.wan2_speed.is_(None),
                EnrichedCircuit.wan2_speed == ''
            )
        ).filter(
            # WAN2 provider is AT&T or Verizon
            db.or_(
                EnrichedCircuit.wan2_provider.ilike('%at&t%'),
                EnrichedCircuit.wan2_provider.ilike('%att%'),
                EnrichedCircuit.wan2_provider.ilike('%verizon%'),
                EnrichedCircuit.wan2_provider.ilike('%vzw%')
            )
        ).filter(
            # Exclude hub/lab/voice/test sites
            ~(
                EnrichedCircuit.network_name.ilike('%hub%') |
                EnrichedCircuit.network_name.ilike('%lab%') |
                EnrichedCircuit.network_name.ilike('%voice%') |
                EnrichedCircuit.network_name.ilike('%test%')
            )
        ).order_by(EnrichedCircuit.network_name).all()
        
        # Create CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/usr/local/bin/wan2_unknown_speeds_{timestamp}.csv'
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Network Name',
                'WAN2 Provider',
                'WAN2 Speed',
                'WAN2 IP',
                'WAN2 ARIN Provider',
                'Device Tags'
            ])
            
            # Write data
            count = 0
            for row in results:
                # Convert tags list to string
                tags = row.device_tags if row.device_tags else []
                tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags)
                
                writer.writerow([
                    row.network_name,
                    row.wan2_provider or 'N/A',
                    row.wan2_speed or 'Unknown',
                    row.wan2_ip or 'N/A',
                    row.wan2_arin_provider or 'N/A',
                    tags_str
                ])
                count += 1
        
        print(f"Export complete!")
        print(f"Found {count} WAN2 interfaces with unknown speed but AT&T/Verizon provider")
        print(f"CSV file saved to: {filename}")
        
        # Also show some statistics
        att_count = sum(1 for r in results if r.wan2_provider and ('at&t' in r.wan2_provider.lower() or 'att' in r.wan2_provider.lower()))
        vzw_count = sum(1 for r in results if r.wan2_provider and ('verizon' in r.wan2_provider.lower() or 'vzw' in r.wan2_provider.lower()))
        
        print(f"\nBreakdown by provider:")
        print(f"  AT&T: {att_count}")
        print(f"  Verizon: {vzw_count}")

if __name__ == '__main__':
    export_wan2_unknown_speeds()