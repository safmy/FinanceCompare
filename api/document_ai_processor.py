"""
Google Document AI processor for bank statements
This handles complex PDF layouts better than Vision API
"""

import os
import json
import base64
from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account

class DocumentAIProcessor:
    def __init__(self):
        # Initialize Document AI client
        creds_json = os.environ.get('GOOGLE_CLOUD_CREDENTIALS')
        
        if creds_json:
            credentials_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            self.client = documentai.DocumentProcessorServiceClient(credentials=credentials)
        else:
            self.client = documentai.DocumentProcessorServiceClient()
        
        # You'll need to create a processor in Google Cloud Console
        # and add these to your environment variables
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'your-project-id')
        self.location = os.environ.get('DOCUMENT_AI_LOCATION', 'us')  # or 'eu'
        self.processor_id = os.environ.get('DOCUMENT_AI_PROCESSOR_ID', 'your-processor-id')
        
    def process_document(self, pdf_content):
        """Process a PDF document using Document AI"""
        # The full resource name of the processor
        name = self.client.processor_path(self.project_id, self.location, self.processor_id)
        
        # Read the file into memory
        document = documentai.Document(content=pdf_content, mime_type="application/pdf")
        
        # Configure the process request
        request = documentai.ProcessRequest(name=name, raw_document=document)
        
        # Process the document
        result = self.client.process_document(request=request)
        document = result.document
        
        return document.text
    
    def extract_table_data(self, document):
        """Extract table data from Document AI response"""
        transactions = []
        
        # Document AI provides structured data for tables
        for page in document.pages:
            for table in page.tables:
                # Process each row in the table
                for row_idx, row in enumerate(table.body_rows):
                    if row_idx == 0:  # Skip header row
                        continue
                    
                    row_data = []
                    for cell in row.cells:
                        cell_text = self.get_text(cell.layout, document.text)
                        row_data.append(cell_text)
                    
                    # Parse the row data into a transaction
                    transaction = self.parse_table_row(row_data)
                    if transaction:
                        transactions.append(transaction)
        
        return transactions
    
    def get_text(self, layout, document_text):
        """Extract text from a layout element"""
        response = ""
        for segment in layout.text_anchor.text_segments:
            start_index = segment.start_index if hasattr(segment, 'start_index') else 0
            end_index = segment.end_index
            response += document_text[start_index:end_index]
        return response.strip()
    
    def parse_table_row(self, row_data):
        """Parse a table row into a transaction"""
        # This depends on your bank's table format
        # Adjust based on the column order in your statements
        if len(row_data) >= 3:
            try:
                return {
                    'date': row_data[0],
                    'description': row_data[1],
                    'amount': self.parse_amount(row_data[2]),
                    'category': self.categorize_transaction(row_data[1])
                }
            except:
                return None
        return None
    
    def parse_amount(self, amount_str):
        """Parse amount string to float"""
        # Remove currency symbols and convert
        amount_str = amount_str.replace('£', '').replace(',', '').strip()
        
        # Handle CR (credit) suffix
        if amount_str.endswith('CR'):
            amount_str = amount_str[:-2].strip()
            return float(amount_str)
        else:
            return -float(amount_str)
    
    def categorize_transaction(self, description):
        """Categorize based on description"""
        # Reuse the categorization logic from pdf_processor.py
        desc_upper = description.upper()
        
        categories = {
            'Groceries': ['TESCO', 'SAINSBURY', 'ASDA', 'WAITROSE', 'LIDL', 'ALDI', 'MORRISONS', 'CO-OP', 'M&S FOOD'],
            'Transport': ['TFL', 'UBER', 'RAIL', 'TRAIN', 'BUS', 'TUBE', 'OYSTER', 'TAXI'],
            'Fast Food': ['MCDONALD', 'KFC', 'BURGER', 'SUBWAY', 'PIZZA', 'DOMINO', 'PAPA JOHN', 'FIVE GUYS'],
            'Coffee Shops': ['COSTA', 'STARBUCKS', 'PRET', 'NERO', 'COFFEE', 'CAFE', 'CAFFE NERO'],
            'Food Delivery': ['DELIVEROO', 'JUST EAT', 'UBER EAT', 'FOODHUB'],
            'Subscriptions': ['NETFLIX', 'SPOTIFY', 'AMAZON PRIME', 'DISNEY', 'APPLE', 'GOOGLE'],
            'Fuel': ['SHELL', 'BP', 'ESSO', 'TEXACO', 'PETROL', 'FUEL'],
            'Parking': ['PARKING', 'NCP', 'RINGO'],
            'Restaurants': ['RESTAURANT', 'WAGAMAMA', 'NANDO', 'ZIZZI', 'PREZZO'],
            'Shopping': ['AMAZON', 'EBAY', 'ASOS', 'NEXT', 'H&M', 'ZARA', 'PRIMARK', 'JOHN LEWIS', 'ARGOS'],
            'Rent': ['RENT'],
            'Bills': ['COUNCIL TAX', 'ELECTRIC', 'GAS', 'WATER', 'BROADBAND', 'INSURANCE'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in desc_upper:
                    return category
        
        return 'Other'