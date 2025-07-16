"""
HISTORICAL DATA AND CHANGE LOG ANALYSIS - DATABASE VERSION
==========================================================

Purpose:
    - Historical circuit data analysis and change tracking from database
    - Circuit change log generation using CircuitHistory table
    - Time-series analysis of circuit status and configuration changes
    - Trend analysis and reporting

Pages Served:
    - /dsrhistorical (historical data and change log interface)

Templates Used:
    - dsrhistorical.html (change log interface with time period selection)

API Endpoints:
    - /api/circuit-changelog (POST) - Generate change log for specified time period

Key Functions:
    - Database-driven change detection using CircuitHistory table
    - Change categorization from database records
    - Statistical analysis of changes over time
    - Flexible time period selection (24h, week, month, quarter, year, custom)
    - Export functionality for change reports

Dependencies:
    - models.py (Circuit, CircuitHistory database models)
    - SQLAlchemy for database operations
    - utils.py for utility functions

Data Processing:
    - Query CircuitHistory table for time-based filtering
    - Change categorization from historical records
    - Impact assessment and statistical analysis
    - Time-based filtering and validation

Features:
    - Flexible time period selection
    - Detailed change categorization
    - Statistical summaries
    - Error handling for missing data periods
    - Export capabilities
    - Change impact analysis
"""

from flask import Blueprint, render_template, jsonify, request
from models import db, Circuit, CircuitHistory
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
from utils import safe_str

def get_change_category(change_type):
    """Map change type to category"""
    if not change_type:
        return "Other"
    
    if "STATUS" in change_type or "ENABLED" in change_type or "READY" in change_type:
        return "Circuit Status"
    elif "PROVIDER" in change_type:
        return "Service Provider"
    elif "SPEED" in change_type:
        return "Technical"
    elif "COST" in change_type:
        return "Financial"
    elif "NEW_CIRCUIT" in change_type:
        return "New Circuit"
    else:
        return "Other"

def get_change_impact(change_type):
    """Map change type to impact description"""
    impact_map = {
        "CIRCUIT_ENABLED": "Circuit activated",
        "CIRCUIT_DISABLED": "Circuit deactivated", 
        "READY_FOR_ENABLEMENT": "Ready for activation",
        "CUSTOMER_ACTION_REQUIRED": "Customer action needed",
        "SPONSOR_APPROVAL_REQUIRED": "Sponsor approval needed",
        "CONTACT_REQUIRED": "Contact required",
        "PROVIDER_CHANGE": "Service provider updated",
        "SPEED_CHANGE": "Service speed updated",
        "COST_CHANGE": "Cost updated",
        "NEW_CIRCUIT": "New circuit added"
    }
    return impact_map.get(change_type, "Circuit updated")

# Create Blueprint
historical_bp = Blueprint('historical', __name__)

@historical_bp.route('/dsrhistorical')
def historical():
    """
    Historical data and change log interface
    
    Provides interface for selecting time periods and generating
    detailed change logs from database history.
    
    Returns:
        Rendered dsrhistorical.html template
    """
    print("📈 Loading historical data interface (database version)")
    return render_template('dsrhistorical.html')

@historical_bp.route('/api/circuit-changelog', methods=['POST'])
def circuit_changelog():
    """
    Generate circuit change log for specified time period from database
    
    Queries CircuitHistory table to identify and categorize changes
    over the requested time period.
    
    Request Parameters:
        timePeriod (str): One of 'last_24_hours', 'last_week', 'last_month', 
                         'last_quarter', 'last_year', 'custom'
        customStart (str): Start date for custom range (YYYY-MM-DD)
        customEnd (str): End date for custom range (YYYY-MM-DD)
    
    Returns:
        JSON response with:
        - Detailed change data from database
        - Summary statistics
        - Period information
        OR error information with helpful guidance
    """
    try:
        time_period = request.form.get('timePeriod', 'last_week')
        custom_start = request.form.get('customStart')
        custom_end = request.form.get('customEnd')
        
        print(f"🔍 Generating changelog from database for period: {time_period}")
        
        # Get available data range from database
        oldest_change = CircuitHistory.query.order_by(CircuitHistory.change_date.asc()).first()
        newest_change = CircuitHistory.query.order_by(CircuitHistory.change_date.desc()).first()
        
        if not oldest_change or not newest_change:
            return jsonify({
                "error": "No Historical Data Available",
                "detailed_error": "No circuit history data found in database. Historical data is generated during nightly processing.",
                "suggested_action": "Wait for nightly processing to complete or check database connectivity."
            }), 400
        
        oldest_date = oldest_change.change_date
        newest_date = newest_change.change_date
        
        print(f"📊 Available history data from {oldest_date} to {newest_date}")
        
        # Calculate requested date range
        today = datetime.now().date()
        
        if time_period == 'custom':
            if not custom_start or not custom_end:
                return jsonify({"error": "Custom date range requires both start and end dates"}), 400
            start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
        elif time_period == 'last_24_hours':
            end_date = today
            start_date = today - timedelta(days=1)
        elif time_period == 'last_week':
            end_date = today
            start_date = today - timedelta(days=7)
        elif time_period == 'last_month':
            end_date = today
            start_date = today - timedelta(days=30)
        elif time_period == 'last_quarter':
            end_date = today
            start_date = today - timedelta(days=90)
        elif time_period == 'last_year':
            end_date = today
            start_date = today - timedelta(days=365)
        else:
            end_date = today
            start_date = today - timedelta(days=7)
        
        print(f"📅 Requested changelog from {start_date} to {end_date}")
        
        if start_date > end_date:
            return jsonify({
                "error": "Invalid Date Range",
                "detailed_error": f"Start date ({start_date}) is after end date ({end_date}).",
                "suggested_action": "Please ensure the start date is before the end date."
            }), 400
        
        # Validate requested date range against available data
        if start_date < oldest_date:
            days_requested = (end_date - start_date).days
            oldest_date_str = oldest_date.strftime('%B %d, %Y')
            newest_date_str = newest_date.strftime('%B %d, %Y')
            
            return jsonify({
                "error": f"No Data Available for Requested Period",
                "detailed_error": f"You requested data going back {days_requested} days (starting {start_date.strftime('%B %d, %Y')}), but our historical data only goes back to {oldest_date_str}.\n\nAvailable data range: {oldest_date_str} to {newest_date_str}\n\nPlease select a date range within this period or use a shorter time frame.",
                "available_from": oldest_date.strftime('%Y-%m-%d'),
                "available_to": newest_date.strftime('%Y-%m-%d'),
                "requested_from": start_date.strftime('%Y-%m-%d'),
                "suggested_action": f"Try selecting 'Custom Range' and choose dates between {oldest_date_str} and {newest_date_str}"
            }), 400
        
        # Only reject dates that are clearly in the future (more than today)
        if start_date > today:
            return jsonify({
                "error": f"Future Date Selected",
                "detailed_error": f"You selected a start date of {start_date.strftime('%B %d, %Y')}, which is in the future.\n\nPlease select dates up to today ({today.strftime('%B %d, %Y')}).",
                "available_from": oldest_date.strftime('%Y-%m-%d'),
                "available_to": newest_date.strftime('%Y-%m-%d'),
                "requested_from": start_date.strftime('%Y-%m-%d'),
                "suggested_action": f"Select dates up to today ({today.strftime('%B %d, %Y')})"
            }), 400
        
        # Query changes from database within date range
        changes_query = CircuitHistory.query.filter(
            and_(
                CircuitHistory.change_date >= start_date,
                CircuitHistory.change_date <= end_date
            )
        ).order_by(CircuitHistory.change_date.desc(), CircuitHistory.id.desc())
        
        circuit_changes = changes_query.all()
        
        print(f"📂 Found {len(circuit_changes)} changes in database for requested range")
        
        if len(circuit_changes) == 0:
            period_desc = time_period.replace('_', ' ').title()
            return jsonify({
                "message": f"No circuit changes were detected during the {period_desc} period ({start_date} to {end_date}).",
                "data": [],
                "summary": {
                    "total_changes": 0,
                    "changes_by_type": {},
                    "period_days": (end_date - start_date).days,
                    "changes_per_day": 0,
                    "most_common_change": "None"
                },
                "period": {
                    "description": period_desc,
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                }
            }), 200
        
        # Convert database records to change format
        changes = []
        for change_record in circuit_changes:
            # Get circuit information
            circuit = Circuit.query.get(change_record.circuit_id)
            
            # Map database fields to match frontend expectations
            change_category = get_change_category(change_record.change_type)
            change_description = f"{change_record.field_changed or 'status'} changed"
            if change_record.old_value and change_record.new_value:
                change_description = f"{change_record.field_changed or 'status'} changed: {change_record.old_value} → {change_record.new_value}"
            
            change_data = {
                "site_name": circuit.site_name if circuit else "Unknown",
                "site_id": circuit.site_id if circuit else "",
                "circuit_purpose": circuit.circuit_purpose if circuit else "",
                "change_type": change_record.change_type or "STATUS_CHANGE",
                "field_changed": change_record.field_changed or "status",
                "before_value": change_record.old_value or "",  # Map old_value to before_value
                "after_value": change_record.new_value or "",   # Map new_value to after_value
                "change_time": change_record.change_date.strftime('%Y-%m-%d'),
                "change_category": change_category,
                "description": change_description,
                "impact": get_change_impact(change_record.change_type),
                "csv_file_source": change_record.csv_file_source or "database",
                "provider_name": circuit.provider_name if circuit else "",
                "details_ordered_service_speed": circuit.details_ordered_service_speed if circuit else "",
                "billing_monthly_cost": str(circuit.billing_monthly_cost) if circuit and circuit.billing_monthly_cost else ""
            }
            changes.append(change_data)
        
        # Generate summary statistics
        summary = generate_summary_from_db_changes(changes, start_date, end_date)
        
        response = {
            "data": changes,
            "summary": summary,
            "period": {
                "description": time_period.replace('_', ' ').title(),
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            },
            "data_source": "database"
        }
        
        print(f"✅ Generated {len(changes)} changes from database")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error generating changelog from database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "System Error", 
            "detailed_error": f"An unexpected error occurred while generating the changelog: {str(e)}",
            "suggested_action": "Please try again or contact support if the problem persists."
        }), 500

def generate_summary_from_db_changes(changes, start_date, end_date):
    """
    Generate summary statistics from database change records
    
    Args:
        changes: List of change dictionaries from database
        start_date: Start date of analysis period
        end_date: End date of analysis period
    
    Returns:
        Dictionary containing summary statistics
    """
    if not changes:
        return {
            "total_changes": 0,
            "changes_by_type": {},
            "period_days": (end_date - start_date).days,
            "changes_per_day": 0,
            "most_common_change": "None"
        }
    
    # Count changes by type
    changes_by_type = {}
    changes_by_field = {}
    
    for change in changes:
        change_type = change.get('change_type', 'unknown')
        field_changed = change.get('field_changed', 'unknown')
        
        changes_by_type[change_type] = changes_by_type.get(change_type, 0) + 1
        changes_by_field[field_changed] = changes_by_field.get(field_changed, 0) + 1
    
    # Calculate daily average
    period_days = max((end_date - start_date).days, 1)
    changes_per_day = round(len(changes) / period_days, 2)
    
    # Find most common change type
    most_common_change = max(changes_by_type.items(), key=lambda x: x[1])[0] if changes_by_type else "None"
    
    return {
        "total_changes": len(changes),
        "changes_by_type": changes_by_type,
        "changes_by_field": changes_by_field,
        "period_days": period_days,
        "changes_per_day": changes_per_day,
        "most_common_change": most_common_change,
        "unique_circuits_affected": len(set(change.get('site_name', '') for change in changes))
    }