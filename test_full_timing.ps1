#!/usr/bin/env pwsh

Write-Host "Full Context Timing Test" -ForegroundColor Yellow
Write-Host "========================" -ForegroundColor Yellow

$baseUrl = "http://localhost:8000"

$testMessage = "I'm growing maize. What about timing for fertilizer application?"
$conversationId = "full-timing-test"

try {
    $body = @{
        message = $testMessage
        conversation_id = $conversationId
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/chat" -Method Post -Body $body -ContentType "application/json"
    
    Write-Host "Message: '$testMessage'" -ForegroundColor Gray
    Write-Host "Timing detected: $($response.metadata.combined_context.timing_question)" -ForegroundColor Green
    Write-Host "Question type: $($response.metadata.combined_context.question_type)" -ForegroundColor Green
    Write-Host "Products found: $($response.metadata.products_count)" -ForegroundColor Green
    Write-Host "Combined context: $($response.metadata.combined_context | ConvertTo-Json -Compress)" -ForegroundColor Cyan
    
    Write-Host "`n--- FULL RESPONSE ---" -ForegroundColor Yellow
    Write-Host $response.response -ForegroundColor White
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
