#!/usr/bin/env python3
"""
Extract transaction data from PDF bank statements
This script helps convert PDF text to transaction data for the React dashboard
"""

import PyPDF2
import re
import json
from datetime import datetime
import sys

def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def parse_transactions(text, month_name):
    """Parse transactions from extracted text"""
    transactions = []
    
    # Common transaction patterns - adjust based on your bank format
    patterns = [
        # Pattern: DD MMM Description Amount
        r'(\d{1,2}\s+\w{3})\s+([A-Z][A-Z\s&\-\.]+?)\s+([\d,]+\.\d{2})',
        # Pattern: DD/MM/YYYY Description Amount
        r'(\d{2}/\d{2}/\d{4})\s+([A-Z][A-Z\s&\-\.]+?)\s+([\d,]+\.\d{2})',
        # Pattern with merchant details
        r'(\d{1,2}\s+\w{3})\s+(.+?)\s+(?:CARD\s+\d+|REF\s+\d+)?\s*([\d,]+\.\d{2})',
    ]
    
    lines = text.split('\n')
    transaction_id = 1
    
    for line in lines:
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    date_str = match.group(1)
                    description = match.group(2).strip()
                    amount = float(match.group(3).replace(',', ''))
                    
                    # Skip balance lines
                    if any(skip in description.upper() for skip in ['BALANCE', 'TOTAL', 'BROUGHT FORWARD']):
                        continue
                    
                    # Clean up description
                    description = re.sub(r'\s+', ' ', description)
                    description = description.title()
                    
                    # Determine if it's a debit (negative) or credit (positive)
                    # Most purchases are debits (negative)
                    if not any(credit in description.upper() for credit in ['PAYMENT', 'CREDIT', 'REFUND', 'TRANSFER IN']):
                        amount = -amount
                    
                    transaction = {
                        'id': transaction_id,
                        'date': date_str,
                        'description': description,
                        'amount': amount,
                        'category': categorize_transaction(description),
                        'month': month_name
                    }
                    
                    transactions.append(transaction)
                    transaction_id += 1
                    break
                    
                except Exception as e:
                    continue
    
    return transactions

def categorize_transaction(description):
    """Categorize transaction based on description"""
    desc_upper = description.upper()
    
    categories = {
        'Groceries': ['TESCO', 'SAINSBURY', 'ASDA', 'WAITROSE', 'LIDL', 'ALDI', 'MORRISONS', 'CO-OP', 'MARKS & SPENCER', 'M&S'],
        'Transport': ['TFL', 'UBER', 'RAIL', 'TRAIN', 'BUS', 'TUBE', 'OYSTER', 'TAXI', 'LONDON UNDERGROUND'],
        'Fast Food': ['MCDONALD', 'KFC', 'BURGER', 'SUBWAY', 'PIZZA HUT', 'DOMINO', 'PAPA JOHN', 'FIVE GUYS'],
        'Coffee Shops': ['COSTA', 'STARBUCKS', 'PRET', 'NERO', 'COFFEE', 'CAFE'],
        'Food Delivery': ['DELIVEROO', 'JUST EAT', 'UBER EAT', 'FOODHUB'],
        'Subscriptions': ['NETFLIX', 'SPOTIFY', 'AMAZON PRIME', 'DISNEY', 'APPLE', 'GOOGLE', 'MICROSOFT'],
        'Fuel': ['SHELL', 'BP', 'ESSO', 'TEXACO', 'PETROL', 'FUEL', 'MURCO'],
        'Parking': ['PARKING', 'NCP', 'RINGO', 'PARKINGPERMIT'],
        'Restaurants': ['RESTAURANT', 'WAGAMAMA', 'NANDO', 'ZIZZI', 'PREZZO', 'GRILL', 'KITCHEN', 'DINING'],
        'Shopping': ['AMAZON', 'EBAY', 'ASOS', 'NEXT', 'H&M', 'ZARA', 'PRIMARK', 'JOHN LEWIS', 'ARGOS'],
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in desc_upper:
                return category
    
    # Additional categorization logic
    if any(word in desc_upper for word in ['PHARMACY', 'BOOTS', 'SUPERDRUG']):
        return 'Healthcare'
    elif any(word in desc_upper for word in ['GYM', 'FITNESS', 'SPORT']):
        return 'Fitness'
    elif any(word in desc_upper for word in ['MOBILE', 'PHONE', 'VODAFONE', 'EE', 'O2', 'THREE']):
        return 'Phone'
    
    return 'Other'

def main():
    # PDF files and their corresponding months
    pdf_files = [
        ('2025-01-09_Statement.pdf', 'January'),
        ('2025-02-08_Statement.pdf', 'February'),
        ('2025-03-08_Statement.pdf', 'March'),
        ('2025-04-09_Statement.pdf', 'April'),
        ('2025-05-09_Statement.pdf', 'May'),
        ('2025-06-09_Statement.pdf', 'June'),
    ]
    
    all_transactions = []
    transaction_id = 1
    
    print("Extracting transactions from PDF statements...")
    
    for pdf_file, month in pdf_files:
        print(f"\nProcessing {pdf_file}...")
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_file)
        if not text:
            print(f"  ⚠️  Could not extract text from {pdf_file}")
            continue
        
        # Parse transactions
        transactions = parse_transactions(text, month)
        
        # Update IDs to be continuous
        for trans in transactions:
            trans['id'] = transaction_id
            transaction_id += 1
        
        all_transactions.extend(transactions)
        print(f"  ✓ Found {len(transactions)} transactions")
    
    print(f"\nTotal transactions extracted: {len(all_transactions)}")
    
    # Generate JavaScript file
    js_content = "// Extracted transaction data from bank statements\n\n"
    js_content += "export const transactions = [\n"
    
    for trans in all_transactions:
        # Format date properly
        try:
            # Try to parse and format date
            if '/' in trans['date']:
                date_obj = datetime.strptime(trans['date'], '%d/%m/%Y')
            else:
                # Handle DD MMM format - assume current year
                date_obj = datetime.strptime(f"{trans['date']} 2025", '%d %b %Y')
            
            formatted_date = date_obj.strftime('%Y-%m-%d')
        except:
            formatted_date = trans['date']
        
        js_content += f"  {{\n"
        js_content += f"    id: {trans['id']},\n"
        js_content += f"    date: '{formatted_date}',\n"
        js_content += f"    description: '{trans['description'].replace("'", "\\'")}',\n"
        js_content += f"    amount: {trans['amount']},\n"
        js_content += f"    category: '{trans['category']}',\n"
        js_content += f"    month: '{trans['month']}'\n"
        js_content += f"  }},\n"
    
    js_content += "];\n\n"
    
    # Add category colors
    js_content += """// Category colors for consistent visualization
export const categoryColors = {
  'Transport': '#3B82F6',
  'Fast Food': '#EF4444',
  'Groceries': '#10B981',
  'Restaurants': '#F59E0B',
  'Coffee Shops': '#8B5CF6',
  'Food Delivery': '#EC4899',
  'Subscriptions': '#6366F1',
  'Fuel': '#14B8A6',
  'Shopping': '#F97316',
  'Parking': '#F59E0B',
  'Healthcare': '#06B6D4',
  'Fitness': '#84CC16',
  'Phone': '#A855F7',
  'Other': '#6B7280'
};

// Budget targets (optional - set your monthly budget for each category)
export const budgetTargets = {
  'Transport': 300,
  'Fast Food': 100,
  'Groceries': 400,
  'Restaurants': 200,
  'Coffee Shops': 50,
  'Food Delivery': 150,
  'Subscriptions': 100,
  'Fuel': 200,
  'Shopping': 300,
  'Parking': 50,
  'Healthcare': 100,
  'Fitness': 50,
  'Phone': 50,
  'Other': 200
};"""
    
    # Save to file
    output_file = '../src/data/extractedData.js'
    with open(output_file, 'w') as f:
        f.write(js_content)
    
    print(f"\n✅ Data exported to {output_file}")
    
    # Show summary
    print("\nSummary by Category:")
    category_totals = {}
    for trans in all_transactions:
        cat = trans['category']
        if cat not in category_totals:
            category_totals[cat] = {'count': 0, 'amount': 0}
        category_totals[cat]['count'] += 1
        category_totals[cat]['amount'] += abs(trans['amount'])
    
    for cat, data in sorted(category_totals.items(), key=lambda x: x[1]['amount'], reverse=True):
        print(f"  {cat}: £{data['amount']:.2f} ({data['count']} transactions)")
    
    total_spending = sum(abs(t['amount']) for t in all_transactions if t['amount'] < 0)
    print(f"\nTotal Spending: £{total_spending:.2f}")

if __name__ == "__main__":
    main()