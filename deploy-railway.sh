#!/bin/bash
# Railway deployment script

echo "🚀 Deploying FreshNutrients Chatbot to Railway..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Initializing..."
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
fi

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔐 Please login to Railway..."
railway login

# Initialize Railway project
echo "🎯 Initializing Railway project..."
railway init

# Set environment variables
echo "⚙️ Setting environment variables..."
echo "Please set these in Railway dashboard:"
echo "- AZURE_OPENAI_API_KEY"
echo "- AZURE_OPENAI_ENDPOINT" 
echo "- DATABASE_URL"
echo "- PORT=8000"

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo "Your API will be available at the Railway-provided URL"
