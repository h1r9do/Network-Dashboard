#!/usr/bin/env python3
"""
Test script to download EOL PDFs and check MS220 models - V2
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import PyPDF2
import re
from datetime import datetime
import logging
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create EOL directory
EOL_DIR = "/var/www/html/meraki-data/EOL"
os.makedirs(EOL_DIR, exist_ok=True)

def download_pdf(url, filename):
    """Download a PDF file"""
    try:
        # Clean filename
        clean_filename = filename.replace('%2b', '+').replace('%20', '_')
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        filepath = os.path.join(EOL_DIR, clean_filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded: {clean_filename} ({len(response.content)} bytes)")
        return filepath
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return ""

def parse_dates_from_text(text):
    """Extract dates from PDF text"""
    dates = {
        'announcement': None,
        'end_of_sale': None,
        'end_of_support': None
    }
    
    # Look for dates in various formats
    text_lines = text.split('\n')
    
    for i, line in enumerate(text_lines):
        line_lower = line.lower()
        
        # Look for announcement date
        if 'announcement' in line_lower:
            # Check current line and next few lines for dates
            for j in range(i, min(i+5, len(text_lines))):
                date_match = re.search(r'(\w+\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})', text_lines[j])
                if date_match:
                    dates['announcement'] = date_match.group(1)
                    break
        
        # Look for end of sale
        if any(phrase in line_lower for phrase in ['end of sale', 'end-of-sale', 'eos date', 'last order']):
            for j in range(i, min(i+5, len(text_lines))):
                date_match = re.search(r'(\w+\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})', text_lines[j])
                if date_match:
                    dates['end_of_sale'] = date_match.group(1)
                    break
        
        # Look for end of support
        if any(phrase in line_lower for phrase in ['end of support', 'end-of-support', 'last date of support']):
            for j in range(i, min(i+5, len(text_lines))):
                date_match = re.search(r'(\w+\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})', text_lines[j])
                if date_match:
                    dates['end_of_support'] = date_match.group(1)
                    break
    
    return dates

def extract_ms220_models(text):
    """Extract MS220 model variants from text"""
    models = set()
    
    # More comprehensive pattern to match MS220 variants
    patterns = [
        r'MS220-(\d+)(P|LP|FP)?(?:\s|,|$)',
        r'MS\s*220-(\d+)(P|LP|FP)?(?:\s|,|$)',
        r'MS220–(\d+)(P|LP|FP)?(?:\s|,|$)',  # Em dash variant
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            port_count = match[0]
            variant = match[1] if len(match) > 1 and match[1] else ''
            model = f"MS220-{port_count}{variant}".upper()
            models.add(model)
            
            # Also add base model (e.g., MS220-8 for MS220-8P)
            if variant:
                base_model = f"MS220-{port_count}".upper()
                models.add(base_model)
    
    # Also look for "MS220 Series" or generic mentions
    if re.search(r'MS220\s+Series', text, re.IGNORECASE):
        models.add("MS220 SERIES")
    
    return sorted(list(models))

def check_inventory_models():
    """Check what MS220 models we have in inventory"""
    try:
        import psycopg2
        from config import Config
        
        # Parse database URI
        match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
        if not match:
            logger.error("Invalid database URI")
            return []
        
        user, password, host, port, database = match.groups()
        
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        
        cursor = conn.cursor()
        
        # Get MS220 models from inventory
        cursor.execute("""
            SELECT DISTINCT model, COUNT(*) as count
            FROM inventory_summary
            WHERE model LIKE 'MS220%'
            GROUP BY model
            ORDER BY model
        """)
        
        models = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return models
        
    except Exception as e:
        logger.error(f"Error checking inventory: {e}")
        return []

def main():
    """Main function"""
    logger.info("Starting MS220 EOL test V2")
    logger.info(f"EOL directory: {EOL_DIR}")
    
    # First check what MS220 models we have in inventory
    inventory_models = check_inventory_models()
    if inventory_models:
        logger.info("\n=== MS220 Models in Inventory ===")
        for model, count in inventory_models:
            logger.info(f"  {model}: {count} devices")
    
    # Get the EOL page
    base_url = "https://documentation.meraki.com"
    eol_url = f"{base_url}/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
    
    try:
        logger.info("\nFetching EOL page...")
        response = requests.get(eol_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links that might be PDFs
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Check for PDF extensions or PDF-like URLs
            if '.pdf' in href.lower() or 'pdf' in href.lower():
                full_url = urljoin(base_url, href)
                pdf_links.append({
                    'url': full_url,
                    'text': link.get_text(strip=True),
                    'filename': os.path.basename(href).split('?')[0]  # Remove query params
                })
        
        # Also check for links in the page that might lead to PDFs
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            if 'MS220' in text and link['href'] not in [p['url'] for p in pdf_links]:
                href = link['href']
                full_url = urljoin(base_url, href)
                pdf_links.append({
                    'url': full_url,
                    'text': text,
                    'filename': f"MS220_{text.replace(' ', '_').replace('/', '_')}.pdf"
                })
        
        logger.info(f"Found {len(pdf_links)} potential PDF links")
        
        # Download first few PDFs to check
        logger.info("\n=== Downloading sample PDFs ===")
        for i, pdf in enumerate(pdf_links[:5]):  # Just first 5 for testing
            logger.info(f"\nLink {i+1}: {pdf['text'][:50]}...")
            logger.info(f"  URL: {pdf['url'][:100]}...")
        
        # Look for MS220 in HTML tables
        ms220_html_data = {}
        logger.info("\n=== Checking HTML tables for MS220 ===")
        for table in soup.find_all('table'):
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            if 'model' in headers or 'product' in headers:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        model_text = cols[0].get_text(strip=True)
                        if 'MS220' in model_text.upper():
                            model = model_text.split(',')[0].split('(')[0].strip().upper()
                            
                            ms220_html_data[model] = {
                                'announcement': cols[1].get_text(strip=True),
                                'end_of_sale': cols[2].get_text(strip=True),
                                'end_of_support': cols[3].get_text(strip=True)
                            }
                            
                            logger.info(f"  Found: {model}")
                            logger.info(f"    Announcement: {ms220_html_data[model]['announcement']}")
                            logger.info(f"    End of Sale: {ms220_html_data[model]['end_of_sale']}")
                            logger.info(f"    End of Support: {ms220_html_data[model]['end_of_support']}")
        
        # Test matching logic with HTML data
        if inventory_models and ms220_html_data:
            logger.info("\n=== Matching Logic Test ===")
            for inv_model, count in inventory_models:
                logger.info(f"\nInventory model: {inv_model} ({count} devices)")
                
                # Exact match
                if inv_model in ms220_html_data:
                    logger.info(f"  ✓ Exact match found: {inv_model}")
                    logger.info(f"    EOL: {ms220_html_data[inv_model]['end_of_support']}")
                else:
                    # Check if MS220-8P should match MS220-8
                    if inv_model == "MS220-8P" and "MS220-8" in ms220_html_data:
                        logger.info(f"  ✓ Base model match: MS220-8")
                        logger.info(f"    EOL: {ms220_html_data['MS220-8']['end_of_support']}")
                    # Check if any model should match MS220 SERIES
                    elif "MS220 SERIES" in ms220_html_data:
                        logger.info(f"  ✓ Series match: MS220 SERIES")
                        logger.info(f"    EOL: {ms220_html_data['MS220 SERIES']['end_of_support']}")
                    else:
                        logger.info(f"  ✗ No match found")
        
        # Now let's check if we can download the EOL CSV file
        logger.info("\n=== Looking for EOL CSV file ===")
        csv_url = "https://documentation.meraki.com/images/6/68/Meraki_EoS_Products_-_CSV_Format.csv"
        try:
            csv_response = requests.get(csv_url, timeout=10)
            if csv_response.status_code == 200:
                csv_path = os.path.join(EOL_DIR, "Meraki_EoS_Products.csv")
                with open(csv_path, 'wb') as f:
                    f.write(csv_response.content)
                logger.info(f"✓ Downloaded EOL CSV file ({len(csv_response.content)} bytes)")
                
                # Quick check of CSV content
                import csv
                with open(csv_path, 'r') as f:
                    reader = csv.DictReader(f)
                    ms220_count = 0
                    for row in reader:
                        if 'MS220' in str(row.get('Model', '')):
                            if ms220_count == 0:
                                logger.info("\nMS220 entries in CSV:")
                            logger.info(f"  {row.get('Model')}: EOS={row.get('End-of-Sale Date')}, EOL={row.get('End-of-Support Date')}")
                            ms220_count += 1
                    logger.info(f"\nFound {ms220_count} MS220 entries in CSV")
            else:
                logger.info(f"✗ CSV file not accessible (status: {csv_response.status_code})")
        except Exception as e:
            logger.info(f"✗ Error accessing CSV: {e}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()