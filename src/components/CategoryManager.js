import React, { useState, useRef } from 'react';
import { Plus, Trash2, Edit2, Check, X, Palette } from 'lucide-react';

const CategoryManager = ({ transactions, onClose, onUpdateCategories }) => {
  const [categories, setCategories] = useState(() => {
    // Extract unique categories from transactions
    const uniqueCategories = [...new Set(transactions.map(t => t.category))];
    const categoryData = {};
    
    uniqueCategories.forEach(cat => {
      const catTransactions = transactions.filter(t => t.category === cat);
      categoryData[cat] = {
        name: cat,
        count: catTransactions.length,
        amount: catTransactions.reduce((sum, t) => sum + Math.abs(t.amount), 0),
        color: getCategoryColor(cat)
      };
    });
    
    return categoryData;
  });

  const [draggedCategory, setDraggedCategory] = useState(null);
  const [dragOverCategory, setDragOverCategory] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [showNewCategory, setShowNewCategory] = useState(false);
  const [newCategoryInput, setNewCategoryInput] = useState('');
  const [selectedColor, setSelectedColor] = useState('#3b82f6');

  const dragCounter = useRef(0);

  const defaultColors = [
    '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
    '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
    '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
    '#ec4899', '#f43f5e', '#6b7280'
  ];

  function getCategoryColor(category) {
    const colors = {
      'Income': '#10b981',
      'Rent': '#dc2626',
      'Bills & Utilities': '#7c3aed',
      'Groceries': '#f59e0b',
      'Restaurants': '#ec4899',
      'Fast Food': '#f97316',
      'Food Delivery': '#d946ef',
      'Coffee Shops': '#8b5cf6',
      'Transport': '#3b82f6',
      'Fuel': '#06b6d4',
      'Parking': '#0ea5e9',
      'Shopping': '#6366f1',
      'Subscriptions': '#a855f7',
      'Financial Services': '#84cc16',
      'Entertainment': '#f43f5e',
      'Healthcare': '#14b8a6',
      'Personal Care': '#fb923c',
      'Other': '#6b7280'
    };
    return colors[category] || '#6b7280';
  }

  const handleDragStart = (e, category) => {
    setDraggedCategory(category);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragEnter = (e, category) => {
    e.preventDefault();
    dragCounter.current++;
    if (category !== draggedCategory) {
      setDragOverCategory(category);
    }
  };

  const handleDragLeave = (e) => {
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setDragOverCategory(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, targetCategory) => {
    e.preventDefault();
    dragCounter.current = 0;
    
    if (draggedCategory && targetCategory && draggedCategory !== targetCategory) {
      // Merge categories
      const mergedData = {
        ...categories[targetCategory],
        count: categories[targetCategory].count + categories[draggedCategory].count,
        amount: categories[targetCategory].amount + categories[draggedCategory].amount
      };
      
      const newCategories = { ...categories };
      newCategories[targetCategory] = mergedData;
      delete newCategories[draggedCategory];
      
      setCategories(newCategories);
      
      // Notify parent component
      if (onUpdateCategories) {
        onUpdateCategories({
          type: 'merge',
          source: draggedCategory,
          target: targetCategory
        });
      }
    }
    
    setDraggedCategory(null);
    setDragOverCategory(null);
  };

  const handleEditCategory = (category) => {
    setEditingCategory(category);
    setNewCategoryName(category);
  };

  const handleSaveEdit = () => {
    if (newCategoryName && newCategoryName !== editingCategory) {
      const newCategories = { ...categories };
      newCategories[newCategoryName] = {
        ...categories[editingCategory],
        name: newCategoryName
      };
      delete newCategories[editingCategory];
      
      setCategories(newCategories);
      
      if (onUpdateCategories) {
        onUpdateCategories({
          type: 'rename',
          oldName: editingCategory,
          newName: newCategoryName
        });
      }
    }
    setEditingCategory(null);
  };

  const handleCreateCategory = () => {
    if (newCategoryInput.trim()) {
      const newCategories = {
        ...categories,
        [newCategoryInput]: {
          name: newCategoryInput,
          count: 0,
          amount: 0,
          color: selectedColor
        }
      };
      
      setCategories(newCategories);
      
      if (onUpdateCategories) {
        onUpdateCategories({
          type: 'create',
          name: newCategoryInput,
          color: selectedColor
        });
      }
      
      setNewCategoryInput('');
      setShowNewCategory(false);
      setSelectedColor('#3b82f6');
    }
  };

  const handleDeleteCategory = (category) => {
    if (window.confirm(`Delete category "${category}"? Transactions will be moved to "Other".`)) {
      const newCategories = { ...categories };
      delete newCategories[category];
      
      setCategories(newCategories);
      
      if (onUpdateCategories) {
        onUpdateCategories({
          type: 'delete',
          name: category
        });
      }
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Category Manager</h2>
            <p className="text-sm text-gray-600 mt-1">
              Drag categories to merge them, or create new ones
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        
        <div className="p-6 overflow-auto max-h-[calc(90vh-200px)]">
          {/* Create New Category */}
          <div className="mb-6">
            {!showNewCategory ? (
              <button
                onClick={() => setShowNewCategory(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                <span>Create New Category</span>
              </button>
            ) : (
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center space-x-4 mb-3">
                  <input
                    type="text"
                    value={newCategoryInput}
                    onChange={(e) => setNewCategoryInput(e.target.value)}
                    placeholder="Category name"
                    className="flex-1 px-3 py-2 border rounded-lg"
                    autoFocus
                  />
                  <div className="flex items-center space-x-2">
                    <Palette className="w-5 h-5 text-gray-600" />
                    <input
                      type="color"
                      value={selectedColor}
                      onChange={(e) => setSelectedColor(e.target.value)}
                      className="w-10 h-10 border rounded cursor-pointer"
                    />
                  </div>
                  <button
                    onClick={handleCreateCategory}
                    className="p-2 text-green-600 hover:bg-green-100 rounded"
                  >
                    <Check className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => {
                      setShowNewCategory(false);
                      setNewCategoryInput('');
                    }}
                    className="p-2 text-red-600 hover:bg-red-100 rounded"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {defaultColors.map(color => (
                    <button
                      key={color}
                      onClick={() => setSelectedColor(color)}
                      className={`w-8 h-8 rounded border-2 ${
                        selectedColor === color ? 'border-gray-800' : 'border-gray-300'
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Category List */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(categories)
              .sort(([, a], [, b]) => b.amount - a.amount)
              .map(([category, data]) => (
                <div
                  key={category}
                  draggable
                  onDragStart={(e) => handleDragStart(e, category)}
                  onDragEnter={(e) => handleDragEnter(e, category)}
                  onDragLeave={handleDragLeave}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, category)}
                  className={`p-4 rounded-lg border-2 cursor-move transition-all ${
                    dragOverCategory === category
                      ? 'border-blue-500 bg-blue-50 scale-105'
                      : 'border-gray-200 hover:border-gray-300'
                  } ${draggedCategory === category ? 'opacity-50' : ''}`}
                  style={{
                    borderLeftColor: data.color,
                    borderLeftWidth: '4px'
                  }}
                >
                  <div className="flex justify-between items-start mb-2">
                    {editingCategory === category ? (
                      <div className="flex items-center space-x-2 flex-1">
                        <input
                          type="text"
                          value={newCategoryName}
                          onChange={(e) => setNewCategoryName(e.target.value)}
                          className="flex-1 px-2 py-1 border rounded text-sm"
                          autoFocus
                        />
                        <button
                          onClick={handleSaveEdit}
                          className="p-1 text-green-600 hover:bg-green-100 rounded"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setEditingCategory(null)}
                          className="p-1 text-red-600 hover:bg-red-100 rounded"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <h3 className="font-semibold text-lg">{category}</h3>
                        <div className="flex space-x-1">
                          <button
                            onClick={() => handleEditCategory(category)}
                            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          {data.count === 0 && (
                            <button
                              onClick={() => handleDeleteCategory(category)}
                              className="p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    <div>{data.count} transactions</div>
                    <div className="font-medium">£{data.amount.toFixed(2)}</div>
                  </div>
                </div>
              ))}
          </div>
        </div>

        <div className="p-4 border-t bg-gray-50">
          <p className="text-sm text-gray-600">
            Tip: Drag and drop categories on top of each other to merge them. 
            The dropped category's transactions will be moved to the target category.
          </p>
        </div>
      </div>
    </div>
  );
};

export default CategoryManager;