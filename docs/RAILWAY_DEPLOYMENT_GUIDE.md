# Railway Deployment Guide for FreshNutrients Chatbot

## 🚀 Quick Railway Deployment (5 minutes setup)

### Prerequisites
- GitHub account
- Your code pushed to GitHub

### Step 1: Prepare Your Project
```bash
# Make sure your code is on GitHub
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Railway Setup
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "Start a New Project"
4. Select "Deploy from GitHub repo"
5. Choose your FreshNutrients chatbot repository

### Step 3: Environment Variables
Add these environment variables in Railway dashboard:
- `AZURE_OPENAI_API_KEY` = your_api_key
- `AZURE_OPENAI_ENDPOINT` = your_endpoint
- `DATABASE_URL` = your_azure_sql_connection
- `PORT` = 8000

### Step 4: Deploy
Railway will automatically:
- Detect Python project
- Use the Procfile we created
- Install requirements.txt
- Deploy and give you a public URL

### Result
- ✅ 24/7 availability
- ✅ Automatic HTTPS
- ✅ Custom domain option
- ✅ Free tier: 500 hours/month
- ✅ Auto-deploys on git push

## Alternative: Render.com
Similar process, also free tier available.

## Alternative: Heroku
More complex, has pricing changes.
