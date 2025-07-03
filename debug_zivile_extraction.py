#!/usr/bin/env python3
"""
Debug Zivile PDF extraction to see why we're only getting 16 transactions
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from zivile_pdf_processor import ZivilePDFProcessor
import base64

def debug_pdf_files():
    processor = ZivilePDFProcessor()
    
    pdf_dir = "/Users/safmy/Desktop/OCR_Arabic-1/FinanceCompare/current account/zivile"
    pdf_files = [
        "2025-01-04_Statement.pdf",
        "2025-02-04_Statement.pdf", 
        "2025-03-04_Statement.pdf",
        "2025-04-04_Statement.pdf",
        "2025-05-04_Statement.pdf",
        "2025-06-04_Statement.pdf"
    ]
    
    total_transactions = 0
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print(f"\n{'='*80}")
        print(f"Processing: {pdf_file}")
        print(f"{'='*80}")
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
                
            # Extract text
            text = processor.extract_text_from_pdf(pdf_content)
            
            if text:
                print(f"Extracted {len(text)} characters")
                
                # Show first 1500 characters to see what we're working with
                print("\nFirst 1500 characters of extracted text:")
                print("-" * 40)
                print(repr(text[:1500]))
                print("-" * 40)
                
                # Parse transactions
                month_name = pdf_file.split('_')[0].split('-')[1] + "/2025"
                transactions = processor.parse_transactions(text, month_name, 'Current Account')
                
                print(f"\nFound {len(transactions)} transactions")
                
                # Show first few transactions
                if transactions:
                    print("\nFirst 3 transactions:")
                    for i, trans in enumerate(transactions[:3]):
                        print(f"{i+1}. Date: {trans['date']}, Desc: {trans['description'][:50]}..., Amount: {trans['amount']}")
                
                total_transactions += len(transactions)
            else:
                print("NO TEXT EXTRACTED!")
                
        except Exception as e:
            print(f"ERROR processing {pdf_file}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"TOTAL TRANSACTIONS FOUND: {total_transactions}")
    print(f"{'='*80}")

if __name__ == "__main__":
    debug_pdf_files()