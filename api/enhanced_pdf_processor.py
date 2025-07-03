"""
Enhanced PDF processor for bank statements with table extraction
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

class EnhancedPDFProcessor:
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    def extract_text_from_pdf(self, pdf_content):
        """Extract text from PDF with enhanced table support"""
        try:
            pdf_file = BytesIO(pdf_content)
            all_text = ""
            tables_data = []
            
            # Try pdfplumber first for better table extraction
            if HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(pdf_file) as pdf:
                        for page_num, page in enumerate(pdf.pages):
                            # Extract text
                            page_text = page.extract_text()
                            if page_text:
                                all_text += page_text + "\n"
                            
                            # Extract tables
                            tables = page.extract_tables()
                            for table in tables:
                                if table and len(table) > 1:
                                    tables_data.append({
                                        'page': page_num + 1,
                                        'data': table
                                    })
                    
                    print(f"pdfplumber extracted {len(all_text)} characters and {len(tables_data)} tables")
                    
                    # If we found tables, process them
                    if tables_data:
                        return self.process_tables(tables_data, all_text)
                        
                except Exception as e:
                    print(f"pdfplumber error: {e}")
            
            # Fallback to PyPDF2
            if not all_text:
                pdf_file.seek(0)
                try:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page in pdf_reader.pages:
                        try:
                            all_text += page.extract_text() + "\n"
                        except:
                            continue
                except Exception as e:
                    print(f"PyPDF2 error: {e}")
            
            return all_text
            
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return None
    
    def process_tables(self, tables_data, raw_text):
        """Process extracted tables to find transactions"""
        processed_text = raw_text
        
        for table_info in tables_data:
            table = table_info['data']
            
            # Look for transaction-like tables
            for row in table:
                if not row or len(row) < 3:
                    continue
                
                # Skip header rows
                if any(cell and ('DATE' in str(cell).upper() or 'DESCRIPTION' in str(cell).upper()) for cell in row):
                    continue
                
                # Try to identify transaction rows
                # Common patterns: Date | Type | Description | Amount
                # or: Date | Description | Amount | Balance
                row_text = " ".join([str(cell) if cell else "" for cell in row])
                
                # Add structured row to text for better parsing
                if re.search(r'\d+\.\d{2}', row_text):  # Has amount
                    processed_text += "\n" + row_text
        
        return processed_text
    
    def parse_transactions(self, text, month_name, source='Current Account'):
        """Parse transactions with enhanced pattern matching"""
        if not text:
            return []
        
        transactions = []
        lines = text.split('\n')
        
        # Enhanced patterns for HSBC current account
        patterns = [
            # Table row format: Date Type Description Amount Balance
            (r'(\d{2}\s+\w{3}\s+\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*([D]?)$', 'table_with_balance'),
            # Without balance
            (r'(\d{2}\s+\w{3}\s+\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})\s*([D]?)$', 'table_no_balance'),
            # Compact format
            (r'(\d{2}[A-Za-z]{3}\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})', 'compact'),
            # Standard formats
            (r'(\d{1,2}\s+\w{3}\s+\d{2})\s+(.+?)\s+([\d,]+\.\d{2})', 'standard'),
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip known non-transaction lines
            skip_patterns = [
                'BALANCE', 'STATEMENT', 'PAGE', 'SHEET', 'TOTAL',
                'YOUR HSBC', 'PAYMENT TYPE', 'DATE', 'DESCRIPTION',
                'PO BOX', 'GUILDFORD', 'ACCOUNT SUMMARY'
            ]
            if any(skip in line.upper() for skip in skip_patterns):
                continue
            
            for pattern_regex, pattern_type in patterns:
                match = re.search(pattern_regex, line)
                if match:
                    try:
                        if pattern_type == 'table_with_balance':
                            date_str = match.group(1)
                            type_code = match.group(2)
                            description = match.group(3).strip()
                            amount_str = match.group(4)
                            balance_str = match.group(5)
                            debit_flag = match.group(6)
                        elif pattern_type == 'table_no_balance':
                            date_str = match.group(1)
                            type_code = match.group(2)
                            description = match.group(3).strip()
                            amount_str = match.group(4)
                            debit_flag = match.group(5) if len(match.groups()) > 4 else 'D'
                        else:
                            date_str = match.group(1)
                            description = match.group(2).strip()
                            amount_str = match.group(3)
                            type_code = ""
                            debit_flag = 'D'
                        
                        # Clean up description
                        if type_code and type_code not in description:
                            description = f"{type_code} {description}"
                        
                        # Parse date
                        formatted_date = self.parse_date(date_str)
                        
                        # Parse amount
                        amount = float(amount_str.replace(',', ''))
                        
                        # Determine debit/credit
                        if debit_flag == 'D' or (source == 'Current Account' and debit_flag != 'C'):
                            amount = -abs(amount)
                        elif debit_flag == 'C' or 'CREDIT' in line.upper():
                            amount = abs(amount)
                        
                        # Categorize
                        category = self.categorize_transaction(description)
                        if category is None:
                            continue
                        
                        transaction = {
                            'date': formatted_date,
                            'description': description[:100],
                            'amount': amount,
                            'category': category,
                            'month': month_name,
                            'source': source
                        }
                        
                        transactions.append(transaction)
                        break
                        
                    except Exception as e:
                        print(f"Error parsing line: {line[:50]}... - {e}")
                        continue
        
        print(f"Parsed {len(transactions)} transactions from {month_name}")
        return transactions
    
    def parse_date(self, date_str):
        """Parse various date formats"""
        date_formats = [
            "%d %b %y", "%d %b %Y", "%d/%m/%Y", "%d-%m-%Y",
            "%d/%m/%y", "%d-%m-%y", "%d %b", "%Y-%m-%d",
            "%d%b%y", "%d%b%Y", "%d%b %y", "%d%b %Y"
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                if fmt in ["%d %b", "%d/%m", "%d-%m"]:
                    date_obj = date_obj.replace(year=2024)
                return date_obj.strftime("%Y-%m-%d")
            except:
                continue
        
        # Fallback
        return f"2024-01-01"
    
    def categorize_transaction(self, description):
        """Enhanced categorization"""
        desc_upper = description.upper()
        
        # Skip balance entries
        if any(skip in desc_upper for skip in ['BALANCE', 'BROUGHT FORWARD', 'CARRIED FORWARD']):
            return None
        
        # Enhanced mappings for HSBC current account
        categories = {
            'Income': ['PAYSTREAM', 'SALARY', 'WAGE', 'PAYMENT RECEIVED', 'CR PAYMENT', 'CRPAYSTREAM'],
            'Financial Services': ['ATM', 'CASH', 'HSBC', 'BANK', 'FEE', 'CHARGE'],
            'Transport': ['TFL', 'RAIL', 'UBER', 'TAXI', 'TRANSPORT', 'TRAIN'],
            'Groceries': ['TESCO', 'SAINSBURY', 'ASDA', 'WAITROSE', 'CO-OP'],
            'Bills & Utilities': ['DD', 'DIRECT DEBIT', 'COUNCIL', 'ELECTRIC', 'GAS', 'WATER'],
            'Shopping': ['AMAZON', 'EBAY', 'SHOP', 'STORE'],
            'Subscriptions': ['SUBSCRIPTION', 'MEMBERSHIP', 'MONTHLY'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in desc_upper:
                    return category
        
        # Check for specific codes
        if desc_upper.startswith('ATM'):
            return 'Financial Services'
        if desc_upper.startswith('DD'):
            return 'Bills & Utilities'
        if desc_upper.startswith('CR'):
            return 'Income'
        if desc_upper.startswith('BP') or desc_upper.startswith('VIS'):
            return 'Shopping'
        
        return 'Other'
    
    def process_pdf_batch(self, pdf_files_data):
        """Process multiple PDFs efficiently"""
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
                continue
        
        print(f"\nTotal transactions found: {len(all_transactions)}")
        return all_transactions