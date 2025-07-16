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
import os
import glob

# Create Blueprint
status_bp = Blueprint('status', __name__)

def get_latest_tracking_file_date():
    """Get the date of the latest tracking CSV file"""
    try:
        tracking_files = glob.glob('/var/www/html/circuitinfo/tracking_data_*.csv')
        if tracking_files:
            latest_file = max(tracking_files, key=os.path.getmtime)
            # Extract date from filename (tracking_data_YYYY-MM-DD.csv)
            filename = os.path.basename(latest_file)
            date_part = filename.replace('tracking_data_', '').replace('.csv', '')
            # Get file modification time
            mtime = os.path.getmtime(latest_file)
            file_time = datetime.fromtimestamp(mtime)
            return {
                "date": date_part,
                "time": file_time.strftime('%I:%M:%S %p'),
                "full": file_time.strftime('%Y-%m-%d %I:%M:%S %p')
            }
    except Exception as e:
        print(f"Error getting tracking file date: {e}")
    return None

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

@status_bp.route('/api/dashboard-summary', methods=['GET'])
def dashboard_summary():
    """
    Fast API endpoint for dashboard summary stats only (no full data)
    Returns just counts and breakdowns for quick page load
    """
    try:
        import time
        import json
        from utils import categorize_status
        start_time = time.time()
        
        # Get only counts for fast loading
        total_circuits = db.session.query(Circuit).filter(
            ~Circuit.status.ilike('%order canceled%')
        ).count()
        
        if total_circuits == 0:
            return jsonify({"error": "No circuit data found in database"}), 400
        
        # Get status counts directly from database
        status_counts = db.session.query(
            Circuit.status,
            func.count(Circuit.id)
        ).filter(
            ~Circuit.status.ilike('%order canceled%')
        ).group_by(Circuit.status).all()
        
        # Process status breakdown without loading full data
        status_breakdown = {}
        substatus_breakdown = {}
        
        for status, count in status_counts:
            category = categorize_status(status)
            if category not in status_breakdown:
                status_breakdown[category] = 0
            status_breakdown[category] += count
            
            # Add to substatus as well
            if category not in substatus_breakdown:
                substatus_breakdown[category] = {}
            if status not in substatus_breakdown[category]:
                substatus_breakdown[category][status] = 0
            substatus_breakdown[category][status] += count
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        result = {
            "stats": {
                "total_circuits": total_circuits,
                "processing_time": round(processing_time, 3)
            },
            "status_breakdown": status_breakdown,
            "substatus_breakdown": substatus_breakdown,
            "last_updated": datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            "data_summary": f"Summary only - {total_circuits} circuits",
            "tracking_file_date": get_latest_tracking_file_date()
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Dashboard summary error: {str(e)}")
        return jsonify({"error": f"Failed to load dashboard summary: {str(e)}"}), 500

@status_bp.route('/api/dashboard-data', methods=['GET'])
def dashboard_data():
    """
    API endpoint to get dashboard data from database
    
    Optimized version that uses database aggregation for counts and
    only loads full circuit data when needed for detailed display.
    
    Returns:
        JSON response with dashboard statistics and data
    """
    try:
        import time
        import json
        from utils import categorize_status
        start_time = time.time()
        print("📊 Loading dashboard data from database (optimized)")
        
        # Try Redis cache first
        cache_key = "dashboard_data_v2"
        try:
            from config import get_redis_connection
            redis_conn = get_redis_connection()
            if redis_conn:
                cached_result = redis_conn.get(cache_key)
                if cached_result:
                    print("📊 Dashboard: Cache hit - returning cached data")
                    return jsonify(json.loads(cached_result))
        except Exception as e:
            print(f"Redis cache error: {e}")
            redis_conn = None
        
        # First, get fast aggregated counts using database queries
        total_circuits = db.session.query(Circuit).filter(
            ~Circuit.status.ilike('%order canceled%')
        ).count()
        
        if total_circuits == 0:
            return jsonify({"error": "No circuit data found in database"}), 400
        
        # Get status counts directly from database
        status_counts = db.session.query(
            Circuit.status,
            func.count(Circuit.id)
        ).filter(
            ~Circuit.status.ilike('%order canceled%')
        ).group_by(Circuit.status).all()
        
        # Get substatus counts
        substatus_counts = db.session.query(
            Circuit.substatus,
            func.count(Circuit.id)
        ).filter(
            ~Circuit.status.ilike('%order canceled%'),
            Circuit.substatus.isnot(None),
            Circuit.substatus != '',
            ~Circuit.substatus.ilike('nan')
        ).group_by(Circuit.substatus).all()
        
        # Calculate new sites (circuits added in last 30 days)
        new_sites_count = 0
        new_sites_list = []
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            new_sites_query = db.session.query(
                Circuit.site_name
            ).filter(
                Circuit.created_at >= cutoff_date,
                Circuit.site_name.isnot(None)
            ).distinct()
            
            new_sites_list = [row[0] for row in new_sites_query.all()]
            new_sites_count = len(new_sites_list)
        except Exception as e:
            print(f"Warning: Could not calculate new sites: {e}")
        
        # Get new stores count
        new_stores_count = NewStore.query.filter_by(is_active=True).count()
        
        query_time = time.time() - start_time
        print(f"⏱️ Database aggregation queries took {query_time:.3f} seconds")
        
        # Process status categorization using the fast counts
        category_counts = {
            'enabled': 0, 'ready': 0, 'customer_action': 0, 'sponsor_approval': 0,
            'contact_required': 0, 'construction': 0, 'canceled': 0, 'other': 0
        }
        
        status_breakdown = {}
        
        # Categorize each status and build breakdown
        for status, count in status_counts:
            if not status:
                continue
                
            category = categorize_status(status)
            category_counts[category] = category_counts.get(category, 0) + count
            
            if category not in status_breakdown:
                status_breakdown[category] = {}
            status_breakdown[category][status] = count
        
        # Fix: For "ready" category, count unique site IDs instead of circuit records
        if 'ready' in category_counts and category_counts['ready'] > 0:
            ready_site_count = db.session.query(Circuit.site_id).filter(
                Circuit.status.in_([status for status, count in status_counts if categorize_status(status) == 'ready']),
                ~Circuit.status.ilike('%order canceled%')
            ).distinct().count()
            category_counts['ready'] = ready_site_count
        
        # Build substatus breakdown by category
        substatus_breakdown = {}
        for category in category_counts.keys():
            substatus_breakdown[category] = {}
        
        # For substatus, we need to get the circuits to know their categories
        # But we'll do this more efficiently with a join
        substatus_with_status = db.session.query(
            Circuit.status,
            Circuit.substatus,
            func.count(Circuit.id)
        ).filter(
            ~Circuit.status.ilike('%order canceled%'),
            Circuit.substatus.isnot(None),
            Circuit.substatus != '',
            ~Circuit.substatus.ilike('nan')
        ).group_by(Circuit.status, Circuit.substatus).all()
        
        for status, substatus, count in substatus_with_status:
            if status and substatus:
                category = categorize_status(status)
                if category not in substatus_breakdown:
                    substatus_breakdown[category] = {}
                substatus_breakdown[category][substatus] = substatus_breakdown[category].get(substatus, 0) + count
        
        # Now load detailed circuit data more efficiently
        # Apply customer action date filter at database level
        cutoff_date_120 = datetime.now() - timedelta(days=120)
        
        # Load circuits with conditional filtering for customer action categories
        customer_categories = ['customer_action', 'sponsor_approval', 'contact_required']
        customer_statuses = []
        for status, count in status_counts:
            if status and categorize_status(status) in customer_categories:
                customer_statuses.append(status)
        
        # Build query to get circuits with date filtering for customer action
        circuits_query = db.session.query(Circuit).filter(
            ~Circuit.status.ilike('%order canceled%')
        )
        
        if customer_statuses:
            # For customer action statuses, apply date filter
            circuits_query = circuits_query.filter(
                or_(
                    ~Circuit.status.in_(customer_statuses),  # Non-customer action circuits
                    and_(
                        Circuit.status.in_(customer_statuses),  # Customer action circuits
                        or_(
                            Circuit.date_record_updated >= cutoff_date_120,  # Recent updates
                            Circuit.date_record_updated.is_(None)  # Or no date
                        )
                    )
                )
            )
        
        circuits = circuits_query.all()
        
        # Get assignment data for all circuits to merge with circuit data
        assignment_data = {}
        assignments = CircuitAssignment.query.filter_by(status='active').all()
        for assignment in assignments:
            assignment_data[assignment.site_name] = {
                'sctask': assignment.sctask or '',
                'assigned_to': assignment.assigned_to or ''
            }
        
        # Convert to list of dictionaries - MATCH CSV COLUMN NAMES
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
            
            # Merge assignment data from circuit_assignments table (takes priority)
            site_assignment = assignment_data.get(circuit.site_name, {})
            if site_assignment.get('assigned_to'):
                circuit_dict['assigned_to'] = safe_str(site_assignment['assigned_to'])
            if site_assignment.get('sctask'):
                circuit_dict['sctask'] = safe_str(site_assignment['sctask'])
            
            # Add status categorization
            circuit_dict['status_category'] = categorize_status(circuit_dict.get('status', ''))
            
            # For Ready for Enablement circuits, ensure editable fields are marked
            if circuit_dict['status_category'] == 'ready':
                circuit_dict['editable_fields'] = ['sctask_number', 'assigned_to']
            else:
                circuit_dict['editable_fields'] = []
            
            # Basic assignment data - prioritize assignment table data
            circuit_dict['sctask_number'] = circuit_dict['sctask']  # Use merged SCTASK data
            circuit_dict['sctask_sys_id'] = ''  # Not used
            
            circuit_data.append(circuit_dict)
        
        # Note: Date filtering was already applied at database level for customer action categories
        
        # Prepare dashboard response using the optimized counts
        dashboard_stats = {
            "new_sites": new_sites_count,
            "new_stores": new_stores_count,
            "enabled": category_counts.get('enabled', 0),
            "ready": category_counts.get('ready', 0),
            "customer_action": category_counts.get('customer_action', 0),
            "sponsor_approval": category_counts.get('sponsor_approval', 0),
            "contact_required": category_counts.get('contact_required', 0),
            "construction": category_counts.get('construction', 0),
            "canceled": category_counts.get('canceled', 0),
            "other": category_counts.get('other', 0),
            "total": len(circuit_data)
        }
        
        processing_time = time.time() - start_time
        print(f"⏱️ Total dashboard processing took {processing_time:.3f} seconds for {len(circuit_data)} circuits")
        
        print(f"📊 Dashboard stats from database: {dashboard_stats}")
        
        result = {
            "stats": dashboard_stats,
            "status_breakdown": status_breakdown,
            "substatus_breakdown": substatus_breakdown,
            "data": circuit_data,
            "new_sites_list": new_sites_list,
            "last_updated": datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            "data_source": "database-optimized",
            "query_time_ms": int(processing_time * 1000),
            "tracking_file_date": get_latest_tracking_file_date()
        }
        
        # Cache the result for 2 minutes (dashboard data changes frequently)
        if redis_conn:
            try:
                redis_conn.setex(cache_key, 120, json.dumps(result))
                print("📊 Dashboard: Cached result for 2 minutes")
            except Exception as e:
                print(f"Redis cache set error: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error generating dashboard data from database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@status_bp.route('/api/dashboard-category/<category>', methods=['GET'])
def dashboard_category_data(category):
    """
    Load specific category data on-demand for faster initial page load
    """
    try:
        from utils import categorize_status
        
        # Load only circuits for the requested category
        circuits = db.session.query(Circuit).filter(
            ~Circuit.status.ilike('%order canceled%')
        ).all()
        
        category_circuits = []
        for circuit in circuits:
            circuit_category = categorize_status(circuit.status or '')
            if circuit_category == category:
                # Get assignment data
                assignment = db.session.query(CircuitAssignment).filter_by(
                    site_name=circuit.site_name
                ).first()
                
                circuit_data = circuit.to_dict()
                if assignment:
                    circuit_data['sctask'] = assignment.sctask
                    circuit_data['assigned_to'] = assignment.assigned_to
                
                category_circuits.append(circuit_data)
        
        return jsonify({
            "category": category,
            "data": category_circuits,
            "count": len(category_circuits)
        })
        
    except Exception as e:
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
            "last_updated": datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            "data_source": "database",
            "tracking_file_date": get_latest_tracking_file_date(),
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
            # Update existing assignment - only update fields that were provided
            if sctask_number is not None:
                assignment.sctask = sctask_number
            if assigned_to is not None:
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
            if sctask_number is not None:
                circuit.sctask = sctask_number
            if assigned_to is not None:
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




