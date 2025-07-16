#!/usr/bin/env python3
"""
Enhanced EOL Tracker that properly parses PDF content and updates the database
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import PyPDF2
import re
from datetime import datetime
import logging
import psycopg2
from urllib.parse import urljoin
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directories
EOL_DIR = "/var/www/html/meraki-data/EOL"
os.makedirs(EOL_DIR, exist_ok=True)

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

def create_enhanced_eol_table(conn):
    """Create enhanced EOL table"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meraki_eol_enhanced (
                id SERIAL PRIMARY KEY,
                model VARCHAR(100) NOT NULL,
                description TEXT,
                replacement_model VARCHAR(200),
                announcement_date DATE,
                end_of_sale DATE,
                end_of_support DATE,
                source VARCHAR(50) DEFAULT 'PDF',
                pdf_name VARCHAR(200),
                pdf_url VARCHAR(500),
                confidence VARCHAR(20) DEFAULT 'high',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(model)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eol_enhanced_model 
            ON meraki_eol_enhanced(model)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eol_enhanced_dates 
            ON meraki_eol_enhanced(end_of_sale, end_of_support)
        """)
        
        conn.commit()
        logger.info("Enhanced EOL table created/verified")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        conn.rollback()
    finally:
        cursor.close()

def download_pdf(url, filename):
    """Download a PDF file"""
    try:
        clean_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        if not clean_filename.endswith('.pdf'):
            clean_filename += '.pdf'
        
        filepath = os.path.join(EOL_DIR, clean_filename)
        
        if os.path.exists(filepath):
            logger.info(f"Already exists: {clean_filename}")
            return filepath
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded: {clean_filename}")
        return filepath
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        return None

def parse_date_string(date_str):
    """Parse date string to date object"""
    if not date_str:
        return None
    
    # Clean up the string
    date_str = date_str.strip().replace('st,', ',').replace('nd,', ',').replace('rd,', ',').replace('th,', ',')
    
    formats = [
        '%B %d, %Y',      # January 1, 2024
        '%b %d, %Y',      # Jan 1, 2024
        '%m/%d/%Y',       # 01/01/2024
        '%Y-%m-%d',       # 2024-01-01
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    
    return None

def extract_ms220_data_from_pdf(text):
    """Extract MS220 model data from PDF text"""
    models = {}
    
    # For MS220 series PDF
    if 'MS220' in text and 'End-of-Sale Announcement' in text:
        # Extract models from the model table
        model_section = re.search(r'MODEL NUMBER\s+DESCRIPTION\s+(.*?)The following products', text, re.DOTALL)
        if model_section:
            model_text = model_section.group(1)
            
            # Parse each MS220 model
            ms220_models = re.findall(r'(MS220-\d+[A-Z]*)-HW\s+([^\n]+)', model_text)
            
            for model, description in ms220_models:
                models[model] = {
                    'description': description.strip(),
                    'replacement': None,
                    'dates': {}
                }
        
        # Extract replacement products
        replacement_section = re.search(r'will replace the above\s+products:\s+(.*?)We expect', text, re.DOTALL)
        if replacement_section:
            # This is more complex, but we can note the general replacements
            pass
        
        # Extract dates
        # MS220 series (not MS220-8)
        if 'MS220-24' in text or 'MS220-48' in text:
            # End of sale: July 29, 2017
            # End of support: July 29, 2024
            eos_match = re.search(r'final orders.*?through\s+(\w+\s+\d+\w*,\s+\d{4})', text)
            eol_match = re.search(r'End of support.*?will be\s+(\w+\s+\d+\w*,\s+\d{4})', text)
            
            if eos_match and eol_match:
                eos_date = parse_date_string(eos_match.group(1))
                eol_date = parse_date_string(eol_match.group(1))
                
                for model in models:
                    if model != 'MS220-8' and model != 'MS220-8P':
                        models[model]['dates'] = {
                            'announcement': None,
                            'end_of_sale': eos_date,
                            'end_of_support': eol_date
                        }
        
        # MS220-8 series
        if 'MS220-8' in text:
            # These have different dates
            # End of sale: September 21, 2018
            # End of support: September 21, 2025
            eos_match = re.search(r'September\s+21\w*,\s+2018', text)
            eol_match = re.search(r'September\s+21\w*,\s+2025', text)
            ann_match = re.search(r'January\s+9\w*,\s+2018', text)
            
            if eos_match and eol_match:
                for model in ['MS220-8', 'MS220-8P']:
                    if model not in models:
                        models[model] = {'description': '', 'replacement': None, 'dates': {}}
                    
                    models[model]['dates'] = {
                        'announcement': parse_date_string('January 9, 2018') if ann_match else None,
                        'end_of_sale': parse_date_string('September 21, 2018'),
                        'end_of_support': parse_date_string('September 21, 2025')
                    }
    
    return models

def process_pdfs_and_update_db(conn):
    """Process PDFs and update database"""
    cursor = conn.cursor()
    
    # Get EOL page
    base_url = "https://documentation.meraki.com"
    eol_url = f"{base_url}/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
    
    logger.info("Fetching EOL page...")
    response = requests.get(eol_url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Parse HTML tables first
    logger.info("Parsing HTML tables...")
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
        if 'model' in headers or 'product' in headers:
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    model_text = cols[0].get_text(strip=True)
                    if 'MS220' in model_text.upper():
                        model = model_text.split(',')[0].split('(')[0].strip().upper()
                        
                        # Skip generic entries for now
                        if model == 'MS220 SERIES':
                            continue
                        
                        dates = {
                            'announcement': parse_date_string(cols[1].get_text(strip=True)),
                            'end_of_sale': parse_date_string(cols[2].get_text(strip=True)),
                            'end_of_support': parse_date_string(cols[3].get_text(strip=True))
                        }
                        
                        try:
                            cursor.execute("""
                                INSERT INTO meraki_eol_enhanced (
                                    model, announcement_date, end_of_sale, 
                                    end_of_support, source
                                ) VALUES (%s, %s, %s, %s, 'HTML')
                                ON CONFLICT (model) DO UPDATE SET
                                    announcement_date = EXCLUDED.announcement_date,
                                    end_of_sale = EXCLUDED.end_of_sale,
                                    end_of_support = EXCLUDED.end_of_support,
                                    source = EXCLUDED.source,
                                    updated_at = NOW()
                            """, (model, dates['announcement'], dates['end_of_sale'], dates['end_of_support']))
                        except Exception as e:
                            logger.error(f"Error storing {model}: {e}")
    
    # Find and process PDFs
    pdf_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '.pdf' in href.lower():
            full_url = urljoin(base_url, href)
            filename = os.path.basename(href).split('?')[0]
            
            # Focus on MS220 related PDFs
            if 'MS220' in filename or 'ms220' in filename.lower():
                pdf_links.append({
                    'url': full_url,
                    'filename': filename
                })
    
    logger.info(f"Found {len(pdf_links)} MS220-related PDFs")
    
    # Process MS220 PDFs
    for pdf in pdf_links:
        logger.info(f"Processing: {pdf['filename']}")
        
        pdf_path = download_pdf(pdf['url'], pdf['filename'])
        if not pdf_path:
            continue
        
        # Extract text
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Extract MS220 data
            models = extract_ms220_data_from_pdf(text)
            
            for model, data in models.items():
                if data['dates'].get('end_of_sale'):
                    try:
                        cursor.execute("""
                            INSERT INTO meraki_eol_enhanced (
                                model, description, replacement_model,
                                announcement_date, end_of_sale, end_of_support,
                                source, pdf_name, pdf_url
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (model) DO UPDATE SET
                                description = EXCLUDED.description,
                                replacement_model = EXCLUDED.replacement_model,
                                announcement_date = EXCLUDED.announcement_date,
                                end_of_sale = EXCLUDED.end_of_sale,
                                end_of_support = EXCLUDED.end_of_support,
                                pdf_name = EXCLUDED.pdf_name,
                                pdf_url = EXCLUDED.pdf_url,
                                updated_at = NOW()
                        """, (
                            model,
                            data['description'],
                            data['replacement'],
                            data['dates'].get('announcement'),
                            data['dates'].get('end_of_sale'),
                            data['dates'].get('end_of_support'),
                            'PDF',
                            pdf['filename'],
                            pdf['url']
                        ))
                        logger.info(f"Stored {model}: EOS={data['dates'].get('end_of_sale')}, EOL={data['dates'].get('end_of_support')}")
                    except Exception as e:
                        logger.error(f"Error storing {model}: {e}")
        except Exception as e:
            logger.error(f"Error processing PDF {pdf['filename']}: {e}")
    
    conn.commit()

def update_inventory_with_eol(conn):
    """Update inventory summary with EOL data"""
    cursor = conn.cursor()
    
    try:
        # Update exact matches
        cursor.execute("""
            UPDATE inventory_summary s
            SET 
                announcement_date = e.announcement_date,
                end_of_sale = e.end_of_sale,
                end_of_support = e.end_of_support,
                highlight = CASE
                    WHEN e.end_of_support <= CURRENT_DATE THEN 'red'
                    WHEN e.end_of_sale <= CURRENT_DATE THEN 'yellow'
                    WHEN e.end_of_sale > CURRENT_DATE THEN 'blue'
                    ELSE NULL
                END
            FROM meraki_eol_enhanced e
            WHERE UPPER(s.model) = e.model
        """)
        
        exact_matches = cursor.rowcount
        logger.info(f"Updated {exact_matches} exact model matches")
        
        # For MS220 variants (8P, 24P, etc) that don't have exact matches
        # Use the base model EOL dates
        cursor.execute("""
            UPDATE inventory_summary s
            SET 
                announcement_date = e.announcement_date,
                end_of_sale = e.end_of_sale,
                end_of_support = e.end_of_support,
                highlight = CASE
                    WHEN e.end_of_support <= CURRENT_DATE THEN 'red'
                    WHEN e.end_of_sale <= CURRENT_DATE THEN 'yellow'
                    WHEN e.end_of_sale > CURRENT_DATE THEN 'blue'
                    ELSE NULL
                END
            FROM meraki_eol_enhanced e
            WHERE s.announcement_date IS NULL
              AND s.model LIKE 'MS220-%'
              AND (
                  (s.model LIKE 'MS220-8%' AND e.model = 'MS220-8')
                  OR (s.model LIKE 'MS220-24%' AND e.model = 'MS220-24')
                  OR (s.model LIKE 'MS220-48%' AND e.model = 'MS220-48')
              )
        """)
        
        pattern_matches = cursor.rowcount
        logger.info(f"Updated {pattern_matches} pattern matches")
        
        conn.commit()
        
        # Show results
        cursor.execute("""
            SELECT model, announcement_date, end_of_sale, end_of_support
            FROM inventory_summary
            WHERE model LIKE 'MS220%'
            ORDER BY model
        """)
        
        results = cursor.fetchall()
        logger.info("\n=== MS220 Inventory Summary Update ===")
        for model, ann, eos, eol in results:
            logger.info(f"{model}: Ann={ann}, EOS={eos}, EOL={eol}")
        
    except Exception as e:
        logger.error(f"Error updating inventory: {e}")
        conn.rollback()
    finally:
        cursor.close()

def main():
    """Main function"""
    logger.info("Starting Enhanced EOL Tracker")
    
    conn = get_db_connection()
    
    try:
        # Create table
        create_enhanced_eol_table(conn)
        
        # Process PDFs and update database
        process_pdfs_and_update_db(conn)
        
        # Update inventory with EOL data
        update_inventory_with_eol(conn)
        
        logger.info("Enhanced EOL tracking completed")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()