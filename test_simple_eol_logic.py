#!/usr/bin/env python3
"""
Test the simpler EOL logic:
1. Download all PDFs from EOL page
2. Parse PDFs for models
3. Match PDF with EOL dates from the webpage line
4. Models inherit dates from their PDF
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
import json

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

def step1_get_pdf_to_dates_mapping():
    """
    Step 1: Get EOL page and map each PDF to its EOL dates
    Returns: {pdf_filename: {ann_date, eos_date, eol_date}}
    """
    logger.info("Step 1: Mapping PDFs to their EOL dates from webpage...")
    
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
                        pdf_links.append(pdf_filename)
            
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
            
            # Associate these dates with all PDFs found in this row
            if pdf_links and any(dates.values()):
                for pdf_filename in pdf_links:
                    if pdf_filename not in pdf_date_mapping:
                        pdf_date_mapping[pdf_filename] = dates.copy()
                        logger.info(f"  {pdf_filename} -> EOS: {dates['end_of_sale']}, EOL: {dates['end_of_support']}")
    
    logger.info(f"Found {len(pdf_date_mapping)} PDFs with associated dates")
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
                
                # Find all models using patterns
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

def step3_create_model_date_mapping(pdf_dates, pdf_models):
    """
    Step 3: Create final mapping of models to their EOL dates
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

def step4_compare_with_current_inventory():
    """
    Step 4: Compare new logic results with current inventory
    """
    logger.info("Step 4: Comparing with current inventory...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get our current inventory models
    cursor.execute("""
        SELECT DISTINCT model 
        FROM inventory_summary 
        WHERE model IS NOT NULL
        ORDER BY model
    """)
    
    inventory_models = [row[0] for row in cursor.fetchall()]
    logger.info(f"Found {len(inventory_models)} unique models in inventory")
    
    # Get current EOL data
    cursor.execute("""
        SELECT model, announcement_date, end_of_sale, end_of_support, source
        FROM meraki_eol_enhanced
        WHERE model IN %s
        ORDER BY model
    """, (tuple(inventory_models),))
    
    current_eol_data = {}
    for row in cursor.fetchall():
        model, ann, eos, eol, source = row
        current_eol_data[model] = {
            'announcement_date': ann,
            'end_of_sale': eos,
            'end_of_support': eol,
            'source': source
        }
    
    cursor.close()
    conn.close()
    
    return inventory_models, current_eol_data

def main():
    """Test the simple EOL logic"""
    logger.info("=== Testing Simple EOL Logic ===")
    
    # Step 1: Map PDFs to dates from webpage
    pdf_dates = step1_get_pdf_to_dates_mapping()
    
    # Step 2: Parse PDFs for models
    pdf_models = step2_parse_pdfs_for_models()
    
    # Step 3: Create model mappings
    new_model_data = step3_create_model_date_mapping(pdf_dates, pdf_models)
    
    # Step 4: Compare with inventory
    inventory_models, current_eol_data = step4_compare_with_current_inventory()
    
    # Analysis
    logger.info("\n=== COMPARISON ANALYSIS ===")
    
    # Models in inventory with current EOL data
    current_coverage = len([m for m in inventory_models if m in current_eol_data])
    
    # Models in inventory that would have data with new logic
    new_coverage = len([m for m in inventory_models if m in new_model_data])
    
    # Find differences
    current_only = set(m for m in inventory_models if m in current_eol_data and m not in new_model_data)
    new_only = set(m for m in inventory_models if m in new_model_data and m not in current_eol_data)
    both = set(m for m in inventory_models if m in current_eol_data and m in new_model_data)
    
    print(f"\n=== COVERAGE COMPARISON ===")
    print(f"Inventory models: {len(inventory_models)}")
    print(f"Current EOL coverage: {current_coverage} models ({current_coverage/len(inventory_models)*100:.1f}%)")
    print(f"New logic coverage: {new_coverage} models ({new_coverage/len(inventory_models)*100:.1f}%)")
    print(f"Models only in current: {len(current_only)}")
    print(f"Models only in new: {len(new_only)}")
    print(f"Models in both: {len(both)}")
    
    # Sample differences
    if current_only:
        print(f"\nSample models LOST with new logic:")
        for model in sorted(list(current_only))[:10]:
            current = current_eol_data[model]
            print(f"  {model}: {current['source']} -> EOS: {current['end_of_sale']}")
    
    if new_only:
        print(f"\nSample models GAINED with new logic:")
        for model in sorted(list(new_only))[:10]:
            new = new_model_data[model]
            print(f"  {model}: {new['source_pdf']} -> EOS: {new['end_of_sale']}")
    
    # Date comparison for models in both
    date_differences = []
    for model in list(both)[:20]:  # Check first 20
        current = current_eol_data[model]
        new = new_model_data[model]
        
        if (current['end_of_sale'] != new['end_of_sale'] or 
            current['end_of_support'] != new['end_of_support']):
            date_differences.append({
                'model': model,
                'current': current,
                'new': new
            })
    
    if date_differences:
        print(f"\nDATE DIFFERENCES (first 10):")
        for diff in date_differences[:10]:
            model = diff['model']
            curr = diff['current']
            new = diff['new']
            print(f"\n{model}:")
            print(f"  Current: EOS={curr['end_of_sale']}, EOL={curr['end_of_support']} ({curr['source']})")
            print(f"  New:     EOS={new['end_of_sale']}, EOL={new['end_of_support']} ({new['source_pdf']})")
    
    # Save results for detailed analysis
    results = {
        'pdf_dates': {k: {
            'announcement': str(v['announcement']) if v['announcement'] else None,
            'end_of_sale': str(v['end_of_sale']) if v['end_of_sale'] else None,
            'end_of_support': str(v['end_of_support']) if v['end_of_support'] else None
        } for k, v in pdf_dates.items()},
        'pdf_models': pdf_models,
        'coverage_stats': {
            'inventory_models': len(inventory_models),
            'current_coverage': current_coverage,
            'new_coverage': new_coverage,
            'current_only': list(current_only),
            'new_only': list(new_only),
            'both': list(both)
        },
        'date_differences': date_differences
    }
    
    with open('/tmp/eol_logic_comparison.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nDetailed results saved to /tmp/eol_logic_comparison.json")
    
    print(f"\n=== RECOMMENDATION ===")
    if new_coverage >= current_coverage * 0.95:  # Within 5%
        print("✅ New logic maintains good coverage - RECOMMEND PROCEEDING")
    else:
        print("⚠️  New logic has significantly lower coverage - INVESTIGATE BEFORE PROCEEDING")

if __name__ == "__main__":
    main()