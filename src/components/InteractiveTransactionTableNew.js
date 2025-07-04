import React, { useState } from 'react';
import { format } from 'date-fns';
import { ChevronUp, ChevronDown, X } from 'lucide-react';

const InteractiveTransactionTableNew = ({ transactions, onClose, onUpdateTransaction, onDragStart }) => {
  const [sortField, setSortField] = useState('date');
  const [sortDirection, setSortDirection] = useState('desc');
  const [selectedMonth, setSelectedMonth] = useState('all');
  const [draggedTransaction, setDraggedTransaction] = useState(null);

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
    if (onDragStart) {
      onDragStart(transaction);
    }
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
                <DraggableTransactionRow
                  key={transaction.id}
                  transaction={transaction}
                  onDragStart={handleDragStart}
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

// Draggable Transaction Row Component
const DraggableTransactionRow = ({ transaction, onDragStart, isDragging }) => {
  const [isLongPress, setIsLongPress] = useState(false);
  const [longPressTimer, setLongPressTimer] = useState(null);

  const handleMouseDown = (e) => {
    const timer = setTimeout(() => {
      setIsLongPress(true);
      e.currentTarget.draggable = true;
    }, 500);
    setLongPressTimer(timer);
  };

  const handleMouseUp = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
    setIsLongPress(false);
  };

  const handleMouseLeave = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
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

  const handleDragEnd = () => {
    setIsLongPress(false);
  };

  return (
    <tr
      className={`border-b hover:bg-gray-50 cursor-move transition-all ${
        isDragging ? 'opacity-50' : ''
      } ${isLongPress ? 'bg-blue-50 shadow-lg' : ''}`}
      draggable={isLongPress}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
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
        <span className={transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}>
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

export default InteractiveTransactionTableNew;