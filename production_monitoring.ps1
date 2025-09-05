# Production Monitoring Script for FreshNutrients AI Chat API
# Usage: .\production_monitoring.ps1 -ApiUrl "https://your-app.azurecontainerapps.io" -ApiKey "your-production-api-key"

param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$ApiKey = "your-secret-api-key-here",
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

function Get-Configuration {
    try {
        Write-Host "Checking configuration..." -ForegroundColor Blue
        $config = Invoke-RestMethod -Uri "$ApiUrl/admin/config" -Headers $headers -Method GET
        $cfg = $config.configuration
        
        Write-Host "=== SECURITY CONFIGURATION ===" -ForegroundColor Cyan
        Write-Host "API Auth: $($cfg.api_auth_enabled)" -ForegroundColor White
        Write-Host "Rate Limiting: $($cfg.rate_limiting.enabled)" -ForegroundColor White
        Write-Host "Requests/Hour: $($cfg.rate_limiting.requests_per_hour)" -ForegroundColor White
        Write-Host "HTTPS Redirect: $($cfg.https_redirect)" -ForegroundColor White
        Write-Host "Environment: $($cfg.environment)" -ForegroundColor White
        
        return $true
    }
    catch {
        Write-Host "✗ Configuration check failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Get-Errors {
    try {
        Write-Host "Checking error summary..." -ForegroundColor Blue
        $errors = Invoke-RestMethod -Uri "$ApiUrl/admin/errors" -Headers $headers -Method GET
        $summary = $errors.error_summary
        
        Write-Host "=== ERROR SUMMARY ===" -ForegroundColor Cyan
        Write-Host "Total Errors (24h): $($summary.total_errors)" -ForegroundColor White
        
        if ($summary.total_errors -gt 0) {
            Write-Host "Error Details:" -ForegroundColor Red
            if ($summary.error_types) {
                $summary.error_types.PSObject.Properties | ForEach-Object {
                    Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor White
                }
            }
        } else {
            Write-Host "✓ No errors in the last 24 hours" -ForegroundColor Green
        }
        
        return $true
    }
    catch {
        Write-Host "✗ Error summary failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution based on action
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
            Write-Host ""
            Get-Configuration
            Write-Host ""
            Get-Errors
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
    
    "config" {
        Get-Configuration
    }
    
    "errors" {
        Get-Errors
    }
    
    default {
        Write-Host "Available actions: dashboard, health, analytics, config, errors" -ForegroundColor Yellow
        Write-Host "Example: .\production_monitoring.ps1 -ApiUrl 'https://your-app.azurecontainerapps.io' -ApiKey 'your-key' -Action 'dashboard'" -ForegroundColor White
    }
}
