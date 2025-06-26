# FinanceCompare Deployment Guide

This guide provides detailed instructions for deploying FinanceCompare to Netlify (frontend) and Render (backend).

## Prerequisites

Before deploying, ensure you have:
- A GitHub account with the FinanceCompare repository
- An OpenAI API key (get one at https://platform.openai.com)
- Accounts on Netlify and Render (free tiers work fine)

## Step 1: Prepare Your Repository

1. Push all code to GitHub:
   ```bash
   cd /Users/safmy/Desktop/FinanceCompare
   git add .
   git commit -m "Initial commit - FinanceCompare application"
   git push origin main
   ```

## Step 2: Deploy Backend API to Render

1. **Sign up/Login to Render**: Go to https://render.com

2. **Create New Web Service**:
   - Click "New +" button
   - Select "Web Service"
   - Connect your GitHub account if not already connected
   - Select the `FinanceCompare` repository

3. **Configure the Service**:
   - **Name**: `finance-compare-api` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

4. **Set Environment Variables**:
   Click "Advanced" and add:
   - `OPENAI_API_KEY` = `your-openai-api-key-here`
   - `PYTHON_VERSION` = `3.11`

5. **Choose Instance Type**:
   - Free tier is sufficient for personal use
   - Upgrade if you need better performance

6. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment (takes 5-10 minutes)
   - Note your API URL: `https://finance-compare-api.onrender.com`

## Step 3: Deploy Frontend to Netlify

1. **Sign up/Login to Netlify**: Go to https://app.netlify.com

2. **Import Project**:
   - Click "Add new site" > "Import an existing project"
   - Choose "GitHub"
   - Authorize Netlify to access your GitHub
   - Select the `FinanceCompare` repository

3. **Configure Build Settings**:
   - **Base directory**: (leave empty)
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
   - **Functions directory**: (leave empty)

4. **Set Environment Variables**:
   Click "Show advanced" > "New variable":
   - **Key**: `VITE_API_URL`
   - **Value**: Your Render API URL (e.g., `https://finance-compare-api.onrender.com`)

5. **Deploy**:
   - Click "Deploy site"
   - Wait for build to complete (2-5 minutes)
   - Your site will be available at a URL like: `https://amazing-name-123.netlify.app`

6. **Custom Domain (Optional)**:
   - Go to "Domain settings"
   - Add your custom domain
   - Follow DNS configuration instructions

## Step 4: Post-Deployment Configuration

### Update API URL in Netlify

If you deployed Netlify before Render:
1. Go to Netlify dashboard
2. Site settings > Environment variables
3. Update `VITE_API_URL` with your Render URL
4. Trigger a redeploy: Deploys > "Trigger deploy"

### Enable CORS (if needed)

The API already has CORS configured, but if you have issues:
1. In Render dashboard, add environment variable:
   - `ALLOWED_ORIGINS` = `https://your-netlify-url.netlify.app`

### Monitor Your Services

**Render**:
- Free tier spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- Check logs: Dashboard > Logs

**Netlify**:
- 100GB bandwidth/month on free tier
- Check analytics: Dashboard > Analytics

## Step 5: Testing Your Deployment

1. **Visit your Netlify URL**
2. **Test file upload**:
   - Create a sample CSV file:
   ```csv
   Date,Description,Amount
   2024-01-15,Amazon Purchase,-45.99
   2024-01-16,Salary Deposit,3000.00
   2024-01-17,Grocery Store,-125.50
   ```
   - Upload and verify processing

3. **Check all features**:
   - Transaction categorization
   - Analytics charts
   - Filtering and sorting

## Troubleshooting

### API Not Responding
- Check Render logs for errors
- Verify environment variables are set
- Ensure API is not sleeping (free tier limitation)

### File Upload Fails
- Check browser console for errors
- Verify CORS is properly configured
- Check file size (limit is 10MB)

### OpenAI Errors
- Verify API key is correct
- Check OpenAI usage limits
- Review API response in Render logs

### Build Failures

**Netlify**:
- Check build logs
- Verify Node version compatibility
- Clear cache and retry: "Clear cache and deploy site"

**Render**:
- Check Python version
- Verify requirements.txt is correct
- Review build logs for missing dependencies

## Cost Optimization

### Free Tier Limits
- **Netlify**: 100GB bandwidth, 300 build minutes/month
- **Render**: 750 hours/month, spins down after 15 min inactivity
- **OpenAI**: Pay-per-use, ~$0.002 per transaction categorization

### Recommendations
1. Use client-side caching to reduce API calls
2. Batch transaction processing
3. Implement rate limiting for production use
4. Consider upgrading Render for always-on service

## Security Best Practices

1. **Never commit API keys**:
   - Always use environment variables
   - Add `.env` to `.gitignore`

2. **Limit file uploads**:
   - Current limit: 10MB
   - Only accept specific file types

3. **Sanitize user input**:
   - All data is validated before processing
   - No direct database queries

4. **Use HTTPS**:
   - Both Netlify and Render provide SSL certificates
   - Ensure all API calls use HTTPS

## Updating Your Application

### Frontend Updates
1. Push changes to GitHub
2. Netlify auto-deploys from main branch
3. Or manually trigger: Deploys > "Trigger deploy"

### Backend Updates
1. Push changes to GitHub
2. Render auto-deploys from main branch
3. Monitor logs during deployment

### Database Integration (Future)

If you want to add data persistence:
1. Add PostgreSQL to Render ($7/month)
2. Update API to store processed transactions
3. Add user authentication
4. Implement data export features

## Support

For issues:
1. Check deployment logs
2. Review error messages in browser console
3. Open an issue on GitHub
4. Check service status pages

Remember to keep your API keys secure and monitor your usage to avoid unexpected charges!