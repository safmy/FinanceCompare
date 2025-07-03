import React from 'react';
import { ChevronRight } from 'lucide-react';

const CategoryCard = ({ category, amount, percentage, color, onClick, transactionCount }) => {
  return (
    <div 
      className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{category}</h3>
        <div 
          className="w-12 h-12 rounded-full flex items-center justify-center"
          style={{ backgroundColor: `${color}20` }}
        >
          <div 
            className="w-6 h-6 rounded-full"
            style={{ backgroundColor: color }}
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <p className="text-2xl font-bold text-gray-900">
          £{Math.abs(amount).toFixed(2)}
        </p>
        <p className="text-sm text-gray-500">
          {percentage}% of total
        </p>
        <p className="text-xs text-gray-400">
          {transactionCount} transactions
        </p>
      </div>
      
      <div className="mt-4 flex items-center text-blue-600 text-sm">
        <span>Click to view details</span>
        <ChevronRight className="w-4 h-4 ml-1" />
      </div>
    </div>
  );
};

export default CategoryCard;