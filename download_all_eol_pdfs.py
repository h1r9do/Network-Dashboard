#!/usr/bin/env python3
"""
Download ALL EOL PDFs from Meraki documentation site
This is the comprehensive version that gets everything, not just MS220
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directories
EOL_DIR = "/var/www/html/meraki-data/EOL"
os.makedirs(EOL_DIR, exist_ok=True)

def download_pdf(url, filename):
    """Download a PDF file with retry logic"""
    try:
        # Clean filename
        clean_filename = filename.replace('%2b', '_').replace('%2B', '_').replace('%20', '_')
        clean_filename = clean_filename.replace('(', '').replace(')', '')
        if not clean_filename.endswith('.pdf'):
            clean_filename += '.pdf'
        
        filepath = os.path.join(EOL_DIR, clean_filename)
        
        if os.path.exists(filepath):
            logger.info(f"Already exists: {clean_filename}")
            return filepath
        
        logger.info(f"Downloading: {clean_filename}")
        
        # Download with retry
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded: {clean_filename} ({len(response.content):,} bytes)")
                return filepath
            except Exception as e:
                if attempt < 2:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
                else:
                    raise
                    
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        return None

def main():
    """Download all EOL PDFs"""
    # Get EOL page
    base_url = "https://documentation.meraki.com"
    eol_url = f"{base_url}/General_Administration/Other_Topics/Meraki_End-of-Life_(EOL)_Products_and_Dates"
    
    logger.info("Fetching EOL page...")
    response = requests.get(eol_url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find ALL PDF links
    pdf_links = []
    seen_urls = set()  # Track unique URLs
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '.pdf' in href.lower():
            full_url = urljoin(base_url, href)
            
            # Skip duplicates
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            
            filename = href.split('/')[-1].split('?')[0]
            link_text = link.get_text(strip=True)
            
            pdf_links.append({
                'url': full_url,
                'filename': filename,
                'text': link_text
            })
    
    logger.info(f"Found {len(pdf_links)} unique PDFs to download")
    
    # Download all PDFs
    downloaded = 0
    failed = 0
    
    for i, pdf in enumerate(pdf_links, 1):
        logger.info(f"\n[{i}/{len(pdf_links)}] Processing: {pdf['text']}")
        
        result = download_pdf(pdf['url'], pdf['filename'])
        if result:
            downloaded += 1
        else:
            failed += 1
        
        # Small delay to be nice to the server
        time.sleep(0.5)
    
    logger.info(f"\n=== Download Summary ===")
    logger.info(f"Total PDFs found: {len(pdf_links)}")
    logger.info(f"Successfully downloaded: {downloaded}")
    logger.info(f"Failed downloads: {failed}")
    logger.info(f"PDFs stored in: {EOL_DIR}")
    
    # List all PDFs in directory
    pdf_files = [f for f in os.listdir(EOL_DIR) if f.endswith('.pdf')]
    logger.info(f"\nTotal PDFs in directory: {len(pdf_files)}")

if __name__ == "__main__":
    main()