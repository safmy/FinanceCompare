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
    # Import all available processors
    from enhanced_pdf_processor import EnhancedPDFProcessor
    from zivile_pdf_processor import ZivilePDFProcessor
    from simple_pdf_processor import SimplePDFProcessor
    
    # Default to enhanced processor
    PDFProcessor = EnhancedPDFProcessor
    print("PDF processors loaded successfully")
except ImportError as e:
    print(f"Error importing PDF processors: {e}")
    try:
        from simple_pdf_processor import SimplePDFProcessor as PDFProcessor
        print("Using simple PDF processor (PyPDF2)")
    except:
        PDFProcessor = None

app = Flask(__name__)
CORS(app)

# Configure OpenAI
openai.api_key = os.environ.get('OPENAI_API_KEY')

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
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        pdf_content = file.read()
        
        # Try to extract text
        processor = PDFProcessor()
        text = processor.extract_text_from_pdf(pdf_content)
        
        return jsonify({
            'success': text is not None,
            'text_length': len(text) if text else 0,
            'first_500_chars': text[:500] if text else None,
            'pdf_size': len(pdf_content)
        })
    except Exception as e:
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
        
        # Process with Google Vision
        if PDFProcessor is None:
            return jsonify({'error': 'PDF processor not available. Check server logs.'}), 500
            
        processor = PDFProcessor()
        transactions = processor.process_pdf_batch([{
            'content': pdf_base64,
            'month': month,
            'filename': file.filename,
            'source': 'Current Account' if 'current' in file.filename.lower() else 'Credit Card'
        }])
        
        return jsonify({'transactions': transactions})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parse-pdfs-batch', methods=['POST', 'OPTIONS'])
def parse_pdfs_batch():
    """Parse multiple PDFs at once"""
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
        
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        # Get months from request
        months = request.form.getlist('months')
        
        pdf_data = []
        for i, file in enumerate(files):
            if file and allowed_file(file.filename):
                pdf_content = file.read()
                pdf_base64 = base64.b64encode(pdf_content).decode()
                
                month = months[i] if i < len(months) else f'Month {i+1}'
                pdf_data.append({
                    'content': pdf_base64,
                    'month': month,
                    'filename': file.filename,
                    'source': 'Current Account' if 'current' in file.filename.lower() else 'Credit Card'
                })
        
        # Process all PDFs
        print(f"Processing {len(pdf_data)} PDFs")
        
        if PDFProcessor is None:
            return jsonify({'error': 'PDF processor not available. Check server logs.'}), 500
        
        # Detect which processor to use based on filename patterns
        processor = None
        if pdf_data and 'filename' in pdf_data[0]:
            first_filename = pdf_data[0]['filename'].lower()
            if 'zivile' in first_filename or any('zivile' in pd.get('filename', '').lower() for pd in pdf_data):
                try:
                    processor = ZivilePDFProcessor()
                    print("Using Zivile PDF processor for specialized format")
                except:
                    processor = PDFProcessor()
            else:
                processor = PDFProcessor()
        else:
            processor = PDFProcessor()
            
        all_transactions = processor.process_pdf_batch(pdf_data)
        print(f"Found {len(all_transactions)} total transactions")
        
        # Auto-categorize transactions using GPT-4
        if all_transactions:
            print(f"Auto-categorizing {len(all_transactions)} transactions...")
            categorized = categorize_with_openai(all_transactions)
            
            # Apply categories back to transactions
            for i, trans in enumerate(all_transactions):
                if i < len(categorized):
                    # Update category if it's currently "Other" or uncategorized
                    if trans.get('category', 'Other') == 'Other':
                        trans['category'] = categorized[i].get('category', 'Other')
        
        # Generate JavaScript format
        js_content = generate_js_export(all_transactions)
        
        return jsonify({
            'transactions': all_transactions,
            'js_export': js_content,
            'summary': generate_summary(all_transactions)
        })
        
    except Exception as e:
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
            - CRHMRC CHILD BENEFIT = Income (government benefit)
            - CRVICTORAS GIFT = Income (gift/transfer)
            - DDPAYPAL = Financial Services (PayPal direct debit)
            - DDHSBC PLC LOANS = Financial Services (loan payment)
            - DDEE LIMITED / DDEE = Bills & Utilities (likely energy company)
            - DDEVERYONE ACTIVE = Subscriptions (gym membership)
            - PAYMENT THANK YOU = Income
            - Look for DD prefix = Direct Debit (usually bills or subscriptions)
            - Look for CR prefix = Credit (income)
            - ATM = Financial Services (cash withdrawal)
            - HSBC/bank names = Financial Services
            - VIS = Shopping (Visa card transaction)
            - WEEKLY SUBSISTENCE = Income (allowance/subsistence)
            
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
                model="gpt-4o",  # Using GPT-4o for improved categorization
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