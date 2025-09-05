# Cost Optimization Monitoring Script
# Run this daily/weekly to monitor optimized app performance

Write-Host "=== OPTIMIZED APP PERFORMANCE MONITOR ===" -ForegroundColor Green
Write-Host "Monitoring cost-optimized application..." -ForegroundColor Yellow

# Performance Test Function
function Test-OptimizedPerformance {
    $times = @()
    $errors = 0
    
    Write-Host "`n🔍 Testing application performance..." -ForegroundColor Cyan
    
    for ($i = 1; $i -le 5; $i++) {
        $start = Get-Date
        try {
            $response = Invoke-WebRequest -Uri "https://productapp.freshnutrients.org" -TimeoutSec 30
            $time = (Get-Date) - $start
            $times += $time.TotalMilliseconds
            
            if ($time.TotalMilliseconds -lt 5000) {
                Write-Host "  ✅ Test $i: $($time.TotalMilliseconds) ms" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️ Test $i: $($time.TotalMilliseconds) ms (SLOW)" -ForegroundColor Yellow
            }
        } catch {
            $errors++
            Write-Host "  ❌ Test $i: FAILED - $($_.Exception.Message)" -ForegroundColor Red
        }
        Start-Sleep 2
    }
    
    # Calculate results
    if ($times.Count -gt 0) {
        $avgTime = ($times | Measure-Object -Average).Average
        $maxTime = ($times | Measure-Object -Maximum).Maximum
        $minTime = ($times | Measure-Object -Minimum).Minimum
        
        Write-Host "`n📊 PERFORMANCE SUMMARY:" -ForegroundColor Cyan
        Write-Host "   Average: $([math]::Round($avgTime, 2)) ms" -ForegroundColor White
        Write-Host "   Min: $([math]::Round($minTime, 2)) ms" -ForegroundColor White  
        Write-Host "   Max: $([math]::Round($maxTime, 2)) ms" -ForegroundColor White
        Write-Host "   Errors: $errors / 5" -ForegroundColor White
        
        # Performance assessment
        if ($avgTime -lt 3000 -and $errors -eq 0) {
            Write-Host "`n🎯 STATUS: EXCELLENT - Optimization successful!" -ForegroundColor Green
        } elseif ($avgTime -lt 5000 -and $errors -le 1) {
            Write-Host "`n✅ STATUS: GOOD - Performance within acceptable range" -ForegroundColor Green
        } elseif ($avgTime -lt 8000 -and $errors -le 2) {
            Write-Host "`n⚠️ STATUS: MODERATE - Monitor closely" -ForegroundColor Yellow
        } else {
            Write-Host "`n❌ STATUS: POOR - Consider rollback!" -ForegroundColor Red
        }
        
        return @{
            Average = $avgTime
            Errors = $errors
            Status = if ($avgTime -lt 5000 -and $errors -le 1) { "Good" } else { "Poor" }
        }
    } else {
        Write-Host "`n❌ All tests failed - Check app availability!" -ForegroundColor Red
        return @{ Status = "Failed" }
    }
}

# Check Azure Resources Status
function Check-OptimizedResources {
    Write-Host "`n🔍 Checking optimized Azure resources..." -ForegroundColor Cyan
    
    try {
        # Check Azure connection
        $context = Get-AzContext
        if (-not $context) {
            Write-Host "❌ Not connected to Azure. Run: Connect-AzAccount" -ForegroundColor Red
            return
        }
        
        # Check SQL Database
        $db = Get-AzSqlDatabase -ResourceGroupName "FreshNutrientsAzure" -ServerName "freshnutrients" -DatabaseName "FNProducts"
        Write-Host "📊 SQL Database: $($db.Edition) $($db.ServiceObjectiveName)" -ForegroundColor White
        
        # Check App Service Plan
        $appPlan = Get-AzAppServicePlan -ResourceGroupName "FreshNutrientsAzure"
        Write-Host "🖥️ App Service: $($appPlan.Sku.Tier) $($appPlan.Sku.Name)" -ForegroundColor White
        
        # Cost estimate
        $sqlCost = switch ($db.ServiceObjectiveName) {
            "Basic" { 5 }
            "S0" { 15 }
            "S1" { 30 }
            default { 20 }
        }
        
        $appCost = switch ($appPlan.Sku.Tier) {
            "Basic" { 15 }
            "Standard" { 75 }
            "Premium" { 150 }
            default { 50 }
        }
        
        $totalCost = $sqlCost + $appCost
        Write-Host "💰 Estimated Monthly Cost: ~$$totalCost" -ForegroundColor Green
        
    } catch {
        Write-Host "❌ Error checking resources: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Emergency Rollback Function
function Invoke-EmergencyRollback {
    Write-Host "`n🚨 EMERGENCY ROLLBACK INITIATED" -ForegroundColor Red
    Write-Host "Rolling back to higher performance tiers..." -ForegroundColor Yellow
    
    try {
        # Rollback SQL Database
        Write-Host "Rolling back SQL Database to Standard S1..." -ForegroundColor Yellow
        Set-AzSqlDatabase -ResourceGroupName "FreshNutrientsAzure" -ServerName "freshnutrients" -DatabaseName "FNProducts" -Edition "Standard" -ServiceObjectiveName "S1"
        
        # Rollback App Service Plan
        Write-Host "Rolling back App Service Plan to Standard..." -ForegroundColor Yellow
        Set-AzAppServicePlan -ResourceGroupName "FreshNutrientsAzure" -Name "ASP-FreshNutrientsAzure-876c" -Tier "Standard" -WorkerSize "Medium"
        
        Write-Host "✅ Rollback complete! Wait 5 minutes then test performance." -ForegroundColor Green
        
    } catch {
        Write-Host "❌ Rollback failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Manual intervention required!" -ForegroundColor Red
    }
}

# Main Monitoring Execution
Write-Host "Starting monitoring check..." -ForegroundColor White
$performanceResult = Test-OptimizedPerformance
Check-OptimizedResources

# Show recommendations
Write-Host "`n=== RECOMMENDATIONS ===" -ForegroundColor Green
if ($performanceResult.Status -eq "Good") {
    Write-Host "✅ Continue with current optimization" -ForegroundColor Green
    Write-Host "💡 Consider additional optimizations if needed" -ForegroundColor White
} elseif ($performanceResult.Status -eq "Poor") {
    Write-Host "⚠️ Performance issues detected!" -ForegroundColor Yellow
    Write-Host "💡 Consider running: Invoke-EmergencyRollback" -ForegroundColor White
} else {
    Write-Host "❌ Monitoring failed - check app availability" -ForegroundColor Red
}

Write-Host "`n🔄 Run this script regularly to monitor optimization success" -ForegroundColor Cyan
