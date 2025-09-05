# Production Monitoring Script for FreshNutrients AI Chat API
# Usage: .\production_monitoring.ps1 -ApiUrl "https://your-app.azurecontainerapps.io" -ApiKey "your-production-api-key"

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$ApiKey,
    
    [string]$Action = "dashboard"
)

# Set up headers for authenticated requests
$headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host "=== FreshNutrients Production Monitoring ===" -ForegroundColor Green
Write-Host "API URL: $ApiUrl" -ForegroundColor Yellow
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

# Test basic health endpoint (no auth required)
function Test-BasicHealth {
    try {
        Write-Host "Testing basic health endpoint..." -ForegroundColor Blue
        $health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method GET
        Write-Host "✓ Basic Health: $($health.status)" -ForegroundColor Green
        Write-Host "  Database: $($health.database)" -ForegroundColor White
        Write-Host "  LLM Service: $($health.llm_service)" -ForegroundColor White
        Write-Host "  Version: $($health.version)" -ForegroundColor White
        return $true
    }
    catch {
        Write-Host "✗ Basic health check failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test admin endpoint access
function Test-AdminAccess {
    try {
        Write-Host "Testing admin authentication..." -ForegroundColor Blue
        $adminHealth = Invoke-RestMethod -Uri "$ApiUrl/admin/health" -Headers $headers -Method GET
        Write-Host "✓ Admin access working" -ForegroundColor Green
        Write-Host "  CPU: $($adminHealth.metrics.cpu_percent)%" -ForegroundColor White
        Write-Host "  Memory: $($adminHealth.metrics.memory_percent)%" -ForegroundColor White
        Write-Host "  Uptime: $([math]::Round($adminHealth.uptime_hours, 2)) hours" -ForegroundColor White
        return $true
    }
    catch {
        Write-Host "✗ Admin access failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Get usage analytics
function Get-Analytics {
    try {
        Write-Host "Retrieving usage analytics..." -ForegroundColor Blue
        $analytics = Invoke-RestMethod -Uri "$ApiUrl/admin/analytics" -Headers $headers -Method GET
        $data = $analytics.analytics
        
        Write-Host "=== USAGE ANALYTICS ===" -ForegroundColor Cyan
        Write-Host "Total Requests: $($data.total_requests)" -ForegroundColor White
        Write-Host "Unique Endpoints: $($data.unique_endpoints)" -ForegroundColor White
        Write-Host "Uptime: $([math]::Round($data.uptime_hours, 2)) hours" -ForegroundColor White
        
        if ($data.endpoint_usage) {
            Write-Host "Top Endpoints:" -ForegroundColor Yellow
            $data.endpoint_usage.PSObject.Properties | Sort-Object Value -Descending | ForEach-Object {
                Write-Host "  $($_.Name): $($_.Value) requests" -ForegroundColor White
            }
        }
        
        if ($data.error_summary -and $data.error_summary.PSObject.Properties.Count -gt 0) {
            Write-Host "Errors:" -ForegroundColor Red
            $data.error_summary.PSObject.Properties | ForEach-Object {
                Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor White
            }
        } else {
            Write-Host "✓ No errors detected" -ForegroundColor Green
        }
        
        return $true
    }
    catch {
        Write-Host "✗ Analytics retrieval failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Execute based on action
switch ($Action.ToLower()) {
    "dashboard" {
        Write-Host "Running full monitoring dashboard..." -ForegroundColor Magenta
        Write-Host ""
        
        $healthOk = Test-BasicHealth
        Write-Host ""
        
        $adminOk = Test-AdminAccess
        Write-Host ""
        
        if ($adminOk) {
            Get-Analytics
        }
        
        Write-Host ""
        Write-Host "=== SUMMARY ===" -ForegroundColor Green
        Write-Host "Basic Health: $(if ($healthOk) { '✓ OK' } else { '✗ FAILED' })" -ForegroundColor $(if ($healthOk) { 'Green' } else { 'Red' })
        Write-Host "Admin Access: $(if ($adminOk) { '✓ OK' } else { '✗ FAILED' })" -ForegroundColor $(if ($adminOk) { 'Green' } else { 'Red' })
    }
    
    "health" {
        Test-BasicHealth
        Test-AdminAccess
    }
    
    "analytics" {
        Get-Analytics
    }
    
    default {
        Write-Host "Available actions: dashboard, health, analytics" -ForegroundColor Yellow
        Write-Host "Example: .\production_monitoring.ps1 -ApiUrl 'https://your-app.azurecontainerapps.io' -ApiKey 'your-key'" -ForegroundColor White
    }
}
