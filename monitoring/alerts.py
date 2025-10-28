"""
Alerting System

Author: Adrian Johnson <adrian207@gmail.com>

Sends alerts via multiple channels (email, Slack, PagerDuty, webhooks).
"""

import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

import httpx

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)


class AlertManager:
    """
    Alert management and distribution.
    
    Sends alerts through configured channels based on severity and rules.
    """
    
    def __init__(self):
        """Initialize alert manager."""
        self.config = get_config()
        self.monitoring_config = self.config._raw_config.get("monitoring", {})
        self.alert_config = self.monitoring_config.get("alerts", {})
    
    def send_alert(
        self,
        alert_name: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an alert through appropriate channels.
        
        Args:
            alert_name: Name of the alert
            severity: Alert severity (low, medium, high, critical)
            message: Alert message
            details: Optional additional details
        
        Returns:
            Dict with send results
        """
        logger.info(
            "alert_triggered",
            alert_name=alert_name,
            severity=severity
        )
        
        # Determine which channels to use
        channels = self._get_channels_for_alert(alert_name, severity)
        
        results = {
            "alert_name": alert_name,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "channels": []
        }
        
        # Send to each channel
        for channel in channels:
            try:
                if channel == "email":
                    success = self._send_email_alert(alert_name, severity, message, details)
                elif channel == "slack":
                    success = self._send_slack_alert(alert_name, severity, message, details)
                elif channel == "pagerduty":
                    success = self._send_pagerduty_alert(alert_name, severity, message, details)
                elif channel == "webhook":
                    success = self._send_webhook_alert(alert_name, severity, message, details)
                else:
                    success = False
                
                results["channels"].append({
                    "channel": channel,
                    "success": success
                })
                
                if success:
                    logger.info(
                        "alert_sent",
                        alert_name=alert_name,
                        channel=channel
                    )
                else:
                    logger.error(
                        "alert_send_failed",
                        alert_name=alert_name,
                        channel=channel
                    )
            
            except Exception as e:
                logger.error(
                    "alert_send_error",
                    alert_name=alert_name,
                    channel=channel,
                    error=str(e)
                )
                results["channels"].append({
                    "channel": channel,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def _get_channels_for_alert(
        self,
        alert_name: str,
        severity: str
    ) -> List[str]:
        """
        Determine which channels to use for an alert.
        
        Args:
            alert_name: Name of the alert
            severity: Alert severity
        
        Returns:
            List of channel names
        """
        # Check alert rules
        alert_rules = self.monitoring_config.get("alert_rules", [])
        
        for rule in alert_rules:
            if rule.get("name") == alert_name:
                return rule.get("channels", [])
        
        # Default channels based on severity
        if severity in ["critical", "high"]:
            return ["email"]
        elif severity == "medium":
            return ["email"]
        else:
            return []
    
    def _send_email_alert(
        self,
        alert_name: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]]
    ) -> bool:
        """Send alert via email."""
        email_config = self.alert_config.get("email", {})
        
        if not email_config.get("enabled", False):
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = email_config["from_address"]
            msg["To"] = ", ".join(email_config["to_addresses"])
            msg["Subject"] = f"[{severity.upper()}] {alert_name}"
            
            # Build email body
            body = f"""
Security Alert

Alert: {alert_name}
Severity: {severity.upper()}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

{message}
"""
            
            if details:
                body += "\n\nDetails:\n"
                for key, value in details.items():
                    body += f"  {key}: {value}\n"
            
            body += "\n\n---\nMac OS Zero Trust Security Platform\n"
            
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(email_config["smtp_host"], email_config["smtp_port"]) as server:
                server.starttls()
                server.login(email_config["smtp_username"], email_config["smtp_password"])
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            logger.error("email_alert_failed", error=str(e))
            return False
    
    def _send_slack_alert(
        self,
        alert_name: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]]
    ) -> bool:
        """Send alert via Slack."""
        slack_config = self.alert_config.get("slack", {})
        
        if not slack_config.get("enabled", False):
            return False
        
        try:
            # Determine emoji based on severity
            emoji_map = {
                "critical": ":rotating_light:",
                "high": ":warning:",
                "medium": ":exclamation:",
                "low": ":information_source:"
            }
            emoji = emoji_map.get(severity, ":bell:")
            
            # Build Slack message
            payload = {
                "channel": slack_config.get("channel", "#security-alerts"),
                "username": "Zero Trust Security",
                "icon_emoji": emoji,
                "text": f"*{severity.upper()}:* {alert_name}",
                "attachments": [
                    {
                        "color": self._get_severity_color(severity),
                        "fields": [
                            {
                                "title": "Alert",
                                "value": alert_name,
                                "short": True
                            },
                            {
                                "title": "Severity",
                                "value": severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": message,
                                "short": False
                            }
                        ],
                        "footer": "Mac OS Zero Trust Security Platform",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            if details:
                for key, value in details.items():
                    payload["attachments"][0]["fields"].append({
                        "title": key,
                        "value": str(value),
                        "short": True
                    })
            
            # Send to Slack
            response = httpx.post(
                slack_config["webhook_url"],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            return True
        
        except Exception as e:
            logger.error("slack_alert_failed", error=str(e))
            return False
    
    def _send_pagerduty_alert(
        self,
        alert_name: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]]
    ) -> bool:
        """Send alert via PagerDuty."""
        pagerduty_config = self.alert_config.get("pagerduty", {})
        
        if not pagerduty_config.get("enabled", False):
            return False
        
        try:
            # Build PagerDuty event
            payload = {
                "routing_key": pagerduty_config["integration_key"],
                "event_action": "trigger",
                "payload": {
                    "summary": f"{alert_name}: {message}",
                    "severity": severity,
                    "source": "zerotrust-platform",
                    "custom_details": details or {}
                }
            }
            
            # Send to PagerDuty
            response = httpx.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            return True
        
        except Exception as e:
            logger.error("pagerduty_alert_failed", error=str(e))
            return False
    
    def _send_webhook_alert(
        self,
        alert_name: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]]
    ) -> bool:
        """Send alert via webhook."""
        webhook_config = self.alert_config.get("webhook", {})
        
        if not webhook_config.get("enabled", False):
            return False
        
        try:
            # Build webhook payload
            payload = {
                "alert_name": alert_name,
                "severity": severity,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Get custom headers
            headers = webhook_config.get("headers", {})
            
            # Send to webhook URL
            response = httpx.post(
                webhook_config["url"],
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            return True
        
        except Exception as e:
            logger.error("webhook_alert_failed", error=str(e))
            return False
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color code for severity level."""
        color_map = {
            "critical": "#FF0000",
            "high": "#FF6600",
            "medium": "#FFCC00",
            "low": "#00CC00"
        }
        return color_map.get(severity, "#808080")


def send_alert(
    alert_name: str,
    severity: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send an alert.
    
    Args:
        alert_name: Alert name
        severity: Alert severity
        message: Alert message
        details: Optional details
    
    Returns:
        Alert send results
    """
    alert_manager = AlertManager()
    return alert_manager.send_alert(alert_name, severity, message, details)

