# Personal Finance Dashboard

A comprehensive React-based financial dashboard for analyzing your spending patterns from bank statements.

**Live Demo**: [https://financecompare.netlify.app/](https://financecompare.netlify.app/)

## Features

- **Interactive Category Breakdown**: Click on any category to see detailed transactions
- **Monthly Trends**: Visualize spending patterns over time
- **Budget Analysis**: Track spending against budget targets
- **Multi-Format Support**: Import bank statements (CSV, PDF), including PayPal statements
- **AI-Powered Categorization**: Automatically categorize transactions using OpenAI
- **Responsive Design**: Works on desktop and mobile
- **Date Range Filtering**: View all time or specific periods

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Add Your Transaction Data

#### Option A: Upload PDF Statements
1. Export your bank/PayPal statements as PDF
2. Use the "Upload" tab in the dashboard
3. Supported formats:
   - Bank Current Account statements
   - Credit Card statements
   - PayPal monthly statements (MSR format)
4. The system automatically detects the statement type and extracts transactions

#### Option B: Upload CSV File
1. Export your bank statements as CSV
2. Use the "Upload" tab in the dashboard
3. Follow the format: `Date,Description,Amount,Category`

#### Option C: Manually Edit Sample Data
Edit `src/data/sampleData.js` with your actual transactions:

```javascript
export const transactions = [
  { 
    id: 1, 
    date: '2025-01-05', 
    description: 'Tesco Express', 
    amount: -45.67, 
    category: 'Groceries', 
    month: 'January' 
  },
  // Add more transactions...
];
```

### 3. Customize Budget Targets

Edit budget targets in `src/data/sampleData.js`:

```javascript
export const budgetTargets = {
  'Transport': 300,
  'Groceries': 400,
  'Restaurants': 200,
  // Add more categories...
};
```

### 4. Run Locally

```bash
npm start
```

Visit `http://localhost:3000` to view your dashboard.

## Deploy to Netlify

### Method 1: Drag & Drop

1. Build the project:
   ```bash
   npm run build
   ```

2. Go to [Netlify Drop](https://app.netlify.com/drop)

3. Drag the `build` folder to the upload area

### Method 2: Git Integration

1. Push this project to GitHub/GitLab/Bitbucket

2. Go to [Netlify](https://app.netlify.com)

3. Click "New site from Git"

4. Connect your repository

5. Configure build settings:
   - Build command: `npm run build`
   - Publish directory: `build`

6. Click "Deploy site"

### Method 3: Netlify CLI

1. Install Netlify CLI:
   ```bash
   npm install -g netlify-cli
   ```

2. Build and deploy:
   ```bash
   npm run build
   netlify deploy --prod --dir=build
   ```

## Converting PDF Statements to CSV

Since your bank statements are in PDF format, you'll need to convert them to CSV:

### Manual Method:
1. Copy transaction data from PDF
2. Paste into Excel/Google Sheets
3. Format columns: Date, Description, Amount, Category
4. Export as CSV

### Automated Method:
Use a PDF to CSV converter tool or service

## Data Categories

The dashboard automatically categorizes transactions based on keywords:
- **Groceries**: Tesco, Sainsbury's, ASDA, Waitrose
- **Transport**: TfL, Uber, Rail
- **Fast Food**: McDonald's, KFC, Burger King
- **Coffee Shops**: Costa, Starbucks, Pret
- **Food Delivery**: Deliveroo, Just Eat, Uber Eats
- **Fuel**: Shell, BP, Esso, Petrol
- **Subscriptions**: Netflix, Spotify, Amazon Prime
- **Restaurants**: Restaurant names, Wagamama, Nando's
- **Other**: Everything else

You can modify the categorization logic in `src/components/DataUpload.js`.

## Environment Variables (Optional)

Create a `.env` file for any API keys or configuration:

```
REACT_APP_API_KEY=your-api-key
```

### For PDF Processing API

The PDF processing requires a backend API with the following environment variables:

```
OPENAI_API_KEY=your-openai-api-key  # For AI-powered categorization
GOOGLE_CLOUD_CREDENTIALS=your-google-cloud-credentials-json  # For OCR processing
```

The API supports:
- Google Vision API for OCR
- Document AI for enhanced PDF processing
- OpenAI GPT-4 for intelligent transaction categorization
- Specialized processors for different statement types (Bank, Credit Card, PayPal)

## Troubleshooting

1. **Blank Page**: Check console for errors, ensure all dependencies are installed
2. **CSV Upload Fails**: Verify CSV format matches the expected structure
3. **Missing Categories**: Add new category colors in `src/data/sampleData.js`

## Future Enhancements

- Export reports as PDF
- Set spending alerts
- Connect to bank APIs for automatic updates
- Add savings goals tracking
- Include investment tracking

## License

MIT