#!/usr/bin/env python3
"""
Update reports.py APIs to read from database instead of JSON files
"""

import os

# Read the current reports.py file
with open('/usr/local/bin/Main/reports.py', 'r') as f:
    content = f.read()

# Replace ready_queue_data function with database version
old_ready_queue = '''@reports_bp.route('/api/ready-queue-data', methods=['GET'])
def ready_queue_data():
    """
    Get daily ready queue statistics with CSV FALLBACK for full historical data
    
    Tries JSON cache first, falls back to CSV processing for complete history.
    
    Query Parameters:
        days (int): Number of days to analyze 
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        (no parameters = all available data)
    
    Returns:
        JSON response with daily ready queue data
    """
    try:
        # Get parameters
        days = request.args.get('days', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        use_csv_fallback = False
        
        # Try JSON cache first
        master_data = load_json_safely(ENABLEMENT_DATA_FILE, {})
        
        # Check if JSON cache has sufficient data
        if master_data and 'daily_summaries' in master_data:
            json_start_date = master_data.get('date_range', {}).get('start', '')
            
            # Determine if we need CSV fallback
            if not days and not start_date and not end_date:
                # User wants ALL data - check if JSON has complete history
                use_csv_fallback = True  # Always use CSV for complete history
                logging.info("Using CSV fallback for complete historical data")
            elif start_date:
                # Check if requested start date is before JSON cache starts
                try:
                    req_start = datetime.strptime(start_date, '%Y-%m-%d')
                    json_start = datetime.strptime(json_start_date, '%Y-%m-%d') if json_start_date else datetime.now()
                    if req_start < json_start:
                        use_csv_fallback = True
                        logging.info(f"Using CSV fallback: requested start {start_date} before JSON start {json_start_date}")
                except:
                    pass
        else:
            use_csv_fallback = True
            logging.info("No JSON cache available - using CSV fallback")
        
        if use_csv_fallback:
            # Use daily JSON files for complete historical data
            logging.info("Processing daily JSON files for ready queue data")
            json_data = process_daily_json_files_for_historical_data(start_date, end_date, days)
            
            if json_data:
                queue_data = json_data['daily_queue_data']
                
                # Calculate summary statistics
                total_ready = sum(d.get('ready_count', 0) for d in queue_data)
                avg_queue_size = total_ready / len(queue_data) if queue_data else 0
                total_closed = sum(d.get('closed_from_ready', 0) for d in queue_data)
                
                return jsonify({
                    'success': True,
                    'data': queue_data,
                    'summary': {
                        'average_queue_size': round(avg_queue_size, 1),
                        'total_ready': total_ready,
                        'total_closed_from_ready': total_closed,
                        'days_analyzed': len(queue_data)
                    },
                    'data_source': 'daily_json_historical_processing',
                    'generated_at': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'error': 'No historical data available from daily JSON processing',
                    'success': False
                }), 404
        
        else:
            # Use optimized JSON cache
            queue_data = []
            for daily_summary in master_data['daily_summaries']:
                if 'enablement_data' in daily_summary:
                    enablement = daily_summary['enablement_data']
                    queue_data.append({
                        'date': enablement['date'],
                        'formatted_date': format_date_for_display(enablement['date']),
                        'ready_count': enablement.get('ready_for_enablement_count', 0),
                        'closed_from_ready': enablement.get('total_enabled', 0),
                        'total_circuits': daily_summary.get('total_circuits', 0)
                    })
            
            # Sort by date
            queue_data.sort(key=lambda x: x['date'])
            
            # Filter by date range
            filtered_data = filter_data_by_date_range(queue_data, start_date, end_date, days)
            
            # Calculate summary statistics
            total_ready = sum(d.get('ready_count', 0) for d in filtered_data)
            avg_queue_size = total_ready / len(filtered_data) if filtered_data else 0
            total_closed = sum(d.get('closed_from_ready', 0) for d in filtered_data)
            
            return jsonify({
                'success': True,
                'data': filtered_data,
                'summary': {
                    'average_queue_size': round(avg_queue_size, 1),
                    'total_ready': total_ready,
                    'total_closed_from_ready': total_closed,
                    'days_analyzed': len(filtered_data)
                },
                'data_source': 'optimized_json',
                'generated_at': datetime.now().isoformat()
            })
        
    except Exception as e:
        logging.error(f"Error in ready_queue_data: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500'''

new_ready_queue = '''@reports_bp.route('/api/ready-queue-data', methods=['GET'])
def ready_queue_data():
    """
    Get daily ready queue statistics from DATABASE
    
    Query Parameters:
        days (int): Number of days to analyze 
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        (no parameters = all available data)
    
    Returns:
        JSON response with daily ready queue data
    """
    from config import Config
    import psycopg2
    import re
    
    try:
        # Connect to database
        match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
        user, password, host, port, database = match.groups()
        
        conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
        cursor = conn.cursor()
        
        # Get ready queue data and enablements data
        cursor.execute("""
            SELECT 
                rq.summary_date,
                rq.ready_count,
                COALESCE(es.daily_count, 0) as closed_from_ready
            FROM ready_queue_daily rq
            LEFT JOIN enablement_summary es ON rq.summary_date = es.summary_date
            ORDER BY rq.summary_date ASC
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert to API format
        queue_data = []
        total_circuits = 4171  # Current circuit count
        
        for summary_date, ready_count, closed_from_ready in results:
            queue_data.append({
                'date': summary_date.strftime('%Y-%m-%d'),
                'formatted_date': summary_date.strftime('%b %d'),
                'ready_count': ready_count,
                'closed_from_ready': closed_from_ready,
                'total_circuits': total_circuits
            })
        
        # Calculate summary statistics
        total_ready = sum(d.get('ready_count', 0) for d in queue_data)
        avg_queue_size = total_ready / len(queue_data) if queue_data else 0
        total_closed = sum(d.get('closed_from_ready', 0) for d in queue_data)
        
        return jsonify({
            'success': True,
            'data': queue_data,
            'summary': {
                'average_queue_size': round(avg_queue_size, 1),
                'total_ready': total_ready,
                'total_closed_from_ready': total_closed,
                'days_analyzed': len(queue_data)
            },
            'data_source': 'database',
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Database error in ready_queue_data: {str(e)}")
        return jsonify({
            'error': f'Database error: {str(e)}',
            'success': False
        }), 500'''

# Replace the function in the content
if old_ready_queue in content:
    content = content.replace(old_ready_queue, new_ready_queue)
    print("✅ Updated ready_queue_data function")
else:
    print("❌ Could not find ready_queue_data function to replace")

# Write the updated content back
with open('/usr/local/bin/Main/reports.py', 'w') as f:
    f.write(content)

print("Updated reports.py with database-driven ready queue API")