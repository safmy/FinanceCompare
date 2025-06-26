export interface Transaction {
  id: string;
  date: Date;
  description: string;
  amount: number;
  balance?: number;
  category?: string;
  merchant?: string;
  type: 'debit' | 'credit';
  originalText?: string;
}

export interface Category {
  name: string;
  total: number;
  percentage: number;
  transactions: Transaction[];
}

export interface AnalyticsData {
  totalIncome: number;
  totalExpenses: number;
  netSavings: number;
  categorySummary: Category[];
  monthlyTrends: MonthlyTrend[];
  topMerchants: MerchantSummary[];
}

export interface MonthlyTrend {
  month: string;
  income: number;
  expenses: number;
  savings: number;
}

export interface MerchantSummary {
  name: string;
  total: number;
  count: number;
  category: string;
}

export interface FileParseResult {
  transactions: Transaction[];
  errors?: string[];
}

export const EXPENSE_CATEGORIES = [
  'Food & Dining',
  'Shopping',
  'Transportation',
  'Bills & Utilities',
  'Entertainment',
  'Healthcare',
  'Education',
  'Travel',
  'Personal Care',
  'Home & Garden',
  'Gifts & Donations',
  'Financial',
  'Business',
  'Other'
] as const;

export type ExpenseCategory = typeof EXPENSE_CATEGORIES[number];