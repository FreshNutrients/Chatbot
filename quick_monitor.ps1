# Simple Production Monitor
param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$ApiKey = "your-secret-api-key-here"
)

$headers = @{ "Authorization" = "Bearer $ApiKey" }

Write-Host "=== Production Monitor ===" -ForegroundColor Green
Write-Host "API: $ApiUrl"
Write-Host ""

# Basic Health Check
Write-Host "1. Testing Basic Health..." -ForegroundColor Blue
try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/health"
    Write-Host "   Status: $($health.status)" -ForegroundColor Green
    Write-Host "   Database: $($health.database)"
    Write-Host "   Version: $($health.version)"
}
catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Admin Health Check
Write-Host "2. Testing Admin Access..." -ForegroundColor Blue
try {
    $admin = Invoke-RestMethod -Uri "$ApiUrl/admin/health" -Headers $headers
    Write-Host "   Admin Status: Working" -ForegroundColor Green
    Write-Host "   CPU: $($admin.metrics.cpu_percent)%"
    Write-Host "   Memory: $($admin.metrics.memory_percent)%"
    Write-Host "   Uptime: $([math]::Round($admin.uptime_hours, 2)) hours"
}
catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Analytics
Write-Host "3. Getting Analytics..." -ForegroundColor Blue
try {
    $analytics = Invoke-RestMethod -Uri "$ApiUrl/admin/analytics" -Headers $headers
    $data = $analytics.analytics
    Write-Host "   Total Requests: $($data.total_requests)" -ForegroundColor Green
    Write-Host "   Unique Endpoints: $($data.unique_endpoints)"
    Write-Host "   Uptime: $([math]::Round($data.uptime_hours * 60, 1)) minutes"
    
    if ($data.endpoint_usage) {
        Write-Host "   Top Endpoints:"
        $data.endpoint_usage.PSObject.Properties | Sort-Object Value -Descending | Select-Object -First 5 | ForEach-Object {
            Write-Host "     $($_.Name): $($_.Value)"
        }
    }
}
catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Configuration
Write-Host "4. Checking Security Config..." -ForegroundColor Blue
try {
    $config = Invoke-RestMethod -Uri "$ApiUrl/admin/config" -Headers $headers
    $cfg = $config.configuration
    Write-Host "   API Auth: $($cfg.api_auth_enabled)" -ForegroundColor Green
    Write-Host "   Rate Limiting: $($cfg.rate_limiting.enabled)"
    Write-Host "   Environment: $($cfg.environment)"
}
catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Monitor Complete ===" -ForegroundColor Green
