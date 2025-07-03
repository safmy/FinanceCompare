"""
Corrected PDF processor that properly handles bank statement format
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

class CorrectedPDFProcessor:
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
    
    def parse_transactions(self, text, month_name, source='Current Account'):
        """Parse ALL transactions from bank statement text"""
        if not text:
            return []
        
        transactions = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Track state
        in_transaction_section = False
        current_date = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Start transaction section
            if 'Your Bank Account details' in line:
                in_transaction_section = True
                continue
            
            # End transaction section
            if 'Prospect Place Darlington' in line:
                in_transaction_section = False
                continue
            
            if not in_transaction_section:
                continue
            
            # Skip headers
            if any(skip in line for skip in ['Date Payment type', 'BALANCEBROUGHTFORWARD', 'BALANCECARRIEDFORWARD']):
                continue
            
            # Check for date line (DD Mon YY at start)
            date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})\s+(.+)', line)
            if date_match:
                current_date = self.parse_date(date_match.group(1))
                rest_of_line = date_match.group(2)
                
                # Parse transaction from rest of line
                trans = self.parse_transaction_line(rest_of_line, current_date)
                if trans:
                    transactions.append(trans)
            
            # Check for continuation line (starts with )))
            elif line.startswith(')))') and current_date:
                rest_of_line = line[3:].strip()
                trans = self.parse_transaction_line(rest_of_line, current_date)
                if trans:
                    transactions.append(trans)
            
            # Check for other transaction patterns (VIS, DD, CR, etc.)
            elif current_date and any(line.startswith(prefix) for prefix in ['VIS ', 'DD ', 'CR ', 'TFR ', 'BP ', 'SO ', 'ATM ']):
                trans = self.parse_transaction_line(line, current_date)
                if trans:
                    transactions.append(trans)
        
        print(f"Parsed {len(transactions)} transactions from {month_name}")
        return transactions
    
    def parse_transaction_line(self, line, date):
        """Parse a single transaction line"""
        if not line or 'BALANCE' in line.upper():
            return None
        
        # The format is typically:
        # TYPE MERCHANT_NAME LOCATION/DETAILS amount [balance]
        # We need to find the transaction amount (not the balance)
        
        # Find all numbers that could be amounts (format: 123.45)
        numbers = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2})', line)
        
        if not numbers:
            return None
        
        # The transaction amount is usually the first number
        # The balance (if present) is the last number and often has 'D' suffix
        transaction_amount = None
        
        if len(numbers) == 1:
            # Only one number, it's the transaction amount
            transaction_amount = numbers[0]
        else:
            # Multiple numbers - first is usually transaction, last is usually balance
            # Check if last number has 'D' after it (indicates debit balance)
            if re.search(rf'{re.escape(numbers[-1])}\s*D', line):
                # Last number is balance, use first as transaction
                transaction_amount = numbers[0]
            else:
                # Use first number as transaction amount
                transaction_amount = numbers[0]
        
        if not transaction_amount:
            return None
        
        # Convert to float
        try:
            amount = float(transaction_amount.replace(',', ''))
        except:
            return None
        
        # Extract description (everything before the first amount)
        amount_pos = line.find(transaction_amount)
        if amount_pos > 0:
            description = line[:amount_pos].strip()
        else:
            description = line
        
        # Clean up description - remove trailing spaces and dots
        description = description.strip(' .')
        
        # Determine if debit or credit
        if any(prefix in description for prefix in ['CR ', 'TFR ']):
            # Credit transaction
            amount = abs(amount)
        else:
            # Debit transaction
            amount = -abs(amount)
        
        # Special handling for income
        income_keywords = ['WEEKLY SUBSISTENCE', 'CHILD BENEFIT', 'GIFT', 'PAYMENT THANK YOU', 'PAYMENT RECEIVED']
        if any(keyword in description.upper() for keyword in income_keywords):
            amount = abs(amount)
        
        return {
            'date': date,
            'description': description,
            'amount': amount,
            'category': self.categorize_transaction(description),
            'type': 'credit' if amount > 0 else 'debit'
        }
    
    def parse_date(self, date_str):
        """Parse date string to standard format"""
        try:
            # Handle dates like "05 Dec 24"
            parts = date_str.strip().split()
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = '20' + year
                date_str = f"{day} {month} {year}"
            
            date_obj = datetime.strptime(date_str, "%d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Date parse error for '{date_str}': {e}")
            return "2024-01-01"
    
    def categorize_transaction(self, description):
        """Categorize transaction based on description"""
        desc_upper = description.upper()
        
        # Income
        if any(pattern in desc_upper for pattern in [
            'CHILD BENEFIT', 'WEEKLY SUBSISTENCE', 'GIFT', 'SALARY', 
            'PAYMENT THANK YOU', 'PAYMENT RECEIVED', 'CR PAYMENT'
        ]):
            return 'Income'
        
        # Rent
        if 'RENT' in desc_upper:
            return 'Rent'
        
        # Financial Services
        if any(pattern in desc_upper for pattern in ['HSBC', 'LOAN', 'PAYPAL', 'ATM', 'BANK']):
            return 'Financial Services'
        
        # Bills & Utilities
        if any(pattern in desc_upper for pattern in ['DD EE', 'DDEE', 'ELECTRIC', 'GAS', 'WATER', 'EE LIMITED']):
            return 'Bills & Utilities'
        
        # Groceries
        if any(pattern in desc_upper for pattern in [
            'SAINSBURY', 'TESCO', 'ASDA', 'BUDGENS', 'CO-OP', 'ALDI', 'LIDL', 'WAITROSE'
        ]):
            return 'Groceries'
        
        # Transport
        if any(pattern in desc_upper for pattern in ['TFL', 'UBER', 'TAXI', 'TRAIN', 'RAIL']):
            return 'Transport'
        
        # Fast Food
        if any(pattern in desc_upper for pattern in ['GREGGS', 'MCDONALD', 'KFC', 'SUBWAY', 'BURGER']):
            return 'Fast Food'
        
        # Coffee Shops
        if any(pattern in desc_upper for pattern in ['CAFFE NERO', 'STARBUCKS', 'COSTA', 'PRET A MANGER']):
            return 'Coffee Shops'
        
        # Shopping
        if any(pattern in desc_upper for pattern in [
            'AMAZON', 'PRIMARK', 'T K MAXX', 'TK MAXX', 'H & M', 'H&M', 'BOOTS', 
            'HOLLAND & BARRETT', 'APPLE.COM', 'GOOGLE', 'AUDIBLE', 'IKEA', 'ARGOS'
        ]):
            return 'Shopping'
        
        # Entertainment/Subscriptions
        if any(pattern in desc_upper for pattern in [
            'LITTLE GYM', 'CINEMA', 'EVERYONE ACTIVE', 'NETFLIX', 'SPOTIFY', 'GYM'
        ]):
            return 'Entertainment'
        
        # Restaurants
        if any(pattern in desc_upper for pattern in ['NANDO', 'WAGAMAMA', 'PIZZA', 'RESTAURANT']):
            return 'Restaurants'
        
        # Pharmacy/Healthcare
        if any(pattern in desc_upper for pattern in ['PHARMA', 'CHEMIST', 'MEDICAL']):
            return 'Healthcare'
        
        return 'Other'
    
    def process_pdf_batch(self, pdf_files_data):
        """Process multiple PDFs"""
        all_transactions = []
        transaction_id = 1
        
        for i, pdf_data in enumerate(pdf_files_data):
            try:
                pdf_content = base64.b64decode(pdf_data['content'])
                month_name = pdf_data['month']
                source = pdf_data.get('source', 'Current Account')
                
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