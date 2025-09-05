# PowerShell script for Railway deployment

Write-Host "Railway FreshNutrients Chatbot - Railway Deployment" -ForegroundColor Green
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
}

# Check current status
Write-Host "Current git status:" -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "Railway Deployment Steps:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Push to GitHub:" -ForegroundColor Yellow
Write-Host "   git add ." -ForegroundColor White
Write-Host "   git commit -m 'Deploy to Railway'" -ForegroundColor White
Write-Host "   git push origin main" -ForegroundColor White
Write-Host ""
Write-Host "2. Go to https://railway.app" -ForegroundColor Yellow
Write-Host "3. Sign up with GitHub" -ForegroundColor Yellow
Write-Host "4. Click 'Start a New Project' > 'Deploy from GitHub repo'" -ForegroundColor Yellow
Write-Host "5. Select your FreshNutrients repository" -ForegroundColor Yellow
Write-Host ""
Write-Host "6. Add Environment Variables in Railway:" -ForegroundColor Yellow
Write-Host "   - AZURE_OPENAI_API_KEY = your_api_key" -ForegroundColor White
Write-Host "   - AZURE_OPENAI_ENDPOINT = your_endpoint" -ForegroundColor White  
Write-Host "   - DATABASE_URL = your_azure_sql_connection" -ForegroundColor White
Write-Host "   - PORT = 8000" -ForegroundColor White
Write-Host ""
Write-Host "7. Railway will auto-deploy and give you a permanent URL!" -ForegroundColor Yellow
Write-Host ""

$deploy = Read-Host "Push to GitHub now? (y/n)"

if ($deploy -eq "y" -or $deploy -eq "Y") {
    Write-Host "Pushing to GitHub..." -ForegroundColor Green
    git add .
    git commit -m "Deploy to Railway - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    
    # Check if remote origin exists
    $remoteExists = git remote get-url origin 2>$null
    if (-not $remoteExists) {
        Write-Host "No GitHub remote found. Please add your GitHub repository:" -ForegroundColor Red
        Write-Host "   git remote add origin https://github.com/yourusername/yourrepo.git" -ForegroundColor White
    } else {
        git push origin main
        Write-Host "Pushed to GitHub! Now go to railway.app to deploy." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Benefits of Railway:" -ForegroundColor Cyan
Write-Host "   Always running (24/7)" -ForegroundColor Green
Write-Host "   Free tier available" -ForegroundColor Green
Write-Host "   Automatic HTTPS" -ForegroundColor Green
Write-Host "   Custom domains" -ForegroundColor Green
Write-Host "   Auto-deploy on git push" -ForegroundColor Green
