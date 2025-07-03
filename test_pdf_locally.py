#!/usr/bin/env python3
"""
Test PDF parsing locally to debug issues
"""

import PyPDF2
from io import BytesIO
import re
from datetime import datetime

def test_pdf_extraction(pdf_path):
    """Test PDF text extraction"""
    print(f"Testing PDF: {pdf_path}")
    print("-" * 50)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"Number of pages: {len(pdf_reader.pages)}")
            
            # Extract text from all pages to find transactions
            all_text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                all_text += text + "\n"
            
            print(f"\nSearching for transaction patterns...")
            
            # Look for specific transaction-like patterns in the concatenated text
            # First let's see if we can find any dates or amounts
            if "Dec 24" in all_text:
                print("Found 'Dec 24' in text")
            if "))) " in all_text:
                print("Found '))) ' markers")
            
            # Find lines that might be transactions (contain dates like "Dec 24")
            print("\nLooking for lines with date patterns:")
            for page_num in range(len(pdf_reader.pages)):
                page_text = pdf_reader.pages[page_num].extract_text()
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if re.search(r'\d{1,2}\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{2}', line):
                        print(f"Page {page_num+1}, Line {i}: {line[:100]}...")
            
            print(f"\nFirst 1000 characters of page 2 (likely has transactions):")
            if len(pdf_reader.pages) > 1:
                page2_text = pdf_reader.pages[1].extract_text()
                print(page2_text[:1000])
            print("\n" + "-" * 50)
            
            # Show lines that might be transactions
            print("\nLines containing numbers (potential transactions):")
            lines = text.split('\n')
            for i, line in enumerate(lines[:50]):  # First 50 lines
                if re.search(r'\d+\.\d{2}', line):  # Lines with decimal numbers
                    print(f"Line {i}: {line}")
            
            # Test transaction patterns
            print("\n" + "-" * 50)
            print("Testing transaction patterns:")
            
            patterns = [
                (r'(\d{1,2}\s+\w{3})(\d{2})(\d{2})\s+\w{3}\d{2}\s+\)+\s*([^£\d]+?)\s+([\d,]+\.\d{2})(?:\s*CR)?', "Pattern 1: Concatenated dates with )))"),
                (r'(\d{1,2}\s+\w{3})(\d{2})(\d{2})\s+\w{3}\d{2}\s+([^£\d]+?)\s+([\d,]+\.\d{2})(?:\s*CR)?', "Pattern 2: Concatenated dates without )))"),
                (r'(\d{1,2}\s+\w{3}\s+\d{2})\s+(.+?)\s+£?([\d,]+\.\d{2})(?:\s*CR)?$', "Pattern 3: Simple"),
                (r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})', "Pattern 4: Date with /"),
            ]
            
            for pattern, name in patterns:
                print(f"\nTesting {name}:")
                matches = 0
                # Test against all pages
                for page_num in range(len(pdf_reader.pages)):
                    page_text = pdf_reader.pages[page_num].extract_text()
                    page_lines = page_text.split('\n')
                    for line in page_lines:
                        match = re.search(pattern, line)
                        if match:
                            matches += 1
                            print(f"  Match: {line[:100]}...")
                            print(f"    Groups: {match.groups()}")
                            if matches >= 3:  # Show first 3 matches
                                break
                    if matches >= 3:
                        break
                if matches == 0:
                    print(f"  No matches found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test the PDF file
    print("=== TESTING CREDIT CARD STATEMENT ===")
    pdf_path = "/Users/safmy/Desktop/OCR_Arabic-1/FinanceCompare/2025-01-09_Statement.pdf"
    test_pdf_extraction(pdf_path)
    
    print("\n\n=== TESTING CURRENT ACCOUNT STATEMENT ===")
    current_account_path = "/Users/safmy/Desktop/OCR_Arabic-1/FinanceCompare/current account/2025-01-07_Statement.pdf"
    test_pdf_extraction(current_account_path)