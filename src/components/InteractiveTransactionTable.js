import React, { useState } from 'react';
import { format } from 'date-fns';
import { ChevronUp, ChevronDown, Edit2, Check, X } from 'lucide-react';
import DraggableTransaction from './DraggableTransaction';

const InteractiveTransactionTable = ({ transactions, onClose, onUpdateTransaction, onDragStart }) => {
  const [sortField, setSortField] = useState('date');
  const [sortDirection, setSortDirection] = useState('desc');
  const [selectedMonth, setSelectedMonth] = useState('all');
  const [editingId, setEditingId] = useState(null);
  const [editCategory, setEditCategory] = useState('');
  const [localTransactions, setLocalTransactions] = useState(transactions);

  const months = ['all', ...new Set(transactions.map(t => t.month))];
  
  const categories = [
    'Income', 'Rent', 'Bills & Utilities', 'Groceries', 'Restaurants', 
    'Fast Food', 'Food Delivery', 'Coffee Shops', 'Transport', 'Fuel', 
    'Parking', 'Shopping', 'Subscriptions', 'Financial Services', 
    'Entertainment', 'Healthcare', 'Personal Care', 'Other'
  ];

  const categoryColors = {
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
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleEditCategory = (transaction) => {
    setEditingId(transaction.id);
    setEditCategory(transaction.category);
  };

  const handleSaveCategory = async (transaction) => {
    // Update local state
    const updatedTransactions = localTransactions.map(t => 
      t.id === transaction.id ? { ...t, category: editCategory } : t
    );
    setLocalTransactions(updatedTransactions);
    
    // Call parent update function if provided
    if (onUpdateTransaction) {
      onUpdateTransaction(transaction.id, editCategory);
    }
    
    // Call API to update category
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/update-category`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: transaction.id,
          category: editCategory
        })
      });
      
      if (!response.ok) {
        console.error('Failed to update category');
      }
    } catch (error) {
      console.error('Error updating category:', error);
    }
    
    setEditingId(null);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditCategory('');
  };

  const filteredTransactions = selectedMonth === 'all' 
    ? localTransactions 
    : localTransactions.filter(t => t.month === selectedMonth);

  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    if (sortField === 'date') {
      aValue = new Date(aValue);
      bValue = new Date(bValue);
    }
    
    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    }
    return aValue < bValue ? 1 : -1;
  });

  const monthlyTotals = filteredTransactions.reduce((acc, t) => {
    acc[t.month] = (acc[t.month] || 0) + t.amount;
    return acc;
  }, {});

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b flex justify-between items-center">
          <h2 className="text-2xl font-bold">Transaction Details</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        
        <div className="p-4 border-b flex items-center space-x-4">
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="px-4 py-2 border rounded-lg"
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

        <div className="overflow-auto max-h-[60vh]">
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th 
                  className="px-6 py-3 text-left cursor-pointer hover:bg-gray-100"
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
                <th className="px-6 py-3 text-left">Category</th>
                <th className="px-6 py-3 text-left">Source</th>
                <th 
                  className="px-6 py-3 text-right cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('amount')}
                >
                  <div className="flex items-center justify-end">
                    Amount
                    {sortField === 'amount' && (
                      sortDirection === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
                    )}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedTransactions.map((transaction) => (
                <tr key={transaction.id} className="border-b hover:bg-gray-50">
                  <td className="px-6 py-4">
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
                  <td className="px-6 py-4">{transaction.description}</td>
                  <td className="px-6 py-4">
                    {editingId === transaction.id ? (
                      <div className="flex items-center space-x-2">
                        <select
                          value={editCategory}
                          onChange={(e) => setEditCategory(e.target.value)}
                          className="px-2 py-1 border rounded text-sm"
                          autoFocus
                        >
                          {categories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => handleSaveCategory(transaction)}
                          className="p-1 text-green-600 hover:bg-green-100 rounded"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="p-1 text-red-600 hover:bg-red-100 rounded"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <span 
                          className="px-2 py-1 rounded text-xs font-medium"
                          style={{
                            backgroundColor: `${categoryColors[transaction.category]}20`,
                            color: categoryColors[transaction.category]
                          }}
                        >
                          {transaction.category}
                        </span>
                        <button
                          onClick={() => handleEditCategory(transaction)}
                          className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {transaction.source || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 text-right font-medium">
                    <span className={transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}>
                      £{Math.abs(transaction.amount).toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-4 border-t bg-gray-50">
          <div className="flex justify-between items-center">
            <span className="font-semibold">Total:</span>
            <span className="text-xl font-bold text-red-600">
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

export default InteractiveTransactionTable;