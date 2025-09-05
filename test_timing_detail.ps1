#!/usr/bin/env pwsh

Write-Host "Detailed Timing Response Analysis" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow

$baseUrl = "http://localhost:8000"

$testMessage = "What about timing for application?"
$conversationId = "timing-detail-test"

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
    
    Write-Host "`n--- FULL RESPONSE ---" -ForegroundColor Yellow
    Write-Host $response.response -ForegroundColor White
    
    Write-Host "`n--- CONTEXT USED ---" -ForegroundColor Yellow
    Write-Host ($response.context_used | ConvertTo-Json -Depth 2) -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
