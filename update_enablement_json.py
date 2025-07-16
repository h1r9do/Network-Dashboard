#!/usr/bin/env python3
"""
Quick script to update the JSON files with current database data
This ensures the web interface shows updated data through 6/25
"""

import json
import psycopg2
from config import Config
import re
from datetime import datetime

def get_db_connection():
    """Get database connection"""
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

def update_enablement_json():
    """Update the JSON file with database data"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get summary data from database
    cursor.execute("""
        SELECT summary_date, daily_count 
        FROM enablement_summary 
        ORDER BY summary_date ASC
    """)
    
    results = cursor.fetchall()
    
    # Build daily data array
    daily_data = []
    for summary_date, daily_count in results:
        daily_data.append({
            'date': summary_date.strftime('%Y-%m-%d'),
            'count': daily_count,
            'formatted_date': summary_date.strftime('%b %d')
        })
    
    # Calculate summary
    if daily_data:
        total_enabled = sum(item['count'] for item in daily_data)
        avg_per_day = round(total_enabled / len(daily_data), 1) if daily_data else 0
        max_day = max(daily_data, key=lambda x: x['count']) if daily_data else {'count': 0, 'date': ''}
        
        summary = {
            'total_enabled': total_enabled,
            'avg_per_day': avg_per_day,
            'max_day': {
                'count': max_day['count'],
                'date': max_day['date']
            },
            'days_analyzed': len(daily_data),
            'period_start': daily_data[0]['date'] if daily_data else '',
            'period_end': daily_data[-1]['date'] if daily_data else '',
            'last_updated': datetime.now().isoformat()
        }
    else:
        summary = {
            'total_enabled': 0,
            'avg_per_day': 0,
            'max_day': {'count': 0, 'date': ''},
            'days_analyzed': 0,
            'period_start': '',
            'period_end': '',
            'last_updated': datetime.now().isoformat()
        }
    
    # Create JSON structure
    json_data = {
        'summary': summary,
        'daily_data': daily_data,
        'last_updated': datetime.now().isoformat()
    }
    
    # Write to both files
    output_files = [
        '/var/www/html/meraki-data/circuit_enablement_data.json',
        '/var/www/html/json-cache/enablement_master_summary.json'
    ]
    
    for output_file in output_files:
        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=2)
        print(f"✅ Updated {output_file}")
    
    cursor.close()
    conn.close()
    
    print(f"📊 Updated with {len(daily_data)} days of data through {daily_data[-1]['date']}")
    print(f"📊 Total enablements: {summary['total_enabled']}")

if __name__ == "__main__":
    update_enablement_json()