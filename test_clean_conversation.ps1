#!/usr/bin/env pwsh

Write-Host "Clean Conversation Test" -ForegroundColor Yellow
Write-Host "=======================" -ForegroundColor Yellow

$baseUrl = "http://localhost:8000"
$cleanConversationId = "clean-test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host "Using fresh conversation ID: $cleanConversationId" -ForegroundColor Cyan

$testMessage = "I'm growing maize and need help with plant nutrition"

try {
    $body = @{
        message = $testMessage
        conversation_id = $cleanConversationId
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/chat" -Method Post -Body $body -ContentType "application/json"
    
    $timingDetected = $response.metadata.combined_context.timing_question -eq $true
    
    Write-Host "`nMessage: '$testMessage'" -ForegroundColor Gray
    Write-Host "Timing detected: $timingDetected" -ForegroundColor $(if ($timingDetected) { "Red" } else { "Green" })
    Write-Host "Current context: $($response.metadata.context_extracted | ConvertTo-Json -Compress)" -ForegroundColor Cyan
    Write-Host "Conversation context: $($response.metadata.conversation_context | ConvertTo-Json -Compress)" -ForegroundColor Cyan
    Write-Host "Combined context: $($response.metadata.combined_context | ConvertTo-Json -Compress)" -ForegroundColor Yellow
    
    if ($timingDetected) {
        Write-Host "`n❌ ERROR: This should NOT be detected as a timing question!" -ForegroundColor Red
    } else {
        Write-Host "`n✅ SUCCESS: Correctly identified as non-timing question!" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
