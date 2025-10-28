# Grafana Dashboards for Mac OS Zero Trust Endpoint Security Platform

**Author:** Adrian Johnson <adrian207@gmail.com>

This directory contains pre-built Grafana dashboards for comprehensive monitoring of the Mac OS Zero Trust Endpoint Security Platform.

## 📊 Available Dashboards

### 1. Device Risk Overview (`device-risk-overview.json`)
**Purpose:** Monitor and analyze device risk scores, trends, and risk factor distribution.

**Key Metrics:**
- Average Device Risk Score (gauge)
- Device Risk Score Trends (time series)
- Risk Level Distribution (pie chart)
- Top 10 High-Risk Devices (table)
- Risk Factors by Category (stacked bar chart)
- Total Devices Monitored
- Risk Assessments per Minute
- Average Assessment Duration

**Use Cases:**
- Identify devices requiring immediate attention
- Track risk score trends over time
- Analyze common risk factors across your fleet
- Monitor risk assessment performance

**Refresh Rate:** 30 seconds

---

### 2. Compliance Monitoring (`compliance-monitoring.json`)
**Purpose:** Track device compliance status, policy violations, and compliance trends.

**Key Metrics:**
- Overall Compliance Score (gauge with thresholds)
- Compliance Score Trends (time series by device)
- Compliance Violations by Device (table)
- Violations by Severity (time series)
- Violations by Policy Category (pie chart)
- Violation Rate by Category (time series)
- Fully Compliant Devices
- Critical Violations
- Compliance Checks per Minute
- Average Check Duration

**Use Cases:**
- Monitor overall compliance posture
- Identify policy violations requiring remediation
- Track compliance improvement over time
- Analyze violation patterns by category

**Refresh Rate:** 30 seconds

---

### 3. System Health & Performance (`system-health-performance.json`)
**Purpose:** Monitor platform health, API performance, database operations, and system resources.

**Key Metrics:**
- API Request Rate (by method and endpoint)
- API Response Time (p50, p95, p99 percentiles)
- HTTP Status Codes (2xx, 4xx, 5xx)
- API Success Rate (gauge)
- Database Query Rate (by operation)
- Database Query Duration (p95)
- Database Connection Pool Status
- Integration API Call Rate
- Total Requests/sec
- Server Errors/min
- System Uptime
- Memory Usage

**Use Cases:**
- Monitor API health and performance
- Detect performance degradation
- Track database performance
- Monitor system resource utilization
- Identify integration issues

**Refresh Rate:** 10 seconds

---

### 4. Security Events & Threats (`security-events-threats.json`)
**Purpose:** Track security events, threat indicators, and alerts in real-time.

**Key Metrics:**
- Security Events per Minute (by severity)
- Events by Severity (pie chart - 24h)
- Events by Type (pie chart - 24h)
- Top 10 Devices by Event Count
- Recent Security Events (table)
- Threat Indicators Detected per Minute
- Alerts Triggered per Minute
- Total Events (24h)
- Critical/High Events (24h)
- Threat Indicators (24h)
- Alerts Triggered (24h)

**Use Cases:**
- Monitor security events in real-time
- Identify high-risk devices by event volume
- Track threat indicator detection
- Analyze alert patterns
- Investigate security incidents

**Refresh Rate:** 30 seconds

---

## 🚀 Quick Start

### Prerequisites

1. **Grafana** (version 9.0 or higher)
2. **Prometheus** data source configured in Grafana
3. **Mac OS Zero Trust Platform** deployed and running
4. Platform metrics exposed on Prometheus endpoint (default: `http://localhost:8000/metrics`)

### Installation Steps

#### Step 1: Configure Prometheus Data Source

1. Log in to your Grafana instance
2. Navigate to **Configuration** → **Data Sources**
3. Click **Add data source**
4. Select **Prometheus**
5. Configure the connection:
   - **Name:** `Prometheus` (or your preferred name)
   - **URL:** `http://localhost:9090` (or your Prometheus server URL)
   - **Access:** Server (default)
6. Click **Save & Test** to verify the connection

#### Step 2: Import Dashboards

**Option A: Manual Import (Recommended)**

1. In Grafana, navigate to **Dashboards** → **Import**
2. Click **Upload JSON file**
3. Select one of the dashboard JSON files from `grafana/dashboards/`:
   - `device-risk-overview.json`
   - `compliance-monitoring.json`
   - `system-health-performance.json`
   - `security-events-threats.json`
4. On the import screen:
   - Select your Prometheus data source from the dropdown
   - Optionally modify the dashboard name or UID
   - Click **Import**
5. Repeat for all dashboards

**Option B: Import via API**

```bash
# Set your Grafana details
GRAFANA_URL="http://localhost:3000"
GRAFANA_API_KEY="your-api-key"

# Import all dashboards
for dashboard in grafana/dashboards/*.json; do
    curl -X POST \
        -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
        -H "Content-Type: application/json" \
        -d @"${dashboard}" \
        "${GRAFANA_URL}/api/dashboards/db"
done
```

**Option C: Using Provisioning**

1. Copy the dashboard files to your Grafana provisioning directory:
   ```bash
   cp grafana/dashboards/*.json /etc/grafana/provisioning/dashboards/
   ```

2. Create a provisioning configuration file `/etc/grafana/provisioning/dashboards/mac-hardening.yaml`:
   ```yaml
   apiVersion: 1
   
   providers:
     - name: 'Mac Hardening'
       orgId: 1
       folder: 'Mac OS Zero Trust'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 10
       allowUiUpdates: true
       options:
         path: /etc/grafana/provisioning/dashboards
         foldersFromFilesStructure: false
   ```

3. Restart Grafana:
   ```bash
   sudo systemctl restart grafana-server
   ```

#### Step 3: Configure Data Source Variable

After importing, each dashboard will have a data source variable. Ensure it's set to your Prometheus data source:

1. Open the dashboard
2. Click the **Settings** gear icon (top right)
3. Go to **Variables**
4. Edit the `DS_PROMETHEUS` variable
5. Ensure it's configured correctly
6. Click **Update** and **Save dashboard**

---

## 📈 Dashboard Usage Guide

### Navigation

All dashboards are organized with:
- **Time range selector** (top right) - Adjust the time window
- **Refresh controls** (top right) - Auto-refresh settings
- **Dashboard tags** - Filter dashboards by tag (security, compliance, performance, etc.)

### Customization

You can customize dashboards to fit your needs:

1. **Add Panels:** Click **Add panel** → **Add a new panel**
2. **Edit Panels:** Click panel title → **Edit**
3. **Duplicate Panels:** Click panel title → **More** → **Duplicate**
4. **Organize Layout:** Drag and drop panels to reposition
5. **Set Alerts:** Click panel title → **More** → **New alert rule**

### Creating Alerts

[Inference] To set up alerting (requires Grafana 8.0+):

1. Navigate to **Alerting** → **Alert rules**
2. Click **New alert rule**
3. Select a query from any dashboard panel
4. Define alert conditions (e.g., risk score > 70)
5. Configure notification channels (email, Slack, PagerDuty, etc.)
6. Set evaluation frequency
7. Save the alert rule

---

## 🔍 Metric Reference

### Platform Metrics Exposed

The platform exposes the following Prometheus metrics:

#### Risk Assessment Metrics
```
device_risk_score{device_id, risk_level} - Current risk score per device (0-100)
risk_assessment_total - Total number of risk assessments performed
risk_assessment_duration_ms - Risk assessment execution time
risk_factor_count{category} - Number of risk factors by category
```

#### Compliance Metrics
```
compliance_score{device_id} - Compliance score per device (0.0-1.0)
compliance_violations_count{device_id, policy_category, severity} - Violation count
compliance_check_total - Total compliance checks performed
compliance_check_duration_ms - Compliance check execution time
```

#### API Metrics
```
http_requests_total{method, endpoint, status_code} - Total HTTP requests
http_request_duration_seconds_bucket{endpoint, le} - Request duration histogram
```

#### Database Metrics
```
db_query_total{operation} - Total database queries
db_query_duration_seconds_bucket{operation, le} - Query duration histogram
db_connection_pool_active - Active database connections
db_connection_pool_idle - Idle database connections
db_connection_pool_size - Total connection pool size
```

#### Security Event Metrics
```
security_event_total{event_type, severity, device_id} - Security events
threat_indicator_detected_total{indicator_type} - Threat indicators detected
alert_triggered_total{alert_type, severity} - Alerts triggered
```

#### Integration Metrics
```
integration_api_call_total{integration} - Integration API calls
```

#### System Metrics
```
process_start_time_seconds - Process start timestamp
process_resident_memory_bytes - Memory usage
```

---

## 🎨 Dashboard Themes

The dashboards are designed with a **dark theme** by default. To change:

1. Open the dashboard
2. Click **Settings** gear icon
3. Go to **General** → **Style**
4. Select **Light** or **Dark**
5. Save the dashboard

---

## 🔧 Troubleshooting

### Dashboard shows "No data"

**Possible causes:**
1. Prometheus data source not configured correctly
2. Platform not exposing metrics
3. Time range doesn't include available data
4. Firewall blocking Prometheus scraping

**Solutions:**
- Verify Prometheus can reach the platform: `curl http://localhost:8000/metrics`
- Check Prometheus targets: Navigate to Prometheus UI → Status → Targets
- Adjust the time range in Grafana
- Verify the platform is running: `docker-compose ps` or `systemctl status mac-hardening`

### Panels show errors or warnings

**Common issues:**
- **"Query returned no data"** - No metrics available for the selected time range
- **"Prometheus query error"** - Check query syntax in panel edit mode
- **"Template variable not found"** - Ensure `DS_PROMETHEUS` variable is configured

### Dashboard performance is slow

**Optimization tips:**
- Reduce the time range (e.g., from 24h to 6h)
- Increase the refresh interval (e.g., from 10s to 30s)
- Use downsampling for long time ranges
- Optimize Prometheus queries (add rate windows, use recording rules)

### Metrics are missing or incomplete

**Checklist:**
- Verify the platform is generating metrics: Check `http://localhost:8000/metrics`
- Ensure Prometheus is scraping the platform target
- Check Prometheus retention settings (default: 15 days)
- Verify metric names match the dashboard queries

---

## 📚 Additional Resources

### Grafana Documentation
- [Official Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/best-practices-for-creating-dashboards/)
- [Prometheus Data Source](https://grafana.com/docs/grafana/latest/datasources/prometheus/)

### Platform Documentation
- [Main README](../README.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Operations Guide](../docs/OPERATIONS.md)
- [Testing Guide](../TESTING.md)

---

## 🤝 Contributing

To contribute new dashboards or improvements:

1. Create your dashboard in Grafana
2. Export it as JSON (**Settings** → **JSON Model** → **Copy to clipboard**)
3. Save the JSON to `grafana/dashboards/`
4. Update this README with dashboard documentation
5. Test the import process
6. Submit a pull request

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-28 | Initial release with 4 comprehensive dashboards |

---

## 📞 Support

For questions or issues with the dashboards:

- **GitHub Issues:** [Mac-Compliance-System Issues](https://github.com/adrian207/Mac-Compliance-System/issues)
- **Email:** adrian207@gmail.com
- **Documentation:** See [Main README](../README.md)

---

**Note:** These dashboards are designed for the v0.9.0 Beta release. As the platform evolves, dashboard metrics and queries may be updated to reflect new features and capabilities.

