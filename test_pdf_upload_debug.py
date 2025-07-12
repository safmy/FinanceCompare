#!/usr/bin/env python3
"""
Test script to debug PDF upload issues with comprehensive logging
"""

import requests
import sys
import os
import base64
import json

def test_pdf_upload(pdf_path, api_url=None):
    """Test PDF upload with debug output"""
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found: {pdf_path}")
        return
    
    # Default to local API if not specified
    if not api_url:
        api_url = "http://localhost:5000"
    
    print(f"\n=== Testing PDF Upload ===")
    print(f"PDF file: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path)} bytes")
    print(f"API URL: {api_url}")
    
    # First test if API is running
    try:
        health_response = requests.get(f"{api_url}/health")
        print(f"\nHealth check response: {health_response.status_code}")
        if health_response.ok:
            print(f"Health data: {health_response.json()}")
    except Exception as e:
        print(f"\nERROR: Cannot connect to API at {api_url}")
        print(f"Error: {e}")
        print("\nMake sure the API is running:")
        print("  cd api && python app.py")
        return
    
    # Test PDF extraction first
    print("\n--- Testing PDF extraction ---")
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            response = requests.post(f"{api_url}/api/test-pdf", files=files)
            
        print(f"Test PDF response: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"Extraction success: {data.get('success')}")
            print(f"Text length: {data.get('text_length')}")
            print(f"PDF size: {data.get('pdf_size')}")
            if data.get('first_500_chars'):
                print(f"\nFirst 500 chars of extracted text:")
                print("-" * 50)
                print(data['first_500_chars'])
                print("-" * 50)
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing PDF extraction: {e}")
    
    # Now test full PDF processing
    print("\n--- Testing full PDF processing ---")
    try:
        with open(pdf_path, 'rb') as f:
            files = [('files', (os.path.basename(pdf_path), f, 'application/pdf'))]
            data = {'months': ['January']}  # Default month
            
            response = requests.post(
                f"{api_url}/api/parse-pdfs-batch",
                files=files,
                data=data
            )
        
        print(f"Parse PDFs response: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.ok:
            result = response.json()
            print(f"\nProcessing successful!")
            print(f"Transactions found: {len(result.get('transactions', []))}")
            
            if result.get('summary'):
                summary = result['summary']
                print(f"\nSummary:")
                print(f"  Total spending: £{summary.get('total_spending', 0):.2f}")
                print(f"  Transaction count: {summary.get('transaction_count', 0)}")
                print(f"  Categories: {list(summary.get('categories', {}).keys())}")
            
            if result.get('transactions'):
                print(f"\nFirst 5 transactions:")
                for i, trans in enumerate(result['transactions'][:5]):
                    print(f"\n  Transaction {i+1}:")
                    print(f"    Date: {trans.get('date')}")
                    print(f"    Description: {trans.get('description')}")
                    print(f"    Amount: £{trans.get('amount', 0):.2f}")
                    print(f"    Category: {trans.get('category')}")
                    print(f"    Type: {trans.get('type')}")
            else:
                print("\nNo transactions found!")
                print("This could mean:")
                print("  1. The PDF is empty or corrupted")
                print("  2. The PDF format is not recognized")
                print("  3. The text extraction failed")
                print("  4. The transaction parsing failed")
                
        else:
            print(f"\nError response: {response.status_code}")
            error_data = response.json()
            print(f"Error message: {error_data.get('error')}")
            
    except Exception as e:
        print(f"\nError during PDF processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_upload_debug.py <pdf_file> [api_url]")
        print("\nExample:")
        print("  python test_pdf_upload_debug.py 'current account/CurrentAccount/2025-01-07_Statement.pdf'")
        print("  python test_pdf_upload_debug.py 'current account/CurrentAccount/2025-01-07_Statement.pdf' http://localhost:5000")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    test_pdf_upload(pdf_file, api_url)