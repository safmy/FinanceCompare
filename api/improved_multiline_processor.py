"""
Improved Multi-line PDF processor that correctly handles Paid in/Paid out columns
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

# Import credit card processor
try:
    from .credit_card_processor import CreditCardProcessor
except ImportError:
    from credit_card_processor import CreditCardProcessor

class ImprovedMultilineProcessor:
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.credit_card_processor = CreditCardProcessor()
    
    def is_credit_card_statement(self, text):
        """Detect if the PDF is a credit card statement"""
        if not text:
            return False
        
        # First check for current account markers (to exclude)
        if 'Your HSBC Advance details' in text or 'Your Bank Account details' in text:
            return False
        
        # Check for credit card specific markers
        credit_card_markers = [
            'ReceivedByUsTransactionDateDetailsAmount',
            'ReceivedByUs TransactionDate Details',  # With spaces
            'ReceivedByUs',  # More specific marker
            'Your Visa Card',
            'Your Credit Card statement',
            'CreditLimit',
            'Credit Limit',
            'APR',
            'Minimumpayment',
            'Minimum payment'
        ]
        
        for marker in credit_card_markers:
            if marker in text:
                return True
        
        # Also check without spaces for better matching
        text_no_spaces = text.replace(' ', '')
        markers_no_spaces = ['YourTransactionDetails', 'CreditLimit', 'Minimumpayment']
        for marker in markers_no_spaces:
            if marker in text_no_spaces:
                return True
        
        return False
    
    def extract_text_from_pdf(self, pdf_content):
        """Extract text from PDF - try multiple methods"""
        print(f"\n--- Extracting text from PDF (size: {len(pdf_content)} bytes) ---")
        try:
            pdf_file = BytesIO(pdf_content)
            all_text = ""
            
            # Try pdfplumber first
            if HAS_PDFPLUMBER:
                print("Trying pdfplumber...")
                try:
                    with pdfplumber.open(pdf_file) as pdf:
                        for i, page in enumerate(pdf.pages):
                            try:
                                # Try with different extraction options
                                page_text = page.extract_text()
                                if not page_text:
                                    # Try with x_tolerance and y_tolerance
                                    page_text = page.extract_text(
                                        x_tolerance=3,
                                        y_tolerance=3
                                    )
                                if page_text:
                                    all_text += page_text + "\n"
                                    print(f"  Page {i+1}: extracted {len(page_text)} chars")
                            except Exception as page_e:
                                print(f"  Page {i+1} error: {page_e}")
                                continue
                    
                    if all_text:
                        print(f"pdfplumber SUCCESS: extracted {len(all_text)} characters")
                        print(f"First 200 chars: {all_text[:200]}")
                        return all_text
                    else:
                        print("pdfplumber extracted no text")
                except Exception as e:
                    print(f"pdfplumber ERROR: {e}")
                    # Reset file pointer for next attempt
                    pdf_file.seek(0)
            
            # Fallback to PyPDF2
            print("\nTrying PyPDF2...")
            pdf_file.seek(0)
            try:
                # Try with strict=False first
                try:
                    pdf_reader = PyPDF2.PdfReader(pdf_file, strict=False)
                except Exception as e:
                    print(f"PyPDF2 initial error (trying lenient mode): {e}")
                    pdf_file.seek(0)
                    # Try creating a new BytesIO from the content
                    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content), strict=False)
                
                print(f"PyPDF2: Found {len(pdf_reader.pages)} pages")
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            all_text += page_text + "\n"
                            print(f"  Page {i+1}: extracted {len(page_text)} chars")
                    except Exception as e:
                        print(f"  Error on page {i+1}: {e}")
                        # Try alternative extraction method
                        try:
                            if hasattr(page, 'extractText'):
                                page_text = page.extractText()
                                if page_text:
                                    all_text += page_text + "\n"
                                    print(f"  Page {i+1}: extracted {len(page_text)} chars (using extractText)")
                        except:
                            continue
                
                if all_text:
                    print(f"PyPDF2 SUCCESS: extracted {len(all_text)} characters")
                    print(f"First 200 chars: {all_text[:200]}")
                else:
                    print("PyPDF2 extracted no text")
            except Exception as e:
                print(f"PyPDF2 ERROR: {e}")
            
            if not all_text:
                print("WARNING: No text extracted from PDF")
                
                # Last resort: Try reading as corrupted PDF
                print("\nTrying last resort: reading as potentially corrupted PDF...")
                pdf_file.seek(0)
                try:
                    # Read raw bytes and look for text patterns
                    raw_content = pdf_file.read()
                    # Simple text extraction from raw PDF
                    import re
                    # Look for text between BT and ET markers
                    text_pattern = rb'BT[^>]*?>([^<]+)<[^>]*?ET'
                    matches = re.findall(text_pattern, raw_content)
                    if matches:
                        extracted_texts = []
                        for match in matches:
                            try:
                                text = match.decode('utf-8', errors='ignore')
                                if text.strip():
                                    extracted_texts.append(text)
                            except:
                                continue
                        if extracted_texts:
                            all_text = ' '.join(extracted_texts)
                            print(f"Raw extraction found {len(all_text)} characters")
                except Exception as raw_e:
                    print(f"Raw extraction error: {raw_e}")
            
            return all_text if all_text else None
            
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_transactions(self, text, month_name, source='Current Account'):
        """Parse transactions from multi-line bank statement format"""
        print(f"\n--- Parsing transactions for {month_name} ---")
        if not text:
            print("ERROR: No text to parse")
            return []
        
        print(f"Text length: {len(text)} characters")
        transactions = []
        lines = text.split('\n')
        print(f"Number of lines: {len(lines)}")
        
        # Look for header patterns to understand column structure
        paid_in_column = False
        paid_out_column = False
        
        for line in lines:
            if 'Paid in' in line and 'Paid out' in line:
                # We have both columns
                paid_in_column = True
                paid_out_column = True
                break
        
        # Find transaction sections
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip until we find transaction section header
            # Different banks use different headers
            if not any(header in line for header in [
                'Your Bank Account details',
                'Your HSBC Advance details',
                'Your account details',
                'Account details',
                'Transaction details'
            ]):
                i += 1
                continue
            
            # We're now in a transaction section
            i += 1  # Skip header line
            
            # Process transactions until we hit end markers
            while i < len(lines):
                line = lines[i].strip()
                
                # End of section markers
                if any(marker in line for marker in ['BALANCECARRIEDFORWARD', 'Prospect Place Darlington']):
                    break
                
                # Skip empty lines and headers
                if not line or line == 'A' or 'Date Payment type' in line or 'BALANCEBROUGHTFORWARD' in line:
                    i += 1
                    continue
                
                # Check if this is a date line
                date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})\s*(.*)$', line)
                if date_match:
                    date_str = date_match.group(1)
                    date = self.parse_date(date_str)
                    remainder = date_match.group(2).strip()
                    
                    # Process all transactions for this date
                    trans_list = self.extract_transactions_for_date(lines, i, date, remainder, paid_in_column, paid_out_column)
                    transactions.extend(trans_list)
                
                i += 1
        
        # Filter out invalid transactions
        valid_transactions = [t for t in transactions if t and t['amount'] != 0]
        
        print(f"\nParsed {len(valid_transactions)} valid transactions from {month_name}")
        if valid_transactions:
            print("First 3 transactions:")
            for i, trans in enumerate(valid_transactions[:3]):
                print(f"  {i+1}. Date: {trans['date']}, Amount: £{trans['amount']:.2f}, Desc: {trans['description'][:50]}...")
        
        return valid_transactions
    
    def extract_transactions_for_date(self, lines, date_line_idx, date, first_line_remainder, has_paid_in, has_paid_out):
        """Extract all transactions for a given date"""
        transactions = []
        current_idx = date_line_idx
        
        # Process first line remainder if it has content
        if first_line_remainder:
            trans = self.build_transaction_from_lines(lines, date_line_idx, date, first_line_remainder, has_paid_in, has_paid_out)
            if trans:
                transactions.append(trans)
                # Skip lines consumed by the first transaction
                lines_consumed = self.count_lines_consumed(lines, date_line_idx, first_line_remainder)
                current_idx = date_line_idx + lines_consumed
        
        # Look ahead for more transactions on this date
        i = current_idx + 1
        while i < len(lines):
            line = lines[i].strip()
            
            # Stop if we hit a new date or end marker
            if re.match(r'^\d{2}\s+\w{3}\s+\d{2}', line) or any(m in line for m in ['BALANCECARRIEDFORWARD', 'Prospect Place']):
                break
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Process transaction lines - any line with transaction prefixes or continuation
            if line.startswith(')))'):
                # Continuation transaction
                trans = self.build_transaction_from_lines(lines, i, date, line, has_paid_in, has_paid_out)
                if trans:
                    transactions.append(trans)
                    # Skip consumed lines
                    lines_consumed = self.count_lines_consumed(lines, i, line)
                    i += max(1, lines_consumed)
                else:
                    i += 1
            elif any(line.startswith(t) for t in ['VIS ', 'DD ', 'CR ', 'TFR ', 'BP ', 'SO ', 'ATM ']):
                # New transaction
                trans = self.build_transaction_from_lines(lines, i, date, line, has_paid_in, has_paid_out)
                if trans:
                    transactions.append(trans)
                    # Skip consumed lines
                    lines_consumed = self.count_lines_consumed(lines, i, line)
                    i += max(1, lines_consumed)
                else:
                    i += 1
            else:
                i += 1
        
        return transactions
    
    def count_lines_consumed(self, lines, start_idx, first_line):
        """Count how many lines were consumed by a transaction"""
        # This is a simplified version - in reality would need to track exact consumption
        consumed = 0
        i = start_idx + 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Stop at next transaction or date
            if (not line or 
                re.match(r'^\d{2}\s+\w{3}\s+\d{2}', line) or 
                line.startswith(')))') or 
                any(line.startswith(t) for t in ['VIS ', 'DD ', 'CR ', 'TFR ', 'BP ', 'SO ', 'ATM '])):
                break
            
            # Check if this line has an amount (end of transaction)
            if re.search(r'\d{1,3}(?:,\d{3})*\.\d{2}(?:\s+\d{1,3}(?:,\d{3})*\.\d{2}\s*D?)?$', line):
                consumed = i - start_idx
                break
            
            i += 1
        
        return consumed
    
    def build_transaction_from_lines(self, lines, start_idx, date, first_line, has_paid_in, has_paid_out):
        """Build a complete transaction from multiple lines"""
        description_parts = []
        amount = None
        is_credit = False
        
        # Handle first line
        if first_line.startswith(')))'):
            first_line = first_line[3:].strip()
        
        # Check if first line has CR, TFR, or other credit indicators
        if any(marker in first_line for marker in ['CR ', 'TFR ']):
            is_credit = True
        
        # Check if first line already contains amount
        first_line_amount = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})(?:\s+\d{1,3}(?:,\d{3})*\.\d{2}\s*D?)?$', first_line)
        if first_line_amount:
            # Extract amount from first line
            amount = float(first_line_amount.group(1).replace(',', ''))
            # Only add the description part (before amount) to description_parts
            desc_part = first_line[:first_line_amount.start()].strip()
            if desc_part:
                description_parts.append(desc_part)
        else:
            # No amount in first line, add the whole line
            if first_line:
                description_parts.append(first_line)
        
        # Look at next lines for completion
        i = start_idx + 1
        while i < len(lines) and len(description_parts) < 5:
            line = lines[i].strip()
            
            # Stop conditions
            if not line or re.match(r'^\d{2}\s+\w{3}\s+\d{2}', line) or line.startswith(')))') or any(line.startswith(t) for t in ['VIS ', 'DD ', 'CR ', 'TFR ', 'BP ', 'SO ', 'ATM ']):
                break
            
            # Look for amounts - could be in "Paid in" or "Paid out" position
            # The pattern is: optional text, then amount, then possibly balance
            # If we have Paid in/out columns, amounts appear in specific positions
            
            # Try to find standalone amount (just numbers)
            standalone_amount = re.match(r'^(\d{1,3}(?:,\d{3})*\.\d{2})(?:\s+\d{1,3}(?:,\d{3})*\.\d{2}\s*D?)?$', line)
            if standalone_amount:
                amount_str = standalone_amount.group(1)
                amount = float(amount_str.replace(',', ''))
                
                # This is a paid-in amount (credit) if it appears alone on a line after description
                # In bank statements, paid-in amounts often appear on separate lines
                if len(description_parts) > 0:
                    is_credit = True
                break
            
            # Check if line ends with amount
            line_with_amount = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})(?:\s+\d{1,3}(?:,\d{3})*\.\d{2}\s*D?)?$', line)
            if line_with_amount:
                # Extract description part
                desc_part = line[:line_with_amount.start()].strip()
                if desc_part:
                    description_parts.append(desc_part)
                
                amount_str = line_with_amount.group(1)
                amount = float(amount_str.replace(',', ''))
                break
            else:
                # This is a description line
                description_parts.append(line)
            
            i += 1
        
        # If no amount found, return None
        if amount is None:
            return None
        
        # Build final description
        full_description = ' '.join(description_parts)
        
        # Determine final amount sign
        # Credit transactions (money in) are positive
        # Debit transactions (money out) are negative
        
        # Check description for credit indicators
        credit_indicators = ['CR ', 'TFR ', 'CHILD BENEFIT', 'GIFT', 
                           'PAYMENT THANK YOU', 'PAYMENT RECEIVED', 'SALARY', 'PAYSTREAM']
        
        if is_credit or any(indicator in full_description.upper() for indicator in credit_indicators):
            amount = abs(amount)  # Positive for credits
        else:
            amount = -abs(amount)  # Negative for debits
        
        return {
            'date': date,
            'description': full_description,
            'amount': amount,
            'category': self.categorize_transaction(full_description),
            'type': 'credit' if amount > 0 else 'debit'
        }
    
    def parse_date(self, date_str):
        """Parse date string to standard format"""
        try:
            parts = date_str.strip().split()
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = '20' + year
                date_str = f"{day} {month} {year}"
            
            date_obj = datetime.strptime(date_str, "%d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Date parse error for '{date_str}': {e}")
            return "2024-01-01"
    
    def categorize_transaction(self, description):
        """Categorize transaction based on description"""
        desc_upper = description.upper()
        
        # Income
        if any(pattern in desc_upper for pattern in [
            'CHILD BENEFIT', 'WEEKLY SUBSISTENCE', 'GIFT', 'SALARY', 
            'PAYMENT THANK YOU', 'PAYMENT RECEIVED', 'CR PAYMENT', 'PAYSTREAM',
            'WAGES', 'BONUS', 'REFUND', 'REIMBURSEMENT'
        ]):
            return 'Income'
        
        # Rent
        if 'RENT' in desc_upper:
            return 'Rent'
        
        # Financial Services
        if any(pattern in desc_upper for pattern in ['HSBC', 'LOAN', 'PAYPAL', 'ATM', 'BANK']):
            return 'Financial Services'
        
        # Bills & Utilities
        if any(pattern in desc_upper for pattern in ['DD EE', 'DDEE', 'ELECTRIC', 'GAS', 'WATER', 'EE LIMITED']):
            return 'Bills & Utilities'
        
        # Groceries
        if any(pattern in desc_upper for pattern in [
            'SAINSBURY', 'TESCO', 'ASDA', 'BUDGENS', 'CO-OP', 'ALDI', 'LIDL', 'WAITROSE', 'MORRISONS'
        ]):
            return 'Groceries'
        
        # Transport
        if any(pattern in desc_upper for pattern in ['TFL', 'UBER', 'TAXI', 'TRAIN', 'RAIL', 'OYSTER']):
            return 'Transport'
        
        # Fast Food
        if any(pattern in desc_upper for pattern in ['GREGGS', 'MCDONALD', 'KFC', 'SUBWAY', 'BURGER', 'PIZZA HUT']):
            return 'Fast Food'
        
        # Coffee Shops
        if any(pattern in desc_upper for pattern in ['CAFFE NERO', 'STARBUCKS', 'COSTA', 'PRET A MANGER']):
            return 'Coffee Shops'
        
        # Shopping
        if any(pattern in desc_upper for pattern in [
            'AMAZON', 'PRIMARK', 'T K MAXX', 'TK MAXX', 'H & M', 'H&M', 'BOOTS', 
            'HOLLAND & BARRETT', 'APPLE.COM', 'GOOGLE', 'AUDIBLE', 'IKEA', 'ARGOS',
            'B & Q', 'B&Q', 'JOHN LEWIS', 'NEXT', 'ZARA', 'EBAY', 'ETSY'
        ]):
            return 'Shopping'
        
        # Entertainment/Subscriptions
        if any(pattern in desc_upper for pattern in [
            'LITTLE GYM', 'CINEMA', 'EVERYONE ACTIVE', 'NETFLIX', 'SPOTIFY', 'GYM',
            'PLAYSTATION', 'XBOX', 'NINTENDO', 'DISNEY', 'PRIME VIDEO'
        ]):
            return 'Entertainment'
        
        # Restaurants
        if any(pattern in desc_upper for pattern in ['NANDO', 'WAGAMAMA', 'PIZZA EXPRESS', 'RESTAURANT']):
            return 'Restaurants'
        
        # Healthcare
        if any(pattern in desc_upper for pattern in ['PHARMA', 'CHEMIST', 'MEDICAL', 'DOCTOR', 'DENTAL']):
            return 'Healthcare'
        
        # Food Delivery
        if any(pattern in desc_upper for pattern in ['DELIVEROO', 'JUST EAT', 'UBER EATS']):
            return 'Food Delivery'
        
        return 'Other'
    
    def process_pdf_batch(self, pdf_files_data):
        """Process multiple PDFs"""
        print("\n=== ImprovedMultilineProcessor: Processing PDF Batch ===")
        print(f"Number of PDFs to process: {len(pdf_files_data)}")
        
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
                    # Check if this is a credit card statement
                    if self.is_credit_card_statement(text):
                        print("Detected credit card statement - using credit card processor")
                        # Use the credit card processor directly
                        transactions = self.credit_card_processor.parse_transactions(text, month_name, source)
                    else:
                        # Use regular parser for current account statements
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