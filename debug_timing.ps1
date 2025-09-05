#!/usr/bin/env pwsh

Write-Host "Debug Timing Keyword Matching" -ForegroundColor Yellow
Write-Host "==============================" -ForegroundColor Yellow

$testMessage = "I'm growing maize and need help with plant nutrition"
$timingKeywords = @(
    "timing", "when should", "what time", "schedule", "frequency", "interval", "how often",
    "application timing", "spray timing", "fertilizer timing", "season", "seasonal",
    "before planting", "after planting", "during growing", "monthly", "weekly", "daily", 
    "days apart", "weeks apart", "months apart", "how many times"
)

Write-Host "Test message: '$testMessage'" -ForegroundColor Cyan
Write-Host "Checking each timing keyword:" -ForegroundColor Gray

$messageLower = $testMessage.ToLower()
$matches = @()

foreach ($keyword in $timingKeywords) {
    if ($messageLower.Contains($keyword.ToLower())) {
        $matches += $keyword
        Write-Host "  ✅ MATCH: '$keyword'" -ForegroundColor Red
    } else {
        Write-Host "  ❌ No match: '$keyword'" -ForegroundColor Gray
    }
}

Write-Host "`nMatches found: $($matches.Count)" -ForegroundColor Yellow
if ($matches.Count -gt 0) {
    Write-Host "Matching keywords: $($matches -join ', ')" -ForegroundColor Red
} else {
    Write-Host "No timing keywords found - this is correct!" -ForegroundColor Green
}
