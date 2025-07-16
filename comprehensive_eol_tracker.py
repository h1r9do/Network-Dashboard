#!/usr/bin/env python3
"""
Comprehensive EOL Tracker that combines PDF parsing with HTML table scraping
This ensures we get complete EOL data from all available sources
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
            
            # Clean model name
            model = re.sub(r'\s*\(.*?\)\s*', '', model_text)  # Remove parentheses
            model = model.split(',')[0].strip()  # Take first if comma-separated
            model = re.sub(r'-(HW|WW|NA|EU|UK|US|AU|CN)$', '', model.upper())  # Remove suffixes
            
            if not model or len(model) < 3:
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
                    'pdf_url': pdf_link
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
                                    'pdf_url': pdf_link
                                }
    
    logger.info(f"Found {len(models_from_html)} models from HTML tables")
    return models_from_html

def download_pdf(url, filename):
    """Download a PDF file"""
    try:
        clean_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        if not clean_filename.endswith('.pdf'):
            clean_filename += '.pdf'
        
        filepath = os.path.join(EOL_DIR, clean_filename)
        
        if os.path.exists(filepath):
            return filepath
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded: {clean_filename}")
        return filepath
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        return None

def extract_models_from_pdf(text, filename):
    """Extract model numbers from PDF text"""
    models = set()
    
    # Clean text
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\w+)\s*-\s*(\w+)', r'\1-\2', text)
    
    # Model patterns
    model_patterns = [
        r'\b(M[XSRVG]\d{2,3}[A-Z0-9\-]*)\b',
        r'\b(Z\d+[A-Z0-9\-]*)\b',
        r'\b(G[XRS]\d{2,3}[A-Z0-9\-]*)\b',
        r'\b(MA-[A-Z0-9\-]+)\b',
        r'\b(LIC-[A-Z0-9\-]+)\b',
        r'\b(MC\d+[A-Z0-9\-]*)\b',
    ]
    
    for pattern in model_patterns:
        matches = re.findall(pattern, text.upper())
        for match in matches:
            # Clean model
            clean_model = re.sub(r'-(HW|WW|NA|EU|UK|US|AU|CN)$', '', match)
            if clean_model and len(clean_model) > 2:
                models.add(clean_model)
    
    return list(models)

def process_pdfs():
    """Process all PDFs to extract model lists"""
    logger.info("Processing PDFs for model extraction...")
    
    pdf_models = {}
    pdf_files = [f for f in os.listdir(EOL_DIR) if f.endswith('.pdf')]
    
    for pdf_file in pdf_files:
        try:
            filepath = os.path.join(EOL_DIR, pdf_file)
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages[:5]:  # Just first 5 pages
                    text += page.extract_text() + " "
            
            models = extract_models_from_pdf(text, pdf_file)
            for model in models:
                if model not in pdf_models:
                    pdf_models[model] = []
                pdf_models[model].append(pdf_file)
                
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")
    
    logger.info(f"Found {len(pdf_models)} unique models from PDFs")
    return pdf_models

def merge_data_sources(html_data, pdf_models):
    """Merge HTML and PDF data for comprehensive coverage"""
    logger.info("Merging data sources...")
    
    merged_data = {}
    
    # Start with HTML data as it has complete dates
    for model, data in html_data.items():
        merged_data[model] = data.copy()
        # Add PDF references if available
        if model in pdf_models:
            merged_data[model]['pdf_files'] = pdf_models[model]
    
    # Add models that are only in PDFs
    for model, pdf_files in pdf_models.items():
        if model not in merged_data:
            # Try to find if this model is part of a family in HTML
            base_model = re.match(r'([A-Z]{2,3}\d{2,3})', model)
            if base_model:
                base = base_model.group(1)
                # Look for family entries
                for html_model, html_item in html_data.items():
                    if base in html_model and ('SERIES' in html_model or 'FAMILY' in html_model):
                        merged_data[model] = {
                            'description': f'{model} (from {html_model})',
                            'announcement_date': html_item['announcement_date'],
                            'end_of_sale': html_item['end_of_sale'],
                            'end_of_support': html_item['end_of_support'],
                            'source': 'HTML+PDF',
                            'pdf_files': pdf_files
                        }
                        break
    
    return merged_data

def update_database(merged_data, conn):
    """Update database with comprehensive EOL data"""
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
    
    for model, data in merged_data.items():
        try:
            # Only store if we have meaningful dates
            if data.get('end_of_sale') or data.get('end_of_support'):
                pdf_name = data.get('pdf_files', [None])[0] if 'pdf_files' in data else None
                
                cursor.execute("""
                    INSERT INTO meraki_eol_enhanced (
                        model, description, announcement_date, end_of_sale, 
                        end_of_support, source, pdf_name, confidence
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'high')
                    ON CONFLICT (model) DO UPDATE SET
                        description = COALESCE(EXCLUDED.description, meraki_eol_enhanced.description),
                        announcement_date = COALESCE(EXCLUDED.announcement_date, meraki_eol_enhanced.announcement_date),
                        end_of_sale = COALESCE(EXCLUDED.end_of_sale, meraki_eol_enhanced.end_of_sale),
                        end_of_support = COALESCE(EXCLUDED.end_of_support, meraki_eol_enhanced.end_of_support),
                        source = EXCLUDED.source,
                        pdf_name = COALESCE(EXCLUDED.pdf_name, meraki_eol_enhanced.pdf_name),
                        confidence = 'high',
                        updated_at = NOW()
                """, (
                    model,
                    data.get('description', ''),
                    data.get('announcement_date'),
                    data.get('end_of_sale'),
                    data.get('end_of_support'),
                    data.get('source', 'HTML'),
                    pdf_name
                ))
                
                if 'INSERT' in cursor.statusmessage:
                    stored += 1
                else:
                    updated += 1
                    
        except Exception as e:
            logger.error(f"Error storing {model}: {e}")
            conn.rollback()  # Rollback on error to prevent transaction abort
            # Try to continue with next model
            cursor = conn.cursor()  # Get fresh cursor after rollback
    
    conn.commit()
    cursor.close()
    
    return stored, updated

def download_all_pdfs():
    """Download all PDFs referenced on the EOL page"""
    logger.info("Downloading all EOL PDFs...")
    
    base_url = "https://documentation.meraki.com"
    eol_url = f"{base_url}/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
    
    try:
        response = requests.get(eol_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching EOL page: {e}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all PDF links
    pdf_count = 0
    for link in soup.find_all('a', href=True):
        if '.pdf' in link['href'].lower():
            pdf_url = urljoin(base_url, link['href'])
            filename = os.path.basename(link['href'].split('?')[0])
            
            result = download_pdf(pdf_url, filename)
            if result:
                pdf_count += 1
            
            time.sleep(0.5)  # Be nice to the server
    
    logger.info(f"Downloaded {pdf_count} PDFs")

def main():
    """Main function"""
    logger.info("=== Comprehensive EOL Tracker ===")
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Step 1: Download all PDFs
        download_all_pdfs()
        
        # Step 2: Scrape HTML tables for complete data
        html_data = scrape_eol_html_tables()
        
        # Step 3: Process PDFs to get model lists
        pdf_models = process_pdfs()
        
        # Step 4: Merge data sources
        merged_data = merge_data_sources(html_data, pdf_models)
        
        # Step 5: Update database
        logger.info(f"\nTotal models to process: {len(merged_data)}")
        stored, updated = update_database(merged_data, conn)
        
        logger.info(f"\nDatabase update complete:")
        logger.info(f"  New records: {stored}")
        logger.info(f"  Updated records: {updated}")
        
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
        
        # Check MS120 specifically
        cursor.execute("""
            SELECT model, announcement_date, end_of_sale, end_of_support, source
            FROM meraki_eol_enhanced
            WHERE model LIKE 'MS120%'
            ORDER BY model
            LIMIT 10
        """)
        
        logger.info(f"\n=== MS120 Family Status ===")
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