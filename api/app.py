from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
# import pandas as pd  # Removed to save memory
# import pdfplumber  # Using PyPDF2 instead
import openai
from werkzeug.utils import secure_filename
from typing import List, Dict, Any
import re
from datetime import datetime
import tempfile
import base64
try:
    # Try improved multiline processor first
    from improved_multiline_processor import ImprovedMultilineProcessor as PDFProcessor
    print("Using improved multiline PDF processor")
except ImportError:
    try:
        # Fallback to multiline processor
        from multiline_pdf_processor import MultilinePDFProcessor as PDFProcessor
        print("Using multiline PDF processor")
    except ImportError:
        try:
            # Fallback to corrected processor
            from corrected_pdf_processor import CorrectedPDFProcessor as PDFProcessor
            print("Using corrected PDF processor")
        except ImportError:
            try:
                # Fallback to enhanced processor
                from enhanced_pdf_processor import EnhancedPDFProcessor as PDFProcessor
                print("Using enhanced PDF processor")
            except ImportError as e:
                print(f"Error importing PDF processors: {e}")
                PDFProcessor = None

# Import PayPal processor
try:
    from paypal_processor import PayPalStatementProcessor
    print("PayPal processor imported successfully")
except ImportError as e:
    print(f"Error importing PayPal processor: {e}")
    PayPalStatementProcessor = None

app = Flask(__name__)
CORS(app)

# Configure OpenAI
openai.api_key = os.environ.get('OPENAI_API_KEY')
print(f"OpenAI API Key configured: {'Yes' if openai.api_key else 'No'}")
if not openai.api_key:
    print("WARNING: OPENAI_API_KEY environment variable not set!")

# Configure upload settings
ALLOWED_EXTENSIONS = {'csv', 'pdf', 'xls', 'xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'FinanceCompare API'})

@app.route('/api/test-pdf', methods=['POST'])
def test_pdf():
    """Test PDF extraction without parsing"""
    try:
        print("\n--- Test PDF Endpoint Called ---")
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        print(f"File received: {file.filename}")
        pdf_content = file.read()
        print(f"PDF size: {len(pdf_content)} bytes")
        
        if PDFProcessor is None:
            print("ERROR: PDFProcessor is None")
            return jsonify({'error': 'PDF processor not available'}), 500
        
        # Try to extract text
        processor = PDFProcessor()
        text = processor.extract_text_from_pdf(pdf_content)
        
        # Also check if it's a credit card statement
        is_credit_card = processor.is_credit_card_statement(text) if text else False
        
        response_data = {
            'success': text is not None,
            'text_length': len(text) if text else 0,
            'first_500_chars': text[:500] if text else None,
            'pdf_size': len(pdf_content),
            'is_credit_card': is_credit_card,
            'processor_used': PDFProcessor.__name__
        }
        
        print(f"Test PDF Result: success={response_data['success']}, text_length={response_data['text_length']}")
        return jsonify(response_data)
    except Exception as e:
        print(f"ERROR in test_pdf: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.route('/api/parse-pdf', methods=['POST'])
def parse_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            file.save(tmp_file.name)
            
            # Extract text from PDF
            transactions = []
            with pdfplumber.open(tmp_file.name) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Parse transactions from text using AI
                        page_transactions = parse_pdf_text_with_ai(text)
                        transactions.extend(page_transactions)
            
            # Clean up temp file
            os.unlink(tmp_file.name)
            
        return jsonify({'transactions': transactions})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Excel endpoint commented out - pandas removed
# @app.route('/api/parse-excel', methods=['POST'])
# def parse_excel():
#     try:
#         if 'file' not in request.files:
#             return jsonify({'error': 'No file provided'}), 400
#         
#         file = request.files['file']
#         if file.filename == '':
#             return jsonify({'error': 'No file selected'}), 400
#         
#         if not allowed_file(file.filename):
#             return jsonify({'error': 'Invalid file type'}), 400
#         
#         # Read Excel file
#         df = pd.read_excel(file)
#         
#         # Convert to transactions
#         transactions = []
#         for index, row in df.iterrows():
#             transaction = parse_excel_row(row, index)
#             transactions.append(transaction)
#         
#         return jsonify({'transactions': transactions})
#         
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

@app.route('/api/parse-pdf-vision', methods=['POST'])
def parse_pdf_vision():
    """Parse PDF using Google Vision API for better OCR accuracy"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get month from request
        month = request.form.get('month', 'Unknown')
        
        # Read file content
        pdf_content = file.read()
        pdf_base64 = base64.b64encode(pdf_content).decode()
        
        # Detect source type
        filename_lower = file.filename.lower()
        if 'paypal' in filename_lower or 'msr' in filename_lower:
            source = 'PayPal'
            if PayPalStatementProcessor is None:
                return jsonify({'error': 'PayPal processor not available. Check server logs.'}), 500
            processor = PayPalStatementProcessor()
        else:
            source = 'Current Account' if 'current' in filename_lower else 'Credit Card'
            if PDFProcessor is None:
                return jsonify({'error': 'PDF processor not available. Check server logs.'}), 500
            processor = PDFProcessor()
        
        transactions = processor.process_pdf_batch([{
            'content': pdf_base64,
            'month': month,
            'filename': file.filename,
            'source': source
        }])
        
        return jsonify({'transactions': transactions})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parse-pdfs-batch', methods=['POST', 'OPTIONS'])
def parse_pdfs_batch():
    """Parse multiple PDFs at once"""
    print("\n=== PDF Batch Processing Start ===")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
        
    try:
        files = request.files.getlist('files')
        print(f"Number of files received: {len(files)}")
        
        if not files:
            print("ERROR: No files provided")
            return jsonify({'error': 'No files provided'}), 400
        
        # Get months from request
        months = request.form.getlist('months')
        print(f"Months received: {months}")
        
        pdf_data = []
        for i, file in enumerate(files):
            print(f"\nProcessing file {i+1}: {file.filename}")
            if file and allowed_file(file.filename):
                pdf_content = file.read()
                print(f"  - File size: {len(pdf_content)} bytes")
                pdf_base64 = base64.b64encode(pdf_content).decode()
                
                month = months[i] if i < len(months) else f'Month {i+1}'
                
                # Detect source type from filename
                filename_lower = file.filename.lower()
                if 'paypal' in filename_lower or 'msr' in filename_lower:
                    source = 'PayPal'
                elif 'current' in filename_lower:
                    source = 'Current Account'
                else:
                    source = 'Credit Card'
                
                print(f"  - Month: {month}")
                print(f"  - Source: {source}")
                
                pdf_data.append({
                    'content': pdf_base64,
                    'month': month,
                    'filename': file.filename,
                    'source': source
                })
            else:
                print(f"  - SKIPPED: Invalid file type")
        
        # Process all PDFs
        print(f"\nProcessing {len(pdf_data)} PDFs")
        
        # Separate PayPal and non-PayPal PDFs
        paypal_pdfs = [pdf for pdf in pdf_data if pdf['source'] == 'PayPal']
        other_pdfs = [pdf for pdf in pdf_data if pdf['source'] != 'PayPal']
        
        all_transactions = []
        
        # Process PayPal statements
        if paypal_pdfs:
            print(f"\nProcessing {len(paypal_pdfs)} PayPal PDFs")
            if PayPalStatementProcessor is None:
                print("ERROR: PayPalStatementProcessor is None")
                return jsonify({'error': 'PayPal processor not available. Check server logs.'}), 500
            
            paypal_processor = PayPalStatementProcessor()
            paypal_transactions = paypal_processor.process_pdf_batch(paypal_pdfs)
            all_transactions.extend(paypal_transactions)
            print(f"PayPal processor returned {len(paypal_transactions)} transactions")
        
        # Process other statements
        if other_pdfs:
            print(f"\nProcessing {len(other_pdfs)} bank statement PDFs")
            if PDFProcessor is None:
                print("ERROR: PDFProcessor is None")
                return jsonify({'error': 'PDF processor not available. Check server logs.'}), 500
            
            print(f"Using PDFProcessor: {PDFProcessor.__name__}")
            processor = PDFProcessor()
            bank_transactions = processor.process_pdf_batch(other_pdfs)
            all_transactions.extend(bank_transactions)
            print(f"Bank processor returned {len(bank_transactions)} transactions")
        
        print(f"\nTotal transactions from all processors: {len(all_transactions)}")
        
        # Debug: Print first few transactions
        if all_transactions:
            print("\nFirst 3 transactions:")
            for i, trans in enumerate(all_transactions[:3]):
                print(f"  Transaction {i+1}: {trans}")
        else:
            print("\nWARNING: No transactions returned from PDFProcessor")
        
        # Auto-categorize transactions using GPT-4
        if all_transactions:
            print(f"\nAuto-categorizing {len(all_transactions)} transactions with OpenAI...")
            try:
                categorized = categorize_with_openai(all_transactions)
                print(f"Categorization complete: {len(categorized)} categories returned")
                
                # Apply categories back to transactions
                for i, trans in enumerate(all_transactions):
                    if i < len(categorized):
                        # Update category if it's currently "Other" or uncategorized
                        old_category = trans.get('category', 'Other')
                        new_category = categorized[i].get('category', 'Other')
                        if old_category == 'Other' and new_category != 'Other':
                            trans['category'] = new_category
                            print(f"  Updated transaction {i+1} category: {old_category} -> {new_category}")
            except Exception as cat_error:
                print(f"ERROR during categorization: {cat_error}")
                # Continue without categorization
        else:
            print("\nSkipping categorization - no transactions to categorize")
        
        # Generate JavaScript format
        js_content = generate_js_export(all_transactions)
        
        # Generate summary
        summary = generate_summary(all_transactions)
        print(f"\nSummary generated:")
        print(f"  - Total spending: £{summary.get('total_spending', 0):.2f}")
        print(f"  - Transaction count: {summary.get('transaction_count', 0)}")
        print(f"  - Categories: {list(summary.get('categories', {}).keys())}")
        
        response_data = {
            'transactions': all_transactions,
            'js_export': js_content,
            'summary': summary
        }
        
        print(f"\nReturning response with {len(all_transactions)} transactions")
        print("=== PDF Batch Processing End (Success) ===")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"\nERROR in parse_pdfs_batch: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=== PDF Batch Processing End (Error) ===")
        return jsonify({'error': str(e)}), 500

def generate_js_export(transactions):
    """Generate JavaScript export format for frontend"""
    js_content = "export const transactions = [\n"
    
    for trans in transactions:
        js_content += f"  {{\n"
        js_content += f"    id: {trans['id']},\n"
        js_content += f"    date: '{trans['date']}',\n"
        desc = trans['description'].replace('"', '\\"').replace("'", "\\'")
        js_content += f"    description: '{desc}',\n"
        js_content += f"    amount: {trans['amount']},\n"
        js_content += f"    category: '{trans['category']}',\n"
        js_content += f"    month: '{trans['month']}'\n"
        js_content += f"  }},\n"
    
    js_content += "];\n"
    return js_content

def generate_summary(transactions):
    """Generate summary statistics"""
    categories = {}
    total_spending = 0
    
    for trans in transactions:
        if trans['amount'] < 0:  # Only count debits
            amount = abs(trans['amount'])
            total_spending += amount
            
            category = trans['category']
            if category not in categories:
                categories[category] = {'count': 0, 'amount': 0}
            
            categories[category]['count'] += 1
            categories[category]['amount'] += amount
    
    return {
        'total_spending': total_spending,
        'transaction_count': len(transactions),
        'categories': categories
    }

@app.route('/api/categorize', methods=['POST'])
def categorize_transactions():
    try:
        data = request.get_json()
        transactions = data.get('transactions', [])
        
        if not transactions:
            return jsonify({'categorized': []})
        
        # Use OpenAI to categorize transactions
        categorized = categorize_with_openai(transactions)
        
        return jsonify({'categorized': categorized})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-category', methods=['POST'])
def update_transaction_category():
    """Update a single transaction's category"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        new_category = data.get('category')
        
        # In a real app, this would update a database
        # For now, just return success
        return jsonify({
            'success': True,
            'transaction_id': transaction_id,
            'category': new_category
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/merge-categories', methods=['POST'])
def merge_categories():
    """Merge two categories into one"""
    try:
        data = request.get_json()
        source_category = data.get('source')
        target_category = data.get('target')
        
        # In a real app, this would update all transactions with source category
        # For now, just return success
        return jsonify({
            'success': True,
            'merged': f"{source_category} -> {target_category}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recategorize', methods=['POST'])
def recategorize_category():
    """Re-categorize all transactions in a specific category using AI"""
    try:
        data = request.get_json()
        category_name = data.get('category')
        transactions = data.get('transactions', [])
        
        if not transactions:
            return jsonify({'recategorized': []})
        
        # Filter transactions for the specified category
        category_transactions = [t for t in transactions if t.get('category') == category_name]
        
        if not category_transactions:
            return jsonify({'recategorized': []})
        
        print(f"Re-categorizing {len(category_transactions)} transactions from '{category_name}'")
        
        # Use OpenAI to recategorize these specific transactions
        categorized = categorize_with_openai(category_transactions)
        
        # Apply the new categories
        recategorized = []
        for i, trans in enumerate(category_transactions):
            if i < len(categorized):
                new_category = categorized[i].get('category', 'Other')
                # Only update if the category is different and not 'Other'
                if new_category != category_name and new_category != 'Other':
                    recategorized.append({
                        'id': trans['id'],
                        'oldCategory': category_name,
                        'newCategory': new_category,
                        'description': trans['description']
                    })
        
        return jsonify({
            'recategorized': recategorized,
            'total': len(category_transactions),
            'updated': len(recategorized)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def parse_pdf_text_with_ai(text: str) -> List[Dict[str, Any]]:
    """Use OpenAI to extract transactions from PDF text"""
    try:
        prompt = f"""
        Extract financial transactions from the following bank statement text.
        For each transaction, extract:
        - Date (in ISO format YYYY-MM-DD)
        - Description
        - Amount (negative for debits, positive for credits)
        - Balance (if available)
        
        Return as JSON array with format:
        [
            {{
                "date": "YYYY-MM-DD",
                "description": "transaction description",
                "amount": -123.45,
                "balance": 1234.56
            }}
        ]
        
        Text:
        {text[:3000]}  # Limit text to avoid token limits
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial data extraction assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=2000
        )
        
        result = response.choices[0].message['content']
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        if json_match:
            transactions_data = json.loads(json_match.group())
            
            # Convert to transaction format
            transactions = []
            for i, item in enumerate(transactions_data):
                transaction = {
                    'id': f'pdf-{datetime.now().timestamp()}-{i}',
                    'date': item.get('date', datetime.now().isoformat()),
                    'description': item.get('description', 'Unknown'),
                    'amount': float(item.get('amount', 0)),
                    'balance': float(item.get('balance', 0)) if item.get('balance') else None,
                    'type': 'credit' if float(item.get('amount', 0)) > 0 else 'debit'
                }
                transactions.append(transaction)
            
            return transactions
        
        return []
        
    except Exception as e:
        print(f"Error parsing PDF with AI: {e}")
        return []

"""
# Excel row parser - commented out since pandas was removed
def parse_excel_row(row: pd.Series, index: int) -> Dict[str, Any]:
    # Parse a row from Excel/CSV file
    transaction = {
        'id': f'excel-{datetime.now().timestamp()}-{index}',
        'date': None,
        'description': '',
        'amount': 0,
        'balance': None,
        'type': 'debit'
    }
    
    # Try to find date
    date_columns = ['Date', 'Transaction Date', 'Trans Date', 'Posted Date']
    for col in date_columns:
        if col in row and pd.notna(row[col]):
            try:
                transaction['date'] = pd.to_datetime(row[col]).isoformat()
                break
            except:
                pass
    
    if not transaction['date']:
        transaction['date'] = datetime.now().isoformat()
    
    # Try to find description
    desc_columns = ['Description', 'Memo', 'Transaction Description', 'Details']
    for col in desc_columns:
        if col in row and pd.notna(row[col]):
            transaction['description'] = str(row[col])
            break
    
    # Try to find amount
    amount_columns = ['Amount', 'Debit', 'Credit', 'Transaction Amount']
    for col in amount_columns:
        if col in row and pd.notna(row[col]):
            try:
                amount = float(str(row[col]).replace('$', '').replace(',', ''))
                if 'debit' in col.lower():
                    amount = -abs(amount)
                elif 'credit' in col.lower():
                    amount = abs(amount)
                transaction['amount'] = abs(amount)
                transaction['type'] = 'credit' if amount > 0 else 'debit'
                break
            except:
                pass
    
    # Try to find balance
    balance_columns = ['Balance', 'Running Balance', 'Account Balance']
    for col in balance_columns:
        if col in row and pd.notna(row[col]):
            try:
                transaction['balance'] = float(str(row[col]).replace('$', '').replace(',', ''))
                break
            except:
                pass
    
    return transaction
"""

def categorize_with_openai(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use OpenAI to categorize transactions"""
    try:
        if not openai.api_key:
            print("WARNING: OpenAI API key not set, skipping categorization")
            return [{'category': 'Other', 'merchant': t.get('description', '')} for t in transactions]
        all_categorized = []
        
        # Process in batches of 40 to avoid token limits
        batch_size = 40
        for batch_start in range(0, len(transactions), batch_size):
            batch = transactions[batch_start:batch_start + batch_size]
            
            # Prepare transaction descriptions
            transaction_list = "\n".join([
                f"{i+1}. {t['description']} (£{abs(t.get('amount', 0)):.2f}) {'CR' if t.get('amount', 0) > 0 else 'DR'}"
                for i, t in enumerate(batch)
            ])
        
            prompt = f"""
            Categorize the following UK bank transactions intelligently. Be specific and accurate based on the merchant names:

            Categories to use:
            - Income (salaries, payments received, transfers in - PAYSTREAM, CR PAYMENTS)
            - Rent (monthly rent payments)
            - Bills & Utilities (electricity, gas, water, internet, phone - EDF ENERGY, BT GROUP)
            - Groceries (supermarkets - TESCO, SAINSBURY'S, ASDA, CO-OP, BUDGENS)
            - Restaurants (sit-down dining - NANDO'S, WAGAMAMA, restaurants)
            - Fast Food (quick service - MCDONALD'S, KFC, SUBWAY, GREGGS)
            - Food Delivery (DELIVEROO, JUST EAT, UBER EATS)
            - Coffee Shops (CAFFE NERO, STARBUCKS, COSTA)
            - Transport (TFL, trains, buses, UBER, taxis)
            - Fuel (petrol stations - BP, SHELL, ESSO)
            - Parking (parking fees, RINGGO, NCP)
            - Shopping (retail stores, online shopping - AMAZON, IKEA, clothing)
            - Subscriptions (recurring services - NETFLIX, SPOTIFY, gym memberships like EVERYONE ACTIVE)
            - Financial Services (PAYPAL, bank fees, ATM)
            - Entertainment (cinema, gaming, streaming)
            - Healthcare (pharmacy, medical)
            - Personal Care (barber, beauty)
            - Other (anything else)
            
            Important notes:
            - PAYSTREAM/CRPAYSTREAM = Income (salary)
            - DDPAYPAL = Financial Services (PayPal direct debit)
            - DDEVERYONE ACTIVE = Subscriptions (gym membership)
            - PAYMENT THANK YOU = Income
            - Look for DD prefix = Direct Debit
            - Look for CR suffix = Credit (income)
            - ATM = Financial Services (cash withdrawal)
            - HSBC/bank names = Financial Services
            - CR at start or CRPAYSTREAM = Income
            
            Transactions:
            {transaction_list}
            
            Return as JSON array with format:
            [
                {{
                    "category": "Category Name",
                    "merchant": "Clean Merchant Name"
                }}
            ]
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-1106-preview",  # Using GPT-4 for better categorization
                messages=[
                    {"role": "system", "content": "You are an expert financial categorization assistant for UK bank statements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=2000
            )
            
            result = response.choices[0].message['content']
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                categories = json.loads(json_match.group())
                
                # Add to all categorized
                for i, cat in enumerate(categories):
                    if i < len(batch):
                        all_categorized.append({
                            'category': cat.get('category', 'Other'),
                            'merchant': cat.get('merchant', batch[i].get('description', ''))
                        })
            else:
                # Fallback for this batch
                for t in batch:
                    all_categorized.append({
                        'category': 'Other',
                        'merchant': t.get('description', '')
                    })
        
        return all_categorized
        
    except Exception as e:
        print(f"Error categorizing with OpenAI: {e}")
        # Fallback to basic categorization
        return [{'category': 'Other', 'merchant': t['description']} for t in transactions]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)