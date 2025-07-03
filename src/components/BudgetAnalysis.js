import React from 'react';
import { budgetTargets } from '../data/fullTransactionData';
import { AlertTriangle, CheckCircle } from 'lucide-react';

const BudgetAnalysis = ({ transactions }) => {
  // Calculate spending by category
  const spendingByCategory = transactions.reduce((acc, transaction) => {
    const category = transaction.category;
    if (!acc[category]) {
      acc[category] = 0;
    }
    acc[category] += Math.abs(transaction.amount);
    return acc;
  }, {});

  // Calculate monthly average
  const months = [...new Set(transactions.map(t => t.month))];
  const monthCount = months.length || 1;

  const budgetData = Object.entries(budgetTargets).map(([category, budget]) => {
    const totalSpent = spendingByCategory[category] || 0;
    const monthlyAverage = totalSpent / monthCount;
    const percentUsed = (monthlyAverage / budget) * 100;
    const status = percentUsed > 100 ? 'over' : percentUsed > 80 ? 'warning' : 'good';

    return {
      category,
      budget,
      monthlyAverage,
      percentUsed,
      status,
      difference: budget - monthlyAverage
    };
  });

  const totalBudget = Object.values(budgetTargets).reduce((sum, val) => sum + val, 0);
  const totalSpent = Object.values(spendingByCategory).reduce((sum, val) => sum + val, 0) / monthCount;
  const totalPercentUsed = (totalSpent / totalBudget) * 100;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-6">Budget Analysis</h2>
      
      {/* Overall Budget Status */}
      <div className="mb-8 p-4 rounded-lg bg-gray-50">
        <div className="flex justify-between items-center mb-2">
          <span className="text-lg font-semibold">Total Monthly Budget</span>
          <span className="text-lg">£{totalBudget.toFixed(2)}</span>
        </div>
        <div className="flex justify-between items-center mb-2">
          <span>Average Monthly Spending</span>
          <span className={`font-semibold ${totalPercentUsed > 100 ? 'text-red-600' : 'text-green-600'}`}>
            £{totalSpent.toFixed(2)}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 mt-3">
          <div 
            className={`h-4 rounded-full transition-all ${
              totalPercentUsed > 100 ? 'bg-red-500' : totalPercentUsed > 80 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(totalPercentUsed, 100)}%` }}
          />
        </div>
        <p className="text-sm text-gray-600 mt-2">
          {totalPercentUsed.toFixed(1)}% of budget used
        </p>
      </div>

      {/* Category Budget Details */}
      <div className="space-y-4">
        {budgetData.sort((a, b) => b.percentUsed - a.percentUsed).map(({ 
          category, 
          budget, 
          monthlyAverage, 
          percentUsed, 
          status, 
          difference 
        }) => (
          <div key={category} className="border rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-semibold text-lg">{category}</h3>
                <p className="text-sm text-gray-600">
                  Budget: £{budget}/month
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold">
                  £{monthlyAverage.toFixed(2)}/month
                </p>
                <p className={`text-sm ${difference >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {difference >= 0 ? '+' : ''}£{difference.toFixed(2)}
                </p>
              </div>
            </div>
            
            <div className="relative">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all ${
                    status === 'over' ? 'bg-red-500' : 
                    status === 'warning' ? 'bg-yellow-500' : 
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(percentUsed, 100)}%` }}
                />
              </div>
              {percentUsed > 100 && (
                <div className="absolute right-0 top-0 flex items-center mt-3">
                  <AlertTriangle className="w-4 h-4 text-red-500 mr-1" />
                  <span className="text-xs text-red-500">
                    {(percentUsed - 100).toFixed(1)}% over budget
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex justify-between items-center mt-2">
              <span className="text-sm text-gray-600">
                {percentUsed.toFixed(1)}% used
              </span>
              {status === 'good' && (
                <CheckCircle className="w-4 h-4 text-green-500" />
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Budget Tips */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold mb-2">Budget Tips</h3>
        <ul className="text-sm space-y-1 text-gray-700">
          {budgetData.filter(b => b.status === 'over').length > 0 && (
            <li>• Consider reducing spending in categories that are over budget</li>
          )}
          {budgetData.filter(b => b.difference > 50).length > 0 && (
            <li>• You have room to save more in some categories</li>
          )}
          <li>• Set up automatic transfers to savings for unused budget</li>
          <li>• Review and adjust budgets quarterly based on actual spending</li>
        </ul>
      </div>
    </div>
  );
};

export default BudgetAnalysis;