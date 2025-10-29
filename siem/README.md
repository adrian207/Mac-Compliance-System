# SIEM Integration Module

**Author:** Adrian Johnson <adrian207@gmail.com>  
**Version:** 0.9.6

## Overview

The SIEM Integration module enables exporting security events, anomalies, risk assessments, and compliance data to enterprise SIEM platforms. Supports multiple SIEM types with intelligent batching, retry logic, and health monitoring.

## Supported SIEM Platforms

- **Splunk** - HTTP Event Collector (HEC)
- **Elastic Stack** - Elasticsearch Bulk API
- **Syslog** - RFC 5424 protocol (UDP/TCP/TLS)
- **CEF** - Common Event Format via Syslog
- **Generic** - Extensible architecture for additional SIEMs

## Key Features

- **Multi-Platform Support** - Connect to multiple SIEMs simultaneously
- **Event Batching** - Efficient bulk export with configurable batch sizes
- **Retry Logic** - Automatic retry with exponential backoff
- **Health Monitoring** - Connection health checks and status tracking
- **Event Formatting** - SIEM-specific formatters (HEC, Bulk API, CEF, Syslog)
- **Selective Export** - Filter by event type and severity
- **REST API** - Complete API for configuration and management
- **Statistics Tracking** - Success rates, throughput, failure tracking

## Architecture

```
siem/
├── models.py                      # Data models
├── manager.py                     # SIEM manager (orchestration)
├── api.py                         # REST API endpoints
├── connectors/                    # SIEM connectors
│   ├── base.py                   # Base connector class
│   ├── splunk.py                 # Splunk HEC connector
│   ├── elastic.py                # Elasticsearch connector
│   └── syslog.py                 # Syslog/CEF connector
└── formatters/                    # Event formatters
    ├── anomaly.py                # Anomaly formatter
    ├── risk.py                   # Risk assessment formatter
    └── compliance.py             # Compliance formatter
```

## Event Types

The following event types can be exported to SIEM:

1. **Anomaly** - Behavioral anomalies detected by analytics engine
2. **Risk Assessment** - Device risk score assessments  
3. **Compliance Check** - Compliance validation results
4. **Telemetry** - Device telemetry data
5. **Workflow Execution** - Workflow automation events
6. **Security Event** - General security events
7. **Alert** - Security alerts and notifications

## Quick Start

### 1. Configure SIEM Connection

**Splunk HEC:**
```bash
curl -X POST http://localhost:8000/api/v1/siem/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Splunk",
    "siem_type": "splunk",
    "endpoint": "splunk.example.com",
    "port": 8088,
    "use_ssl": true,
    "verify_ssl": true,
    "auth_type": "token",
    "auth_token": "your-hec-token-here",
    "index_name": "zerotrust",
    "source_type": "_json",
    "enabled_event_types": ["anomaly", "risk_assessment", "compliance_check"],
    "batch_size": 100,
    "batch_interval_seconds": 60,
    "enabled": true
  }'
```

**Elasticsearch:**
```bash
curl -X POST http://localhost:8000/api/v1/siem/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Elastic",
    "siem_type": "elastic",
    "endpoint": "elasticsearch.example.com",
    "port": 9200,
    "use_ssl": true,
    "auth_type": "basic",
    "username": "elastic_user",
    "password": "elastic_password",
    "index_name": "zerotrust-events",
    "enabled_event_types": ["anomaly", "risk_assessment", "security_event"],
    "batch_size": 500,
    "enabled": true
  }'
```

**Syslog (CEF):**
```bash
curl -X POST http://localhost:8000/api/v1/siem/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SIEM via Syslog",
    "siem_type": "cef",
    "endpoint": "syslog.example.com",
    "port": 514,
    "auth_type": "tcp",
    "facility": "local0",
    "enabled_event_types": ["anomaly", "alert"],
    "enabled": true
  }'
```

### 2. Test Connection

```bash
curl -X POST http://localhost:8000/api/v1/siem/connections/SIEM-CONN-ABC123/test
```

### 3. Export Events

Events are automatically exported based on configuration. You can also manually export:

```bash
curl -X POST http://localhost:8000/api/v1/siem/export \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "anomaly",
    "event_source": "DEV-123",
    "event_data": {
      "anomaly_id": "ANO-ABC123",
      "severity": "high",
      "title": "Unusual network activity detected"
    }
  }'
```

## Usage

### Python API

**Initialize SIEM Manager:**
```python
from siem.manager import SIEMManager
from siem.models import SIEMEventType

manager = SIEMManager(db)
```

**Export Anomaly to SIEM:**
```python
from analytics.models import AnomalyDetection
from siem.formatters import AnomalyFormatter

# Get anomaly
anomaly = db.query(AnomalyDetection).filter(
    AnomalyDetection.anomaly_id == "ANO-ABC123"
).first()

# Format for SIEM
event_data = AnomalyFormatter.format(anomaly)

# Export to all configured SIEMs
results = manager.export_event(
    event_type=SIEMEventType.ANOMALY,
    event_source=anomaly.device_id,
    event_data=event_data
)

print(f"Export results: {results}")
```

**Process Pending Events:**
```python
# Process up to 1000 pending events
results = manager.process_pending_events(limit=1000)

for connection_id, (successful, failed) in results.items():
    print(f"{connection_id}: {successful} sent, {failed} failed")
```

**Retry Failed Events:**
```python
# Retry events that failed within last 24 hours
results = manager.retry_failed_events(max_age_hours=24)
```

**Health Check:**
```python
# Check all connections
health = manager.health_check_all()

for connection_id, status in health.items():
    print(f"{connection_id}: {status['status']}")
```

### REST API Endpoints

#### Connections

```bash
# List all connections
GET /api/v1/siem/connections

# Get specific connection
GET /api/v1/siem/connections/{connection_id}

# Create connection
POST /api/v1/siem/connections

# Update connection
PUT /api/v1/siem/connections/{connection_id}

# Delete connection
DELETE /api/v1/siem/connections/{connection_id}

# Test connection
POST /api/v1/siem/connections/{connection_id}/test
```

#### Events

```bash
# Export event
POST /api/v1/siem/export

# Process pending events
POST /api/v1/siem/process-pending

# Retry failed events
POST /api/v1/siem/retry-failed
```

#### Monitoring

```bash
# Get statistics
GET /api/v1/siem/statistics

# Health check all
GET /api/v1/siem/health
```

## Connector Details

### Splunk HEC Connector

**Format:** Splunk HTTP Event Collector format
```json
{
  "time": 1698537600.0,
  "host": "zerotrust-platform",
  "source": "zerotrust:anomaly",
  "sourcetype": "_json",
  "index": "zerotrust",
  "event": {
    "event_id": "ANO-ABC123",
    "anomaly_type": "authentication",
    "severity": "high",
    ...
  }
}
```

**Features:**
- Batch support (newline-separated JSON)
- Automatic HEC token authentication
- Index and sourcetype configuration
- SSL/TLS support

**Configuration:**
- `endpoint`: Splunk server hostname
- `port`: HEC port (default: 8088)
- `auth_token`: HEC token
- `index_name`: Target index
- `source_type`: Sourcetype (default: `_json`)

### Elasticsearch Connector

**Format:** Elasticsearch Bulk API (ndjson)
```json
{"index": {"_index": "zerotrust-events", "_id": "ANO-ABC123"}}
{"@timestamp": "2025-10-29T12:00:00Z", "event": {...}, ...}
```

**Features:**
- Bulk API for efficient indexing
- Elastic Common Schema (ECS) mapping
- Basic and API key authentication
- SSL/TLS support
- Date-based index support (optional)

**Configuration:**
- `endpoint`: Elasticsearch hostname
- `port`: ES port (default: 9200)
- `auth_type`: `basic` or `apikey`
- `username/password`: For basic auth
- `auth_token`: For API key auth
- `index_name`: Target index

### Syslog/CEF Connector

**Syslog Format (RFC 5424):**
```
<134>1 2025-10-29T12:00:00Z zerotrust-platform zerotrust - anomaly - type=authentication device=DEV-123
```

**CEF Format:**
```
CEF:0|ZeroTrust|Mac-Compliance-System|1.0|authentication|Unusual Authentication|7|externalId=ANO-ABC123 dvc=DEV-123 msg=Unusual authentication pattern detected
```

**Features:**
- UDP, TCP, and TLS support
- RFC 5424 syslog format
- CEF (Common Event Format) support
- Configurable facility and severity mapping
- MITRE ATT&CK integration

**Configuration:**
- `endpoint`: Syslog server hostname
- `port`: Syslog port (default: 514)
- `auth_type`: `udp`, `tcp`, or `tls`
- `facility`: Syslog facility (default: `local0`)
- `siem_type`: Use `cef` for CEF format

## Event Formatting

### Anomaly Events

```json
{
  "event_id": "ANO-ABC123",
  "timestamp": "2025-10-29T12:00:00Z",
  "event_type": "anomaly",
  "source": "DEV-123",
  "anomaly": {
    "type": "authentication",
    "severity": "high",
    "score": 85.0,
    "confidence": 0.92
  },
  "detection": {
    "method": "statistical",
    "detector": "StatisticalDetector"
  },
  "title": "Excessive failed authentication attempts",
  "description": "Device has 15 failed authentication attempts...",
  "recommendations": [
    "Lock user account",
    "Verify user identity"
  ],
  "mitre_attack": {
    "tactic": "TA0006",
    "tactic_name": "Credential Access",
    "technique": "T1110",
    "technique_name": "Brute Force"
  }
}
```

### Risk Assessment Events

```json
{
  "event_id": "RISK-ABC123",
  "timestamp": "2025-10-29T12:00:00Z",
  "event_type": "risk_assessment",
  "source": "DEV-123",
  "risk": {
    "total_score": 75,
    "level": "high",
    "previous_score": 45,
    "score_change": 30
  },
  "risk_components": {
    "security_posture": 60,
    "compliance": 80,
    "vulnerability": 70,
    "behavior": 85
  },
  "risk_factors": [
    "Multiple security controls disabled",
    "High anomaly count"
  ]
}
```

### Compliance Events

```json
{
  "event_id": "COMP-456",
  "timestamp": "2025-10-29T12:00:00Z",
  "event_type": "compliance_check",
  "source": "DEV-123",
  "compliance": {
    "is_compliant": false,
    "score": 65,
    "policies_total": 20,
    "policies_passed": 13,
    "policies_failed": 7
  },
  "violations": {
    "critical_count": 2,
    "critical_policies": ["FileVault disabled", "SIP disabled"]
  },
  "severity": "critical"
}
```

## Batching and Performance

### Batch Configuration

```python
# Per-connection batch settings
connection.batch_size = 100  # Events per batch
connection.batch_interval_seconds = 60  # Max wait time
```

### Performance Tuning

**For High-Volume Environments:**
- Increase `batch_size` (100-1000)
- Decrease `batch_interval_seconds` (30-60)
- Use multiple workers for parallel processing
- Enable connection pooling

**For Low-Latency Requirements:**
- Decrease `batch_size` (10-50)
- Decrease `batch_interval_seconds` (10-30)
- Use TCP/TLS instead of UDP for reliability

## Retry Logic

**Automatic Retry:**
- Failed events are automatically retried
- Exponential backoff between retries
- Maximum retry attempts (default: 3)
- Configurable retry delay

**Manual Retry:**
```bash
# Retry events failed within last 24 hours
curl -X POST "http://localhost:8000/api/v1/siem/retry-failed?max_age_hours=24"
```

## Health Monitoring

**Connection Health States:**
- `healthy` - Connection working normally
- `degraded` - Partial failures
- `failed` - Connection not working
- `unknown` - Not yet checked

**Health Check:**
```bash
# Check all connections
curl http://localhost:8000/api/v1/siem/health
```

**Response:**
```json
{
  "timestamp": "2025-10-29T12:00:00Z",
  "connections": {
    "SIEM-CONN-ABC123": {
      "healthy": true,
      "status": "healthy",
      "connection_id": "SIEM-CONN-ABC123",
      "siem_type": "splunk",
      "last_check": "2025-10-29T12:00:00Z"
    }
  }
}
```

## Statistics and Monitoring

**Get Statistics:**
```bash
curl http://localhost:8000/api/v1/siem/statistics
```

**Response:**
```json
{
  "total_events": 10000,
  "sent_events": 9500,
  "failed_events": 300,
  "pending_events": 200,
  "success_rate": 0.95,
  "active_connections": 3
}
```

## Troubleshooting

### Events Not Exporting

**Check:**
1. Connection is enabled
2. Event type is in `enabled_event_types`
3. Connection health is good
4. Network connectivity to SIEM

**Solutions:**
```bash
# Test connection
curl -X POST http://localhost:8000/api/v1/siem/connections/SIEM-CONN-ABC123/test

# Check health
curl http://localhost:8000/api/v1/siem/health

# Process pending manually
curl -X POST http://localhost:8000/api/v1/siem/process-pending
```

### High Failure Rate

**Check:**
- SIEM server capacity
- Network latency
- Batch size too large
- Authentication issues

**Solutions:**
- Reduce batch size
- Increase retry delay
- Check SIEM server logs
- Verify credentials

### Connection Timeouts

**Check:**
- Network connectivity
- Firewall rules
- SSL/TLS configuration
- SIEM server load

**Solutions:**
- Increase timeout (modify connector)
- Use connection pooling
- Check firewall/network paths

## Security Considerations

- **Credentials:** Store auth tokens/passwords encrypted
- **SSL/TLS:** Always use SSL for production
- **Certificate Validation:** Enable `verify_ssl` in production
- **Network Security:** Use private networks/VPNs
- **Access Control:** Restrict SIEM API access
- **Audit Logging:** Track configuration changes

## Best Practices

1. **Start Small:** Begin with one event type, expand gradually
2. **Monitor Health:** Regular health checks on all connections
3. **Tune Batching:** Optimize batch size for your environment
4. **Handle Failures:** Review and retry failed events regularly
5. **Test Thoroughly:** Test connections before production use
6. **Document Config:** Maintain documentation of SIEM configs
7. **Security First:** Use TLS, verify certificates, encrypt credentials

## Future Enhancements

- **IBM QRadar Connector** - Native QRadar API integration
- **Microsoft Sentinel** - Azure Sentinel connector
- **AWS Security Hub** - AWS Security Hub integration
- **Event Enrichment** - Add threat intelligence data
- **Custom Connectors** - Plugin architecture for custom SIEMs
- **Performance Metrics** - Detailed throughput and latency tracking
- **Data Masking** - PII/sensitive data masking options

## Support

For issues or questions:
- **GitHub:** https://github.com/adrian207/Mac-Compliance-System
- **Email:** adrian207@gmail.com
- **Documentation:** See `docs/` directory

## License

See LICENSE file in the project root.

