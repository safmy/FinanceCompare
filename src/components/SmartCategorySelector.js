import React, { useState, useEffect, useRef } from 'react';
import { Search, Check, X } from 'lucide-react';

const SmartCategorySelector = ({ 
  currentCategory, 
  onSelect, 
  onClose, 
  availableCategories, 
  categoryColors,
  transactionDescription = '',
  transactionAmount = 0,
  recentCategories = [],
  frequentCategories = []
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [hoveredCategory, setHoveredCategory] = useState(null);
  const searchInputRef = useRef(null);
  const categoryRefs = useRef({});

  // Group categories by type
  const categoryGroups = {
    'Financial': ['Income', 'Financial Services', 'Savings', 'Investments', 'Insurance', 'Cash'],
    'Housing': ['Rent', 'Bills & Utilities', 'Home & Garden'],
    'Food': ['Groceries', 'Restaurants', 'Fast Food', 'Coffee Shops', 'Food Delivery'],
    'Transport': ['Transport', 'Transportation', 'Fuel', 'Parking', 'Travel'],
    'Shopping': ['Shopping', 'Entertainment', 'Subscriptions', 'Personal Care', 'Healthcare'],
    'Other': ['Education', 'Charity', 'Gifts', 'Pets', 'Fitness', 'Phone', 'Other']
  };

  // Flatten all categories from groups
  const allCategoriesFromGroups = Object.values(categoryGroups).flat();
  
  // Add any categories not in groups
  const ungroupedCategories = availableCategories.filter(cat => !allCategoriesFromGroups.includes(cat));
  if (ungroupedCategories.length > 0) {
    categoryGroups['Uncategorized'] = ungroupedCategories;
  }

  // Score categories based on relevance
  const scoreCategory = (category) => {
    let score = 0;
    const desc = transactionDescription.toUpperCase();
    const cat = category.toUpperCase();
    
    // Exact match in description
    if (desc.includes(cat)) score += 100;
    
    // Category keywords in description
    const categoryKeywords = {
      'Income': ['SALARY', 'PAYSTREAM', 'PAYMENT THANK YOU', 'CR PAYMENT'],
      'Rent': ['RENT', 'SCHOLARS WALK', 'LANDLORD'],
      'Insurance': ['INSURANCE', 'INS', 'ANSWER INS'],
      'Bills & Utilities': ['DD EE', 'COUNCIL TAX', 'ELECTRIC', 'GAS', 'WATER'],
      'Groceries': ['SAINSBURY', 'TESCO', 'ASDA', 'CO-OP'],
      'Coffee Shops': ['PRET', 'STARBUCKS', 'COSTA', 'CAFFE NERO'],
      'Shopping': ['AMAZON', 'IKEA', 'PRIMARK', 'BOOTS'],
      'Transport': ['TFL', 'UBER', 'TRAIN', 'OYSTER'],
      'Financial Services': ['ATM', 'HSBC', 'BANK', 'PAYPAL']
    };
    
    if (categoryKeywords[category]) {
      categoryKeywords[category].forEach(keyword => {
        if (desc.includes(keyword)) score += 50;
      });
    }
    
    // Recent usage
    const recentIndex = recentCategories.indexOf(category);
    if (recentIndex !== -1) {
      score += (10 - recentIndex) * 5;
    }
    
    // Frequent usage
    const freqIndex = frequentCategories.indexOf(category);
    if (freqIndex !== -1) {
      score += (10 - freqIndex) * 3;
    }
    
    // Current category gets a boost
    if (category === currentCategory) score += 20;
    
    // Search term matching
    if (searchTerm && category.toLowerCase().includes(searchTerm.toLowerCase())) {
      score += 200;
    }
    
    return score;
  };

  // Get suggested categories
  const getSuggestedCategories = () => {
    const scored = availableCategories.map(cat => ({
      category: cat,
      score: scoreCategory(cat)
    }));
    
    // Sort by score
    scored.sort((a, b) => b.score - a.score);
    
    // Get top 5 suggestions with score > 0
    const suggestions = scored
      .filter(item => item.score > 0 && item.category !== currentCategory)
      .slice(0, 5)
      .map(item => item.category);
    
    // Always include current category at the start if not in suggestions
    if (!suggestions.includes(currentCategory)) {
      suggestions.unshift(currentCategory);
    }
    
    return suggestions;
  };

  const suggestedCategories = getSuggestedCategories();

  // Filter categories based on search
  const getFilteredCategories = () => {
    if (!searchTerm) return availableCategories;
    
    const term = searchTerm.toLowerCase();
    return availableCategories.filter(cat => 
      cat.toLowerCase().includes(term)
    );
  };

  const filteredCategories = getFilteredCategories();

  // Focus search input on mount
  useEffect(() => {
    searchInputRef.current?.focus();
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      const visibleCategories = searchTerm ? filteredCategories : suggestedCategories;
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < visibleCategories.length - 1 ? prev + 1 : 0
          );
          break;
          
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : visibleCategories.length - 1
          );
          break;
          
        case 'Enter':
          e.preventDefault();
          if (visibleCategories[selectedIndex]) {
            onSelect(visibleCategories[selectedIndex]);
          }
          break;
          
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
          
        case 'Tab':
          e.preventDefault();
          // Tab through category groups
          break;
          
        default:
          // Handle other keys
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedIndex, filteredCategories, suggestedCategories, searchTerm, onSelect, onClose]);

  // Scroll selected category into view
  useEffect(() => {
    const visibleCategories = searchTerm ? filteredCategories : suggestedCategories;
    const selectedCategory = visibleCategories[selectedIndex];
    if (selectedCategory && categoryRefs.current[selectedCategory]) {
      categoryRefs.current[selectedCategory].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  }, [selectedIndex, filteredCategories, suggestedCategories, searchTerm]);

  const renderCategory = (category, isSelected, isSuggested = false) => {
    const color = categoryColors[category] || '#6b7280';
    const isCurrentCategory = category === currentCategory;
    
    return (
      <button
        key={category}
        ref={el => categoryRefs.current[category] = el}
        onClick={() => onSelect(category)}
        onMouseEnter={() => {
          setHoveredCategory(category);
          const visibleCategories = searchTerm ? filteredCategories : suggestedCategories;
          const index = visibleCategories.indexOf(category);
          if (index !== -1) setSelectedIndex(index);
        }}
        onMouseLeave={() => setHoveredCategory(null)}
        className={`
          relative flex items-center justify-between w-full px-4 py-3 text-left
          transition-all duration-150 ease-out
          ${isSelected || hoveredCategory === category
            ? 'bg-gray-100 scale-[1.02]' 
            : 'hover:bg-gray-50'
          }
          ${isCurrentCategory ? 'font-semibold' : ''}
        `}
      >
        <div className="flex items-center space-x-3">
          <div 
            className="w-5 h-5 rounded-full flex-shrink-0 ring-2 ring-offset-1"
            style={{ 
              backgroundColor: color,
              ringColor: color
            }}
          />
          <span className="text-gray-900">{category}</span>
          {isCurrentCategory && (
            <span className="text-xs text-gray-500">(current)</span>
          )}
          {isSuggested && (
            <span className="text-xs text-blue-600 font-medium">suggested</span>
          )}
        </div>
        {(isSelected || hoveredCategory === category) && (
          <Check className="w-5 h-5 text-gray-400" />
        )}
      </button>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
      <div 
        className="bg-white rounded-lg shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold">Select Category</h3>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search categories..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setSelectedIndex(0);
              }}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* Transaction info */}
          {transactionDescription && (
            <div className="mt-3 text-sm text-gray-600">
              <div className="truncate">{transactionDescription}</div>
              <div className="font-medium">
                £{Math.abs(transactionAmount).toFixed(2)}
              </div>
            </div>
          )}
        </div>

        {/* Categories */}
        <div className="overflow-y-auto max-h-[calc(80vh-180px)]">
          {!searchTerm ? (
            <>
              {/* Suggested categories */}
              {suggestedCategories.length > 0 && (
                <div className="p-4 pb-2">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Suggested</h4>
                  <div className="space-y-1">
                    {suggestedCategories.map((cat, index) => 
                      renderCategory(cat, index === selectedIndex, true)
                    )}
                  </div>
                </div>
              )}

              {/* All categories by group */}
              <div className="p-4 pt-2">
                <h4 className="text-sm font-medium text-gray-700 mb-2">All Categories</h4>
                {Object.entries(categoryGroups).map(([group, categories]) => {
                  const availableInGroup = categories.filter(cat => availableCategories.includes(cat));
                  if (availableInGroup.length === 0) return null;
                  
                  return (
                    <div key={group} className="mb-4">
                      <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                        {group}
                      </h5>
                      <div className="space-y-1">
                        {availableInGroup.map(cat => renderCategory(cat, false))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            /* Search results */
            <div className="p-4">
              {filteredCategories.length > 0 ? (
                <div className="space-y-1">
                  {filteredCategories.map((cat, index) => 
                    renderCategory(cat, index === selectedIndex)
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No categories found matching "{searchTerm}"
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 text-sm text-gray-600">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium">↑↓</span> Navigate • 
              <span className="font-medium">Enter</span> Select • 
              <span className="font-medium">Esc</span> Cancel
            </div>
            <div>
              Press <span className="font-medium">Tab</span> to jump between groups
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SmartCategorySelector;