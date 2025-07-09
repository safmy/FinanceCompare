import React, { useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const MonthlyTrends = ({ transactions, categoryColors = {} }) => {
  const categories = [...new Set(transactions.map(t => t.category))];
  const [selectedCategories, setSelectedCategories] = useState(categories);
  const [showCategorySelector, setShowCategorySelector] = useState(false);
  // Filter transactions by selected categories
  const filteredTransactions = selectedCategories.length === categories.length 
    ? transactions 
    : transactions.filter(t => selectedCategories.includes(t.category));
  
  // Process data for monthly spending by category
  const monthlyData = filteredTransactions.reduce((acc, transaction) => {
    const month = transaction.month;
    if (!acc[month]) {
      acc[month] = { month, total: 0 };
    }
    
    const category = transaction.category;
    if (!acc[month][category]) {
      acc[month][category] = 0;
    }
    
    acc[month][category] += Math.abs(transaction.amount);
    acc[month].total += Math.abs(transaction.amount);
    
    return acc;
  }, {});

  const chartData = Object.values(monthlyData);
  
  const toggleCategory = (category) => {
    setSelectedCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };
  
  const selectAllCategories = () => {
    setSelectedCategories(categories);
  };
  
  const deselectAllCategories = () => {
    setSelectedCategories([]);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Monthly Spending Trends</h2>
        <button
          onClick={() => setShowCategorySelector(!showCategorySelector)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          {showCategorySelector ? 'Hide' : 'Select'} Categories ({selectedCategories.length}/{categories.length})
        </button>
      </div>
      
      {/* Category Selector */}
      {showCategorySelector && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold">Select Categories to Display</h3>
            <div className="space-x-2">
              <button
                onClick={selectAllCategories}
                className="text-sm text-blue-600 hover:underline"
              >
                Select All
              </button>
              <button
                onClick={deselectAllCategories}
                className="text-sm text-blue-600 hover:underline"
              >
                Deselect All
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {categories.map(category => (
              <button
                key={category}
                onClick={() => toggleCategory(category)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedCategories.includes(category)
                    ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-500'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
                style={{
                  borderLeft: `4px solid ${categoryColors[category] || '#9CA3AF'}`
                }}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Total Spending Trend */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Total Monthly Spending</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => `£${value.toFixed(2)}`} />
              <Line 
                type="monotone" 
                dataKey="total" 
                stroke="#3B82F6" 
                strokeWidth={2}
                dot={{ fill: '#3B82F6', r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Category Breakdown */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Spending by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => `£${value.toFixed(2)}`} />
              <Legend />
              {selectedCategories.slice(0, 8).map((category) => (
                <Bar 
                  key={category}
                  dataKey={category} 
                  stackId="a"
                  fill={categoryColors[category] || '#9CA3AF'} 
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Summary Table */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-4">Monthly Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Month</th>
                <th className="text-right py-2">Total Spent</th>
                <th className="text-right py-2">Transactions</th>
                <th className="text-right py-2">Avg Transaction</th>
              </tr>
            </thead>
            <tbody>
              {chartData.map((monthData) => {
                const monthTransactions = filteredTransactions.filter(t => t.month === monthData.month);
                const avgTransaction = monthData.total / monthTransactions.length;
                
                return (
                  <tr key={monthData.month} className="border-b">
                    <td className="py-2">{monthData.month}</td>
                    <td className="text-right py-2 font-semibold">£{monthData.total.toFixed(2)}</td>
                    <td className="text-right py-2">{monthTransactions.length}</td>
                    <td className="text-right py-2">£{avgTransaction.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MonthlyTrends;