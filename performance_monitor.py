#!/usr/bin/env python3
"""
Performance monitoring script for DSR Circuits API endpoints
Runs hourly to collect performance metrics for all key endpoints
"""

import os
import sys
import json
import time
import requests
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from models import db, PerformanceMetric
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/performance-monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Base URL for API calls
BASE_URL = "http://localhost:5052"

# Endpoints to monitor
ENDPOINTS = [
    # Dashboard endpoints
    {
        'name': '/api/dashboard-data',
        'module': 'dashboard',
        'params': {}
    },
    {
        'name': '/api/inflight-data',
        'module': 'dashboard',
        'params': {}
    },
    
    # Historical endpoints
    {
        'name': '/api/circuit-changelog',
        'module': 'historical',
        'method': 'POST',
        'form_data': {'timePeriod': 'last_week'}
    },
    
    # Inventory endpoints
    {
        'name': '/api/inventory-summary',
        'module': 'inventory',
        'params': {}
    },
    {
        'name': '/api/inventory-details',
        'module': 'inventory',
        'params': {'limit': '100'}
    },
    
    # Reports endpoints
    {
        'name': '/api/daily-enablement-data',
        'module': 'reports',
        'params': {}
    },
    
    # New stores endpoints
    {
        'name': '/api/new-stores',
        'module': 'new_stores',
        'params': {}
    },
    {
        'name': '/api/new-store-circuits-with-tod',
        'module': 'new_stores',
        'params': {}
    },
    
    # Circuit search endpoints (various parameters)
    {
        'name': '/api/circuits/search',
        'module': 'circuits',
        'params': {'site_name': 'Phoenix', 'limit': '50'}
    },
    {
        'name': '/api/circuits/search',
        'module': 'circuits',
        'params': {'status': 'Enabled', 'limit': '100'}
    },
    {
        'name': '/api/circuits/search',
        'module': 'circuits',
        'params': {'provider': 'AT&T', 'limit': '50'}
    },
    
    # Network endpoints
    {
        'name': '/api/networks',
        'module': 'networks',
        'params': {}
    },
    
    # System health endpoints
    {
        'name': '/api/health',
        'module': 'system',
        'params': {}
    },
    {
        'name': '/api/stats/quick',
        'module': 'system',
        'params': {}
    }
]

def measure_endpoint(endpoint):
    """Measure the performance of a single endpoint"""
    url = BASE_URL + endpoint['name']
    method = endpoint.get('method', 'GET')
    params = endpoint.get('params', {})
    form_data = endpoint.get('form_data', {})
    
    # Add query string if GET parameters exist
    if method == 'GET' and params:
        url += '?' + urlencode(params)
    
    # Store parameters for logging
    all_params = {**params, **form_data} if form_data else params
    
    metric = {
        'endpoint_name': endpoint['name'],
        'endpoint_method': method,
        'endpoint_params': json.dumps(all_params) if all_params else None,
        'module_category': endpoint['module'],
        'is_monitoring': True
    }
    
    try:
        # Measure execution time
        start_time = time.time()
        
        if method == 'POST' and form_data:
            response = requests.post(url, data=form_data, timeout=30)
        else:
            response = requests.get(url, timeout=30)
            
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        metric['query_execution_time_ms'] = int(execution_time)
        metric['response_status'] = response.status_code
        
        # Calculate data size
        metric['data_size_bytes'] = len(response.content)
        
        # Try to parse JSON and count records
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Count rows based on endpoint type
                if isinstance(data, list):
                    metric['data_rows_returned'] = len(data)
                elif isinstance(data, dict):
                    # Look for common keys that contain lists
                    for key in ['circuits', 'inventory', 'rules', 'stores', 'data', 'results']:
                        if key in data and isinstance(data[key], list):
                            metric['data_rows_returned'] = len(data[key])
                            break
                    else:
                        # If no list found, count dict keys
                        metric['data_rows_returned'] = len(data)
                else:
                    metric['data_rows_returned'] = 1
                    
            except json.JSONDecodeError:
                metric['data_rows_returned'] = 0
                
        logger.info(f"Measured {endpoint['name']}: {execution_time:.2f}ms, {metric['data_size_bytes']} bytes")
        
    except requests.Timeout:
        metric['response_status'] = 0
        metric['error_message'] = 'Request timeout (30s)'
        metric['query_execution_time_ms'] = 30000
        logger.error(f"Timeout for {endpoint['name']}")
        
    except requests.RequestException as e:
        metric['response_status'] = 0
        metric['error_message'] = str(e)
        metric['query_execution_time_ms'] = 0
        logger.error(f"Error for {endpoint['name']}: {e}")
        
    except Exception as e:
        metric['response_status'] = 0
        metric['error_message'] = f"Unexpected error: {str(e)}"
        metric['query_execution_time_ms'] = 0
        logger.error(f"Unexpected error for {endpoint['name']}: {e}")
    
    return metric

def cleanup_old_metrics(days=90):
    """Remove metrics older than specified days"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = PerformanceMetric.query.filter(
            PerformanceMetric.timestamp < cutoff
        ).delete()
        db.session.commit()
        logger.info(f"Deleted {deleted} metrics older than {days} days")
    except Exception as e:
        logger.error(f"Error cleaning up old metrics: {e}")
        db.session.rollback()

def main():
    """Main monitoring function"""
    logger.info("Starting performance monitoring run")
    
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(config['production'])
    db.init_app(app)
    
    with app.app_context():
        # Cleanup old metrics first
        cleanup_old_metrics()
        
        # Monitor each endpoint
        for endpoint in ENDPOINTS:
            try:
                metric_data = measure_endpoint(endpoint)
                
                # Save to database
                metric = PerformanceMetric(**metric_data)
                db.session.add(metric)
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error saving metric for {endpoint['name']}: {e}")
                db.session.rollback()
        
        # Get summary statistics
        try:
            total_metrics = PerformanceMetric.query.filter(
                PerformanceMetric.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            avg_response_time = db.session.query(
                db.func.avg(PerformanceMetric.query_execution_time_ms)
            ).filter(
                PerformanceMetric.timestamp >= datetime.utcnow() - timedelta(hours=1),
                PerformanceMetric.response_status == 200
            ).scalar()
            
            logger.info(f"Monitoring complete. Collected {total_metrics} metrics. "
                       f"Average response time: {avg_response_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
    
    logger.info("Performance monitoring run completed")

if __name__ == "__main__":
    main()