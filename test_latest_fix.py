#!/usr/bin/env python3
"""
Test the latest PDF processor fix
"""

import sys
sys.path.append('./api')
import base64

from improved_multiline_processor import ImprovedMultilineProcessor

def test_pdf(pdf_path, month='June'):
    """Test PDF processing with the improved processor"""
    print(f"Testing PDF: {pdf_path}")
    print("-" * 50)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_content = file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            processor = ImprovedMultilineProcessor()
            transactions = processor.process_pdf_batch([{
                'content': pdf_base64,
                'month': month
            }])
            
            print(f"Total transactions found: {len(transactions)}")
            
            # Calculate summary
            total_spending = sum(t['amount'] for t in transactions)
            categories = {}
            for t in transactions:
                cat = t['category']
                if cat not in categories:
                    categories[cat] = {'amount': 0, 'count': 0}
                categories[cat]['amount'] += t['amount']
                categories[cat]['count'] += 1
            
            print(f"Total spending: £{total_spending:.2f}")
            print(f"\nCategories:")
            for category, data in categories.items():
                print(f"  {category}: £{data['amount']:.2f} ({data['count']} transactions)")
            
            print(f"\nFirst 5 transactions:")
            for i, tx in enumerate(transactions[:5]):
                print(f"  {i+1}. {tx['date']} - {tx['description'][:50]} - £{tx['amount']:.2f} ({tx['category']})")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with June current account statement
    print("=== TESTING CURRENT ACCOUNT STATEMENT (JUNE) ===")
    test_pdf("/Users/safmy/Desktop/OCR_Arabic-1/FinanceCompare/current account/CurrentAccount/2025-06-07_Statement.pdf")
    
    print("\n\n=== TESTING CREDIT CARD STATEMENT (JUNE) ===")
    test_pdf("/Users/safmy/Desktop/OCR_Arabic-1/FinanceCompare/current account/CreditCard/2025-06-09_Statement.pdf")