import React, { useState } from 'react';
import CategoryCard from './components/CategoryCard';
import TransactionTable from './components/TransactionTable';
import MonthlyTrends from './components/MonthlyTrends';
import BudgetAnalysis from './components/BudgetAnalysis';
import DataUpload from './components/DataUpload';
import PDFUpload from './components/PDFUpload';
import { transactions as sampleTransactions, categoryColors } from './data/currentAccountData';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Calendar, TrendingUp, DollarSign, Upload } from 'lucide-react';

function App() {
  const [transactions, setTransactions] = useState(sampleTransactions);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState('all');

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

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">Personal Finance Dashboard</h1>
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
            {['overview', 'trends', 'budget', 'upload'].map((tab) => (
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
                <h2 className="text-xl font-bold mb-4">Categories (Click to see transactions)</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(spendingByCategory)
                    .sort(([, a], [, b]) => b.amount - a.amount)
                    .map(([category, data]) => (
                      <CategoryCard
                        key={category}
                        category={category}
                        amount={data.amount}
                        percentage={((data.amount / totalSpending) * 100).toFixed(1)}
                        color={categoryColors[category] || '#9CA3AF'}
                        transactionCount={data.count}
                        onClick={() => setSelectedCategory(category)}
                      />
                    ))}
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
      </main>

      {/* Transaction Modal */}
      {selectedCategory && (
        <TransactionTable
          transactions={spendingByCategory[selectedCategory].transactions}
          onClose={() => setSelectedCategory(null)}
        />
      )}
    </div>
  );
}

export default App;