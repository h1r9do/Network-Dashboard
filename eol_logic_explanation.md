# EOL Data Collection Logic - Detailed Explanation

## The Process Flow

### Step 1: HTML Table Scraping (Primary Source)
```
https://documentation.meraki.com/.../EOL_Products_and_Dates
│
├── Scrape all HTML tables
├── Extract: Model | Announcement | EOS | EOL 
├── Capture PDF links associated with each table row
└── Store as "HTML" source with high confidence
```

**Example HTML Table Row:**
```
Model: "MR33" | Ann: "Jan 27, 2021" | EOS: "Jul 14, 2022" | EOL: "Jul 21, 2026" | PDF: "mr33.pdf"
```

### Step 2: PDF Download and Cataloging
```
For each PDF link found:
├── Download PDF to /var/www/html/meraki-data/EOL/
├── Extract text content
├── Parse for model numbers mentioned
└── Store model-to-PDF associations
```

### Step 3: Date Association Logic

**NOT**: "Download PDF → extract dates → associate with line"

**ACTUALLY**: 
1. **HTML tables provide the dates** (structured, reliable)
2. **PDFs provide model confirmation** (which models are affected)
3. **Family mapping fills gaps** (MS220 SERIES → MS220-8P)

### Step 4: Data Merging Strategy

```python
def merge_data_sources(html_data, pdf_models):
    # Priority 1: Direct HTML table matches
    if model in html_data:
        use html_data[model]
    
    # Priority 2: Family inheritance 
    elif model matches family pattern in html_data:
        use family_data from html_data
    
    # Priority 3: PDF-specific data (if parsed successfully)
    elif model in pdf_data and has_valid_dates:
        use pdf_data[model]
```

## Real Examples

### Case 1: Direct HTML Match (MR33)
```
Source: HTML table
Process: Found "MR33" directly in EOL table
Dates: Extracted from table columns
Confidence: HIGH
```

### Case 2: Family Inheritance (MS220-8P)
```
Source: HTML + PDF combination
Process: 
  1. HTML table has "MS220 SERIES" with dates
  2. PDF confirms MS220-8P is in that series
  3. Apply series dates to specific variant
Confidence: HIGH
```

### Case 3: PDF-Only (Some legacy models)
```
Source: PDF parsing
Process: 
  1. Model not in HTML tables
  2. Found in specific PDF with dates
  3. Parse dates from PDF text
Confidence: MEDIUM
```

## Quality Assurance

### Data Validation
- **Cross-reference**: HTML vs PDF consistency
- **Date parsing**: Multiple format support
- **Conflict resolution**: HTML takes precedence
- **Missing data**: Family inference where appropriate

### Source Tracking
Every record tracks:
- `source`: "HTML" | "PDF" | "HTML+PDF"
- `pdf_name`: Which PDF(s) mention this model
- `confidence`: "high" | "medium" | "low"
- `updated_at`: When last verified

## The MS220-8P Case Study

### What Actually Happened:
1. **HTML table** had "MS220 SERIES" with dates Mar 16, 2017 / Jul 29, 2017 / Jul 29, 2024
2. **PDF parsing** found MS220-8P in `meraki_eol_ms220-8.pdf`
3. **Initial mapping** incorrectly used the series dates
4. **Manual correction** applied the specific PDF dates: Jan 9, 2018 / Sep 21, 2018 / Sep 21, 2025

### The Fix:
The system now correctly shows MS220-8P dates from its specific PDF, not the generic series dates.

## Summary

**The logic does NOT simply**:
- Download PDF → extract dates → associate with webpage line

**The logic ACTUALLY**:
1. Extracts comprehensive date data from HTML tables
2. Downloads PDFs to identify which models they cover  
3. Creates intelligent mappings between models and date sources
4. Applies family inheritance where appropriate
5. Maintains source tracking for verification

This approach ensures maximum coverage while maintaining data accuracy and traceability.