#!/usr/bin/env python3
"""
EOL PDF Parser - Downloads and parses all EOL PDFs to extract model-specific EOL dates
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
import json

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

def create_eol_pdf_table(conn):
    """Create table for PDF-based EOL data"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meraki_eol_pdf (
                id SERIAL PRIMARY KEY,
                model VARCHAR(100) NOT NULL,
                model_family VARCHAR(100),
                announcement_date DATE,
                end_of_sale DATE,
                end_of_support DATE,
                source_pdf VARCHAR(200),
                pdf_url VARCHAR(500),
                pdf_hash VARCHAR(64),
                extracted_text TEXT,
                confidence VARCHAR(20) DEFAULT 'high',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(model, source_pdf)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eol_pdf_model 
            ON meraki_eol_pdf(model)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_eol_pdf_family 
            ON meraki_eol_pdf(model_family)
        """)
        
        conn.commit()
        logger.info("EOL PDF table created/verified")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        conn.rollback()
    finally:
        cursor.close()

def download_pdf(url, filename):
    """Download a PDF file"""
    try:
        # Clean filename
        clean_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        if not clean_filename.endswith('.pdf'):
            clean_filename += '.pdf'
        
        filepath = os.path.join(EOL_DIR, clean_filename)
        
        # Check if already downloaded
        if os.path.exists(filepath):
            logger.info(f"Already exists: {clean_filename}")
            return filepath
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded: {clean_filename} ({len(response.content)} bytes)")
        return filepath
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF with better error handling"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for i, page in enumerate(pdf_reader.pages):
                try:
                    text += page.extract_text() + "\n"
                except Exception as e:
                    logger.warning(f"Error extracting page {i}: {e}")
            return text
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return ""

def parse_dates_from_text(text):
    """Extract all three dates from PDF text"""
    dates = {
        'announcement': None,
        'end_of_sale': None,
        'end_of_support': None
    }
    
    # Convert text to lines for easier parsing
    lines = text.split('\n')
    
    # Date patterns
    date_patterns = [
        r'(\w+\s+\d{1,2},\s+\d{4})',  # January 1, 2024
        r'(\d{1,2}/\d{1,2}/\d{4})',    # 01/01/2024
        r'(\d{4}-\d{2}-\d{2})',        # 2024-01-02
    ]
    
    # Search for dates with context
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Announcement date
        if any(phrase in line_lower for phrase in ['announcement', 'announced', 'notice date']):
            for j in range(max(0, i-2), min(len(lines), i+3)):
                for pattern in date_patterns:
                    match = re.search(pattern, lines[j])
                    if match and not dates['announcement']:
                        dates['announcement'] = match.group(1)
                        break
        
        # End of Sale date
        if any(phrase in line_lower for phrase in ['end of sale', 'end-of-sale', 'last order', 'eos date']):
            for j in range(max(0, i-2), min(len(lines), i+3)):
                for pattern in date_patterns:
                    match = re.search(pattern, lines[j])
                    if match and not dates['end_of_sale']:
                        dates['end_of_sale'] = match.group(1)
                        break
        
        # End of Support date
        if any(phrase in line_lower for phrase in ['end of support', 'end-of-support', 'last date of support', 'eol date']):
            for j in range(max(0, i-2), min(len(lines), i+3)):
                for pattern in date_patterns:
                    match = re.search(pattern, lines[j])
                    if match and not dates['end_of_support']:
                        dates['end_of_support'] = match.group(1)
                        break
    
    return dates

def extract_models_from_text(text, focus_family=None):
    """Extract all Meraki model numbers from text"""
    models = {}
    
    # Common Meraki model patterns
    model_patterns = [
        # MS switches
        (r'MS(\d{3,4})-(\d+)(P|LP|FP|UP|UX|UX2)?(?:-HW)?', 'MS'),
        # MR access points
        (r'MR(\d{2,3})(?:-HW)?', 'MR'),
        # MX security appliances
        (r'MX(\d{2,3})(?:-HW)?', 'MX'),
        # MV cameras
        (r'MV(\d{2,3})(?:-HW)?', 'MV'),
        # Other models
        (r'(MS|MR|MX|MV|MG|MT|MA)[-\s]?(\d+)([-\s]?\w+)?', 'Generic'),
    ]
    
    # If focusing on a specific family
    if focus_family and focus_family.startswith('MS220'):
        # Special handling for MS220 family
        ms220_pattern = r'MS220-(\d+)(P|LP|FP)?'
        matches = re.findall(ms220_pattern, text, re.IGNORECASE)
        for match in matches:
            port_count = match[0]
            variant = match[1] if match[1] else ''
            model = f"MS220-{port_count}{variant}"
            if model not in models:
                models[model] = {'family': 'MS220', 'base': f"MS220-{port_count}"}
        
        # Also check for generic MS220 mentions
        if re.search(r'MS220\s+(series|family|switches)', text, re.IGNORECASE):
            models['MS220'] = {'family': 'MS220', 'base': 'MS220'}
    else:
        # General model extraction
        for pattern, family in model_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if family == 'MS':
                        series = match[0]
                        ports = match[1]
                        variant = match[2] if len(match) > 2 and match[2] else ''
                        model = f"MS{series}-{ports}{variant}".upper()
                        models[model] = {'family': f"MS{series}", 'base': f"MS{series}-{ports}"}
                    else:
                        model = ''.join(match).upper()
                        models[model] = {'family': family, 'base': model}
                else:
                    model = match.upper()
                    models[model] = {'family': family, 'base': model}
    
    return models

def parse_date_string(date_str):
    """Convert date string to date object"""
    if not date_str:
        return None
    
    formats = [
        '%B %d, %Y',      # January 1, 2024
        '%b %d, %Y',      # Jan 1, 2024
        '%m/%d/%Y',       # 01/01/2024
        '%d/%m/%Y',       # 01/01/2024
        '%Y-%m-%d',       # 2024-01-01
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except:
            continue
    
    return None

def process_pdf(pdf_path, pdf_url, pdf_name, conn):
    """Process a single PDF and extract EOL data"""
    cursor = conn.cursor()
    
    try:
        # Calculate PDF hash
        with open(pdf_path, 'rb') as f:
            pdf_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Check if we've already processed this PDF
        cursor.execute("""
            SELECT COUNT(*) FROM meraki_eol_pdf 
            WHERE pdf_hash = %s
        """, (pdf_hash,))
        
        if cursor.fetchone()[0] > 0:
            logger.info(f"Already processed: {pdf_name}")
            return 0
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"No text extracted from {pdf_name}")
            return 0
        
        # Extract dates
        dates = parse_dates_from_text(text)
        
        # Determine model family from filename or content
        family = None
        if 'MS220' in pdf_name:
            family = 'MS220'
        elif 'MS320' in pdf_name:
            family = 'MS320'
        
        # Extract models
        models = extract_models_from_text(text, family)
        
        if not models:
            logger.warning(f"No models found in {pdf_name}")
            return 0
        
        # Store data for each model
        count = 0
        for model, model_info in models.items():
            try:
                cursor.execute("""
                    INSERT INTO meraki_eol_pdf (
                        model, model_family, announcement_date, 
                        end_of_sale, end_of_support, source_pdf, 
                        pdf_url, pdf_hash, extracted_text
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (model, source_pdf) DO UPDATE SET
                        announcement_date = EXCLUDED.announcement_date,
                        end_of_sale = EXCLUDED.end_of_sale,
                        end_of_support = EXCLUDED.end_of_support,
                        pdf_hash = EXCLUDED.pdf_hash,
                        extracted_text = EXCLUDED.extracted_text,
                        updated_at = NOW()
                """, (
                    model,
                    model_info['family'],
                    parse_date_string(dates['announcement']),
                    parse_date_string(dates['end_of_sale']),
                    parse_date_string(dates['end_of_support']),
                    pdf_name,
                    pdf_url,
                    pdf_hash,
                    text[:5000]  # Store first 5000 chars
                ))
                count += 1
            except Exception as e:
                logger.error(f"Error storing {model}: {e}")
        
        conn.commit()
        logger.info(f"Stored {count} models from {pdf_name}")
        return count
        
    except Exception as e:
        logger.error(f"Error processing {pdf_name}: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()

def main():
    """Main function"""
    logger.info("Starting EOL PDF Parser")
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Create table
        create_eol_pdf_table(conn)
        
        # Get EOL page
        base_url = "https://documentation.meraki.com"
        eol_url = f"{base_url}/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
        
        logger.info("Fetching EOL page...")
        response = requests.get(eol_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all PDF links
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.pdf' in href.lower():
                full_url = urljoin(base_url, href)
                filename = os.path.basename(href).split('?')[0]
                pdf_links.append({
                    'url': full_url,
                    'text': link.get_text(strip=True),
                    'filename': filename
                })
        
        logger.info(f"Found {len(pdf_links)} PDF links")
        
        # Process PDFs
        total_models = 0
        for pdf in pdf_links:
            logger.info(f"\nProcessing: {pdf['filename']}")
            
            # Download PDF
            pdf_path = download_pdf(pdf['url'], pdf['filename'])
            if not pdf_path:
                continue
            
            # Process PDF
            count = process_pdf(pdf_path, pdf['url'], pdf['filename'], conn)
            total_models += count
        
        # Summary
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT model) as models,
                   COUNT(DISTINCT source_pdf) as pdfs,
                   COUNT(DISTINCT model_family) as families
            FROM meraki_eol_pdf
        """)
        
        stats = cursor.fetchone()
        logger.info(f"\n=== Summary ===")
        logger.info(f"Total models: {stats[0]}")
        logger.info(f"Total PDFs: {stats[1]}")
        logger.info(f"Model families: {stats[2]}")
        
        # Show MS220 specific data
        cursor.execute("""
            SELECT model, end_of_sale, end_of_support, source_pdf
            FROM meraki_eol_pdf
            WHERE model LIKE 'MS220%'
            ORDER BY model
        """)
        
        ms220_data = cursor.fetchall()
        if ms220_data:
            logger.info(f"\n=== MS220 Models Found ===")
            for model, eos, eol, pdf in ms220_data:
                logger.info(f"{model}: EOS={eos}, EOL={eol} (from {pdf})")
        
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()