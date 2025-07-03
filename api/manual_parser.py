"""
Manual parser for bank statements based on the exact format shown in screenshots
"""

import re
from datetime import datetime

def parse_bank_statement_text(text, month_name):
    """Parse transactions from bank statement text"""
    transactions = []
    
    # Based on your screenshots, the format is:
    # DD Mon YY  DD Mon YY  ))) DESCRIPTION  LOCATION  AMOUNT
    # or
    # DD Mon YY  DD Mon YY  DESCRIPTION  LOCATION  AMOUNT
    
    lines = text.split('\n')
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Try to match the transaction pattern
        # Pattern: DD Mon YY followed by another date, then description and amount
        pattern = r'(\d{1,2}\s+\w{3}\s+\d{2})\s+\d{1,2}\s+\w{3}\s+\d{2}\s+\)?\)?\)?\s*([^£\d]+?)\s+([\d,]+\.\d{2})(?:\s*CR)?'
        
        match = re.search(pattern, line)
        if match:
            date_str = match.group(1)  # e.g., "11 Dec 24"
            description = match.group(2).strip()
            amount_str = match.group(3)
            
            # Parse date
            try:
                # Convert "11 Dec 24" to "2024-12-11"
                date_obj = datetime.strptime(date_str, "%d %b %y")
                formatted_date = date_obj.strftime("%Y-%m-%d")
            except:
                formatted_date = date_str
            
            # Parse amount
            amount = float(amount_str.replace(',', ''))
            
            # Check if it's a credit (CR at end of line)
            if 'CR' in line[match.end():match.end()+5]:
                amount = amount  # Credit (positive)
            else:
                amount = -amount  # Debit (negative)
            
            # Clean description - remove location info after multiple spaces
            desc_parts = description.split('  ')
            clean_desc = desc_parts[0].strip()
            
            transaction = {
                'date': formatted_date,
                'description': clean_desc,
                'amount': amount,
                'category': categorize_transaction(clean_desc),
                'month': month_name,
                'source': 'Credit Card'
            }
            
            transactions.append(transaction)
    
    return transactions

def categorize_transaction(description):
    """Categorize based on description"""
    desc_upper = description.upper()
    
    # Based on your screenshots
    if 'CAFFE NERO' in desc_upper or 'STARBUCKS' in desc_upper:
        return 'Coffee Shops'
    elif 'TFL' in desc_upper or 'RAIL' in desc_upper or 'UBER' in desc_upper:
        return 'Transport'
    elif 'MCDONALD' in desc_upper or 'KFC' in desc_upper or 'BURGER' in desc_upper:
        return 'Fast Food'
    elif 'DELIVEROO' in desc_upper or 'JUST EAT' in desc_upper or 'UBER EAT' in desc_upper:
        return 'Food Delivery'
    elif 'TESCO' in desc_upper or 'SAINSBURY' in desc_upper or 'WAITROSE' in desc_upper:
        return 'Groceries'
    elif 'AMAZON' in desc_upper or 'EBAY' in desc_upper:
        return 'Shopping'
    elif 'PAYMENT' in desc_upper or 'THANK YOU' in desc_upper:
        return 'Payments'
    elif any(restaurant in desc_upper for restaurant in ['NANDO', 'WAGAMAMA', 'PIZZA', 'RESTAURANT']):
        return 'Restaurants'
    elif 'SUBSCRIPTION' in desc_upper or 'NETFLIX' in desc_upper or 'SPOTIFY' in desc_upper:
        return 'Subscriptions'
    elif 'PARKING' in desc_upper:
        return 'Parking'
    else:
        return 'Other'

# Test with sample data from your screenshot
sample_text = """11 Dec 24  10 Dec 24  ))) CAFFE NERO WINDSOR PEA WINDSOR  3.60
11 Dec 24  09 Dec 24  ))) THUNDERBIRD FRIED CHIC LONDON E20  12.25
12 Dec 24  10 Dec 24  ))) CAFFE NERO 535 STRATFO LONDON  3.75
12 Dec 24  10 Dec 24  ))) TFL TRAVEL CH  TFL.GOV.UK/CP  22.90
13 Dec 24  11 Dec 24  ))) GREGGS PLC  PLAISTOW  3.55
14 Dec 24  13 Dec 24  ))) MCDONALDS 1008  SLOUGH  16.47
18 Dec 24  16 Dec 24  ))) CAFFE NERO WINDSOR PEA WINDSOR  5.75
19 Dec 24  18 Dec 24  ))) TFL TRAVEL CH  TFL.GOV.UK/CP  22.90
21 Dec 24  20 Dec 24  ))) PAYMENT - THANK YOU  500.00CR"""

if __name__ == "__main__":
    # Test the parser
    transactions = parse_bank_statement_text(sample_text, "December")
    for t in transactions:
        print(f"{t['date']}: {t['description']} - £{abs(t['amount']):.2f} {'CR' if t['amount'] > 0 else ''} [{t['category']}]")