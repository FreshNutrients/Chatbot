#!/usr/bin/env pwsh

Write-Host "Testing Timing Question Enhancement" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow

# Test URL
$baseUrl = "http://localhost:8000"

# Test messages with timing questions
$timingTests = @(
    @{
        message = "I'm growing maize and need fertilizer. What about timing for application?"
        description = "Basic timing question with crop context"
    },
    @{
        message = "When should I apply fertilizer to my potatoes?"
        description = "Direct timing question"
    },
    @{
        message = "What's the best schedule for spraying tomatoes?"
        description = "Schedule/timing question"
    },
    @{
        message = "How often should I fertilize my wheat crop?"
        description = "Frequency timing question"
    }
)

# Test each timing scenario
for ($i = 0; $i -lt $timingTests.Count; $i++) {
    $test = $timingTests[$i]
    
    Write-Host "`n--- Test $($i + 1): $($test.description) ---" -ForegroundColor Cyan
    Write-Host "Message: '$($test.message)'" -ForegroundColor Gray
    
    try {
        $body = @{
            message = $test.message
            conversation_id = "timing-test-$i"
        } | ConvertTo-Json -Depth 5
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/chat" -Method Post -Body $body -ContentType "application/json"
        
        # Check if timing was detected
        $timingDetected = $response.metadata.combined_context.timing_question -eq $true
        $questionType = $response.metadata.combined_context.question_type
        
        Write-Host "`n✅ Response received" -ForegroundColor Green
        Write-Host "Timing detected: $timingDetected" -ForegroundColor $(if ($timingDetected) { "Green" } else { "Red" })
        Write-Host "Question type: $questionType" -ForegroundColor Gray
        Write-Host "Products found: $($response.metadata.products_count)" -ForegroundColor Gray
        Write-Host "Context extracted: $($response.metadata.context_extracted | ConvertTo-Json -Compress)" -ForegroundColor Gray
        
        # Show first 200 characters of response to see if timing guidance is working
        $shortResponse = if ($response.response.Length -gt 200) { 
            $response.response.Substring(0, 200) + "..." 
        } else { 
            $response.response 
        }
        Write-Host "`nResponse preview:" -ForegroundColor Yellow
        Write-Host $shortResponse -ForegroundColor White
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1
}

Write-Host "`n=====================================" -ForegroundColor Yellow
Write-Host "Timing Enhancement Test Complete" -ForegroundColor Yellow
