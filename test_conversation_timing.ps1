#!/usr/bin/env pwsh

Write-Host "Conversation Memory + Timing Test" -ForegroundColor Yellow
Write-Host "==================================" -ForegroundColor Yellow

$baseUrl = "http://localhost:8000"
$conversationId = "memory-timing-test"

# Test conversation flow
$messages = @(
    @{
        text = "I'm growing maize and need help with plant nutrition"
        description = "Initial message - establish crop context"
    },
    @{
        text = "What about timing?"
        description = "Follow-up timing question - should use previous context"
    },
    @{
        text = "How often should I apply it?"
        description = "Another timing question - should maintain context"
    }
)

for ($i = 0; $i -lt $messages.Count; $i++) {
    $msg = $messages[$i]
    
    Write-Host "`n--- Message $($i + 1): $($msg.description) ---" -ForegroundColor Cyan
    Write-Host "Sending: '$($msg.text)'" -ForegroundColor Gray
    
    try {
        $body = @{
            message = $msg.text
            conversation_id = $conversationId
        } | ConvertTo-Json -Depth 5
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/chat" -Method Post -Body $body -ContentType "application/json"
        
        $timingDetected = $response.metadata.combined_context.timing_question -eq $true
        
        Write-Host "✅ Response received" -ForegroundColor Green
        Write-Host "Products found: $($response.metadata.products_count)" -ForegroundColor Yellow
        Write-Host "Timing detected: $timingDetected" -ForegroundColor $(if ($timingDetected) { "Green" } else { "Gray" })
        Write-Host "Combined context: $($response.metadata.combined_context | ConvertTo-Json -Compress)" -ForegroundColor Cyan
        
        # Show response preview
        $preview = if ($response.response.Length -gt 300) { 
            $response.response.Substring(0, 300) + "..." 
        } else { 
            $response.response 
        }
        Write-Host "`nResponse preview:" -ForegroundColor Yellow
        Write-Host $preview -ForegroundColor White
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1
}

Write-Host "`n==================================" -ForegroundColor Yellow
Write-Host "Conversation + Timing Test Complete" -ForegroundColor Yellow
