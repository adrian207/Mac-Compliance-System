# Integration Test Runner Script for Windows
# Author: Adrian Johnson <adrian207@gmail.com>

param(
    [ValidateSet('mock', 'live')]
    [string]$Mode = 'mock',
    
    [ValidateSet('all', 'kandji', 'zscaler', 'seraphic', 'okta', 'crowdstrike')]
    [string]$Integration = 'all',
    
    [switch]$StartMockServers
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Integration Test Runner" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running in mock mode
if ($Mode -eq 'mock') {
    Write-Host "Mode: MOCK (using local mock servers)" -ForegroundColor Yellow
    
    if ($StartMockServers) {
        Write-Host "`nStarting mock servers..." -ForegroundColor Green
        
        # Start Kandji mock server in background
        Write-Host "  Starting Mock Kandji API on port 8001..."
        Start-Process python -ArgumentList "tests\mocks\mock_kandji.py" -WindowStyle Minimized
        
        # Wait for servers to start
        Write-Host "  Waiting for servers to initialize..."
        Start-Sleep -Seconds 3
        
        # Test if server is up
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001/docs" -UseBasicParsing -TimeoutSec 2
            Write-Host "  ✓ Mock Kandji API is running" -ForegroundColor Green
        }
        catch {
            Write-Host "  ✗ Failed to start Mock Kandji API" -ForegroundColor Red
            Write-Host "    Try running manually: python tests\mocks\mock_kandji.py"
            exit 1
        }
    }
    else {
        Write-Host "`n⚠️  Make sure mock servers are running:" -ForegroundColor Yellow
        Write-Host "   python tests\mocks\mock_kandji.py" -ForegroundColor Gray
        Write-Host "`n   Or run with -StartMockServers flag`n" -ForegroundColor Gray
    }
}
else {
    Write-Host "Mode: LIVE (using real API credentials)" -ForegroundColor Yellow
    Write-Host "`n⚠️  Make sure environment variables are set:" -ForegroundColor Yellow
    Write-Host "   KANDJI_ENDPOINT, KANDJI_API_KEY, etc.`n" -ForegroundColor Gray
}

# Run tests
Write-Host "`nRunning integration tests..." -ForegroundColor Green
Write-Host "Integration: $Integration" -ForegroundColor Cyan
Write-Host ""

$testArgs = "--mode", $Mode, "--integration", $Integration
python tests\integration_tests\test_integrations.py $testArgs

$exitCode = $LASTEXITCODE

# Cleanup message
if ($Mode -eq 'mock' -and $StartMockServers) {
    Write-Host "`n⚠️  Mock servers are still running in background" -ForegroundColor Yellow
    Write-Host "   Kill them manually if needed: Get-Process python | Stop-Process" -ForegroundColor Gray
}

exit $exitCode

