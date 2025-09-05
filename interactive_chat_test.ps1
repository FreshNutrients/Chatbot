# Interactive Chat Test Script for FreshNutrients AI
Write-Host "🌱 FreshNutrients AI Chat - Interactive Test" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer your-secret-key-here"
}

# Generate session ID
$sessionId = "interactive-test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "Session ID: $sessionId" -ForegroundColor Yellow
Write-Host "Type 'quit' to exit, 'new' for new session, 'history' to see conversation" -ForegroundColor Cyan
Write-Host ""

$messageCount = 0

while ($true) {
    # Get user input
    $userMessage = Read-Host "You"
    
    if ($userMessage -eq "quit" -or $userMessage -eq "exit") {
        Write-Host "Goodbye! 👋" -ForegroundColor Green
        break
    }
    
    if ($userMessage -eq "new") {
        $sessionId = "interactive-test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Write-Host "Started new session: $sessionId" -ForegroundColor Yellow
        $messageCount = 0
        continue
    }
    
    if ($userMessage -eq "history") {
        try {
            $sessionInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/session/$sessionId" -Method GET
            Write-Host "Session Info:" -ForegroundColor Cyan
            Write-Host "  Messages: $($sessionInfo.message_count)" -ForegroundColor White
            Write-Host "  Active: $($sessionInfo.session_active)" -ForegroundColor White
        } catch {
            Write-Host "Could not retrieve session info: $($_.Exception.Message)" -ForegroundColor Red
        }
        continue
    }
    
    if ([string]::IsNullOrWhiteSpace($userMessage)) {
        continue
    }
    
    try {
        Write-Host "🤔 Thinking..." -ForegroundColor Yellow
        
        $body = @{
            message = $userMessage
            conversation_id = $sessionId
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Headers $headers -Method POST -Body $body
        
        # Display bot response
        Write-Host ""
        Write-Host "Bot: " -ForegroundColor Green -NoNewline
        
        # Clean up response formatting
        $cleanResponse = $response.response -replace '\\n', "`n"
        Write-Host $cleanResponse -ForegroundColor White
        
        # Show metadata
        Write-Host ""
        Write-Host "📊 " -ForegroundColor Cyan -NoNewline
        Write-Host "Response: $($response.metadata.response_time)ms | Products: $($response.metadata.products_count) | History: $($response.metadata.history_count)" -ForegroundColor DarkGray
        
        # Show context if available
        if ($response.metadata.context_extracted -and ($response.metadata.context_extracted | Get-Member -MemberType Properties).Count -gt 0) {
            Write-Host "🎯 Context: " -ForegroundColor Cyan -NoNewline
            $contextItems = @()
            $response.metadata.context_extracted.PSObject.Properties | ForEach-Object {
                $contextItems += "$($_.Name): $($_.Value)"
            }
            Write-Host ($contextItems -join ", ") -ForegroundColor DarkGray
        }
        
        $messageCount += 2
        Write-Host ""
        
    } catch {
        Write-Host ""
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}
