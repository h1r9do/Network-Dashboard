#!/usr/bin/env python3
"""
Test script to download EOL PDFs and check MS220 models
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import PyPDF2
import re
from datetime import datetime
import logging

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
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        filepath = os.path.join(EOL_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded: {filename}")
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
                text += page.extract_text()
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
    
    # Common date patterns
    date_patterns = [
        r'(\b\w+\s+\d{1,2},\s+\d{4})',  # January 1, 2024
        r'(\d{1,2}/\d{1,2}/\d{4})',      # 01/01/2024
        r'(\d{4}-\d{2}-\d{2})',          # 2024-01-01
    ]
    
    # Look for key phrases
    text_lower = text.lower()
    
    # Find announcement date
    if 'announcement' in text_lower:
        for pattern in date_patterns:
            match = re.search(f'announcement[^\\n]*?' + pattern, text_lower)
            if match:
                dates['announcement'] = match.group(1)
                break
    
    # Find end of sale date
    for phrase in ['end of sale', 'end-of-sale', 'eos date']:
        if phrase in text_lower:
            for pattern in date_patterns:
                match = re.search(f'{phrase}[^\\n]*?' + pattern, text_lower)
                if match:
                    dates['end_of_sale'] = match.group(1)
                    break
            if dates['end_of_sale']:
                break
    
    # Find end of support date
    for phrase in ['end of support', 'end-of-support', 'last date of support']:
        if phrase in text_lower:
            for pattern in date_patterns:
                match = re.search(f'{phrase}[^\\n]*?' + pattern, text_lower)
                if match:
                    dates['end_of_support'] = match.group(1)
                    break
            if dates['end_of_support']:
                break
    
    return dates

def extract_ms220_models(text):
    """Extract MS220 model variants from text"""
    models = set()
    
    # Pattern to match MS220 variants
    ms220_pattern = r'MS220-(\d+)(P|LP|FP)?'
    matches = re.findall(ms220_pattern, text, re.IGNORECASE)
    
    for match in matches:
        port_count = match[0]
        variant = match[1] if match[1] else ''
        model = f"MS220-{port_count}{variant}".upper()
        models.add(model)
        
        # Also add base model (e.g., MS220-8 for MS220-8P)
        if variant:
            base_model = f"MS220-{port_count}".upper()
            models.add(base_model)
    
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
    logger.info("Starting MS220 EOL test")
    logger.info(f"EOL directory: {EOL_DIR}")
    
    # First check what MS220 models we have in inventory
    inventory_models = check_inventory_models()
    if inventory_models:
        logger.info("\n=== MS220 Models in Inventory ===")
        for model, count in inventory_models:
            logger.info(f"  {model}: {count} devices")
    
    # Get the EOL page
    url = "https://documentation.meraki.com/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
    
    try:
        logger.info("\nFetching EOL page...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all PDF links
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf'):
                pdf_links.append({
                    'url': href if href.startswith('http') else f"https://documentation.meraki.com{href}",
                    'text': link.get_text(strip=True),
                    'filename': os.path.basename(href)
                })
        
        logger.info(f"Found {len(pdf_links)} PDF links")
        
        # Look for MS220 related PDFs
        ms220_pdfs = []
        for pdf in pdf_links:
            if 'MS220' in pdf['filename'] or 'MS220' in pdf['text']:
                ms220_pdfs.append(pdf)
        
        logger.info(f"\n=== Found {len(ms220_pdfs)} MS220-related PDFs ===")
        
        # Download and parse MS220 PDFs
        ms220_data = {}
        
        for pdf in ms220_pdfs:
            logger.info(f"\nProcessing: {pdf['filename']}")
            
            # Download PDF
            pdf_path = download_pdf(pdf['url'], pdf['filename'])
            if not pdf_path:
                continue
            
            # Extract text
            text = extract_text_from_pdf(pdf_path)
            if not text:
                continue
            
            # Extract models
            models = extract_ms220_models(text)
            logger.info(f"  Models found: {models}")
            
            # Extract dates
            dates = parse_dates_from_text(text)
            logger.info(f"  Dates found: {dates}")
            
            # Store data for each model
            for model in models:
                if model not in ms220_data or dates['end_of_sale']:  # Prefer entries with dates
                    ms220_data[model] = {
                        'source_pdf': pdf['filename'],
                        'dates': dates,
                        'url': pdf['url']
                    }
        
        # Also check the main HTML for MS220 entries
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
                            logger.info(f"  Found in HTML: {model}")
                            logger.info(f"    Announcement: {cols[1].get_text(strip=True)}")
                            logger.info(f"    End of Sale: {cols[2].get_text(strip=True)}")
                            logger.info(f"    End of Support: {cols[3].get_text(strip=True)}")
        
        # Summary
        logger.info("\n=== MS220 EOL Data Summary ===")
        for model in sorted(ms220_data.keys()):
            data = ms220_data[model]
            logger.info(f"\n{model}:")
            logger.info(f"  Source: {data['source_pdf']}")
            logger.info(f"  Announcement: {data['dates']['announcement']}")
            logger.info(f"  End of Sale: {data['dates']['end_of_sale']}")
            logger.info(f"  End of Support: {data['dates']['end_of_support']}")
        
        # Check matching logic
        if inventory_models:
            logger.info("\n=== Matching Logic Test ===")
            for inv_model, count in inventory_models:
                logger.info(f"\nInventory model: {inv_model} ({count} devices)")
                
                # Exact match
                if inv_model in ms220_data:
                    logger.info(f"  ✓ Exact match found")
                else:
                    # Check pattern match (MS220-8P matches MS220-8)
                    base_match = re.match(r'(MS220-\d+)', inv_model)
                    if base_match:
                        base_model = base_match.group(1)
                        if base_model in ms220_data:
                            logger.info(f"  ✓ Base model match found: {base_model}")
                        else:
                            logger.info(f"  ✗ No match found")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()