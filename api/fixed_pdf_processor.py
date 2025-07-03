"""
Enhanced PDF processor to capture ALL transactions from bank statements
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

class FixedPDFProcessor:
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
        lines = text.split('\n')
        
        # First, find the transaction section
        in_transaction_section = False
        transaction_lines = []
        
        for line in lines:
            # Skip headers and footers
            if 'Your Bank Account details' in line:
                in_transaction_section = True
                continue
            elif 'BALANCECARRIEDFORWARD' in line or 'Prospect Place Darlington' in line:
                in_transaction_section = False
                
            if in_transaction_section and line.strip():
                transaction_lines.append(line)
        
        # Now parse transactions line by line
        i = 0
        while i < len(transaction_lines):
            line = transaction_lines[i].strip()
            
            # Skip header lines
            if ('Date' in line and 'Payment type' in line) or line == 'A' or 'BALANCEBROUGHTFORWARD' in line:
                i += 1
                continue
            
            # Check for date at start of line (format: DD Mon YY)
            date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})\s+(.+)', line)
            if date_match:
                date_str = date_match.group(1)
                rest_of_line = date_match.group(2)
                
                # Parse all transactions for this date
                transactions_on_date = self.parse_transactions_for_date(
                    date_str, rest_of_line, transaction_lines, i
                )
                
                for trans in transactions_on_date:
                    if trans:  # Skip None results
                        transactions.append(trans)
            
            i += 1
        
        # Filter out invalid transactions
        valid_transactions = []
        for trans in transactions:
            # Skip balance entries and invalid amounts
            if trans and 'BALANCE' not in trans['description'].upper():
                # Ensure we have a valid numeric amount
                try:
                    float(trans['amount'])
                    valid_transactions.append(trans)
                except:
                    continue
        
        print(f"Parsed {len(valid_transactions)} transactions from {month_name}")
        return valid_transactions
    
    def parse_transactions_for_date(self, date_str, first_line_content, all_lines, current_idx):
        """Parse all transactions for a given date"""
        transactions = []
        
        # Format the date
        formatted_date = self.parse_date(date_str)
        
        # Process the first line content
        if first_line_content.strip():
            trans = self.parse_single_transaction(first_line_content, formatted_date)
            if trans:
                transactions.append(trans)
        
        # Look for continuation lines (starting with )))
        idx = current_idx + 1
        while idx < len(all_lines):
            line = all_lines[idx].strip()
            
            # Stop if we hit a new date or end markers
            if re.match(r'^\d{2}\s+\w{3}\s+\d{2}', line) or 'BALANCECARRIEDFORWARD' in line:
                break
            
            # Process continuation lines
            if line.startswith(')))'):
                content = line[3:].strip()
                trans = self.parse_single_transaction(content, formatted_date)
                if trans:
                    transactions.append(trans)
            elif line and not line.startswith('Date') and line != 'A':
                # Sometimes transactions continue without )))
                trans = self.parse_single_transaction(line, formatted_date)
                if trans:
                    transactions.append(trans)
            
            idx += 1
        
        return transactions
    
    def parse_single_transaction(self, line_content, date):
        """Parse a single transaction from a line"""
        if not line_content or 'BALANCE' in line_content.upper():
            return None
        
        # Extract transaction type, description, and amount
        # Common patterns: VIS, DD, CR, TFR, BP, SO, ATM
        
        # Look for amount at the end (format: 123.45 or 1,234.56)
        amount_pattern = r'([0-9,]+\.\d{2})(?:\s*[DC]?)?\s*$'
        amount_match = re.search(amount_pattern, line_content)
        
        if not amount_match:
            return None
        
        amount_str = amount_match.group(1).replace(',', '')
        try:
            amount = float(amount_str)
        except:
            return None
        
        # Get description (everything before the amount)
        description = line_content[:amount_match.start()].strip()
        
        # Determine transaction type and sign
        trans_type = 'debit'
        if description.startswith(('CR ', 'TFR ')):
            trans_type = 'credit'
            amount = abs(amount)  # Credit is positive
        else:
            amount = -abs(amount)  # Debit is negative
        
        # Special cases for income
        income_keywords = ['WEEKLY SUBSISTENCE', 'CHILD BENEFIT', 'GIFT', 'PAYMENT THANK YOU']
        if any(keyword in description.upper() for keyword in income_keywords):
            trans_type = 'credit'
            amount = abs(amount)
        
        return {
            'date': date,
            'description': description[:100],  # Limit length
            'amount': amount,
            'category': self.categorize_transaction(description),
            'type': trans_type
        }
    
    def parse_date(self, date_str):
        """Parse date string to standard format"""
        # Format: DD Mon YY (e.g., "04 Dec 24")
        try:
            # Handle year 24 as 2024, 25 as 2025
            parts = date_str.strip().split()
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year_int = int(year)
                    if year_int >= 24:
                        year = '20' + year
                    else:
                        year = '20' + year
                date_str = f"{day} {month} {year}"
            
            date_obj = datetime.strptime(date_str, "%d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Date parse error for '{date_str}': {e}")
            return "2024-01-01"  # Fallback
    
    def categorize_transaction(self, description):
        """Basic categorization"""
        desc_upper = description.upper()
        
        # Income
        if any(pattern in desc_upper for pattern in [
            'CHILD BENEFIT', 'WEEKLY SUBSISTENCE', 'GIFT', 'SALARY', 
            'PAYMENT THANK YOU', 'PAYMENT RECEIVED'
        ]):
            return 'Income'
        
        # Rent
        if 'RENT' in desc_upper:
            return 'Rent'
        
        # Financial Services
        if any(pattern in desc_upper for pattern in ['HSBC', 'LOAN', 'PAYPAL', 'ATM', 'BANK']):
            return 'Financial Services'
        
        # Bills & Utilities
        if any(pattern in desc_upper for pattern in ['DD EE', 'DDEE', 'ELECTRIC', 'GAS', 'WATER']):
            return 'Bills & Utilities'
        
        # Groceries
        if any(pattern in desc_upper for pattern in [
            'SAINSBURY', 'TESCO', 'ASDA', 'BUDGENS', 'CO-OP', 'ALDI', 'LIDL'
        ]):
            return 'Groceries'
        
        # Transport
        if any(pattern in desc_upper for pattern in ['TFL', 'UBER', 'TAXI', 'TRAIN']):
            return 'Transport'
        
        # Fast Food
        if any(pattern in desc_upper for pattern in ['GREGGS', 'MCDONALD', 'KFC', 'SUBWAY']):
            return 'Fast Food'
        
        # Coffee Shops
        if any(pattern in desc_upper for pattern in ['CAFFE NERO', 'STARBUCKS', 'COSTA', 'PRET A MANGER']):
            return 'Coffee Shops'
        
        # Shopping
        if any(pattern in desc_upper for pattern in [
            'AMAZON', 'PRIMARK', 'T K MAXX', 'H & M', 'BOOTS', 'HOLLAND & BARRETT',
            'APPLE.COM', 'GOOGLE', 'AUDIBLE'
        ]):
            return 'Shopping'
        
        # Entertainment/Activities
        if any(pattern in desc_upper for pattern in ['LITTLE GYM', 'CINEMA', 'EVERYONE ACTIVE']):
            return 'Entertainment'
        
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