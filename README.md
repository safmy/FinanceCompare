# FinanceCompare

A smart financial analysis web application that helps you understand your spending patterns by analyzing bank statements.

## Features

- 📤 **Multi-format Support**: Upload bank statements in CSV, PDF, XLS, or XLSX formats
- 🤖 **AI-Powered Categorization**: Automatically categorizes transactions using OpenAI
- 📊 **Visual Analytics**: Interactive charts showing spending by category, monthly trends, and top merchants
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- 🔍 **Smart Parsing**: Intelligently extracts transaction data from various bank formats
- 📈 **Comprehensive Reports**: View spending patterns over weeks, months, or years

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Chart.js
- **Backend**: Python, Flask, OpenAI API
- **Deployment**: Netlify (frontend), Render (backend)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- OpenAI API key

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/safmy/FinanceCompare.git
   cd FinanceCompare
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Set up Python environment for the API:
   ```bash
   cd api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   Add your OpenAI API key to the `.env` file.

5. Start the backend API:
   ```bash
   cd api
   python app.py
   ```

6. In a new terminal, start the frontend:
   ```bash
   npm run dev
   ```

7. Open http://localhost:3000 in your browser

## Deployment

### Deploy to Netlify (Frontend)

1. Fork this repository to your GitHub account

2. Go to [Netlify](https://app.netlify.com)

3. Click "Add new site" > "Import an existing project"

4. Connect your GitHub account and select the FinanceCompare repository

5. Configure build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Add environment variable: `VITE_API_URL` = `https://your-render-api-url.onrender.com`

6. Click "Deploy site"

### Deploy to Render (Backend API)

1. Go to [Render](https://render.com)

2. Click "New +" > "Web Service"

3. Connect your GitHub account and select the FinanceCompare repository

4. Configure the service:
   - Name: `finance-compare-api`
   - Environment: `Python`
   - Build Command: `cd api && pip install -r requirements.txt`
   - Start Command: `cd api && gunicorn app:app`

5. Add environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PYTHON_VERSION`: `3.11`

6. Click "Create Web Service"

7. Once deployed, update your Netlify environment variable `VITE_API_URL` with the Render URL

## Usage

1. **Upload Bank Statements**: Drag and drop or click to upload your bank statement files
2. **Automatic Processing**: The app will parse and categorize your transactions
3. **View Analytics**: Explore your spending patterns through interactive charts
4. **Filter and Sort**: Use the transaction list to filter by category and sort by date or amount

## Supported Bank Formats

The app automatically detects and parses common CSV formats from major banks. For best results:
- Ensure CSV files have headers
- PDF statements should be text-based (not scanned images)
- Excel files should have transaction data in the first sheet

## Privacy & Security

- All processing happens in real-time - we don't store your financial data
- Bank statements are processed and immediately discarded
- Only aggregated analytics are displayed
- API calls to OpenAI contain only transaction descriptions, not personal information

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

MIT