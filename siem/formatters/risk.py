"""
Risk Assessment Formatter

Author: Adrian Johnson <adrian207@gmail.com>

Formats risk assessments for SIEM export.
"""

from typing import Dict, Any
from risk_engine.models import RiskAssessment


class RiskAssessmentFormatter:
    """
    Formats risk assessment events for SIEM export.
    
    Transforms risk assessment data into SIEM-friendly format.
    """
    
    @staticmethod
    def format(assessment: RiskAssessment) -> Dict[str, Any]:
        """
        Format risk assessment for SIEM export.
        
        Args:
            assessment: RiskAssessment object
        
        Returns:
            Formatted event dictionary
        """
        event = {
            # Standard fields
            "event_id": assessment.assessment_id,
            "timestamp": assessment.assessment_time.isoformat(),
            "event_type": "risk_assessment",
            "source": assessment.device_id,
            
            # Risk scores
            "risk": {
                "total_score": assessment.total_risk_score,
                "level": assessment.risk_level,
                "previous_score": assessment.previous_risk_score,
                "score_change": assessment.score_delta
            },
            
            # Component scores
            "risk_components": {
                "security_posture": assessment.security_posture_score,
                "compliance": assessment.compliance_score,
                "vulnerability": assessment.vulnerability_score,
                "behavior": assessment.behavior_score
            },
            
            # Risk factors
            "risk_factors": assessment.risk_factors or [],
            "risk_factor_count": len(assessment.risk_factors or []),
            
            # Context
            "assessment": {
                "method": "multi_factor",
                "confidence": 0.9,  # Risk assessments have high confidence
                "assessor": assessment.assessed_by
            },
            
            # Changes
            "changes": {
                "risk_increased": assessment.score_delta > 0 if assessment.score_delta else False,
                "risk_decreased": assessment.score_delta < 0 if assessment.score_delta else False,
                "level_changed": assessment.risk_level_changed
            },
            
            # Platform metadata
            "platform": {
                "product": "ZeroTrust Mac Compliance",
                "module": "risk_engine",
                "version": "0.9.0"
            }
        }
        
        # Add severity classification for SIEM
        event["severity"] = RiskAssessmentFormatter._map_risk_to_severity(
            assessment.risk_level
        )
        
        return event
    
    @staticmethod
    def _map_risk_to_severity(risk_level: str) -> str:
        """
        Map risk level to SIEM severity.
        
        Args:
            risk_level: Risk level (low, medium, high, critical)
        
        Returns:
            SIEM severity string
        """
        severity_map = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        
        return severity_map.get(risk_level, "info")

