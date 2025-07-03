#!/usr/bin/env python3
"""
PDF Bank Statement to JSON Converter
This script helps extract transaction data from PDF bank statements
"""

import sys
import json
import re
from datetime import datetime

def parse_transaction_line(line):
    """
    Parse a transaction line from the PDF text.
    Adjust the regex pattern based on your bank's statement format.
    """
    # Example patterns - adjust based on your bank's format
    patterns = [
        # Pattern 1: Date Description Amount
        r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-£]?\d+\.\d{2})',
        # Pattern 2: Date Description Debit Credit Balance
        r'(\d{2}\s+\w{3}\s+\d{4})\s+(.+?)\s+([-£]?\d+\.\d{2})\s+',
        # Pattern 3: Common UK bank format
        r'(\d{2}\s+\w{3})\s+(.+?)\s+([-£]?\d+\.\d{2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            date_str = match.group(1)
            description = match.group(2).strip()
            amount = match.group(3).replace('£', '').replace(',', '')
            
            # Convert date to standard format
            try:
                # Try different date formats
                for date_format in ['%d/%m/%Y', '%d %b %Y', '%d %b']:
                    try:
                        date_obj = datetime.strptime(date_str, date_format)
                        # If year is missing, use current year
                        if date_format == '%d %b':
                            date_obj = date_obj.replace(year=datetime.now().year)
                        date_formatted = date_obj.strftime('%Y-%m-%d')
                        break
                    except:
                        continue
            except:
                date_formatted = date_str
            
            return {
                'date': date_formatted,
                'description': description,
                'amount': float(amount)
            }
    
    return None

def categorize_transaction(description):
    """
    Categorize transaction based on description
    """
    desc_lower = description.lower()
    
    categories = {
        'Groceries': ['tesco', 'sainsbury', 'asda', 'waitrose', 'lidl', 'aldi', 'morrisons', 'co-op'],
        'Transport': ['tfl', 'uber', 'rail', 'train', 'bus', 'tube', 'oyster'],
        'Fast Food': ['mcdonald', 'kfc', 'burger', 'subway', 'pizza hut', 'dominos'],
        'Coffee Shops': ['costa', 'starbucks', 'pret', 'caffè nero', 'coffee'],
        'Food Delivery': ['deliveroo', 'just eat', 'uber eat', 'foodhub'],
        'Subscriptions': ['netflix', 'spotify', 'amazon prime', 'disney', 'apple'],
        'Fuel': ['shell', 'bp', 'esso', 'texaco', 'petrol', 'fuel'],
        'Parking': ['parking', 'ncp', 'ringo'],
        'Restaurants': ['restaurant', 'wagamama', 'nando', 'zizzi', 'prezzo', 'cafe', 'bar'],
        'Shopping': ['amazon', 'ebay', 'asos', 'next', 'h&m', 'zara', 'primark'],
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    
    return 'Other'

def process_pdf_text(text_content):
    """
    Process PDF text content and extract transactions
    """
    lines = text_content.strip().split('\n')
    transactions = []
    transaction_id = 1
    
    for line in lines:
        transaction = parse_transaction_line(line)
        if transaction:
            # Add additional fields
            transaction['id'] = transaction_id
            transaction['category'] = categorize_transaction(transaction['description'])
            transaction['month'] = datetime.strptime(transaction['date'], '%Y-%m-%d').strftime('%B')
            
            transactions.append(transaction)
            transaction_id += 1
    
    return transactions

def convert_to_javascript(transactions):
    """
    Convert transactions to JavaScript format for direct use in React app
    """
    js_content = "export const transactions = [\n"
    
    for trans in transactions:
        js_content += f"  {{\n"
        js_content += f"    id: {trans['id']},\n"
        js_content += f"    date: '{trans['date']}',\n"
        js_content += f"    description: '{trans['description']}',\n"
        js_content += f"    amount: {trans['amount']},\n"
        js_content += f"    category: '{trans['category']}',\n"
        js_content += f"    month: '{trans['month']}'\n"
        js_content += f"  }},\n"
    
    js_content += "];\n"
    return js_content

def main():
    print("PDF Bank Statement Parser")
    print("=" * 50)
    print("\nThis script helps convert PDF bank statement text to transaction data.")
    print("\nInstructions:")
    print("1. Open your PDF bank statement")
    print("2. Select all text (Ctrl+A) and copy (Ctrl+C)")
    print("3. Paste the text into a file called 'statement.txt'")
    print("4. Run this script\n")
    
    try:
        # Read the statement text
        with open('statement.txt', 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Process transactions
        transactions = process_pdf_text(text_content)
        
        if not transactions:
            print("No transactions found. Please check the format of your statement.")
            print("You may need to adjust the regex patterns in parse_transaction_line()")
            return
        
        print(f"Found {len(transactions)} transactions")
        
        # Save as JSON
        with open('transactions.json', 'w') as f:
            json.dump(transactions, f, indent=2)
        print("✓ Saved to transactions.json")
        
        # Save as JavaScript
        js_content = convert_to_javascript(transactions)
        with open('transactions.js', 'w') as f:
            f.write(js_content)
        print("✓ Saved to transactions.js")
        
        # Show summary
        print("\nSummary by Category:")
        category_totals = {}
        for trans in transactions:
            cat = trans['category']
            if cat not in category_totals:
                category_totals[cat] = 0
            category_totals[cat] += abs(trans['amount'])
        
        for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: £{total:.2f}")
        
        print(f"\nTotal Spending: £{sum(abs(t['amount']) for t in transactions):.2f}")
        
    except FileNotFoundError:
        print("Error: statement.txt not found!")
        print("Please create a file called 'statement.txt' with your PDF content.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()