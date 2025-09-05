# Test 2: Single Context - Crop Mentioned
Write-Host "=== TEST 2: SINGLE CONTEXT (CROP) ===" -ForegroundColor Green
Write-Host "Testing chat request with crop context in message" -ForegroundColor Yellow

$uri = "http://localhost:8000/api/v1/chat"
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer your-secret-key-here"
}

$body = @{
    message = "What fertilizer do you recommend for tomatoes?"
} | ConvertTo-Json

Write-Host "`nSending request..." -ForegroundColor Cyan
Write-Host "URL: $uri" -ForegroundColor White
Write-Host "Body: $body" -ForegroundColor White

try {
    $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body
    
    # Display readable response
    Write-Host "`n=== 🤖 AI RESPONSE ===" -ForegroundColor Green
    # Convert \n to actual line breaks and clean up formatting
    $cleanResponse = $response.response -replace '\\n', "`n" -replace '\\t', "`t"
    Write-Host $cleanResponse -ForegroundColor White
    
    Write-Host "`n=== 📊 CONTEXT EXTRACTED ===" -ForegroundColor Cyan
    $contextExtracted = $response.metadata.context_extracted
    if ($contextExtracted -and ($contextExtracted.PSObject.Properties | Measure-Object).Count -gt 0) {
        $contextExtracted.PSObject.Properties | ForEach-Object {
            Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor White
        }
    } else {
        Write-Host "No context detected" -ForegroundColor Yellow
    }
    
    Write-Host "`n=== 🎯 PRODUCTS FOUND ===" -ForegroundColor Magenta
    $productsCount = $response.metadata.products_count
    if ($productsCount -gt 0 -and $response.context_used) {
        Write-Host "Count: $productsCount" -ForegroundColor White
        foreach ($product in $response.context_used) {
            Write-Host "  • $($product.product_name)" -ForegroundColor White
        }
    } else {
        Write-Host "No products found" -ForegroundColor Yellow
    }
    
    Write-Host "`n=== ⚡ METADATA ===" -ForegroundColor Blue
    Write-Host "Response Time: $($response.metadata.response_time) ms" -ForegroundColor White
    Write-Host "Conversation ID: $($response.conversation_id)" -ForegroundColor White
    
    Write-Host "`n=== 📋 FULL JSON (for debugging) ===" -ForegroundColor DarkGray
    $response | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "`n❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}
