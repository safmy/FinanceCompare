import React, { useState } from 'react';
import DroppableCategoryCard from './components/DroppableCategoryCard';
import InteractiveTransactionTable from './components/InteractiveTransactionTableNew';
import CategoryManager from './components/CategoryManager';
import MonthlyTrends from './components/MonthlyTrends';
import BudgetAnalysis from './components/BudgetAnalysis';
import DataUpload from './components/DataUpload';
import PDFUpload from './components/PDFUpload';
import ExportTransactions from './components/ExportTransactions';
import { transactions as sampleTransactions, categoryColors as defaultColors } from './data/currentAccountData';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Calendar, TrendingUp, DollarSign, Upload } from 'lucide-react';

function App() {
  const [transactions, setTransactions] = useState(sampleTransactions);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showCategoryManager, setShowCategoryManager] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState('all');
  const [draggedTransaction, setDraggedTransaction] = useState(null);
  const [categoryColors, setCategoryColors] = useState(defaultColors);

  // Filter transactions by date range
  const filteredTransactions = dateRange === 'all' 
    ? transactions 
    : transactions.filter(t => {
        const transactionDate = new Date(t.date);
        const now = new Date();
        
        switch(dateRange) {
          case '30days':
            return transactionDate >= new Date(now.setDate(now.getDate() - 30));
          case '90days':
            return transactionDate >= new Date(now.setDate(now.getDate() - 90));
          case '6months':
            return transactionDate >= new Date(now.setMonth(now.getMonth() - 6));
          default:
            return true;
        }
      });

  // Calculate spending by category
  const spendingByCategory = filteredTransactions.reduce((acc, transaction) => {
    const category = transaction.category;
    if (!acc[category]) {
      acc[category] = { amount: 0, count: 0, transactions: [] };
    }
    acc[category].amount += Math.abs(transaction.amount);
    acc[category].count += 1;
    acc[category].transactions.push(transaction);
    return acc;
  }, {});

  const totalSpending = Object.values(spendingByCategory).reduce(
    (sum, cat) => sum + cat.amount, 
    0
  );

  // Prepare data for pie chart
  const pieChartData = Object.entries(spendingByCategory)
    .map(([category, data]) => ({
      name: category,
      value: data.amount,
      percentage: ((data.amount / totalSpending) * 100).toFixed(1)
    }))
    .sort((a, b) => b.value - a.value);

  // Calculate summary statistics
  const transactionCount = filteredTransactions.length;
  const avgTransactionAmount = totalSpending / (transactionCount || 1);

  const handleDataUpload = (newTransactions) => {
    setTransactions(newTransactions);
  };

  const handleCategoryUpdate = (update) => {
    switch (update.type) {
      case 'merge':
        // Update all transactions with the source category to the target category
        setTransactions(prev => prev.map(t => 
          t.category === update.source ? { ...t, category: update.target } : t
        ));
        break;
      case 'rename':
        // Rename category for all matching transactions
        setTransactions(prev => prev.map(t => 
          t.category === update.oldName ? { ...t, category: update.newName } : t
        ));
        break;
      case 'delete':
        // Move deleted category transactions to "Other"
        setTransactions(prev => prev.map(t => 
          t.category === update.name ? { ...t, category: 'Other' } : t
        ));
        break;
      case 'create':
        // New category created, no transaction updates needed
        break;
      default:
        break;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Personal Finance Dashboard</h1>
              <p className="text-xs text-gray-500 mt-1">v1.4.1 - Click Amount to Toggle Income/Expense</p>
            </div>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-4 py-2 border rounded-lg bg-white"
            >
              <option value="all">All Time</option>
              <option value="30days">Last 30 Days</option>
              <option value="90days">Last 90 Days</option>
              <option value="6months">Last 6 Months</option>
            </select>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {['overview', 'trends', 'budget', 'upload', 'export'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Spending</p>
                    <p className="text-2xl font-bold text-gray-900">
                      £{totalSpending.toFixed(2)}
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-gray-400" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Transactions</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {transactionCount}
                    </p>
                  </div>
                  <Calendar className="w-8 h-8 text-gray-400" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Avg Transaction</p>
                    <p className="text-2xl font-bold text-gray-900">
                      £{avgTransactionAmount.toFixed(2)}
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-gray-400" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Categories</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {Object.keys(spendingByCategory).length}
                    </p>
                  </div>
                  <Upload className="w-8 h-8 text-gray-400" />
                </div>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Pie Chart */}
              <div className="lg:col-span-1 bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-bold mb-4">Spending Distribution</h2>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ percentage }) => `${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={categoryColors[entry.name] || '#9CA3AF'} 
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `£${value.toFixed(2)}`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Category Cards */}
              <div className="lg:col-span-2">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold">Categories (Click to see transactions)</h2>
                  <button
                    onClick={() => setShowCategoryManager(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                  >
                    Manage Categories
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(spendingByCategory)
                    .sort(([, a], [, b]) => b.amount - a.amount)
                    .map(([category, data]) => (
                      <DroppableCategoryCard
                        key={category}
                        category={category}
                        amount={data.amount}
                        percentage={((data.amount / totalSpending) * 100).toFixed(1)}
                        color={categoryColors[category] || '#9CA3AF'}
                        transactionCount={data.count}
                        onClick={() => setSelectedCategory(category)}
                        onDrop={(targetCategory) => {
                          if (draggedTransaction) {
                            setTransactions(prev => prev.map(t => 
                              t.id === draggedTransaction.id ? { ...t, category: targetCategory } : t
                            ));
                            setDraggedTransaction(null);
                          }
                        }}
                      />
                    ))}
                  {/* Add Create New Category Card */}
                  <DroppableCategoryCard
                    isCreateNew={true}
                    onCreateCategory={(name, color) => {
                      setCategoryColors(prev => ({ ...prev, [name]: color }));
                      if (draggedTransaction) {
                        setTransactions(prev => prev.map(t => 
                          t.id === draggedTransaction.id ? { ...t, category: name } : t
                        ));
                        setDraggedTransaction(null);
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'trends' && (
          <MonthlyTrends transactions={filteredTransactions} />
        )}

        {activeTab === 'budget' && (
          <BudgetAnalysis transactions={filteredTransactions} />
        )}

        {activeTab === 'upload' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <PDFUpload onDataUpload={handleDataUpload} />
            <DataUpload onDataUpload={handleDataUpload} />
          </div>
        )}

        {activeTab === 'export' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">Export Transactions</h2>
            <p className="text-gray-600 mb-6">
              Export your categorized transactions to save your work and re-import later.
            </p>
            
            <div className="mb-6">
              <h3 className="font-semibold mb-2">Summary:</h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600">Total Transactions</p>
                  <p className="text-xl font-bold">{filteredTransactions.length}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600">Categories</p>
                  <p className="text-xl font-bold">{Object.keys(spendingByCategory).length}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600">Date Range</p>
                  <p className="text-xl font-bold">{dateRange === 'all' ? 'All Time' : dateRange}</p>
                </div>
              </div>
            </div>
            
            <ExportTransactions transactions={filteredTransactions} />
            
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold mb-2">How to use exported files:</h3>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• <strong>JS File:</strong> Can be re-imported in the Upload tab to restore your categorized transactions</li>
                <li>• <strong>CSV File:</strong> Can be opened in Excel, Google Sheets, or any spreadsheet application</li>
                <li>• Your categories and changes are preserved in the export</li>
              </ul>
            </div>
          </div>
        )}
      </main>

      {/* Transaction Modal */}
      {selectedCategory && (
        <InteractiveTransactionTable
          transactions={spendingByCategory[selectedCategory].transactions}
          onClose={() => setSelectedCategory(null)}
          onUpdateTransaction={(id, newCategory, newAmount) => {
            // Update the transaction in the main state
            setTransactions(prev => prev.map(t => 
              t.id === id ? { 
                ...t, 
                category: newCategory,
                amount: newAmount !== undefined ? newAmount : t.amount
              } : t
            ));
          }}
          onDragStart={setDraggedTransaction}
        />
      )}

      {/* Category Manager Modal */}
      {showCategoryManager && (
        <CategoryManager
          transactions={filteredTransactions}
          onClose={() => setShowCategoryManager(false)}
          onUpdateCategories={handleCategoryUpdate}
        />
      )}
    </div>
  );
}

export default App;