"""
STATUS DASHBOARD AND CIRCUIT ORDERS - DATABASE VERSION
======================================================

Purpose:
    - Circuit status dashboard with categorized views
    - In-flight circuit orders management
    - Real-time status monitoring and filtering
    - Action-oriented dashboard for circuit management
    - SCTASK and assignment management

Pages Served:
    - /dsrdashboard (main status dashboard)
    - /circuit-orders (circuit orders management dashboard)

Templates Used:
    - dsrdashboard.html (main status dashboard with action panels)
    - circuit_orders.html (in-flight orders dashboard)

API Endpoints:
    - /api/dashboard-data (GET) - Main dashboard data with status categorization
    - /api/inflight-data (GET) - In-flight circuit orders data with workflow states
    - /api/save-assignment (POST) - Save SCTASK number and assigned personnel
    - /api/get-assignments (GET) - Retrieve all circuit assignments

Key Functions:
    - Status categorization and filtering
    - Action-required item identification
    - In-flight order tracking and prioritization
    - Real-time status updates
    - Workflow-based circuit management
    - Assignment data persistence and management

Dependencies:
    - models.py (Circuit, CircuitAssignment database models)
    - SQLAlchemy for database operations
    - utils.py for categorization functions

Data Processing:
    - Status categorization (enabled, ready, customer_action, etc.)
    - Date-based filtering for stale records
    - In-flight status classification
    - Action priority assignment
    - Assignment data correlation

Features:  
    - Interactive status filtering
    - Action-required highlighting
    - Priority-based sorting
    - Export capabilities
    - Real-time status monitoring
    - Editable SCTASK and assignment fields
    - ServiceNow integration with clickable links
"""

from flask import Blueprint, render_template, jsonify, request
from models import db, Circuit, CircuitAssignment, NewStore
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
from utils import safe_str, categorize_status

# Create Blueprint
status_bp = Blueprint('status', __name__)

@status_bp.route('/dsrdashboard')
def dashboard():
    """
    Main status dashboard page
    
    Displays circuit status overview with action-required items,
    status categorization, and interactive filtering capabilities.
    
    Returns:
        Rendered dsrdashboard.html template
    """
    print("📊 Loading status dashboard (database version)")
    return render_template('dsrdashboard.html')


@status_bp.route('/circuit-orders')
def circuit_orders():
    """
    Circuit Orders Dashboard page
    
    Displays in-flight circuit orders with workflow states,
    priority indicators, and action tracking.
    
    Returns:
        Rendered circuit_orders.html template
    """
    print("🚀 Loading circuit orders dashboard (database version)")
    return render_template('circuit_orders.html')

@status_bp.route('/api/dashboard-data', methods=['GET'])
def dashboard_data():
    """
    API endpoint to get dashboard data from database
    
    Processes circuit data from database and provides:
    - Status category counts (enabled, ready, customer_action, etc.)
    - Detailed status breakdowns
    - Sub-status information
    - New sites identification
    - Action-required item highlighting
    - Assignment data integration
    
    Returns:
        JSON response with dashboard statistics and data
    """
    try:
        import time
        start_time = time.time()
        print("📊 Loading dashboard data from database")
        
        # Get ALL current circuits except Order Canceled (database contains only current state, no grouping needed)
        # Exclude Order Canceled to reduce data size and improve performance
        circuits = db.session.query(Circuit).filter(
            ~Circuit.status.ilike('%order canceled%')
        ).all()
        
        load_time = time.time() - start_time
        print(f"⏱️ Database query took {load_time:.3f} seconds for {len(circuits)} circuits (excluding Order Canceled)")
        
        if not circuits:
            return jsonify({"error": "No circuit data found in database"}), 400
        
        # Convert to list of dictionaries and process - MATCH CSV COLUMN NAMES
        circuit_data = []
        for circuit in circuits:
            # Map database fields to CSV column names for frontend compatibility
            circuit_dict = {
                'Site Name': safe_str(circuit.site_name or ''),
                'Site ID': safe_str(circuit.site_id or ''),
                'Circuit Purpose': safe_str(circuit.circuit_purpose or ''),
                'status': safe_str(circuit.status or ''),
                'substatus': safe_str(circuit.substatus or ''),
                'provider_name': safe_str(circuit.provider_name or ''),
                'details_ordered_service_speed': safe_str(circuit.details_ordered_service_speed or ''),
                'billing_monthly_cost': safe_str(circuit.billing_monthly_cost or ''),
                'date_record_updated': circuit.date_record_updated.strftime('%Y-%m-%d') if circuit.date_record_updated else '',
                'id': str(circuit.id),
                'ip_address_start': safe_str(circuit.ip_address_start or ''),
                'city': safe_str(circuit.city or ''),
                'state': safe_str(circuit.state or ''),
                'assigned_to': safe_str(circuit.assigned_to or ''),
                'sctask': safe_str(circuit.sctask or '')
            }
            
            # Add status categorization
            circuit_dict['status_category'] = categorize_status(circuit_dict.get('status', ''))
            
            # Add assignment data from database
            assignment = CircuitAssignment.query.filter_by(
                site_name=circuit.site_name
            ).first()
            
            if assignment:
                circuit_dict['sctask_number'] = safe_str(assignment.sctask or '')
                circuit_dict['sctask_sys_id'] = ''  # Not stored in current model
                circuit_dict['assigned_to'] = safe_str(assignment.assigned_to or '')
            else:
                circuit_dict['sctask_number'] = ''
                circuit_dict['sctask_sys_id'] = ''
                # Keep the assigned_to from circuit record if no assignment record
            
            # For Ready for Enablement circuits, ensure editable fields are marked
            if circuit_dict['status_category'] == 'ready':
                circuit_dict['editable_fields'] = ['sctask_number', 'assigned_to']
            else:
                circuit_dict['editable_fields'] = []
            
            circuit_data.append(circuit_dict)
        
        # Filter customer action categories by 120 days (same logic as CSV version)
        customer_categories = ['customer_action', 'sponsor_approval', 'contact_required']
        
        filtered_data = []
        for circuit_dict in circuit_data:
            status_category = circuit_dict.get('status_category', '')
            
            if status_category in customer_categories:
                # Apply date filter
                date_str = circuit_dict.get('date_record_updated', '')
                if date_str:
                    try:
                        record_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        cutoff_date = datetime.now() - timedelta(days=120)
                        
                        if record_date >= cutoff_date:
                            filtered_data.append(circuit_dict)
                    except (ValueError, TypeError):
                        # Include if date parsing fails
                        filtered_data.append(circuit_dict)
                else:
                    # Include if no date
                    filtered_data.append(circuit_dict)
            else:
                # Include all non-customer-action circuits
                filtered_data.append(circuit_dict)
        
        # Calculate category counts
        category_counts = {}
        status_breakdown = {}
        substatus_breakdown = {}
        
        all_categories = ['enabled', 'ready', 'customer_action', 'sponsor_approval', 
                         'contact_required', 'construction', 'canceled', 'other']
        
        for category in all_categories:
            category_circuits = [c for c in filtered_data if c.get('status_category') == category]
            category_counts[category] = len(category_circuits)
            
            # Status breakdown
            status_counts = {}
            substatus_counts = {}
            
            for circuit in category_circuits:
                status = circuit.get('status', '')
                substatus = circuit.get('substatus', '')
                
                # Count statuses
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count substatuses (if not empty)
                if substatus and substatus.strip() and substatus.lower() != 'nan':
                    substatus_counts[substatus] = substatus_counts.get(substatus, 0) + 1
            
            status_breakdown[category] = status_counts
            substatus_breakdown[category] = substatus_counts
        
        # Calculate new sites (circuits added in last 30 days)
        new_sites_count = 0
        new_sites_list = []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            new_circuits = Circuit.query.filter(
                Circuit.created_at >= cutoff_date
            ).all()
            
            new_sites_set = set(circuit.site_name for circuit in new_circuits if circuit.site_name)
            new_sites_count = len(new_sites_set)
            new_sites_list = list(new_sites_set)
            
        except Exception as e:
            print(f"Warning: Could not calculate new sites: {e}")
        
        # Get new stores count
        new_stores_count = NewStore.query.filter_by(is_active=True).count()
        
        # Prepare dashboard response
        dashboard_stats = {
            "new_sites": new_sites_count,
            "new_stores": new_stores_count,  # Add new stores being built
            "enabled": category_counts.get('enabled', 0),
            "ready": category_counts.get('ready', 0),
            "customer_action": category_counts.get('customer_action', 0),
            "sponsor_approval": category_counts.get('sponsor_approval', 0),
            "contact_required": category_counts.get('contact_required', 0),
            "construction": category_counts.get('construction', 0),
            "canceled": category_counts.get('canceled', 0),
            "other": category_counts.get('other', 0),
            "total": len(filtered_data)
        }
        
        print(f"📊 Dashboard stats from database: {dashboard_stats}")
        
        return jsonify({
            "stats": dashboard_stats,
            "status_breakdown": status_breakdown,
            "substatus_breakdown": substatus_breakdown,
            "data": filtered_data,
            "new_sites_list": new_sites_list,
            "last_updated": datetime.now().strftime('%Y-%m-%d'),
            "data_source": "database"
        })
        
    except Exception as e:
        print(f"❌ Error generating dashboard data from database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@status_bp.route('/api/inflight-data', methods=['GET'])
def inflight_data():
    """
    API endpoint to get in-flight circuits data from database
    
    Processes circuit data to identify in-flight orders and categorizes them
    by workflow state for priority management.
    
    Returns:
        JSON response with in-flight circuit data
    """
    try:
        print("📊 Loading in-flight data from database")
        
        # Define in-flight statuses
        inflight_statuses = [
            'Information/Approval Needed From Sponsor',
            'Customer Action Required', 
            'Pending Scheduled Deployment',
            'Construction In Progress',
            'Ready for Enablement',
            'Construction Approved',
            'Order Placed',
            'Order Ready To Be Placed',
            'Prequal Required',
            'Jeopardy',
            'Customer Contacted With Activation Date',
            'Site Survey In Progress',
            'Installation Failed',
            'Waiting On Service Activation Date',
            'Rescheduled/Waiting On New Activation Date',
            'End-User Contact Required',
            'Provider Contact Required'
        ]
        
        # Get ALL current circuits, then filter for in-flight statuses (database contains only current state)
        # Also exclude Order Canceled status
        inflight_circuits = db.session.query(Circuit).filter(
            Circuit.status.in_(inflight_statuses),
            ~Circuit.status.ilike('%order canceled%')
        ).all()
        
        # Convert to dictionaries and add safe string conversion - MATCH CSV COLUMN NAMES
        circuit_data = []
        for circuit in inflight_circuits:
            # Map database fields to CSV column names for frontend compatibility
            circuit_dict = {
                'Site Name': safe_str(circuit.site_name or ''),
                'Site ID': safe_str(circuit.site_id or ''),
                'Circuit Purpose': safe_str(circuit.circuit_purpose or ''),
                'status': safe_str(circuit.status or ''),
                'substatus': safe_str(circuit.substatus or ''),
                'provider_name': safe_str(circuit.provider_name or ''),
                'details_ordered_service_speed': safe_str(circuit.details_ordered_service_speed or ''),
                'billing_monthly_cost': safe_str(circuit.billing_monthly_cost or ''),
                'date_record_updated': circuit.date_record_updated.strftime('%Y-%m-%d') if circuit.date_record_updated else '',
                'id': str(circuit.id),
                'ip_address_start': safe_str(circuit.ip_address_start or ''),
                'city': safe_str(circuit.city or ''),
                'state': safe_str(circuit.state or ''),
                'assigned_to': safe_str(circuit.assigned_to or ''),
                'sctask': safe_str(circuit.sctask or '')
            }
            
            circuit_data.append(circuit_dict)
        
        # Get status breakdown
        status_counts = {}
        for circuit_dict in circuit_data:
            status = circuit_dict.get('status', '')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Categorize circuits
        customer_action_statuses = [
            'Information/Approval Needed From Sponsor',
            'Customer Action Required',
            'End-User Contact Required',
            'Provider Contact Required'
        ]
        
        construction_statuses = [
            'Construction In Progress',
            'Construction Approved', 
            'Site Survey In Progress',
            'Installation Failed',
            'Pending Scheduled Deployment',
            'Customer Contacted With Activation Date',
            'Waiting On Service Activation Date'
        ]
        
        ready_statuses = [
            'Ready for Enablement'
        ]
        
        planning_statuses = [
            'Order Placed',
            'Order Ready To Be Placed',
            'Prequal Required'
        ]
        
        priority_statuses = [
            'Jeopardy',
            'Rescheduled/Waiting On New Activation Date'
        ]
        
        # Calculate category totals
        customer_action_total = sum(status_counts.get(status, 0) for status in customer_action_statuses)
        construction_total = sum(status_counts.get(status, 0) for status in construction_statuses)
        ready_total = sum(status_counts.get(status, 0) for status in ready_statuses)
        planning_total = sum(status_counts.get(status, 0) for status in planning_statuses)
        priority_total = sum(status_counts.get(status, 0) for status in priority_statuses)
        
        # Calculate stale circuits (updated more than 30 days ago)
        stale_count = 0
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for circuit_dict in circuit_data:
            date_str = circuit_dict.get('date_record_updated', '')
            if date_str:
                try:
                    record_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    if record_date < cutoff_date:
                        stale_count += 1
                except (ValueError, TypeError):
                    continue
        
        # Sort by priority
        def sort_priority(circuit_dict):
            status = circuit_dict.get('status', '').lower()
            if 'jeopardy' in status:
                return 0
            elif any(word in status for word in ['customer action', 'approval needed', 'contact required']):
                return 1
            elif 'ready for enablement' in status:
                return 2
            else:
                return 3
        
        circuit_data.sort(key=sort_priority)
        
        print(f"📊 In-flight data from database: {len(circuit_data)} total circuits")
        print(f"📊 Customer Action: {customer_action_total}, Construction: {construction_total}, Ready: {ready_total}")
        
        return jsonify({
            "total_inflight": len(circuit_data),
            "customer_action": customer_action_total,
            "construction": construction_total, 
            "ready": ready_total,
            "planning": planning_total,
            "priority": priority_total,
            "stale_circuits": stale_count,
            "status_breakdown": status_counts,
            "data": circuit_data,
            "last_updated": datetime.now().strftime('%Y-%m-%d'),
            "data_source": "database",
            "categories": {
                "customer_action": customer_action_statuses,
                "construction": construction_statuses,
                "ready": ready_statuses,
                "planning": planning_statuses,
                "priority": priority_statuses
            }
        })
        
    except Exception as e:
        print(f"❌ Error generating in-flight data from database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@status_bp.route('/api/save-assignment', methods=['POST'])
def save_assignment():
    """
    Save SCTASK number and assigned person for a circuit to database
    
    Request Body:
        JSON with assignment data:
        - site_name: Name of the site
        - site_id: ID of the site (optional)
        - circuit_purpose: Circuit purpose (optional)
        - sctask_number: SCTASK number
        - assigned_to: Person assigned to the task
        
    Returns:
        JSON response indicating success or error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        site_name = data.get('site_name')
        sctask_number = data.get('sctask_number')
        assigned_to = data.get('assigned_to')
        
        if not site_name:
            return jsonify({"error": "Site name is required"}), 400
        
        # Find or create circuit assignment
        assignment = CircuitAssignment.query.filter_by(
            site_name=site_name
        ).first()
        
        if assignment:
            # Update existing assignment
            assignment.sctask = sctask_number
            assignment.assigned_to = assigned_to
            assignment.assignment_date = datetime.utcnow()
        else:
            # Create new assignment
            assignment = CircuitAssignment(
                site_name=site_name,
                sctask=sctask_number,
                assigned_to=assigned_to,
                assignment_date=datetime.utcnow(),
                status='active',
                created_by='dashboard_user'
            )
            db.session.add(assignment)
        
        # Also update the circuit record if it exists
        circuit = Circuit.query.filter_by(site_name=site_name).first()
        if circuit:
            circuit.sctask = sctask_number
            circuit.assigned_to = assigned_to
            circuit.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        print(f"✅ Saved assignment to database for {site_name}: SCTASK={sctask_number}, Assigned={assigned_to}")
        
        return jsonify({
            "success": True,
            "message": f"Assignment saved for {site_name}",
            "data": assignment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving assignment to database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@status_bp.route('/api/get-assignments', methods=['GET'])
def get_assignments():
    """
    Get all circuit assignments from database
    
    Returns:
        JSON response with all assignment data
    """
    try:
        assignments = CircuitAssignment.query.all()
        
        assignments_dict = {}
        for assignment in assignments:
            # Create key similar to file-based version
            key = f"{assignment.site_name}||"  # Simplified key format
            assignments_dict[key] = {
                'site_name': assignment.site_name,
                'sctask_number': assignment.sctask or '',
                'assigned_to': assignment.assigned_to or '',
                'updated_at': assignment.assignment_date.isoformat() if assignment.assignment_date else '',
                'updated_by': assignment.created_by or 'database_user'
            }
        
        print(f"📊 Retrieved {len(assignments_dict)} circuit assignments from database")
        return jsonify({"assignments": assignments_dict})
        
    except Exception as e:
        print(f"❌ Error getting assignments from database: {e}")
        return jsonify({"assignments": {}})




