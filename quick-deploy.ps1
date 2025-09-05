# Quick Deployment Script for FreshNutrients Chatbot
# This script helps you deploy to various platforms quickly

Write-Host "🚀 FreshNutrients Chatbot - Quick Deploy Options" -ForegroundColor Green
Write-Host ""

Write-Host "Available deployment options:" -ForegroundColor Yellow
Write-Host "1. ngrok (Local tunnel - Recommended for testing)"
Write-Host "2. Railway (Cloud deployment - Free tier)"
Write-Host "3. Render (Cloud deployment - Free tier)"
Write-Host "4. Heroku (Cloud deployment)"
Write-Host ""

$choice = Read-Host "Select option (1-4)"

switch ($choice) {
    "1" {
        Write-Host "Setting up ngrok tunnel..." -ForegroundColor Green
        Write-Host ""
        Write-Host "1. Download ngrok from: https://ngrok.com/download" -ForegroundColor Cyan
        Write-Host "2. Extract ngrok.exe to this folder" -ForegroundColor Cyan
        Write-Host "3. Run: .\ngrok.exe http 8000" -ForegroundColor Cyan
        Write-Host "4. Share the https://xyz.ngrok.io URL with colleagues" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Your server should be running on port 8000 first!" -ForegroundColor Yellow
    }
    "2" {
        Write-Host "Railway deployment setup..." -ForegroundColor Green
        Write-Host "1. Install Railway CLI: npm install -g @railway/cli" -ForegroundColor Cyan
        Write-Host "2. railway login" -ForegroundColor Cyan
        Write-Host "3. railway init" -ForegroundColor Cyan
        Write-Host "4. railway deploy" -ForegroundColor Cyan
    }
    "3" {
        Write-Host "Render deployment setup..." -ForegroundColor Green
        Write-Host "1. Go to https://render.com" -ForegroundColor Cyan
        Write-Host "2. Connect your GitHub repo" -ForegroundColor Cyan
        Write-Host "3. Create new Web Service" -ForegroundColor Cyan
        Write-Host "4. Use: uvicorn app.main:app --host 0.0.0.0 --port $PORT" -ForegroundColor Cyan
    }
    "4" {
        Write-Host "Heroku deployment setup..." -ForegroundColor Green
        Write-Host "1. Install Heroku CLI" -ForegroundColor Cyan
        Write-Host "2. heroku create your-app-name" -ForegroundColor Cyan
        Write-Host "3. git push heroku main" -ForegroundColor Cyan
    }
    default {
        Write-Host "Invalid option selected" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "💡 For quick testing, ngrok is the fastest option!" -ForegroundColor Green
Write-Host "💡 For permanent hosting, use Railway or Render free tiers!" -ForegroundColor Green
