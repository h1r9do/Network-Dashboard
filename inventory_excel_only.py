#!/usr/bin/env python3
"""
INVENTORY MANAGEMENT - EXCEL ONLY VERSION
=========================================
Tab 1: Meraki Executive Summary (original, no changes)
Tab 2: Corp Network Summary (executive summary from Excel EOL data)
Tab 3: Meraki Inventory Details (original, no changes) 
Tab 4: Corp Network Inventory (all Excel sheets as sections)
"""

# Import the ORIGINAL functions from the real inventory.py
import sys
import os

# Add the path and import the original inventory module
sys.path.insert(0, '/usr/local/bin')

# Import everything from the original inventory module
import importlib.util
spec = importlib.util.spec_from_file_location("original_inventory", "/usr/local/bin/inventory.py")
original_inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original_inventory)

# Import what we need
from flask import Blueprint, render_template, jsonify, request
import json
from datetime import datetime, date

# Import our corporate data functions
from corp_network_data import get_corp_executive_summary, get_corp_inventory_by_location

# Create Blueprint
inventory_bp = Blueprint('inventory', __name__)

# Copy ALL original functions exactly
get_db_connection = original_inventory.get_db_connection
get_device_type_from_model = original_inventory.get_device_type_from_model
generate_critical_insights = original_inventory.generate_critical_insights
get_inventory_summary_data = original_inventory.get_inventory_summary_data
get_inventory_details_data = original_inventory.get_inventory_details_data

@inventory_bp.route('/inventory-summary')
def inventory_summary():
    """
    4-Tab layout with Excel-based corporate data
    """
    try:
        # Get ORIGINAL Meraki data exactly as before
        meraki_data = get_inventory_summary_data()
        
        # Get Corporate data from Excel only
        corp_executive = get_corp_executive_summary()
        corp_inventory = get_corp_inventory_by_location()
        
        meraki_summary = meraki_data.get('summary', [])
        org_names = meraki_data.get('org_names', [])
        eol_summary = meraki_data.get('eol_summary', {})
        data_source = meraki_data.get('data_source', 'unknown')
        
        print(f"📊 Loaded Meraki data from {data_source}: {len(meraki_summary)} models")
        print(f"🏢 Loaded Corporate data: {corp_executive['overall'].get('total_models', 0)} models")
        
        if data_source == 'error':
            return "Error loading Meraki inventory summary from database", 500
        
        # Calculate total devices for display
        total_meraki_devices = sum(entry.get('total', 0) for entry in meraki_summary)
        total_corp_devices = corp_executive['overall'].get('total_devices', 0)
        
        # Use the new 4-tab template
        return render_template('inventory_4tab_excel.html', 
                             # Meraki data (unchanged)
                             summary=meraki_summary, 
                             org_names=org_names,
                             eol_summary=eol_summary,
                             total_meraki_devices=total_meraki_devices,
                             data_source=data_source,
                             # Corporate data (Excel-based)
                             corp_executive=corp_executive,
                             corp_inventory=corp_inventory,
                             total_corp_devices=total_corp_devices)

    except Exception as e:
        print(f"❌ Error loading inventory summary: {e}")
        return f"Error loading inventory summary: {e}", 500

# Copy ALL other original routes exactly
@inventory_bp.route('/inventory-details')
def inventory_details():
    """Original inventory details - unchanged"""
    return original_inventory.inventory_details()

@inventory_bp.route('/api/inventory-summary')
def api_inventory_summary():
    """Original API - unchanged"""
    return original_inventory.api_inventory_summary()

@inventory_bp.route('/api/inventory-details')
def api_inventory_details():
    """Original API - unchanged"""
    return original_inventory.api_inventory_details()

@inventory_bp.route('/eol-dashboard')
def eol_dashboard():
    """Original EOL dashboard - unchanged"""
    return original_inventory.eol_dashboard()

# Add route for testing
@inventory_bp.route('/test-corp-data')
def test_corp_data():
    """Test endpoint for corporate data"""
    try:
        corp_executive = get_corp_executive_summary()
        corp_inventory = get_corp_inventory_by_location()
        
        return jsonify({
            'corp_executive': corp_executive,
            'corp_inventory_summary': [
                {
                    'location_type': loc['location_type'],
                    'total_devices': loc['total_devices'],
                    'unique_models': loc['unique_models'],
                    'unique_sites': loc['unique_sites']
                }
                for loc in corp_inventory['by_location']
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500