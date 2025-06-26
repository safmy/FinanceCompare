import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import TransactionList from './components/TransactionList';
import Analytics from './components/Analytics';
import { Transaction, AnalyticsData } from './types';
import { parseTransactions } from './utils/parser';
import { categorizeTransactions } from './utils/categorizer';
import { generateAnalytics } from './utils/analytics';
import './App.css';

function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (files: File[]) => {
    setLoading(true);
    setError(null);
    
    try {
      // Parse transactions from uploaded files
      const parsedTransactions: Transaction[] = [];
      
      for (const file of files) {
        const fileTransactions = await parseTransactions(file);
        parsedTransactions.push(...fileTransactions);
      }
      
      // Categorize transactions using AI
      const categorizedTransactions = await categorizeTransactions(parsedTransactions);
      setTransactions(categorizedTransactions);
      
      // Generate analytics
      const analyticsData = generateAnalytics(categorizedTransactions);
      setAnalytics(analyticsData);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>FinanceCompare</h1>
        <p>Upload your bank statements to analyze your spending</p>
      </header>
      
      <main className="App-main">
        <FileUpload onUpload={handleFileUpload} loading={loading} />
        
        {error && (
          <div className="error-message">
            <p>Error: {error}</p>
          </div>
        )}
        
        {transactions.length > 0 && (
          <>
            <Analytics data={analytics} />
            <TransactionList transactions={transactions} />
          </>
        )}
      </main>
    </div>
  );
}

export default App;