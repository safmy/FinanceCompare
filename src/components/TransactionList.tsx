import React, { useState } from 'react';
import { Transaction } from '../types';
import { format } from 'date-fns';
import './TransactionList.css';

interface TransactionListProps {
  transactions: Transaction[];
}

const TransactionList: React.FC<TransactionListProps> = ({ transactions }) => {
  const [filter, setFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'amount'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const filteredTransactions = transactions.filter(transaction => {
    if (filter === 'all') return true;
    return transaction.category === filter;
  });

  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    if (sortBy === 'date') {
      return sortOrder === 'asc' 
        ? a.date.getTime() - b.date.getTime()
        : b.date.getTime() - a.date.getTime();
    } else {
      return sortOrder === 'asc' 
        ? a.amount - b.amount
        : b.amount - a.amount;
    }
  });

  const categories = ['all', ...new Set(transactions.map(t => t.category).filter(Boolean))];

  return (
    <div className="transaction-list">
      <h2>Transactions</h2>
      
      <div className="controls">
        <select 
          value={filter} 
          onChange={(e) => setFilter(e.target.value)}
          className="filter-select"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>
              {cat === 'all' ? 'All Categories' : cat}
            </option>
          ))}
        </select>
        
        <div className="sort-controls">
          <button
            className={`sort-btn ${sortBy === 'date' ? 'active' : ''}`}
            onClick={() => {
              if (sortBy === 'date') {
                setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
              } else {
                setSortBy('date');
                setSortOrder('desc');
              }
            }}
          >
            Date {sortBy === 'date' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
          <button
            className={`sort-btn ${sortBy === 'amount' ? 'active' : ''}`}
            onClick={() => {
              if (sortBy === 'amount') {
                setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
              } else {
                setSortBy('amount');
                setSortOrder('desc');
              }
            }}
          >
            Amount {sortBy === 'amount' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
        </div>
      </div>

      <div className="transaction-table">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Category</th>
              <th>Amount</th>
              <th>Balance</th>
            </tr>
          </thead>
          <tbody>
            {sortedTransactions.map(transaction => (
              <tr key={transaction.id} className={transaction.type}>
                <td>{format(transaction.date, 'MMM dd, yyyy')}</td>
                <td>
                  <div className="description">
                    <span className="merchant">{transaction.merchant || transaction.description}</span>
                    {transaction.merchant && (
                      <span className="original">{transaction.description}</span>
                    )}
                  </div>
                </td>
                <td>
                  <span className={`category-badge ${transaction.category?.toLowerCase().replace(/[^a-z]/g, '-')}`}>
                    {transaction.category || 'Uncategorized'}
                  </span>
                </td>
                <td className={`amount ${transaction.type}`}>
                  {transaction.type === 'credit' ? '+' : '-'}
                  ${Math.abs(transaction.amount).toFixed(2)}
                </td>
                <td className="balance">
                  {transaction.balance ? `$${transaction.balance.toFixed(2)}` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TransactionList;