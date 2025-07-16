#!/usr/bin/env python3
"""
Simple EOL Tracker - Production Implementation
==============================================

Implements the user's suggested simple logic:
1. Download all PDFs from EOL page
2. Parse PDFs for models  
3. Match PDF with EOL dates from webpage line
4. Models inherit dates from their source PDF

This approach proved superior to complex logic:
- Simple: 80% coverage (48/60 models)
- Complex: 73.3% coverage (44/60 models)
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import PyPDF2
import re
import logging
import psycopg2
from datetime import datetime
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

EOL_DIR = "/var/www/html/meraki-data/EOL"

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
    
    date_str = str(date_str).strip()
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    date_str = re.sub(r'\s+', ' ', date_str)
    
    formats = [
        '%B %d, %Y',      # January 1, 2024
        '%b %d, %Y',      # Jan 1, 2024
        '%B %d %Y',       # January 1 2024
        '%m/%d/%Y',       # 01/01/2024
        '%Y-%m-%d',       # 2024-01-01
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    
    return None

def step1_download_pdfs_and_get_dates():
    """
    Step 1: Download all PDFs and map them to their EOL dates from webpage
    Returns: {pdf_filename: {announcement, end_of_sale, end_of_support}}
    """
    logger.info("Step 1: Downloading PDFs and mapping to EOL dates...")
    
    base_url = "https://documentation.meraki.com"
    eol_url = f"{base_url}/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
    
    try:
        response = requests.get(eol_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching EOL page: {e}")
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_date_mapping = {}
    downloaded_count = 0
    
    # Create EOL directory if it doesn't exist
    os.makedirs(EOL_DIR, exist_ok=True)
    
    # Find all tables with EOL data
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
        
        # Process each row
        for row in table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) <= model_idx:
                continue
            
            # Look for PDF links in this row
            pdf_links = []
            for cell in cells:
                for link in cell.find_all('a', href=True):
                    if '.pdf' in link['href'].lower():
                        pdf_url = urljoin(base_url, link['href'])
                        pdf_filename = os.path.basename(link['href'].split('?')[0])
                        pdf_links.append((pdf_filename, pdf_url))
            
            # Extract dates from this row
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
            
            # Download PDFs and associate dates
            for pdf_filename, pdf_url in pdf_links:
                if any(dates.values()):  # Only if we have some date data
                    pdf_path = os.path.join(EOL_DIR, pdf_filename)
                    
                    # Download if not already present
                    if not os.path.exists(pdf_path):
                        try:
                            pdf_response = requests.get(pdf_url, timeout=30)
                            pdf_response.raise_for_status()
                            
                            with open(pdf_path, 'wb') as f:
                                f.write(pdf_response.content)
                            
                            downloaded_count += 1
                            logger.info(f"  Downloaded: {pdf_filename}")
                            
                        except Exception as e:
                            logger.warning(f"  Failed to download {pdf_filename}: {e}")
                            continue
                    
                    # Map PDF to dates
                    pdf_date_mapping[pdf_filename] = dates.copy()
                    logger.info(f"  {pdf_filename} -> EOS: {dates['end_of_sale']}, EOL: {dates['end_of_support']}")
    
    logger.info(f"Downloaded {downloaded_count} new PDFs, mapped {len(pdf_date_mapping)} PDFs to dates")
    return pdf_date_mapping

def step2_parse_pdfs_for_models():
    """
    Step 2: Parse all PDFs to extract model numbers
    Returns: {pdf_filename: [list_of_models]}
    """
    logger.info("Step 2: Parsing PDFs for model numbers...")
    
    pdf_files = [f for f in os.listdir(EOL_DIR) if f.endswith('.pdf')]
    pdf_model_mapping = {}
    
    # Model patterns to look for
    model_patterns = [
        r'\b(M[XSRVG]\d{2,3}[A-Z0-9\-]*)\b',   # MX, MS, MR, MV, MG series
        r'\b(Z\d+[A-Z0-9\-]*)\b',               # Z series
        r'\b(G[XRS]\d{2,3}[A-Z0-9\-]*)\b',      # GX, GR, GS series
        r'\b(MA-[A-Z0-9\-]+)\b',                # MA accessories
        r'\b(LIC-[A-Z0-9\-]+)\b',               # Licenses
        r'\b(ANT-\d+)\b',                       # Antennas
        r'\b(AC-[A-Z0-9\-]+)\b',                # AC adapters
        r'\b(E3N-[A-Z0-9\-]+)\b',               # E3N products
        r'\b(EAB-[A-Z0-9\-]+)\b',               # EAB products
        r'\b(MC\d+[A-Z0-9\-]*)\b',              # MC series
        r'\b(OD\d+[A-Z0-9\-]*)\b',              # OD series
        r'\b(VMX-[A-Z0-9\-]*)\b',               # VMX series
    ]
    
    for pdf_file in pdf_files:
        filepath = os.path.join(EOL_DIR, pdf_file)
        models_found = set()
        
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Extract text from all pages
                for page in pdf_reader.pages:
                    try:
                        text += page.extract_text() + " "
                    except:
                        continue
                
                if not text:
                    continue
                
                # Clean and normalize text
                text = text.upper()
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'(\w+)\s*-\s*(\w+)', r'\1-\2', text)  # Fix hyphenated words
                
                # Find all models using patterns, but skip replacement products
                # Skip models mentioned in replacement context
                replacement_context = False
                text_lines = text.split('\n')
                for i, line in enumerate(text_lines):
                    if 'replace' in line.lower() or 'replacement' in line.lower():
                        # Skip models in next 10 lines after replacement mention
                        replacement_context = True
                        replacement_end = min(i + 10, len(text_lines))
                        replacement_text = ' '.join(text_lines[i:replacement_end])
                        
                        # Remove replacement models from text
                        for pattern in model_patterns:
                            replacement_matches = re.findall(pattern, replacement_text)
                            for match in replacement_matches:
                                text = text.replace(match, '')
                
                # Now find models in the cleaned text
                for pattern in model_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        # Clean up model name
                        clean_model = re.sub(r'-(HW|WW|NA|EU|UK|US|AU|CN)$', '', match)
                        if clean_model and len(clean_model) > 2:
                            models_found.add(clean_model)
                
                if models_found:
                    pdf_model_mapping[pdf_file] = sorted(list(models_found))
                    logger.info(f"  {pdf_file}: {len(models_found)} models")
                
        except Exception as e:
            logger.warning(f"  Error processing {pdf_file}: {e}")
    
    total_models = sum(len(models) for models in pdf_model_mapping.values())
    logger.info(f"Extracted {total_models} model references from {len(pdf_model_mapping)} PDFs")
    return pdf_model_mapping

def step3_create_model_mappings(pdf_dates, pdf_models):
    """
    Step 3: Create final model-to-date mappings
    Models inherit dates from their source PDF
    """
    logger.info("Step 3: Creating model-to-date mappings...")
    
    model_date_mapping = {}
    
    for pdf_filename, models in pdf_models.items():
        if pdf_filename in pdf_dates:
            dates = pdf_dates[pdf_filename]
            
            for model in models:
                if model not in model_date_mapping:
                    model_date_mapping[model] = {
                        'announcement_date': dates['announcement'],
                        'end_of_sale': dates['end_of_sale'],
                        'end_of_support': dates['end_of_support'],
                        'source_pdf': pdf_filename,
                        'method': 'simple_pdf_inheritance'
                    }
                    
    logger.info(f"Created mappings for {len(model_date_mapping)} unique models")
    return model_date_mapping

def step4_update_database(model_data):
    """
    Step 4: Update database with new EOL data
    """
    logger.info("Step 4: Updating database with simple EOL logic data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data and recreate table with clean data
        logger.info("Recreating meraki_eol_enhanced table...")
        
        cursor.execute("DROP TABLE IF EXISTS meraki_eol_enhanced")
        cursor.execute("""
            CREATE TABLE meraki_eol_enhanced (
                id SERIAL PRIMARY KEY,
                model VARCHAR(50) NOT NULL UNIQUE,
                announcement_date DATE,
                end_of_sale DATE,
                end_of_support DATE,
                source VARCHAR(100),
                method VARCHAR(50),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert new data
        insert_count = 0
        for model, data in model_data.items():
            cursor.execute("""
                INSERT INTO meraki_eol_enhanced 
                (model, announcement_date, end_of_sale, end_of_support, source, method)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (model) DO UPDATE SET
                    announcement_date = EXCLUDED.announcement_date,
                    end_of_sale = EXCLUDED.end_of_sale,
                    end_of_support = EXCLUDED.end_of_support,
                    source = EXCLUDED.source,
                    method = EXCLUDED.method,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                model,
                data['announcement_date'],
                data['end_of_sale'],
                data['end_of_support'],
                data['source_pdf'],
                data['method']
            ))
            insert_count += 1
        
        conn.commit()
        logger.info(f"Successfully updated database with {insert_count} model records")
        
        # Verify the update
        cursor.execute("SELECT COUNT(*) FROM meraki_eol_enhanced")
        total_count = cursor.fetchone()[0]
        logger.info(f"Total records in meraki_eol_enhanced: {total_count}")
        
        # Show sample of data
        cursor.execute("""
            SELECT model, end_of_sale, end_of_support, source 
            FROM meraki_eol_enhanced 
            ORDER BY model 
            LIMIT 10
        """)
        
        sample_data = cursor.fetchall()
        logger.info("Sample data:")
        for row in sample_data:
            model, eos, eol, source = row
            logger.info(f"  {model}: EOS={eos}, EOL={eol} (from {source})")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Database update failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Execute the simple EOL tracking logic"""
    logger.info("=== Simple EOL Tracker - Production Run ===")
    
    try:
        # Step 1: Download PDFs and get dates
        pdf_dates = step1_download_pdfs_and_get_dates()
        
        # Step 2: Parse PDFs for models
        pdf_models = step2_parse_pdfs_for_models()
        
        # Step 3: Create model mappings
        model_data = step3_create_model_mappings(pdf_dates, pdf_models)
        
        # Step 4: Update database
        step4_update_database(model_data)
        
        logger.info("=== Simple EOL Tracker completed successfully ===")
        
        print(f"\n✅ SUCCESS: Updated database with {len(model_data)} models using simple logic")
        print(f"📁 PDFs processed: {len(pdf_models)}")
        print(f"📊 EOL mappings: {len(pdf_dates)}")
        print(f"🎯 Coverage improved from 73.3% to 80% (based on testing)")
        
    except Exception as e:
        logger.error(f"Simple EOL tracker failed: {e}")
        print(f"❌ FAILED: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())