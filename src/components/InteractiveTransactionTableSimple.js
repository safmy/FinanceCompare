import React, { useState } from 'react';
import { format } from 'date-fns';
import { ChevronUp, ChevronDown, X, Check } from 'lucide-react';
import '../styles/animations.css';

const InteractiveTransactionTableSimple = ({ 
  transactions, 
  onClose, 
  onUpdateTransaction, 
  availableCategories = [
    'Income', 'Rent', 'Bills & Utilities', 'Groceries', 'Restaurants', 
    'Fast Food', 'Food Delivery', 'Coffee Shops', 'Transport', 'Fuel', 
    'Parking', 'Shopping', 'Subscriptions', 'Financial Services', 
    'Entertainment', 'Healthcare', 'Personal Care', 'Other'
  ],
  categoryColors = {
    'Income': '#10b981',
    'Rent': '#dc2626',
    'Bills & Utilities': '#7c3aed',
    'Groceries': '#f59e0b',
    'Restaurants': '#ec4899',
    'Fast Food': '#f97316',
    'Food Delivery': '#d946ef',
    'Coffee Shops': '#8b5cf6',
    'Transport': '#3b82f6',
    'Fuel': '#06b6d4',
    'Parking': '#0ea5e9',
    'Shopping': '#6366f1',
    'Subscriptions': '#a855f7',
    'Financial Services': '#84cc16',
    'Entertainment': '#f43f5e',
    'Healthcare': '#14b8a6',
    'Personal Care': '#fb923c',
    'Other': '#6b7280'
  }
}) => {
  const [sortField, setSortField] = useState('date');
  const [sortDirection, setSortDirection] = useState('desc');
  const [selectedMonth, setSelectedMonth] = useState('all');
  const [editingCategoryId, setEditingCategoryId] = useState(null);

  const months = ['all', ...new Set(transactions.map(t => t.month))];

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleClickOutside = (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
      onClose();
    }
  };

  const handleAmountToggle = (transaction) => {
    const newAmount = -transaction.amount;
    const newCategory = newAmount > 0 ? 'Income' : transaction.category === 'Income' ? 'Other' : transaction.category;
    onUpdateTransaction(transaction.id, newCategory, newAmount);
  };

  const handleCategoryClick = (transactionId) => {
    setEditingCategoryId(editingCategoryId === transactionId ? null : transactionId);
  };

  const handleCategorySelect = (transactionId, newCategory) => {
    onUpdateTransaction(transactionId, newCategory);
    setEditingCategoryId(null);
  };

  const filteredTransactions = selectedMonth === 'all' 
    ? transactions 
    : transactions.filter(t => t.month === selectedMonth);

  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    const aValue = sortField === 'date' ? new Date(a.date) : a[sortField];
    const bValue = sortField === 'date' ? new Date(b.date) : b[sortField];
    
    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const monthlyTotals = transactions.reduce((acc, t) => {
    if (!acc[t.month]) acc[t.month] = 0;
    acc[t.month] += t.amount;
    return acc;
  }, {});

  return (
    <div 
      className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50 modal-backdrop"
      onClick={handleClickOutside}
    >
      <div className="bg-white rounded-lg shadow-xl w-[90%] max-w-6xl h-[85vh] flex flex-col">
        <div className="p-6 border-b flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Transaction Details</h2>
            <p className="text-sm text-gray-600 mt-1">
              Click amounts to toggle income/expense • Click categories to change them
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-4 border-b flex justify-between items-center">
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {months.map(month => (
              <option key={month} value={month}>
                {month === 'all' ? 'All Months' : month}
              </option>
            ))}
          </select>
          
          <div className="text-sm text-gray-600">
            Showing {sortedTransactions.length} transactions
          </div>
        </div>

        <div className="overflow-auto flex-1">
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th 
                  className="px-6 py-3 text-left cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => handleSort('date')}
                >
                  <div className="flex items-center">
                    Date
                    {sortField === 'date' && (
                      sortDirection === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left">Description</th>
                <th 
                  className="px-6 py-3 text-right cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => handleSort('amount')}
                >
                  <div className="flex items-center justify-end">
                    Amount
                    {sortField === 'amount' && (
                      sortDirection === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left">Category</th>
              </tr>
            </thead>
            <tbody>
              {sortedTransactions.map((transaction) => (
                <tr key={transaction.id} className="border-b hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {transaction.date ? (
                      (() => {
                        try {
                          return format(new Date(transaction.date), 'dd MMM yyyy');
                        } catch (e) {
                          return transaction.date;
                        }
                      })()
                    ) : 'No date'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-xs truncate" title={transaction.description}>
                      {transaction.description}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-right">
                    <button
                      className={`${
                        transaction.amount < 0 ? 'text-red-600 hover:bg-red-50' : 'text-green-600 hover:bg-green-50'
                      } px-3 py-1 rounded-md transition-all hover:scale-105 active:scale-95`}
                      onClick={() => handleAmountToggle(transaction)}
                      title="Click to toggle between income/expense"
                    >
                      {transaction.amount < 0 ? '-' : '+'}£{Math.abs(transaction.amount).toFixed(2)}
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="relative">
                      <button
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-all hover:scale-105 active:scale-95 ${
                          editingCategoryId === transaction.id
                            ? 'ring-2 ring-blue-500'
                            : 'hover:ring-2 hover:ring-gray-300'
                        }`}
                        style={{
                          backgroundColor: `${categoryColors[transaction.category]}20`,
                          color: categoryColors[transaction.category]
                        }}
                        onClick={() => handleCategoryClick(transaction.id)}
                      >
                        {transaction.category}
                      </button>
                      
                      {editingCategoryId === transaction.id && (
                        <div className="absolute z-20 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 max-h-64 overflow-y-auto category-dropdown">
                          {availableCategories.map(category => (
                            <button
                              key={category}
                              className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 transition-colors flex items-center justify-between ${
                                category === transaction.category ? 'bg-blue-50' : ''
                              }`}
                              onClick={() => handleCategorySelect(transaction.id, category)}
                            >
                              <span className="flex items-center">
                                <span
                                  className="w-3 h-3 rounded-full mr-2"
                                  style={{ backgroundColor: categoryColors[category] }}
                                />
                                {category}
                              </span>
                              {category === transaction.category && (
                                <Check className="w-4 h-4 text-blue-600" />
                              )}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-4 border-t bg-gray-50">
          <div className="flex justify-between items-center">
            <span className="font-semibold">Total:</span>
            <span className={`text-xl font-bold ${
              sortedTransactions.reduce((sum, t) => sum + t.amount, 0) < 0 ? 'text-red-600' : 'text-green-600'
            }`}>
              £{Math.abs(sortedTransactions.reduce((sum, t) => sum + t.amount, 0)).toFixed(2)}
            </span>
          </div>
          {selectedMonth !== 'all' && Object.keys(monthlyTotals).length > 0 && (
            <div className="mt-2 text-sm text-gray-600">
              Monthly breakdown: {Object.entries(monthlyTotals).map(([month, total]) => (
                <span key={month} className="ml-2">
                  {month}: £{Math.abs(total).toFixed(2)}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InteractiveTransactionTableSimple;