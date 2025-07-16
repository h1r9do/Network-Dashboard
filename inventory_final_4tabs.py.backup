#!/usr/bin/env python3
"""
FINAL 4-TAB INVENTORY IMPLEMENTATION
====================================
Tab 1: Meraki Executive Summary - EXACT copy of original
Tab 2: Corp Network Summary - Excel EOL data rows 62+ only
Tab 3: Meraki Inventory Details - EXACT copy of original
Tab 4: All Data Centers - With EOL dates from Excel
"""

import sys
sys.path.insert(0, '/usr/local/bin')
sys.path.insert(0, '/root')

# Import the ORIGINAL inventory module to get exact functionality
import importlib.util
spec = importlib.util.spec_from_file_location("original_inventory", "/usr/local/bin/inventory.py")
original_inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original_inventory)

from flask import Blueprint, render_template, jsonify
from corp_network_data_db import get_corp_executive_summary_db, get_datacenter_inventory_with_eol_db, get_comprehensive_datacenter_inventory_db
from datetime import date

# Create Blueprint
inventory_bp = Blueprint('inventory', __name__)

# Use ALL original functions for Meraki data
get_inventory_summary_data = original_inventory.get_inventory_summary_data

@inventory_bp.route('/inventory-summary')
def inventory_summary():
    """
    Final 4-tab layout
    """
    try:
        # Get ORIGINAL Meraki data exactly as it appears on port 5052
        meraki_data = get_inventory_summary_data()
        
        # Get Corporate data from database (Tabs 2 & 4)
        corp_executive = get_corp_executive_summary_db()
        print("🔍 About to call get_comprehensive_datacenter_inventory_db()...", file=sys.stderr)
        datacenter_data = get_comprehensive_datacenter_inventory_db()
        print(f"🔍 Returned data summary: {datacenter_data.get('summary', {})}", file=sys.stderr)
        sys.stderr.flush()
        
        meraki_summary = meraki_data.get('summary', [])
        org_names = meraki_data.get('org_names', [])
        eol_summary = meraki_data.get('eol_summary', {})
        data_source = meraki_data.get('data_source', 'unknown')
        
        print(f"📊 Loaded original Meraki data: {len(meraki_summary)} models")
        print(f"🏢 Loaded corporate data: {corp_executive['overall'].get('total_models', 0)} models from database")
        print(f"🏢 Loaded comprehensive datacenter inventory: {datacenter_data['summary']['total_devices']} master devices, {datacenter_data['summary']['total_chassis_blades']} blades, {datacenter_data['summary']['total_sfp_modules']} SFPs, {datacenter_data['summary']['total_hardware_components']} components")
        
        # Calculate totals
        total_meraki_devices = sum(entry.get('total', 0) for entry in meraki_summary)
        
        # Render the final template
        return render_template('inventory_final_4tabs.html', 
                             # Original Meraki data - unchanged
                             summary=meraki_summary, 
                             org_names=org_names,
                             eol_summary=eol_summary,
                             total_meraki_devices=total_meraki_devices,
                             data_source=data_source,
                             # Corporate data
                             corp_executive=corp_executive,
                             datacenter_data=datacenter_data,
                             # Date for comparison
                             today=date.today())

    except Exception as e:
        print(f"❌ Error loading inventory: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading inventory: {e}", 500

# All other routes use original functions
@inventory_bp.route('/inventory-details')
def inventory_details():
    return original_inventory.inventory_details()

@inventory_bp.route('/eol-dashboard')  
def eol_dashboard():
    return original_inventory.eol_dashboard()

@inventory_bp.route('/api/inventory-summary')
def api_inventory_summary():
    return original_inventory.api_inventory_summary()

@inventory_bp.route('/api/inventory-details')
def api_inventory_details():
    return original_inventory.api_inventory_details()