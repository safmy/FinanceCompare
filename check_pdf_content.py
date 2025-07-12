#!/usr/bin/env python3
"""
Check PDF content to understand detection issue
"""

import PyPDF2
import pdfplumber

def check_pdf_content(pdf_path, name):
    """Check what markers are in the PDF"""
    print(f"\n=== Checking {name} ===")
    print(f"File: {pdf_path}")
    print("-" * 50)
    
    try:
        with open(pdf_path, 'rb') as file:
            # Try pdfplumber
            file.seek(0)
            with pdfplumber.open(file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                
                print("Checking for credit card markers in text:")
                markers = [
                    'ReceivedByUsTransactionDateDetailsAmount',
                    'ReceivedByUs TransactionDate Details',
                    'Received By Us Transaction Date',
                    'ReceivedByUs',
                    'YourVisa Card',
                    'Your Visa Card',
                    'Your Credit Card statement',
                    'CreditLimit',
                    'Your Transaction Details',
                    'YourTransactionDetails'
                ]
                
                for marker in markers:
                    if marker in text:
                        print(f"  ✓ Found: '{marker}'")
                
                # Also check for current account markers
                print("\nChecking for current account markers:")
                current_markers = [
                    'Your HSBC Advance details',
                    'Your Bank Account details',
                    'Balance brought forward',
                    'Paid in',
                    'Paid out'
                ]
                
                for marker in current_markers:
                    if marker in text:
                        print(f"  ✓ Found: '{marker}'")
                
                # Show first 500 chars
                print(f"\nFirst 500 characters of text:")
                print(text[:500])
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_pdf_content("/Users/safmy/Desktop/OCR_Arabic-1/FinanceCompare/current account/CurrentAccount/2025-06-07_Statement.pdf", "Current Account")
    check_pdf_content("/Users/safmy/Desktop/OCR_Arabic-1/FinanceCompare/current account/CreditCard/2025-06-09_Statement.pdf", "Credit Card")