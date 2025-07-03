import React, { useState } from 'react';
import { Upload, X } from 'lucide-react';

const DataUpload = ({ onDataUpload }) => {
  const [showInstructions, setShowInstructions] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'text/csv') {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const csvData = e.target.result;
          const transactions = parseCSV(csvData);
          onDataUpload(transactions);
          setUploadStatus('success');
        } catch (error) {
          setUploadStatus('error');
          console.error('Error parsing CSV:', error);
        }
      };
      reader.readAsText(file);
    } else {
      setUploadStatus('error');
    }
  };

  const parseCSV = (csvData) => {
    const lines = csvData.split('\n');
    const transactions = [];
    
    // Skip header if exists
    const startIndex = lines[0].toLowerCase().includes('date') ? 1 : 0;
    
    lines.slice(startIndex).forEach((line, index) => {
      if (line.trim()) {
        const [date, description, amount, category] = line.split(',').map(item => item.trim());
        
        transactions.push({
          id: index + 1,
          date: date,
          description: description.replace(/"/g, ''),
          amount: parseFloat(amount),
          category: category || categorizeTransaction(description),
          month: new Date(date).toLocaleDateString('en-US', { month: 'long' })
        });
      }
    });
    
    return transactions;
  };

  const categorizeTransaction = (description) => {
    const desc = description.toLowerCase();
    
    if (desc.includes('tesco') || desc.includes('sainsbury') || desc.includes('asda') || desc.includes('waitrose')) {
      return 'Groceries';
    } else if (desc.includes('tfl') || desc.includes('uber') || desc.includes('rail')) {
      return 'Transport';
    } else if (desc.includes('mcdonald') || desc.includes('kfc') || desc.includes('burger')) {
      return 'Fast Food';
    } else if (desc.includes('costa') || desc.includes('starbucks') || desc.includes('pret')) {
      return 'Coffee Shops';
    } else if (desc.includes('deliveroo') || desc.includes('just eat') || desc.includes('uber eat')) {
      return 'Food Delivery';
    } else if (desc.includes('netflix') || desc.includes('spotify') || desc.includes('amazon prime')) {
      return 'Subscriptions';
    } else if (desc.includes('shell') || desc.includes('bp') || desc.includes('esso') || desc.includes('petrol')) {
      return 'Fuel';
    } else if (desc.includes('parking')) {
      return 'Parking';
    } else if (desc.includes('restaurant') || desc.includes('wagamama') || desc.includes('nando')) {
      return 'Restaurants';
    }
    
    return 'Other';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Upload Bank Statement</h2>
      
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        
        <p className="text-gray-600 mb-4">
          Upload your bank statement CSV file to analyze your spending
        </p>
        
        <input
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          className="hidden"
          id="file-upload"
        />
        
        <label
          htmlFor="file-upload"
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors"
        >
          Choose CSV File
        </label>
        
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          className="block mx-auto mt-4 text-sm text-blue-600 hover:underline"
        >
          How to export from your bank?
        </button>
      </div>

      {uploadStatus === 'success' && (
        <div className="mt-4 p-4 bg-green-100 text-green-700 rounded-lg">
          ✓ File uploaded successfully! Your data is being analyzed.
        </div>
      )}

      {uploadStatus === 'error' && (
        <div className="mt-4 p-4 bg-red-100 text-red-700 rounded-lg">
          ✗ Error uploading file. Please ensure it's a valid CSV file.
        </div>
      )}

      {showInstructions && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg relative">
          <button
            onClick={() => setShowInstructions(false)}
            className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
          
          <h3 className="font-semibold mb-3">CSV Format Instructions:</h3>
          <p className="text-sm text-gray-700 mb-3">
            Your CSV file should have the following format:
          </p>
          <pre className="bg-white p-3 rounded text-xs overflow-x-auto">
{`Date,Description,Amount,Category
2025-01-05,Tesco Express,-45.67,Groceries
2025-01-06,TfL Travel,-25.50,Transport
2025-01-08,Pret A Manger,-12.95,Coffee Shops`}
          </pre>
          
          <div className="mt-4">
            <h4 className="font-semibold text-sm mb-2">Common Bank Export Steps:</h4>
            <ol className="text-sm text-gray-700 space-y-1">
              <li>1. Log into your online banking</li>
              <li>2. Navigate to your account statements</li>
              <li>3. Select date range (e.g., last 6 months)</li>
              <li>4. Choose "Export" or "Download"</li>
              <li>5. Select "CSV" format</li>
              <li>6. Save the file and upload here</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataUpload;