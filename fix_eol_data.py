#!/usr/bin/env python3
"""
Simple script to fix EOL data by scraping HTML and updating database
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import psycopg2
from datetime import datetime, date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

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

def parse_date_string(date_str):
    """Parse various date formats"""
    if not date_str:
        return None
    
    # Clean up the string
    date_str = str(date_str).strip()
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    date_str = re.sub(r'\s+', ' ', date_str)
    
    formats = [
        '%B %d, %Y',      # January 1, 2024
        '%b %d, %Y',      # Jan 1, 2024
        '%B %d %Y',       # January 1 2024
        '%m/%d/%Y',       # 01/01/2024
        '%Y-%m-%d',       # 2024-01-01
        '%d %B %Y',       # 1 January 2024
        '%d-%b-%Y',       # 1-Jan-2024
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    
    return None

def scrape_eol_html():
    """Scrape the EOL page HTML tables"""
    print("Scraping EOL HTML tables...")
    
    eol_url = "https://documentation.meraki.com/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
    
    try:
        response = requests.get(eol_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching EOL page: {e}")
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    models = {}
    
    # Find all tables
    for table in soup.find_all('table'):
        headers = []
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        # Check if this is an EOL table
        if not any(h in headers for h in ['model', 'product', 'sku']):
            continue
            
        # Find column indices
        model_idx = next((i for i, h in enumerate(headers) if h in ['model', 'product', 'sku', 'model number']), None)
        ann_idx = next((i for i, h in enumerate(headers) if 'announcement' in h), None)
        eos_idx = next((i for i, h in enumerate(headers) if 'end-of-sale' in h or 'end of sale' in h), None)
        eol_idx = next((i for i, h in enumerate(headers) if 'end-of-support' in h or 'end of support' in h), None)
        
        if model_idx is None:
            continue
        
        # Process rows
        for row in table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) <= model_idx:
                continue
            
            # Extract model
            model_text = cells[model_idx].get_text(strip=True)
            if not model_text:
                continue
            
            # Clean model name
            model = re.sub(r'\s*\(.*?\)\s*', '', model_text)  # Remove parentheses
            model = model.split(',')[0].strip()  # Take first if comma-separated
            model = model.upper()
            
            # Only remove regional suffixes if they're at the end
            model = re.sub(r'-(HW|WW|NA|EU|UK|US|AU|CN)$', '', model)
            
            if not model or len(model) < 2:
                continue
            
            # Extract dates
            dates = {
                'announcement': None,
                'end_of_sale': None,
                'end_of_support': None
            }
            
            if ann_idx is not None and ann_idx < len(cells):
                dates['announcement'] = parse_date_string(cells[ann_idx].get_text(strip=True))
            
            if eos_idx is not None and eos_idx < len(cells):
                dates['end_of_sale'] = parse_date_string(cells[eos_idx].get_text(strip=True))
            
            if eol_idx is not None and eol_idx < len(cells):
                dates['end_of_support'] = parse_date_string(cells[eol_idx].get_text(strip=True))
            
            if any(dates.values()):  # Only store if we have at least one date
                models[model] = dates
    
    print(f"Found {len(models)} models from HTML tables")
    return models

def update_database(models):
    """Update database with scraped EOL data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updated = 0
    inserted = 0
    
    for model, dates in models.items():
        try:
            # Check if model exists
            cursor.execute("SELECT id FROM meraki_eol_enhanced WHERE model = %s", (model,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE meraki_eol_enhanced
                    SET announcement_date = %s,
                        end_of_sale = %s,
                        end_of_support = %s,
                        source = 'HTML',
                        updated_at = NOW()
                    WHERE model = %s
                """, (
                    dates['announcement'],
                    dates['end_of_sale'],
                    dates['end_of_support'],
                    model
                ))
                updated += 1
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO meraki_eol_enhanced (
                        model, announcement_date, end_of_sale, 
                        end_of_support, source
                    ) VALUES (%s, %s, %s, %s, 'HTML')
                """, (
                    model,
                    dates['announcement'],
                    dates['end_of_sale'],
                    dates['end_of_support']
                ))
                inserted += 1
                
        except Exception as e:
            print(f"Error updating {model}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    print(f"Database update complete: {inserted} inserted, {updated} updated")
    
    # Update inventory_summary table
    print("Updating inventory_summary with EOL data...")
    
    today = date.today()
    
    cursor.execute("""
        UPDATE inventory_summary AS inv
        SET announcement_date = eol.announcement_date,
            end_of_sale = eol.end_of_sale,
            end_of_support = eol.end_of_support,
            highlight = CASE
                WHEN eol.end_of_support <= %s THEN 'eol'
                WHEN eol.end_of_sale <= %s THEN 'eos'
                ELSE ''
            END
        FROM meraki_eol_enhanced AS eol
        WHERE inv.model = eol.model
    """, (today, today))
    
    inv_updated = cursor.rowcount
    print(f"Updated {inv_updated} models in inventory_summary")
    
    # Verify specific models
    print("\nVerifying key models:")
    cursor.execute("""
        SELECT model, announcement_date, end_of_sale, end_of_support, source
        FROM meraki_eol_enhanced
        WHERE model IN ('MR16', 'MR12', 'MR24')
        ORDER BY model
    """)
    
    for row in cursor.fetchall():
        model, ann, eos, eol, source = row
        print(f"  {model}: Ann={ann}, EOS={eos}, EOL={eol} (Source: {source})")
    
    cursor.close()
    conn.close()

def main():
    print("=== Fixing EOL Data ===")
    
    # Scrape HTML data
    models = scrape_eol_html()
    
    # Update database
    update_database(models)
    
    print("\nDone!")

if __name__ == "__main__":
    main()