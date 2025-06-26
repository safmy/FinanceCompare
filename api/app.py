from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import pandas as pd
import pdfplumber
import openai
from werkzeug.utils import secure_filename
from typing import List, Dict, Any
import re
from datetime import datetime
import tempfile

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

@app.route('/api/parse-excel', methods=['POST'])
def parse_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Read Excel file
        df = pd.read_excel(file)
        
        # Convert to transactions
        transactions = []
        for index, row in df.iterrows():
            transaction = parse_excel_row(row, index)
            transactions.append(transaction)
        
        return jsonify({'transactions': transactions})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

def parse_excel_row(row: pd.Series, index: int) -> Dict[str, Any]:
    """Parse a row from Excel/CSV file"""
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

def categorize_with_openai(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use OpenAI to categorize transactions"""
    try:
        # Prepare transaction descriptions
        transaction_list = "\n".join([
            f"{i+1}. {t['description']} (${t['amount']})"
            for i, t in enumerate(transactions[:50])  # Limit to 50 transactions
        ])
        
        prompt = f"""
        Categorize the following financial transactions into these categories:
        - Food & Dining
        - Shopping
        - Transportation
        - Bills & Utilities
        - Entertainment
        - Healthcare
        - Education
        - Travel
        - Personal Care
        - Home & Garden
        - Gifts & Donations
        - Financial
        - Business
        - Income (for credits/deposits)
        - Other
        
        Also extract the merchant name from each description.
        
        Transactions:
        {transaction_list}
        
        Return as JSON array with format:
        [
            {{
                "category": "Category Name",
                "merchant": "Merchant Name"
            }}
        ]
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial categorization assistant."},
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
            
            # Apply categories to all transactions
            categorized = []
            for i, transaction in enumerate(transactions):
                if i < len(categories):
                    categorized.append({
                        'category': categories[i].get('category', 'Other'),
                        'merchant': categories[i].get('merchant', transaction['description'])
                    })
                else:
                    # Fallback for transactions beyond the limit
                    categorized.append({
                        'category': 'Other',
                        'merchant': transaction['description']
                    })
            
            return categorized
        
        # Fallback if parsing fails
        return [{'category': 'Other', 'merchant': t['description']} for t in transactions]
        
    except Exception as e:
        print(f"Error categorizing with OpenAI: {e}")
        # Fallback to basic categorization
        return [{'category': 'Other', 'merchant': t['description']} for t in transactions]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)