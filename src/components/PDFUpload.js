import React, { useState } from 'react';
import { Upload, FileText, X, Loader, Download } from 'lucide-react';

const PDFUpload = ({ onDataUpload }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [processingResults, setProcessingResults] = useState(null);
  const [jsFiles, setJsFiles] = useState([]);

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const pdfFiles = selectedFiles.filter(file => file.type === 'application/pdf');
    const jsFilesList = selectedFiles.filter(file => file.name.endsWith('.js'));
    
    if (jsFilesList.length > 0) {
      // Handle JS file upload - now supports multiple files
      setJsFiles(jsFilesList);
      setFiles([]);
      setError('');
      return;
    }
    
    if (pdfFiles.length !== selectedFiles.length) {
      setError('Please select only PDF or JS files');
      return;
    }

    const filesWithMonth = pdfFiles.map((file, index) => ({
      file,
      month: extractMonthFromFilename(file.name) || months[index] || 'Unknown',
      source: detectFileSource(file.name)
    }));

    setFiles(filesWithMonth);
    setError('');
  };

  const detectFileSource = (filename) => {
    const lowerFilename = filename.toLowerCase();
    
    // Check for PayPal patterns
    if (lowerFilename.includes('paypal') || lowerFilename.includes('msr-')) {
      return 'PayPal';
    }
    // Check for Current Account patterns
    else if (lowerFilename.includes('current')) {
      return 'Current Account';
    }
    // Default to Credit Card
    else {
      return 'Credit Card';
    }
  };

  const extractMonthFromFilename = (filename) => {
    // Try to extract month from filename like "2025-01-09_Statement.pdf"
    const monthMatch = filename.match(/\d{4}-(\d{2})-\d{2}/);
    if (monthMatch) {
      const monthNum = parseInt(monthMatch[1]) - 1;
      return months[monthNum];
    }
    
    // Try PayPal format: "L9KVCHMVCLBS4-MSR-20250601000000-20250630235959.PDF"
    const paypalMatch = filename.match(/MSR-\d{4}(\d{2})\d{2}/);
    if (paypalMatch) {
      const monthNum = parseInt(paypalMatch[1]) - 1;
      return months[monthNum];
    }
    
    // Try to find month name in filename
    const lowerFilename = filename.toLowerCase();
    for (const month of months) {
      if (lowerFilename.includes(month.toLowerCase())) {
        return month;
      }
    }
    
    return null;
  };

  const handleRemoveFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleMonthChange = (index, month) => {
    const updatedFiles = [...files];
    updatedFiles[index].month = month;
    setFiles(updatedFiles);
  };

  const handleJsFileUpload = async () => {
    if (!jsFiles || jsFiles.length === 0) return;
    
    setUploading(true);
    setError('');
    setSuccess('');
    
    try {
      let allTransactions = [];
      const fileResults = [];
      
      // Process each JS file
      for (const jsFile of jsFiles) {
        try {
          const content = await jsFile.text();
          
          // Parse the JS file to extract transactions
          const transactionMatch = content.match(/export\s+const\s+transactions\s*=\s*(\[[\s\S]*?\]);/);
          if (!transactionMatch) {
            fileResults.push({ file: jsFile.name, success: false, error: 'Invalid format' });
            continue;
          }
          
          // Use a safer approach to parse the JavaScript array
          let transactionsData;
          try {
            // Try to parse as JSON first (in case it's already valid JSON)
            transactionsData = JSON.parse(transactionMatch[1]);
          } catch (e) {
            // If that fails, use Function constructor with proper sandboxing
            try {
              // eslint-disable-next-line no-new-func
              const parseFunc = new Function('return ' + transactionMatch[1]);
              transactionsData = parseFunc();
              
              // Validate the result
              if (!Array.isArray(transactionsData)) {
                throw new Error('Invalid transactions data: expected an array');
              }
            } catch (funcError) {
              throw new Error('Failed to parse transactions data: ' + funcError.message);
            }
          }
          
          // Add source file information to each transaction
          const transactionsWithSource = transactionsData.map(t => ({
            ...t,
            sourceFile: jsFile.name
          }));
          
          allTransactions = allTransactions.concat(transactionsWithSource);
          fileResults.push({ 
            file: jsFile.name, 
            success: true, 
            count: transactionsData.length 
          });
          
        } catch (fileError) {
          fileResults.push({ 
            file: jsFile.name, 
            success: false, 
            error: fileError.message 
          });
        }
      }
      
      // Remove duplicate transactions based on date, description, and amount
      const uniqueTransactions = [];
      const seen = new Set();
      
      allTransactions.forEach(transaction => {
        const key = `${transaction.date}-${transaction.description}-${transaction.amount}`;
        if (!seen.has(key)) {
          seen.add(key);
          uniqueTransactions.push(transaction);
        }
      });
      
      // Sort transactions by date
      uniqueTransactions.sort((a, b) => new Date(b.date) - new Date(a.date));
      
      // Generate success message
      const successCount = fileResults.filter(r => r.success).length;
      const duplicatesRemoved = allTransactions.length - uniqueTransactions.length;
      
      let successMessage = `Successfully loaded ${uniqueTransactions.length} unique transactions from ${successCount}/${jsFiles.length} file(s)`;
      if (duplicatesRemoved > 0) {
        successMessage += ` (${duplicatesRemoved} duplicates removed)`;
      }
      
      setSuccess(successMessage);
      
      // Show detailed results
      console.log('File processing results:', fileResults);
      
      // Pass transactions to parent component
      if (onDataUpload && uniqueTransactions.length > 0) {
        onDataUpload(uniqueTransactions);
      }
      
      // Clear the files
      setJsFiles([]);
      
    } catch (err) {
      setError(err.message || 'Failed to load JavaScript files');
    } finally {
      setUploading(false);
    }
  };

  const handleUpload = async () => {
    console.log('=== PDF Upload Debug Start ===');
    if (jsFiles && jsFiles.length > 0) {
      return handleJsFileUpload();
    }
    
    if (files.length === 0) {
      setError('Please select at least one PDF file');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      console.log('Creating FormData with files:', files);
      const formData = new FormData();
      
      files.forEach((fileObj, index) => {
        console.log(`Adding file ${index}: ${fileObj.file.name}, month: ${fileObj.month}, size: ${fileObj.file.size} bytes`);
        formData.append('files', fileObj.file);
        formData.append('months', fileObj.month);
      });

      // Use the Render API endpoint
      const apiUrl = process.env.REACT_APP_API_URL || 'https://financecompare.onrender.com';
      console.log('API URL:', apiUrl);
      console.log('Sending request to:', `${apiUrl}/api/parse-pdfs-batch`);
      
      const response = await fetch(`${apiUrl}/api/parse-pdfs-batch`, {
        method: 'POST',
        body: formData
      });
      
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      let data;
      let responseText;
      try {
        responseText = await response.text();
        console.log('Raw response text:', responseText.substring(0, 500)); // First 500 chars
        
        if (!responseText) {
          console.error('Empty response from server');
          throw new Error('Server returned empty response');
        }
        
        data = JSON.parse(responseText);
        console.log('Parsed response data:', {
          hasTransactions: !!data.transactions,
          transactionCount: data.transactions?.length || 0,
          hasSummary: !!data.summary,
          hasJsExport: !!data.js_export,
          errorMessage: data.error
        });
      } catch (jsonError) {
        console.error('Failed to parse response:', jsonError);
        console.error('Response text that failed to parse:', responseText);
        throw new Error('Server returned invalid response. Please check if the API is running.');
      }

      if (!response.ok) {
        console.error('API Error:', response.status, data);
        throw new Error(data.error || `Failed to process PDFs (Error ${response.status})`);
      }

      console.log('Processing complete. Summary:', data.summary);
      
      if (!data.transactions || data.transactions.length === 0) {
        console.warn('No transactions found in response');
        setError('No transactions found in the uploaded PDFs. The PDFs might be empty or in an unsupported format.');
        return;
      }
      
      setProcessingResults(data);
      setSuccess(`Successfully processed ${data.transactions.length} transactions from ${files.length} PDFs`);
      
      // Pass transactions to parent component
      if (onDataUpload) {
        console.log('Passing transactions to parent component');
        onDataUpload(data.transactions);
      }
      
      console.log('=== PDF Upload Debug End (Success) ===');

    } catch (err) {
      console.error('PDF Upload Error:', err);
      console.error('Error stack:', err.stack);
      if (err.message.includes('Failed to fetch')) {
        setError('Unable to connect to the server. Please check if the API is running.');
      } else {
        setError(err.message || 'Failed to process PDFs');
      }
      console.log('=== PDF Upload Debug End (Error) ===');
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadJS = () => {
    if (!processingResults || !processingResults.js_export) return;

    const blob = new Blob([processingResults.js_export], { type: 'text/javascript' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'transactions.js';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Upload Bank Statement PDFs</h2>
      
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        
        <p className="text-gray-600 mb-4">
          Upload your bank statement PDF files for automatic transaction extraction
        </p>
        
        <input
          type="file"
          accept=".pdf,.js,application/javascript,text/javascript,application/x-javascript"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="pdf-upload"
          disabled={uploading}
        />
        
        <label
          htmlFor="pdf-upload"
          className={`inline-block px-6 py-3 ${
            uploading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
          } text-white rounded-lg transition-colors`}
        >
          Choose PDF Files
        </label>
        
        <p className="mt-4 text-sm text-gray-500">
          Supports multiple PDF files or multiple JS transactions files
        </p>
      </div>

      {/* Selected JS Files */}
      {jsFiles.length > 0 && (
        <div className="mt-6">
          <h3 className="font-semibold mb-3">Selected JavaScript Files ({jsFiles.length}):</h3>
          <div className="space-y-2 mb-4">
            {jsFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                <div className="flex items-center space-x-3">
                  <FileText className="w-5 h-5 text-gray-500" />
                  <span className="text-sm">{file.name}</span>
                </div>
                <button
                  onClick={() => {
                    const newFiles = jsFiles.filter((_, i) => i !== index);
                    setJsFiles(newFiles);
                  }}
                  className="text-red-500 hover:text-red-700"
                  disabled={uploading}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
          
          <button
            onClick={handleUpload}
            disabled={uploading}
            className={`w-full py-3 ${
              uploading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-green-600 hover:bg-green-700'
            } text-white rounded-lg transition-colors flex items-center justify-center`}
          >
            {uploading ? (
              <>
                <Loader className="w-5 h-5 mr-2 animate-spin" />
                Processing JavaScript files...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5 mr-2" />
                Combine & Load Transactions
              </>
            )}
          </button>
          
          <p className="mt-2 text-sm text-gray-600 text-center">
            Duplicate transactions will be automatically removed
          </p>
        </div>
      )}

      {/* Selected Files */}
      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="font-semibold mb-3">Selected Files:</h3>
          <div className="space-y-2">
            {files.map((fileObj, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                <div className="flex items-center space-x-3">
                  <FileText className="w-5 h-5 text-gray-500" />
                  <div className="flex flex-col">
                    <span className="text-sm">{fileObj.file.name}</span>
                    <span className="text-xs text-gray-500">Source: {fileObj.source}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <select
                    value={fileObj.month}
                    onChange={(e) => handleMonthChange(index, e.target.value)}
                    className="px-3 py-1 border rounded text-sm"
                    disabled={uploading}
                  >
                    {months.map(month => (
                      <option key={month} value={month}>{month}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="text-red-500 hover:text-red-700"
                    disabled={uploading}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          <button
            onClick={handleUpload}
            disabled={uploading}
            className={`mt-4 w-full py-3 ${
              uploading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-green-600 hover:bg-green-700'
            } text-white rounded-lg transition-colors flex items-center justify-center`}
          >
            {uploading ? (
              <>
                <Loader className="w-5 h-5 mr-2 animate-spin" />
                Processing PDFs...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5 mr-2" />
                Process All PDFs
              </>
            )}
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-100 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mt-4 p-4 bg-green-100 text-green-700 rounded-lg">
          {success}
        </div>
      )}

      {/* Processing Results */}
      {processingResults && processingResults.summary && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold mb-3">Processing Summary:</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-600">Total Transactions</p>
              <p className="text-xl font-bold">{processingResults.summary.transaction_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Spending</p>
              <p className="text-xl font-bold">£{processingResults.summary.total_spending.toFixed(2)}</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium">Categories:</h4>
            {Object.entries(processingResults.summary.categories)
              .sort(([, a], [, b]) => b.amount - a.amount)
              .map(([category, data]) => (
                <div key={category} className="flex justify-between text-sm">
                  <span>{category} ({data.count} transactions)</span>
                  <span className="font-medium">£{data.amount.toFixed(2)}</span>
                </div>
              ))}
          </div>
          
          <button
            onClick={handleDownloadJS}
            className="mt-4 flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Download className="w-4 h-4 mr-2" />
            Download as JavaScript
          </button>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold mb-2">How it works:</h3>
        <ol className="text-sm text-gray-700 space-y-1">
          <li>1. Select your bank statement PDF files</li>
          <li>2. Verify the month for each statement</li>
          <li>3. Click "Process All PDFs" to extract transactions</li>
          <li>4. Transactions will be automatically categorized and displayed</li>
          <li>5. Download the JavaScript file to update your app data</li>
        </ol>
        
        <p className="mt-3 text-sm text-gray-600">
          <strong>Note:</strong> The OCR process uses Google Vision API for accurate text extraction
          from scanned PDFs. Processing may take a few moments depending on file size.
        </p>
      </div>
    </div>
  );
};

export default PDFUpload;