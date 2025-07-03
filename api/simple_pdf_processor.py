"""
Simple PDF text extraction for bank statements
No heavy OCR needed - just extract text and parse it
"""

import os
import base64
import re
from datetime import datetime
import json
import PyPDF2
from io import BytesIO
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

class SimplePDFProcessor:
    def __init__(self):
        # We only need OpenAI for categorization if patterns don't match
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    def extract_text_from_pdf(self, pdf_content):
        """Extract text from PDF using PyPDF2 - lightweight and fast"""
        try:
            # Create a PDF reader object
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            all_text = ""
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    all_text += text + "\n"
                except Exception as page_error:
                    print(f"Warning: Error reading page {page_num + 1}: {page_error}")
                    continue
            
            print(f"PyPDF2 extracted {len(all_text)} characters")
            
            # If PyPDF2 fails to extract text, try alternative method
            if len(all_text.strip()) < 100:
                print("Minimal text extracted, trying alternative extraction...")
                
                # Try pdfplumber if available
                if HAS_PDFPLUMBER:
                    try:
                        print("Trying pdfplumber...")
                        pdf_file.seek(0)
                        with pdfplumber.open(pdf_file) as pdf:
                            plumber_text = ""
                            for page in pdf.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    plumber_text += page_text + "\n"
                            
                            if len(plumber_text) > len(all_text):
                                all_text = plumber_text
                                print(f"pdfplumber extracted {len(all_text)} characters")
                    except Exception as e:
                        print(f"pdfplumber failed: {e}")
                
                # Try PyPDF2 with different settings
                if len(all_text.strip()) < 100:
                    pdf_file.seek(0)
                    try:
                        pdf_reader = PyPDF2.PdfReader(pdf_file, strict=False)
                        all_text = ""
                        for page in pdf_reader.pages:
                            all_text += page.extract_text() + "\n"
                    except:
                        pass
            
            return all_text if all_text else None
            
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return None
    
    def parse_transactions(self, text, month_name, source='Credit Card'):
        """Parse transactions using regex patterns"""
        if not text:
            return []
        
        transactions = []
        lines = text.split('\n')
        
        # Pattern for your bank statement format
        # Different patterns for different bank statement formats
        patterns = [
            # Credit card format - PyPDF2 extracts dates without spaces: "11 Dec2409 Dec24"
            (r'(\d{1,2}\s+\w{3})(\d{2})(\d{2})\s+\w{3}\d{2}\s+\)+\s*([^£\d]+?)\s+([\d,]+\.\d{2})(?:\s*CR)?', 'credit_card_with_markers'),
            (r'(\d{1,2}\s+\w{3})(\d{2})(\d{2})\s+\w{3}\d{2}\s+([^£\d]+?)\s+([\d,]+\.\d{2})(?:\s*CR)?', 'credit_card_no_markers'),
            
            # Current account formats - common patterns
            (r'(\d{2}\s+\w{3}\s+\d{2})\s+(.+?)\s+£?([\d,]+\.\d{2})\s*(?:CR|DR)?', 'current_account_simple'),
            (r'(\d{2}\s+\w{3})\s+(.+?)\s+([\d,]+\.\d{2})\s*(?:CR|DR)?', 'current_account_no_year'),
            
            # More flexible patterns
            (r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+(.+?)\s+£?([\d,]+\.\d{2})', 'date_with_slashes'),
            (r'(\d{1,2}\s+\w{3}\s+\d{2,4})\s+(.+?)\s+£?([\d,]+\.\d{2})', 'standard_date_format'),
            
            # HSBC current account format from your screenshot
            (r'(\d{2}\s+\w{3}\s+\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})\s*(?:D)?', 'hsbc_current_format'),
            (r'([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})\s*(?:D)?', 'hsbc_current_no_date'),
            
            # Additional HSBC formats
            (r'(\d{2}[A-Za-z]{3}\d{2})\s+([A-Z]{2,3})\s+(.+?)\s+([\d,]+\.\d{2})', 'hsbc_compact_date'),
            (r'([A-Z]{2,3})\s+([A-Z\s]+)\s+([\d,]+\.\d{2})\s*([D]?)$', 'hsbc_type_first')
        ]
        
        transaction_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip headers, footers, and non-transaction entries
            skip_patterns = [
                'BALANCE BROUGHT', 'BALANCE CARRIED', 'STATEMENT', 'PAGE', 
                'TOTAL SPENT', 'TRANSACTIONS', 'SHEET NUMBER', 'YOUR HSBC',
                'PAYMENT TYPE', 'RECEIVED BY US', 'TRANSACTION DATE',
                'PO BOX', 'GUILDFORD'  # Skip address lines
            ]
            if any(skip in line.upper() for skip in skip_patterns):
                continue
            
            matched = False
            for pattern_regex, pattern_type in patterns:
                match = re.search(pattern_regex, line)
                if match:
                    try:
                        # Parse based on pattern type
                        if pattern_type.startswith('credit_card'):
                            # Credit card format: date_part, year1, year2, description, amount
                            date_part = match.group(1)  # e.g., "11 Dec"
                            year_str = match.group(2)   # e.g., "24" (from Dec24)
                            description = match.group(4).strip()
                            amount_str = match.group(5)
                            date_str = f"{date_part} {year_str}"  # "11 Dec 24"
                            
                        elif pattern_type == 'hsbc_current_format':
                            # HSBC current: date, type_code, description, amount
                            date_str = match.group(1)
                            type_code = match.group(2)  # ATM, DD, BP, etc.
                            description = f"{type_code} {match.group(3).strip()}"
                            amount_str = match.group(4)
                            
                        elif pattern_type == 'hsbc_current_no_date':
                            # HSBC current without date: type_code, description, amount
                            type_code = match.group(1)
                            description = f"{type_code} {match.group(2).strip()}"
                            amount_str = match.group(3)
                            # Use a default date or extract from context
                            date_str = f"01 {month_name[:3]} 24"
                            
                        elif pattern_type == 'hsbc_compact_date':
                            # HSBC compact date: 07Dec24 ATM DESCRIPTION 40.00
                            date_str = match.group(1)
                            type_code = match.group(2)
                            description = f"{type_code} {match.group(3).strip()}"
                            amount_str = match.group(4)
                            
                        elif pattern_type == 'hsbc_type_first':
                            # Type first format: ATM DESCRIPTION 40.00 D
                            type_code = match.group(1)
                            description = f"{type_code} {match.group(2).strip()}"
                            amount_str = match.group(3)
                            # Use default date
                            date_str = f"01 {month_name[:3]} 24"
                            
                        else:
                            # Generic formats
                            date_str = match.group(1)
                            description = match.group(2).strip()
                            amount_str = match.group(3)
                        
                        # Parse date with multiple format attempts
                        formatted_date = None
                        date_formats = [
                            "%d %b %y", "%d %b %Y", "%d/%m/%Y", "%d-%m-%Y",
                            "%d/%m/%y", "%d-%m-%y", "%d %b", "%Y-%m-%d",
                            "%d%b%y", "%d%b%Y"  # Compact formats like "07Dec24"
                        ]
                        
                        for fmt in date_formats:
                            try:
                                date_obj = datetime.strptime(date_str.strip(), fmt)
                                # If year is missing, use current year
                                if fmt in ["%d %b", "%d/%m", "%d-%m"]:
                                    date_obj = date_obj.replace(year=2024)
                                formatted_date = date_obj.strftime("%Y-%m-%d")
                                break
                            except:
                                continue
                        
                        if not formatted_date:
                            formatted_date = f"2024-{transaction_count:02d}-01"  # Fallback
                        
                        # Parse amount
                        amount = float(amount_str.replace(',', ''))
                        
                        # Check if it's a credit (positive) or debit (negative)
                        if 'CR' in line:
                            amount = abs(amount)  # Credit
                        elif 'D' in line[-5:] or source == 'Current Account':
                            amount = -abs(amount)  # Debit (D at end or current account default)
                        else:
                            amount = -abs(amount)  # Default to debit for expenses
                        
                        # Clean description - remove extra spaces and location info
                        description = re.sub(r'\s+', ' ', description)
                        # Extract main merchant name (before location/reference)
                        desc_parts = description.split('  ')
                        if len(desc_parts) > 0:
                            description = desc_parts[0]
                        
                        category = self.categorize_transaction(description)
                        
                        # Skip balance entries
                        if category is None:
                            continue
                            
                        transaction = {
                            'date': formatted_date,
                            'description': description[:100],  # Limit length
                            'amount': amount,
                            'category': category,
                            'month': month_name,
                            'source': source
                        }
                        
                        transactions.append(transaction)
                        transaction_count += 1
                        matched = True
                        break
                        
                    except Exception as e:
                        print(f"Error parsing line: {line[:50]}... - {e}")
                        continue
            
            if not matched and line and not line.startswith('-'):
                # Log unmatched lines that look like transactions
                if re.search(r'\d+\.\d{2}', line):
                    print(f"Unmatched potential transaction: {line[:80]}...")
        
        print(f"Parsed {len(transactions)} transactions from {month_name}")
        return transactions
    
    def categorize_transaction(self, description):
        """Categorize transaction based on merchant name"""
        desc_upper = description.upper()
        
        # Skip balance entries
        if any(skip in desc_upper for skip in ['BALANCE', 'BROUGHT FORWARD', 'CARRIED FORWARD']):
            return None  # Will be filtered out
        
        # More comprehensive category mappings
        categories = {
            'Income': ['PAYSTREAM', 'SALARY', 'WAGE', 'PAYMENT RECEIVED', 'TRANSFER IN'],
            'Coffee Shops': ['CAFFE NERO', 'STARBUCKS', 'COSTA', 'PRET A MANGER', 'COFFEE'],
            'Transport': ['TFL', 'RAIL', 'UBER', 'TAXI', 'TRANSPORT', 'TRAIN', 'SADKOVSKYTE'],
            'Groceries': ['TESCO', 'SAINSBURY', 'ASDA', 'WAITROSE', 'CO-OP', 'M&S FOOD', 'LIDL', 'ALDI', 'BUDGENS'],
            'Fast Food': ['MCDONALD', 'KFC', 'BURGER', 'SUBWAY', 'GREGGS', 'THUNDERBIRD FRIED'],
            'Food Delivery': ['DELIVEROO', 'JUST EAT', 'UBER EAT', 'FOODHUB', 'DOMINO'],
            'Restaurants': ['RESTAURANT', 'NANDO', 'WAGAMAMA', 'PIZZA', 'DINING', 'GRILL', 'DONER', 'DOLCE VITA', 'ITSU'],
            'Shopping': ['AMAZON', 'EBAY', 'ASOS', 'NEXT', 'PRIMARK', 'ZARA', 'IKEA', 'CLARKS'],
            'Entertainment': ['CINEMA', 'NETFLIX', 'SPOTIFY', 'DISNEY', 'PRIME VIDEO'],
            'Parking': ['PARKING', 'NCP', 'CAR PARK', 'RINGGO', 'SABA PARK'],
            'Fuel': ['SHELL', 'BP', 'ESSO', 'PETROL', 'FUEL', 'BP BESSBOROUGH'],
            'Bills & Utilities': ['COUNCIL TAX', 'ELECTRIC', 'GAS', 'WATER', 'INSURANCE', 'EDF ENERGY', 'BT GROUP'],
            'Rent': ['RENT'],
            'Subscriptions': ['SUBSCRIPTION', 'MEMBERSHIP', 'OPENAI', 'CLAUDE', 'ANTHROPIC', 'EVERYONE ACTIVE', 'GOOGLE CLOUD'],
            'Financial': ['PAYPAL', 'BANK TRANSFER', 'ATM', 'CASH'],
            'Healthcare': ['PHARMACY', 'DOCTOR', 'HOSPITAL', 'MEDICAL'],
            'Personal Care': ['BARBER', 'HAIR', 'BEAUTY', 'SPA'],
            'Charity': ['DONATION', 'CHARITY'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in desc_upper:
                    return category
        
        # Special cases
        if 'PAYMENT' in desc_upper and 'THANK YOU' in desc_upper:
            return 'Income'
        if 'CR' in desc_upper and 'PAYSTREAM' in desc_upper:
            return 'Income'
        if 'DD' in desc_upper:  # Direct Debit
            if 'PAYPAL' in desc_upper:
                return 'Financial'
            elif 'EVERYONE ACTIVE' in desc_upper:
                return 'Subscriptions'
        
        return 'Other'
    
    def process_pdf_batch(self, pdf_files_data):
        """Process multiple PDFs efficiently"""
        all_transactions = []
        transaction_id = 1
        
        for i, pdf_data in enumerate(pdf_files_data):
            try:
                # Decode base64 PDF content
                pdf_content = base64.b64decode(pdf_data['content'])
                month_name = pdf_data['month']
                
                # Determine source from filename or path
                source = pdf_data.get('source', 'Credit Card')
                if 'filename' in pdf_data:
                    filename = pdf_data['filename'].lower()
                    if 'current' in filename or 'checking' in filename:
                        source = 'Current Account'
                
                print(f"\nProcessing PDF {i+1} for {month_name} (Source: {source})")
                
                # Extract text using PyPDF2
                text = self.extract_text_from_pdf(pdf_content)
                
                if text:
                    # Parse transactions with source
                    transactions = self.parse_transactions(text, month_name, source)
                    
                    # Add sequential IDs
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