#!/usr/bin/env python3
"""
Initialize performance monitoring for DSR Circuits
Creates necessary database tables and runs initial performance test
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from models import db, PerformanceMetric
from flask import Flask
from performance_monitor import measure_endpoint, ENDPOINTS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_performance_monitoring():
    """Initialize performance monitoring system"""
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(config['production'])
    db.init_app(app)
    
    with app.app_context():
        # Create tables if they don't exist
        logger.info("Creating performance_metrics table if needed...")
        db.create_all()
        
        # Check if table exists and has data
        try:
            count = PerformanceMetric.query.count()
            logger.info(f"Performance metrics table exists with {count} records")
        except Exception as e:
            logger.error(f"Error checking performance metrics table: {e}")
            return False
        
        # Run initial performance test
        logger.info("Running initial performance test...")
        success_count = 0
        
        for endpoint in ENDPOINTS[:5]:  # Test first 5 endpoints
            try:
                metric_data = measure_endpoint(endpoint)
                metric = PerformanceMetric(**metric_data)
                db.session.add(metric)
                db.session.commit()
                success_count += 1
                logger.info(f"✓ Tested {endpoint['name']}")
            except Exception as e:
                logger.error(f"✗ Failed to test {endpoint['name']}: {e}")
                db.session.rollback()
        
        logger.info(f"Initial test complete. Successfully tested {success_count}/{min(5, len(ENDPOINTS))} endpoints")
        
        # Display next steps
        print("\n" + "="*60)
        print("Performance Monitoring System Initialized!")
        print("="*60)
        print("\nNext steps:")
        print("1. Add the monitoring script to crontab:")
        print("   sudo crontab -e")
        print("   Add: 0 * * * * /usr/bin/python3 /usr/local/bin/Main/performance_monitor.py >> /var/log/performance-monitor.log 2>&1")
        print("\n2. Access the performance dashboard at:")
        print("   http://localhost:5052/performance")
        print("\n3. The system will collect metrics hourly and display:")
        print("   - Response time trends")
        print("   - Data size metrics")
        print("   - Error rates")
        print("   - Performance anomalies")
        print("="*60 + "\n")
        
        return True

if __name__ == "__main__":
    if init_performance_monitoring():
        logger.info("Performance monitoring initialization completed successfully!")
    else:
        logger.error("Performance monitoring initialization failed!")
        sys.exit(1)