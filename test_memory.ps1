#!/usr/bin/env pwsh

# Conversation Memory Test Script for FreshNutrients AI Chatbot
Write-Host "=== Conversation Memory Test ===" -ForegroundColor Green
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer your-secret-key-here"
}
# Generate unique conversation ID
$testId = [System.Guid]::NewGuid().ToString()
Write-Host "Test Conversation ID: $testId" -ForegroundColor Yellow

# Test 1: Initial message about potatoes
Write-Host "`nTest 1: Initial message about potatoes" -ForegroundColor Cyan
$test1 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Headers $headers -Method POST -ContentType "application/json" -Body "{`"message`": `"I'm growing potatoes and need help with fertilizer`", `"conversation_id`": `"$testId`"}"

Write-Host "Response: $($test1.response)" -ForegroundColor White
Write-Host "Current Message Context: $($test1.metadata.context_extracted)" -ForegroundColor Gray
Write-Host "Previous Conversation Context: $($test1.metadata.conversation_context)" -ForegroundColor DarkGray
Write-Host "Merged Context Used: $($test1.metadata.combined_context)" -ForegroundColor Yellow
Write-Host "History items: $($test1.metadata.history_count)" -ForegroundColor Yellow

# Test 2: Follow-up message - should remember potato context
Write-Host "`nTest 2: Follow-up about changing to Maize" -ForegroundColor Cyan
$test2 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Headers $headers -Method POST -ContentType "application/json" -Body "{`"message`": `"What if it was Maize instead?`", `"conversation_id`": `"$testId`"}"

Write-Host "Response: $($test2.response)" -ForegroundColor White
Write-Host "Current Message Context: $($test2.metadata.context_extracted)" -ForegroundColor Gray
Write-Host "Previous Conversation Context: $($test2.metadata.conversation_context)" -ForegroundColor DarkGray
Write-Host "Merged Context Used: $($test2.metadata.combined_context)" -ForegroundColor Yellow
Write-Host "History items: $($test2.metadata.history_count)" -ForegroundColor Yellow
Write-Host "Products found: $($test2.metadata.products_count)" -ForegroundColor White

# Test 3: Third message - should have full conversation context
Write-Host "`nTest 3: Ask about timing" -ForegroundColor Cyan
$test3 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Headers $headers -Method POST -ContentType "application/json" -Body "{`"message`": `"When should I apply it?`", `"conversation_id`": `"$testId`"}"

Write-Host "Response: $($test3.response)" -ForegroundColor White
Write-Host "Current Message Context: $($test3.metadata.context_extracted)" -ForegroundColor Gray
Write-Host "Previous Conversation Context: $($test3.metadata.conversation_context)" -ForegroundColor DarkGray  
Write-Host "Merged Context Used: $($test3.metadata.combined_context)" -ForegroundColor Yellow
Write-Host "History items: $($test3.metadata.history_count)" -ForegroundColor Yellow

# Test Session Info
Write-Host "`nSession Info:" -ForegroundColor Cyan
$sessionInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/session/$testId" -Method GET

Write-Host "Messages in session: $($sessionInfo.message_count)" -ForegroundColor White
Write-Host "First message: $($sessionInfo.first_message_time)" -ForegroundColor Gray
Write-Host "Last message: $($sessionInfo.last_message_time)" -ForegroundColor Gray

# Conversation Memory Analysis
Write-Host "`nMemory Analysis:" -ForegroundColor Green

if ($test2.metadata.history_count -gt 0) {
    Write-Host "✓ Conversation memory is working!" -ForegroundColor Green
    Write-Host "  - History preserved between messages" -ForegroundColor Green
    Write-Host "  - Context building across conversation" -ForegroundColor Green
} else {
    Write-Host "✗ Conversation memory failed!" -ForegroundColor Red
    Write-Host "  - No history found in follow-up messages" -ForegroundColor Red
    Write-Host "  - Context not being preserved" -ForegroundColor Red
}

if ($sessionInfo.message_count -ge 3) {
    Write-Host "✓ Session tracking working!" -ForegroundColor Green
    Write-Host "  - All messages logged in database" -ForegroundColor Green
} else {
    Write-Host "✗ Session tracking failed!" -ForegroundColor Red
    Write-Host "  - Expected 3+ messages, found $($sessionInfo.message_count)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
