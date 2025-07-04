import React from 'react';
import { format } from 'date-fns';

const TransactionList = ({ transactions, onUpdateTransaction }) => {
  const handleAmountClick = (transaction, e) => {
    e.stopPropagation();
    // Toggle amount sign and update category
    const newAmount = -transaction.amount;
    const newCategory = newAmount > 0 ? 'Income' : transaction.category === 'Income' ? 'Other' : transaction.category;
    onUpdateTransaction(transaction.id, newCategory, newAmount);
  };

  return (
    <div className="space-y-2">
      {transactions.map((transaction) => (
        <div 
          key={transaction.id} 
          className="flex items-center justify-between p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="flex-1">
            <div className="text-sm font-medium text-gray-900">
              {transaction.description}
            </div>
            <div className="text-xs text-gray-500">
              {transaction.date ? (
                (() => {
                  try {
                    return format(new Date(transaction.date), 'dd MMM yyyy');
                  } catch (e) {
                    return transaction.date;
                  }
                })()
              ) : 'No date'}
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <span className="text-xs px-2 py-1 rounded-full bg-gray-100">
              {transaction.category}
            </span>
            
            <span 
              className={`font-medium cursor-pointer hover:bg-gray-100 px-2 py-1 rounded transition-all ${
                transaction.amount < 0 ? 'text-red-600' : 'text-green-600'
              }`}
              onClick={(e) => handleAmountClick(transaction, e)}
              title="Click to toggle income/expense"
            >
              {transaction.amount < 0 ? '-' : '+'}£{Math.abs(transaction.amount).toFixed(2)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TransactionList;