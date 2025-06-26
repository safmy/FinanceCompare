import { Transaction, AnalyticsData, Category, MonthlyTrend, MerchantSummary } from '../types';
import { format, startOfMonth, isWithinInterval } from 'date-fns';

export function generateAnalytics(transactions: Transaction[]): AnalyticsData {
  const totalIncome = transactions
    .filter(t => t.type === 'credit')
    .reduce((sum, t) => sum + t.amount, 0);
    
  const totalExpenses = transactions
    .filter(t => t.type === 'debit')
    .reduce((sum, t) => sum + t.amount, 0);
    
  const netSavings = totalIncome - totalExpenses;
  
  const categorySummary = generateCategorySummary(transactions);
  const monthlyTrends = generateMonthlyTrends(transactions);
  const topMerchants = generateTopMerchants(transactions);
  
  return {
    totalIncome,
    totalExpenses,
    netSavings,
    categorySummary,
    monthlyTrends,
    topMerchants,
  };
}

function generateCategorySummary(transactions: Transaction[]): Category[] {
  const categoryMap = new Map<string, Transaction[]>();
  
  // Group transactions by category
  transactions.forEach(transaction => {
    if (transaction.type === 'debit' && transaction.category) {
      const existing = categoryMap.get(transaction.category) || [];
      categoryMap.set(transaction.category, [...existing, transaction]);
    }
  });
  
  // Calculate totals and percentages
  const totalExpenses = transactions
    .filter(t => t.type === 'debit')
    .reduce((sum, t) => sum + t.amount, 0);
    
  const categories: Category[] = [];
  
  categoryMap.forEach((transactions, name) => {
    const total = transactions.reduce((sum, t) => sum + t.amount, 0);
    categories.push({
      name,
      total,
      percentage: (total / totalExpenses) * 100,
      transactions,
    });
  });
  
  // Sort by total descending
  return categories.sort((a, b) => b.total - a.total);
}

function generateMonthlyTrends(transactions: Transaction[]): MonthlyTrend[] {
  const monthlyMap = new Map<string, { income: number; expenses: number }>();
  
  transactions.forEach(transaction => {
    const monthKey = format(startOfMonth(transaction.date), 'MMM yyyy');
    const existing = monthlyMap.get(monthKey) || { income: 0, expenses: 0 };
    
    if (transaction.type === 'credit') {
      existing.income += transaction.amount;
    } else {
      existing.expenses += transaction.amount;
    }
    
    monthlyMap.set(monthKey, existing);
  });
  
  // Convert to array and sort by date
  const trends: MonthlyTrend[] = [];
  monthlyMap.forEach((data, month) => {
    trends.push({
      month,
      income: data.income,
      expenses: data.expenses,
      savings: data.income - data.expenses,
    });
  });
  
  // Sort by date (parse month back to date for sorting)
  return trends.sort((a, b) => {
    const dateA = new Date(a.month);
    const dateB = new Date(b.month);
    return dateA.getTime() - dateB.getTime();
  });
}

function generateTopMerchants(transactions: Transaction[]): MerchantSummary[] {
  const merchantMap = new Map<string, { total: number; count: number; category: string }>();
  
  transactions.forEach(transaction => {
    if (transaction.type === 'debit' && transaction.merchant) {
      const existing = merchantMap.get(transaction.merchant) || {
        total: 0,
        count: 0,
        category: transaction.category || 'Other',
      };
      
      existing.total += transaction.amount;
      existing.count += 1;
      
      merchantMap.set(transaction.merchant, existing);
    }
  });
  
  // Convert to array and sort by total
  const merchants: MerchantSummary[] = [];
  merchantMap.forEach((data, name) => {
    merchants.push({
      name,
      total: data.total,
      count: data.count,
      category: data.category,
    });
  });
  
  return merchants.sort((a, b) => b.total - a.total);
}

export function filterTransactionsByPeriod(
  transactions: Transaction[],
  period: 'week' | 'month' | 'year' | 'all'
): Transaction[] {
  if (period === 'all') return transactions;
  
  const now = new Date();
  let startDate: Date;
  
  switch (period) {
    case 'week':
      startDate = new Date(now);
      startDate.setDate(now.getDate() - 7);
      break;
    case 'month':
      startDate = new Date(now);
      startDate.setMonth(now.getMonth() - 1);
      break;
    case 'year':
      startDate = new Date(now);
      startDate.setFullYear(now.getFullYear() - 1);
      break;
  }
  
  return transactions.filter(transaction =>
    isWithinInterval(transaction.date, { start: startDate, end: now })
  );
}