#!/usr/bin/env python3
"""
Enhanced PDF Parser that thoroughly extracts ALL models and dates from EOL PDFs
This parser is designed to handle various PDF formats and extract all relevant data
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
    
    # Clean up the string
    date_str = date_str.strip()
    # Remove ordinals (1st, 2nd, 3rd, 4th, etc.)
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    # Remove extra spaces
    date_str = re.sub(r'\s+', ' ', date_str)
    
    formats = [
        '%B %d, %Y',      # January 1, 2024
        '%b %d, %Y',      # Jan 1, 2024
        '%B %d %Y',       # January 1 2024 (no comma)
        '%b %d %Y',       # Jan 1 2024 (no comma)
        '%m/%d/%Y',       # 01/01/2024
        '%Y-%m-%d',       # 2024-01-01
        '%d %B %Y',       # 1 January 2024
        '%d-%b-%Y',       # 1-Jan-2024
        '%m-%d-%Y',       # 01-01-2024
        '%d/%m/%Y',       # 01/01/2024 (European format)
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    
    # Try to extract just month day year
    match = re.search(r'(\w+)\s+(\d+),?\s+(\d{4})', date_str)
    if match:
        try:
            month, day, year = match.groups()
            return datetime.strptime(f"{month} {day}, {year}", '%B %d, %Y').date()
        except:
            try:
                return datetime.strptime(f"{month} {day}, {year}", '%b %d, %Y').date()
            except:
                pass
    
    return None

def extract_all_models_and_dates(text, filename):
    """Enhanced extraction that captures all models and their dates"""
    results = {}
    
    # Clean text - normalize whitespace and remove special characters
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ').replace('\r', ' ')
    # Fix hyphenated words that got split
    text = re.sub(r'(\w+)\s*-\s*(\w+)', r'\1-\2', text)
    
    # Step 1: Find model tables or lists
    # Look for sections with MODEL NUMBER headers
    model_sections = re.findall(
        r'MODEL\s*NUMBER\s*(.*?)(?:The\s+following|We\s+expect|will\s+replace|$)', 
        text, 
        re.IGNORECASE | re.DOTALL
    )
    
    # Extract models from table sections
    all_models = []
    for section in model_sections:
        # Find model patterns in the section
        models = re.findall(r'([A-Z]{2,3}\d{2,3}[A-Z0-9\-]*)', section)
        all_models.extend(models)
    
    # Step 2: Also find models mentioned anywhere in the text
    # Comprehensive model patterns
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
    ]
    
    for pattern in model_patterns:
        matches = re.findall(pattern, text)
        all_models.extend(matches)
    
    # Remove duplicates and clean up
    all_models = list(set(m.strip().upper() for m in all_models if len(m) > 2))
    
    # Remove common suffixes that aren't part of the base model
    cleaned_models = []
    for model in all_models:
        # Remove -HW, -WW, -NA, -EU, -UK, -US suffixes
        clean_model = re.sub(r'-(HW|WW|NA|EU|UK|US|AU|CN)$', '', model)
        if clean_model:
            cleaned_models.append(clean_model)
    
    all_models = list(set(cleaned_models))
    
    # Step 3: Find all dates in the document
    date_patterns = [
        r'(\w+\s+\d{1,2},?\s+\d{4})',           # Month DD, YYYY
        r'(\d{1,2}\s+\w+\s+\d{4})',             # DD Month YYYY
        r'(\d{1,2}/\d{1,2}/\d{4})',             # MM/DD/YYYY
        r'(\d{4}-\d{1,2}-\d{1,2})',             # YYYY-MM-DD
    ]
    
    all_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            parsed = parse_date_string(match)
            if parsed:
                all_dates.append((match, parsed))
    
    # Step 4: Look for specific date contexts
    date_contexts = {}
    
    # Announcement date patterns
    ann_patterns = [
        r'announce[d\s]+on\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'effective\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'notification\s+date[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
    ]
    
    for pattern in ann_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date = parse_date_string(match.group(1))
            if date:
                date_contexts['announcement'] = date
                break
    
    # End of Sale date patterns
    eos_patterns = [
        r'end[\s\-]*of[\s\-]*sale[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
        r'last\s+order[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
        r'final\s+orders.*?until\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'accepting\s+final\s+orders.*?until\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'orders.*?accepted\s+through\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'will\s+be\s+(\w+\s+\d{1,2},?\s+\d{4}).*?end[\s\-]*of[\s\-]*sale',
    ]
    
    for pattern in eos_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            date = parse_date_string(match.group(1))
            if date:
                date_contexts['end_of_sale'] = date
                break
    
    # End of Support date patterns
    eol_patterns = [
        r'end[\s\-]*of[\s\-]*support[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
        r'end[\s\-]*of[\s\-]*life[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
        r'support.*?will\s+be\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'support.*?through\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'will\s+be\s+(\w+\s+\d{1,2},?\s+\d{4}).*?end[\s\-]*of[\s\-]*support',
    ]
    
    for pattern in eol_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            date = parse_date_string(match.group(1))
            if date:
                date_contexts['end_of_support'] = date
                break
    
    # Step 5: Special handling for common patterns
    # Look for "End-of-Support will be [X] years after the End-of-Sale Date"
    years_pattern = re.search(r'End-of-Support.*?(\d+)\s*years?\s*after.*?End-of-Sale', text, re.IGNORECASE)
    if years_pattern and 'end_of_sale' in date_contexts:
        years = int(years_pattern.group(1))
        eos_date = date_contexts['end_of_sale']
        try:
            eol_date = date(eos_date.year + years, eos_date.month, eos_date.day)
            date_contexts['end_of_support'] = eol_date
        except:
            pass
    
    # Look for date sequences (often announcement, EOS, EOL in order)
    if len(all_dates) >= 3 and not all(date_contexts.values()):
        # Sort dates chronologically
        sorted_dates = sorted(all_dates, key=lambda x: x[1])
        
        # If we have exactly 3 dates, they might be announcement, EOS, EOL
        if len(sorted_dates) >= 3:
            if 'announcement' not in date_contexts:
                date_contexts['announcement'] = sorted_dates[0][1]
            if 'end_of_sale' not in date_contexts:
                date_contexts['end_of_sale'] = sorted_dates[1][1]
            if 'end_of_support' not in date_contexts:
                date_contexts['end_of_support'] = sorted_dates[-1][1]
    
    # Step 6: Create results for all models with the dates found
    for model in all_models:
        results[model] = {
            'description': f'{model} - EOL from {filename}',
            'announcement_date': date_contexts.get('announcement'),
            'end_of_sale': date_contexts.get('end_of_sale'),
            'end_of_support': date_contexts.get('end_of_support'),
            'source_pdf': filename,
            'confidence': 'high' if len(date_contexts) >= 2 else 'medium'
        }
    
    # Log what we found
    if results:
        logger.info(f"  Found {len(results)} models with {len(date_contexts)} dates")
        if date_contexts:
            logger.debug(f"  Dates: {date_contexts}")
    
    return results

def process_pdf(filepath):
    """Process a single PDF file with enhanced extraction"""
    try:
        filename = os.path.basename(filepath)
        logger.info(f"Processing: {filename}")
        
        # Extract all text from PDF
        text = ""
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"  Error extracting page {page_num}: {e}")
        
        if not text:
            logger.warning(f"  No text extracted from {filename}")
            return {}
        
        # Extract models and dates
        models = extract_all_models_and_dates(text, filename)
        
        return models
        
    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return {}

def update_database(models, conn):
    """Update database with extracted models"""
    cursor = conn.cursor()
    
    # First, create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meraki_eol_enhanced (
            id SERIAL PRIMARY KEY,
            model VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            replacement_model VARCHAR(200),
            announcement_date DATE,
            end_of_sale DATE,
            end_of_support DATE,
            source VARCHAR(50) DEFAULT 'PDF',
            pdf_name VARCHAR(200),
            pdf_url VARCHAR(500),
            confidence VARCHAR(20) DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    stored = 0
    updated = 0
    
    for model, data in models.items():
        try:
            # Only update if we have at least one date
            if data.get('end_of_sale') or data.get('end_of_support'):
                cursor.execute("""
                    INSERT INTO meraki_eol_enhanced (
                        model, description, announcement_date, end_of_sale, 
                        end_of_support, source, pdf_name, confidence
                    ) VALUES (%s, %s, %s, %s, %s, 'PDF', %s, %s)
                    ON CONFLICT (model) DO UPDATE SET
                        description = COALESCE(EXCLUDED.description, meraki_eol_enhanced.description),
                        announcement_date = COALESCE(EXCLUDED.announcement_date, meraki_eol_enhanced.announcement_date),
                        end_of_sale = COALESCE(EXCLUDED.end_of_sale, meraki_eol_enhanced.end_of_sale),
                        end_of_support = COALESCE(EXCLUDED.end_of_support, meraki_eol_enhanced.end_of_support),
                        pdf_name = EXCLUDED.pdf_name,
                        confidence = EXCLUDED.confidence,
                        updated_at = NOW()
                    WHERE 
                        (EXCLUDED.end_of_sale IS NOT NULL AND 
                         (meraki_eol_enhanced.end_of_sale IS NULL OR EXCLUDED.confidence = 'high'))
                        OR
                        (EXCLUDED.end_of_support IS NOT NULL AND 
                         (meraki_eol_enhanced.end_of_support IS NULL OR EXCLUDED.confidence = 'high'))
                """, (
                    model,
                    data.get('description', ''),
                    data.get('announcement_date'),
                    data.get('end_of_sale'),
                    data.get('end_of_support'),
                    data.get('source_pdf', ''),
                    data.get('confidence', 'medium')
                ))
                
                if cursor.rowcount > 0:
                    if 'INSERT' in cursor.statusmessage:
                        stored += 1
                    else:
                        updated += 1
                
        except Exception as e:
            logger.error(f"Error storing {model}: {e}")
    
    conn.commit()
    cursor.close()
    
    return stored, updated

def main():
    """Main function to process all PDFs"""
    logger.info("=== Enhanced EOL PDF Parser ===")
    
    # Get all PDFs
    pdf_files = sorted([f for f in os.listdir(EOL_DIR) if f.endswith('.pdf')])
    logger.info(f"Found {len(pdf_files)} PDFs to process")
    
    # Connect to database
    conn = get_db_connection()
    
    # Process all PDFs
    all_models = {}
    
    for i, pdf_file in enumerate(pdf_files, 1):
        logger.info(f"\n[{i}/{len(pdf_files)}] {pdf_file}")
        
        filepath = os.path.join(EOL_DIR, pdf_file)
        models = process_pdf(filepath)
        
        if models:
            logger.info(f"  Extracted {len(models)} models")
            # Merge with existing, preferring higher confidence
            for model, data in models.items():
                if model not in all_models or data.get('confidence') == 'high':
                    all_models[model] = data
        else:
            logger.warning(f"  No models extracted")
    
    # Update database
    logger.info(f"\n=== Updating Database ===")
    logger.info(f"Total unique models found: {len(all_models)}")
    
    stored, updated = update_database(all_models, conn)
    logger.info(f"New models stored: {stored}")
    logger.info(f"Existing models updated: {updated}")
    
    # Show summary
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN end_of_support <= CURRENT_DATE THEN 1 END) as eol,
            COUNT(CASE WHEN end_of_sale <= CURRENT_DATE AND end_of_support > CURRENT_DATE THEN 1 END) as eos,
            COUNT(CASE WHEN end_of_sale > CURRENT_DATE THEN 1 END) as active,
            COUNT(DISTINCT pdf_name) as pdfs
        FROM meraki_eol_enhanced
    """)
    
    total, eol, eos, active, pdfs = cursor.fetchone()
    
    logger.info(f"\n=== Database Summary ===")
    logger.info(f"Total models in database: {total}")
    logger.info(f"  - End of Life (red): {eol}")
    logger.info(f"  - End of Sale (yellow): {eos}")
    logger.info(f"  - Active (blue): {active}")
    logger.info(f"Source PDFs: {pdfs}")
    
    # Show sample of recent additions
    cursor.execute("""
        SELECT model, end_of_sale, end_of_support, pdf_name
        FROM meraki_eol_enhanced
        WHERE model LIKE 'MS120%'
        ORDER BY model
        LIMIT 10
    """)
    
    logger.info(f"\n=== Sample MS120 Models ===")
    for model, eos, eol, pdf in cursor.fetchall():
        logger.info(f"{model}: EOS={eos}, EOL={eol} (PDF: {pdf})")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()