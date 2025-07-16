#!/usr/bin/env python3
"""
Complete Database-Integrated Nightly Enablement Processor
Tracks:
1. Circuits changing from "Ready for Enablement" to "Enabled"
2. Daily ready queue counts
3. Team attribution based on assigned_to field
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
        password=password,
        cursor_factory=RealDictCursor
    )

def create_tables(conn):
    """Create necessary tables if they don't exist"""
    cursor = conn.cursor()
    
    try:
        # Drop and recreate daily_enablements with correct schema
        cursor.execute("DROP TABLE IF EXISTS daily_enablements CASCADE")
        
        # Daily enablements table - individual circuit records that went from ready to enabled
        cursor.execute("""
            CREATE TABLE daily_enablements (
                id SERIAL PRIMARY KEY,
                date DATE,
                site_name VARCHAR(200),
                circuit_purpose VARCHAR(100),
                provider_name VARCHAR(100),
                service_speed VARCHAR(50),
                monthly_cost DECIMAL(10,2),
                previous_status VARCHAR(100),
                current_status VARCHAR(100),
                assigned_to VARCHAR(100),
                sctask VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Enablement summary - daily counts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enablement_summary (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE,
                daily_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
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
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_enablements_date ON daily_enablements(date);
            CREATE INDEX IF NOT EXISTS idx_daily_enablements_assigned ON daily_enablements(assigned_to);
            CREATE INDEX IF NOT EXISTS idx_enablement_summary_date ON enablement_summary(summary_date);
            CREATE INDEX IF NOT EXISTS idx_ready_queue_date ON ready_queue_daily(summary_date);
        """)
        
        conn.commit()
        logger.info("Tables created/verified successfully")
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def update_daily_summaries(conn):
    """Update daily summaries table with circuit counts by status"""
    cursor = conn.cursor()
    
    try:
        # Get date range (last 90 days)
        cursor.execute("""
            SELECT MIN(DATE(date_record_updated)) as min_date, 
                   MAX(DATE(date_record_updated)) as max_date
            FROM circuits
            WHERE date_record_updated >= CURRENT_DATE - INTERVAL '90 days'
        """)
        
        date_range = cursor.fetchone()
        if not date_range or not date_range['min_date']:
            logger.warning("No circuit data found")
            return
            
        min_date = date_range['min_date']
        max_date = date_range['max_date']
        
        logger.info(f"Processing dates from {min_date} to {max_date}")
        
        # Update daily_summaries for each date
        cursor.execute("""
            INSERT INTO daily_summaries (
                summary_date, total_circuits, enabled_count, ready_count,
                customer_action_count, construction_count, planning_count, created_at
            )
            SELECT 
                DATE(date_record_updated) as summary_date,
                COUNT(*) as total_circuits,
                SUM(CASE WHEN LOWER(status) LIKE '%%enabled%%' 
                         AND LOWER(status) NOT LIKE '%%ready for enablement%%' THEN 1 ELSE 0 END) as enabled_count,
                SUM(CASE WHEN LOWER(status) LIKE '%%ready for enablement%%' THEN 1 ELSE 0 END) as ready_count,
                SUM(CASE WHEN LOWER(status) LIKE '%%customer action%%' THEN 1 ELSE 0 END) as customer_action_count,
                SUM(CASE WHEN LOWER(status) LIKE '%%construction%%' THEN 1 ELSE 0 END) as construction_count,
                SUM(CASE WHEN LOWER(status) LIKE '%%planning%%' THEN 1 ELSE 0 END) as planning_count,
                NOW() as created_at
            FROM circuits
            WHERE date_record_updated >= %s::date - INTERVAL '90 days'
            GROUP BY DATE(date_record_updated)
            ON CONFLICT (summary_date) DO UPDATE SET
                total_circuits = EXCLUDED.total_circuits,
                enabled_count = EXCLUDED.enabled_count,
                ready_count = EXCLUDED.ready_count,
                customer_action_count = EXCLUDED.customer_action_count,
                construction_count = EXCLUDED.construction_count,
                planning_count = EXCLUDED.planning_count,
                created_at = EXCLUDED.created_at
        """, (min_date,))
        
        conn.commit()
        logger.info("Daily summaries updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating daily summaries: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def process_enablements(conn):
    """Process circuits that changed from Ready for Enablement to Enabled"""
    cursor = conn.cursor()
    
    try:
        # Clear existing daily enablements for reprocessing
        cursor.execute("DELETE FROM daily_enablements WHERE date >= CURRENT_DATE - INTERVAL '90 days'")
        cursor.execute("DELETE FROM enablement_summary WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'")
        
        # Get all status changes from ready to enabled in the last 90 days
        cursor.execute("""
            SELECT 
                c.site_name,
                ch.change_date,
                ch.old_value as previous_status,
                ch.new_value as current_status,
                c.circuit_purpose,
                c.provider_name,
                c.details_service_speed as service_speed,
                c.billing_monthly_cost,
                c.assigned_to,
                c.sctask
            FROM circuit_history ch
            JOIN circuits c ON ch.circuit_id = c.id
            WHERE ch.change_type = 'status'
            AND LOWER(ch.old_value) LIKE '%%ready for enablement%%'
            AND LOWER(ch.new_value) LIKE '%%enabled%%'
            AND LOWER(ch.new_value) NOT LIKE '%%ready for enablement%%'
            AND ch.change_date >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY ch.change_date
        """)
        
        enablements = cursor.fetchall()
        logger.info(f"Found {len(enablements)} enablements in the last 90 days")
        
        # Process each enablement
        daily_counts = {}
        
        for enablement in enablements:
            change_date = enablement['change_date'].date()
            
            # Insert into daily_enablements
            cursor.execute("""
                INSERT INTO daily_enablements (
                    date, site_name, circuit_purpose, provider_name,
                    service_speed, monthly_cost, previous_status, current_status,
                    assigned_to, sctask, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                change_date,
                enablement['site_name'],
                enablement['circuit_purpose'],
                enablement['provider_name'],
                enablement['service_speed'],
                enablement['billing_monthly_cost'],
                enablement['previous_status'],
                enablement['current_status'],
                enablement['assigned_to'],
                enablement['sctask']
            ))
            
            # Count by date
            if change_date not in daily_counts:
                daily_counts[change_date] = 0
            daily_counts[change_date] += 1
        
        # Update enablement_summary
        for date, count in daily_counts.items():
            cursor.execute("""
                INSERT INTO enablement_summary (summary_date, daily_count, created_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (summary_date) DO UPDATE SET
                    daily_count = EXCLUDED.daily_count,
                    created_at = EXCLUDED.created_at
            """, (date, count))
        
        logger.info(f"Updated enablement summary for {len(daily_counts)} days")
        
        # Fill in missing dates with 0
        cursor.execute("""
            INSERT INTO enablement_summary (summary_date, daily_count, created_at)
            SELECT 
                generate_series(
                    CURRENT_DATE - INTERVAL '90 days',
                    CURRENT_DATE,
                    '1 day'::interval
                )::date as summary_date,
                0 as daily_count,
                NOW() as created_at
            ON CONFLICT (summary_date) DO NOTHING
        """)
        
        conn.commit()
        logger.info("Enablement processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing enablements: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def update_ready_queue(conn):
    """Update daily ready queue counts"""
    cursor = conn.cursor()
    
    try:
        # Clear existing data for reprocessing
        cursor.execute("DELETE FROM ready_queue_daily WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'")
        
        # For each day in the last 90 days, get the ready count from daily_summaries
        # Since we already calculated ready_count in daily_summaries, use that
        cursor.execute("""
            INSERT INTO ready_queue_daily (summary_date, ready_count, created_at)
            SELECT 
                summary_date,
                ready_count,
                NOW() as created_at
            FROM daily_summaries
            WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY summary_date
        """)
        
        rows_affected = cursor.rowcount
        logger.info(f"Updated ready queue counts for {rows_affected} days")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error updating ready queue: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def calculate_trends(conn):
    """Calculate weekly and monthly trends"""
    cursor = conn.cursor()
    
    try:
        # Clear existing trends
        cursor.execute("DELETE FROM enablement_trends WHERE period_start >= CURRENT_DATE - INTERVAL '90 days'")
        
        # Calculate weekly trends
        cursor.execute("""
            INSERT INTO enablement_trends (
                period_type, period_start, period_end, enablement_count, created_at
            )
            SELECT 
                'weekly',
                DATE_TRUNC('week', summary_date::date) as period_start,
                DATE_TRUNC('week', summary_date::date) + INTERVAL '6 days' as period_end,
                SUM(daily_count) as enablement_count,
                NOW()
            FROM enablement_summary 
            WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY DATE_TRUNC('week', summary_date::date)
        """)
        
        # Calculate monthly trends
        cursor.execute("""
            INSERT INTO enablement_trends (
                period_type, period_start, period_end, enablement_count, created_at
            )
            SELECT 
                'monthly',
                DATE_TRUNC('month', summary_date::date) as period_start,
                DATE_TRUNC('month', summary_date::date) + INTERVAL '1 month' - INTERVAL '1 day' as period_end,
                SUM(daily_count) as enablement_count,
                NOW()
            FROM enablement_summary 
            WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY DATE_TRUNC('month', summary_date::date)
        """)
        
        conn.commit()
        logger.info("Trend calculations completed")
        
    except Exception as e:
        logger.error(f"Error calculating trends: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def main():
    """Main processing function"""
    logger.info("=" * 60)
    logger.info("Starting complete database-integrated enablement processing")
    logger.info("=" * 60)
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create/verify tables
        create_tables(conn)
        
        # Update daily summaries
        logger.info("Step 1: Updating daily summaries...")
        update_daily_summaries(conn)
        
        # Process enablements (ready -> enabled transitions)
        logger.info("Step 2: Processing enablements...")
        process_enablements(conn)
        
        # Update ready queue counts
        logger.info("Step 3: Updating ready queue counts...")
        update_ready_queue(conn)
        
        # Calculate trends
        logger.info("Step 4: Calculating trends...")
        calculate_trends(conn)
        
        # Summary report
        cursor = conn.cursor()
        
        # Get summary stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_days,
                SUM(daily_count) as total_enablements,
                AVG(daily_count) as avg_per_day
            FROM enablement_summary
            WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'
        """)
        summary = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(DISTINCT assigned_to) as unique_assignees
            FROM daily_enablements
            WHERE assigned_to IS NOT NULL AND assigned_to != ''
        """)
        assignee_count = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info("=" * 60)
        logger.info("Processing completed successfully!")
        logger.info(f"Total days processed: {summary['total_days']}")
        logger.info(f"Total enablements: {summary['total_enablements']}")
        logger.info(f"Average per day: {summary['avg_per_day']:.1f}")
        logger.info(f"Unique team members: {assignee_count['unique_assignees']}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)