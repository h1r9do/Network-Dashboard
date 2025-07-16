#!/usr/bin/env python3
"""
Fixed Comprehensive EOL Tracker that prioritizes HTML data over PDF extraction
This ensures we get accurate EOL data from the official HTML tables
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import PyPDF2
import re
import logging
import psycopg2
from datetime import datetime, date
from urllib.parse import urljoin
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

EOL_DIR = "/var/www/html/meraki-data/EOL"
os.makedirs(EOL_DIR, exist_ok=True)

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

def scrape_eol_html_tables():
    """Scrape the EOL page HTML tables for complete data"""
    logger.info("Scraping EOL HTML tables...")
    
    base_url = "https://documentation.meraki.com"
    eol_url = f"{base_url}/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
    
    try:
        response = requests.get(eol_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching EOL page: {e}")
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    models_from_html = {}
    
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
            
            # Clean model name - be more careful about what we remove
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
            
            # Check if this row has a PDF link
            pdf_link = None
            for link in cells[model_idx].find_all('a', href=True):
                if '.pdf' in link['href'].lower():
                    pdf_link = link['href']
                    break
            
            if any(dates.values()):  # Only store if we have at least one date
                models_from_html[model] = {
                    'description': model_text,
                    'announcement_date': dates['announcement'],
                    'end_of_sale': dates['end_of_sale'],
                    'end_of_support': dates['end_of_support'],
                    'source': 'HTML',
                    'pdf_url': pdf_link,
                    'confidence': 'high'  # HTML data is most reliable
                }
                
                # Also check for model families (like MS120 SERIES)
                if 'SERIES' in model.upper() or 'FAMILY' in model.upper():
                    # Extract the base model
                    base_match = re.match(r'([A-Z]{2,3}\d{2,3})', model)
                    if base_match:
                        base_model = base_match.group(1)
                        # Apply to all variants we might have
                        for variant in ['8', '8P', '8LP', '8FP', '24', '24P', '48', '48P', '48LP', '48FP']:
                            variant_model = f"{base_model}-{variant}"
                            if variant_model not in models_from_html:
                                models_from_html[variant_model] = {
                                    'description': f'{variant_model} (from {model} family)',
                                    'announcement_date': dates['announcement'],
                                    'end_of_sale': dates['end_of_sale'],
                                    'end_of_support': dates['end_of_support'],
                                    'source': 'HTML',
                                    'pdf_url': pdf_link,
                                    'confidence': 'high'
                                }
    
    logger.info(f"Found {len(models_from_html)} models from HTML tables")
    return models_from_html

def update_database(data, conn):
    """Update database with EOL data, prioritizing HTML sources"""
    cursor = conn.cursor()
    
    # Create table if needed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meraki_eol_enhanced (
            id SERIAL PRIMARY KEY,
            model VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            replacement_model VARCHAR(200),
            announcement_date DATE,
            end_of_sale DATE,
            end_of_support DATE,
            source VARCHAR(50) DEFAULT 'HTML',
            pdf_name VARCHAR(200),
            pdf_url VARCHAR(500),
            confidence VARCHAR(20) DEFAULT 'high',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    stored = 0
    updated = 0
    
    for model, item in data.items():
        try:
            # Only store if we have meaningful dates
            if item.get('end_of_sale') or item.get('end_of_support'):
                
                # Check if model already exists
                cursor.execute("SELECT source, confidence FROM meraki_eol_enhanced WHERE model = %s", (model,))
                existing = cursor.fetchone()
                
                # Skip update if existing data is from HTML and new data is not
                if existing and existing[0] == 'HTML' and item.get('source') != 'HTML':
                    logger.debug(f"Skipping {model} - HTML data already exists")
                    continue
                
                cursor.execute("""
                    INSERT INTO meraki_eol_enhanced (
                        model, description, announcement_date, end_of_sale, 
                        end_of_support, source, pdf_url, confidence
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (model) DO UPDATE SET
                        description = EXCLUDED.description,
                        announcement_date = EXCLUDED.announcement_date,
                        end_of_sale = EXCLUDED.end_of_sale,
                        end_of_support = EXCLUDED.end_of_support,
                        source = EXCLUDED.source,
                        pdf_url = EXCLUDED.pdf_url,
                        confidence = EXCLUDED.confidence,
                        updated_at = NOW()
                    WHERE meraki_eol_enhanced.source != 'HTML' OR EXCLUDED.source = 'HTML'
                """, (
                    model,
                    item.get('description', ''),
                    item.get('announcement_date'),
                    item.get('end_of_sale'),
                    item.get('end_of_support'),
                    item.get('source', 'HTML'),
                    item.get('pdf_url'),
                    item.get('confidence', 'high')
                ))
                
                if 'INSERT' in cursor.statusmessage:
                    stored += 1
                else:
                    updated += 1
                    
        except Exception as e:
            logger.error(f"Error storing {model}: {e}")
    
    conn.commit()
    cursor.close()
    
    return stored, updated

def update_inventory_summary(conn):
    """Update inventory_summary table with corrected EOL data"""
    cursor = conn.cursor()
    
    logger.info("Updating inventory_summary with EOL data...")
    
    # Get today's date for comparisons
    today = date.today()
    
    # Update all models in inventory_summary with EOL data
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
    
    updated_count = cursor.rowcount
    logger.info(f"Updated {updated_count} models in inventory_summary")
    
    conn.commit()
    cursor.close()

def main():
    """Main function"""
    logger.info("=== Fixed Comprehensive EOL Tracker ===")
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Step 1: Scrape HTML tables for complete data (most reliable source)
        html_data = scrape_eol_html_tables()
        
        # Step 2: Update database with HTML data
        logger.info(f"\nTotal models from HTML: {len(html_data)}")
        stored, updated = update_database(html_data, conn)
        
        logger.info(f"\nDatabase update complete:")
        logger.info(f"  New records: {stored}")
        logger.info(f"  Updated records: {updated}")
        
        # Step 3: Update inventory_summary table
        update_inventory_summary(conn)
        
        # Show summary
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN end_of_support <= CURRENT_DATE THEN 1 END) as eol,
                COUNT(CASE WHEN end_of_sale <= CURRENT_DATE AND end_of_support > CURRENT_DATE THEN 1 END) as eos,
                COUNT(CASE WHEN end_of_sale > CURRENT_DATE THEN 1 END) as active
            FROM meraki_eol_enhanced
        """)
        
        total, eol, eos, active = cursor.fetchone()
        
        logger.info(f"\n=== Database Summary ===")
        logger.info(f"Total models: {total}")
        logger.info(f"  - End of Life (red): {eol}")
        logger.info(f"  - End of Sale (yellow): {eos}")
        logger.info(f"  - Active (blue): {active}")
        
        # Check specific models that were problematic
        cursor.execute("""
            SELECT model, announcement_date, end_of_sale, end_of_support, source
            FROM meraki_eol_enhanced
            WHERE model IN ('MR16', 'MR12', 'MR24')
            ORDER BY model
        """)
        
        logger.info(f"\n=== Verification of Fixed Models ===")
        for row in cursor.fetchall():
            model, ann, eos, eol, source = row
            logger.info(f"{model}: Ann={ann}, EOS={eos}, EOL={eol} (Source: {source})")
        
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()