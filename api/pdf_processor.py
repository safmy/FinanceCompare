"""
PDF Processing API for extracting bank transactions using Google Vision API
"""

import os
import base64
import re
from datetime import datetime
from google.cloud import vision
from google.oauth2 import service_account
import json

class PDFProcessor:
    def __init__(self):
        # Initialize Google Vision client
        # You'll need to set GOOGLE_APPLICATION_CREDENTIALS env variable
        # or provide credentials directly
        self.vision_client = vision.ImageAnnotatorClient()
        
    def extract_text_from_pdf(self, pdf_content):
        """Extract text from PDF using Google Vision API"""
        try:
            # Convert PDF to image pages first (Google Vision works with images)
            # For now, we'll assume the PDF content is base64 encoded
            image = vision.Image(content=pdf_content)
            
            # Perform OCR
            response = self.vision_client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
                
            return response.full_text_annotation.text
            
        except Exception as e:
            print(f"Error in OCR: {e}")
            return None
    
    def parse_transactions(self, text, month_name):
        """Parse transactions from extracted text"""
        transactions = []
        
        # Common UK bank statement patterns
        patterns = [
            # Pattern: DD MMM DESCRIPTION AMOUNT
            r'(\d{1,2}\s+\w{3})\s+(.+?)\s+£?([\d,]+\.\d{2})',
            # Pattern: DD/MM/YYYY DESCRIPTION AMOUNT
            r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+£?([\d,]+\.\d{2})',
            # Pattern: DD MMM YY DESCRIPTION AMOUNT
            r'(\d{1,2}\s+\w{3}\s+\d{2})\s+(.+?)\s+£?([\d,]+\.\d{2})',
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            # Skip header/footer lines
            if any(skip in line.upper() for skip in ['BALANCE', 'STATEMENT', 'PAGE', 'TOTAL']):
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        amount = float(match.group(3).replace(',', ''))
                        
                        # Clean up description
                        description = re.sub(r'\s+', ' ', description)
                        description = re.sub(r'[*#]', '', description)
                        
                        # Determine if debit or credit
                        if 'CR' in line or any(credit in description.upper() for credit in ['PAYMENT', 'CREDIT', 'REFUND']):
                            amount = abs(amount)
                        else:
                            amount = -abs(amount)
                        
                        transaction = {
                            'date': self.parse_date(date_str),
                            'description': description,
                            'amount': amount,
                            'category': self.categorize_transaction(description),
                            'month': month_name
                        }
                        
                        transactions.append(transaction)
                        break
                        
                    except Exception as e:
                        continue
        
        return transactions
    
    def parse_date(self, date_str):
        """Parse various date formats"""
        date_formats = [
            '%d %b',      # 15 Jan
            '%d %b %y',   # 15 Jan 25
            '%d %b %Y',   # 15 Jan 2025
            '%d/%m/%Y',   # 15/01/2025
            '%d/%m/%y',   # 15/01/25
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                # If year is missing, use current year
                if date_obj.year == 1900:
                    date_obj = date_obj.replace(year=datetime.now().year)
                return date_obj.strftime('%Y-%m-%d')
            except:
                continue
        
        return date_str
    
    def categorize_transaction(self, description):
        """Categorize transaction based on description"""
        desc_upper = description.upper()
        
        categories = {
            'Groceries': ['TESCO', 'SAINSBURY', 'ASDA', 'WAITROSE', 'LIDL', 'ALDI', 'MORRISONS', 'CO-OP', 'M&S FOOD'],
            'Transport': ['TFL', 'UBER', 'RAIL', 'TRAIN', 'BUS', 'TUBE', 'OYSTER', 'TAXI', 'CITYMAPPER'],
            'Fast Food': ['MCDONALD', 'KFC', 'BURGER', 'SUBWAY', 'PIZZA', 'DOMINO', 'PAPA JOHN', 'FIVE GUYS', 'GREGGS'],
            'Coffee Shops': ['COSTA', 'STARBUCKS', 'PRET', 'NERO', 'COFFEE', 'CAFE', 'BREW'],
            'Food Delivery': ['DELIVEROO', 'JUST EAT', 'UBER EAT', 'FOODHUB', 'ZOMATO'],
            'Subscriptions': ['NETFLIX', 'SPOTIFY', 'AMAZON PRIME', 'DISNEY', 'APPLE', 'GOOGLE', 'MICROSOFT', 'ADOBE'],
            'Fuel': ['SHELL', 'BP', 'ESSO', 'TEXACO', 'PETROL', 'FUEL', 'MURCO', 'GULF'],
            'Parking': ['PARKING', 'NCP', 'RINGO', 'PARKINGPERMIT', 'CAR PARK'],
            'Restaurants': ['RESTAURANT', 'WAGAMAMA', 'NANDO', 'ZIZZI', 'PREZZO', 'GRILL', 'KITCHEN', 'DINING', 'BISTRO'],
            'Shopping': ['AMAZON', 'EBAY', 'ASOS', 'NEXT', 'H&M', 'ZARA', 'PRIMARK', 'JOHN LEWIS', 'ARGOS', 'BOOTS'],
            'Rent': ['RENT'],
            'Bills': ['COUNCIL TAX', 'ELECTRIC', 'GAS', 'WATER', 'BROADBAND', 'INSURANCE'],
            'Entertainment': ['CINEMA', 'ODEON', 'VUE', 'THEATRE', 'CONCERT', 'TICKET'],
            'Fitness': ['GYM', 'FITNESS', 'SPORT', 'PURE GYM', 'VIRGIN ACTIVE'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in desc_upper:
                    return category
        
        return 'Other'
    
    def process_pdf_batch(self, pdf_files_data):
        """Process multiple PDF files and return combined transactions"""
        all_transactions = []
        transaction_id = 1
        
        for pdf_data in pdf_files_data:
            pdf_content = pdf_data['content']  # Base64 encoded
            month_name = pdf_data['month']
            
            # Extract text using OCR
            text = self.extract_text_from_pdf(base64.b64decode(pdf_content))
            
            if text:
                # Parse transactions
                transactions = self.parse_transactions(text, month_name)
                
                # Add IDs
                for trans in transactions:
                    trans['id'] = transaction_id
                    transaction_id += 1
                
                all_transactions.extend(transactions)
        
        return all_transactions