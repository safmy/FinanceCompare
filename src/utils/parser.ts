import Papa from 'papaparse';
import { Transaction } from '../types';

export async function parseTransactions(file: File): Promise<Transaction[]> {
  const fileType = file.name.split('.').pop()?.toLowerCase();
  
  switch (fileType) {
    case 'csv':
      return parseCSV(file);
    case 'pdf':
      return parsePDF(file);
    case 'xls':
    case 'xlsx':
      return parseExcel(file);
    default:
      throw new Error(`Unsupported file type: ${fileType}`);
  }
}

async function parseCSV(file: File): Promise<Transaction[]> {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      complete: (results) => {
        try {
          const transactions = results.data
            .filter((row: any) => row && Object.keys(row).length > 0)
            .map((row: any, index: number) => parseTransactionRow(row, index));
          resolve(transactions);
        } catch (error) {
          reject(error);
        }
      },
      error: (error) => {
        reject(error);
      },
    });
  });
}

async function parsePDF(file: File): Promise<Transaction[]> {
  // For PDF parsing, we'll need to send to backend API
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/parse-pdf', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('Failed to parse PDF');
  }
  
  const data = await response.json();
  return data.transactions;
}

async function parseExcel(file: File): Promise<Transaction[]> {
  // For Excel parsing, we'll need to send to backend API
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/parse-excel', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('Failed to parse Excel file');
  }
  
  const data = await response.json();
  return data.transactions;
}

function parseTransactionRow(row: any, index: number): Transaction {
  // Try to detect common CSV formats from different banks
  const transaction: Transaction = {
    id: `tx-${Date.now()}-${index}`,
    date: parseDate(row),
    description: parseDescription(row),
    amount: parseAmount(row),
    type: 'debit',
    originalText: JSON.stringify(row),
  };
  
  // Parse balance if available
  const balance = parseBalance(row);
  if (balance !== null) {
    transaction.balance = balance;
  }
  
  // Determine if credit or debit
  if (transaction.amount > 0) {
    transaction.type = 'credit';
  } else {
    transaction.amount = Math.abs(transaction.amount);
  }
  
  return transaction;
}

function parseDate(row: any): Date {
  // Common date field names
  const dateFields = ['Date', 'Transaction Date', 'Trans Date', 'Posted Date', 'date', 'trans_date'];
  
  for (const field of dateFields) {
    if (row[field]) {
      const date = new Date(row[field]);
      if (!isNaN(date.getTime())) {
        return date;
      }
    }
  }
  
  // If no valid date found, use current date
  return new Date();
}

function parseDescription(row: any): string {
  // Common description field names
  const descFields = ['Description', 'Memo', 'Transaction Description', 'Details', 'description', 'memo'];
  
  for (const field of descFields) {
    if (row[field]) {
      return row[field].trim();
    }
  }
  
  return 'Unknown Transaction';
}

function parseAmount(row: any): number {
  // Common amount field names
  const amountFields = ['Amount', 'Debit', 'Credit', 'Transaction Amount', 'amount', 'debit', 'credit'];
  
  for (const field of amountFields) {
    if (row[field]) {
      const amount = parseFloat(row[field].replace(/[^0-9.-]/g, ''));
      if (!isNaN(amount)) {
        // Handle separate debit/credit columns
        if (field.toLowerCase().includes('debit')) {
          return -Math.abs(amount);
        } else if (field.toLowerCase().includes('credit')) {
          return Math.abs(amount);
        }
        return amount;
      }
    }
  }
  
  // Check for separate debit and credit columns
  const debit = parseFloat(row['Debit']?.replace(/[^0-9.-]/g, '') || '0');
  const credit = parseFloat(row['Credit']?.replace(/[^0-9.-]/g, '') || '0');
  
  if (!isNaN(debit) && debit !== 0) {
    return -Math.abs(debit);
  } else if (!isNaN(credit) && credit !== 0) {
    return Math.abs(credit);
  }
  
  return 0;
}

function parseBalance(row: any): number | null {
  // Common balance field names
  const balanceFields = ['Balance', 'Running Balance', 'Account Balance', 'balance', 'running_balance'];
  
  for (const field of balanceFields) {
    if (row[field]) {
      const balance = parseFloat(row[field].replace(/[^0-9.-]/g, ''));
      if (!isNaN(balance)) {
        return balance;
      }
    }
  }
  
  return null;
}