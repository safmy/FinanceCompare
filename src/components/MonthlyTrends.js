import React from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { categoryColors } from '../data/sampleData';

const MonthlyTrends = ({ transactions }) => {
  // Process data for monthly spending by category
  const monthlyData = transactions.reduce((acc, transaction) => {
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
  const categories = [...new Set(transactions.map(t => t.category))];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-6">Monthly Spending Trends</h2>
      
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
              {categories.slice(0, 5).map((category) => (
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
                const monthTransactions = transactions.filter(t => t.month === monthData.month);
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