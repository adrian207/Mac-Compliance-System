"""
Compliance Event Formatter

Author: Adrian Johnson <adrian207@gmail.com>

Formats compliance checks for SIEM export.
"""

from typing import Dict, Any
from reporting.models import ComplianceHistory


class ComplianceFormatter:
    """
    Formats compliance check events for SIEM export.
    
    Transforms compliance data into SIEM-friendly format.
    """
    
    @staticmethod
    def format(compliance: ComplianceHistory) -> Dict[str, Any]:
        """
        Format compliance check for SIEM export.
        
        Args:
            compliance: ComplianceHistory object
        
        Returns:
            Formatted event dictionary
        """
        event = {
            # Standard fields
            "event_id": f"COMP-{compliance.id}",
            "timestamp": compliance.recorded_at.isoformat(),
            "event_type": "compliance_check",
            "source": compliance.device_id,
            
            # Compliance status
            "compliance": {
                "is_compliant": compliance.is_compliant,
                "score": compliance.compliance_score,
                "policies_total": compliance.policies_total,
                "policies_passed": compliance.policies_passed,
                "policies_failed": compliance.policies_failed
            },
            
            # Violations
            "violations": {
                "critical_count": len(compliance.critical_failures or []),
                "critical_policies": compliance.critical_failures or [],
                "newly_failed": compliance.newly_failed_policies or [],
                "newly_passed": compliance.newly_passed_policies or []
            },
            
            # Changes
            "changes": {
                "status_changed": compliance.status_changed,
                "previously_compliant": not compliance.is_compliant if compliance.status_changed else compliance.is_compliant
            },
            
            # Platform metadata
            "platform": {
                "product": "ZeroTrust Mac Compliance",
                "module": "compliance_checker",
                "version": "0.9.0"
            }
        }
        
        # Add severity based on compliance status
        if not compliance.is_compliant:
            if compliance.critical_failures and len(compliance.critical_failures) > 0:
                event["severity"] = "critical"
            elif compliance.policies_failed > 3:
                event["severity"] = "high"
            else:
                event["severity"] = "medium"
        else:
            event["severity"] = "info"
        
        return event

