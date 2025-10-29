# Integration Testing Setup

Quick reference for running integration tests.

## Quick Start

### Windows (PowerShell)

```powershell
# Start mock servers and run tests automatically
.\scripts\run_integration_tests.ps1 -Mode mock -StartMockServers

# Or manually:
# Terminal 1: Start mock server
python tests\mocks\mock_kandji.py

# Terminal 2: Run tests
python tests\integration_tests\test_integrations.py --mode mock
```

### Linux/Mac (Bash)

```bash
# Make script executable
chmod +x scripts/run_integration_tests.sh

# Start mock servers and run tests automatically
./scripts/run_integration_tests.sh --mode mock --start-mocks

# Or manually:
# Terminal 1: Start mock server
python tests/mocks/mock_kandji.py

# Terminal 2: Run tests
python tests/integration_tests/test_integrations.py --mode mock
```

## Test Modes

### Mock Mode (Default)
Tests against local mock servers. No credentials needed.

```bash
python tests/integration_tests/test_integrations.py --mode mock
```

### Live Mode
Tests against real APIs. Requires environment variables.

```bash
# Set credentials
export KANDJI_ENDPOINT="https://yourtenant.api.kandji.io"
export KANDJI_API_KEY="your-api-key"

# Run tests
python tests/integration_tests/test_integrations.py --mode live
```

## Test Specific Integration

```bash
# Test only Kandji
python tests/integration_tests/test_integrations.py --mode mock --integration kandji

# Test only Zscaler (when implemented)
python tests/integration_tests/test_integrations.py --mode mock --integration zscaler
```

## Available Mock Servers

- **Kandji:** `tests/mocks/mock_kandji.py` (port 8001)
- **Zscaler:** Coming soon
- **Seraphic:** Coming soon
- **Okta:** Coming soon
- **CrowdStrike:** Coming soon

## Documentation

See `docs/INTEGRATION_TESTING.md` for comprehensive testing guide.

## CI/CD

Tests run automatically in CI/CD pipelines using mock mode.

## Troubleshooting

**Port already in use:**
```bash
# Kill process on port 8001
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8001  # Windows (find PID, then: taskkill /F /PID <PID>)
```

**Import errors:**
```bash
# Make sure you're in project root
cd /path/to/Mac-Hardening

# Install dependencies
pip install -r requirements.txt
```

## Support

adrian207@gmail.com

