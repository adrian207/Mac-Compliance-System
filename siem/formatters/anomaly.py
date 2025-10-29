"""
Anomaly Event Formatter

Author: Adrian Johnson <adrian207@gmail.com>

Formats anomaly detections for SIEM export.
"""

from typing import Dict, Any
from analytics.models import AnomalyDetection


class AnomalyFormatter:
    """
    Formats anomaly detection events for SIEM export.
    
    Transforms anomaly data into SIEM-friendly format with proper
    categorization and enrichment.
    """
    
    @staticmethod
    def format(anomaly: AnomalyDetection) -> Dict[str, Any]:
        """
        Format anomaly detection for SIEM export.
        
        Args:
            anomaly: AnomalyDetection object
        
        Returns:
            Formatted event dictionary
        """
        event = {
            # Standard fields
            "event_id": anomaly.anomaly_id,
            "timestamp": anomaly.detected_at.isoformat(),
            "event_type": "anomaly",
            "source": anomaly.device_id,
            
            # Anomaly classification
            "anomaly": {
                "type": anomaly.anomaly_type,
                "severity": anomaly.anomaly_severity,
                "score": anomaly.anomaly_score,
                "confidence": anomaly.confidence
            },
            
            # Detection details
            "detection": {
                "method": anomaly.detection_method,
                "detector": anomaly.detector_name,
                "model_version": anomaly.model_version
            },
            
            # Context
            "title": anomaly.title,
            "description": anomaly.description,
            "feature": anomaly.feature_name,
            
            # Values
            "observed_value": anomaly.observed_value,
            "expected_value": anomaly.expected_value,
            "deviation": anomaly.deviation,
            
            # Recommendations
            "recommendations": anomaly.recommendations or [],
            
            # Status
            "status": {
                "confirmed": anomaly.is_confirmed,
                "false_positive": anomaly.is_false_positive,
                "resolved": anomaly.is_resolved,
                "alert_sent": anomaly.alert_sent
            },
            
            # Platform metadata
            "platform": {
                "product": "ZeroTrust Mac Compliance",
                "module": "behavioral_analytics",
                "version": "0.9.5"
            }
        }
        
        # Add MITRE ATT&CK mapping (if applicable)
        if anomaly.anomaly_type in ["authentication", "network", "process"]:
            event["mitre_attack"] = AnomalyFormatter._map_to_mitre(anomaly)
        
        return event
    
    @staticmethod
    def _map_to_mitre(anomaly: AnomalyDetection) -> Dict[str, Any]:
        """
        Map anomaly to MITRE ATT&CK framework.
        
        Args:
            anomaly: AnomalyDetection object
        
        Returns:
            MITRE ATT&CK mapping
        """
        # Simplified MITRE mapping
        mitre_mappings = {
            "authentication": {
                "tactic": "TA0006",  # Credential Access
                "tactic_name": "Credential Access",
                "technique": "T1110",  # Brute Force
                "technique_name": "Brute Force"
            },
            "network": {
                "tactic": "TA0011",  # Command and Control
                "tactic_name": "Command and Control",
                "technique": "T1071",  # Application Layer Protocol
                "technique_name": "Application Layer Protocol"
            },
            "process": {
                "tactic": "TA0002",  # Execution
                "tactic_name": "Execution",
                "technique": "T1059",  # Command and Scripting Interpreter
                "technique_name": "Command and Scripting Interpreter"
            }
        }
        
        return mitre_mappings.get(anomaly.anomaly_type, {})

