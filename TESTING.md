# Testing Guide

**Author:** Adrian Johnson <adrian207@gmail.com>

## Testing the Platform

This guide covers testing the Mac OS Zero Trust Platform.

---

## Quick Test (1 Minute)

Run quick validation to ensure everything is set up correctly:

```bash
python test_runner.py --quick
```

This checks:
- ✓ Python version (3.10+)
- ✓ Dependencies installed
- ✓ Configuration files present
- ✓ All modules importable

---

## Full Test Suite (5 Minutes)

Run the complete test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run all tests
python test_runner.py
```

### What Gets Tested

**Configuration Tests** (`tests/test_config.py`)
- Configuration loading
- Required sections present
- Risk weights sum to 100
- Thresholds properly ordered

**Risk Engine Tests** (`tests/test_risk_engine.py`)
- Risk assessor initialization
- Secure devices get low risk scores
- Insecure devices get high risk scores
- All component scores calculated
- Risk factors identified
- Recommendations generated

**Compliance Tests** (`tests/test_compliance.py`)
- Compliance checker initialization
- Compliant devices pass
- Non-compliant devices fail
- Violation detection
- Remediation actions generated

**API Tests** (`tests/test_api.py`)
- All endpoints accessible
- Health check works
- Metrics exposed
- Risk assessment endpoint
- Compliance check endpoint

**Integration Tests** (`tests/test_integration.py`)
- Base integration functionality
- HTTP request methods
- Retry logic
- Error handling

---

## Manual Testing

### Test 1: Configuration Loading

```bash
python -c "from core.config import get_config; c = get_config(); print(f'✓ Config loaded: {c.platform_name}')"
```

Expected output:
```
✓ Config loaded: Mac OS Zero Trust Security Platform
```

### Test 2: Risk Assessment

```bash
python -c "
from risk_engine.assessor import assess_device_risk

telemetry = {
    'system_info': {'os_version': '14.0', 'uuid': 'test-123'},
    'security_status': {
        'filevault_enabled': True,
        'firewall_enabled': True,
        'gatekeeper_enabled': True,
        'sip_enabled': True
    },
    'authentication': {
        'password_required': True,
        'screen_lock_enabled': True
    },
    'network_info': {},
    'processes': [],
    'network_connections': []
}

result = assess_device_risk(telemetry)
print(f'✓ Risk Score: {result[\"total_risk_score\"]}')
print(f'✓ Risk Level: {result[\"risk_level\"]}')
"
```

### Test 3: Compliance Check

```bash
python -c "
from hardening.compliance_checker import check_device_compliance

telemetry = {
    'system_info': {'os_version': '14.0'},
    'security_status': {
        'filevault_enabled': True,
        'firewall_enabled': True,
        'gatekeeper_enabled': True,
        'sip_enabled': True
    },
    'authentication': {
        'password_required': True,
        'screen_lock_enabled': True
    }
}

result = check_device_compliance(telemetry)
print(f'✓ Compliant: {result[\"is_compliant\"]}')
print(f'✓ Score: {result[\"compliance_score\"]}')
print(f'✓ Violations: {len(result[\"violations\"])}')
"
```

### Test 4: API Server

```bash
# Terminal 1: Start API server
python api_server.py

# Terminal 2: Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/metrics | head -20
```

### Test 5: Database Connection

```bash
python -c "
from core.database import get_db_manager

db = get_db_manager()
print('✓ Database connection established')

with db.get_session() as session:
    print('✓ Database session created')
print('✓ Database test passed')
"
```

---

## Integration Testing (Requires API Credentials)

### Test Kandji Integration

```bash
python -c "
from integrations.kandji import get_kandji_client

try:
    with get_kandji_client() as kandji:
        if kandji.test_connection():
            print('✓ Kandji connection successful')
            devices = kandji.get_devices(limit=5)
            print(f'✓ Retrieved {len(devices)} devices')
        else:
            print('✗ Kandji connection failed')
except Exception as e:
    print(f'✗ Kandji error: {e}')
"
```

### Test Zscaler Integration

```bash
python -c "
from integrations.zscaler import get_zscaler_client

try:
    with get_zscaler_client() as zscaler:
        if zscaler.test_connection():
            print('✓ Zscaler connection successful')
        else:
            print('✗ Zscaler connection failed')
except Exception as e:
    print(f'✗ Zscaler error: {e}')
"
```

### Test Seraphic Integration

```bash
python -c "
from integrations.seraphic import get_seraphic_client

try:
    with get_seraphic_client() as seraphic:
        if seraphic.test_connection():
            print('✓ Seraphic connection successful')
        else:
            print('✗ Seraphic connection failed')
except Exception as e:
    print(f'✗ Seraphic error: {e}')
"
```

---

## API Endpoint Testing

### Test with cURL

```bash
# Health check
curl http://localhost:8000/health

# Risk assessment
curl -X POST http://localhost:8000/api/v1/devices/risk-assessment \
  -H "Content-Type: application/json" \
  -d '{
    "telemetry": {
      "system_info": {"os_version": "14.0", "uuid": "test-123"},
      "security_status": {
        "filevault_enabled": true,
        "firewall_enabled": true,
        "gatekeeper_enabled": true,
        "sip_enabled": true
      },
      "authentication": {
        "password_required": true,
        "screen_lock_enabled": true
      },
      "network_info": {},
      "processes": [],
      "network_connections": []
    }
  }'

# Compliance check
curl -X POST http://localhost:8000/api/v1/devices/compliance-check \
  -H "Content-Type: application/json" \
  -d '{
    "telemetry": {
      "system_info": {"os_version": "14.0"},
      "security_status": {
        "filevault_enabled": true,
        "firewall_enabled": true,
        "gatekeeper_enabled": true,
        "sip_enabled": true
      },
      "authentication": {
        "password_required": true,
        "screen_lock_enabled": true
      }
    }
  }'
```

### Test with Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(f"Health: {response.json()}")

# Risk assessment
telemetry = {
    "system_info": {"os_version": "14.0", "uuid": "test-123"},
    "security_status": {
        "filevault_enabled": True,
        "firewall_enabled": True,
        "gatekeeper_enabled": True,
        "sip_enabled": True
    },
    "authentication": {
        "password_required": True,
        "screen_lock_enabled": True
    },
    "network_info": {},
    "processes": [],
    "network_connections": []
}

response = requests.post(
    "http://localhost:8000/api/v1/devices/risk-assessment",
    json={"telemetry": telemetry}
)
print(f"Risk Assessment: {response.json()}")
```

---

## Performance Testing

### Test Risk Assessment Performance

```bash
python -c "
import time
from risk_engine.assessor import assess_device_risk

telemetry = {
    'system_info': {'os_version': '14.0', 'uuid': 'test-123'},
    'security_status': {
        'filevault_enabled': True,
        'firewall_enabled': True,
        'gatekeeper_enabled': True,
        'sip_enabled': True
    },
    'authentication': {
        'password_required': True,
        'screen_lock_enabled': True
    },
    'network_info': {},
    'processes': [],
    'network_connections': []
}

# Run 100 assessments
start = time.time()
for i in range(100):
    assess_device_risk(telemetry)
duration = time.time() - start

print(f'✓ 100 assessments in {duration:.2f}s')
print(f'✓ Average: {duration/100*1000:.2f}ms per assessment')
"
```

---

## Load Testing

Use `locust` or `apache bench` to test API under load:

```bash
# Install locust
pip install locust

# Create locustfile.py with test scenarios
# Run load test
locust -f locustfile.py --host http://localhost:8000
```

---

## Docker Testing

### Test Docker Build

```bash
# Build image
docker build -t zerotrust-test .

# Run container
docker run --rm zerotrust-test python test_runner.py --quick
```

### Test Docker Compose

```bash
# Start services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Test health
curl http://localhost:8000/health

# Check logs
docker-compose logs platform

# Stop services
docker-compose down
```

---

## Test Results Interpretation

### Expected Results

**Quick Validation:**
- All checks should pass (100%)
- No import errors
- Configuration loads successfully

**Full Test Suite:**
- All tests pass (100%)
- No failures or errors
- Test coverage > 70%

**Risk Assessment:**
- Secure device: Risk score < 30, Level = "low"
- Insecure device: Risk score > 70, Level = "high" or "critical"

**Compliance:**
- Compliant device: Score > 80, is_compliant = True
- Non-compliant: Violations identified with severity

**API:**
- All endpoints return 200 OK
- Responses include expected fields
- Error handling works correctly

---

## Troubleshooting Test Failures

### Import Errors

```bash
# Ensure dependencies installed
pip install -r requirements.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Configuration Errors

```bash
# Verify config file exists
ls -la config/config.example.yaml

# Test config loading
python -c "from core.config import load_config; load_config('config/config.example.yaml')"
```

### Database Errors

```bash
# Check database configuration
# Edit config/config.yaml

# Initialize database
python scripts/init_database.py
```

### API Test Failures

```bash
# Ensure API server is running
curl http://localhost:8000/health

# Check for port conflicts
netstat -an | grep 8000

# View API logs
tail -f logs/platform.log
```

---

## Continuous Testing

### Pre-commit Testing

```bash
# Run before committing
python test_runner.py --quick
```

### Automated Testing

```bash
# Run full suite periodically
crontab -e

# Add:
# 0 2 * * * cd /path/to/Mac-Hardening && python test_runner.py
```

---

## Test Coverage

Generate test coverage report:

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run -m pytest tests/

# Generate report
coverage report

# Generate HTML report
coverage html
open htmlcov/index.html
```

---

## Writing New Tests

### Test Template

```python
"""
New Feature Tests

Author: Adrian Johnson <adrian207@gmail.com>
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from your_module import YourClass


def test_feature_works():
    """Test that feature works as expected."""
    instance = YourClass()
    result = instance.method()
    
    assert result is not None
    assert result == expected_value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Support

For testing issues, contact:  
**Adrian Johnson** <adrian207@gmail.com>

