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
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                all_text += text + "\n"
            
            print(f"PyPDF2 extracted {len(all_text)} characters")
            return all_text
            
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
        # Example: "11 Dec 24  10 Dec 24  ))) CAFFE NERO WINDSOR PEA WINDSOR  3.60"
        patterns = [
            # With ))) markers
            r'(\d{1,2}\s+\w{3}\s+\d{2})\s+\d{1,2}\s+\w{3}\s+\d{2}\s+\)+\s*([^£\d]+?)\s+([\d,]+\.\d{2})(?:\s*CR)?',
            # Without ))) markers
            r'(\d{1,2}\s+\w{3}\s+\d{2})\s+\d{1,2}\s+\w{3}\s+\d{2}\s+([^£\d]+?)\s+([\d,]+\.\d{2})(?:\s*CR)?',
            # Alternative format with amount at different position
            r'(\d{1,2}\s+\w{3}\s+\d{2})\s+(.+?)\s+£?([\d,]+\.\d{2})(?:\s*CR)?$'
        ]
        
        transaction_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip headers and footers
            if any(skip in line.upper() for skip in ['BALANCE', 'STATEMENT', 'PAGE', 'TOTAL SPENT', 'TRANSACTIONS']):
                continue
            
            matched = False
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        date_str = match.group(1)  # e.g., "11 Dec 24"
                        description = match.group(2).strip()
                        amount_str = match.group(3)
                        
                        # Parse date
                        try:
                            date_obj = datetime.strptime(date_str, "%d %b %y")
                            formatted_date = date_obj.strftime("%Y-%m-%d")
                        except:
                            # Try alternative format
                            try:
                                date_obj = datetime.strptime(date_str, "%d %b %Y")
                                formatted_date = date_obj.strftime("%Y-%m-%d")
                            except:
                                formatted_date = f"2024-{transaction_count:02d}-01"  # Fallback
                        
                        # Parse amount
                        amount = float(amount_str.replace(',', ''))
                        
                        # Check if it's a credit (positive) or debit (negative)
                        if 'CR' in line:
                            amount = abs(amount)  # Credit
                        else:
                            amount = -abs(amount)  # Debit
                        
                        # Clean description - remove extra spaces and location info
                        description = re.sub(r'\s+', ' ', description)
                        # Extract main merchant name (before location/reference)
                        desc_parts = description.split('  ')
                        if len(desc_parts) > 0:
                            description = desc_parts[0]
                        
                        transaction = {
                            'date': formatted_date,
                            'description': description[:100],  # Limit length
                            'amount': amount,
                            'category': self.categorize_transaction(description),
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
        
        # Category mappings based on your screenshots
        categories = {
            'Coffee Shops': ['CAFFE NERO', 'STARBUCKS', 'COSTA', 'PRET A MANGER', 'COFFEE'],
            'Transport': ['TFL', 'RAIL', 'UBER', 'TAXI', 'TRANSPORT', 'TRAIN'],
            'Groceries': ['TESCO', 'SAINSBURY', 'ASDA', 'WAITROSE', 'CO-OP', 'M&S FOOD', 'LIDL', 'ALDI'],
            'Fast Food': ['MCDONALD', 'KFC', 'BURGER', 'SUBWAY', 'GREGGS'],
            'Food Delivery': ['DELIVEROO', 'JUST EAT', 'UBER EAT', 'FOODHUB'],
            'Restaurants': ['RESTAURANT', 'NANDO', 'WAGAMAMA', 'PIZZA', 'DINING', 'GRILL'],
            'Shopping': ['AMAZON', 'EBAY', 'ASOS', 'NEXT', 'PRIMARK', 'ZARA'],
            'Entertainment': ['CINEMA', 'NETFLIX', 'SPOTIFY', 'DISNEY'],
            'Parking': ['PARKING', 'NCP', 'CAR PARK'],
            'Fuel': ['SHELL', 'BP', 'ESSO', 'PETROL', 'FUEL'],
            'Bills': ['COUNCIL TAX', 'ELECTRIC', 'GAS', 'WATER', 'INSURANCE'],
            'Rent': ['RENT'],
            'Subscriptions': ['SUBSCRIPTION', 'MEMBERSHIP'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in desc_upper:
                    return category
        
        # Special cases
        if 'PAYMENT' in desc_upper and 'THANK YOU' in desc_upper:
            return 'Payments'
        
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
                
                print(f"\nProcessing PDF {i+1} for {month_name}")
                
                # Extract text using PyPDF2
                text = self.extract_text_from_pdf(pdf_content)
                
                if text:
                    # Parse transactions
                    transactions = self.parse_transactions(text, month_name)
                    
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