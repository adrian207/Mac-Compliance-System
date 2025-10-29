

# Behavioral Analytics & Anomaly Detection Module

**Author:** Adrian Johnson <adrian207@gmail.com>  
**Version:** 0.9.5

## Overview

The Behavioral Analytics & Anomaly Detection module provides AI-powered threat detection using machine learning, statistical analysis, and rule-based detection to identify unusual device behavior patterns and security threats in real-time.

## Key Features

- **Multi-Method Detection** - Statistical, ML-based, and rule-based anomaly detection
- **Baseline Profiling** - Learns normal behavior patterns over 30-day periods
- **Device Profiles** - Creates comprehensive behavioral profiles for each device
- **Real-time Detection** - Processes telemetry data as it arrives
- **Intelligent Alerting** - Sends notifications for critical anomalies
- **REST API** - Programmatic access to analytics and anomalies
- **False Positive Management** - Learn from feedback to improve detection

## Architecture

```
analytics/
├── models/                        # Data models
│   └── behavior.py               # Baseline, profile, anomaly models
├── profilers/                     # Behavior profiling
│   ├── baseline_profiler.py      # Statistical baseline building
│   └── device_profiler.py        # Device behavior profiling
├── detectors/                     # Anomaly detectors
│   ├── statistical_detector.py   # Z-score and statistical methods
│   ├── ml_detector.py            # ML-based detection
│   └── rule_based_detector.py    # Known bad patterns
├── detection_engine.py            # Orchestrates all detectors
├── alerting.py                    # Alert notifications
└── api.py                         # REST API endpoints
```

## Detection Methods

### 1. Statistical Detection

Uses statistical baselines and z-score analysis to detect deviations from normal behavior.

**Approach:**
- Builds statistical baselines (mean, std dev, percentiles) from historical data
- Compares current values against baselines
- Flags anomalies when deviations exceed threshold (default: 3 standard deviations)

**Strengths:**
- High confidence for quantitative metrics
- Mathematically sound
- Explainable results

**Use Cases:**
- CPU/memory/disk usage spikes
- Unusual connection counts
- Excessive failed authentications
- Process count anomalies

**Example:**
```python
from analytics.detectors import StatisticalDetector

detector = StatisticalDetector(db, z_score_threshold=3.0)
anomalies = detector.detect_anomalies(device_id, telemetry)
```

### 2. Machine Learning Detection

[Inference] Uses Isolation Forest and ensemble methods for unsupervised anomaly detection.

**Approach:**
- Extracts numerical features from telemetry
- Trains Isolation Forest on normal behavior
- Predicts anomaly scores for new data
- Flags high-scoring instances as anomalous

**Strengths:**
- Detects complex multivariate patterns
- Adapts to new attack vectors
- Finds unknown threats

**Use Cases:**
- Complex behavioral patterns
- Multi-factor anomalies
- Zero-day threat detection
- User behavior analysis

**Example:**
```python
from analytics.detectors import MLAnomalyDetector

detector = MLAnomalyDetector(db, contamination=0.05)
# detector.train_model(training_data)  # Train first
anomalies = detector.detect_anomalies(device_id, telemetry)
```

### 3. Rule-Based Detection

Detects known bad patterns and policy violations using predefined rules.

**Approach:**
- Applies expert-defined detection rules
- Checks for known malicious indicators
- Validates security policy compliance
- Triggers on exact pattern matches

**Strengths:**
- Very high confidence (95%+)
- Immediate detection
- Actionable results

**Use Cases:**
- Multiple security controls disabled
- Known malicious processes
- Excessive failed auth attempts
- Critical configuration changes

**Example:**
```python
from analytics.detectors import RuleBasedDetector

detector = RuleBasedDetector(db)
anomalies = detector.detect_anomalies(device_id, telemetry)
```

## Baseline Profiling

### Statistical Baselines

Builds statistical profiles of normal device behavior across four categories:

#### 1. Authentication Baseline
- Failed authentication patterns
- Login time patterns (hourly/daily)
- Typical authentication sources

#### 2. Network Baseline
- Connection count statistics
- Known networks (SSIDs)
- VPN usage patterns
- Bandwidth utilization

#### 3. Process Baseline
- Typical process count
- Common running processes
- Process diversity metrics

#### 4. System Baseline
- CPU usage patterns
- Memory usage patterns
- Disk usage trends

### Building Baselines

```python
from analytics.profilers import BaselineProfiler

profiler = BaselineProfiler(db, learning_period_days=30)

# Build all baselines for a device
baselines = profiler.build_all_baselines(device_id)

# Build specific baseline type
baseline = profiler.build_baseline(
    device_id=device_id,
    baseline_type="authentication",
    force_refresh=False
)
```

### Baseline Requirements

- **Minimum Samples:** 10 data points
- **Confidence Levels:**
  - < 50 samples: 50% confidence
  - 50-100 samples: 75% confidence
  - 100+ samples: 75%+ (increases with data)

## Device Profiles

High-level behavioral profiles that summarize device characteristics:

### Profile Components

**Temporal Patterns:**
- Typical login hours (top 8 hours)
- Typical login days (top 5 days)
- Average session duration

**Network Patterns:**
- Typical networks (top 5)
- VPN usage rate
- Average bandwidth usage

**Application Patterns:**
- Common applications (top 15)
- Application diversity score (entropy-based)

**Process Patterns:**
- Typical process count
- Common processes (top 15)

**Security Patterns:**
- Typical failed auth count
- Security tool usage

**Behavior Scores:**
- Activity regularity (0-100) - How predictable
- Risk appetite (0-100) - Tendency for risky behavior

### Building Profiles

```python
from analytics.profilers import DeviceProfiler

profiler = DeviceProfiler(db, profile_period_days=90)
profile = profiler.build_profile(device_id, force_refresh=False)

print(f"Activity Regularity: {profile.activity_regularity_score}")
print(f"Risk Appetite: {profile.risk_appetite_score}")
print(f"Confidence: {profile.confidence_score}%")
```

## Real-Time Detection Engine

The Detection Engine orchestrates all detection methods:

### Features

- **Multi-Detector Orchestration** - Runs all enabled detectors
- **Deduplication** - Removes duplicate detections
- **Prioritization** - Keeps highest severity/confidence anomaly
- **Automatic Profiling** - Ensures baselines exist
- **Statistics Tracking** - Monitors detection performance

### Usage

```python
from analytics.detection_engine import DetectionEngine

engine = DetectionEngine(db, enable_ml=True)

# Process single telemetry record
anomalies = engine.process_telemetry(device_id, telemetry)

# Process batch
batch = [(device_id1, telemetry1), (device_id2, telemetry2)]
results = engine.process_batch(batch)

# Get statistics
stats = engine.get_statistics()
print(f"Detection Rate: {stats['detection_rate']:.2%}")
print(f"False Positive Rate: {stats['false_positive_rate']:.2%}")
```

### Anomaly Management

```python
# Mark as false positive
engine.mark_false_positive(anomaly_id)

# Confirm as real threat
engine.confirm_anomaly(anomaly_id)

# Resolve anomaly
engine.resolve_anomaly(
    anomaly_id=anomaly_id,
    resolved_by="analyst@example.com",
    notes="Investigated and remediated"
)
```

## Alerting System

Sends email notifications for detected anomalies.

### Configuration

```python
from analytics.alerting import AnomalyAlerter

email_config = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "alerts@example.com",
    "smtp_password": "password",
    "use_tls": True
}

alerter = AnomalyAlerter(
    db,
    email_config=email_config,
    alert_recipients=["soc@example.com", "admin@example.com"]
)
```

### Sending Alerts

```python
# Alert single anomaly
success = alerter.alert_anomaly(
    anomaly=anomaly,
    recipients=["analyst@example.com"]
)

# Alert multiple anomalies (batched by severity)
sent_count = alerter.alert_multiple(
    anomalies=anomalies,
    recipients=["soc@example.com"]
)
```

### Alert Triggering

Alerts are sent for:
- **Medium severity and higher**
- **Not previously alerted**
- **Not marked as false positive**
- **Not already resolved**

### Email Format

Alerts include:
- Severity level with color coding
- Device identifier
- Anomaly type and description
- Detection details (method, score, confidence)
- Observed vs. expected values
- Recommended actions
- Link to view in platform

## API Endpoints

### Anomalies

- `GET /api/v1/analytics/anomalies` - List anomalies
- `GET /api/v1/analytics/anomalies/{id}` - Get anomaly details
- `POST /api/v1/analytics/anomalies/{id}/resolve` - Resolve anomaly
- `POST /api/v1/analytics/anomalies/{id}/false-positive` - Mark false positive
- `POST /api/v1/analytics/anomalies/{id}/alert` - Send alert

### Baselines

- `GET /api/v1/analytics/baselines` - List baselines
- `POST /api/v1/analytics/baselines/build` - Build baseline

### Profiles

- `GET /api/v1/analytics/profiles/{device_id}` - Get profile
- `POST /api/v1/analytics/profiles/{device_id}/build` - Build profile

### Analytics

- `GET /api/v1/analytics/summary` - Get summary statistics
- `GET /api/v1/analytics/statistics` - Get detection statistics

## Usage Examples

### Complete Detection Pipeline

```python
from sqlalchemy.orm import Session
from analytics.detection_engine import DetectionEngine
from analytics.alerting import AnomalyAlerter
from telemetry.models import DeviceTelemetry

# Initialize components
engine = DetectionEngine(db, enable_ml=True)
alerter = AnomalyAlerter(db, email_config=email_config)

# Process telemetry
telemetry = db.query(DeviceTelemetry).filter(
    DeviceTelemetry.device_id == device_id
).order_by(DeviceTelemetry.collection_time.desc()).first()

# Detect anomalies
anomalies = engine.process_telemetry(device_id, telemetry)

# Send alerts for critical anomalies
if anomalies:
    print(f"Detected {len(anomalies)} anomalies")
    
    critical = [a for a in anomalies if a.anomaly_severity == "critical"]
    if critical:
        alerter.alert_multiple(critical, recipients=["soc@example.com"])
```

### API Usage

```bash
# List recent anomalies
curl http://localhost:8000/api/v1/analytics/anomalies?limit=50

# Get specific anomaly
curl http://localhost:8000/api/v1/analytics/anomalies/ANO-ABC123DEF456

# Resolve anomaly
curl -X POST http://localhost:8000/api/v1/analytics/anomalies/ANO-ABC123DEF456/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "resolved_by": "analyst@example.com",
    "notes": "False alarm - scheduled maintenance"
  }'

# Build baseline
curl -X POST http://localhost:8000/api/v1/analytics/baselines/build \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEV-123",
    "baseline_type": "authentication",
    "force_refresh": false
  }'

# Get analytics summary
curl http://localhost:8000/api/v1/analytics/summary
```

## Data Models

### AnomalyDetection

Records detected anomalies:
- `anomaly_id` - Unique identifier
- `device_id` - Device that triggered anomaly
- `anomaly_type` - Type (authentication, network, process, etc.)
- `anomaly_severity` - Severity level
- `detection_method` - Method used (statistical, ml_model, rule_based)
- `anomaly_score` - Score (0-100)
- `confidence` - Confidence level (0-1)
- `feature_name` - Which feature is anomalous
- `observed_value` - What was observed
- `expected_value` - What was expected
- `deviation` - Statistical deviation (z-score)
- `title` - Anomaly title
- `description` - Detailed description
- `recommendations` - List of recommended actions
- `is_confirmed` - Manually confirmed
- `is_false_positive` - Marked as false positive
- `is_resolved` - Resolution status
- `alert_sent` - Alert delivery status
- `detected_at` - Detection timestamp

### BehaviorBaseline

Statistical baselines for device behavior:
- `baseline_id` - Unique identifier
- `device_id` - Device identifier
- `baseline_type` - Type (authentication, network, process, system)
- `learning_start` - Learning period start
- `learning_end` - Learning period end
- `sample_count` - Number of samples
- `confidence_score` - Baseline confidence (0-100)
- `mean_values` - Mean values for metrics
- `std_dev_values` - Standard deviations
- `percentiles` - Percentile values (25th, 50th, 75th, 95th, 99th)
- `common_values` - Most common categorical values
- `hourly_patterns` - Hour-of-day activity distribution
- `daily_patterns` - Day-of-week activity distribution
- `is_active` - Active status
- `needs_refresh` - Refresh indicator

### BehaviorProfile

High-level device behavioral profile:
- `profile_id` - Unique identifier
- `device_id` - Device identifier
- `profile_version` - Version number
- `typical_login_hours` - Typical login hours
- `typical_login_days` - Typical login days
- `typical_networks` - Known networks
- `typical_vpn_usage` - VPN usage pattern
- `common_applications` - Top applications
- `application_diversity` - App diversity score
- `typical_process_count` - Normal process count
- `common_processes` - Top processes
- `activity_regularity_score` - Behavior regularity (0-100)
- `risk_appetite_score` - Risk-taking tendency (0-100)
- `confidence_score` - Profile confidence (0-100)
- `is_complete` - Completion status

## Detection Thresholds

### Statistical Detection
- **Z-Score Threshold:** 3.0 (3 standard deviations)
- **Severity Mapping:**
  - >= 6.0 std devs: Critical
  - >= 4.5 std devs: High
  - >= 3.5 std devs: Medium
  - < 3.5 std devs: Low

### ML Detection
[Inference] Isolation Forest parameters:
- **Contamination:** 0.05 (5% expected anomalies)
- **Anomaly Threshold:** 0.7 (70% anomaly score)
- **Severity Mapping:**
  - >= 0.9: Critical
  - >= 0.8: High
  - >= 0.7: Medium

### Rule-Based Detection
- High confidence (95%) by design
- Severity determined per rule
- Immediate triggering

## Performance Considerations

### Baseline Building
- **Time:** 2-5 seconds per baseline type
- **Data Requirements:** Minimum 10 samples, ideal 100+
- **Frequency:** Refresh weekly or when `needs_refresh` flag set

### Profile Building
- **Time:** 5-10 seconds per device
- **Data Requirements:** Minimum 20 samples, ideal 500+
- **Frequency:** Refresh weekly

### Real-Time Detection
- **Latency:** < 1 second per telemetry record
- **Throughput:** 100+ devices/second
- **Memory:** ~50MB per 1000 baselines

## Best Practices

1. **Baseline Management**
   - Build initial baselines after 30 days of telemetry collection
   - Refresh baselines monthly
   - Mark for refresh after major system changes

2. **False Positive Handling**
   - Always mark confirmed false positives
   - System learns from feedback
   - Review patterns in false positives monthly

3. **Alert Configuration**
   - Start with high/critical only
   - Tune thresholds based on false positive rate
   - Use batch alerts to reduce email volume

4. **Performance Optimization**
   - Build baselines in background tasks
   - Cache frequently accessed profiles
   - Archive old resolved anomalies

5. **Integration**
   - Process telemetry through detection engine
   - Connect alerting to incident response workflow
   - Export anomalies to SIEM for correlation

## Troubleshooting

### No Anomalies Detected

**Possible Causes:**
- Insufficient historical data
- Baselines not built
- All behavior within normal ranges

**Solutions:**
- Check baseline existence: `GET /api/v1/analytics/baselines`
- Verify telemetry collection is working
- Build baselines manually if needed

### Too Many False Positives

**Possible Causes:**
- Z-score threshold too low
- Insufficient baseline data
- High variance in normal behavior

**Solutions:**
- Increase z_score_threshold to 4.0 or 5.0
- Collect more baseline data (extend learning period)
- Mark false positives to track patterns
- Adjust alert severity filters

### Alerts Not Sending

**Possible Causes:**
- SMTP configuration incorrect
- No recipients configured
- Anomaly severity below threshold

**Solutions:**
- Test SMTP settings manually
- Verify `alert_recipients` configuration
- Check anomaly severity (only medium+ alert)

## Future Enhancements

- **Behavioral Clustering** - Group similar devices for peer comparison
- **Threat Intelligence Integration** - Correlate with known threats
- **Automated Response** - Trigger workflows for specific anomalies
- **Advanced ML Models** - LSTM for time-series, autoencoders for reconstruction
- **Explainable AI** - SHAP values for ML predictions
- **User Behavior Analytics (UBA)** - User-level behavioral profiling
- **Anomaly Trends** - Track anomaly patterns over time

## Support

For issues or questions:
- **GitHub:** https://github.com/adrian207/Mac-Compliance-System
- **Email:** adrian207@gmail.com
- **Documentation:** See `docs/` directory

## License

See LICENSE file in the project root.

