"""
Metrics Collection and Prometheus Integration

Author: Adrian Johnson <adrian207@gmail.com>

Collects and exposes platform metrics for monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, generate_latest
from typing import Dict, Any

from core.logging_config import get_logger

logger = get_logger(__name__)


# Create custom registry
registry = CollectorRegistry()


# Device metrics
device_count = Gauge(
    'zerotrust_devices_total',
    'Total number of managed devices',
    registry=registry
)

device_risk_score = Gauge(
    'zerotrust_device_risk_score',
    'Current device risk score',
    ['device_id', 'risk_level'],
    registry=registry
)

devices_by_risk_level = Gauge(
    'zerotrust_devices_by_risk_level',
    'Number of devices by risk level',
    ['risk_level'],
    registry=registry
)

device_compliance = Gauge(
    'zerotrust_device_compliance',
    'Device compliance status (0=non-compliant, 1=compliant)',
    ['device_id'],
    registry=registry
)


# Risk assessment metrics
risk_assessments_total = Counter(
    'zerotrust_risk_assessments_total',
    'Total number of risk assessments performed',
    registry=registry
)

risk_assessment_duration = Histogram(
    'zerotrust_risk_assessment_duration_seconds',
    'Risk assessment duration in seconds',
    registry=registry
)


# Workflow metrics
workflow_executions_total = Counter(
    'zerotrust_workflow_executions_total',
    'Total number of workflow executions',
    ['workflow_name', 'status'],
    registry=registry
)

workflow_execution_duration = Histogram(
    'zerotrust_workflow_execution_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_name'],
    registry=registry
)

workflow_actions_total = Counter(
    'zerotrust_workflow_actions_total',
    'Total number of workflow actions executed',
    ['action_type', 'status'],
    registry=registry
)


# Integration metrics
integration_requests_total = Counter(
    'zerotrust_integration_requests_total',
    'Total number of integration API requests',
    ['integration', 'method', 'status'],
    registry=registry
)

integration_request_duration = Histogram(
    'zerotrust_integration_request_duration_seconds',
    'Integration API request duration in seconds',
    ['integration', 'method'],
    registry=registry
)

integration_errors_total = Counter(
    'zerotrust_integration_errors_total',
    'Total number of integration errors',
    ['integration', 'error_type'],
    registry=registry
)


# Security event metrics
security_events_total = Counter(
    'zerotrust_security_events_total',
    'Total number of security events detected',
    ['severity', 'category'],
    registry=registry
)

incidents_total = Counter(
    'zerotrust_incidents_total',
    'Total number of security incidents created',
    ['severity'],
    registry=registry
)


# Compliance metrics
compliance_checks_total = Counter(
    'zerotrust_compliance_checks_total',
    'Total number of compliance checks performed',
    registry=registry
)

compliance_violations_total = Counter(
    'zerotrust_compliance_violations_total',
    'Total number of compliance violations detected',
    ['severity'],
    registry=registry
)


# Telemetry collection metrics
telemetry_collections_total = Counter(
    'zerotrust_telemetry_collections_total',
    'Total number of telemetry collections',
    ['status'],
    registry=registry
)

telemetry_collection_duration = Histogram(
    'zerotrust_telemetry_collection_duration_seconds',
    'Telemetry collection duration in seconds',
    registry=registry
)


# System metrics
platform_uptime = Gauge(
    'zerotrust_platform_uptime_seconds',
    'Platform uptime in seconds',
    registry=registry
)

database_connections = Gauge(
    'zerotrust_database_connections',
    'Number of active database connections',
    registry=registry
)


class MetricsCollector:
    """
    Metrics collector for platform monitoring.
    
    Provides methods to update metrics and expose them for Prometheus.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        logger.info("metrics_collector_initialized")
    
    def update_device_metrics(
        self,
        total_devices: int,
        devices_by_risk: Dict[str, int]
    ) -> None:
        """
        Update device-related metrics.
        
        Args:
            total_devices: Total number of devices
            devices_by_risk: Dictionary of device counts by risk level
        """
        device_count.set(total_devices)
        
        for risk_level, count in devices_by_risk.items():
            devices_by_risk_level.labels(risk_level=risk_level).set(count)
    
    def record_risk_assessment(
        self,
        device_id: str,
        risk_score: float,
        risk_level: str,
        duration_seconds: float
    ) -> None:
        """
        Record a risk assessment.
        
        Args:
            device_id: Device identifier
            risk_score: Risk score (0-100)
            risk_level: Risk level (low, medium, high, critical)
            duration_seconds: Assessment duration in seconds
        """
        risk_assessments_total.inc()
        device_risk_score.labels(
            device_id=device_id,
            risk_level=risk_level
        ).set(risk_score)
        risk_assessment_duration.observe(duration_seconds)
    
    def record_workflow_execution(
        self,
        workflow_name: str,
        status: str,
        duration_seconds: float
    ) -> None:
        """
        Record a workflow execution.
        
        Args:
            workflow_name: Name of the workflow
            status: Execution status (completed, failed)
            duration_seconds: Execution duration in seconds
        """
        workflow_executions_total.labels(
            workflow_name=workflow_name,
            status=status
        ).inc()
        
        workflow_execution_duration.labels(
            workflow_name=workflow_name
        ).observe(duration_seconds)
    
    def record_workflow_action(
        self,
        action_type: str,
        status: str
    ) -> None:
        """
        Record a workflow action.
        
        Args:
            action_type: Type of action
            status: Action status (completed, failed)
        """
        workflow_actions_total.labels(
            action_type=action_type,
            status=status
        ).inc()
    
    def record_integration_request(
        self,
        integration: str,
        method: str,
        status: int,
        duration_seconds: float
    ) -> None:
        """
        Record an integration API request.
        
        Args:
            integration: Integration name (kandji, zscaler, seraphic)
            method: HTTP method
            status: HTTP status code
            duration_seconds: Request duration in seconds
        """
        integration_requests_total.labels(
            integration=integration,
            method=method,
            status=str(status)
        ).inc()
        
        integration_request_duration.labels(
            integration=integration,
            method=method
        ).observe(duration_seconds)
    
    def record_integration_error(
        self,
        integration: str,
        error_type: str
    ) -> None:
        """
        Record an integration error.
        
        Args:
            integration: Integration name
            error_type: Type of error
        """
        integration_errors_total.labels(
            integration=integration,
            error_type=error_type
        ).inc()
    
    def record_security_event(
        self,
        severity: str,
        category: str
    ) -> None:
        """
        Record a security event.
        
        Args:
            severity: Event severity
            category: Event category
        """
        security_events_total.labels(
            severity=severity,
            category=category
        ).inc()
    
    def record_incident(self, severity: str) -> None:
        """
        Record a security incident.
        
        Args:
            severity: Incident severity
        """
        incidents_total.labels(severity=severity).inc()
    
    def record_compliance_check(
        self,
        device_id: str,
        is_compliant: bool
    ) -> None:
        """
        Record a compliance check.
        
        Args:
            device_id: Device identifier
            is_compliant: Whether device is compliant
        """
        compliance_checks_total.inc()
        device_compliance.labels(device_id=device_id).set(1 if is_compliant else 0)
    
    def record_compliance_violation(self, severity: str) -> None:
        """
        Record a compliance violation.
        
        Args:
            severity: Violation severity
        """
        compliance_violations_total.labels(severity=severity).inc()
    
    def record_telemetry_collection(
        self,
        status: str,
        duration_seconds: float
    ) -> None:
        """
        Record a telemetry collection.
        
        Args:
            status: Collection status (success, failed)
            duration_seconds: Collection duration in seconds
        """
        telemetry_collections_total.labels(status=status).inc()
        telemetry_collection_duration.observe(duration_seconds)
    
    def get_metrics(self) -> bytes:
        """
        Get metrics in Prometheus format.
        
        Returns:
            Metrics data in Prometheus text format
        """
        return generate_latest(registry)


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance.
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

