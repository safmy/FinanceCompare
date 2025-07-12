#!/usr/bin/env python3
"""
Check if PDF files exist and are readable
"""

import os
import PyPDF2

def check_pdf_files():
    """Check all PDF files in the current account directories"""
    
    directories = [
        "current account/CurrentAccount",
        "current account/CreditCard",
        "current account/zivile"
    ]
    
    print("=== Checking PDF Files ===\n")
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            continue
            
        print(f"\nChecking directory: {directory}")
        print("-" * 50)
        
        pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
        
        if not pdf_files:
            print("No PDF files found")
            continue
        
        for pdf_file in sorted(pdf_files):
            pdf_path = os.path.join(directory, pdf_file)
            file_size = os.path.getsize(pdf_path)
            
            print(f"\nFile: {pdf_file}")
            print(f"  Size: {file_size:,} bytes")
            
            # Try to read the PDF
            try:
                with open(pdf_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    num_pages = len(pdf_reader.pages)
                    print(f"  Pages: {num_pages}")
                    
                    # Try to extract text from first page
                    if num_pages > 0:
                        first_page_text = pdf_reader.pages[0].extract_text()
                        text_length = len(first_page_text) if first_page_text else 0
                        print(f"  First page text length: {text_length} chars")
                        
                        if text_length > 0:
                            print(f"  First 100 chars: {first_page_text[:100]}...")
                        else:
                            print("  WARNING: No text extracted from first page")
                            
            except Exception as e:
                print(f"  ERROR reading PDF: {e}")
    
    print("\n\nTo test a specific PDF upload, run:")
    print("  python test_pdf_upload_debug.py 'current account/CurrentAccount/2025-01-07_Statement.pdf'")

if __name__ == "__main__":
    check_pdf_files()