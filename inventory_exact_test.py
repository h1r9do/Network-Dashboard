"""
INVENTORY MANAGEMENT - EXACT ORIGINAL WITH CORPORATE TABS
=========================================================
This preserves the EXACT original Meraki functionality and just adds corporate tabs
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
import psycopg2
import re
from config import Config
from datetime import datetime, date

# Create Blueprint
inventory_bp = Blueprint('inventory', __name__)

# Copy ALL original functions exactly
get_db_connection = original_inventory.get_db_connection
get_device_type_from_model = original_inventory.get_device_type_from_model
generate_critical_insights = original_inventory.generate_critical_insights
get_inventory_summary_data = original_inventory.get_inventory_summary_data
get_inventory_details_data = original_inventory.get_inventory_details_data

def get_corporate_network_data():
    """Get Corporate Network data for tabs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get detailed device data
        cursor.execute("""
            SELECT vendor, model, device_type, logical_devices, physical_devices, 
                   end_of_sale, end_of_support
            FROM netdisco_inventory_summary
            ORDER BY device_type, physical_devices DESC
        """)
        
        device_details = []
        for row in cursor.fetchall():
            vendor, model, device_type, logical, physical, eos, eol = row
            device_details.append({
                'vendor': vendor,
                'model': model,
                'device_type': device_type,
                'logical_devices': logical,
                'physical_devices': physical,
                'end_of_sale': eos.isoformat() if eos else None,
                'end_of_support': eol.isoformat() if eol else None
            })
        
        # Get summary by device type
        cursor.execute("""
            SELECT 
                device_type,
                COUNT(DISTINCT model) as model_count,
                SUM(logical_devices) as logical_count,
                SUM(physical_devices) as physical_count,
                COUNT(*) FILTER (WHERE end_of_support IS NOT NULL AND end_of_support <= CURRENT_DATE) as eol_count,
                COUNT(*) FILTER (WHERE end_of_sale IS NOT NULL AND end_of_sale <= CURRENT_DATE AND (end_of_support IS NULL OR end_of_support > CURRENT_DATE)) as eos_count
            FROM netdisco_inventory_summary
            GROUP BY device_type
            ORDER BY physical_count DESC
        """)
        
        summary_data = []
        total_models = 0
        total_logical = 0
        total_physical = 0
        total_eol = 0
        total_eos = 0
        
        for row in cursor.fetchall():
            device_type, model_count, logical_count, physical_count, eol_count, eos_count = row
            
            summary_data.append({
                'device_type': device_type,
                'model_count': model_count,
                'logical_count': logical_count,
                'physical_count': physical_count,
                'eol_count': eol_count,
                'eos_count': eos_count,
                'active_count': model_count - eol_count - eos_count
            })
            
            total_models += model_count
            total_logical += logical_count
            total_physical += physical_count
            total_eol += eol_count
            total_eos += eos_count
        
        return {
            'summary': summary_data,
            'details': device_details,
            'totals': {
                'models': total_models,
                'logical': total_logical,
                'physical': total_physical,
                'eol': total_eol,
                'eos': total_eos,
                'active': total_models - total_eol - total_eos
            }
        }
        
    except Exception as e:
        print(f"Error getting corporate data: {e}")
        return {'summary': [], 'details': [], 'totals': {}}
    finally:
        cursor.close()
        conn.close()

# ORIGINAL ROUTES - COPIED EXACTLY
@inventory_bp.route('/inventory-summary')
def inventory_summary():
    """
    Device model summary page with lifecycle status - ORIGINAL PRESERVED
    """
    try:
        # Get ORIGINAL Meraki data exactly as before
        data = get_inventory_summary_data()
        
        # Get Corporate data for tabs
        corporate_data = get_corporate_network_data()
        
        summary_data = data.get('summary', [])
        org_names = data.get('org_names', [])
        eol_summary = data.get('eol_summary', {})
        data_source = data.get('data_source', 'unknown')
        
        print(f"📊 Loaded inventory summary from {data_source}: {len(summary_data)} models across {len(org_names)} orgs")
        
        if data_source == 'error':
            return "Error loading inventory summary from database", 500
        
        # Calculate total devices for display
        total_devices = sum(entry.get('total', 0) for entry in summary_data)
        
        # Use the final tabbed template with all original content preserved
        return render_template('inventory_tabbed_final.html', 
                             summary=summary_data, 
                             org_names=org_names,
                             eol_summary=eol_summary,
                             total_devices=total_devices,
                             data_source=data_source,
                             corporate_data=corporate_data)

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