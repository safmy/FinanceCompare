import { Transaction, EXPENSE_CATEGORIES } from '../types';

// Category keywords for rule-based categorization (fallback when AI is not available)
const CATEGORY_KEYWORDS: Record<string, string[]> = {
  'Food & Dining': ['restaurant', 'cafe', 'coffee', 'food', 'pizza', 'burger', 'sushi', 'grocery', 'supermarket', 'market', 'uber eats', 'doordash', 'grubhub'],
  'Shopping': ['amazon', 'walmart', 'target', 'store', 'shop', 'mall', 'ebay', 'etsy', 'clothing', 'shoes', 'fashion'],
  'Transportation': ['uber', 'lyft', 'taxi', 'gas', 'fuel', 'parking', 'toll', 'transit', 'metro', 'bus', 'train', 'airline', 'car rental'],
  'Bills & Utilities': ['electric', 'gas', 'water', 'internet', 'cable', 'phone', 'mobile', 'verizon', 'att', 'comcast', 'utility', 'rent', 'mortgage'],
  'Entertainment': ['movie', 'cinema', 'theater', 'concert', 'spotify', 'netflix', 'hulu', 'game', 'book', 'music', 'entertainment'],
  'Healthcare': ['pharmacy', 'doctor', 'hospital', 'clinic', 'medical', 'health', 'dental', 'vision', 'insurance', 'cvs', 'walgreens'],
  'Education': ['university', 'college', 'school', 'course', 'udemy', 'coursera', 'education', 'tuition', 'textbook', 'student'],
  'Travel': ['hotel', 'airbnb', 'flight', 'airline', 'travel', 'vacation', 'booking', 'expedia', 'resort', 'tourism'],
  'Personal Care': ['salon', 'spa', 'barber', 'beauty', 'cosmetic', 'gym', 'fitness', 'yoga', 'massage', 'hair', 'nail'],
  'Home & Garden': ['home depot', 'lowes', 'ikea', 'furniture', 'garden', 'hardware', 'appliance', 'decor', 'renovation'],
  'Gifts & Donations': ['gift', 'donation', 'charity', 'church', 'nonprofit', 'fundraiser', 'present'],
  'Financial': ['bank', 'atm', 'fee', 'interest', 'investment', 'transfer', 'wire', 'paypal', 'venmo', 'zelle'],
  'Business': ['office', 'supplies', 'software', 'subscription', 'adobe', 'microsoft', 'google', 'aws', 'hosting'],
};

export async function categorizeTransactions(transactions: Transaction[]): Promise<Transaction[]> {
  try {
    // Try to use AI categorization first
    const response = await fetch('/api/categorize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        transactions: transactions.map(t => ({
          description: t.description,
          amount: t.amount,
          type: t.type,
        })),
      }),
    });
    
    if (response.ok) {
      const { categorized } = await response.json();
      return transactions.map((transaction, index) => ({
        ...transaction,
        category: categorized[index].category,
        merchant: categorized[index].merchant || extractMerchant(transaction.description),
      }));
    }
  } catch (error) {
    console.error('AI categorization failed, falling back to rule-based:', error);
  }
  
  // Fallback to rule-based categorization
  return transactions.map(transaction => ({
    ...transaction,
    category: categorizeByRules(transaction),
    merchant: extractMerchant(transaction.description),
  }));
}

function categorizeByRules(transaction: Transaction): string {
  const description = transaction.description.toLowerCase();
  
  // Check each category's keywords
  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    for (const keyword of keywords) {
      if (description.includes(keyword)) {
        return category;
      }
    }
  }
  
  // Income transactions
  if (transaction.type === 'credit') {
    if (description.includes('salary') || description.includes('payroll') || description.includes('deposit')) {
      return 'Income';
    }
  }
  
  return 'Other';
}

function extractMerchant(description: string): string {
  // Clean up common transaction prefixes
  let cleaned = description
    .replace(/^(purchase|payment|withdrawal|deposit|transfer|pos|atm|online)\s+/i, '')
    .replace(/\s+\d{2}\/\d{2}.*$/, '') // Remove dates at end
    .replace(/\s+#\d+.*$/, '') // Remove reference numbers
    .replace(/\*+/g, '') // Remove asterisks
    .trim();
  
  // Extract merchant name (usually first part before special characters)
  const match = cleaned.match(/^([A-Za-z0-9\s&'-]+)/);
  if (match) {
    cleaned = match[1].trim();
  }
  
  // Title case
  return cleaned
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}