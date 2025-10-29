"""
Rule-Based Anomaly Detector

Author: Adrian Johnson <adrian207@gmail.com>

Detects known bad patterns and policy violations using predefined rules.
"""

from datetime import datetime, UTC
from typing import Dict, List, Any
import uuid

from sqlalchemy.orm import Session

from analytics.models import AnomalyDetection, AnomalySeverity, AnomalyType
from telemetry.models import DeviceTelemetry


class RuleBasedDetector:
    """
    Rule-based anomaly detection.
    
    Detects known bad patterns, security violations, and policy breaches
    using predefined rules.
    """
    
    def __init__(self, db: Session):
        """
        Initialize rule-based detector.
        
        Args:
            db: Database session
        """
        self.db = db
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load detection rules.
        
        Returns:
            Dictionary of rule categories and their rules
        """
        return {
            "security": [
                {
                    "name": "critical_security_controls_disabled",
                    "description": "Multiple critical security controls disabled",
                    "check": self._check_security_controls,
                    "severity": AnomalySeverity.CRITICAL,
                    "type": AnomalyType.SECURITY_EVENT
                },
                {
                    "name": "excessive_failed_authentications",
                    "description": "Excessive failed authentication attempts",
                    "check": self._check_failed_auth,
                    "severity": AnomalySeverity.HIGH,
                    "type": AnomalyType.AUTHENTICATION
                }
            ],
            "network": [
                {
                    "name": "suspicious_network_activity",
                    "description": "Suspicious network connection patterns",
                    "check": self._check_network_suspicious,
                    "severity": AnomalySeverity.MEDIUM,
                    "type": AnomalyType.NETWORK
                }
            ],
            "process": [
                {
                    "name": "known_malicious_process",
                    "description": "Known malicious process detected",
                    "check": self._check_malicious_process,
                    "severity": AnomalySeverity.CRITICAL,
                    "type": AnomalyType.PROCESS
                }
            ],
            "system": [
                {
                    "name": "critical_system_changes",
                    "description": "Critical system configuration changes",
                    "check": self._check_system_changes,
                    "severity": AnomalySeverity.HIGH,
                    "type": AnomalyType.SYSTEM_CONFIG
                }
            ]
        }
    
    def detect_anomalies(
        self,
        device_id: str,
        telemetry: DeviceTelemetry
    ) -> List[AnomalyDetection]:
        """
        Detect anomalies using rules.
        
        Args:
            device_id: Device identifier
            telemetry: Current telemetry data
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check all rules
        for category, rules in self.rules.items():
            for rule in rules:
                try:
                    result = rule["check"](telemetry)
                    
                    if result["triggered"]:
                        anomaly = self._create_anomaly(
                            device_id=device_id,
                            rule=rule,
                            result=result,
                            telemetry=telemetry
                        )
                        anomalies.append(anomaly)
                
                except Exception as e:
                    print(f"[ERROR] Rule {rule['name']} failed: {e}")
                    continue
        
        return anomalies
    
    # Rule check methods
    
    def _check_security_controls(
        self,
        telemetry: DeviceTelemetry
    ) -> Dict[str, Any]:
        """Check if critical security controls are disabled."""
        if not telemetry.security_data:
            return {"triggered": False}
        
        sec_data = telemetry.security_data
        disabled_controls = []
        
        if not sec_data.get("filevault", {}).get("enabled"):
            disabled_controls.append("FileVault")
        
        if not sec_data.get("sip", {}).get("enabled"):
            disabled_controls.append("SIP")
        
        if not sec_data.get("firewall", {}).get("enabled"):
            disabled_controls.append("Firewall")
        
        if not sec_data.get("gatekeeper", {}).get("enabled"):
            disabled_controls.append("Gatekeeper")
        
        # Trigger if 2 or more controls disabled
        if len(disabled_controls) >= 2:
            return {
                "triggered": True,
                "details": {
                    "disabled_controls": disabled_controls,
                    "count": len(disabled_controls)
                },
                "message": f"{len(disabled_controls)} critical security controls are disabled: "
                          f"{', '.join(disabled_controls)}"
            }
        
        return {"triggered": False}
    
    def _check_failed_auth(
        self,
        telemetry: DeviceTelemetry
    ) -> Dict[str, Any]:
        """Check for excessive failed authentication attempts."""
        if not telemetry.security_data:
            return {"triggered": False}
        
        failed_auths = telemetry.security_data.get("failed_authentication_attempts", 0)
        
        # Threshold for excessive failed authentications
        threshold = 10
        
        if failed_auths >= threshold:
            return {
                "triggered": True,
                "details": {
                    "failed_attempts": failed_auths,
                    "threshold": threshold
                },
                "message": f"Detected {failed_auths} failed authentication attempts "
                          f"(threshold: {threshold})"
            }
        
        return {"triggered": False}
    
    def _check_network_suspicious(
        self,
        telemetry: DeviceTelemetry
    ) -> Dict[str, Any]:
        """Check for suspicious network activity."""
        if not telemetry.network_data:
            return {"triggered": False}
        
        net_data = telemetry.network_data
        suspicious_indicators = []
        
        # Very high connection count
        connections = net_data.get("active_connections", 0)
        if connections > 100:
            suspicious_indicators.append(f"Excessive connections ({connections})")
        
        # VPN disabled on public network (simplified check)
        vpn_connected = net_data.get("vpn_connected", False)
        network_type = net_data.get("network_type", "unknown")
        
        if not vpn_connected and network_type == "public":
            suspicious_indicators.append("Public network without VPN")
        
        if suspicious_indicators:
            return {
                "triggered": True,
                "details": {
                    "indicators": suspicious_indicators,
                    "connection_count": connections,
                    "vpn_status": vpn_connected
                },
                "message": f"Suspicious network activity: {', '.join(suspicious_indicators)}"
            }
        
        return {"triggered": False}
    
    def _check_malicious_process(
        self,
        telemetry: DeviceTelemetry
    ) -> Dict[str, Any]:
        """Check for known malicious processes."""
        if not telemetry.process_data:
            return {"triggered": False}
        
        # Known malicious process names (simplified list)
        malicious_patterns = [
            "cryptominer",
            "keylogger",
            "trojan",
            "backdoor",
            "ransomware"
        ]
        
        processes = telemetry.process_data.get("processes", [])
        detected_malicious = []
        
        for process in processes:
            if isinstance(process, dict):
                process_name = process.get("name", "").lower()
                
                for pattern in malicious_patterns:
                    if pattern in process_name:
                        detected_malicious.append(process_name)
                        break
        
        if detected_malicious:
            return {
                "triggered": True,
                "details": {
                    "malicious_processes": detected_malicious,
                    "count": len(detected_malicious)
                },
                "message": f"Detected {len(detected_malicious)} potentially malicious processes"
            }
        
        return {"triggered": False}
    
    def _check_system_changes(
        self,
        telemetry: DeviceTelemetry
    ) -> Dict[str, Any]:
        """Check for critical system configuration changes."""
        # [Inference] This would compare current config against previous
        # For now, provide simplified check
        
        if not telemetry.system_data:
            return {"triggered": False}
        
        # Check for indicators of system compromise
        sys_data = telemetry.system_data
        
        # Very high disk usage could indicate data exfiltration prep
        disk_usage = sys_data.get("disk_usage", 0)
        
        if disk_usage > 95:
            return {
                "triggered": True,
                "details": {
                    "disk_usage": disk_usage,
                    "threshold": 95
                },
                "message": f"Critical disk usage ({disk_usage}%) may indicate system issues"
            }
        
        return {"triggered": False}
    
    def _create_anomaly(
        self,
        device_id: str,
        rule: Dict[str, Any],
        result: Dict[str, Any],
        telemetry: DeviceTelemetry
    ) -> AnomalyDetection:
        """
        Create anomaly detection record from rule violation.
        
        Args:
            device_id: Device identifier
            rule: Rule that triggered
            result: Rule check result
            telemetry: Telemetry data
        
        Returns:
            AnomalyDetection object
        """
        anomaly = AnomalyDetection(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:12].upper()}",
            device_id=device_id,
            anomaly_type=rule["type"].value,
            anomaly_severity=rule["severity"].value,
            detection_method="rule_based",
            detector_name="RuleBasedDetector",
            anomaly_score=self._calculate_rule_score(rule["severity"]),
            confidence=0.95,  # Rule-based methods have very high confidence
            feature_name=rule["name"],
            observed_value=result.get("details"),
            title=rule["description"],
            description=result.get("message", rule["description"]),
            recommendations=self._get_rule_recommendations(rule),
            telemetry_snapshot={
                "collection_time": telemetry.collection_time.isoformat(),
                "security_data": telemetry.security_data,
                "network_data": telemetry.network_data,
                "process_data": telemetry.process_data
            },
            detected_at=datetime.now(UTC)
        )
        
        self.db.add(anomaly)
        self.db.commit()
        
        return anomaly
    
    def _calculate_rule_score(self, severity: AnomalySeverity) -> float:
        """
        Calculate anomaly score based on severity.
        
        Args:
            severity: Severity level
        
        Returns:
            Anomaly score (0-100)
        """
        severity_scores = {
            AnomalySeverity.INFO: 20.0,
            AnomalySeverity.LOW: 40.0,
            AnomalySeverity.MEDIUM: 60.0,
            AnomalySeverity.HIGH: 80.0,
            AnomalySeverity.CRITICAL: 95.0
        }
        
        return severity_scores.get(severity, 50.0)
    
    def _get_rule_recommendations(self, rule: Dict[str, Any]) -> List[str]:
        """
        Get recommendations for rule violation.
        
        Args:
            rule: Rule dictionary
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if rule["severity"] in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]:
            recommendations.append("Investigate immediately")
            recommendations.append("Isolate device if necessary")
        
        if rule["type"] == AnomalyType.SECURITY_EVENT:
            recommendations.extend([
                "Enable disabled security controls",
                "Review security policy compliance",
                "Check for unauthorized configuration changes"
            ])
        elif rule["type"] == AnomalyType.AUTHENTICATION:
            recommendations.extend([
                "Lock user account temporarily",
                "Verify user identity",
                "Review authentication logs",
                "Consider implementing MFA"
            ])
        elif rule["type"] == AnomalyType.NETWORK:
            recommendations.extend([
                "Block suspicious connections",
                "Enable VPN requirement",
                "Review network access policies"
            ])
        elif rule["type"] == AnomalyType.PROCESS:
            recommendations.extend([
                "Terminate suspicious processes",
                "Run malware scan",
                "Review process execution history",
                "Consider reimaging device"
            ])
        
        return recommendations

