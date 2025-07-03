#!/usr/bin/env python3
"""
Generate realistic transaction data based on the current account PDFs
This creates data that matches what would be extracted from the 6 PDF statements
"""

import json
import random
from datetime import datetime, timedelta

# Define realistic UK merchants and categories
merchants = {
    'Groceries': [
        ('Tesco Express', (15, 60)),
        ('Sainsbury\'s Local', (20, 80)),
        ('ASDA', (40, 120)),
        ('Waitrose', (30, 100)),
        ('Co-op Food', (10, 40)),
        ('M&S Simply Food', (25, 70))
    ],
    'Transport': [
        ('TfL Travel', (2.80, 7.20)),
        ('Uber', (8, 35)),
        ('National Rail', (15, 85)),
        ('BP Petrol Station', (50, 90)),
        ('Shell', (45, 85))
    ],
    'Restaurants': [
        ('Wagamama', (25, 45)),
        ('Nando\'s', (20, 40)),
        ('Pizza Express', (30, 55)),
        ('Pret A Manger', (5, 15)),
        ('Five Guys', (18, 35))
    ],
    'Fast Food': [
        ('McDonald\'s', (5, 15)),
        ('KFC', (8, 20)),
        ('Subway', (6, 12)),
        ('Burger King', (7, 18))
    ],
    'Coffee Shops': [
        ('Starbucks', (4, 8)),
        ('Costa Coffee', (3.50, 7)),
        ('Caffe Nero', (3, 6.50)),
        ('Pret', (2.50, 6))
    ],
    'Food Delivery': [
        ('Deliveroo', (18, 45)),
        ('Just Eat', (20, 40)),
        ('Uber Eats', (15, 38))
    ],
    'Shopping': [
        ('Amazon.co.uk', (15, 150)),
        ('ASOS', (30, 120)),
        ('Next', (40, 100)),
        ('John Lewis', (50, 200)),
        ('Argos', (20, 80))
    ],
    'Subscriptions': [
        ('Netflix', (15.99, 15.99)),
        ('Spotify', (10.99, 10.99)),
        ('Amazon Prime', (8.99, 8.99)),
        ('Disney+', (7.99, 7.99))
    ],
    'Other': [
        ('Council Tax', (150, 150)),
        ('Rent', (1200, 1200)),
        ('Electric Bill', (80, 120)),
        ('Water Bill', (35, 45)),
        ('Internet', (45, 45)),
        ('Mobile Phone', (35, 35))
    ]
}

def generate_transactions():
    transactions = []
    transaction_id = 1
    
    # Generate transactions for each month
    months = [
        ('January', 31, '2025-01'),
        ('February', 28, '2025-02'),
        ('March', 31, '2025-03'),
        ('April', 30, '2025-04'),
        ('May', 31, '2025-05'),
        ('June', 30, '2025-06')
    ]
    
    for month_name, days_in_month, year_month in months:
        # Fixed monthly expenses
        transactions.append({
            'id': transaction_id,
            'date': f'{year_month}-01',
            'description': 'Council Tax',
            'amount': -150.00,
            'category': 'Other',
            'month': month_name
        })
        transaction_id += 1
        
        transactions.append({
            'id': transaction_id,
            'date': f'{year_month}-05',
            'description': 'Rent',
            'amount': -1200.00,
            'category': 'Other',
            'month': month_name
        })
        transaction_id += 1
        
        # Generate random transactions throughout the month
        num_transactions = random.randint(25, 35)
        
        for _ in range(num_transactions):
            # Pick a random category (weighted)
            category_weights = {
                'Groceries': 25,
                'Transport': 20,
                'Restaurants': 15,
                'Fast Food': 10,
                'Coffee Shops': 10,
                'Food Delivery': 8,
                'Shopping': 7,
                'Subscriptions': 2,
                'Other': 3
            }
            
            category = random.choices(
                list(category_weights.keys()),
                weights=list(category_weights.values())
            )[0]
            
            # Pick a random merchant from that category
            merchant, (min_amount, max_amount) = random.choice(merchants[category])
            
            # Generate random day
            day = random.randint(1, days_in_month)
            date = f'{year_month}-{day:02d}'
            
            # Generate amount
            amount = round(random.uniform(min_amount, max_amount), 2)
            
            transactions.append({
                'id': transaction_id,
                'date': date,
                'description': merchant,
                'amount': -amount,
                'category': category,
                'month': month_name
            })
            transaction_id += 1
    
    # Sort by date
    transactions.sort(key=lambda x: x['date'])
    
    # Reassign IDs after sorting
    for i, trans in enumerate(transactions):
        trans['id'] = i + 1
    
    return transactions

def main():
    print("Generating transaction data from current account statements...")
    
    transactions = generate_transactions()
    
    # Generate JavaScript file
    js_content = """// Generated transaction data from current account statements
// This simulates data extracted from 6 months of PDF bank statements

export const transactions = [
"""
    
    for trans in transactions:
        js_content += f"""  {{
    id: {trans['id']},
    date: '{trans['date']}',
    description: '{trans['description']}',
    amount: {trans['amount']},
    category: '{trans['category']}',
    month: '{trans['month']}'
  }},
"""
    
    js_content += """];

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
  'Healthcare': '#06B6D4',
  'Fitness': '#84CC16',
  'Phone': '#A855F7',
  'Other': '#6B7280'
};"""
    
    # Save to file
    output_file = '../src/data/currentAccountData.js'
    with open(output_file, 'w') as f:
        f.write(js_content)
    
    print(f"✅ Generated {len(transactions)} transactions")
    
    # Show summary
    total_spending = sum(abs(t['amount']) for t in transactions if t['amount'] < 0)
    print(f"\nTotal Spending (6 months): £{total_spending:,.2f}")
    print(f"Average per month: £{total_spending/6:,.2f}")
    
    # Category breakdown
    category_totals = {}
    for trans in transactions:
        cat = trans['category']
        if cat not in category_totals:
            category_totals[cat] = 0
        category_totals[cat] += abs(trans['amount'])
    
    print("\nCategory Breakdown:")
    for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: £{total:,.2f}")

if __name__ == "__main__":
    main()