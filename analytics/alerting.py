"""
Anomaly Alerting System

Author: Adrian Johnson <adrian207@gmail.com>

Sends alerts and notifications for detected anomalies.
"""

from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from analytics.models import AnomalyDetection, AnomalySeverity
from reporting.email_delivery import EmailDelivery


class AnomalyAlerter:
    """
    Anomaly alerting system.
    
    Sends notifications via email, webhooks, or other channels when
    anomalies are detected.
    """
    
    def __init__(
        self,
        db: Session,
        email_config: Optional[Dict[str, Any]] = None,
        alert_recipients: Optional[List[str]] = None
    ):
        """
        Initialize anomaly alerter.
        
        Args:
            db: Database session
            email_config: Email configuration dictionary
            alert_recipients: Default recipients for alerts
        """
        self.db = db
        self.alert_recipients = alert_recipients or []
        
        # Initialize email delivery
        if email_config:
            self.email_delivery = EmailDelivery(**email_config)
        else:
            self.email_delivery = None
    
    def alert_anomaly(
        self,
        anomaly: AnomalyDetection,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        Send alert for anomaly.
        
        Args:
            anomaly: Anomaly to alert on
            recipients: Email recipients (uses default if not provided)
        
        Returns:
            True if alert sent successfully
        """
        recipients = recipients or self.alert_recipients
        
        if not recipients:
            print(f"[WARN] No alert recipients configured for anomaly {anomaly.anomaly_id}")
            return False
        
        # Check if alert should be sent based on severity
        if not self._should_alert(anomaly):
            return False
        
        # Send via email
        if self.email_delivery:
            success = self._send_email_alert(anomaly, recipients)
            
            if success:
                # Update anomaly record
                anomaly.alert_sent = True
                anomaly.alert_sent_at = datetime.now(UTC)
                anomaly.alert_recipients = recipients
                self.db.commit()
                
                return True
        
        return False
    
    def alert_multiple(
        self,
        anomalies: List[AnomalyDetection],
        recipients: Optional[List[str]] = None
    ) -> int:
        """
        Send alerts for multiple anomalies.
        
        Args:
            anomalies: List of anomalies
            recipients: Email recipients
        
        Returns:
            Number of alerts sent successfully
        """
        sent_count = 0
        
        # Group by severity for batch alerting
        by_severity = self._group_by_severity(anomalies)
        
        # Send alerts for each severity group
        for severity, group in by_severity.items():
            if self._send_batch_alert(group, severity, recipients):
                sent_count += len(group)
                
                # Update anomaly records
                for anomaly in group:
                    anomaly.alert_sent = True
                    anomaly.alert_sent_at = datetime.now(UTC)
                    anomaly.alert_recipients = recipients or self.alert_recipients
                
                self.db.commit()
        
        return sent_count
    
    def _should_alert(self, anomaly: AnomalyDetection) -> bool:
        """
        Determine if anomaly should trigger alert.
        
        Args:
            anomaly: Anomaly to check
        
        Returns:
            True if should alert
        """
        # Don't alert on already sent, false positives, or resolved
        if anomaly.alert_sent or anomaly.is_false_positive or anomaly.is_resolved:
            return False
        
        # Alert on medium and higher severity
        alert_severities = [
            AnomalySeverity.MEDIUM.value,
            AnomalySeverity.HIGH.value,
            AnomalySeverity.CRITICAL.value
        ]
        
        return anomaly.anomaly_severity in alert_severities
    
    def _send_email_alert(
        self,
        anomaly: AnomalyDetection,
        recipients: List[str]
    ) -> bool:
        """
        Send email alert for single anomaly.
        
        Args:
            anomaly: Anomaly to alert on
            recipients: Email recipients
        
        Returns:
            True if sent successfully
        """
        if not self.email_delivery:
            return False
        
        subject = self._build_subject(anomaly)
        body = self._build_email_body(anomaly)
        html_body = self._build_html_email(anomaly)
        
        success = self.email_delivery.send_report(
            recipients=recipients,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        if success:
            print(f"[INFO] Alert sent for anomaly {anomaly.anomaly_id}")
        else:
            print(f"[ERROR] Failed to send alert for anomaly {anomaly.anomaly_id}")
        
        return success
    
    def _send_batch_alert(
        self,
        anomalies: List[AnomalyDetection],
        severity: str,
        recipients: Optional[List[str]]
    ) -> bool:
        """
        Send batch alert for multiple anomalies.
        
        Args:
            anomalies: List of anomalies
            severity: Severity level
            recipients: Email recipients
        
        Returns:
            True if sent successfully
        """
        if not self.email_delivery:
            return False
        
        recipients = recipients or self.alert_recipients
        
        subject = f"[{severity.upper()}] {len(anomalies)} Anomalies Detected"
        body = self._build_batch_email_body(anomalies, severity)
        
        success = self.email_delivery.send_report(
            recipients=recipients,
            subject=subject,
            body=body
        )
        
        if success:
            print(f"[INFO] Batch alert sent for {len(anomalies)} anomalies ({severity})")
        else:
            print(f"[ERROR] Failed to send batch alert")
        
        return success
    
    def _build_subject(self, anomaly: AnomalyDetection) -> str:
        """Build email subject line."""
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "ℹ️"
        }
        
        emoji = severity_emoji.get(anomaly.anomaly_severity, "⚠️")
        
        return f"{emoji} [{anomaly.anomaly_severity.upper()}] {anomaly.title}"
    
    def _build_email_body(self, anomaly: AnomalyDetection) -> str:
        """Build plain text email body."""
        body = f"""
ANOMALY DETECTED

Severity: {anomaly.anomaly_severity.upper()}
Device: {anomaly.device_id}
Type: {anomaly.anomaly_type}

Title: {anomaly.title}

Description:
{anomaly.description}

Detection Details:
- Method: {anomaly.detection_method}
- Detector: {anomaly.detector_name}
- Anomaly Score: {anomaly.anomaly_score:.1f}
- Confidence: {anomaly.confidence:.2f}
- Detected At: {anomaly.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

"""
        
        if anomaly.feature_name:
            body += f"Feature: {anomaly.feature_name}\n"
        
        if anomaly.observed_value:
            body += f"Observed Value: {anomaly.observed_value}\n"
        
        if anomaly.expected_value:
            body += f"Expected Value: {anomaly.expected_value}\n"
        
        if anomaly.deviation:
            body += f"Deviation: {anomaly.deviation:.2f} standard deviations\n"
        
        if anomaly.recommendations:
            body += "\nRecommended Actions:\n"
            for i, rec in enumerate(anomaly.recommendations, 1):
                body += f"{i}. {rec}\n"
        
        body += f"""
---
View in Platform: https://your-platform.com/anomalies/{anomaly.anomaly_id}

This is an automated alert from the ZeroTrust Platform Behavioral Analytics system.
"""
        
        return body
    
    def _build_html_email(self, anomaly: AnomalyDetection) -> str:
        """Build HTML email body."""
        severity_colors = {
            "critical": "#DC2626",
            "high": "#EA580C",
            "medium": "#F59E0B",
            "low": "#10B981",
            "info": "#3B82F6"
        }
        
        color = severity_colors.get(anomaly.anomaly_severity, "#6B7280")
        
        html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 20px; }}
        .detail {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 3px solid {color}; }}
        .label {{ font-weight: bold; }}
        .recommendations {{ background-color: #e7f3ff; padding: 15px; border-left: 4px solid #3B82F6; margin: 15px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
        .button {{ background-color: {color}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🚨 Anomaly Detected</h2>
            <p><strong>Severity:</strong> {anomaly.anomaly_severity.upper()}</p>
        </div>
        
        <div class="content">
            <h3>{anomaly.title}</h3>
            <p>{anomaly.description}</p>
            
            <div class="detail">
                <p><span class="label">Device:</span> {anomaly.device_id}</p>
                <p><span class="label">Type:</span> {anomaly.anomaly_type}</p>
                <p><span class="label">Detection Method:</span> {anomaly.detection_method}</p>
                <p><span class="label">Anomaly Score:</span> {anomaly.anomaly_score:.1f}</p>
                <p><span class="label">Detected:</span> {anomaly.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
            
            {f'''
            <div class="recommendations">
                <h4>Recommended Actions:</h4>
                <ul>
                    {"".join(f"<li>{rec}</li>" for rec in anomaly.recommendations)}
                </ul>
            </div>
            ''' if anomaly.recommendations else ''}
            
            <p style="text-align: center; margin-top: 20px;">
                <a href="https://your-platform.com/anomalies/{anomaly.anomaly_id}" class="button">
                    View Details
                </a>
            </p>
        </div>
        
        <div class="footer">
            <p>This is an automated alert from the ZeroTrust Platform</p>
            <p>Behavioral Analytics & Anomaly Detection System</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _build_batch_email_body(
        self,
        anomalies: List[AnomalyDetection],
        severity: str
    ) -> str:
        """Build batch alert email body."""
        body = f"""
MULTIPLE ANOMALIES DETECTED

Severity Level: {severity.upper()}
Count: {len(anomalies)}
Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}

Summary:
"""
        
        for i, anomaly in enumerate(anomalies, 1):
            body += f"""
{i}. Device: {anomaly.device_id}
   Type: {anomaly.anomaly_type}
   Title: {anomaly.title}
   Score: {anomaly.anomaly_score:.1f}
   
"""
        
        body += """
---
View all anomalies: https://your-platform.com/anomalies

This is an automated alert from the ZeroTrust Platform.
"""
        
        return body
    
    def _group_by_severity(
        self,
        anomalies: List[AnomalyDetection]
    ) -> Dict[str, List[AnomalyDetection]]:
        """Group anomalies by severity."""
        groups = {}
        
        for anomaly in anomalies:
            severity = anomaly.anomaly_severity
            
            if severity not in groups:
                groups[severity] = []
            
            groups[severity].append(anomaly)
        
        return groups

