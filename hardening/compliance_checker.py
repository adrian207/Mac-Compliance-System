"""
Compliance Checker

Author: Adrian Johnson <adrian207@gmail.com>

Validates device compliance against security policies and baselines.
"""

from datetime import datetime, UTC
from typing import Any, Dict, List

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)


class ComplianceChecker:
    """
    Device compliance checker.
    
    Validates device configuration against security policies and identifies violations.
    """
    
    def __init__(self):
        """Initialize compliance checker."""
        self.config = get_config()
        self.hardening_config = self.config.hardening
    
    def check_compliance(
        self, telemetry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check device compliance against all policies.
        
        Args:
            telemetry: Device telemetry data
        
        Returns:
            Dict containing compliance results
        """
        check_start = datetime.now(UTC)
        
        checks = []
        violations = []
        
        # Run all compliance checks
        checks.extend(self._check_os_requirements(telemetry))
        checks.extend(self._check_security_requirements(telemetry))
        checks.extend(self._check_authentication_requirements(telemetry))
        checks.extend(self._check_network_requirements(telemetry))
        
        # Separate passed and failed checks
        passed_checks = [c for c in checks if c["passed"]]
        failed_checks = [c for c in checks if not c["passed"]]
        
        # Build violations list from failed checks
        for check in failed_checks:
            violations.append({
                "name": check["name"],
                "category": check["category"],
                "severity": check["severity"],
                "description": check["description"],
                "current": check["current_value"],
                "expected": check["expected_value"],
                "remediation": check["remediation"],
                "impact": check["impact_score"]
            })
        
        # Calculate compliance score
        total_checks = len(checks)
        passed_count = len(passed_checks)
        compliance_score = (passed_count / total_checks * 100) if total_checks > 0 else 0
        
        # Determine if compliant (all critical checks must pass)
        critical_failures = [c for c in failed_checks if c["severity"] == "critical"]
        is_compliant = len(critical_failures) == 0 and compliance_score >= 80
        
        # Determine remediation actions
        remediation_actions = []
        if failed_checks:
            for check in failed_checks:
                if check["remediation"] == "automated":
                    remediation_actions.append({
                        "action": "automated_fix",
                        "check": check["name"],
                        "priority": check["severity"]
                    })
                elif check["remediation"] == "manual":
                    remediation_actions.append({
                        "action": "manual_intervention",
                        "check": check["name"],
                        "priority": check["severity"]
                    })
        
        duration = (datetime.now(UTC) - check_start).total_seconds() * 1000
        
        result = {
            "check_time": check_start.isoformat(),
            "is_compliant": is_compliant,
            "compliance_score": round(compliance_score, 2),
            "total_checks": total_checks,
            "passed_checks": passed_count,
            "failed_checks": len(failed_checks),
            "violations": violations,
            "check_results": checks,
            "remediation_required": len(remediation_actions) > 0,
            "remediation_actions": remediation_actions,
            "policy_version": "1.0",
            "policy_name": "Mac OS Security Baseline",
            "calculation_time_ms": int(duration)
        }
        
        logger.info(
            "compliance_check_completed",
            is_compliant=is_compliant,
            compliance_score=round(compliance_score, 2),
            violations=len(violations),
            duration_ms=int(duration)
        )
        
        return result
    
    def _check_os_requirements(
        self, telemetry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check OS version and patch requirements."""
        checks = []
        system_info = telemetry.get("system_info", {})
        
        # OS version check
        os_version = system_info.get("os_version", "0.0")
        min_version = self.hardening_config.minimum_os_version
        
        try:
            version_parts = os_version.split(".")
            current_major = int(version_parts[0]) if version_parts else 0
            
            min_parts = min_version.split(".")
            required_major = int(min_parts[0]) if min_parts else 0
            
            passed = current_major >= required_major
        except (ValueError, IndexError):
            passed = False
        
        checks.append({
            "name": "OS Version",
            "category": "os_requirements",
            "passed": passed,
            "severity": "critical",
            "impact_score": 25,
            "description": f"Mac OS version must be {min_version} or higher",
            "current_value": os_version,
            "expected_value": f">= {min_version}",
            "remediation": "automated"
        })
        
        return checks
    
    def _check_security_requirements(
        self, telemetry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check security feature requirements."""
        checks = []
        security_status = telemetry.get("security_status", {})
        
        # FileVault check
        if self.hardening_config.require_filevault:
            filevault_enabled = security_status.get("filevault_enabled", False)
            checks.append({
                "name": "FileVault Encryption",
                "category": "security",
                "passed": filevault_enabled,
                "severity": "critical",
                "impact_score": 30,
                "description": "Disk encryption must be enabled",
                "current_value": "Enabled" if filevault_enabled else "Disabled",
                "expected_value": "Enabled",
                "remediation": "automated"
            })
        
        # Firewall check
        if self.hardening_config.require_firewall:
            firewall_enabled = security_status.get("firewall_enabled", False)
            checks.append({
                "name": "System Firewall",
                "category": "security",
                "passed": firewall_enabled,
                "severity": "high",
                "impact_score": 20,
                "description": "System firewall must be enabled",
                "current_value": "Enabled" if firewall_enabled else "Disabled",
                "expected_value": "Enabled",
                "remediation": "automated"
            })
        
        # Gatekeeper check
        if self.hardening_config.require_gatekeeper:
            gatekeeper_enabled = security_status.get("gatekeeper_enabled", False)
            checks.append({
                "name": "Gatekeeper",
                "category": "security",
                "passed": gatekeeper_enabled,
                "severity": "high",
                "impact_score": 15,
                "description": "Gatekeeper must be enabled",
                "current_value": "Enabled" if gatekeeper_enabled else "Disabled",
                "expected_value": "Enabled",
                "remediation": "automated"
            })
        
        # SIP check
        if self.hardening_config.require_sip:
            sip_enabled = security_status.get("sip_enabled", False)
            checks.append({
                "name": "System Integrity Protection",
                "category": "security",
                "passed": sip_enabled,
                "severity": "critical",
                "impact_score": 25,
                "description": "System Integrity Protection must be enabled",
                "current_value": "Enabled" if sip_enabled else "Disabled",
                "expected_value": "Enabled",
                "remediation": "manual"
            })
        
        return checks
    
    def _check_authentication_requirements(
        self, telemetry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check authentication and access control requirements."""
        checks = []
        auth_info = telemetry.get("authentication", {})
        
        # Password requirement
        if self.hardening_config.require_password:
            password_required = auth_info.get("password_required", False)
            checks.append({
                "name": "Password Required",
                "category": "authentication",
                "passed": password_required,
                "severity": "critical",
                "impact_score": 20,
                "description": "Device must require password for login",
                "current_value": "Required" if password_required else "Not Required",
                "expected_value": "Required",
                "remediation": "automated"
            })
        
        # Screen lock requirement
        if self.hardening_config.require_screen_lock:
            screen_lock_enabled = auth_info.get("screen_lock_enabled", False)
            checks.append({
                "name": "Screen Lock",
                "category": "authentication",
                "passed": screen_lock_enabled,
                "severity": "medium",
                "impact_score": 10,
                "description": "Automatic screen lock must be enabled",
                "current_value": "Enabled" if screen_lock_enabled else "Disabled",
                "expected_value": "Enabled",
                "remediation": "automated"
            })
        
        return checks
    
    def _check_network_requirements(
        self, telemetry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check network security requirements."""
        checks = []
        network_info = telemetry.get("network_info", {})
        
        # [Inference] Additional network checks could be added here
        # For example: VPN requirements, DNS settings, etc.
        
        return checks


def check_device_compliance(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check device compliance.
    
    Args:
        telemetry: Device telemetry data
    
    Returns:
        Compliance check results
    """
    checker = ComplianceChecker()
    return checker.check_compliance(telemetry)

