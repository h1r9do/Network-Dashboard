#!/usr/bin/env python3
"""
Parse ALL EOL PDFs to extract model numbers and dates
This comprehensive parser handles various PDF formats
"""

import os
import sys
import PyPDF2
import re
import logging
import psycopg2
from datetime import datetime, date
import json

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
    
    # Clean up
    date_str = date_str.strip()
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)  # Remove ordinals
    
    formats = [
        '%B %d, %Y',      # January 1, 2024
        '%b %d, %Y',      # Jan 1, 2024
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

def extract_model_data_generic(text, filename):
    """Generic extraction for various PDF formats"""
    models = {}
    
    # Common patterns for model numbers
    model_patterns = [
        r'(M[XSRVG]\d+[A-Z0-9\-]*)',  # MX, MS, MR, MV, MG series
        r'(Z\d+[A-Z0-9\-]*)',          # Z series
        r'(GX\d+[A-Z0-9\-]*)',         # GX series
        r'(GR\d+[A-Z0-9\-]*)',         # GR series
        r'(GS\d+[A-Z0-9\-]*)',         # GS series
        r'(MA-[A-Z0-9\-]+)',           # MA accessories
        r'(LIC-[A-Z0-9\-]+)',          # Licenses
        r'(ANT-\d+)',                  # Antennas
        r'(AC-[A-Z0-9\-]+)',           # AC adapters
    ]
    
    # Find all potential model numbers
    found_models = set()
    for pattern in model_patterns:
        matches = re.findall(pattern, text.upper())
        found_models.update(matches)
    
    # Date patterns to look for
    date_indicators = {
        'announcement': [
            r'announce[d\s]*.*?(\w+\s+\d{1,2},?\s+\d{4})',
            r'notification.*?(\w+\s+\d{1,2},?\s+\d{4})',
            r'effective.*?(\w+\s+\d{1,2},?\s+\d{4})'
        ],
        'end_of_sale': [
            r'end[\s\-]*of[\s\-]*sale.*?(\w+\s+\d{1,2},?\s+\d{4})',
            r'last[\s\-]*order.*?(\w+\s+\d{1,2},?\s+\d{4})',
            r'final[\s\-]*order.*?(\w+\s+\d{1,2},?\s+\d{4})',
            r'eos.*?(\w+\s+\d{1,2},?\s+\d{4})'
        ],
        'end_of_support': [
            r'end[\s\-]*of[\s\-]*support.*?(\w+\s+\d{1,2},?\s+\d{4})',
            r'end[\s\-]*of[\s\-]*life.*?(\w+\s+\d{1,2},?\s+\d{4})',
            r'eol.*?(\w+\s+\d{1,2},?\s+\d{4})',
            r'support[\s\-]*end.*?(\w+\s+\d{1,2},?\s+\d{4})'
        ]
    }
    
    # Extract dates
    dates_found = {}
    for date_type, patterns in date_indicators.items():
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                # Take the first valid date found
                for match in matches:
                    parsed_date = parse_date_string(match)
                    if parsed_date:
                        dates_found[date_type] = parsed_date
                        break
                if date_type in dates_found:
                    break
    
    # Apply dates to all models found in this PDF
    for model in found_models:
        # Clean up model name
        model = model.strip('-HW').strip()
        if model and len(model) > 2:  # Skip very short strings
            models[model] = {
                'description': f'{model} from {filename}',
                'announcement_date': dates_found.get('announcement'),
                'end_of_sale': dates_found.get('end_of_sale'),
                'end_of_support': dates_found.get('end_of_support'),
                'source_pdf': filename
            }
    
    return models

def extract_from_table_format(text):
    """Extract from table-formatted PDFs"""
    models = {}
    
    # Look for table headers
    if 'MODEL' in text.upper() and ('END-OF-SALE' in text.upper() or 'END OF SALE' in text.upper()):
        # Try to parse table rows
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Skip headers and empty lines
            if not line.strip() or 'MODEL' in line.upper():
                continue
            
            # Look for lines that might be table rows
            # Pattern: Model Description Date Date Date
            row_match = re.match(r'([A-Z0-9\-]+)\s+(.+?)\s+(\w+\s+\d+,?\s+\d{4})\s+(\w+\s+\d+,?\s+\d{4})\s+(\w+\s+\d+,?\s+\d{4})', line)
            if row_match:
                model = row_match.group(1)
                desc = row_match.group(2)
                date1 = parse_date_string(row_match.group(3))
                date2 = parse_date_string(row_match.group(4))
                date3 = parse_date_string(row_match.group(5))
                
                models[model] = {
                    'description': desc,
                    'announcement_date': date1,
                    'end_of_sale': date2,
                    'end_of_support': date3
                }
    
    return models

def process_pdf(filepath):
    """Process a single PDF file"""
    try:
        filename = os.path.basename(filepath)
        logger.info(f"Processing: {filename}")
        
        # Extract text
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        # Try different extraction methods
        models = {}
        
        # Method 1: Table format
        table_models = extract_from_table_format(text)
        models.update(table_models)
        
        # Method 2: Generic extraction
        generic_models = extract_model_data_generic(text, filename)
        models.update(generic_models)
        
        # Method 3: Special handling for specific formats
        if 'MS220' in filename.upper():
            # Use our specific MS220 parser
            from enhanced_eol_tracker import extract_ms220_data_from_pdf
            ms220_models = extract_ms220_data_from_pdf(text)
            for model, data in ms220_models.items():
                if model not in models and data.get('dates', {}).get('end_of_sale'):
                    models[model] = {
                        'description': data.get('description', ''),
                        'announcement_date': data['dates'].get('announcement'),
                        'end_of_sale': data['dates'].get('end_of_sale'),
                        'end_of_support': data['dates'].get('end_of_support'),
                        'source_pdf': filename
                    }
        
        return models
        
    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}")
        return {}

def store_in_database(models, conn):
    """Store extracted models in database"""
    cursor = conn.cursor()
    stored = 0
    
    for model, data in models.items():
        try:
            cursor.execute("""
                INSERT INTO meraki_eol_enhanced (
                    model, description, announcement_date, end_of_sale, 
                    end_of_support, source, pdf_name, confidence
                ) VALUES (%s, %s, %s, %s, %s, 'PDF', %s, 'medium')
                ON CONFLICT (model) DO UPDATE SET
                    description = COALESCE(EXCLUDED.description, meraki_eol_enhanced.description),
                    announcement_date = COALESCE(EXCLUDED.announcement_date, meraki_eol_enhanced.announcement_date),
                    end_of_sale = COALESCE(EXCLUDED.end_of_sale, meraki_eol_enhanced.end_of_sale),
                    end_of_support = COALESCE(EXCLUDED.end_of_support, meraki_eol_enhanced.end_of_support),
                    pdf_name = EXCLUDED.pdf_name,
                    updated_at = NOW()
                WHERE 
                    EXCLUDED.end_of_sale IS NOT NULL OR 
                    EXCLUDED.end_of_support IS NOT NULL
            """, (
                model,
                data.get('description', ''),
                data.get('announcement_date'),
                data.get('end_of_sale'),
                data.get('end_of_support'),
                data.get('source_pdf', '')
            ))
            
            if cursor.rowcount > 0:
                stored += 1
                
        except Exception as e:
            logger.error(f"Error storing {model}: {e}")
    
    conn.commit()
    return stored

def main():
    """Main function"""
    logger.info("Starting comprehensive EOL PDF parsing")
    
    # Get all PDFs
    pdf_files = [f for f in os.listdir(EOL_DIR) if f.endswith('.pdf')]
    logger.info(f"Found {len(pdf_files)} PDFs to process")
    
    # Connect to database
    conn = get_db_connection()
    
    # Process all PDFs
    all_models = {}
    
    for pdf_file in pdf_files:
        filepath = os.path.join(EOL_DIR, pdf_file)
        models = process_pdf(filepath)
        
        if models:
            logger.info(f"  Extracted {len(models)} models from {pdf_file}")
            all_models.update(models)
    
    # Store in database
    logger.info(f"\nTotal unique models extracted: {len(all_models)}")
    stored = store_in_database(all_models, conn)
    logger.info(f"Stored/updated {stored} models in database")
    
    # Show summary
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN end_of_support <= CURRENT_DATE THEN 1 END) as eol,
               COUNT(CASE WHEN end_of_sale <= CURRENT_DATE AND end_of_support > CURRENT_DATE THEN 1 END) as eos,
               COUNT(CASE WHEN end_of_sale > CURRENT_DATE THEN 1 END) as active
        FROM meraki_eol_enhanced
    """)
    
    total, eol, eos, active = cursor.fetchone()
    logger.info(f"\n=== Database Summary ===")
    logger.info(f"Total models: {total}")
    logger.info(f"End of Life (EOL): {eol}")
    logger.info(f"End of Sale (EOS): {eos}")
    logger.info(f"Active: {active}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()