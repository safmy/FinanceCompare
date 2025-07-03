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
                    # Parse the extracted data
                    trans = self.create_transaction(date_str, transaction_data, month_name, source)
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
        result = {
            'type_code': None,
            'description': [],
            'amount': None,
            'balance': None,
            'lines_consumed': 1
        }
        
        # First line has the date
        first_line = lines[start_idx].strip()
        
        # Check if there's more on the same line after the date
        date_pattern = r'^(\d{2}\s+\w{3}\s+\d{2})\s+'
        remaining = re.sub(date_pattern, '', first_line).strip()
        
        if remaining:
            # Parse what's left on the date line
            parts = remaining.split()
            if parts and parts[0] in ['VIS', 'DD', 'CR', 'ATM', 'BP', 'SO']:
                result['type_code'] = parts[0]
                if len(parts) > 1:
                    result['description'].append(' '.join(parts[1:]))
        
        # Look at following lines for continuation
        idx = start_idx + 1
        while idx < len(lines):
            line = lines[idx].strip()
            
            if not line:
                idx += 1
                continue
            
            # Check if this is a new date line (next transaction)
            if re.match(r'^\d{2}\s+\w{3}\s+\d{2}', line):
                break
            
            # Check for continuation markers
            if line.startswith(')))'):
                # Extract description after markers
                desc = line[3:].strip()
                if desc:
                    result['description'].append(desc)
            elif re.match(r'^[A-Z]{2,3}\s+', line):
                # Line starting with type code
                parts = line.split(None, 1)
                if not result['type_code']:
                    result['type_code'] = parts[0]
                if len(parts) > 1:
                    result['description'].append(parts[1])
            elif re.match(r'^[\d,]+\.\d{2}$', line):
                # Just an amount
                if not result['amount']:
                    result['amount'] = line
                else:
                    result['balance'] = line
            elif re.match(r'^.+?\s+[\d,]+\.\d{2}$', line):
                # Description with amount at end
                match = re.match(r'^(.+?)\s+([\d,]+\.\d{2})$', line)
                if match:
                    result['description'].append(match.group(1).strip())
                    if not result['amount']:
                        result['amount'] = match.group(2)
            else:
                # Continuation of description
                result['description'].append(line)
            
            idx += 1
        
        result['lines_consumed'] = idx - start_idx
        
        # Only return if we found an amount
        return result if result['amount'] else None
    
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
                    
                    for trans in transactions:
                        trans['id'] = transaction_id
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