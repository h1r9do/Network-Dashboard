#!/usr/bin/env python3
"""
Parse MS220 specific PDFs to extract detailed model information
"""

import os
import PyPDF2
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

EOL_DIR = "/var/www/html/meraki-data/EOL"

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
        logger.error(f"Error reading PDF: {e}")
        return ""

def parse_ms220_models(text):
    """Extract MS220 models and their EOL dates"""
    models = {}
    
    # Split text into lines
    lines = text.split('\n')
    
    # Look for MS220 model patterns
    for i, line in enumerate(lines):
        # Find MS220 model mentions
        model_match = re.search(r'MS220-(\d+)(P|LP|FP)?', line, re.IGNORECASE)
        if model_match:
            port_count = model_match.group(1)
            variant = model_match.group(2) if model_match.group(2) else ''
            model = f"MS220-{port_count}{variant}".upper()
            
            # Look for dates near this model (within 10 lines)
            dates = {'announcement': None, 'eos': None, 'eol': None}
            
            for j in range(max(0, i-10), min(len(lines), i+10)):
                date_line = lines[j]
                
                # Look for dates
                date_pattern = r'(\w+\s+\d{1,2},\s+\d{4})'
                date_match = re.search(date_pattern, date_line)
                
                if date_match:
                    date_str = date_match.group(1)
                    
                    # Check context
                    if 'announcement' in date_line.lower():
                        dates['announcement'] = date_str
                    elif 'end of sale' in date_line.lower() or 'eos' in date_line.lower():
                        dates['eos'] = date_str
                    elif 'end of support' in date_line.lower() or 'eol' in date_line.lower():
                        dates['eol'] = date_str
            
            if model not in models or any(dates.values()):
                models[model] = dates
    
    # Also look for tables with dates
    # Try to find structured data
    if 'Product' in text and 'End-of-Sale' in text:
        # Look for table-like structures
        for i, line in enumerate(lines):
            if 'MS220' in line:
                # Check if this looks like a table row
                if i + 1 < len(lines):
                    next_lines = lines[i:i+5]
                    dates_found = []
                    
                    for next_line in next_lines:
                        date_matches = re.findall(r'(\w+\s+\d{1,2},\s+\d{4})', next_line)
                        dates_found.extend(date_matches)
                    
                    if len(dates_found) >= 3:
                        # This might be a table row
                        model_text = line.strip()
                        logger.info(f"Possible table row: {model_text}")
                        logger.info(f"  Dates found: {dates_found}")
    
    return models

def main():
    """Main function"""
    ms220_pdfs = [
        'meraki_eol_ms220.pdf',
        'meraki_eol_ms220-8.pdf'
    ]
    
    for pdf_name in ms220_pdfs:
        pdf_path = os.path.join(EOL_DIR, pdf_name)
        if os.path.exists(pdf_path):
            logger.info(f"\n=== Processing {pdf_name} ===")
            
            text = extract_text_from_pdf(pdf_path)
            if text:
                # Show first 2000 characters to understand structure
                logger.info("PDF Content Preview:")
                logger.info("-" * 80)
                logger.info(text[:2000])
                logger.info("-" * 80)
                
                # Extract models
                models = parse_ms220_models(text)
                
                logger.info(f"\nModels found: {len(models)}")
                for model, dates in models.items():
                    logger.info(f"{model}:")
                    logger.info(f"  Announcement: {dates['announcement']}")
                    logger.info(f"  End of Sale: {dates['eos']}")
                    logger.info(f"  End of Support: {dates['eol']}")
                
                # Also search for specific MS220 variant mentions
                variants = ['MS220-8P', 'MS220-24P', 'MS220-48FP', 'MS220-48LP']
                for variant in variants:
                    if variant in text.upper():
                        logger.info(f"\n{variant} is mentioned in this PDF")
                        # Find context around this variant
                        idx = text.upper().find(variant)
                        if idx > 0:
                            context = text[max(0, idx-200):idx+200]
                            logger.info(f"Context: ...{context}...")

if __name__ == "__main__":
    main()