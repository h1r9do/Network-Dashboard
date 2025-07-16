#!/usr/bin/env python3
"""
Hourly API Performance Collection Script
Collects performance metrics for all API endpoints
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsrcircuits import app
from models import db, PerformanceMetric

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base URL for API calls
BASE_URL = "http://localhost:5052"

# API endpoints to monitor (organized by category)
API_ENDPOINTS = {
    # Core Circuit APIs
    "circuits": [
        {"path": "/api/circuits/search", "method": "GET", "params": {"q": "test"}},
        {"path": "/api/dashboard-data", "method": "GET"},
        {"path": "/api/get-assignments", "method": "GET"},
        {"path": "/api/inflight-data", "method": "GET"},
    ],
    
    # Documentation APIs
    "documentation": [
        {"path": "/api/documentation/content", "method": "GET"},
    ],
    
    # Firewall APIs
    "firewall": [
        {"path": "/api/firewall/template/Standard_Store", "method": "GET"},
        {"path": "/api/networks", "method": "GET"},
    ],
    
    # Inventory APIs
    "inventory": [
        {"path": "/api/inventory-summary", "method": "GET"},
        {"path": "/api/ssh-inventory", "method": "GET"},
    ],
    
    # New Stores APIs
    "new_stores": [
        {"path": "/api/new-stores", "method": "GET"},
        {"path": "/api/new-store-circuits-with-tod", "method": "GET"},
    ],
    
    # Performance APIs
    "performance": [
        {"path": "/api/performance/current", "method": "GET"},
        {"path": "/api/performance/summary", "method": "GET"},
        {"path": "/api/performance/anomalies", "method": "GET"},
    ],
    
    # Reporting APIs
    "reports": [
        {"path": "/api/closure-attribution-data", "method": "GET", "params": {"days": "7"}},
        {"path": "/api/daily-enablement-data", "method": "GET", "params": {"days": "7"}},
        {"path": "/api/enablement-trend", "method": "GET"},
        {"path": "/api/ready-queue-data", "method": "GET"},
        {"path": "/api/reports-health", "method": "GET"},
    ],
    
    # Switch Visibility APIs
    "switch": [
        {"path": "/api/switch-port-clients", "method": "GET", "params": {"store": "test"}},
    ],
    
    # System Health APIs
    "system": [
        {"path": "/api/system-health/summary", "method": "GET"},
        {"path": "/api/system-health/all", "method": "GET"},
        {"path": "/api/health", "method": "GET"},
    ],
    
    # Tag Management APIs
    "tags": [
        {"path": "/api/tags/inventory", "method": "GET", "params": {"limit": "10"}},
    ],
}

def measure_api_performance(endpoint_config):
    """Measure performance for a single API endpoint"""
    url = urljoin(BASE_URL, endpoint_config["path"])
    method = endpoint_config.get("method", "GET")
    params = endpoint_config.get("params", {})
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=params, timeout=30)
        else:
            logger.warning(f"Unsupported method {method} for {url}")
            return None
            
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return {
            "endpoint": endpoint_config["path"],
            "method": method,
            "response_time": response_time,
            "status_code": response.status_code,
            "response_size": len(response.content),
            "success": response.status_code < 400,
            "timestamp": datetime.utcnow()
        }
        
    except requests.exceptions.Timeout:
        return {
            "endpoint": endpoint_config["path"],
            "method": method,
            "response_time": 30000,  # Timeout value
            "status_code": 0,
            "response_size": 0,
            "success": False,
            "error": "Timeout",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error measuring {url}: {str(e)}")
        return {
            "endpoint": endpoint_config["path"],
            "method": method,
            "response_time": 0,
            "status_code": 0,
            "response_size": 0,
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

def collect_performance_metrics():
    """Collect performance metrics for all API endpoints"""
    logger.info("Starting hourly API performance collection")
    
    # Use the imported app directly
    metrics = []
    
    with app.app_context():
        # Test each category of endpoints
        for category, endpoints in API_ENDPOINTS.items():
            logger.info(f"Testing {category} APIs...")
            
            for endpoint in endpoints:
                metric = measure_api_performance(endpoint)
                if metric:
                    metric["category"] = category
                    metrics.append(metric)
                    
                    # Log the result
                    if metric["success"]:
                        logger.info(f"{metric['endpoint']}: {metric['response_time']:.2f}ms")
                    else:
                        logger.warning(f"{metric['endpoint']}: Failed - {metric.get('error', 'HTTP ' + str(metric['status_code']))}")
                    
                    # Small delay to avoid overwhelming the server
                    time.sleep(0.1)
        
        # Calculate summary statistics
        successful_metrics = [m for m in metrics if m["success"]]
        if successful_metrics:
            avg_response_time = sum(m["response_time"] for m in successful_metrics) / len(successful_metrics)
            max_response_time = max(m["response_time"] for m in successful_metrics)
            min_response_time = min(m["response_time"] for m in successful_metrics)
            success_rate = (len(successful_metrics) / len(metrics)) * 100
            
            logger.info(f"\nPerformance Summary:")
            logger.info(f"  Total endpoints tested: {len(metrics)}")
            logger.info(f"  Success rate: {success_rate:.1f}%")
            logger.info(f"  Average response time: {avg_response_time:.2f}ms")
            logger.info(f"  Max response time: {max_response_time:.2f}ms")
            logger.info(f"  Min response time: {min_response_time:.2f}ms")
        
        # Store metrics in database
        try:
            for metric in metrics:
                perf_record = PerformanceMetric(
                    endpoint_name=metric["endpoint"],
                    endpoint_method=metric["method"],
                    module_category=metric["category"],
                    query_execution_time_ms=metric["response_time"],
                    response_status=metric["status_code"],
                    data_size_bytes=metric["response_size"],
                    error_message=metric.get("error"),
                    timestamp=metric["timestamp"],
                    is_monitoring=True
                )
                db.session.add(perf_record)
            
            db.session.commit()
            logger.info(f"Stored {len(metrics)} performance metrics in database")
            
        except Exception as e:
            logger.error(f"Error storing metrics in database: {str(e)}")
            db.session.rollback()
        
        # Clean up old data (keep last 30 days)
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            deleted = PerformanceMetric.query.filter(PerformanceMetric.timestamp < cutoff_date).delete()
            db.session.commit()
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old performance records")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    collect_performance_metrics()