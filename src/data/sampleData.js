// Sample transaction data structure
// Replace this with your actual bank statement data

export const transactions = [
  // January 2025
  { id: 1, date: '2025-01-05', description: 'Tesco Express', amount: -45.67, category: 'Groceries', month: 'January' },
  { id: 2, date: '2025-01-06', description: 'TfL Travel', amount: -25.50, category: 'Transport', month: 'January' },
  { id: 3, date: '2025-01-08', description: 'Pret A Manger', amount: -12.95, category: 'Coffee Shops', month: 'January' },
  { id: 4, date: '2025-01-10', description: 'Shell Petrol Station', amount: -65.00, category: 'Fuel', month: 'January' },
  { id: 5, date: '2025-01-12', description: 'Netflix Subscription', amount: -15.99, category: 'Subscriptions', month: 'January' },
  { id: 6, date: '2025-01-15', description: 'Deliveroo', amount: -28.45, category: 'Food Delivery', month: 'January' },
  { id: 7, date: '2025-01-18', description: 'Sainsburys', amount: -112.34, category: 'Groceries', month: 'January' },
  { id: 8, date: '2025-01-20', description: 'Uber', amount: -18.90, category: 'Transport', month: 'January' },
  { id: 9, date: '2025-01-22', description: 'Restaurant XYZ', amount: -85.50, category: 'Restaurants', month: 'January' },
  { id: 10, date: '2025-01-25', description: 'Amazon Prime', amount: -8.99, category: 'Subscriptions', month: 'January' },
  { id: 11, date: '2025-01-28', description: 'Costa Coffee', amount: -5.45, category: 'Coffee Shops', month: 'January' },
  { id: 12, date: '2025-01-30', description: 'Parking', amount: -12.00, category: 'Parking', month: 'January' },

  // February 2025
  { id: 13, date: '2025-02-02', description: 'Waitrose', amount: -78.90, category: 'Groceries', month: 'February' },
  { id: 14, date: '2025-02-04', description: 'TfL Travel', amount: -30.00, category: 'Transport', month: 'February' },
  { id: 15, date: '2025-02-06', description: 'McDonalds', amount: -15.67, category: 'Fast Food', month: 'February' },
  { id: 16, date: '2025-02-08', description: 'BP Petrol', amount: -72.50, category: 'Fuel', month: 'February' },
  { id: 17, date: '2025-02-10', description: 'Spotify', amount: -9.99, category: 'Subscriptions', month: 'February' },
  { id: 18, date: '2025-02-12', description: 'Just Eat', amount: -35.80, category: 'Food Delivery', month: 'February' },
  { id: 19, date: '2025-02-15', description: 'ASDA', amount: -95.45, category: 'Groceries', month: 'February' },
  { id: 20, date: '2025-02-18', description: 'National Rail', amount: -45.60, category: 'Transport', month: 'February' },
  { id: 21, date: '2025-02-20', description: 'Wagamama', amount: -68.90, category: 'Restaurants', month: 'February' },
  { id: 22, date: '2025-02-22', description: 'Starbucks', amount: -6.75, category: 'Coffee Shops', month: 'February' },
  { id: 23, date: '2025-02-25', description: 'ASOS', amount: -125.00, category: 'Shopping', month: 'February' },
  { id: 24, date: '2025-02-28', description: 'Council Tax', amount: -150.00, category: 'Other', month: 'February' },

  // Add more months as needed...
];

// Category colors for consistent visualization
export const categoryColors = {
  'Transport': '#3B82F6',
  'Fast Food': '#EF4444',
  'Groceries': '#10B981',
  'Restaurants': '#F59E0B',
  'Coffee Shops': '#8B5CF6',
  'Food Delivery': '#EC4899',
  'Subscriptions': '#6366F1',
  'Fuel': '#14B8A6',
  'Shopping': '#F97316',
  'Parking': '#F59E0B',
  'Other': '#6B7280'
};

// Budget targets (optional - set your monthly budget for each category)
export const budgetTargets = {
  'Transport': 300,
  'Fast Food': 100,
  'Groceries': 400,
  'Restaurants': 200,
  'Coffee Shops': 50,
  'Food Delivery': 150,
  'Subscriptions': 100,
  'Fuel': 200,
  'Shopping': 300,
  'Parking': 50,
  'Other': 200
};