"""
Zero Trust Platform REST API Server

Author: Adrian Johnson <adrian207@gmail.com>

FastAPI-based REST API for the Zero Trust security platform.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from core.config import get_config
from core.database import get_db_session
from core.logging_config import setup_logging, get_logger
from monitoring.metrics import get_metrics_collector
from monitoring.alerts import send_alert
from telemetry.collector import collect_telemetry
from risk_engine.assessor import assess_device_risk
from hardening.compliance_checker import check_device_compliance
from workflows.orchestrator import execute_workflow

# Initialize
config = get_config()
setup_logging(log_level=config.log_level)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Mac OS Zero Trust Security Platform API",
    description="REST API for Zero Trust endpoint security management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
if config.api and config.api.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Mac OS Zero Trust Security Platform",
        "version": "1.0.0",
        "author": "Adrian Johnson <adrian207@gmail.com>",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    metrics_collector = get_metrics_collector()
    metrics_data = metrics_collector.get_metrics()
    return Response(content=metrics_data, media_type="text/plain")


# Device Endpoints

@app.post("/api/v1/devices/telemetry")
async def collect_device_telemetry(
    device_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect telemetry from a device.
    
    Args:
        device_id: Optional device identifier
    
    Returns:
        Telemetry data
    """
    try:
        telemetry = collect_telemetry()
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        duration = telemetry.get("collection_duration_ms", 0) / 1000.0
        status = "success" if not telemetry.get("error") else "failed"
        metrics_collector.record_telemetry_collection(status, duration)
        
        logger.info("telemetry_collected", device_id=device_id)
        
        return {
            "success": True,
            "device_id": device_id,
            "telemetry": telemetry
        }
    
    except Exception as e:
        logger.error("telemetry_collection_failed", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telemetry collection failed: {str(e)}"
        )


@app.post("/api/v1/devices/risk-assessment")
async def assess_risk(
    telemetry: Dict[str, Any],
    compliance_results: Optional[Dict[str, Any]] = None,
    security_events: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Perform risk assessment for a device.
    
    Args:
        telemetry: Device telemetry data
        compliance_results: Optional compliance results
        security_events: Optional security events
    
    Returns:
        Risk assessment results
    """
    try:
        assessment = assess_device_risk(
            telemetry,
            compliance_results,
            security_events
        )
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        device_id = telemetry.get("system_info", {}).get("uuid", "unknown")
        duration = assessment.get("calculation_time_ms", 0) / 1000.0
        
        metrics_collector.record_risk_assessment(
            device_id,
            assessment["total_risk_score"],
            assessment["risk_level"],
            duration
        )
        
        # Send alert if high risk
        if assessment["risk_level"] in ["high", "critical"]:
            send_alert(
                "high_risk_device_detected",
                assessment["risk_level"],
                f"Device {device_id} has risk score {assessment['total_risk_score']}",
                {"device_id": device_id, "risk_score": assessment["total_risk_score"]}
            )
        
        logger.info(
            "risk_assessment_completed",
            device_id=device_id,
            risk_score=assessment["total_risk_score"]
        )
        
        return {
            "success": True,
            "assessment": assessment
        }
    
    except Exception as e:
        logger.error("risk_assessment_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment failed: {str(e)}"
        )


@app.post("/api/v1/devices/compliance-check")
async def compliance_check(
    telemetry: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check device compliance.
    
    Args:
        telemetry: Device telemetry data
    
    Returns:
        Compliance check results
    """
    try:
        compliance = check_device_compliance(telemetry)
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        device_id = telemetry.get("system_info", {}).get("uuid", "unknown")
        metrics_collector.record_compliance_check(
            device_id,
            compliance["is_compliant"]
        )
        
        # Record violations
        for violation in compliance.get("violations", []):
            metrics_collector.record_compliance_violation(violation["severity"])
        
        logger.info(
            "compliance_check_completed",
            device_id=device_id,
            is_compliant=compliance["is_compliant"]
        )
        
        return {
            "success": True,
            "compliance": compliance
        }
    
    except Exception as e:
        logger.error("compliance_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance check failed: {str(e)}"
        )


# Workflow Endpoints

@app.post("/api/v1/workflows/execute")
async def execute_workflow_endpoint(
    workflow_name: str,
    trigger_type: str,
    trigger_data: Dict[str, Any],
    device_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute a workflow.
    
    Args:
        workflow_name: Name of the workflow
        trigger_type: Trigger type
        trigger_data: Trigger data
        device_id: Optional device ID
    
    Returns:
        Workflow execution results
    """
    try:
        result = execute_workflow(
            workflow_name,
            trigger_type,
            trigger_data,
            device_id
        )
        
        # Record metrics
        metrics_collector = get_metrics_collector()
        duration = result.get("duration_ms", 0) / 1000.0
        status_str = "completed" if result["success"] else "failed"
        metrics_collector.record_workflow_execution(
            workflow_name,
            status_str,
            duration
        )
        
        logger.info(
            "workflow_executed",
            workflow_name=workflow_name,
            success=result["success"]
        )
        
        return result
    
    except Exception as e:
        logger.error("workflow_execution_failed", workflow_name=workflow_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


# Alert Endpoints

@app.post("/api/v1/alerts/send")
async def send_alert_endpoint(
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
    try:
        result = send_alert(alert_name, severity, message, details)
        
        logger.info("alert_sent", alert_name=alert_name, severity=severity)
        
        return result
    
    except Exception as e:
        logger.error("alert_send_failed", alert_name=alert_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert send failed: {str(e)}"
        )


def start_server():
    """Start the API server."""
    api_config = config.api
    
    uvicorn.run(
        "api_server:app",
        host=api_config.host,
        port=api_config.port,
        workers=api_config.workers,
        reload=api_config.reload,
        access_log=api_config.access_log
    )


if __name__ == "__main__":
    start_server()

