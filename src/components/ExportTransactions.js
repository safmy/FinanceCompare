import React from 'react';
import { Download, Save } from 'lucide-react';

const ExportTransactions = ({ transactions }) => {
  const handleExportJS = () => {
    // Generate JS content
    let jsContent = 'export const transactions = [\n';
    
    transactions.forEach((trans, index) => {
      jsContent += '  {\n';
      jsContent += `    id: ${trans.id},\n`;
      jsContent += `    date: '${trans.date}',\n`;
      
      // Escape quotes in description
      const escapedDesc = trans.description.replace(/'/g, "\\'").replace(/"/g, '\\"');
      jsContent += `    description: '${escapedDesc}',\n`;
      
      jsContent += `    amount: ${trans.amount},\n`;
      jsContent += `    category: '${trans.category}',\n`;
      jsContent += `    month: '${trans.month || 'Unknown'}',\n`;
      
      if (trans.source) {
        jsContent += `    source: '${trans.source}'\n`;
      }
      
      jsContent += '  }';
      if (index < transactions.length - 1) {
        jsContent += ',';
      }
      jsContent += '\n';
    });
    
    jsContent += '];\n\n';
    
    // Add category colors
    const categories = [...new Set(transactions.map(t => t.category))];
    jsContent += 'export const categoryColors = {\n';
    
    const defaultColors = {
      'Income': '#10B981',
      'Rent': '#DC2626',
      'Bills & Utilities': '#7C3AED',
      'Groceries': '#059669',
      'Restaurants': '#F59E0B',
      'Fast Food': '#F97316',
      'Food Delivery': '#FB923C',
      'Coffee Shops': '#92400E',
      'Transport': '#3B82F6',
      'Fuel': '#1F2937',
      'Parking': '#6B7280',
      'Shopping': '#EC4899',
      'Subscriptions': '#8B5CF6',
      'Financial Services': '#6366F1',
      'Entertainment': '#14B8A6',
      'Healthcare': '#EF4444',
      'Personal Care': '#A78BFA',
      'Other': '#9CA3AF'
    };
    
    categories.forEach(cat => {
      jsContent += `  '${cat}': '${defaultColors[cat] || '#' + Math.floor(Math.random()*16777215).toString(16)}',\n`;
    });
    
    jsContent += '};\n';
    
    // Create and download file
    const blob = new Blob([jsContent], { type: 'text/javascript' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    // Generate filename with date
    const date = new Date().toISOString().split('T')[0];
    a.download = `transactions_categorized_${date}.js`;
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportCSV = () => {
    // Generate CSV content
    let csvContent = 'Date,Description,Amount,Category,Month,Source\n';
    
    transactions.forEach(trans => {
      const desc = trans.description.replace(/"/g, '""'); // Escape quotes
      csvContent += `"${trans.date}","${desc}",${trans.amount},"${trans.category}","${trans.month || 'Unknown'}","${trans.source || 'Unknown'}"\n`;
    });
    
    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    const date = new Date().toISOString().split('T')[0];
    a.download = `transactions_${date}.csv`;
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex space-x-3">
      <button
        onClick={handleExportJS}
        className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        title="Export as JavaScript file for re-importing"
      >
        <Save className="w-4 h-4 mr-2" />
        Export as JS
      </button>
      
      <button
        onClick={handleExportCSV}
        className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        title="Export as CSV for spreadsheet applications"
      >
        <Download className="w-4 h-4 mr-2" />
        Export as CSV
      </button>
    </div>
  );
};

export default ExportTransactions;