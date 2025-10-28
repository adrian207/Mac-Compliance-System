"""
Risk Assessment Engine

Author: Adrian Johnson <adrian207@gmail.com>

Calculates comprehensive device risk scores based on multiple factors.
"""

from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)


class RiskAssessor:
    """
    Main risk assessment engine.
    
    Calculates device risk scores by analyzing:
    - Security posture (40%)
    - Compliance status (30%)
    - Behavioral patterns (20%)
    - Threat indicators (10%)
    """
    
    def __init__(self):
        """Initialize risk assessor with configuration."""
        self.config = get_config()
        self.risk_config = self.config.risk_assessment
        
        # Load weights from configuration
        self.weights = {
            "security_posture": self.risk_config.weights.security_posture / 100,
            "compliance": self.risk_config.weights.compliance / 100,
            "behavioral": self.risk_config.weights.behavioral / 100,
            "threat_indicators": self.risk_config.weights.threat_indicators / 100,
        }
        
        # Load thresholds
        self.thresholds = {
            "critical": self.risk_config.thresholds.critical,
            "high": self.risk_config.thresholds.high,
            "medium": self.risk_config.thresholds.medium,
            "low": self.risk_config.thresholds.low,
        }
    
    def assess_device_risk(
        self,
        telemetry: Dict[str, Any],
        compliance_results: Optional[Dict[str, Any]] = None,
        security_events: Optional[List[Dict[str, Any]]] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment for a device.
        
        Args:
            telemetry: Current device telemetry data
            compliance_results: Compliance check results
            security_events: Recent security events
            historical_data: Historical device data for behavioral analysis
        
        Returns:
            Dict containing risk score and detailed assessment
        """
        assessment_start = datetime.now(UTC)
        
        # Calculate component scores
        security_posture_score, security_factors = self._assess_security_posture(telemetry)
        compliance_score, compliance_factors = self._assess_compliance(
            telemetry, compliance_results
        )
        behavioral_score, behavioral_factors = self._assess_behavioral(
            telemetry, historical_data
        )
        threat_score, threat_factors = self._assess_threat_indicators(
            telemetry, security_events
        )
        
        # Calculate weighted total risk score
        total_risk_score = (
            (security_posture_score * self.weights["security_posture"]) +
            (compliance_score * self.weights["compliance"]) +
            (behavioral_score * self.weights["behavioral"]) +
            (threat_score * self.weights["threat_indicators"])
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(total_risk_score)
        
        # Collect all risk factors
        all_factors = (
            security_factors + compliance_factors +
            behavioral_factors + threat_factors
        )
        
        # Filter high-risk factors
        high_risk_factors = [
            f for f in all_factors
            if f["severity"] in ["high", "critical"]
        ]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_factors)
        
        # Calculate assessment duration
        duration = (datetime.now(UTC) - assessment_start).total_seconds() * 1000
        
        assessment_result = {
            "assessment_time": assessment_start.isoformat(),
            "total_risk_score": round(total_risk_score, 2),
            "risk_level": risk_level,
            "component_scores": {
                "security_posture": round(security_posture_score, 2),
                "compliance": round(compliance_score, 2),
                "behavioral": round(behavioral_score, 2),
                "threat_indicators": round(threat_score, 2),
            },
            "weights": self.weights,
            "risk_factors": all_factors,
            "high_risk_factors": high_risk_factors,
            "recommendations": recommendations,
            "calculation_time_ms": int(duration),
        }
        
        logger.info(
            "risk_assessment_completed",
            risk_score=round(total_risk_score, 2),
            risk_level=risk_level,
            factor_count=len(all_factors),
            duration_ms=int(duration)
        )
        
        return assessment_result
    
    def _assess_security_posture(
        self, telemetry: Dict[str, Any]
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Assess security posture (40% weight).
        
        Evaluates:
        - OS version and patch level (25%)
        - Security tools health (25%)
        - Encryption and firewall (25%)
        - Authentication configuration (25%)
        
        Returns:
            Tuple of (score, risk_factors)
        """
        factors = []
        scores = []
        
        security_status = telemetry.get("security_status", {})
        system_info = telemetry.get("system_info", {})
        
        # OS version check (contributes to 100-point scale)
        os_version = system_info.get("os_version", "0.0")
        os_score = self._check_os_version(os_version)
        scores.append(os_score)
        
        if os_score > 50:
            factors.append({
                "category": "security_posture",
                "subcategory": "os_version",
                "factor_name": "Outdated OS Version",
                "severity": "high" if os_score > 75 else "medium",
                "impact_score": os_score,
                "description": f"Mac OS version {os_version} may be outdated",
                "current_value": os_version,
                "expected_value": "13.0 or higher",
                "remediation_available": "automated",
            })
        
        # Security tools check (25%)
        tools_score = 0
        
        # FileVault (most critical - 40 points)
        if security_status.get("filevault_enabled") is False:
            tools_score += 40
            factors.append({
                "category": "security_posture",
                "subcategory": "encryption",
                "factor_name": "FileVault Disabled",
                "severity": "critical",
                "impact_score": 25,
                "description": "Disk encryption is not enabled",
                "current_value": "Disabled",
                "expected_value": "Enabled",
                "remediation_available": "automated",
            })
        
        # Firewall (25 points)
        if security_status.get("firewall_enabled") is False:
            tools_score += 25
            factors.append({
                "category": "security_posture",
                "subcategory": "network_security",
                "factor_name": "Firewall Disabled",
                "severity": "high",
                "impact_score": 25,
                "description": "System firewall is not enabled",
                "current_value": "Disabled",
                "expected_value": "Enabled",
                "remediation_available": "automated",
            })
        
        # Gatekeeper (15 points)
        if security_status.get("gatekeeper_enabled") is False:
            tools_score += 15
            factors.append({
                "category": "security_posture",
                "subcategory": "application_security",
                "factor_name": "Gatekeeper Disabled",
                "severity": "high",
                "impact_score": 15,
                "description": "Gatekeeper protection is disabled",
                "current_value": "Disabled",
                "expected_value": "Enabled",
                "remediation_available": "automated",
            })
        
        # SIP (most critical - 40 points)
        if security_status.get("sip_enabled") is False:
            tools_score += 40
            factors.append({
                "category": "security_posture",
                "subcategory": "system_security",
                "factor_name": "SIP Disabled",
                "severity": "critical",
                "impact_score": 40,
                "description": "System Integrity Protection is disabled",
                "current_value": "Disabled",
                "expected_value": "Enabled",
                "remediation_available": "manual",
            })
        
        # Cap at 100
        tools_score = min(tools_score, 100)
        scores.append(tools_score)
        
        # Authentication check (25%)
        auth_info = telemetry.get("authentication", {})
        auth_score = 0
        
        if auth_info.get("screen_lock_enabled") is False:
            auth_score += 20
            factors.append({
                "category": "security_posture",
                "subcategory": "authentication",
                "factor_name": "Screen Lock Disabled",
                "severity": "medium",
                "impact_score": 20,
                "description": "Screen lock is not configured",
                "current_value": "Disabled",
                "expected_value": "Enabled with timeout",
                "remediation_available": "automated",
            })
        
        if auth_info.get("password_required") is False:
            auth_score += 30
            factors.append({
                "category": "security_posture",
                "subcategory": "authentication",
                "factor_name": "No Password Required",
                "severity": "critical",
                "impact_score": 30,
                "description": "Device does not require password",
                "current_value": "Not Required",
                "expected_value": "Required",
                "remediation_available": "automated",
            })
        
        # Cap at 100
        auth_score = min(auth_score, 100)
        scores.append(auth_score)
        
        # Network security check (25%)
        network_info = telemetry.get("network_info", {})
        network_score = 0
        
        # Check for VPN when not on secure network
        # [Inference] This assumes certain WiFi SSIDs are trusted
        wifi_ssid = network_info.get("wifi_ssid", "")
        vpn_connected = network_info.get("vpn_connected", False)
        
        if wifi_ssid and not vpn_connected:
            if not self._is_trusted_network(wifi_ssid):
                network_score += 10
                factors.append({
                    "category": "security_posture",
                    "subcategory": "network_security",
                    "factor_name": "VPN Not Connected on Untrusted Network",
                    "severity": "medium",
                    "impact_score": 10,
                    "description": f"Connected to '{wifi_ssid}' without VPN",
                    "current_value": "VPN Disconnected",
                    "expected_value": "VPN Connected",
                    "remediation_available": "notification",
                })
        
        scores.append(network_score)
        
        # Calculate average security posture score (0-100 scale)
        # Average the four component scores
        total_score = sum(scores) / len(scores) if scores else 0
        
        return total_score, factors
    
    def _assess_compliance(
        self,
        telemetry: Dict[str, Any],
        compliance_results: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Assess compliance status (30% weight).
        
        Evaluates:
        - Policy adherence (40%)
        - Configuration drift (30%)
        - Required software (20%)
        - Certificate validity (10%)
        
        Returns:
            Tuple of (score, risk_factors)
        """
        factors = []
        
        if not compliance_results:
            # No compliance data, assume non-compliant
            return 50.0, [{
                "category": "compliance",
                "subcategory": "unknown",
                "factor_name": "No Compliance Data",
                "severity": "medium",
                "impact_score": 50,
                "description": "Compliance status unknown",
                "remediation_available": "check_required",
            }]
        
        # Use compliance score from results
        is_compliant = compliance_results.get("is_compliant", False)
        compliance_score = compliance_results.get("compliance_score", 50.0)
        violations = compliance_results.get("violations", [])
        
        # Add violation details as risk factors
        for violation in violations:
            severity_map = {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "low": "low",
            }
            
            factors.append({
                "category": "compliance",
                "subcategory": violation.get("category", "policy"),
                "factor_name": violation.get("name", "Compliance Violation"),
                "severity": severity_map.get(
                    violation.get("severity", "medium"),
                    "medium"
                ),
                "impact_score": violation.get("impact", 10),
                "description": violation.get("description", ""),
                "current_value": violation.get("current", "Non-compliant"),
                "expected_value": violation.get("expected", "Compliant"),
                "remediation_available": violation.get("remediation", "automated"),
            })
        
        # If not compliant, add base risk score
        if not is_compliant:
            base_score = 100 - compliance_score
        else:
            base_score = 0
        
        return base_score, factors
    
    def _assess_behavioral(
        self,
        telemetry: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Assess behavioral patterns (20% weight).
        
        Evaluates:
        - Access anomalies (40%)
        - Network behavior (30%)
        - Login patterns (20%)
        - File system changes (10%)
        
        Returns:
            Tuple of (score, risk_factors)
        """
        factors = []
        score = 0
        
        # [Inference] Behavioral analysis requires historical data
        # This is a simplified implementation
        
        if not historical_data:
            # No historical data for comparison
            return 0.0, []
        
        # Check for unusual network connections
        connections = telemetry.get("network_connections", [])
        suspicious_connections = [
            c for c in connections
            if self._is_suspicious_connection(c)
        ]
        
        if suspicious_connections:
            connection_score = min(len(suspicious_connections) * 5, 30)
            score += connection_score
            
            factors.append({
                "category": "behavioral",
                "subcategory": "network_behavior",
                "factor_name": "Suspicious Network Connections",
                "severity": "high" if len(suspicious_connections) > 5 else "medium",
                "impact_score": connection_score,
                "description": f"{len(suspicious_connections)} suspicious connections detected",
                "current_value": str(len(suspicious_connections)),
                "expected_value": "0",
                "remediation_available": "investigation",
            })
        
        # Check for unusual processes
        processes = telemetry.get("processes", [])
        suspicious_processes = [
            p for p in processes
            if self._is_suspicious_process(p)
        ]
        
        if suspicious_processes:
            process_score = min(len(suspicious_processes) * 10, 40)
            score += process_score
            
            factors.append({
                "category": "behavioral",
                "subcategory": "process_behavior",
                "factor_name": "Suspicious Processes Running",
                "severity": "high",
                "impact_score": process_score,
                "description": f"{len(suspicious_processes)} suspicious processes detected",
                "current_value": str(len(suspicious_processes)),
                "expected_value": "0",
                "remediation_available": "investigation",
            })
        
        return score, factors
    
    def _assess_threat_indicators(
        self,
        telemetry: Dict[str, Any],
        security_events: Optional[List[Dict[str, Any]]]
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Assess threat indicators (10% weight).
        
        Evaluates:
        - Malware detections (40%)
        - Suspicious processes (30%)
        - Network threats (20%)
        - Vulnerabilities (10%)
        
        Returns:
            Tuple of (score, risk_factors)
        """
        factors = []
        score = 0
        
        if not security_events:
            return 0.0, []
        
        # Analyze security events
        for event in security_events:
            severity = event.get("severity", "low")
            event_score = {
                "critical": 40,
                "high": 25,
                "medium": 15,
                "low": 5,
            }.get(severity, 5)
            
            score += event_score
            
            factors.append({
                "category": "threat_indicators",
                "subcategory": event.get("category", "security_event"),
                "factor_name": event.get("title", "Security Event"),
                "severity": severity,
                "impact_score": event_score,
                "description": event.get("description", ""),
                "remediation_available": "investigation",
            })
        
        # Cap threat score at 100
        score = min(score, 100)
        
        return score, factors
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """
        Determine risk level based on score.
        
        Args:
            risk_score: Risk score (0-100)
        
        Returns:
            Risk level string (low, medium, high, critical)
        """
        if risk_score >= self.thresholds["critical"]:
            return "critical"
        elif risk_score >= self.thresholds["high"]:
            return "high"
        elif risk_score >= self.thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(
        self, risk_factors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate remediation recommendations based on risk factors.
        
        Args:
            risk_factors: List of identified risk factors
        
        Returns:
            List of prioritized recommendations
        """
        recommendations = []
        
        # Group by category and prioritize
        critical_factors = [f for f in risk_factors if f["severity"] == "critical"]
        high_factors = [f for f in risk_factors if f["severity"] == "high"]
        
        # Add recommendations for critical factors
        for factor in critical_factors:
            recommendations.append({
                "priority": "critical",
                "action": f"Remediate: {factor['factor_name']}",
                "description": factor.get("description", ""),
                "automated": factor.get("remediation_available") == "automated",
            })
        
        # Add recommendations for high factors
        for factor in high_factors[:5]:  # Limit to top 5
            recommendations.append({
                "priority": "high",
                "action": f"Address: {factor['factor_name']}",
                "description": factor.get("description", ""),
                "automated": factor.get("remediation_available") == "automated",
            })
        
        return recommendations
    
    def _check_os_version(self, os_version: str) -> float:
        """
        Check if OS version meets minimum requirements.
        
        Args:
            os_version: Mac OS version string
        
        Returns:
            Risk score (0-100)
        """
        try:
            version_parts = os_version.split(".")
            major = int(version_parts[0])
            
            minimum_major = int(
                self.config.hardening.minimum_os_version.split(".")[0]
            )
            
            if major < minimum_major:
                # Outdated OS version
                versions_behind = minimum_major - major
                return min(versions_behind * 25, 100)
            elif major == minimum_major:
                # Check minor version
                return 0
            else:
                # Up to date
                return 0
        except (ValueError, AttributeError, IndexError):
            # Unable to parse version
            return 25
    
    def _is_trusted_network(self, ssid: str) -> bool:
        """
        Check if WiFi network is trusted.
        
        [Inference] This would typically check against a list of trusted SSIDs.
        
        Args:
            ssid: WiFi network SSID
        
        Returns:
            True if trusted, False otherwise
        """
        # [Inference] Default implementation - would be configured in production
        trusted_ssids = ["CorpNetwork", "OfficeWiFi", "SecureNet"]
        return ssid in trusted_ssids
    
    def _is_suspicious_connection(self, connection: Dict[str, Any]) -> bool:
        """
        Check if network connection is suspicious.
        
        [Inference] This would typically use threat intelligence feeds.
        
        Args:
            connection: Network connection details
        
        Returns:
            True if suspicious, False otherwise
        """
        # [Inference] Simplified implementation
        remote_addr = connection.get("remote_address", "")
        
        # Check for connections to unusual ports
        remote_port = connection.get("remote_port")
        suspicious_ports = [4444, 6667, 31337]  # Example malicious ports
        
        if remote_port in suspicious_ports:
            return True
        
        return False
    
    def _is_suspicious_process(self, process: Dict[str, Any]) -> bool:
        """
        Check if process is suspicious.
        
        [Inference] This would typically use process reputation databases.
        
        Args:
            process: Process details
        
        Returns:
            True if suspicious, False otherwise
        """
        # [Inference] Simplified implementation
        command = process.get("command", "").lower()
        
        # Check for suspicious keywords
        suspicious_keywords = [
            "mimikatz", "metasploit", "netcat", "nmap",
            "backdoor", "keylogger", "ransomware"
        ]
        
        for keyword in suspicious_keywords:
            if keyword in command:
                return True
        
        return False


def assess_device_risk(
    telemetry: Dict[str, Any],
    compliance_results: Optional[Dict[str, Any]] = None,
    security_events: Optional[List[Dict[str, Any]]] = None,
    historical_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Assess device risk.
    
    Args:
        telemetry: Device telemetry data
        compliance_results: Compliance check results
        security_events: Recent security events
        historical_data: Historical device data
    
    Returns:
        Dict containing risk assessment results
    """
    assessor = RiskAssessor()
    return assessor.assess_device_risk(
        telemetry, compliance_results, security_events, historical_data
    )

