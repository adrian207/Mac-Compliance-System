# Integration Testing Guide

**Author:** Adrian Johnson <adrian207@gmail.com>  
**Version:** 0.9.7

## Overview

Comprehensive guide for testing security tool integrations. Supports both mock APIs (for development/CI) and live API testing (with real credentials).

## Test Modes

### 1. Mock Mode (Recommended for Development)

Uses local mock servers that simulate external APIs without requiring credentials.

**Pros:**
- No credentials needed
- Fast and reliable
- Safe for CI/CD pipelines
- Predictable test data

**Cons:**
- Doesn't test actual API compatibility
- May miss real-world edge cases

### 2. Live Mode (For Production Validation)

Tests against real external APIs with actual credentials.

**Pros:**
- Tests real API behavior
- Validates actual authentication
- Catches API version mismatches

**Cons:**
- Requires valid credentials
- May incur API rate limits
- Slower than mock tests

## Quick Start

### Running Mock Tests

1. **Start mock servers:**
```bash
# Terminal 1: Start Mock Kandji API
python tests/mocks/mock_kandji.py

# Mock server runs on http://localhost:8001
```

2. **Run tests:**
```bash
# Test all integrations
python tests/integration_tests/test_integrations.py --mode mock

# Test specific integration
python tests/integration_tests/test_integrations.py --mode mock --integration kandji
```

### Running Live Tests

1. **Set up environment variables:**
```bash
# Linux/Mac
export KANDJI_ENDPOINT="https://yourtenant.api.kandji.io"
export KANDJI_API_KEY="your-api-key"
export ZSCALER_ENDPOINT="https://zsapi.zscaler.net"
export ZSCALER_API_KEY="your-api-key"
export ZSCALER_USERNAME="your-admin-user"
export ZSCALER_PASSWORD="your-admin-password"
export OKTA_DOMAIN="https://yourdomain.okta.com"
export OKTA_API_KEY="your-ssws-token"
export CROWDSTRIKE_CLIENT_ID="your-client-id"
export CROWDSTRIKE_CLIENT_SECRET="your-client-secret"

# Windows PowerShell
$env:KANDJI_ENDPOINT="https://yourtenant.api.kandji.io"
$env:KANDJI_API_KEY="your-api-key"
# ... etc
```

2. **Run tests:**
```bash
python tests/integration_tests/test_integrations.py --mode live
```

## Setting Up Test Accounts

### Kandji MDM

1. **Get API Token:**
   - Log into Kandji web console
   - Navigate to Settings → API → Tokens
   - Create new API token with read permissions
   - Copy token

2. **Configure:**
```bash
export KANDJI_ENDPOINT="https://YOUR_TENANT.api.kandji.io"
export KANDJI_API_KEY="your-api-token"
```

3. **Test:**
```bash
curl -H "Authorization: Bearer $KANDJI_API_KEY" \
     "$KANDJI_ENDPOINT/api/v1/"
```

### Zscaler ZIA/ZPA

1. **Get API Credentials:**
   - Log into Zscaler Admin Portal
   - Navigate to Administration → API Management
   - Note your API key
   - Create admin credentials for API access

2. **Configure:**
```bash
export ZSCALER_ENDPOINT="https://zsapi.zscaler.net"  # Or your cloud
export ZSCALER_API_KEY="your-api-key"
export ZSCALER_USERNAME="your-admin-username"
export ZSCALER_PASSWORD="your-admin-password"
```

3. **Note:** Zscaler authentication is complex (timestamp-based obfuscation)

### Seraphic Browser Security

1. **Get API Key:**
   - Log into Seraphic console
   - Navigate to Settings → API
   - Generate API key
   - Copy key

2. **Configure:**
```bash
export SERAPHIC_ENDPOINT="https://api.seraphicsecurity.com"
export SERAPHIC_API_KEY="your-api-key"
```

### Okta

1. **Create API Token:**
   - Log into Okta Admin Console
   - Navigate to Security → API → Tokens
   - Create new token (SSWS token)
   - Copy token immediately (shown only once)

2. **Configure:**
```bash
export OKTA_DOMAIN="https://your-domain.okta.com"
export OKTA_API_KEY="your-ssws-token"
```

3. **Test:**
```bash
curl -H "Authorization: SSWS $OKTA_API_KEY" \
     "$OKTA_DOMAIN/api/v1/org"
```

### CrowdStrike Falcon

1. **Create API Client:**
   - Log into Falcon console
   - Navigate to Support → API Clients and Keys
   - Create new API client
   - Select required scopes (Host, Device Control)
   - Copy Client ID and Secret

2. **Configure:**
```bash
export CROWDSTRIKE_ENDPOINT="https://api.crowdstrike.com"
export CROWDSTRIKE_CLIENT_ID="your-client-id"
export CROWDSTRIKE_CLIENT_SECRET="your-client-secret"
```

## Test Coverage

Each integration connector is tested for:

### 1. Connection Test
- API reachability
- Authentication validation
- Basic endpoint access

### 2. Device Sync
- Pull device inventory
- Parse device details
- Handle pagination
- Error handling

### 3. User Sync
- Pull user data
- Parse user profiles
- Handle large datasets

### 4. Policy Sync
- Pull policies/blueprints
- Parse policy configurations
- Map to platform format

### 5. Webhook Processing
- Parse webhook payloads
- Event categorization
- Signature validation (when applicable)

### 6. Push Operations (if applicable)
- Push compliance status
- Push risk scores
- Update external system state

## Expected Test Output

### Successful Mock Test

```
██████████████████████████████████████████████████████████████████
  INTEGRATION CONNECTORS TEST SUITE
  Mode: MOCK
  Started: 2025-10-29 15:30:00 UTC
██████████████████████████████████████████████████████████████████

============================================================
TESTING KANDJI MDM CONNECTOR
============================================================

[1/5] Testing connection...
  ✓ Connection: True
    API Version: v1

[2/5] Syncing devices...
  ✓ Devices synced: 2
    Sample: MacBook-Pro-123 (C02ABC123DEF)
    Compliance: compliant

[3/5] Syncing users...
  ✓ Users synced: 2
    Sample: John Doe (john.doe@example.com)

[4/5] Syncing policies...
  ✓ Policies synced: 2
    Sample: Corporate MacBook Policy

[5/5] Testing webhook processing...
  ✓ Webhook processed: device_enrolled

============================================================
KANDJI TEST RESULT: ✓ PASSED
============================================================

██████████████████████████████████████████████████████████████████
  TEST SUMMARY
██████████████████████████████████████████████████████████████████

Total Integrations Tested: 1
  ✓ Passed: 1
  ✗ Failed: 0

KANDJI: ✓ PASSED

██████████████████████████████████████████████████████████████████
  Completed: 2025-10-29 15:30:15 UTC
██████████████████████████████████████████████████████████████████
```

### Failed Test Example

```
[2/5] Syncing devices...
  ✗ Sync failed: HTTP 401: Unauthorized

KANDJI TEST RESULT: ✗ FAILED

Total Integrations Tested: 1
  ✓ Passed: 0
  ✗ Failed: 1

KANDJI: ✗ FAILED
  Error: Authentication failed
```

## Troubleshooting

### Mock Server Not Starting

**Problem:** `Address already in use`

**Solution:**
```bash
# Find process using port
lsof -i :8001  # Mac/Linux
netstat -ano | findstr :8001  # Windows

# Kill the process
kill -9 <PID>  # Mac/Linux
taskkill /F /PID <PID>  # Windows
```

### Authentication Failures (Live Mode)

**Problem:** `401 Unauthorized`

**Check:**
- API key is correct and not expired
- Endpoint URL is correct
- API key has required permissions
- No extra whitespace in environment variables

**Debug:**
```bash
# Print environment variables
echo $KANDJI_API_KEY  # Should show your key

# Test manually with curl
curl -v -H "Authorization: Bearer $KANDJI_API_KEY" \
     "$KANDJI_ENDPOINT/api/v1/"
```

### Rate Limiting

**Problem:** `429 Too Many Requests`

**Solution:**
- Increase delays between tests
- Use mock mode for development
- Request higher rate limits from vendor
- Run tests during off-peak hours

### SSL/TLS Errors

**Problem:** `SSL certificate verification failed`

**Solution (TEMPORARY - FOR TESTING ONLY):**
```python
# In connector, set verify=False
# DO NOT use in production!
self.client = httpx.AsyncClient(verify=False)
```

**Proper Solution:**
- Install/update root certificates
- Check corporate proxy/firewall
- Verify endpoint URL is correct

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Start mock servers
        run: |
          python tests/mocks/mock_kandji.py &
          sleep 5  # Wait for server to start
      
      - name: Run integration tests
        run: |
          python tests/integration_tests/test_integrations.py --mode mock
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Start Mocks') {
            steps {
                sh 'python tests/mocks/mock_kandji.py &'
                sh 'sleep 5'
            }
        }
        
        stage('Test') {
            steps {
                sh 'python tests/integration_tests/test_integrations.py --mode mock'
            }
        }
    }
    
    post {
        always {
            junit 'test-results/*.xml'
        }
    }
}
```

## Manual API Testing

### Test Kandji Connection

```bash
# Set variables
KANDJI_TOKEN="your-token"
KANDJI_ENDPOINT="https://yourtenant.api.kandji.io"

# Test API root
curl -H "Authorization: Bearer $KANDJI_TOKEN" \
     "$KANDJI_ENDPOINT/api/v1/"

# Get devices
curl -H "Authorization: Bearer $KANDJI_TOKEN" \
     "$KANDJI_ENDPOINT/api/v1/devices?per_page=10"

# Get device details
curl -H "Authorization: Bearer $KANDJI_TOKEN" \
     "$KANDJI_ENDPOINT/api/v1/devices/DEVICE_ID"
```

### Test Okta Connection

```bash
# Set variables
OKTA_TOKEN="your-ssws-token"
OKTA_DOMAIN="https://yourdomain.okta.com"

# Test org endpoint
curl -H "Authorization: SSWS $OKTA_TOKEN" \
     "$OKTA_DOMAIN/api/v1/org"

# Get users
curl -H "Authorization: SSWS $OKTA_TOKEN" \
     "$OKTA_DOMAIN/api/v1/users?limit=10"
```

### Test CrowdStrike Connection

```bash
# Get OAuth2 token first
CROWDSTRIKE_CLIENT_ID="your-client-id"
CROWDSTRIKE_CLIENT_SECRET="your-client-secret"

TOKEN=$(curl -X POST https://api.crowdstrike.com/oauth2/token \
  -u "$CROWDSTRIKE_CLIENT_ID:$CROWDSTRIKE_CLIENT_SECRET" \
  -d "grant_type=client_credentials" | jq -r '.access_token')

# Query devices
curl -H "Authorization: Bearer $TOKEN" \
     "https://api.crowdstrike.com/devices/queries/devices/v1?limit=10"
```

## Best Practices

1. **Start with Mock Tests**
   - Develop and debug with mock APIs
   - Switch to live tests for final validation

2. **Rotate API Keys**
   - Use separate keys for testing
   - Rotate regularly
   - Never commit keys to git

3. **Use Read-Only Permissions**
   - Test accounts should have minimal permissions
   - Read-only access is sufficient for sync tests

4. **Monitor Rate Limits**
   - Track API usage during tests
   - Implement exponential backoff
   - Use batch operations where available

5. **Test Error Scenarios**
   - Invalid credentials
   - Network timeouts
   - Malformed responses
   - Rate limiting

## Support

**Issues:** https://github.com/adrian207/Mac-Compliance-System/issues  
**Email:** adrian207@gmail.com  
**Documentation:** `/docs` directory

## License

See LICENSE file in project root.

