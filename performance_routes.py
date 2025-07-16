#!/usr/bin/env python3
"""
Performance monitoring routes for DSR Circuits
Provides web interface for viewing performance metrics
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging

# Create blueprint
performance_bp = Blueprint('performance', __name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'dsr_circuits',
    'user': 'dsr_user',
    'password': 'your_password_here'  # Update with actual password
}

def get_db_connection():
    """Get database connection with RealDictCursor"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@performance_bp.route('/performance')
def performance_dashboard():
    """Render performance monitoring dashboard"""
    return render_template('performance_dashboard.html')

@performance_bp.route('/api/performance/current')
def get_current_performance():
    """Get current performance metrics for all endpoints"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest metrics for each endpoint
        query = """
            WITH latest_metrics AS (
                SELECT DISTINCT ON (endpoint_name)
                    endpoint_name,
                    module_category,
                    query_execution_time_ms,
                    data_size_bytes,
                    data_rows_returned,
                    response_status,
                    error_message,
                    timestamp
                FROM performance_metrics
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                ORDER BY endpoint_name, timestamp DESC
            )
            SELECT 
                lm.*,
                ps.avg_response_time_ms,
                ps.p95_response_time_ms,
                ps.error_rate
            FROM latest_metrics lm
            LEFT JOIN performance_summary ps 
                ON lm.endpoint_name = ps.endpoint_name
            ORDER BY lm.module_category, lm.endpoint_name
        """
        
        cursor.execute(query)
        metrics = cursor.fetchall()
        
        # Group by module
        grouped_metrics = {}
        for metric in metrics:
            module = metric['module_category'] or 'other'
            if module not in grouped_metrics:
                grouped_metrics[module] = []
            grouped_metrics[module].append(dict(metric))
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'data': grouped_metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error fetching current performance: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@performance_bp.route('/api/performance/history')
def get_performance_history():
    """Get historical performance data for trending"""
    try:
        endpoint = request.args.get('endpoint', '')
        hours = int(request.args.get('hours', 24))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if endpoint:
            # Get history for specific endpoint
            query = """
                SELECT 
                    DATE_TRUNC('hour', timestamp) as hour,
                    endpoint_name,
                    AVG(query_execution_time_ms) as avg_response_time,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY query_execution_time_ms) as median_response_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY query_execution_time_ms) as p95_response_time,
                    MAX(query_execution_time_ms) as max_response_time,
                    COUNT(*) as request_count,
                    SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as error_count
                FROM performance_metrics
                WHERE endpoint_name = %s
                    AND timestamp > NOW() - INTERVAL '%s hours'
                GROUP BY DATE_TRUNC('hour', timestamp), endpoint_name
                ORDER BY hour DESC
            """
            cursor.execute(query, (endpoint, hours))
        else:
            # Get aggregate history
            query = """
                SELECT 
                    DATE_TRUNC('hour', timestamp) as hour,
                    module_category,
                    AVG(query_execution_time_ms) as avg_response_time,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY query_execution_time_ms) as median_response_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY query_execution_time_ms) as p95_response_time,
                    COUNT(*) as request_count,
                    SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as error_count
                FROM performance_metrics
                WHERE timestamp > NOW() - INTERVAL '%s hours'
                GROUP BY DATE_TRUNC('hour', timestamp), module_category
                ORDER BY hour DESC, module_category
            """
            cursor.execute(query, (hours,))
        
        results = cursor.fetchall()
        
        # Convert to JSON-serializable format
        history = []
        for row in results:
            data = dict(row)
            data['hour'] = data['hour'].isoformat() if data['hour'] else None
            history.append(data)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'data': history,
            'endpoint': endpoint,
            'hours': hours
        })
        
    except Exception as e:
        logging.error(f"Error fetching performance history: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@performance_bp.route('/api/performance/alerts')
def get_performance_alerts():
    """Get current performance alerts and anomalies"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get alerts from the view
        query = """
            SELECT 
                endpoint_name,
                recent_avg,
                baseline_avg,
                percent_change,
                alert_status
            FROM performance_alerts
            WHERE alert_status IN ('WARNING', 'DEGRADED')
            ORDER BY percent_change DESC
        """
        
        cursor.execute(query)
        alerts = cursor.fetchall()
        
        # Get recent errors
        error_query = """
            SELECT 
                endpoint_name,
                response_status,
                error_message,
                timestamp
            FROM performance_metrics
            WHERE response_status >= 400
                AND timestamp > NOW() - INTERVAL '1 hour'
            ORDER BY timestamp DESC
            LIMIT 20
        """
        
        cursor.execute(error_query)
        recent_errors = cursor.fetchall()
        
        # Convert to JSON-serializable format
        alerts_data = []
        for alert in alerts:
            data = dict(alert)
            alerts_data.append(data)
        
        errors_data = []
        for error in recent_errors:
            data = dict(error)
            data['timestamp'] = data['timestamp'].isoformat() if data['timestamp'] else None
            errors_data.append(data)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'alerts': alerts_data,
            'recent_errors': errors_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error fetching performance alerts: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@performance_bp.route('/api/performance/summary')
def get_performance_summary():
    """Get overall performance summary statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get overall stats
        query = """
            SELECT 
                COUNT(DISTINCT endpoint_name) as total_endpoints,
                COUNT(*) as total_requests_24h,
                AVG(query_execution_time_ms) as avg_response_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY query_execution_time_ms) as median_response_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY query_execution_time_ms) as p95_response_time,
                SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as error_count_24h,
                ROUND(100.0 * SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate
            FROM performance_metrics
            WHERE timestamp > NOW() - INTERVAL '24 hours'
        """
        
        cursor.execute(query)
        overall = cursor.fetchone()
        
        # Get module breakdown
        module_query = """
            SELECT 
                module_category,
                COUNT(DISTINCT endpoint_name) as endpoint_count,
                COUNT(*) as request_count,
                AVG(query_execution_time_ms) as avg_response_time,
                SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as error_count
            FROM performance_metrics
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY module_category
            ORDER BY request_count DESC
        """
        
        cursor.execute(module_query)
        modules = cursor.fetchall()
        
        # Get slowest endpoints
        slow_query = """
            SELECT 
                endpoint_name,
                module_category,
                AVG(query_execution_time_ms) as avg_response_time,
                MAX(query_execution_time_ms) as max_response_time,
                COUNT(*) as request_count
            FROM performance_metrics
            WHERE timestamp > NOW() - INTERVAL '24 hours'
                AND response_status = 200
            GROUP BY endpoint_name, module_category
            HAVING COUNT(*) > 5
            ORDER BY avg_response_time DESC
            LIMIT 10
        """
        
        cursor.execute(slow_query)
        slowest = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'overall': dict(overall) if overall else {},
            'modules': [dict(m) for m in modules],
            'slowest_endpoints': [dict(s) for s in slowest],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error fetching performance summary: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500