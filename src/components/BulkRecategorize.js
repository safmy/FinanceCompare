import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, X } from 'lucide-react';

const BulkRecategorize = ({ transactions, categories, categoryColors, onClose, onRecategorize }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTransactions, setSelectedTransactions] = useState(new Set());
  const [newCategory, setNewCategory] = useState('');
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [selectAll, setSelectAll] = useState(false);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredTransactions([]);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = transactions.filter(transaction => 
      transaction.description.toLowerCase().includes(query)
    );

    setFilteredTransactions(filtered);
    setSelectedTransactions(new Set());
    setSelectAll(false);
  }, [searchQuery, transactions]);

  const handleToggleSelect = (transactionId) => {
    const newSelected = new Set(selectedTransactions);
    if (newSelected.has(transactionId)) {
      newSelected.delete(transactionId);
    } else {
      newSelected.add(transactionId);
    }
    setSelectedTransactions(newSelected);
    setSelectAll(newSelected.size === filteredTransactions.length && filteredTransactions.length > 0);
  };

  const handleToggleSelectAll = () => {
    if (selectAll) {
      setSelectedTransactions(new Set());
    } else {
      setSelectedTransactions(new Set(filteredTransactions.map(t => t.id)));
    }
    setSelectAll(!selectAll);
  };

  const handleRecategorize = () => {
    if (!newCategory || selectedTransactions.size === 0) return;

    const recategorizations = Array.from(selectedTransactions).map(id => ({
      id,
      newCategory
    }));

    onRecategorize(recategorizations);
    
    // Reset state
    setSearchQuery('');
    setSelectedTransactions(new Set());
    setNewCategory('');
    setFilteredTransactions([]);
    setSelectAll(false);
  };

  const getCategoryStats = () => {
    const stats = {};
    filteredTransactions.forEach(t => {
      stats[t.category] = (stats[t.category] || 0) + 1;
    });
    return stats;
  };

  const categoryStats = getCategoryStats();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Bulk Recategorize Transactions</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Search Input */}
          <div className="mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search transactions by description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Results */}
          {searchQuery && (
            <>
              <div className="mb-4 flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  Found {filteredTransactions.length} transaction{filteredTransactions.length !== 1 ? 's' : ''}
                  {Object.keys(categoryStats).length > 0 && (
                    <span className="ml-2">
                      ({Object.entries(categoryStats).map(([cat, count], index) => (
                        <span key={cat}>
                          {index > 0 && ', '}
                          {count} in {cat}
                        </span>
                      ))})
                    </span>
                  )}
                </div>
                {filteredTransactions.length > 0 && (
                  <button
                    onClick={handleToggleSelectAll}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    {selectAll ? 'Deselect All' : 'Select All'}
                  </button>
                )}
              </div>

              {/* Transactions List */}
              {filteredTransactions.length > 0 ? (
                <div className="border rounded-lg overflow-hidden mb-6">
                  <div className="max-h-96 overflow-y-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            <input
                              type="checkbox"
                              checked={selectAll}
                              onChange={handleToggleSelectAll}
                              className="w-4 h-4"
                            />
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                          {filteredTransactions.some(t => t.sourceFile) && (
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                          )}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {filteredTransactions.map((transaction) => (
                          <tr 
                            key={transaction.id}
                            className={`hover:bg-gray-50 ${selectedTransactions.has(transaction.id) ? 'bg-blue-50' : ''}`}
                          >
                            <td className="px-4 py-3">
                              <input
                                type="checkbox"
                                checked={selectedTransactions.has(transaction.id)}
                                onChange={() => handleToggleSelect(transaction.id)}
                                className="w-4 h-4"
                              />
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {new Date(transaction.date).toLocaleDateString()}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {transaction.description}
                            </td>
                            <td className="px-4 py-3 text-sm font-medium">
                              <span className={transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}>
                                £{Math.abs(transaction.amount).toFixed(2)}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <span 
                                className="px-2 py-1 rounded-full text-xs font-medium"
                                style={{
                                  backgroundColor: `${categoryColors[transaction.category]}20`,
                                  color: categoryColors[transaction.category]
                                }}
                              >
                                {transaction.category}
                              </span>
                            </td>
                            {transaction.sourceFile && (
                              <td className="px-4 py-3 text-sm text-gray-500">
                                {transaction.sourceFile}
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No transactions found matching your search.
                </div>
              )}

              {/* Recategorization Controls */}
              {selectedTransactions.size > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Recategorize {selectedTransactions.size} transaction{selectedTransactions.size !== 1 ? 's' : ''} to:
                      </label>
                      <select
                        value={newCategory}
                        onChange={(e) => setNewCategory(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select a category...</option>
                        {categories.map(category => (
                          <option key={category} value={category}>
                            {category}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <button
                        onClick={handleRecategorize}
                        disabled={!newCategory}
                        className={`px-6 py-3 rounded-lg flex items-center space-x-2 ${
                          newCategory
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }`}
                      >
                        <RefreshCw className="w-5 h-5" />
                        <span>Apply Changes</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Instructions */}
          {!searchQuery && (
            <div className="text-center py-12 text-gray-500">
              <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg mb-2">Search for transactions to recategorize</p>
              <p className="text-sm">
                Enter a search term to find transactions by description, category, or source file.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BulkRecategorize;