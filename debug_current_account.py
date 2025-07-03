#!/usr/bin/env python3
"""
Debug current account PDF parsing
"""

import PyPDF2
from io import BytesIO
import re
import sys

def debug_pdf_extraction(pdf_path):
    """Debug PDF text extraction"""
    print(f"Debugging PDF: {pdf_path}")
    print("-" * 80)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"Number of pages: {len(pdf_reader.pages)}")
            
            # Look at first few pages
            for page_num in range(min(3, len(pdf_reader.pages))):
                print(f"\n--- Page {page_num + 1} ---")
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                # Show raw text
                print("RAW TEXT (first 2000 chars):")
                print(repr(text[:2000]))
                print("\n")
                
                # Show lines that might be transactions
                print("POTENTIAL TRANSACTION LINES:")
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    # Look for lines with amounts
                    if re.search(r'\d+\.\d{2}', line) and len(line) > 10:
                        print(f"Line {i}: {repr(line)}")
                        
                        # Check what patterns match
                        patterns = [
                            (r'(\d{2}\s+\w{3}\s+\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})\s*(?:D)?', 'hsbc_current'),
                            (r'([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})\s*(?:D)?', 'hsbc_no_date'),
                            (r'(\d{2}[A-Za-z]{3}\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})', 'hsbc_compact'),
                            (r'(\d{2}\s+\w{3}\s+\d{2})\s+(.+?)\s+([\d,]+\.\d{2})', 'simple'),
                        ]
                        
                        for pattern, name in patterns:
                            match = re.search(pattern, line)
                            if match:
                                print(f"  MATCHES {name}: groups = {match.groups()}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default path
        pdf_path = "/Users/safmy/Desktop/OCR_Arabic-1/FinanceCompare/current account/2025-01-07_Statement.pdf"
    
    debug_pdf_extraction(pdf_path)