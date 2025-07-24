"""
PayPal Statement PDF Processor
Handles PayPal monthly statement format with multi-currency support
"""

import re
from datetime import datetime
from typing import List, Dict, Any
import base64
from io import BytesIO

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

import PyPDF2


class PayPalStatementProcessor:
    def __init__(self):
        self.currency_symbols = {
            'GBP': '£',
            'USD': '$',
            'EUR': '€'
        }
    
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
            
            return all_text, tables_data
            
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return None, []
    
    def parse_paypal_transactions(self, text: str, tables_data: List[Dict], month_name: str) -> List[Dict[str, Any]]:
        """Parse PayPal statement transactions"""
        transactions = []
        
        # PayPal specific patterns
        patterns = [
            # Date | Description with ID | Name/Email | Gross | Fee | Net
            (r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([A-Z0-9]{17})\s+(.+?)\s+([-]?[\d,]+\.\d{2})\s+([-]?[\d,]+\.\d{2})\s+([-]?[\d,]+\.\d{2})', 'full_detail'),
            # Compact format without fees
            (r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-]?[\d,]+\.\d{2})\s+(\w{3})', 'compact'),
            # Transaction with ID inline
            (r'(\d{2}/\d{2}/\d{4})\s+([^0-9]+)\s+([A-Z0-9]{17})\s+(.+)', 'with_id'),
        ]
        
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and headers
            if not line or any(skip in line.upper() for skip in [
                'DATE', 'DESCRIPTION', 'GROSS', 'FEE', 'NET', 
                'BALANCE', 'ACTIVITY SUMMARY', 'STATEMENT FOR'
            ]):
                i += 1
                continue
            
            # Check if this is a date line (start of transaction)
            date_match = re.match(r'^(\d{2}/\d{2}/\d{4})', line)
            if date_match:
                transaction_data = {
                    'date': date_match.group(1),
                    'lines': [line]
                }
                
                # Collect following lines that belong to this transaction
                j = i + 1
                while j < len(lines) and not re.match(r'^\d{2}/\d{2}/\d{4}', lines[j]):
                    if lines[j].strip():
                        transaction_data['lines'].append(lines[j].strip())
                    j += 1
                
                # Parse the collected lines
                parsed = self._parse_transaction_lines(transaction_data, month_name)
                if parsed:
                    transactions.append(parsed)
                
                i = j
            else:
                i += 1
        
        # Also process tables if available
        if tables_data:
            table_transactions = self._parse_tables(tables_data, month_name)
            transactions.extend(table_transactions)
        
        # Remove duplicates based on transaction ID
        seen_ids = set()
        unique_transactions = []
        for trans in transactions:
            trans_id = trans.get('paypal_id', '')
            if trans_id and trans_id not in seen_ids:
                seen_ids.add(trans_id)
                unique_transactions.append(trans)
            elif not trans_id:
                unique_transactions.append(trans)
        
        return unique_transactions
    
    def _parse_transaction_lines(self, transaction_data: Dict, month_name: str) -> Dict[str, Any]:
        """Parse multi-line transaction data"""
        lines = transaction_data['lines']
        full_text = ' '.join(lines)
        
        # Extract date
        date_str = transaction_data['date']
        
        # Extract transaction ID (PayPal format: 17 alphanumeric characters)
        id_match = re.search(r'([A-Z0-9]{17}[A-Z0-9]*)', full_text)
        paypal_id = id_match.group(1) if id_match else None
        
        # Extract amount (look for patterns like -11.99 or 11.99)
        amount_matches = re.findall(r'([-]?[\d,]+\.\d{2})', full_text)
        if not amount_matches:
            return None
        
        # For PayPal, the last amount is usually the net amount
        amount = float(amount_matches[-1].replace(',', ''))
        
        # Extract description and merchant info
        description_parts = []
        merchant_name = None
        merchant_email = None
        
        for line in lines:
            # Skip lines with just amounts or IDs
            if re.match(r'^[-]?[\d,]+\.\d{2}$', line) or re.match(r'^[A-Z0-9]{17}$', line):
                continue
            
            # Check for email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line)
            if email_match:
                merchant_email = email_match.group(0)
                # Remove email from line to get merchant name
                merchant_name = line.replace(merchant_email, '').strip()
            elif not re.search(r'\d{2}/\d{2}/\d{4}', line):  # Not a date line
                description_parts.append(line)
        
        # Build description
        description = ' '.join(description_parts).strip()
        
        # Remove ID prefix if it exists
        description = re.sub(r'^ID:\s*[A-Z0-9]{17,}\s*', '', description).strip()
        
        # Determine transaction type
        transaction_type = self._determine_transaction_type(description, full_text)
        
        # If we have merchant info, add it to description
        if merchant_name and merchant_name not in description:
            description = f"{description} - {merchant_name}"
        
        return {
            'date': self._parse_date(date_str),
            'description': description[:200],  # Limit length
            'amount': amount,
            'category': self._categorize_paypal_transaction(description, transaction_type),
            'month': month_name,
            'source': 'PayPal',
            'paypal_id': paypal_id,
            'merchant_name': merchant_name,
            'merchant_email': merchant_email,
            'transaction_type': transaction_type
        }
    
    def _parse_tables(self, tables_data: List[Dict], month_name: str) -> List[Dict[str, Any]]:
        """Parse transactions from extracted tables"""
        transactions = []
        
        for table_info in tables_data:
            table = table_info['data']
            
            # Skip if table is too small
            if len(table) < 2:
                continue
            
            # Try to identify header row
            header_idx = None
            for idx, row in enumerate(table):
                if any(cell and 'Date' in str(cell) for cell in row):
                    header_idx = idx
                    break
            
            if header_idx is None:
                continue
            
            # Process rows after header
            for row in table[header_idx + 1:]:
                if not row or len(row) < 3:
                    continue
                
                # Look for date in first few columns
                date_str = None
                for cell in row[:3]:
                    if cell and re.match(r'\d{2}/\d{2}/\d{4}', str(cell)):
                        date_str = str(cell)
                        break
                
                if not date_str:
                    continue
                
                # Extract other fields
                row_text = ' '.join([str(cell) if cell else '' for cell in row])
                
                # Look for amount
                amount_match = re.search(r'([-]?[\d,]+\.\d{2})', row_text)
                if not amount_match:
                    continue
                
                amount = float(amount_match.group(1).replace(',', ''))
                
                # Extract description (remove date and amount from text)
                description = row_text.replace(date_str, '').replace(amount_match.group(1), '').strip()
                
                transaction = {
                    'date': self._parse_date(date_str),
                    'description': description[:200],
                    'amount': amount,
                    'category': self._categorize_paypal_transaction(description, ''),
                    'month': month_name,
                    'source': 'PayPal'
                }
                
                transactions.append(transaction)
        
        return transactions
    
    def _determine_transaction_type(self, description: str, full_text: str) -> str:
        """Determine PayPal transaction type"""
        desc_upper = description.upper()
        text_upper = full_text.upper()
        
        # Check both description and full text for type indicators
        combined_text = desc_upper + ' ' + text_upper
        
        if 'PRE-APPROVED PAYMENT' in combined_text or 'BILL USER PAYMENT' in combined_text:
            return 'Subscription'
        elif 'BANK DEPOSIT' in combined_text or 'PP ACCOUNT' in combined_text:
            return 'Bank Transfer'
        elif 'CURRENCY CONVERSION' in combined_text or 'GENERAL CURRENCY' in combined_text:
            return 'Currency Exchange'
        elif 'PAYMENT RECEIVED' in combined_text:
            return 'Income'
        elif 'REFUND' in combined_text:
            return 'Refund'
        elif 'WITHDRAWAL' in combined_text:
            return 'Withdrawal'
        elif 'TRANSFER' in combined_text:
            return 'Transfer'
        else:
            return 'Payment'
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date from DD/MM/YYYY format"""
        try:
            date_obj = datetime.strptime(date_str.strip(), '%d/%m/%Y')
            return date_obj.strftime('%Y-%m-%d')
        except:
            # Fallback to current year
            return f"{datetime.now().year}-01-01"
    
    def _categorize_paypal_transaction(self, description: str, transaction_type: str) -> str:
        """Categorize PayPal transactions"""
        desc_upper = description.upper()
        
        # Transaction type based categories
        if transaction_type == 'Bank Transfer':
            return 'Transfers'
        elif transaction_type == 'Currency Exchange':
            return 'Financial Services'
        elif transaction_type == 'Income':
            return 'Income'
        elif transaction_type == 'Refund':
            return 'Refunds'
        
        # Description based categories
        categories = {
            'Subscriptions': [
                'SPOTIFY', 'NETFLIX', 'AMAZON PRIME', 'DISNEY', 'APPLE', 
                'GOOGLE', 'MICROSOFT', 'ADOBE', 'YOUTUBE', 'HULU',
                'PRE-APPROVED', 'SUBSCRIPTION', 'MONTHLY', 'RECURRING',
                'CAPCUT', 'CANVA', 'DROPBOX', 'ICLOUD'
            ],
            'Web Services': [
                'GODADDY', 'GO DADDY', 'NAMECHEAP', 'DOMAIN', 'HOSTING', 'AWS', 
                'DIGITAL OCEAN', 'CLOUDFLARE', 'WEB ', 'SERVER', 'SQUARESPACE',
                'WIX', 'WORDPRESS', 'BLUEHOST', 'HOSTGATOR'
            ],
            'Shopping': [
                'AMAZON', 'EBAY', 'ETSY', 'ALIEXPRESS', 'SHOP', 
                'STORE', 'MARKET', 'RETAIL', 'WALMART', 'TARGET'
            ],
            'Food & Delivery': [
                'DELIVEROO', 'UBER EAT', 'JUST EAT', 'GRUBHUB', 
                'DOORDASH', 'FOOD', 'RESTAURANT', 'PIZZA', 'BURGER'
            ],
            'Gaming': [
                'STEAM', 'EPIC GAMES', 'PLAYSTATION', 'XBOX', 
                'NINTENDO', 'GAME', 'GAMING', 'TWITCH', 'DISCORD'
            ],
            'Software': [
                'LICENSE', 'SOFTWARE', 'APP', 'TOOL', 'PLUGIN',
                'PIPO', 'JETBRAINS', 'GITHUB', 'GITLAB'
            ],
            'Financial Services': [
                'PAYPAL', 'FEE', 'CHARGE', 'BANK', 'TRANSFER',
                'CURRENCY CONVERSION', 'EXCHANGE'
            ],
            'Entertainment': [
                'PATREON', 'ONLYFANS', 'TWITCH', 'YOUTUBE PREMIUM',
                'CRUNCHYROLL', 'FUNIMATION'
            ]
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in desc_upper:
                    return category
        
        return 'Other'
    
    def process_pdf_batch(self, pdf_files_data: List[Dict]) -> List[Dict[str, Any]]:
        """Process multiple PayPal PDF statements"""
        all_transactions = []
        transaction_id = 1
        
        for i, pdf_data in enumerate(pdf_files_data):
            try:
                pdf_content = base64.b64decode(pdf_data['content'])
                month_name = pdf_data['month']
                
                print(f"\nProcessing PayPal PDF {i+1} for {month_name}")
                
                text, tables_data = self.extract_text_from_pdf(pdf_content)
                
                if text:
                    transactions = self.parse_paypal_transactions(text, tables_data, month_name)
                    
                    # Add unique IDs
                    for trans in transactions:
                        trans['id'] = transaction_id
                        transaction_id += 1
                    
                    all_transactions.extend(transactions)
                    print(f"Found {len(transactions)} transactions in {month_name}")
                else:
                    print(f"No text extracted from PayPal PDF for {month_name}")
                    
            except Exception as e:
                print(f"Error processing PayPal PDF {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\nTotal PayPal transactions found: {len(all_transactions)}")
        return all_transactions