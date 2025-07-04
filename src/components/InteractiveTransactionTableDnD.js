import React, { useState, useRef } from 'react';
import { format } from 'date-fns';
import { ChevronUp, ChevronDown, X } from 'lucide-react';

const InteractiveTransactionTableDnD = ({ 
  transactions, 
  onClose, 
  onUpdateTransaction, 
  onDragStart,
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
  const [draggedTransaction, setDraggedTransaction] = useState(null);
  const [showCategoryDropZone, setShowCategoryDropZone] = useState(false);

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

  const handleDragStart = (transaction) => {
    setDraggedTransaction(transaction);
    setShowCategoryDropZone(true);
    if (onDragStart) {
      onDragStart(transaction);
    }
  };

  const handleDragEnd = () => {
    setDraggedTransaction(null);
    setShowCategoryDropZone(false);
  };

  const handleCategoryDrop = (category) => {
    if (draggedTransaction) {
      onUpdateTransaction(draggedTransaction.id, category);
      setDraggedTransaction(null);
      setShowCategoryDropZone(false);
    }
  };

  const handleAmountToggle = (transaction) => {
    const newAmount = -transaction.amount;
    const newCategory = newAmount > 0 ? 'Income' : transaction.category === 'Income' ? 'Other' : transaction.category;
    onUpdateTransaction(transaction.id, newCategory, newAmount);
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
      <div className="bg-white rounded-lg shadow-xl w-[90%] max-w-6xl h-[85vh] flex flex-col relative">
        {/* Category Drop Zone - Shows when dragging */}
        {showCategoryDropZone && (
          <div className="absolute inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">Drop transaction into a category:</h3>
              <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
                {availableCategories.map(category => (
                  <CategoryDropZone
                    key={category}
                    category={category}
                    color={categoryColors[category]}
                    onDrop={() => handleCategoryDrop(category)}
                    isDragging={!!draggedTransaction}
                  />
                ))}
              </div>
              <button
                onClick={handleDragEnd}
                className="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="p-6 border-b flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Transaction Details</h2>
            <p className="text-sm text-gray-600 mt-1">
              Long press and drag transactions to different categories to re-categorize them
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-4 border-b flex justify-between items-center">
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

        <div className="overflow-auto flex-1">
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
                <th className="px-6 py-3 text-left">Category</th>
              </tr>
            </thead>
            <tbody>
              {sortedTransactions.map((transaction) => (
                <DraggableRow
                  key={transaction.id}
                  transaction={transaction}
                  onDragStart={handleDragStart}
                  onDragEnd={handleDragEnd}
                  onAmountClick={handleAmountToggle}
                  isDragging={draggedTransaction?.id === transaction.id}
                />
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

// Draggable Row Component
const DraggableRow = ({ transaction, onDragStart, onDragEnd, onAmountClick, isDragging }) => {
  const rowRef = useRef(null);
  const [isLongPress, setIsLongPress] = useState(false);
  const longPressTimer = useRef(null);

  const handleMouseDown = (e) => {
    longPressTimer.current = setTimeout(() => {
      setIsLongPress(true);
      if (rowRef.current) {
        rowRef.current.draggable = true;
      }
    }, 500);
  };

  const handleMouseUp = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    if (rowRef.current) {
      rowRef.current.draggable = false;
    }
    setIsLongPress(false);
  };

  const handleMouseLeave = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    if (rowRef.current) {
      rowRef.current.draggable = false;
    }
    setIsLongPress(false);
  };

  const handleDragStart = (e) => {
    if (!isLongPress) {
      e.preventDefault();
      return;
    }
    onDragStart(transaction);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragEndLocal = () => {
    setIsLongPress(false);
    if (rowRef.current) {
      rowRef.current.draggable = false;
    }
    onDragEnd();
  };

  const handleAmountClick = (e) => {
    e.stopPropagation();
    if (!isLongPress) {
      onAmountClick(transaction);
    }
  };

  // Touch events for mobile
  const handleTouchStart = (e) => {
    longPressTimer.current = setTimeout(() => {
      setIsLongPress(true);
      onDragStart(transaction);
    }, 500);
  };

  const handleTouchEnd = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
    if (isLongPress) {
      onDragEnd();
    }
    setIsLongPress(false);
  };

  return (
    <tr
      ref={rowRef}
      className={`border-b hover:bg-gray-50 cursor-move transition-all ${
        isDragging ? 'opacity-50' : ''
      } ${isLongPress ? 'bg-blue-50 shadow-lg transform scale-105' : ''}`}
      draggable={false}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEndLocal}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
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
        <span 
          className={`${transaction.amount < 0 ? 'text-red-600' : 'text-green-600'} cursor-pointer hover:bg-gray-100 px-2 py-1 rounded transition-colors`}
          onClick={handleAmountClick}
          title="Click to toggle between income/expense"
        >
          {transaction.amount < 0 ? '-' : '+'}£{Math.abs(transaction.amount).toFixed(2)}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        <span className="px-2 py-1 text-xs rounded-full bg-gray-100">
          {transaction.category}
        </span>
      </td>
    </tr>
  );
};

// Category Drop Zone Component
const CategoryDropZone = ({ category, color, onDrop, isDragging }) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    onDrop();
  };

  return (
    <div
      className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
        isDragOver 
          ? 'border-blue-500 bg-blue-50 transform scale-105' 
          : 'border-gray-300 hover:border-gray-400'
      }`}
      style={{ borderLeftWidth: '4px', borderLeftColor: color }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={onDrop}
    >
      <div className="text-sm font-medium text-gray-900">{category}</div>
      {isDragOver && (
        <div className="text-xs text-blue-600 mt-1">Drop here</div>
      )}
    </div>
  );
};

export default InteractiveTransactionTableDnD;