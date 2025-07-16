#!/usr/bin/env python3
"""
Performance monitoring blueprint for DSR Circuits
Displays API endpoint performance metrics and trends
"""

from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import json

from models import db, PerformanceMetric

# Create blueprint
performance_bp = Blueprint('performance', __name__)

@performance_bp.route('/performance')
def performance_dashboard():
    """Main performance monitoring dashboard"""
    return render_template('performance_dashboard.html')

@performance_bp.route('/api/performance/current')
def get_current_performance():
    """Get current performance metrics for all endpoints"""
    try:
        # Get metrics from last hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        # Get average performance by endpoint
        metrics = db.session.query(
            PerformanceMetric.endpoint_name,
            PerformanceMetric.module_category,
            func.avg(PerformanceMetric.query_execution_time_ms).label('avg_time'),
            func.max(PerformanceMetric.query_execution_time_ms).label('max_time'),
            func.min(PerformanceMetric.query_execution_time_ms).label('min_time'),
            func.count().label('sample_count'),
            func.avg(PerformanceMetric.data_size_bytes).label('avg_size'),
            func.sum(func.cast(PerformanceMetric.response_status != 200, db.Integer)).label('error_count')
        ).filter(
            PerformanceMetric.timestamp >= cutoff,
            PerformanceMetric.is_monitoring == True
        ).group_by(
            PerformanceMetric.endpoint_name,
            PerformanceMetric.module_category
        ).all()
        
        # Format results
        results = []
        for metric in metrics:
            error_rate = (metric.error_count / metric.sample_count * 100) if metric.sample_count > 0 else 0
            
            results.append({
                'endpoint': metric.endpoint_name,
                'module': metric.module_category or 'unknown',
                'avg_time': round(metric.avg_time, 2) if metric.avg_time else 0,
                'max_time': round(metric.max_time, 2) if metric.max_time else 0,
                'min_time': round(metric.min_time, 2) if metric.min_time else 0,
                'samples': metric.sample_count,
                'avg_size_kb': round(metric.avg_size / 1024, 2) if metric.avg_size else 0,
                'error_rate': round(error_rate, 2)
            })
        
        # Sort by average time descending
        results.sort(key=lambda x: x['avg_time'], reverse=True)
        
        return jsonify({
            'success': True,
            'metrics': results,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/api/performance/history/<endpoint>')
def get_endpoint_history(endpoint):
    """Get historical performance data for a specific endpoint"""
    try:
        # Get time range from query params
        hours = int(request.args.get('hours', 24))
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Get hourly averages
        history = db.session.query(
            func.date_trunc('hour', PerformanceMetric.timestamp).label('hour'),
            func.avg(PerformanceMetric.query_execution_time_ms).label('avg_time'),
            func.max(PerformanceMetric.query_execution_time_ms).label('max_time'),
            func.count().label('sample_count'),
            func.avg(PerformanceMetric.data_size_bytes).label('avg_size')
        ).filter(
            PerformanceMetric.endpoint_name == endpoint,
            PerformanceMetric.timestamp >= cutoff,
            PerformanceMetric.response_status == 200
        ).group_by(
            func.date_trunc('hour', PerformanceMetric.timestamp)
        ).order_by('hour').all()
        
        # Format for Chart.js
        labels = []
        avg_times = []
        max_times = []
        data_sizes = []
        
        for record in history:
            labels.append(record.hour.strftime('%Y-%m-%d %H:00'))
            avg_times.append(round(record.avg_time, 2) if record.avg_time else 0)
            max_times.append(round(record.max_time, 2) if record.max_time else 0)
            data_sizes.append(round(record.avg_size / 1024, 2) if record.avg_size else 0)
        
        return jsonify({
            'success': True,
            'endpoint': endpoint,
            'labels': labels,
            'datasets': {
                'avg_time': avg_times,
                'max_time': max_times,
                'data_size_kb': data_sizes
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/api/performance/anomalies')
def get_performance_anomalies():
    """Get recent performance anomalies"""
    try:
        # Calculate baseline stats for last 7 days
        baseline_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        
        # Get baseline statistics per endpoint
        baselines = db.session.query(
            PerformanceMetric.endpoint_name,
            func.avg(PerformanceMetric.query_execution_time_ms).label('avg_time'),
            func.stddev(PerformanceMetric.query_execution_time_ms).label('std_dev')
        ).filter(
            PerformanceMetric.timestamp >= baseline_cutoff,
            PerformanceMetric.response_status == 200
        ).group_by(
            PerformanceMetric.endpoint_name
        ).all()
        
        anomalies = []
        
        # Check recent metrics against baselines
        for baseline in baselines:
            if baseline.std_dev and baseline.std_dev > 0:
                # Define anomaly as > 2 standard deviations from mean
                threshold = baseline.avg_time + (2 * baseline.std_dev)
                
                # Find recent slow queries
                slow_queries = PerformanceMetric.query.filter(
                    PerformanceMetric.endpoint_name == baseline.endpoint_name,
                    PerformanceMetric.timestamp >= recent_cutoff,
                    PerformanceMetric.query_execution_time_ms > threshold
                ).all()
                
                for query in slow_queries:
                    deviation = (query.query_execution_time_ms - baseline.avg_time) / baseline.std_dev
                    
                    anomalies.append({
                        'endpoint': query.endpoint_name,
                        'timestamp': query.timestamp.isoformat(),
                        'execution_time': query.query_execution_time_ms,
                        'baseline_avg': round(baseline.avg_time, 2),
                        'threshold': round(threshold, 2),
                        'deviation': round(deviation, 2),
                        'status': query.response_status,
                        'error': query.error_message
                    })
        
        # Sort by deviation (most extreme first)
        anomalies.sort(key=lambda x: abs(x['deviation']), reverse=True)
        
        return jsonify({
            'success': True,
            'anomalies': anomalies[:20]  # Limit to top 20
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/api/performance/summary')
def get_performance_summary():
    """Get overall performance summary statistics"""
    try:
        # Time ranges
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        day_ago = datetime.utcnow() - timedelta(days=1)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get stats for different time periods
        summary = {}
        
        for period_name, cutoff in [('hour', hour_ago), ('day', day_ago), ('week', week_ago)]:
            stats = db.session.query(
                func.avg(PerformanceMetric.query_execution_time_ms).label('avg_time'),
                func.percentile_cont(0.5).within_group(
                    PerformanceMetric.query_execution_time_ms
                ).label('median_time'),
                func.percentile_cont(0.95).within_group(
                    PerformanceMetric.query_execution_time_ms
                ).label('p95_time'),
                func.count().label('total_requests'),
                func.sum(func.cast(PerformanceMetric.response_status != 200, db.Integer)).label('error_count'),
                func.avg(PerformanceMetric.data_size_bytes).label('avg_size')
            ).filter(
                PerformanceMetric.timestamp >= cutoff,
                PerformanceMetric.is_monitoring == True
            ).first()
            
            error_rate = (stats.error_count / stats.total_requests * 100) if stats.total_requests > 0 else 0
            
            summary[period_name] = {
                'avg_time': round(stats.avg_time, 2) if stats.avg_time else 0,
                'median_time': round(stats.median_time, 2) if stats.median_time else 0,
                'p95_time': round(stats.p95_time, 2) if stats.p95_time else 0,
                'total_requests': stats.total_requests or 0,
                'error_rate': round(error_rate, 2),
                'avg_size_kb': round(stats.avg_size / 1024, 2) if stats.avg_size else 0
            }
        
        # Get slowest endpoints
        slowest = db.session.query(
            PerformanceMetric.endpoint_name,
            func.avg(PerformanceMetric.query_execution_time_ms).label('avg_time')
        ).filter(
            PerformanceMetric.timestamp >= day_ago,
            PerformanceMetric.response_status == 200
        ).group_by(
            PerformanceMetric.endpoint_name
        ).order_by(
            func.avg(PerformanceMetric.query_execution_time_ms).desc()
        ).limit(5).all()
        
        summary['slowest_endpoints'] = [
            {
                'endpoint': s.endpoint_name,
                'avg_time': round(s.avg_time, 2)
            } for s in slowest
        ]
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500