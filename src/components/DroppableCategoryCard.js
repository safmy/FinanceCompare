import React, { useState } from 'react';
import { TrendingUp, Plus } from 'lucide-react';
import AICategorizeButton from './AICategorizeButton';

const DroppableCategoryCard = ({ 
  category, 
  amount, 
  percentage, 
  color, 
  transactionCount, 
  onClick, 
  onDrop,
  isCreateNew = false,
  onCreateCategory,
  transactions = [],
  onRecategorize
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryColor, setNewCategoryColor] = useState('#3B82F6');

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
    
    if (isCreateNew) {
      setShowCreateDialog(true);
    } else {
      onDrop(category);
    }
  };

  const handleCreateCategory = () => {
    if (newCategoryName.trim()) {
      onCreateCategory(newCategoryName.trim(), newCategoryColor);
      setShowCreateDialog(false);
      setNewCategoryName('');
      setNewCategoryColor('#3B82F6');
    }
  };

  // Listen for custom touch drop events
  React.useEffect(() => {
    const handleTouchDrop = (e) => {
      if (isCreateNew && e.detail.category === 'create-new') {
        setShowCreateDialog(true);
      }
    };
    
    window.addEventListener('transaction-drop', handleTouchDrop);
    return () => window.removeEventListener('transaction-drop', handleTouchDrop);
  }, [isCreateNew]);

  if (isCreateNew) {
    return (
      <>
        <div
          className={`bg-white rounded-lg shadow-md p-6 cursor-pointer transition-all transform hover:scale-105 border-2 border-dashed ${
            isDragOver ? 'border-blue-500 bg-blue-50 scale-105' : 'border-gray-300'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => setShowCreateDialog(true)}
          data-category-drop="create-new"
        >
          <div className="flex flex-col items-center justify-center h-full">
            <Plus className={`w-12 h-12 mb-2 ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`} />
            <p className={`text-sm font-medium ${isDragOver ? 'text-blue-600' : 'text-gray-600'}`}>
              {isDragOver ? 'Drop to create new category' : 'Create New Category'}
            </p>
          </div>
        </div>

        {showCreateDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96">
              <h3 className="text-lg font-semibold mb-4">Create New Category</h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category Name
                </label>
                <input
                  type="text"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Hobbies"
                  autoFocus
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Color
                </label>
                <div className="flex items-center space-x-3">
                  <input
                    type="color"
                    value={newCategoryColor}
                    onChange={(e) => setNewCategoryColor(e.target.value)}
                    className="w-12 h-12 border border-gray-300 rounded cursor-pointer"
                  />
                  <span className="text-sm text-gray-600">{newCategoryColor}</span>
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreateDialog(false);
                    setNewCategoryName('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCategory}
                  disabled={!newCategoryName.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <div
      className={`bg-white rounded-lg shadow-md p-6 cursor-pointer transition-all transform hover:scale-105 ${
        isDragOver ? 'ring-2 ring-blue-500 scale-105' : ''
      }`}
      style={{ borderLeft: `4px solid ${color}` }}
      onClick={onClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      data-category-drop={category}
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-800">{category}</h3>
        <div 
          className="w-3 h-3 rounded-full" 
          style={{ backgroundColor: color }}
        />
      </div>
      
      <div className="space-y-2">
        <p className="text-2xl font-bold text-gray-900">
          £{amount.toFixed(2)}
        </p>
        
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">{percentage}% of total</span>
          <div className="flex items-center text-gray-500">
            <TrendingUp className="w-4 h-4 mr-1" />
            <span>{transactionCount} transactions</span>
          </div>
        </div>
      </div>

      {isDragOver && (
        <div className="mt-3 text-xs text-blue-600 font-medium">
          Drop here to categorize
        </div>
      )}
      
      {category === 'Other' && transactionCount > 1 && onRecategorize && (
        <AICategorizeButton
          category={category}
          transactionCount={transactionCount}
          transactions={transactions}
          onRecategorize={onRecategorize}
          categoryColors={{ [category]: color }}
        />
      )}
    </div>
  );
};

export default DroppableCategoryCard;