# Simple Production Monitoring for FreshNutrients AI Chat API
param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$ApiKey = "your-secret-api-key-here"
)

$headers = @{ "Authorization" = "Bearer $ApiKey" }

Write-Host "=== Production Monitoring Dashboard ===" -ForegroundColor Green
Write-Host "API: $ApiUrl" -ForegroundColor Yellow
Write-Host ""

# Test basic health
try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/health"
    Write-Host "✓ Basic Health: $($health.status)" -ForegroundColor Green
    Write-Host "  Database: $($health.database)" -ForegroundColor White
    Write-Host "  Version: $($health.version)" -ForegroundColor White
}
catch {
    Write-Host "✗ Health check failed" -ForegroundColor Red
}

Write-Host ""

# Test admin access
try {
    $admin = Invoke-RestMethod -Uri "$ApiUrl/admin/health" -Headers $headers
    Write-Host "✓ Admin Access Working" -ForegroundColor Green
    Write-Host "  CPU: $($admin.metrics.cpu_percent)%" -ForegroundColor White
    Write-Host "  Memory: $($admin.metrics.memory_percent)%" -ForegroundColor White
}
catch {
    Write-Host "✗ Admin access failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Get analytics
try {
    $analytics = Invoke-RestMethod -Uri "$ApiUrl/admin/analytics" -Headers $headers
    $data = $analytics.analytics
    Write-Host "=== USAGE ANALYTICS ===" -ForegroundColor Cyan
    Write-Host "Total Requests: $($data.total_requests)" -ForegroundColor White
    Write-Host "Unique Endpoints: $($data.unique_endpoints)" -ForegroundColor White
    Write-Host "Uptime: $([math]::Round($data.uptime_hours * 60, 1)) minutes" -ForegroundColor White
}
catch {
    Write-Host "✗ Analytics failed" -ForegroundColor Red
}
