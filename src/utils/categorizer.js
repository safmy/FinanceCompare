// Enhanced categorization rules for better transaction classification

export const categorizeTransaction = (description, amount) => {
  const desc = description.toUpperCase();
  
  // Income patterns
  if (desc.includes('PAYSTREAM') || desc.includes('SALARY') || 
      desc.includes('PAYMENT THANK YOU') || desc.includes('PAYMENT RECEIVED') ||
      desc.includes('WAGES') || desc.includes('BONUS') || desc.includes('REFUND') ||
      desc.includes('REIMBURSEMENT') || desc.includes('CR PAYMENT')) {
    return 'Income';
  }
  
  // Rent patterns
  if (desc.includes('RENT') || desc.includes('SCHOLARS WALK') || 
      desc.includes('PROPERTY MANAGEMENT') || desc.includes('LANDLORD') ||
      (desc.includes('SO ') && desc.includes(' WALK')) || 
      (desc.includes('SO ') && Math.abs(amount) >= 800)) {
    return 'Rent';
  }
  
  // Insurance patterns
  if (desc.includes('INSURANCE') || desc.includes(' INS') || desc.includes('ANSWER INS') ||
      desc.includes('AVIVA') || desc.includes('AXA') || desc.includes('BUPA') ||
      desc.includes('VITALITY') || desc.includes('ADMIRAL')) {
    return 'Insurance';
  }
  
  // Bills & Utilities
  if (desc.includes('DD EE') || desc.includes('DDEE') || desc.includes('ELECTRIC') || 
      desc.includes('GAS') || desc.includes('WATER') || desc.includes('EE LIMITED') ||
      desc.includes('BRITISH GAS') || desc.includes('EDF ENERGY') || desc.includes('BT GROUP') ||
      desc.includes('VIRGIN MEDIA') || desc.includes('SKY DIGITAL') || desc.includes('COUNCIL TAX')) {
    return 'Bills & Utilities';
  }
  
  // Financial Services
  if (desc.includes('HSBC') || desc.includes('LOAN') || desc.includes('PAYPAL') || 
      desc.includes('ATM') || desc.includes('BANK') || desc.includes('OVERDRAFT') ||
      desc.includes('INTEREST') || desc.includes('FEE') || desc.includes('CHARGE')) {
    return 'Financial Services';
  }
  
  // Groceries
  if (desc.includes('SAINSBURY') || desc.includes('TESCO') || desc.includes('ASDA') || 
      desc.includes('BUDGENS') || desc.includes('CO-OP') || desc.includes('ALDI') || 
      desc.includes('LIDL') || desc.includes('WAITROSE') || desc.includes('MORRISONS') ||
      desc.includes('ICELAND') || desc.includes('M&S FOOD')) {
    return 'Groceries';
  }
  
  // Transport
  if (desc.includes('TFL') || desc.includes('UBER') || desc.includes('TAXI') || 
      desc.includes('TRAIN') || desc.includes('RAIL') || desc.includes('OYSTER') ||
      desc.includes('CITYMAPPER') || desc.includes('BOLT') || desc.includes('LIME')) {
    return 'Transport';
  }
  
  // Fuel
  if (desc.includes('SHELL') || desc.includes('BP ') || desc.includes('ESSO') || 
      desc.includes('TEXACO') || desc.includes('GULF') || desc.includes('PETROL') ||
      desc.includes('FUEL')) {
    return 'Fuel';
  }
  
  // Parking
  if (desc.includes('PARKING') || desc.includes('RINGGO') || desc.includes('NCP') ||
      desc.includes('APCOA') || desc.includes('PARKOPEDIA')) {
    return 'Parking';
  }
  
  // Fast Food
  if (desc.includes('GREGGS') || desc.includes('MCDONALD') || desc.includes('KFC') || 
      desc.includes('SUBWAY') || desc.includes('BURGER') || desc.includes('PIZZA HUT') ||
      desc.includes('DOMINOS') || desc.includes('PAPA JOHNS')) {
    return 'Fast Food';
  }
  
  // Coffee Shops
  if (desc.includes('CAFFE NERO') || desc.includes('STARBUCKS') || desc.includes('COSTA') || 
      desc.includes('PRET A MANGER') || desc.includes('PRET') || desc.includes('COFFEE')) {
    return 'Coffee Shops';
  }
  
  // Shopping
  if (desc.includes('AMAZON') || desc.includes('PRIMARK') || desc.includes('T K MAXX') || 
      desc.includes('TK MAXX') || desc.includes('H & M') || desc.includes('H&M') || 
      desc.includes('BOOTS') || desc.includes('HOLLAND & BARRETT') || desc.includes('APPLE.COM') || 
      desc.includes('GOOGLE') || desc.includes('AUDIBLE') || desc.includes('IKEA') || 
      desc.includes('ARGOS') || desc.includes('B & Q') || desc.includes('B&Q') || 
      desc.includes('JOHN LEWIS') || desc.includes('NEXT') || desc.includes('ZARA') || 
      desc.includes('EBAY') || desc.includes('ETSY') || desc.includes('ASOS') ||
      desc.includes('UNIQLO') || desc.includes('DECATHLON')) {
    return 'Shopping';
  }
  
  // Entertainment/Subscriptions
  if (desc.includes('LITTLE GYM') || desc.includes('CINEMA') || desc.includes('EVERYONE ACTIVE') || 
      desc.includes('NETFLIX') || desc.includes('SPOTIFY') || desc.includes('GYM') ||
      desc.includes('PLAYSTATION') || desc.includes('XBOX') || desc.includes('NINTENDO') || 
      desc.includes('DISNEY') || desc.includes('PRIME VIDEO') || desc.includes('YOUTUBE') ||
      desc.includes('APPLE MUSIC') || desc.includes('AUDIBLE')) {
    return 'Entertainment';
  }
  
  // Subscriptions (recurring payments)
  if (desc.includes('DD ') && !desc.includes('DD EE') && !desc.includes('DDEE')) {
    // Direct debits are often subscriptions
    if (desc.includes('GOCARDLESS')) {
      return 'Subscriptions';
    }
  }
  
  // Restaurants
  if (desc.includes('NANDO') || desc.includes('WAGAMAMA') || desc.includes('PIZZA EXPRESS') || 
      desc.includes('RESTAURANT') || desc.includes('DINING') || desc.includes('GRILL')) {
    return 'Restaurants';
  }
  
  // Healthcare
  if (desc.includes('PHARMA') || desc.includes('CHEMIST') || desc.includes('MEDICAL') || 
      desc.includes('DOCTOR') || desc.includes('DENTAL') || desc.includes('NHS') ||
      desc.includes('HOSPITAL') || desc.includes('CLINIC')) {
    return 'Healthcare';
  }
  
  // Food Delivery
  if (desc.includes('DELIVEROO') || desc.includes('JUST EAT') || desc.includes('UBER EATS')) {
    return 'Food Delivery';
  }
  
  // Personal Care
  if (desc.includes('BARBER') || desc.includes('HAIR') || desc.includes('BEAUTY') || 
      desc.includes('SPA') || desc.includes('NAIL') || desc.includes('SALON')) {
    return 'Personal Care';
  }
  
  // Charity
  if (desc.includes('CHARITY') || desc.includes('DONATION') || desc.includes('OXFAM') ||
      desc.includes('RED CROSS') || desc.includes('UNICEF')) {
    return 'Charity';
  }
  
  // Travel
  if (desc.includes('HOTEL') || desc.includes('AIRBNB') || desc.includes('BOOKING.COM') ||
      desc.includes('EXPEDIA') || desc.includes('FLIGHT') || desc.includes('AIRLINE')) {
    return 'Travel';
  }
  
  // Education
  if (desc.includes('UNIVERSITY') || desc.includes('COLLEGE') || desc.includes('SCHOOL') ||
      desc.includes('COURSE') || desc.includes('TUITION') || desc.includes('EDUCATION')) {
    return 'Education';
  }
  
  // Cash withdrawals
  if (desc.includes('ATM CASH') || desc.includes('CASH WITHDRAWAL')) {
    return 'Cash';
  }
  
  // Bills pattern for transfers
  if (desc.includes('BP ') && desc.includes('BILLS')) {
    return 'Bills & Utilities';
  }
  
  // Default to Other
  return 'Other';
};

// Function to re-categorize all transactions
export const recategorizeTransactions = (transactions) => {
  return transactions.map(transaction => {
    // Only recategorize if currently "Other"
    if (transaction.category === 'Other') {
      const newCategory = categorizeTransaction(transaction.description, transaction.amount);
      return { ...transaction, category: newCategory };
    }
    return transaction;
  });
};

// Function to analyze and suggest better categorization
export const analyzeCategories = (transactions) => {
  const suggestions = {};
  
  transactions.forEach(transaction => {
    if (transaction.category === 'Other') {
      const suggestedCategory = categorizeTransaction(transaction.description, transaction.amount);
      if (suggestedCategory !== 'Other') {
        if (!suggestions[transaction.description]) {
          suggestions[transaction.description] = {
            currentCategory: 'Other',
            suggestedCategory,
            count: 0,
            totalAmount: 0
          };
        }
        suggestions[transaction.description].count++;
        suggestions[transaction.description].totalAmount += Math.abs(transaction.amount);
      }
    }
  });
  
  return suggestions;
};