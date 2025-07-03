"""
Specialized PDF processor for Zivile's bank statement format
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

class ZivilePDFProcessor:
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
                        # Try to continue with other pages
                        continue
                
                print(f"PyPDF2 extracted {len(all_text)} characters")
            except Exception as e:
                print(f"PyPDF2 error: {e}")
            
            return all_text if all_text else None
            
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return None
    
    def parse_transactions(self, text, month_name, source='Current Account'):
        """Parse transactions from Zivile's specific bank format"""
        if not text:
            return []
        
        transactions = []
        lines = text.split('\n')
        
        # Process line by line, looking for transaction patterns
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and headers
            if not line or self.is_header_line(line):
                i += 1
                continue
            
            # Check if this line starts with a date
            date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})', line)
            if date_match:
                date_str = date_match.group(1)
                
                # Look for transaction details on the same line or following lines
                transaction_data = self.extract_transaction_from_date_line(lines, i)
                
                if transaction_data:
                    # Process each transaction found on this date
                    for trans_data in transaction_data['transactions']:
                        trans = self.create_transaction(transaction_data['date_str'], trans_data, month_name, source)
                        if trans:
                            transactions.append(trans)
                    
                    # Skip the lines we've processed
                    i += transaction_data.get('lines_consumed', 1)
                else:
                    i += 1
            else:
                i += 1
        
        print(f"Parsed {len(transactions)} transactions from {month_name}")
        return transactions
    
    def is_header_line(self, line):
        """Check if line is a header or footer"""
        skip_patterns = [
            'YOUR BANK ACCOUNT', 'BALANCE BROUGHT', 'BALANCE CARRIED',
            'STATEMENT', 'PAGE', 'SHEET', 'PAYMENT TYPE', 'PAID OUT',
            'PAID IN', 'PROSPECT PLACE', 'DARLINGTON', 'DURHAM',
            'DATE', 'DESCRIPTION', 'DETAILS'
        ]
        line_upper = line.upper()
        return any(pattern in line_upper for pattern in skip_patterns)
    
    def extract_transaction_from_date_line(self, lines, start_idx):
        """Extract complete transaction starting from a date line"""
        # First line has the date
        first_line = lines[start_idx].strip()
        
        # Extract the date from the beginning
        date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})', first_line)
        if not date_match:
            return None
            
        date_str = date_match.group(1)
        
        # Look for complete transactions on the same line
        # Pattern: date + type/description + amount + optional balance
        # Each transaction should have its own amount
        
        transactions = []
        idx = start_idx
        current_date_block = []
        
        # Collect all lines that belong to this date
        while idx < len(lines):
            line = lines[idx].strip()
            if not line:
                idx += 1
                continue
                
            # If we hit a new date, stop
            if idx > start_idx and re.match(r'^\d{2}\s+\w{3}\s+\d{2}', line):
                break
                
            current_date_block.append(line)
            idx += 1
        
        # Now parse transactions from this date block
        # Each transaction ends with an amount
        current_trans = {
            'type_code': None,
            'description': [],
            'amount': None
        }
        
        for i, line in enumerate(current_date_block):
            # Skip the date line itself
            if i == 0:
                remaining = re.sub(r'^\d{2}\s+\w{3}\s+\d{2}\s*', '', line).strip()
                if not remaining:
                    continue
                line = remaining
            
            # Check if line starts with transaction type
            type_match = re.match(r'^(VIS|DD|CR|ATM|BP|SO|TFR)\s+(.+)', line)
            if type_match:
                # If we have a pending transaction, save it
                if current_trans['amount']:
                    transactions.append(current_trans.copy())
                    current_trans = {'type_code': None, 'description': [], 'amount': None}
                
                current_trans['type_code'] = type_match.group(1)
                rest = type_match.group(2)
                
                # Check if amount is at end of line
                amount_match = re.search(r'([\d,]+\.\d{2})(?:\s*D)?$', rest)
                if amount_match:
                    current_trans['description'].append(rest[:amount_match.start()].strip())
                    current_trans['amount'] = amount_match.group(1)
                    transactions.append(current_trans.copy())
                    current_trans = {'type_code': None, 'description': [], 'amount': None}
                else:
                    current_trans['description'].append(rest)
                    
            elif line.startswith(')))'):
                # Continuation marker - new transaction
                if current_trans['amount']:
                    transactions.append(current_trans.copy())
                    current_trans = {'type_code': None, 'description': [], 'amount': None}
                
                rest = line[3:].strip()
                # Check for amount at end
                amount_match = re.search(r'([\d,]+\.\d{2})(?:\s*D)?$', rest)
                if amount_match:
                    current_trans['description'].append(rest[:amount_match.start()].strip())
                    current_trans['amount'] = amount_match.group(1)
                    transactions.append(current_trans.copy())
                    current_trans = {'type_code': None, 'description': [], 'amount': None}
                else:
                    current_trans['description'].append(rest)
                    
            elif re.match(r'^[\d,]+\.\d{2}(?:\s*D)?$', line):
                # Just an amount - complete current transaction
                if current_trans['description']:
                    current_trans['amount'] = re.match(r'^([\d,]+\.\d{2})', line).group(1)
                    transactions.append(current_trans.copy())
                    current_trans = {'type_code': None, 'description': [], 'amount': None}
                    
            elif re.search(r'([\d,]+\.\d{2})(?:\s*D)?$', line):
                # Line ending with amount
                amount_match = re.search(r'([\d,]+\.\d{2})(?:\s*D)?$', line)
                current_trans['description'].append(line[:amount_match.start()].strip())
                current_trans['amount'] = amount_match.group(1)
                transactions.append(current_trans.copy())
                current_trans = {'type_code': None, 'description': [], 'amount': None}
            else:
                # Description continuation
                current_trans['description'].append(line)
        
        # Don't forget last transaction if incomplete
        if current_trans['amount']:
            transactions.append(current_trans.copy())
        
        # Convert to expected format
        if transactions:
            return {
                'transactions': transactions,
                'date_str': date_str,
                'lines_consumed': idx - start_idx
            }
        else:
            return None
    
    def create_transaction(self, date_str, data, month_name, source):
        """Create a transaction object from parsed data"""
        try:
            # Parse date
            formatted_date = self.parse_date(date_str)
            
            # Build description
            full_description = ' '.join(data['description'])
            if data['type_code'] and data['type_code'] not in full_description:
                full_description = f"{data['type_code']} {full_description}"
            
            # Clean up description
            full_description = re.sub(r'\s+', ' ', full_description).strip()
            
            # Parse amount
            amount = float(data['amount'].replace(',', ''))
            
            # Determine if it's a debit or credit
            # CR prefix or certain descriptions indicate credit
            if (data['type_code'] == 'CR' or 
                'WEEKLY SUBSISTENCE' in full_description.upper() or
                'CHILD BENEFIT' in full_description.upper() or
                'GIFT' in full_description.upper() or
                'PAYMENT RECEIVED' in full_description.upper()):
                amount = abs(amount)  # Credit (positive)
            else:
                amount = -abs(amount)  # Debit (negative)
            
            # Skip balance entries
            if 'BALANCE' in full_description.upper():
                return None
            
            return {
                'date': formatted_date,
                'description': full_description[:100],
                'amount': amount,
                'category': self.categorize_transaction(full_description),
                'month': month_name,
                'source': source
            }
            
        except Exception as e:
            print(f"Error creating transaction: {e}")
            return None
    
    def parse_date(self, date_str):
        """Parse date string to standard format"""
        formats = [
            "%d %b %y", "%d %b %Y", "%d%b%y", "%d%b%Y"
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                return date_obj.strftime("%Y-%m-%d")
            except:
                continue
        
        return "2024-01-01"  # Fallback
    
    def categorize_transaction(self, description):
        """Basic categorization - will be overridden by GPT-4"""
        desc_upper = description.upper()
        
        # Income patterns
        if any(pattern in desc_upper for pattern in ['CHILD BENEFIT', 'WEEKLY SUBSISTENCE', 'CR PAYMENT', 'GIFT', 'SALARY']):
            return 'Income'
        
        # Direct debits
        if desc_upper.startswith('DD'):
            if 'HSBC' in desc_upper and 'LOAN' in desc_upper:
                return 'Financial Services'
            elif 'EE' in desc_upper or 'LIMITED' in desc_upper:
                return 'Bills & Utilities'
            else:
                return 'Bills & Utilities'
        
        # Shopping
        if desc_upper.startswith('VIS') or any(store in desc_upper for store in ['SAINSBURY', 'TESCO', 'ASDA']):
            if any(grocery in desc_upper for grocery in ['SAINSBURY', 'TESCO', 'ASDA']):
                return 'Groceries'
            else:
                return 'Shopping'
        
        return 'Other'
    
    def process_pdf_batch(self, pdf_files_data):
        """Process multiple PDFs"""
        print(f"\n{'='*60}")
        print(f"ZivilePDFProcessor: Starting batch processing")
        print(f"Number of PDFs to process: {len(pdf_files_data)}")
        print(f"{'='*60}")
        
        all_transactions = []
        transaction_id = 1
        
        for i, pdf_data in enumerate(pdf_files_data):
            try:
                print(f"\n--- Processing PDF {i+1}/{len(pdf_files_data)} ---")
                print(f"Filename: {pdf_data.get('filename', 'Unknown')}")
                
                pdf_content = base64.b64decode(pdf_data['content'])
                month_name = pdf_data['month']
                source = pdf_data.get('source', 'Current Account')
                
                print(f"Month: {month_name}")
                print(f"Source: {source}")
                print(f"PDF size: {len(pdf_content)} bytes")
                
                text = self.extract_text_from_pdf(pdf_content)
                
                if text:
                    print(f"Text extraction successful: {len(text)} characters")
                    transactions = self.parse_transactions(text, month_name, source)
                    print(f"Transactions parsed: {len(transactions)}")
                    
                    # Add IDs and extend list
                    for trans in transactions:
                        trans['id'] = transaction_id
                        transaction_id += 1
                        # Debug first transaction
                        if transaction_id == 2:
                            print(f"Sample transaction: {trans}")
                    
                    all_transactions.extend(transactions)
                    print(f"Running total: {len(all_transactions)} transactions")
                else:
                    print(f"WARNING: No text extracted from PDF for {month_name}")
                    
            except Exception as e:
                print(f"ERROR processing PDF {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"Total transactions found: {len(all_transactions)}")
        print(f"{'='*60}\n")
        
        return all_transactions