"""
Credit Card PDF processor that handles HSBC credit card statement format
"""

import os
import base64
import re
from datetime import datetime
import json
from io import BytesIO

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    
import PyPDF2

class CreditCardProcessor:
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    def extract_text_from_pdf(self, pdf_content):
        """Extract text from PDF - try multiple methods"""
        try:
            pdf_file = BytesIO(pdf_content)
            all_text = ""
            
            # Try pdfplumber first
            if HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                all_text += page_text + "\n"
                    
                    if all_text:
                        print(f"pdfplumber extracted {len(all_text)} characters")
                        return all_text
                except Exception as e:
                    print(f"pdfplumber error: {e}")
            
            # Fallback to PyPDF2
            pdf_file.seek(0)
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file, strict=False)
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        all_text += page_text + "\n"
                    except Exception as e:
                        print(f"Error on page {i+1}: {e}")
                        continue
                
                print(f"PyPDF2 extracted {len(all_text)} characters")
            except Exception as e:
                print(f"PyPDF2 error: {e}")
            
            return all_text if all_text else None
            
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return None
    
    def parse_credit_card_date(self, date_str):
        """Parse credit card date format: '08 May 25' -> '2025-05-08'"""
        try:
            # Simple format: DD Mmm YY
            parts = date_str.strip().split()
            if len(parts) == 3:
                day = parts[0]
                month = parts[1]
                year = parts[2]
                
                # Convert 2-digit year to 4-digit
                if len(year) == 2:
                    year = '20' + year
                
                date_obj = datetime.strptime(f"{day} {month} {year}", "%d %b %Y")
                return date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Date parse error for '{date_str}': {e}")
        
        return "2025-01-01"  # Default date
    
    def parse_transactions(self, text, month_name, source='Credit Card'):
        """Parse transactions from credit card statement format"""
        if not text:
            return []
        
        transactions = []
        lines = text.split('\n')
        
        # Find transaction section
        trans_start = -1
        for i, line in enumerate(lines):
            # Check various formats due to PDF extraction differences
            if any(marker in line for marker in [
                'YourTransactionDetails',
                'Your Transaction Details',
                'Your transaction details',
                'Transaction Details'
            ]):
                trans_start = i
                break
        
        if trans_start < 0:
            print("Could not find transaction section header")
            return []
        
        # Skip to actual transactions (after header line)
        i = trans_start + 2  # Skip 'YourTransactionDetails' and column headers
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # End markers
            if any(marker in line for marker in ['Statement Date', 'Sheet number', 'continued overleaf']):
                i += 1
                continue
            
            # Parse transaction line
            # Format from pdfplumber: "10 May 25 08 May 25 )))CAFFE NERO WINDSOR PEA WINDSOR 8.00"
            # First date is ReceivedByUs, second is TransactionDate
            
            # Match both dates at start of line
            date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})\s+(\d{2}\s+\w{3}\s+\d{2})\s+(.*)$', line)
            if date_match:
                received_date_str = date_match.group(1)  # Not used currently
                trans_date_str = date_match.group(2)     # This is the actual transaction date
                date = self.parse_credit_card_date(trans_date_str)
                remainder = date_match.group(3)
                
                # Extract description and amount
                trans = self.extract_transaction_details(remainder, date)
                if trans:
                    transactions.append(trans)
            
            i += 1
        
        # Filter out invalid transactions
        valid_transactions = [t for t in transactions if t and t['amount'] != 0]
        
        print(f"Parsed {len(valid_transactions)} transactions from {month_name}")
        return valid_transactions
    
    def extract_transaction_details(self, line, date):
        """Extract transaction details from the remainder of a line after the date"""
        # Check for multi-line transactions (exchange rate info)
        # For now, just handle single line transactions
        
        # Remove transaction prefix if present
        if line.startswith(')))'):
            line = line[3:].strip()
        elif line.startswith('IAP'):
            line = line[3:].strip()
        
        # Look for amount at end of line
        # Pattern: description followed by amount, possibly with CR suffix
        amount_match = re.search(r'^(.*?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})(CR)?$', line)
        
        if not amount_match:
            return None
        
        description = amount_match.group(1).strip()
        amount_str = amount_match.group(2)
        is_credit = amount_match.group(3) == 'CR'
        
        # Convert amount to float
        amount = float(amount_str.replace(',', ''))
        
        # Credits are positive, debits are negative
        if is_credit:
            amount = abs(amount)
        else:
            amount = -abs(amount)
        
        return {
            'date': date,
            'description': description,
            'amount': amount,
            'category': self.categorize_transaction(description),
            'type': 'credit' if amount > 0 else 'debit'
        }
    
    def categorize_transaction(self, description):
        """Categorize transaction based on description"""
        desc_upper = description.upper()
        
        # Payments/Credits
        if 'PAYMENT' in desc_upper and 'THANK YOU' in desc_upper:
            return 'Payment'
        
        # Fees
        if any(fee in desc_upper for fee in ['OVERLIMIT FEE', 'TRANSACTION FEE', 'ANNUAL FEE']):
            return 'Fees'
        
        # Groceries
        if any(pattern in desc_upper for pattern in [
            'SAINSBURY', 'TESCO', 'ASDA', 'BUDGENS', 'CO-OP', 'ALDI', 'LIDL', 
            'WAITROSE', 'MORRISONS', 'COSTCO'
        ]):
            return 'Groceries'
        
        # Transport
        if any(pattern in desc_upper for pattern in ['TFL', 'UBER', 'TAXI', 'TRAIN', 'RAIL', 'OYSTER', 'PARKING']):
            return 'Transport'
        
        # Fast Food
        if any(pattern in desc_upper for pattern in ['GREGGS', 'MCDONALD', 'KFC', 'SUBWAY', 'BURGER', 'PIZZA', 'DOMINO']):
            return 'Fast Food'
        
        # Coffee Shops
        if any(pattern in desc_upper for pattern in ['CAFFE NERO', 'STARBUCKS', 'COSTA', 'PRET A MANGER']):
            return 'Coffee Shops'
        
        # Online Services
        if any(pattern in desc_upper for pattern in ['ANTHROPIC', 'OPENAI', 'PRIME VIDEO', 'NETFLIX', 'SPOTIFY']):
            return 'Online Services'
        
        # Shopping
        if any(pattern in desc_upper for pattern in [
            'AMAZON', 'PRIMARK', 'T K MAXX', 'TK MAXX', 'H & M', 'H&M', 'BOOTS', 
            'HOLLAND & BARRETT', 'APPLE.COM', 'GOOGLE', 'AUDIBLE', 'IKEA', 'ARGOS'
        ]):
            return 'Shopping'
        
        # Entertainment
        if any(pattern in desc_upper for pattern in ['ZOO', 'CINEMA', 'AMUSEM', 'FUNFAIR']):
            return 'Entertainment'
        
        # Restaurants
        if any(pattern in desc_upper for pattern in ['NANDO', 'WAGAMAMA', 'PIZZA EXPRESS', 'RESTAURANT', 'DELIGHT']):
            return 'Restaurants'
        
        # Bakery
        if 'BAKERY' in desc_upper:
            return 'Bakery'
        
        return 'Other'
    
    def process_pdf_batch(self, pdf_files_data):
        """Process multiple PDFs"""
        all_transactions = []
        transaction_id = 1
        
        for i, pdf_data in enumerate(pdf_files_data):
            try:
                pdf_content = base64.b64decode(pdf_data['content'])
                month_name = pdf_data['month']
                source = pdf_data.get('source', 'Credit Card')
                
                print(f"\nProcessing PDF {i+1} for {month_name} (Source: {source})")
                
                text = self.extract_text_from_pdf(pdf_content)
                
                if text:
                    transactions = self.parse_transactions(text, month_name, source)
                    
                    # Add IDs and month info
                    for trans in transactions:
                        trans['id'] = transaction_id
                        trans['month'] = month_name
                        trans['source'] = source
                        transaction_id += 1
                    
                    all_transactions.extend(transactions)
                else:
                    print(f"No text extracted from PDF for {month_name}")
                    
            except Exception as e:
                print(f"Error processing PDF {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\nTotal transactions found: {len(all_transactions)}")
        return all_transactions