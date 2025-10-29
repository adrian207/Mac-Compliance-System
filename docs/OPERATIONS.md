# Operations Guide

**Author:** Adrian Johnson <adrian207@gmail.com>

## Day-to-Day Operations

This guide covers operational procedures for maintaining the Zero Trust platform.

---

## System Monitoring

### Health Checks

**Platform Health:**

```bash
# Check platform status
curl http://localhost:8000/health

# Check metrics
curl http://localhost:9090/metrics

# View logs
tail -f logs/platform.log
```

**Key Metrics to Monitor:**

- Device count and risk distribution
- Risk assessment completion rate
- Workflow execution success rate
- Integration API response times
- Database connection pool utilization
- Alert delivery success rate
- **Anomaly detection rate (v0.9.5+)**
- **Behavioral baseline coverage (v0.9.5+)**
- **False positive rate (v0.9.5+)**

### Dashboard Access

**Prometheus Metrics:** `http://localhost:9090/metrics`  
**API Documentation:** `http://localhost:8000/docs`  
**Platform Status:** `http://localhost:8000/health`

---

## Alerting

### Alert Levels

**Critical (Immediate Response Required)**
- Multiple integration failures
- Database connection loss
- High-risk device count spike (>20% of fleet)
- Platform service down

**High (Response within 1 hour)**
- Single integration failure
- Workflow execution failures (>10%)
- Critical compliance violations
- Authentication failures

**Medium (Response within 4 hours)**
- Device risk score increases
- Compliance drift detected
- Integration performance degradation

**Low (Response within 24 hours)**
- General compliance violations
- Routine security events
- Performance warnings

### Alert Channels

**Email:** Configured via SMTP settings  
**Slack:** Webhook integration  
**PagerDuty:** For critical alerts  
**Webhook:** Custom integrations

---

## Anomaly Detection and Behavioral Analytics (v0.9.5+)

### Monitoring Anomaly Detection

**Check Detection Statistics:**

```bash
# Get real-time detection stats
curl http://localhost:8000/api/v1/analytics/statistics

# View analytics summary
curl http://localhost:8000/api/v1/analytics/summary
```

**Key Metrics to Monitor:**
- Detection rate (anomalies per telemetry record)
- False positive rate (< 5% target)
- Anomalies by severity (critical, high, medium, low)
- Anomalies by type (authentication, network, process, system)
- Baseline coverage (% of devices with baselines)

### Managing Anomalies

**List Recent Anomalies:**

```bash
# All unresolved anomalies
curl "http://localhost:8000/api/v1/analytics/anomalies?resolved=false&limit=100"

# Critical severity only
curl "http://localhost:8000/api/v1/analytics/anomalies?severity=critical"

# Specific device
curl "http://localhost:8000/api/v1/analytics/anomalies?device_id=DEV-123"
```

**Investigate Anomaly:**

```bash
# Get full anomaly details
curl http://localhost:8000/api/v1/analytics/anomalies/ANO-ABC123DEF456

# Check related telemetry data
# Review observed vs. expected values
# Examine detection method and confidence
# Read recommended actions
```

**Resolve Anomaly:**

```bash
# Mark as resolved after investigation
curl -X POST http://localhost:8000/api/v1/analytics/anomalies/ANO-ABC123DEF456/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "resolved_by": "analyst@example.com",
    "notes": "Confirmed false alarm - scheduled maintenance activity"
  }'
```

**Mark False Positive:**

```bash
# System will learn from this feedback
curl -X POST http://localhost:8000/api/v1/analytics/anomalies/ANO-ABC123DEF456/false-positive
```

### Baseline Management

**Check Baseline Status:**

```bash
# List all baselines
curl http://localhost:8000/api/v1/analytics/baselines

# Check specific device
curl "http://localhost:8000/api/v1/analytics/baselines?device_id=DEV-123"
```

**Build New Baselines:**

```bash
# For new device (after 30 days of data collection)
curl -X POST http://localhost:8000/api/v1/analytics/baselines/build \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEV-123",
    "baseline_type": "authentication",
    "force_refresh": false
  }'

# Rebuild all baseline types
for type in authentication network process system; do
  curl -X POST http://localhost:8000/api/v1/analytics/baselines/build \
    -H "Content-Type: application/json" \
    -d "{\"device_id\": \"DEV-123\", \"baseline_type\": \"$type\"}"
done
```

**Refresh Stale Baselines:**

```bash
# Refresh baselines older than 7 days
python scripts/refresh_baselines.py --days 7

# Force refresh for specific device
python scripts/refresh_baselines.py --device DEV-123 --force
```

### Profile Management

**View Device Profiles:**

```bash
# Get device behavioral profile
curl http://localhost:8000/api/v1/analytics/profiles/DEV-123

# Profile includes:
# - Activity regularity score
# - Risk appetite score  
# - Typical behavior patterns
# - Confidence score
```

**Rebuild Profiles:**

```bash
# After significant behavior changes
curl -X POST http://localhost:8000/api/v1/analytics/profiles/DEV-123/build
```

### Alert Management

**Test Alert Delivery:**

```bash
# Send test alert
python scripts/test_alert.py --recipients soc@example.com

# Check alert configuration
python scripts/check_smtp.py
```

**Configure Alert Recipients:**

```yaml
# In config/config.yaml
alerting:
  recipients:
    default:
      - soc@example.com
    critical:
      - soc@example.com
      - ciso@example.com
      - oncall@example.com
```

### Troubleshooting Analytics

**No Anomalies Detected:**

```bash
# Check if baselines exist
curl http://localhost:8000/api/v1/analytics/baselines | jq '.[] | .device_id'

# Verify detection engine is processing telemetry
tail -f logs/analytics.log | grep "process_telemetry"

# Check detection thresholds
cat config/config.yaml | grep -A 5 "thresholds:"
```

**Too Many False Positives:**

```bash
# Review false positive rate
curl http://localhost:8000/api/v1/analytics/statistics | jq '.false_positive_rate'

# Adjust z-score threshold (increase from 3.0 to 4.0)
# Edit config/config.yaml:
analytics:
  thresholds:
    z_score: 4.0  # Less sensitive

# Restart platform to apply changes
docker-compose restart platform
```

**Alerts Not Sending:**

```bash
# Test SMTP configuration
python scripts/test_smtp.py

# Check alert logs
tail -f logs/alerting.log

# Verify anomaly severity meets threshold
curl http://localhost:8000/api/v1/analytics/anomalies/ANO-ABC123 | jq '.anomaly_severity'
```

### Performance Tuning

**For High-Volume Environments:**

```yaml
# In config/config.yaml
analytics:
  performance:
    batch_size: 100  # Process telemetry in batches
    batch_interval_seconds: 60
    worker_threads: 4  # Parallel processing
    cache_baselines: true  # Cache frequently accessed baselines
```

**Database Optimization for Analytics:**

```sql
-- Add indexes for analytics queries
CREATE INDEX idx_anomalies_device_detected ON anomaly_detections(device_id, detected_at);
CREATE INDEX idx_anomalies_severity_resolved ON anomaly_detections(anomaly_severity, is_resolved);
CREATE INDEX idx_baselines_device_type ON behavior_baselines(device_id, baseline_type);
```

### Regular Maintenance

**Weekly Tasks:**
- Review unresolved anomalies
- Mark confirmed false positives
- Refresh baselines for devices with significant changes
- Review detection statistics and adjust thresholds

**Monthly Tasks:**
- Rebuild baselines for all devices
- Rebuild device profiles
- Analyze false positive trends
- Retrain ML models (if using ML detection)
- Archive resolved anomalies older than 90 days

**Quarterly Tasks:**
- Review and update detection rules
- Audit alert recipient lists
- Performance optimization review
- Capacity planning for baseline storage

---

## Device Management

### Onboarding New Devices

**Automated Enrollment:**

```bash
# Device enrolls via MDM
# Platform automatically:
# 1. Detects new device
# 2. Collects initial telemetry
# 3. Performs risk assessment
# 4. Applies baseline policies
# 5. Enables monitoring
```

**Manual Device Registration:**

```python
# Via API
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ABC123",
    "hostname": "macbook-pro",
    "user_email": "user@company.com"
  }'
```

### Device Risk Remediation

**High Risk Device Response:**

1. **Immediate Actions (Automated):**
   - Revoke network access tokens
   - Force MFA re-authentication
   - Isolate to quarantine network
   - Alert SOC team

2. **Investigation:**
   - Review risk factors
   - Check security events
   - Analyze telemetry data
   - Verify compliance status

3. **Remediation:**
   - Deploy corrective policies
   - Apply security patches
   - Remove malicious software
   - Restore compliant configuration

4. **Restoration:**
   - Verify fixes applied
   - Re-assess risk score
   - Remove network isolation
   - Enable normal access

### Offboarding Devices

```bash
# Mark device as inactive
curl -X PUT http://localhost:8000/api/v1/devices/ABC123 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Revoke all access
# Remove from MDM
# Archive historical data
```

---

## Compliance Management

### Running Compliance Checks

**On-Demand Check:**

```python
from hardening.compliance_checker import check_device_compliance
from telemetry.collector import collect_telemetry

telemetry = collect_telemetry()
compliance = check_device_compliance(telemetry)

print(f"Compliance Status: {compliance['is_compliant']}")
print(f"Score: {compliance['compliance_score']}")
print(f"Violations: {len(compliance['violations'])}")
```

**Scheduled Checks:**

Compliance checks run automatically based on configuration:

```yaml
telemetry:
  security_status_interval_minutes: 15
```

### Handling Compliance Violations

**Critical Violations:**
- Encryption disabled
- System Integrity Protection disabled
- Firewall disabled
- Password requirements not met

**Automatic Remediation:**
- Deploy policies via Kandji
- Apply security settings
- Install required software
- Enable security features

**Manual Remediation:**
- SIP enablement (requires reboot)
- Hardware security module configuration
- Certificate installation
- Complex authentication setup

### Compliance Reporting

**Generate Compliance Report:**

```python
# Via API
curl http://localhost:8000/api/v1/reports/compliance \
  -H "X-API-Key: your-api-key"

# Export format: JSON, CSV, PDF
```

**Report Contents:**
- Fleet-wide compliance score
- Devices by compliance status
- Violation breakdown by severity
- Trend analysis
- Remediation status

---

## Workflow Management

### Managing Automated Workflows

**View Workflow Status:**

```bash
# List recent executions
curl http://localhost:8000/api/v1/workflows/executions?limit=10

# Get execution details
curl http://localhost:8000/api/v1/workflows/executions/12345
```

**Trigger Manual Workflow:**

```bash
curl -X POST http://localhost:8000/api/v1/workflows/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "high_risk_response",
    "trigger_type": "manual",
    "trigger_data": {
      "device_id": "123",
      "user_id": "user@company.com",
      "risk_score": 85
    }
  }'
```

### Common Workflow Operations

**High-Risk Device Response:**
- Automatically triggers at risk score > 75
- Actions: Token revocation, MFA enforcement, network isolation
- Creates incident ticket
- Alerts SOC team

**Compliance Remediation:**
- Triggers on 3+ violations
- Actions: Deploy policies, restrict access, notify user
- Escalates if unresolved after 24 hours

**Zero Trust Access Enforcement:**
- Triggers on new device connection
- Actions: Verify enrollment, validate posture, apply policies

---

## Integration Management

### Kandji MDM Operations

**Sync Device Inventory:**

```python
from integrations.kandji import get_kandji_client

with get_kandji_client() as kandji:
    devices = kandji.get_devices(limit=100)
    for device in devices:
        # Process device data
        print(f"Device: {device['name']}")
```

**Deploy Policy:**

```python
kandji.deploy_policy(device_id="123", policy_id="baseline-policy")
```

**Common Operations:**
- Device enrollment status check
- Software installation
- Policy deployment
- Compliance status retrieval
- Remote lock/wipe

### Zscaler Operations

**Manage Access Tokens:**

```python
from integrations.zscaler import get_zscaler_client

with get_zscaler_client() as zscaler:
    # Revoke user tokens
    zscaler.revoke_all_user_tokens(user_id="user@company.com")
    
    # Force re-authentication
    zscaler.force_reauthentication(user_id="user@company.com")
```

**Apply Risk-Based Policies:**

```python
# Apply policy based on risk level
zscaler.apply_risk_based_policy(
    user_id="user@company.com",
    risk_level="high"
)
```

**Common Operations:**
- Token management
- Policy application
- Network isolation
- Access logs retrieval
- Security event monitoring

### Seraphic Operations

**Browser Session Management:**

```python
from integrations.seraphic import get_seraphic_client

with get_seraphic_client() as seraphic:
    # Get active sessions
    sessions = seraphic.get_user_sessions(user_id="user@company.com")
    
    # Isolate risky session
    seraphic.isolate_session(session_id="session-123")
```

**Common Operations:**
- Session isolation
- URL blocking
- DLP policy application
- Threat detection monitoring
- Browsing activity analysis

---

## Incident Response

### Incident Workflow

**1. Detection**
- Automated alert triggered
- High-risk device detected
- Security event correlation
- Manual report

**2. Triage**
- Review incident details
- Check device risk factors
- Analyze security events
- Determine severity

**3. Containment**
- Isolate affected device
- Revoke access tokens
- Block malicious connections
- Prevent lateral movement

**4. Investigation**
- Collect forensic data
- Review logs and telemetry
- Identify root cause
- Assess impact

**5. Remediation**
- Remove threats
- Patch vulnerabilities
- Restore configuration
- Apply corrective policies

**6. Recovery**
- Verify security posture
- Test functionality
- Restore access
- Document lessons learned

### Incident Response Playbooks

**Compromised Device:**

```yaml
Severity: Critical
Response Time: Immediate

Actions:
1. Isolate device from network
2. Revoke all access tokens
3. Collect forensic evidence
4. Scan for malware
5. Rebuild from known good state
6. Verify security before restoring access
```

**Data Exfiltration Attempt:**

```yaml
Severity: Critical
Response Time: Immediate

Actions:
1. Block outbound connections
2. Isolate user sessions
3. Review DLP alerts
4. Analyze network traffic
5. Identify compromised accounts
6. Remediate and notify stakeholders
```

**Compliance Violation:**

```yaml
Severity: High
Response Time: 1 hour

Actions:
1. Deploy corrective policies
2. Restrict network access
3. Notify device owner
4. Monitor remediation
5. Verify compliance
6. Document for audit
```

---

## Performance Optimization

### Database Optimization

**Regular Maintenance:**

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Update statistics
ANALYZE;

-- Reindex if needed
REINDEX DATABASE zerotrust_security;
```

**Query Performance:**

```sql
-- Identify slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Add indexes as needed
CREATE INDEX idx_risk_scores_device_time 
ON risk_scores (device_id, assessment_time DESC);
```

### Cache Optimization

**Redis Configuration:**

```yaml
redis:
  maxmemory: 2gb
  maxmemory_policy: allkeys-lru
  save: "900 1 300 10 60 10000"
```

**Cache Strategy:**
- Device telemetry: 5 minutes
- Risk scores: 1 minute
- Compliance results: 15 minutes
- Integration responses: 30 seconds

### API Performance

**Rate Limiting:**

```yaml
api:
  rate_limit:
    enabled: true
    requests_per_minute: 100
    burst: 20
```

**Connection Pooling:**

```yaml
database:
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600
```

---

## Data Retention

### Retention Policies

**Telemetry Data:**
- Raw telemetry: 90 days
- Aggregated data: 365 days
- Historical trends: 2 years

**Risk Assessments:**
- Individual scores: 180 days
- Trend data: 2 years
- Archived reports: 7 years

**Security Events:**
- Event details: 365 days
- Incident records: 7 years
- Audit logs: 7 years

### Data Cleanup

**Automated Cleanup:**

```bash
# Cleanup script runs daily
python scripts/cleanup_old_data.py --days 90
```

**Manual Cleanup:**

```sql
-- Delete old telemetry snapshots
DELETE FROM telemetry_snapshots 
WHERE snapshot_time < NOW() - INTERVAL '90 days';

-- Archive old incidents
INSERT INTO incident_archive 
SELECT * FROM incident_tickets 
WHERE created_at < NOW() - INTERVAL '2 years';
```

---

## Backup Procedures

### Daily Backups

**Automated Backup:**

```bash
#!/bin/bash
# /opt/zerotrust/backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
pg_dump -h $DB_HOST -U $DB_USER zerotrust_security \
  | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Configuration backup
tar -czf $BACKUP_DIR/config_$TIMESTAMP.tar.gz config/

# Retention: 30 days
find $BACKUP_DIR -mtime +30 -delete
```

### Restore Procedures

**Database Restore:**

```bash
# Stop platform
systemctl stop zerotrust-platform

# Restore database
gunzip < /backups/db_20250128.sql.gz \
  | psql -h $DB_HOST -U $DB_USER zerotrust_security

# Start platform
systemctl start zerotrust-platform
```

---

## Security Hardening

### Platform Security

**Authentication:**
- API key authentication required
- Rotate API keys quarterly
- Use strong passwords for database
- Enable MFA for admin access

**Network Security:**
- Use TLS 1.3 for all connections
- Firewall rules limiting access
- VPN required for remote administration
- Network segmentation

**Audit Logging:**
- Log all administrative actions
- Monitor for suspicious activity
- Retain logs per compliance requirements
- Regular log review

---

## Support and Escalation

### Support Tiers

**Tier 1: Self-Service**
- Documentation review
- Log analysis
- Basic troubleshooting

**Tier 2: Platform Team**
- Configuration issues
- Integration problems
- Performance optimization

**Tier 3: Development Team**
- Bug fixes
- Feature requests
- Architecture changes

### Contact Information

**Platform Support:**  
Adrian Johnson <adrian207@gmail.com>

**Emergency Contact:**  
On-call rotation via PagerDuty

---

## Maintenance Windows

### Scheduled Maintenance

**Weekly Maintenance:**
- Sundays 02:00-04:00 UTC
- Database maintenance
- Cache cleanup
- Log rotation

**Monthly Maintenance:**
- First Sunday 02:00-06:00 UTC
- Platform updates
- Security patches
- Performance optimization

### Emergency Maintenance

Performed as needed for:
- Critical security patches
- Service restoration
- Data integrity issues
- Major incidents

---

## Change Management

### Change Request Process

1. **Submit Change Request**
   - Description of change
   - Business justification
   - Risk assessment
   - Rollback plan

2. **Review and Approval**
   - Technical review
   - Security review
   - Management approval

3. **Implementation**
   - Schedule maintenance window
   - Execute changes
   - Test thoroughly
   - Document results

4. **Post-Implementation**
   - Verify functionality
   - Monitor for issues
   - Update documentation
   - Lessons learned

---

## Disaster Recovery

### DR Procedures

**Activation Criteria:**
- Complete platform failure
- Data center outage
- Multiple component failures
- Natural disaster

**Recovery Steps:**

1. Assess situation and declare disaster
2. Activate DR team
3. Restore database from backup
4. Deploy to DR infrastructure
5. Update DNS records
6. Verify functionality
7. Resume operations
8. Plan return to primary site

**RTO:** 4 hours  
**RPO:** 1 hour

---

## Documentation Maintenance

**Keep documentation updated for:**
- Configuration changes
- New integrations
- Workflow modifications
- Operational procedures
- Incident post-mortems
- Performance tuning

**Review Schedule:**
- Operational docs: Monthly
- Technical docs: Quarterly
- Architecture docs: Semi-annually

---

For operational support, contact:  
**Adrian Johnson** <adrian207@gmail.com>

