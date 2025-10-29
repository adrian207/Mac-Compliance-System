# Reporting and Analytics Module

**Author:** Adrian Johnson <adrian207@gmail.com>  
**Version:** 0.9.4

## Overview

The Reporting and Analytics module provides comprehensive reporting capabilities for the ZeroTrust platform. Generate executive dashboards, compliance reports, device inventories, security posture analyses, and risk trend reports with automated scheduling and email delivery.

## Key Features

- **5 Report Types** - Executive dashboard, compliance, inventory, security posture, and risk trends
- **Multiple Export Formats** - PDF, CSV, JSON, HTML, Excel
- **Automated Scheduling** - Daily, weekly, monthly, quarterly reports
- **Email Delivery** - Automatic distribution with attachments
- **REST API** - Programmatic report generation and management
- **History Tracking** - Risk score and compliance history over time

## Report Types

### 1. Executive Dashboard

High-level KPIs and metrics for leadership and stakeholders.

**Includes:**
- Total device count and active/inactive status
- Critical risk device count
- Security health score (0-100)
- Risk distribution (critical/high/medium/low)
- Compliance rate
- Top security risks
- Trend comparisons with previous periods
- Actionable recommendations

**Use Cases:**
- Weekly executive briefings
- Board presentations
- Quarterly security reviews
- Management reporting

### 2. Compliance Report

Detailed compliance status and policy adherence.

**Includes:**
- Overall compliance rate
- Policy-level compliance details
- Compliance violations by severity
- Remediation tracking
- Compliance trends over time
- Per-device compliance status
- Critical failure analysis

**Use Cases:**
- Audit preparation
- Regulatory compliance reporting (SOC2, ISO 27001)
- Internal policy enforcement tracking
- Compliance trend analysis

### 3. Device Inventory

Comprehensive device fleet inventory.

**Includes:**
- Complete device listing
- Hardware specifications
- OS version distribution
- Software inventory (optional)
- Network configuration (optional)
- Security status per device

**Use Cases:**
- Asset management
- License compliance
- Hardware refresh planning
- Security control deployment tracking

### 4. Security Posture Report

Security control effectiveness and vulnerability analysis.

**Includes:**
- Average security posture score
- Security control status (FileVault, SIP, Firewall, etc.)
- Vulnerability analysis
- Control effectiveness metrics
- Security gaps identification
- Improvement recommendations

**Use Cases:**
- Security program assessment
- Control effectiveness measurement
- Gap analysis
- Security roadmap planning

### 5. Risk Trend Report

Historical risk score analysis with trend identification.

**Includes:**
- Time-series risk score history
- Risk level change events
- Risk factor trend analysis
- Device risk distribution
- Trend direction and percentages
- Predictive insights

**Use Cases:**
- Risk management tracking
- Security improvement validation
- Trend identification
- Executive reporting

## Architecture

```
reporting/
├── models.py                      # Data models
├── api.py                         # REST API endpoints
├── scheduler.py                   # Automated scheduling
├── email_delivery.py              # Email system
├── generators/                    # Report generators
│   ├── base.py                   # Base generator class
│   ├── executive_dashboard.py    # Executive dashboard
│   ├── compliance_report.py      # Compliance reports
│   ├── device_inventory.py       # Device inventory
│   ├── security_posture.py       # Security posture
│   └── risk_trend.py             # Risk trends
├── exporters/                     # Format exporters
│   ├── pdf_exporter.py           # PDF export
│   └── csv_exporter.py           # CSV export
└── templates/                     # Email templates
```

## Usage

### Generate Report via API

```bash
POST /api/v1/reports/generate
```

```json
{
  "report_type": "executive_dashboard",
  "report_format": "pdf",
  "parameters": {
    "period": "monthly",
    "compare_previous": true
  },
  "email_recipients": ["executive@example.com"]
}
```

### Schedule Recurring Report

```bash
POST /api/v1/reports/schedule
```

```json
{
  "name": "Weekly Executive Dashboard",
  "report_type": "executive_dashboard",
  "report_format": "pdf",
  "frequency": "weekly",
  "recipients": ["ciso@example.com", "ceo@example.com"],
  "parameters": {
    "period": "weekly",
    "compare_previous": true
  },
  "enabled": true
}
```

### Python API Usage

```python
from reporting.generators import ExecutiveDashboardGenerator
from reporting.exporters import PDFExporter

# Initialize generator
generator = ExecutiveDashboardGenerator(db_session)

# Generate report
report_data = generator.generate({
    "period": "monthly",
    "compare_previous": True
})

# Export to PDF
exporter = PDFExporter()
file_path = exporter.export(
    report_data,
    "Executive Dashboard - January 2025"
)

# Save to database
report = generator.save_report(
    report_data,
    parameters={"period": "monthly"},
    file_path=file_path,
    generated_by="admin@example.com"
)

print(f"Report saved: {report.report_id}")
```

## Report Parameters

### Executive Dashboard

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `"monthly"` | Time period: daily, weekly, monthly, quarterly |
| `compare_previous` | boolean | `true` | Include comparison with previous period |

### Compliance Report

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `framework` | string | `"CIS"` | Compliance framework: CIS, NIST, ISO27001 |
| `include_devices` | boolean | `true` | Include per-device compliance details |
| `start_date` | string | 30 days ago | Start date for historical data (ISO 8601) |
| `end_date` | string | now | End date for historical data (ISO 8601) |

### Device Inventory

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_software` | boolean | `false` | Include software inventory |
| `include_network` | boolean | `false` | Include network configuration |
| `active_only` | boolean | `true` | Only include active devices (7 days) |

### Security Posture

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | 30 days ago | Analysis start date (ISO 8601) |
| `end_date` | string | now | Analysis end date (ISO 8601) |

### Risk Trend

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | 90 days ago | Trend start date (ISO 8601) |
| `end_date` | string | now | Trend end date (ISO 8601) |
| `device_id` | string | `null` | Optional: analyze specific device |

## Scheduling

### Frequencies

- **Daily** - Generated every 24 hours
- **Weekly** - Generated every 7 days
- **Monthly** - Generated every 30 days
- **Quarterly** - Generated every 90 days
- **On-Demand** - Manual generation only

### Scheduler Service

Run the scheduler as a background service:

```python
from reporting.scheduler import ReportScheduler

scheduler = ReportScheduler(
    db_session,
    email_config={
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "reports@example.com",
        "smtp_password": "password",
        "use_tls": True
    }
)

scheduler.start()
```

## Email Delivery

### Configuration

```python
from reporting.email_delivery import EmailDelivery

email = EmailDelivery(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="reports@example.com",
    smtp_password="password",
    use_tls=True,
    from_address="zerotrust@example.com"
)
```

### Send Report

```python
success = email.send_report(
    recipients=["user@example.com"],
    subject="Weekly Security Dashboard",
    body="Your weekly security dashboard is attached.",
    attachments=["/path/to/report.pdf"]
)
```

### Email Templates

Built-in templates for:
- Executive dashboard reports
- Compliance reports
- Scheduled reports

Custom templates can be provided per scheduled report.

## API Endpoints

### Report Generation

- `POST /api/v1/reports/generate` - Generate report on-demand
- `GET /api/v1/reports/list` - List generated reports
- `GET /api/v1/reports/{report_id}` - Get report details
- `DELETE /api/v1/reports/{report_id}` - Delete report

### Scheduling

- `POST /api/v1/reports/schedule` - Create scheduled report
- `GET /api/v1/reports/schedule/list` - List scheduled reports
- `PUT /api/v1/reports/schedule/{schedule_id}` - Update schedule
- `DELETE /api/v1/reports/schedule/{schedule_id}` - Delete schedule

## Data Models

### Report

Stores generated report metadata:
- `report_id` - Unique identifier
- `report_type` - Type of report
- `report_format` - Export format
- `title` - Report title
- `generated_at` - Generation timestamp
- `file_path` - Path to exported file
- `data_snapshot` - Key metrics snapshot
- `delivered` - Email delivery status

### ScheduledReport

Configuration for recurring reports:
- `schedule_id` - Unique identifier
- `name` - Schedule name
- `report_type` - Type of report
- `frequency` - Scheduling frequency
- `recipients` - Email recipients
- `next_run_at` - Next scheduled run
- `enabled` - Active status

### RiskScoreHistory

Historical risk scores for trend analysis:
- `device_id` - Device identifier
- `total_risk_score` - Overall risk score
- `risk_level` - Risk classification
- `risk_factors` - Contributing factors
- `score_delta` - Change from previous
- `recorded_at` - Timestamp

### ComplianceHistory

Historical compliance status:
- `device_id` - Device identifier
- `is_compliant` - Compliance status
- `compliance_score` - Score (0-100)
- `policies_passed` - Passed policy count
- `policies_failed` - Failed policy count
- `critical_failures` - Critical violations
- `recorded_at` - Timestamp

## Export Formats

### PDF

Professional PDF reports with:
- Headers and footers
- Tables and charts
- Executive summary
- Detailed data sections

[Inference] Uses ReportLab library for PDF generation.

### CSV

Tabular data export for:
- Spreadsheet analysis
- Data import to other systems
- Custom visualizations

### JSON

Structured data for:
- API consumption
- Custom processing
- Integration with other systems

## Best Practices

1. **Schedule Reports Appropriately**
   - Executive dashboards: Weekly or monthly
   - Compliance reports: Monthly or quarterly
   - Risk trends: Monthly
   - Device inventory: As needed

2. **Use Parameters Effectively**
   - Set appropriate date ranges for trend analysis
   - Include device details only when necessary
   - Compare previous periods for context

3. **Email Distribution**
   - Keep recipient lists focused
   - Use descriptive subject lines
   - Provide context in email body

4. **Performance Considerations**
   - Large device fleets may require longer generation times
   - Schedule reports during off-peak hours
   - Use appropriate date ranges to limit data volume

5. **Data Retention**
   - Regularly archive or delete old reports
   - Maintain history data for trend analysis
   - Balance storage with analytical needs

## Troubleshooting

### Report Generation Fails

**Check:**
- Database connectivity
- Sufficient historical data
- Valid parameters

### Email Delivery Fails

**Check:**
- SMTP configuration
- Network connectivity
- Recipient email addresses
- Attachment size limits

### Scheduled Reports Not Running

**Check:**
- Scheduler service is running
- Schedule is enabled
- `next_run_at` is in the past

## Future Enhancements

- **Additional Report Types** - Incident reports, user activity
- **Interactive Dashboards** - Real-time web dashboards
- **Custom Report Builder** - User-defined reports
- **Advanced Analytics** - ML-based insights and predictions
- **Data Visualization** - Charts and graphs in reports
- **Report Sharing** - Shareable links for reports
- **Role-Based Access** - Permission-based report access

## Support

For issues or questions:
- **GitHub:** https://github.com/adrian207/Mac-Compliance-System
- **Email:** adrian207@gmail.com
- **Documentation:** See `docs/` directory

## License

See LICENSE file in the project root.

