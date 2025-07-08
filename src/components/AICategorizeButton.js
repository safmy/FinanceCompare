import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';

const AICategorizeButton = ({ 
  category, 
  transactionCount, 
  transactions, 
  onRecategorize,
  categoryColors 
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleRecategorize = async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('https://financecompare-backend.onrender.com/api/recategorize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: category,
          transactions: transactions
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to recategorize');
      }

      const data = await response.json();
      
      if (data.recategorized && data.recategorized.length > 0) {
        // Apply the recategorizations
        onRecategorize(data.recategorized);
        setSuccess(`Successfully recategorized ${data.updated} of ${data.total} transactions`);
      } else {
        setSuccess('No better categorizations found');
      }
    } catch (err) {
      setError('Failed to recategorize. Please try again.');
      console.error('Recategorization error:', err);
    } finally {
      setIsLoading(false);
      // Clear messages after 3 seconds
      setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 3000);
    }
  };

  // Only show button for categories with multiple transactions
  if (transactionCount < 2 || category === 'Income') {
    return null;
  }

  return (
    <div className="mt-2">
      <button
        onClick={handleRecategorize}
        disabled={isLoading}
        className={`w-full px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center justify-center gap-2 ${
          isLoading
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-blue-50 text-blue-600 hover:bg-blue-100 active:scale-95'
        }`}
        title="Use AI to find better categories for these transactions"
      >
        <RefreshCw 
          className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} 
        />
        {isLoading ? 'Analyzing...' : 'AI Re-categorize'}
      </button>
      
      {error && (
        <div className="mt-2 p-2 bg-red-50 text-red-600 text-xs rounded">
          {error}
        </div>
      )}
      
      {success && (
        <div className="mt-2 p-2 bg-green-50 text-green-600 text-xs rounded">
          {success}
        </div>
      )}
    </div>
  );
};

export default AICategorizeButton;