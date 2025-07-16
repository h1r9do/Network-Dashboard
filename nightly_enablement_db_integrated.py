#!/usr/bin/env python3
"""
Fully Database-Integrated Nightly Enablement Processor
Reads from database tables instead of CSV files
Tracks circuit enablements using circuits and circuit_history tables
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
import re

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nightly-enablement-db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using config"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def is_enabled_status(status):
    """Check if a status indicates an enabled circuit"""
    if not status:
        return False
    
    status_lower = str(status).lower().strip()
    # More specific check - must contain "enabled" but not "ready for enablement"
    return 'enabled' in status_lower and 'ready for enablement' not in status_lower

def is_ready_for_enablement(status):
    """Check if a status indicates ready for enablement"""
    if not status:
        return False
    
    status_lower = str(status).lower().strip()
    return 'ready for enablement' in status_lower

def update_daily_summaries(conn):
    """Update daily summaries table with circuit status counts"""
    cursor = conn.cursor()
    
    try:
        # Only process last 90 days of data to avoid processing years of history
        cursor.execute("""
            SELECT DISTINCT DATE(date_record_updated) as summary_date
            FROM circuits
            WHERE date_record_updated IS NOT NULL
            AND DATE(date_record_updated) >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY summary_date
        """)
        
        dates = cursor.fetchall()
        logger.info(f"Found {len(dates)} dates to process (last 90 days)")
        
        for date_row in dates:
            summary_date = date_row[0]
            # Count circuits by status for this date
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_circuits,
                    SUM(CASE WHEN LOWER(status) LIKE '%%enabled%%' THEN 1 ELSE 0 END) as enabled_count,
                    SUM(CASE WHEN LOWER(status) LIKE '%%ready for enablement%%' THEN 1 ELSE 0 END) as ready_count,
                    SUM(CASE WHEN LOWER(status) LIKE '%%customer action%%' THEN 1 ELSE 0 END) as customer_action_count,
                    SUM(CASE WHEN LOWER(status) LIKE '%%construction%%' THEN 1 ELSE 0 END) as construction_count,
                    SUM(CASE WHEN LOWER(status) LIKE '%%planning%%' THEN 1 ELSE 0 END) as planning_count
                FROM circuits
                WHERE DATE(date_record_updated) <= %s
            """, (summary_date,))
            
            counts = cursor.fetchone()
            
            if not counts:
                logger.warning(f"No data for {summary_date}")
                continue
                
            # Unpack the counts
            total_circuits = counts[0] or 0
            enabled_count = counts[1] or 0
            ready_count = counts[2] or 0
            customer_action_count = counts[3] or 0
            construction_count = counts[4] or 0
            planning_count = counts[5] or 0
            
            # Update daily_summaries table
            cursor.execute("""
                INSERT INTO daily_summaries (
                    summary_date, total_circuits, enabled_count, ready_count,
                    customer_action_count, construction_count, planning_count,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    total_circuits = EXCLUDED.total_circuits,
                    enabled_count = EXCLUDED.enabled_count,
                    ready_count = EXCLUDED.ready_count,
                    customer_action_count = EXCLUDED.customer_action_count,
                    construction_count = EXCLUDED.construction_count,
                    planning_count = EXCLUDED.planning_count,
                    created_at = EXCLUDED.created_at
            """, (summary_date, total_circuits, enabled_count, ready_count, 
                  customer_action_count, construction_count, planning_count, 
                  datetime.now(timezone.utc)))
            
            logger.info(f"Updated daily summary for {summary_date}: {total_circuits} total, {enabled_count} enabled, {ready_count} ready")
        
        conn.commit()
        logger.info(f"Updated {len(dates)} daily summaries")
        
    except Exception as e:
        import traceback
        logger.error(f"Error updating daily summaries: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def detect_daily_enablements(conn):
    """Detect enablements from circuit_history table and current circuits"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get dates that have circuit history changes (last 90 days)
        cursor.execute("""
            SELECT DISTINCT DATE(change_date) as change_date
            FROM circuit_history
            WHERE change_type = 'status'
            AND DATE(change_date) >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY change_date
        """)
        
        dates = cursor.fetchall()
        
        for date_row in dates:
            change_date = date_row['change_date']
            daily_enablements = 0
            
            # Find status changes to enabled on this date
            cursor.execute("""
                SELECT 
                    site_name,
                    old_value as previous_status,
                    new_value as current_status
                FROM circuit_history
                WHERE DATE(change_date) = %s
                AND change_type = 'status'
            """, (change_date,))
            
            changes = cursor.fetchall()
            
            for change in changes:
                # Check if this was an enablement (not enabled -> enabled)
                if (not is_enabled_status(change['previous_status']) and 
                    is_enabled_status(change['current_status'])):
                    daily_enablements += 1
                    
                    # Get full circuit details from current circuits table
                    cursor.execute("""
                        SELECT circuit_purpose, provider_name, service_speed, billing_monthly_cost
                        FROM circuits
                        WHERE site_name = %s
                        LIMIT 1
                    """, (change['site_name'],))
                    
                    circuit_details = cursor.fetchone()
                    
                    if circuit_details:
                        # Insert enablement record
                        cursor.execute("""
                            INSERT INTO circuit_enablements (
                                site_name, circuit_purpose, provider_name, enablement_date,
                                previous_status, current_status, service_speed, monthly_cost,
                                detected_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            ON CONFLICT (site_name, circuit_purpose, provider_name, enablement_date) 
                            DO NOTHING
                        """, (
                            change['site_name'],
                            circuit_details['circuit_purpose'],
                            circuit_details['provider_name'],
                            change_date,
                            change['previous_status'],
                            change['current_status'],
                            circuit_details['service_speed'],
                            circuit_details['billing_monthly_cost'],
                            datetime.now(timezone.utc)
                        ))
            
            # Store daily enablement count
            cursor.execute("""
                INSERT INTO enablement_summary (
                    summary_date, daily_count, created_at
                ) VALUES (%s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    daily_count = EXCLUDED.daily_count,
                    created_at = EXCLUDED.created_at
            """, (change_date, daily_enablements, datetime.now(timezone.utc)))
            
            # Update ready queue count for this date
            cursor.execute("""
                SELECT COUNT(*) 
                FROM circuits 
                WHERE DATE(date_record_updated) <= %s
                AND LOWER(status) LIKE '%%ready for enablement%%'
            """, (change_date,))
            
            ready_result = cursor.fetchone()
            ready_count = ready_result[0] if ready_result else 0
            
            cursor.execute("""
                INSERT INTO ready_queue_daily (
                    summary_date, ready_count, created_at
                ) VALUES (%s, %s, %s)
                ON CONFLICT (summary_date) DO UPDATE SET
                    ready_count = EXCLUDED.ready_count,
                    created_at = EXCLUDED.created_at
            """, (change_date, ready_count, datetime.now(timezone.utc)))
            
            logger.info(f"Date {change_date}: {daily_enablements} enablements, {ready_count} ready")
        
        # Also update today's ready count
        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM circuits 
            WHERE LOWER(status) LIKE '%%ready for enablement%%'
        """)
        
        today_ready = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO ready_queue_daily (
                summary_date, ready_count, created_at
            ) VALUES (%s, %s, %s)
            ON CONFLICT (summary_date) DO UPDATE SET
                ready_count = EXCLUDED.ready_count,
                created_at = EXCLUDED.created_at
        """, (today, today_ready, datetime.now(timezone.utc)))
        
        logger.info(f"Today's ready queue: {today_ready} circuits")
        
        # Calculate trends
        calculate_trends(cursor)
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error detecting enablements: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def calculate_trends(cursor):
    """Calculate weekly and monthly trends"""
    try:
        # Calculate weekly trends
        cursor.execute("""
            INSERT INTO enablement_trends (
                period_type, period_start, period_end, enablement_count, created_at
            )
            SELECT 
                'weekly',
                DATE_TRUNC('week', summary_date::date),
                DATE_TRUNC('week', summary_date::date) + INTERVAL '6 days',
                SUM(daily_count),
                NOW()
            FROM enablement_summary 
            GROUP BY DATE_TRUNC('week', summary_date::date)
            ON CONFLICT (period_type, period_start) DO UPDATE SET
                enablement_count = EXCLUDED.enablement_count,
                period_end = EXCLUDED.period_end
        """)
        
        # Calculate monthly trends
        cursor.execute("""
            INSERT INTO enablement_trends (
                period_type, period_start, period_end, enablement_count, created_at
            )
            SELECT 
                'monthly',
                DATE_TRUNC('month', summary_date::date),
                DATE_TRUNC('month', summary_date::date) + INTERVAL '1 month' - INTERVAL '1 day',
                SUM(daily_count),
                NOW()
            FROM enablement_summary 
            GROUP BY DATE_TRUNC('month', summary_date::date)
            ON CONFLICT (period_type, period_start) DO UPDATE SET
                enablement_count = EXCLUDED.enablement_count,
                period_end = EXCLUDED.period_end
        """)
        
        logger.info("Trend calculations completed")
        
    except Exception as e:
        logger.error(f"Error calculating trends: {e}")

def create_enablement_tables(conn):
    """Create enablement tracking tables if they don't exist"""
    cursor = conn.cursor()
    
    try:
        # Circuit enablements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circuit_enablements (
                id SERIAL PRIMARY KEY,
                site_name VARCHAR(200),
                circuit_purpose VARCHAR(100),
                provider_name VARCHAR(100),
                enablement_date DATE,
                previous_status VARCHAR(100),
                current_status VARCHAR(100),
                service_speed VARCHAR(50),
                monthly_cost DECIMAL(10,2),
                detected_at TIMESTAMP,
                UNIQUE(site_name, circuit_purpose, provider_name, enablement_date)
            )
        """)
        
        # Daily enablement summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enablement_summary (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE,
                daily_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Enablement trends
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enablement_trends (
                id SERIAL PRIMARY KEY,
                period_type VARCHAR(20),
                period_start DATE,
                period_end DATE,
                enablement_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(period_type, period_start)
            )
        """)
        
        # Ready queue daily tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ready_queue_daily (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE,
                ready_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_enablements_date ON circuit_enablements(enablement_date);
            CREATE INDEX IF NOT EXISTS idx_enablements_site ON circuit_enablements(site_name);
            CREATE INDEX IF NOT EXISTS idx_enablements_provider ON circuit_enablements(provider_name);
            CREATE INDEX IF NOT EXISTS idx_summary_date ON enablement_summary(summary_date);
            CREATE INDEX IF NOT EXISTS idx_trends_period ON enablement_trends(period_type, period_start);
            CREATE INDEX IF NOT EXISTS idx_ready_queue_date ON ready_queue_daily(summary_date);
        """)
        
        conn.commit()
        logger.info("Enablement tables created/verified")
        
    except Exception as e:
        logger.error(f"Error creating enablement tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def main():
    """Main processing function"""
    logger.info("Starting fully database-integrated nightly enablement processing")
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create tables if needed
        create_enablement_tables(conn)
        
        # Update daily summaries
        update_daily_summaries(conn)
        
        # Process enablement data
        success = detect_daily_enablements(conn)
        
        if success:
            logger.info("Database-integrated enablement processing completed successfully")
        else:
            logger.error("Database-integrated enablement processing failed")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)