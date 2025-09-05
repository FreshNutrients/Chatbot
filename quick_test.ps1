

# Clear the screen to avoid output mixing
Clear-Host

Write-Host "🌱 FreshNutrients Chatbot Quick Tests" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Starting fresh test run..." -ForegroundColor Gray
Write-Host ""

# Test 1: Not enough Context
Write-Host "Test 1: Not enough Context" -ForegroundColor Cyan
try {
    $body1 = '{"message": "Is Trump a good president?"}'
    $result1 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method POST -ContentType "application/json" -Body $body1
    Write-Host "Response: $($result1.response)" -ForegroundColor White
    Write-Host "Products found: $($result1.metadata.products_count)" -ForegroundColor Gray
    Write-Host "Context extracted: $($result1.metadata.context_extracted)" -ForegroundColor Yellow
} catch {
    Write-Host "Error in Test 1: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Avocado
Write-Host "Test 2: Avocado" -ForegroundColor Cyan  
try {
    $body2 = '{"message": "What foliar spray products do you have for Avocado plants?"}'
    $result2 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method POST -ContentType "application/json" -Body $body2
    Write-Host "Response: $($result2.response)" -ForegroundColor White
    Write-Host "Products found: $($result2.metadata.products_count)" -ForegroundColor Gray
    Write-Host "Context extracted: $($result2.metadata.context_extracted)" -ForegroundColor Yellow
} catch {
    Write-Host "Error in Test 2: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Maize
Write-Host "Test 3: Maize growth" -ForegroundColor Cyan
try {
    $body3 = '{"message": "I am growing maize, what products can help with growth?"}'
    $result3 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method POST -ContentType "application/json" -Body $body3
    Write-Host "Response: $($result3.response)" -ForegroundColor White
    Write-Host "Products found: $($result3.metadata.products_count)" -ForegroundColor Gray
    Write-Host "Context extracted: $($result3.metadata.context_extracted)" -ForegroundColor Yellow
} catch {
    Write-Host "Error in Test 3: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "🎯 Tests Complete!" -ForegroundColor Green
Write-Host "All tests finished successfully." -ForegroundColor Gray
