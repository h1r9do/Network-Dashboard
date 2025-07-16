#!/usr/bin/env python3
"""
Meraki EOL Tracker - Enhanced End-of-Life tracking system
Downloads and parses EOL PDFs, maintains database of EOL information
"""

import os
import sys
import requests
import logging
import hashlib
import json
import re
from datetime import datetime, date
from urllib.parse import urljoin, urlparse
import PyPDF2
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import Json, execute_values

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/meraki-eol-tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Data directories
DATA_DIR = "/var/www/html/meraki-data"
EOL_PDF_DIR = os.path.join(DATA_DIR, "eol_pdfs")
EOL_CACHE_FILE = os.path.join(DATA_DIR, "eol_tracker_state.json")

# Create directories if needed
os.makedirs(EOL_PDF_DIR, exist_ok=True)

# EOL documentation URL
EOL_URL = "https://documentation.meraki.com/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
EOL_CSV_URL = "https://documentation.meraki.com/@api/deki/files/30186/Meraki_EOS_Summary.csv?revision=2"

def get_db_connection():
    """Get database connection using config"""
    import re
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

def create_eol_table(conn):
    """Create EOL tracking table if not exists"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meraki_eol (
                id SERIAL PRIMARY KEY,
                model VARCHAR(100) NOT NULL,
                model_variants TEXT,  -- JSON array of all model variants
                announcement_date DATE,
                end_of_sale_date DATE,
                end_of_support_date DATE,
                pdf_url VARCHAR(500),
                pdf_filename VARCHAR(200),
                pdf_hash VARCHAR(64),
                csv_source BOOLEAN DEFAULT FALSE,
                pdf_source BOOLEAN DEFAULT FALSE,
                raw_text TEXT,  -- Raw text extracted from PDF
                parsed_data JSONB,  -- Additional parsed data
                last_checked TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_eol_model ON meraki_eol(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_eol_dates ON meraki_eol(end_of_sale_date, end_of_support_date)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_eol_model_pdf ON meraki_eol(model, pdf_url) WHERE pdf_url IS NOT NULL")
        
        # Create state tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eol_tracker_state (
                id SERIAL PRIMARY KEY,
                last_page_hash VARCHAR(64),
                last_csv_hash VARCHAR(64),
                last_check_time TIMESTAMP,
                pdf_inventory JSONB,  -- Track all known PDFs
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        conn.commit()
        logger.info("EOL tables created/verified")
        
    except Exception as e:
        logger.error(f"Error creating EOL tables: {e}")
        conn.rollback()
    finally:
        cursor.close()

def get_page_hash(content):
    """Generate hash of page content for change detection"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def download_file(url, filename):
    """Download file with proper error handling"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        filepath = os.path.join(EOL_PDF_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded: {filename}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return None

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""

def parse_eol_dates(text):
    """Parse EOL dates from text"""
    dates = {
        'announcement_date': None,
        'end_of_sale_date': None,
        'end_of_support_date': None
    }
    
    # Common date patterns
    date_patterns = [
        r'(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})'
    ]
    
    # Look for specific phrases
    patterns = {
        'announcement_date': [
            r'announcement\s*date[:\s]+([^,\n]+)',
            r'announced\s+on\s+([^,\n]+)',
            r'effective\s+([^,\n]+)'
        ],
        'end_of_sale_date': [
            r'end[\s-]*of[\s-]*sale[:\s]+([^,\n]+)',
            r'last\s+date\s+to\s+order[:\s]+([^,\n]+)',
            r'eos\s+date[:\s]+([^,\n]+)'
        ],
        'end_of_support_date': [
            r'end[\s-]*of[\s-]*support[:\s]+([^,\n]+)',
            r'last\s+date\s+of\s+support[:\s]+([^,\n]+)',
            r'eol\s+date[:\s]+([^,\n]+)'
        ]
    }
    
    # Search for dates
    for date_type, search_patterns in patterns.items():
        for pattern in search_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                # Try to parse the date
                parsed_date = parse_date_string(date_str)
                if parsed_date:
                    dates[date_type] = parsed_date
                    break
    
    return dates

def parse_date_string(date_str):
    """Parse various date formats"""
    if not date_str or date_str.lower() in ['n/a', 'tbd', 'to be determined']:
        return None
    
    # Clean up the string
    date_str = date_str.strip().replace(',', '')
    
    # Try different date formats
    formats = [
        '%B %d %Y',      # January 15 2024
        '%b %d %Y',      # Jan 15 2024
        '%m/%d/%Y',      # 01/15/2024
        '%Y-%m-%d',      # 2024-01-15
        '%d %B %Y',      # 15 January 2024
        '%d %b %Y'       # 15 Jan 2024
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    
    # Try to extract just month and year if full date parsing fails
    month_year_match = re.search(r'(\b(?:January|February|March|April|May|June|July|August|September|October|November|December))\s+(\d{4})', date_str, re.IGNORECASE)
    if month_year_match:
        try:
            # Default to first day of month
            return datetime.strptime(f"{month_year_match.group(1)} 1 {month_year_match.group(2)}", '%B %d %Y').date()
        except:
            pass
    
    return None

def extract_models_from_pdf(text):
    """Extract model numbers from PDF text"""
    models = set()
    
    # Common Meraki model patterns
    model_patterns = [
        r'\b(M[XRSV]\d{2,3}(?:-\d+)?(?:[A-Z]{1,3})?(?:-HW)?)\b',  # MX, MR, MS, MV models
        r'\b(M[A-Z]-[A-Z]+-[A-Z0-9-]+)\b',  # MA-MNT-MV-61 style
        r'\b(LIC-[A-Z0-9-]+)\b',  # License models
        r'\b(G[A-Z]-[A-Z]+-[A-Z0-9-]+)\b',  # GO models
        r'\b(Z\d+(?:-[A-Z]+)?)\b',  # Z series
        r'\b(MG\d+(?:[A-Z])?(?:-HW)?)\b'  # MG models
    ]
    
    for pattern in model_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            models.add(match.upper())
    
    return list(models)

def process_eol_pdf(pdf_url, pdf_filename, conn):
    """Process an EOL PDF file"""
    cursor = conn.cursor()
    
    try:
        # Check if we already processed this PDF
        cursor.execute("SELECT pdf_hash FROM meraki_eol WHERE pdf_url = %s LIMIT 1", (pdf_url,))
        existing = cursor.fetchone()
        
        # Download PDF
        filepath = download_file(pdf_url, pdf_filename)
        if not filepath:
            return False
        
        # Calculate hash
        with open(filepath, 'rb') as f:
            pdf_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Skip if unchanged
        if existing and existing[0] == pdf_hash:
            logger.info(f"PDF unchanged: {pdf_filename}")
            return False
        
        # Extract text
        text = extract_pdf_text(filepath)
        if not text:
            logger.warning(f"No text extracted from {pdf_filename}")
            return False
        
        # Parse dates
        dates = parse_eol_dates(text)
        
        # Extract models
        models = extract_models_from_pdf(text)
        if not models:
            logger.warning(f"No models found in {pdf_filename}")
            return False
        
        # Use first model as primary, store all as variants
        primary_model = models[0]
        
        # Prepare data
        eol_data = {
            'model': primary_model,
            'model_variants': Json(models),
            'announcement_date': dates['announcement_date'],
            'end_of_sale_date': dates['end_of_sale_date'],
            'end_of_support_date': dates['end_of_support_date'],
            'pdf_url': pdf_url,
            'pdf_filename': pdf_filename,
            'pdf_hash': pdf_hash,
            'pdf_source': True,
            'raw_text': text[:10000],  # Store first 10k chars
            'parsed_data': Json({
                'dates_found': {k: str(v) if v else None for k, v in dates.items()},
                'models_found': models,
                'extraction_time': datetime.now().isoformat()
            })
        }
        
        # Insert or update
        cursor.execute("""
            INSERT INTO meraki_eol (
                model, model_variants, announcement_date, end_of_sale_date,
                end_of_support_date, pdf_url, pdf_filename, pdf_hash,
                pdf_source, raw_text, parsed_data
            ) VALUES (
                %(model)s, %(model_variants)s, %(announcement_date)s,
                %(end_of_sale_date)s, %(end_of_support_date)s, %(pdf_url)s,
                %(pdf_filename)s, %(pdf_hash)s, %(pdf_source)s, %(raw_text)s,
                %(parsed_data)s
            )
            ON CONFLICT (model, pdf_url) 
            DO UPDATE SET
                model_variants = EXCLUDED.model_variants,
                announcement_date = COALESCE(EXCLUDED.announcement_date, meraki_eol.announcement_date),
                end_of_sale_date = COALESCE(EXCLUDED.end_of_sale_date, meraki_eol.end_of_sale_date),
                end_of_support_date = COALESCE(EXCLUDED.end_of_support_date, meraki_eol.end_of_support_date),
                pdf_hash = EXCLUDED.pdf_hash,
                raw_text = EXCLUDED.raw_text,
                parsed_data = EXCLUDED.parsed_data,
                updated_at = NOW()
        """, eol_data)
        
        conn.commit()
        logger.info(f"Processed PDF: {pdf_filename} - Found {len(models)} models")
        return True
        
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_filename}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def process_eol_csv(conn):
    """Process the EOL summary CSV file"""
    cursor = conn.cursor()
    
    try:
        # Download CSV
        response = requests.get(EOL_CSV_URL, timeout=30)
        response.raise_for_status()
        csv_content = response.text
        
        # Calculate hash
        csv_hash = hashlib.sha256(csv_content.encode('utf-8')).hexdigest()
        
        # Check if changed
        cursor.execute("SELECT last_csv_hash FROM eol_tracker_state ORDER BY id DESC LIMIT 1")
        existing = cursor.fetchone()
        if existing and existing[0] == csv_hash:
            logger.info("CSV unchanged")
            return False
        
        # Parse CSV
        import csv
        from io import StringIO
        
        reader = csv.DictReader(StringIO(csv_content))
        count = 0
        
        for row in reader:
            try:
                # Extract data
                model = row.get('Model', '').strip()
                if not model:
                    continue
                
                eol_data = {
                    'model': model.upper(),
                    'model_variants': Json([model.upper()]),
                    'announcement_date': parse_date_string(row.get('Announcement Date', '')),
                    'end_of_sale_date': parse_date_string(row.get('End-of-Sale Date', '')),
                    'end_of_support_date': parse_date_string(row.get('End-of-Support Date', '')),
                    'csv_source': True,
                    'parsed_data': Json({
                        'csv_row': row,
                        'import_time': datetime.now().isoformat()
                    })
                }
                
                # Insert or update
                cursor.execute("""
                    INSERT INTO meraki_eol (
                        model, model_variants, announcement_date, end_of_sale_date,
                        end_of_support_date, csv_source, parsed_data
                    ) VALUES (
                        %(model)s, %(model_variants)s, %(announcement_date)s,
                        %(end_of_sale_date)s, %(end_of_support_date)s,
                        %(csv_source)s, %(parsed_data)s
                    )
                    ON CONFLICT (model, pdf_url) WHERE pdf_url IS NULL
                    DO UPDATE SET
                        announcement_date = COALESCE(EXCLUDED.announcement_date, meraki_eol.announcement_date),
                        end_of_sale_date = COALESCE(EXCLUDED.end_of_sale_date, meraki_eol.end_of_sale_date),
                        end_of_support_date = COALESCE(EXCLUDED.end_of_support_date, meraki_eol.end_of_support_date),
                        parsed_data = EXCLUDED.parsed_data,
                        updated_at = NOW()
                """, eol_data)
                
                count += 1
                
            except Exception as e:
                logger.error(f"Error processing CSV row {row}: {e}")
                continue
        
        # Update state
        cursor.execute("""
            INSERT INTO eol_tracker_state (last_csv_hash, last_check_time)
            VALUES (%s, NOW())
        """, (csv_hash,))
        
        conn.commit()
        logger.info(f"Processed CSV: {count} models imported")
        return True
        
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def check_eol_page(conn):
    """Check EOL page for changes and new PDFs"""
    cursor = conn.cursor()
    
    try:
        # Fetch the page
        response = requests.get(EOL_URL, timeout=30)
        response.raise_for_status()
        html = response.text
        
        # Calculate page hash
        page_hash = get_page_hash(html)
        
        # Check if changed
        cursor.execute("SELECT last_page_hash, pdf_inventory FROM eol_tracker_state ORDER BY id DESC LIMIT 1")
        existing = cursor.fetchone()
        
        if existing and existing[0] == page_hash:
            logger.info("EOL page unchanged")
            return False
        
        # Parse page
        soup = BeautifulSoup(html, 'html.parser')
        pdf_links = []
        
        # Find all PDF links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.pdf' in href.lower():
                # Make absolute URL
                if href.startswith('/'):
                    pdf_url = f"https://documentation.meraki.com{href}"
                elif not href.startswith('http'):
                    pdf_url = urljoin(EOL_URL, href)
                else:
                    pdf_url = href
                
                # Extract filename
                pdf_filename = os.path.basename(urlparse(pdf_url).path)
                if not pdf_filename:
                    pdf_filename = f"eol_{hashlib.md5(pdf_url.encode()).hexdigest()[:8]}.pdf"
                
                pdf_links.append({
                    'url': pdf_url,
                    'filename': pdf_filename,
                    'link_text': link.get_text(strip=True)
                })
        
        logger.info(f"Found {len(pdf_links)} PDF links")
        
        # Process each PDF
        processed = 0
        for pdf_info in pdf_links:
            if process_eol_pdf(pdf_info['url'], pdf_info['filename'], conn):
                processed += 1
        
        # Update state
        cursor.execute("""
            INSERT INTO eol_tracker_state (last_page_hash, last_check_time, pdf_inventory)
            VALUES (%s, NOW(), %s)
        """, (page_hash, Json(pdf_links)))
        
        conn.commit()
        logger.info(f"Processed {processed} new/updated PDFs")
        return True
        
    except Exception as e:
        logger.error(f"Error checking EOL page: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def generate_eol_summary(conn):
    """Generate summary statistics"""
    cursor = conn.cursor()
    
    try:
        # Get counts
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT model) as total_models,
                COUNT(DISTINCT model) FILTER (WHERE end_of_sale_date <= CURRENT_DATE) as eos_models,
                COUNT(DISTINCT model) FILTER (WHERE end_of_support_date <= CURRENT_DATE) as eol_models,
                COUNT(DISTINCT model) FILTER (WHERE pdf_source = true) as pdf_sourced,
                COUNT(DISTINCT model) FILTER (WHERE csv_source = true) as csv_sourced,
                COUNT(DISTINCT pdf_url) as total_pdfs
            FROM meraki_eol
        """)
        
        stats = cursor.fetchone()
        
        logger.info(f"""
EOL Database Summary:
- Total Models: {stats[0]}
- End-of-Sale: {stats[1]}
- End-of-Support: {stats[2]}
- From PDFs: {stats[3]}
- From CSV: {stats[4]}
- Total PDFs: {stats[5]}
        """)
        
        # Get upcoming EOL
        cursor.execute("""
            SELECT model, end_of_sale_date, end_of_support_date
            FROM meraki_eol
            WHERE end_of_sale_date > CURRENT_DATE
            AND end_of_sale_date <= CURRENT_DATE + INTERVAL '90 days'
            ORDER BY end_of_sale_date
            LIMIT 10
        """)
        
        upcoming = cursor.fetchall()
        if upcoming:
            logger.info("\nUpcoming End-of-Sale (next 90 days):")
            for model, eos, eol in upcoming:
                logger.info(f"  {model}: EOS {eos}, EOL {eol}")
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
    finally:
        cursor.close()

def main():
    """Main execution function"""
    logger.info("Starting Meraki EOL Tracker")
    
    conn = None
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create tables if needed
        create_eol_table(conn)
        
        # Process CSV first (comprehensive data)
        logger.info("Processing EOL CSV...")
        process_eol_csv(conn)
        
        # Check EOL page for PDFs
        logger.info("Checking EOL page for PDFs...")
        check_eol_page(conn)
        
        # Generate summary
        generate_eol_summary(conn)
        
        logger.info("EOL tracking completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in EOL tracker: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()