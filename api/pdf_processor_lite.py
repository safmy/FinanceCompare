"""
Lightweight PDF processor for limited memory environments
"""

import os
import base64
import re
from datetime import datetime
from google.cloud import documentai_v1beta3 as documentai
from google.oauth2 import service_account
import json
import gc  # Garbage collection

class PDFProcessorLite:
    def __init__(self):
        # Initialize Google Document AI client only
        creds_json = os.environ.get('GOOGLE_CLOUD_CREDENTIALS')
        
        if creds_json:
            credentials_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            self.documentai_client = documentai.DocumentProcessorServiceClient(credentials=credentials)
        else:
            self.documentai_client = documentai.DocumentProcessorServiceClient()
        
        # Document AI configuration
        self.project_id = '693097981002'
        self.location = 'us'
        self.processor_id = 'f62c14e46f0365a9'
    
    def extract_text_from_pdf(self, pdf_content):
        """Extract text using Document AI with minimal memory usage"""
        try:
            # Process with Document AI
            name = f'projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}'
            
            # Create raw document
            raw_document = documentai.RawDocument(
                content=pdf_content, 
                mime_type='application/pdf'
            )
            
            # Create request
            request = documentai.ProcessRequest(
                name=name, 
                raw_document=raw_document
            )
            
            # Process the document
            result = self.documentai_client.process_document(request=request)
            text = result.document.text
            
            # Clean up memory
            del result
            del request
            del raw_document
            gc.collect()
            
            print(f"Document AI extracted {len(text) if text else 0} characters")
            return text
            
        except Exception as e:
            print(f"Error in Document AI: {e}")
            return None
    
    def parse_transactions(self, text, month_name, source='Credit Card'):
        """Parse transactions from text - optimized for bank statements"""
        if not text:
            return []
            
        transactions = []
        
        # Split into lines and process one at a time
        lines = text.split('\n')
        
        # Bank statement patterns
        patterns = [
            # Your statement format: DD Mon YY  DD Mon YY  ))) DESCRIPTION  AMOUNT
            r'(\d{1,2}\s+\w{3}\s+\d{2})\s+\d{1,2}\s+\w{3}\s+\d{2}\s+\)+\s*(.+?)\s+([\d,]+\.\d{2})(?:\s*CR)?',
            # Without )))
            r'(\d{1,2}\s+\w{3}\s+\d{2})\s+\d{1,2}\s+\w{3}\s+\d{2}\s+(.+?)\s+([\d,]+\.\d{2})(?:\s*CR)?',
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        date_str = match.group(1)
                        description = match.group(2).strip()
                        amount = float(match.group(3).replace(',', ''))
                        
                        # Parse date
                        try:
                            date_obj = datetime.strptime(date_str, "%d %b %y")
                            formatted_date = date_obj.strftime("%Y-%m-%d")
                        except:
                            formatted_date = date_str
                        
                        # Check if credit
                        if 'CR' in line[match.end():match.end()+5]:
                            amount = amount
                        else:
                            amount = -amount
                        
                        # Clean description
                        desc_parts = description.split('  ')
                        clean_desc = desc_parts[0].strip()
                        
                        transaction = {
                            'date': formatted_date,
                            'description': clean_desc,
                            'amount': amount,
                            'category': self.categorize_transaction(clean_desc),
                            'month': month_name,
                            'source': source
                        }
                        
                        transactions.append(transaction)
                        break
                        
                    except Exception as e:
                        continue
        
        return transactions
    
    def categorize_transaction(self, description):
        """Simple categorization"""
        desc_upper = description.upper()
        
        # Minimal categories to save memory
        if any(word in desc_upper for word in ['CAFFE NERO', 'STARBUCKS', 'COSTA', 'COFFEE']):
            return 'Coffee Shops'
        elif any(word in desc_upper for word in ['TFL', 'RAIL', 'UBER', 'TRANSPORT']):
            return 'Transport'
        elif any(word in desc_upper for word in ['TESCO', 'SAINSBURY', 'ASDA', 'WAITROSE']):
            return 'Groceries'
        elif any(word in desc_upper for word in ['MCDONALD', 'KFC', 'BURGER', 'SUBWAY']):
            return 'Fast Food'
        elif any(word in desc_upper for word in ['DELIVEROO', 'JUST EAT', 'UBER EAT']):
            return 'Food Delivery'
        elif any(word in desc_upper for word in ['RESTAURANT', 'NANDO', 'WAGAMAMA', 'PIZZA']):
            return 'Restaurants'
        elif 'PAYMENT' in desc_upper or 'THANK YOU' in desc_upper:
            return 'Payments'
        else:
            return 'Other'
    
    def process_pdf_batch(self, pdf_files_data):
        """Process PDFs one at a time to save memory"""
        all_transactions = []
        transaction_id = 1
        
        for i, pdf_data in enumerate(pdf_files_data):
            try:
                pdf_content = base64.b64decode(pdf_data['content'])
                month_name = pdf_data['month']
                
                print(f"\nProcessing PDF {i+1} for {month_name}")
                
                # Extract text
                text = self.extract_text_from_pdf(pdf_content)
                
                # Clear PDF content from memory
                del pdf_content
                gc.collect()
                
                if text:
                    # Parse transactions
                    transactions = self.parse_transactions(text, month_name)
                    print(f"Found {len(transactions)} transactions in {month_name}")
                    
                    # Add IDs
                    for trans in transactions:
                        trans['id'] = transaction_id
                        transaction_id += 1
                    
                    all_transactions.extend(transactions)
                    
                    # Clear text from memory
                    del text
                    gc.collect()
                else:
                    print(f"No text extracted from PDF for {month_name}")
                    
            except Exception as e:
                print(f"Error processing PDF {i+1}: {e}")
                continue
        
        print(f"\nTotal transactions found: {len(all_transactions)}")
        return all_transactions