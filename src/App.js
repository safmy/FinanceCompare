import React, { useState } from 'react';
import DroppableCategoryCard from './components/DroppableCategoryCard';
import InteractiveTransactionTable from './components/InteractiveTransactionTableSimple';
import CategoryManager from './components/CategoryManager';
import MonthlyTrends from './components/MonthlyTrends';
import BudgetAnalysis from './components/BudgetAnalysis';
import DataUpload from './components/DataUpload';
import PDFUpload from './components/PDFUpload';
import ExportTransactions from './components/ExportTransactions';
import { transactions as sampleTransactions, categoryColors as defaultColors } from './data/currentAccountData';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Calendar, TrendingUp, DollarSign, Upload, Search } from 'lucide-react';

function App() {
  const [transactions, setTransactions] = useState(sampleTransactions);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showCategoryManager, setShowCategoryManager] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState('all');
  const [draggedTransaction, setDraggedTransaction] = useState(null);
  const [categoryColors, setCategoryColors] = useState(defaultColors);
  const [searchTerm, setSearchTerm] = useState('');

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

  // Calculate income, expenses, and net separately
  const income = filteredTransactions
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);
  
  const expenses = filteredTransactions
    .filter(t => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);
  
  const netAmount = income - expenses;
  
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

  const handleDataUpload = (newTransactions) => {
    // Extract unique categories from new transactions
    const newCategories = [...new Set(newTransactions.map(t => t.category).filter(Boolean))];
    
    // Create a diverse color palette for new categories
    const colorPalette = [
      '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
      '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
      '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
      '#ec4899', '#f43f5e', '#be123c', '#7c2d12', '#166534'
    ];
    
    // Add any new categories that don't exist in current categoryColors
    const updatedColors = { ...categoryColors };
    let colorIndex = 0;
    
    newCategories.forEach(category => {
      if (!updatedColors[category] && category) {
        // Assign colors in sequence for better distribution
        updatedColors[category] = colorPalette[colorIndex % colorPalette.length];
        colorIndex++;
      }
    });
    
    console.log('Categories found in uploaded data:', newCategories);
    console.log('Updated category colors:', updatedColors);
    
    setCategoryColors(updatedColors);
    setTransactions(newTransactions);
    
    // Show success message with category info
    const categoryCount = Object.keys(updatedColors).length;
    console.log(`Loaded ${newTransactions.length} transactions with ${newCategories.length} categories (${categoryCount} total categories)`);
  };

  const handleRecategorize = (recategorizations) => {
    // Apply recategorizations to transactions
    setTransactions(prev => {
      const updated = [...prev];
      recategorizations.forEach(recat => {
        const idx = updated.findIndex(t => t.id === recat.id);
        if (idx !== -1) {
          updated[idx] = { ...updated[idx], category: recat.newCategory };
        }
      });
      return updated;
    });
  };

  const handleCategoryUpdate = (update) => {
    switch (update.type) {
      case 'merge':
        // Update all transactions with the source category to the target category
        setTransactions(prev => prev.map(t => 
          t.category === update.source ? { ...t, category: update.target } : t
        ));
        // Remove the source category color
        setCategoryColors(prev => {
          const newColors = { ...prev };
          delete newColors[update.source];
          return newColors;
        });
        break;
      case 'rename':
        // Rename category for all matching transactions
        setTransactions(prev => prev.map(t => 
          t.category === update.oldName ? { ...t, category: update.newName } : t
        ));
        // Update category color mapping
        setCategoryColors(prev => {
          const newColors = { ...prev };
          if (prev[update.oldName]) {
            newColors[update.newName] = prev[update.oldName];
            delete newColors[update.oldName];
          }
          return newColors;
        });
        break;
      case 'delete':
        // Move deleted category transactions to "Other"
        setTransactions(prev => prev.map(t => 
          t.category === update.name ? { ...t, category: 'Other' } : t
        ));
        // Remove the category color
        setCategoryColors(prev => {
          const newColors = { ...prev };
          delete newColors[update.name];
          return newColors;
        });
        break;
      case 'create':
        // Add new category color
        setCategoryColors(prev => ({ ...prev, [update.name]: update.color }));
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
              <p className="text-xs text-gray-500 mt-1">v1.5.0 - Enhanced Search, Income/Expense Tracking & Category Controls</p>
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
                    <p className="text-sm text-gray-600">Income</p>
                    <p className="text-2xl font-bold text-green-600">
                      +£{income.toFixed(2)}
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-400" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Expenses</p>
                    <p className="text-2xl font-bold text-red-600">
                      -£{expenses.toFixed(2)}
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-red-400" />
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Net Balance</p>
                    <p className={`text-2xl font-bold ${netAmount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {netAmount >= 0 ? '+' : ''}£{netAmount.toFixed(2)}
                    </p>
                  </div>
                  <Calendar className="w-8 h-8 text-gray-400" />
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
                
                {/* Search Bar */}
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      type="text"
                      placeholder="Search categories or transactions..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(spendingByCategory)
                    .filter(([category, data]) => {
                      if (!searchTerm) return true;
                      const searchLower = searchTerm.toLowerCase();
                      // Search in category name
                      if (category.toLowerCase().includes(searchLower)) return true;
                      // Search in transaction descriptions
                      return data.transactions.some(t => 
                        t.description.toLowerCase().includes(searchLower)
                      );
                    })
                    .sort(([, a], [, b]) => b.amount - a.amount)
                    .map(([category, data]) => (
                      <DroppableCategoryCard
                        key={category}
                        category={category}
                        amount={data.amount}
                        percentage={((data.amount / totalSpending) * 100).toFixed(1)}
                        color={categoryColors[category] || '#9CA3AF'}
                        transactionCount={data.count}
                        transactions={data.transactions}
                        onClick={() => setSelectedCategory(category)}
                        onDrop={(targetCategory) => {
                          if (draggedTransaction) {
                            setTransactions(prev => prev.map(t => 
                              t.id === draggedTransaction.id ? { ...t, category: targetCategory } : t
                            ));
                            setDraggedTransaction(null);
                          }
                        }}
                        onRecategorize={handleRecategorize}
                      />
                    ))}
                  {/* Add Create New Category Card */}
                  <DroppableCategoryCard
                    isCreateNew={true}
                    onCreateCategory={(name, color) => {
                      // Add the new category color
                      setCategoryColors(prev => {
                        const updated = { ...prev, [name]: color };
                        console.log('Created new category:', name, 'with color:', color);
                        return updated;
                      });
                      
                      // If there's a dragged transaction, assign it to the new category
                      if (draggedTransaction) {
                        setTransactions(prev => prev.map(t => 
                          t.id === draggedTransaction.id ? { ...t, category: name } : t
                        ));
                        setDraggedTransaction(null);
                      }
                      
                      // Force re-render to show the new category immediately
                      setTimeout(() => {
                        setDateRange(prev => prev); // Trigger a state update
                      }, 100);
                    }}
                  />
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'trends' && (
          <MonthlyTrends transactions={filteredTransactions} categoryColors={categoryColors} />
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
      {selectedCategory && spendingByCategory[selectedCategory] && (
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
            
            // Close modal if all transactions moved out of current category
            if (spendingByCategory[selectedCategory]?.transactions.length === 1) {
              const lastTransaction = spendingByCategory[selectedCategory].transactions.find(t => t.id === id);
              if (lastTransaction && lastTransaction.category !== newCategory) {
                setSelectedCategory(null);
              }
            }
          }}
          availableCategories={Object.keys(categoryColors)}
          categoryColors={categoryColors}
        />
      )}

      {/* Category Manager Modal */}
      {showCategoryManager && (
        <CategoryManager
          transactions={filteredTransactions}
          categoryColors={categoryColors}
          onClose={() => setShowCategoryManager(false)}
          onUpdateCategories={handleCategoryUpdate}
        />
      )}
    </div>
  );
}

export default App;