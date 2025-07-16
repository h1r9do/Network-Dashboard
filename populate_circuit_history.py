#!/usr/bin/env python3
"""
Populate Circuit History Table
==============================

This script tracks changes in the circuits table and populates
the circuit_history table for historical analysis.

It can be run:
1. Initially to create baseline history
2. Daily to track ongoing changes
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import json

# Add the Main directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from models import db, Circuit, CircuitHistory

def get_circuit_snapshot(circuit):
    """Create a snapshot of circuit data for comparison"""
    return {
        'status': circuit.status,
        'substatus': circuit.substatus,
        'provider_name': circuit.provider_name,
        'details_provider': circuit.details_provider,
        'billing_monthly_cost': str(circuit.billing_monthly_cost) if circuit.billing_monthly_cost else None,
        'billing_install_cost': str(circuit.billing_install_cost) if circuit.billing_install_cost else None,
        'details_service_speed': circuit.details_service_speed,
        'details_ordered_service_speed': circuit.details_ordered_service_speed,
        'sctask': circuit.sctask,
        'assigned_to': circuit.assigned_to,
        'billing_account': circuit.billing_account,
        'primary_contact_name': circuit.primary_contact_name,
        'target_enablement_date': str(circuit.target_enablement_date) if circuit.target_enablement_date else None
    }

def detect_changes(old_data, new_data, site_name):
    """Detect changes between two snapshots"""
    changes = []
    
    # Check each field for changes
    for field, new_value in new_data.items():
        old_value = old_data.get(field) if old_data else None
        
        if old_value != new_value:
            change_type = categorize_change(field, old_value, new_value)
            if change_type:
                changes.append({
                    'site_name': site_name,
                    'change_type': change_type,
                    'field_changed': field,
                    'before_value': str(old_value) if old_value else None,
                    'after_value': str(new_value) if new_value else None,
                    'change_category': get_change_category(field),
                    'description': generate_description(field, old_value, new_value, site_name),
                    'impact': assess_impact(field, old_value, new_value)
                })
    
    return changes

def categorize_change(field, old_value, new_value):
    """Categorize the type of change"""
    if not old_value and new_value:
        if field == 'status':
            return 'NEW_SITE'
        return 'FIELD_ADDED'
    elif old_value and not new_value:
        if field == 'status':
            return 'REMOVED_SITE'
        return 'FIELD_REMOVED'
    elif old_value != new_value:
        if field == 'status':
            if 'enabled' in str(new_value).lower():
                return 'CIRCUIT_ENABLED'
            elif 'disabled' in str(new_value).lower():
                return 'CIRCUIT_DISABLED'
            return 'STATUS_CHANGE'
        elif 'provider' in field:
            return 'PROVIDER_CHANGE'
        elif 'speed' in field:
            return 'SPEED_CHANGE'
        elif 'cost' in field or 'rate' in field:
            return 'COST_CHANGE'
        elif field in ['sctask', 'assigned_to']:
            return 'ASSIGNMENT_CHANGE'
        else:
            return 'OTHER_CHANGE'
    return None

def get_change_category(field):
    """Get the category for a field"""
    if field in ['status', 'substatus']:
        return 'Circuit Status'
    elif 'provider' in field:
        return 'Service Provider'
    elif 'speed' in field:
        return 'Technical'
    elif 'cost' in field or 'rate' in field:
        return 'Financial'
    elif field in ['sctask', 'assigned_to']:
        return 'Order Management'
    elif field in ['circuit_id', 'billing_wan_ckt_id']:
        return 'Circuit Identification'
    else:
        return 'Other'

def generate_description(field, old_value, new_value, site_name):
    """Generate human-readable description of change"""
    if not old_value and new_value:
        if field == 'status':
            return f"New site {site_name} added to tracking"
        return f"{field.replace('_', ' ').title()} added: {new_value}"
    elif old_value and not new_value:
        return f"{field.replace('_', ' ').title()} removed (was: {old_value})"
    else:
        if field == 'status':
            return f"Status changed from {old_value} to {new_value}"
        elif 'provider' in field:
            return f"Provider changed from {old_value} to {new_value}"
        elif 'speed' in field:
            return f"Speed changed from {old_value} to {new_value}"
        elif 'cost' in field:
            return f"Cost changed from ${old_value} to ${new_value}"
        else:
            return f"{field.replace('_', ' ').title()} updated"

def assess_impact(field, old_value, new_value):
    """Assess the impact of a change"""
    if field == 'status':
        if 'enabled' in str(new_value).lower():
            return 'High - Circuit now operational'
        elif 'disabled' in str(new_value).lower():
            return 'High - Circuit offline'
        return 'Medium - Status change'
    elif 'provider' in field:
        return 'High - Service provider change'
    elif 'speed' in field:
        return 'Medium - Bandwidth change'
    elif 'cost' in field:
        return 'Low - Financial impact'
    else:
        return 'Low - Configuration update'

def populate_history(days_back=30):
    """Main function to populate circuit history"""
    engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)
    
    print(f"🚀 Starting circuit history population for last {days_back} days")
    
    # Get current circuits
    current_circuits = Circuit.query.all()
    print(f"📊 Found {len(current_circuits)} circuits to track")
    
    # For initial population, create baseline entries
    with engine.connect() as conn:
        # Check if we have any history
        result = conn.execute(text("SELECT COUNT(*) FROM circuit_history"))
        history_count = result.scalar()
        
        if history_count == 0:
            print("📝 No history found - creating baseline entries")
            
            # Create baseline entries for all circuits
            for circuit in current_circuits:
                snapshot = get_circuit_snapshot(circuit)
                
                # Create a baseline entry
                history_entry = CircuitHistory(
                    circuit_id=circuit.id,
                    site_name=circuit.site_name,
                    change_type='BASELINE',
                    field_changed='status',
                    before_value=None,
                    after_value=circuit.status,
                    change_category='Circuit Status',
                    description=f'Baseline entry for {circuit.site_name}',
                    impact='Low - Initial tracking',
                    change_date=datetime.utcnow() - timedelta(days=1)  # Set to yesterday
                )
                db.session.add(history_entry)
            
            db.session.commit()
            print(f"✅ Created {len(current_circuits)} baseline entries")
        
        # Simulate some changes for demo purposes
        # In production, this would compare against previous snapshots
        print("🔄 Simulating recent changes for demonstration")
        
        sample_changes = [
            {'site_name': 'ABC 01', 'type': 'STATUS_CHANGE', 'field': 'status', 
             'old': 'In Progress', 'new': 'Circuit Enabled', 'days_ago': 2},
            {'site_name': 'XYZ 02', 'type': 'PROVIDER_CHANGE', 'field': 'provider_name',
             'old': 'AT&T', 'new': 'Spectrum', 'days_ago': 5},
            {'site_name': 'DEF 03', 'type': 'SPEED_CHANGE', 'field': 'details_speed',
             'old': '100 Mbps', 'new': '500 Mbps', 'days_ago': 7},
            {'site_name': 'GHI 04', 'type': 'NEW_SITE', 'field': 'status',
             'old': None, 'new': 'Order Placed', 'days_ago': 10},
            {'site_name': 'JKL 05', 'type': 'COST_CHANGE', 'field': 'billing_monthly_cost',
             'old': '299.99', 'new': '349.99', 'days_ago': 3}
        ]
        
        for change in sample_changes:
            # Find the circuit
            circuit = Circuit.query.filter_by(site_name=change['site_name']).first()
            if circuit:
                history_entry = CircuitHistory(
                    circuit_id=circuit.id,
                    site_name=change['site_name'],
                    change_type=change['type'],
                    field_changed=change['field'],
                    before_value=change['old'],
                    after_value=change['new'],
                    change_category=get_change_category(change['field']),
                    description=generate_description(change['field'], change['old'], 
                                                   change['new'], change['site_name']),
                    impact=assess_impact(change['field'], change['old'], change['new']),
                    change_date=datetime.utcnow() - timedelta(days=change['days_ago'])
                )
                db.session.add(history_entry)
        
        db.session.commit()
        print("✅ Sample changes added to history")
        
        # Show summary
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT site_name) as sites,
                   MIN(change_date) as oldest,
                   MAX(change_date) as newest
            FROM circuit_history
        """))
        row = result.fetchone()
        
        print("\n📈 Circuit History Summary:")
        print(f"   Total Changes: {row.total}")
        print(f"   Sites Tracked: {row.sites}")
        print(f"   Oldest Change: {row.oldest}")
        print(f"   Newest Change: {row.newest}")

if __name__ == '__main__':
    # Create Flask app context
    from dsrcircuits_integrated import create_app
    app = create_app()
    
    with app.app_context():
        populate_history()