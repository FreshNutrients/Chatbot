#!/usr/bin/env pwsh

Write-Host "Testing Refined Timing Detection" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow

$baseUrl = "http://localhost:8000"

# Test messages - some should detect timing, others shouldn't
$testMessages = @(
    @{
        message = "I'm growing maize and need help with plant nutrition"
        expectedTiming = $false
        description = "Should NOT detect timing - just nutrition question"
    },
    @{
        message = "What about timing for application?"
        expectedTiming = $true
        description = "Should detect timing - direct timing question"
    },
    @{
        message = "When should I apply fertilizer to potatoes?"
        expectedTiming = $true
        description = "Should detect timing - when question"
    },
    @{
        message = "How often should I spray my tomatoes?"
        expectedTiming = $true
        description = "Should detect timing - frequency question"
    },
    @{
        message = "I need fertilizer for my wheat crop"
        expectedTiming = $false
        description = "Should NOT detect timing - general fertilizer question"
    }
)

for ($i = 0; $i -lt $testMessages.Count; $i++) {
    $test = $testMessages[$i]
    
    Write-Host "`n--- Test $($i + 1): $($test.description) ---" -ForegroundColor Cyan
    Write-Host "Message: '$($test.message)'" -ForegroundColor Gray
    Write-Host "Expected timing: $($test.expectedTiming)" -ForegroundColor Gray
    
    try {
        $body = @{
            message = $test.message
            conversation_id = "timing-detection-test-$i"
        } | ConvertTo-Json -Depth 5
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/chat" -Method Post -Body $body -ContentType "application/json"
        
        $actualTiming = $response.metadata.combined_context.timing_question -eq $true
        $correct = $actualTiming -eq $test.expectedTiming
        
        Write-Host "Actual timing: $actualTiming" -ForegroundColor $(if ($correct) { "Green" } else { "Red" })
        Write-Host "Detection: $(if ($correct) { "✅ CORRECT" } else { "❌ INCORRECT" })" -ForegroundColor $(if ($correct) { "Green" } else { "Red" })
        
        # Show response start for timing questions
        if ($actualTiming) {
            $responseStart = if ($response.response.Length -gt 100) { 
                $response.response.Substring(0, 100) + "..." 
            } else { 
                $response.response 
            }
            Write-Host "Response starts with: $responseStart" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1
}

Write-Host "`n=================================" -ForegroundColor Yellow
Write-Host "Timing Detection Test Complete" -ForegroundColor Yellow
