"""
Behavioral Analytics API Endpoints

Author: Adrian Johnson <adrian207@gmail.com>

FastAPI endpoints for anomaly detection, behavior profiling, and analytics management.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from analytics.models import (
    AnomalyDetection,
    BehaviorBaseline,
    BehaviorProfile,
    AnomalySeverity
)
from analytics.detection_engine import DetectionEngine
from analytics.profilers import BaselineProfiler, DeviceProfiler
from analytics.alerting import AnomalyAlerter


# API Router
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# Request/Response Models
class AnomalyResponse(BaseModel):
    """Anomaly response model."""
    anomaly_id: str
    device_id: str
    anomaly_type: str
    anomaly_severity: str
    title: str
    description: str
    anomaly_score: float
    confidence: float
    detected_at: str
    is_resolved: bool


class BaselineResponse(BaseModel):
    """Baseline response model."""
    baseline_id: str
    device_id: str
    baseline_type: str
    sample_count: int
    confidence_score: float
    is_active: bool
    last_updated: str


class ProfileResponse(BaseModel):
    """Profile response model."""
    profile_id: str
    device_id: str
    profile_version: int
    activity_regularity_score: float
    risk_appetite_score: float
    confidence_score: float
    is_complete: bool


class AnalyticsSummaryResponse(BaseModel):
    """Analytics summary response."""
    total_anomalies: int
    by_severity: dict
    by_type: dict
    recent_anomalies: int
    active_devices: int


class BuildBaselineRequest(BaseModel):
    """Request to build baseline."""
    device_id: str
    baseline_type: str
    force_refresh: bool = False


# Endpoints

@router.get("/anomalies", response_model=List[AnomalyResponse])
async def list_anomalies(
    device_id: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List detected anomalies.
    
    Args:
        device_id: Optional filter by device
        severity: Optional filter by severity
        resolved: Optional filter by resolution status
        limit: Maximum number to return
        db: Database session
    
    Returns:
        List of anomalies
    """
    query = db.query(AnomalyDetection).order_by(
        AnomalyDetection.detected_at.desc()
    )
    
    if device_id:
        query = query.filter(AnomalyDetection.device_id == device_id)
    
    if severity:
        query = query.filter(AnomalyDetection.anomaly_severity == severity)
    
    if resolved is not None:
        query = query.filter(AnomalyDetection.is_resolved == resolved)
    
    anomalies = query.limit(limit).all()
    
    return [
        AnomalyResponse(
            anomaly_id=a.anomaly_id,
            device_id=a.device_id,
            anomaly_type=a.anomaly_type,
            anomaly_severity=a.anomaly_severity,
            title=a.title,
            description=a.description,
            anomaly_score=a.anomaly_score,
            confidence=a.confidence,
            detected_at=a.detected_at.isoformat(),
            is_resolved=a.is_resolved
        )
        for a in anomalies
    ]


@router.get("/anomalies/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(
    anomaly_id: str,
    db: Session = Depends(get_db)
):
    """
    Get anomaly details.
    
    Args:
        anomaly_id: Anomaly ID
        db: Database session
    
    Returns:
        Anomaly details
    """
    anomaly = db.query(AnomalyDetection).filter(
        AnomalyDetection.anomaly_id == anomaly_id
    ).first()
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    return AnomalyResponse(
        anomaly_id=anomaly.anomaly_id,
        device_id=anomaly.device_id,
        anomaly_type=anomaly.anomaly_type,
        anomaly_severity=anomaly.anomaly_severity,
        title=anomaly.title,
        description=anomaly.description,
        anomaly_score=anomaly.anomaly_score,
        confidence=anomaly.confidence,
        detected_at=anomaly.detected_at.isoformat(),
        is_resolved=anomaly.is_resolved
    )


@router.post("/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: str,
    resolved_by: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Resolve an anomaly.
    
    Args:
        anomaly_id: Anomaly ID
        resolved_by: Who is resolving it
        notes: Optional resolution notes
        db: Database session
    
    Returns:
        Success message
    """
    engine = DetectionEngine(db)
    engine.resolve_anomaly(anomaly_id, resolved_by, notes)
    
    return {"message": "Anomaly resolved successfully"}


@router.post("/anomalies/{anomaly_id}/false-positive")
async def mark_false_positive(
    anomaly_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark anomaly as false positive.
    
    Args:
        anomaly_id: Anomaly ID
        db: Database session
    
    Returns:
        Success message
    """
    engine = DetectionEngine(db)
    engine.mark_false_positive(anomaly_id)
    
    return {"message": "Anomaly marked as false positive"}


@router.post("/anomalies/{anomaly_id}/alert")
async def send_alert(
    anomaly_id: str,
    recipients: List[str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send alert for anomaly.
    
    Args:
        anomaly_id: Anomaly ID
        recipients: Email recipients
        background_tasks: FastAPI background tasks
        db: Database session
    
    Returns:
        Success message
    """
    anomaly = db.query(AnomalyDetection).filter(
        AnomalyDetection.anomaly_id == anomaly_id
    ).first()
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    # Send alert in background
    background_tasks.add_task(_send_alert_task, db, anomaly, recipients)
    
    return {"message": "Alert queued for delivery"}


@router.get("/baselines", response_model=List[BaselineResponse])
async def list_baselines(
    device_id: Optional[str] = None,
    baseline_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List behavior baselines.
    
    Args:
        device_id: Optional filter by device
        baseline_type: Optional filter by type
        db: Database session
    
    Returns:
        List of baselines
    """
    query = db.query(BehaviorBaseline)
    
    if device_id:
        query = query.filter(BehaviorBaseline.device_id == device_id)
    
    if baseline_type:
        query = query.filter(BehaviorBaseline.baseline_type == baseline_type)
    
    baselines = query.all()
    
    return [
        BaselineResponse(
            baseline_id=b.baseline_id,
            device_id=b.device_id,
            baseline_type=b.baseline_type,
            sample_count=b.sample_count,
            confidence_score=b.confidence_score,
            is_active=b.is_active,
            last_updated=b.last_updated.isoformat()
        )
        for b in baselines
    ]


@router.post("/baselines/build")
async def build_baseline(
    request: BuildBaselineRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Build or refresh baseline.
    
    Args:
        request: Build request
        background_tasks: FastAPI background tasks
        db: Database session
    
    Returns:
        Success message
    """
    # Build in background
    background_tasks.add_task(
        _build_baseline_task,
        db,
        request.device_id,
        request.baseline_type,
        request.force_refresh
    )
    
    return {"message": "Baseline building queued"}


@router.get("/profiles/{device_id}", response_model=ProfileResponse)
async def get_profile(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Get device behavior profile.
    
    Args:
        device_id: Device ID
        db: Database session
    
    Returns:
        Profile details
    """
    profile = db.query(BehaviorProfile).filter(
        BehaviorProfile.device_id == device_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return ProfileResponse(
        profile_id=profile.profile_id,
        device_id=profile.device_id,
        profile_version=profile.profile_version,
        activity_regularity_score=profile.activity_regularity_score,
        risk_appetite_score=profile.risk_appetite_score,
        confidence_score=profile.confidence_score,
        is_complete=profile.is_complete
    )


@router.post("/profiles/{device_id}/build")
async def build_profile(
    device_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Build or refresh device profile.
    
    Args:
        device_id: Device ID
        background_tasks: FastAPI background tasks
        db: Database session
    
    Returns:
        Success message
    """
    # Build in background
    background_tasks.add_task(_build_profile_task, db, device_id)
    
    return {"message": "Profile building queued"}


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Get analytics summary statistics.
    
    Args:
        db: Database session
    
    Returns:
        Summary statistics
    """
    # Total anomalies
    total_anomalies = db.query(func.count(AnomalyDetection.id)).scalar()
    
    # By severity
    severity_counts = db.query(
        AnomalyDetection.anomaly_severity,
        func.count(AnomalyDetection.id)
    ).group_by(AnomalyDetection.anomaly_severity).all()
    
    by_severity = {sev: count for sev, count in severity_counts}
    
    # By type
    type_counts = db.query(
        AnomalyDetection.anomaly_type,
        func.count(AnomalyDetection.id)
    ).group_by(AnomalyDetection.anomaly_type).all()
    
    by_type = {typ: count for typ, count in type_counts}
    
    # Recent anomalies (last 24 hours)
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    recent_anomalies = db.query(func.count(AnomalyDetection.id)).filter(
        AnomalyDetection.detected_at >= cutoff
    ).scalar()
    
    # Active devices with baselines
    active_devices = db.query(
        func.count(func.distinct(BehaviorBaseline.device_id))
    ).filter(BehaviorBaseline.is_active == True).scalar()
    
    return AnalyticsSummaryResponse(
        total_anomalies=total_anomalies,
        by_severity=by_severity,
        by_type=by_type,
        recent_anomalies=recent_anomalies,
        active_devices=active_devices
    )


@router.get("/statistics")
async def get_detection_statistics(db: Session = Depends(get_db)):
    """
    Get detection engine statistics.
    
    Args:
        db: Database session
    
    Returns:
        Detection statistics
    """
    engine = DetectionEngine(db)
    return engine.get_statistics()


# Background tasks

async def _send_alert_task(
    db: Session,
    anomaly: AnomalyDetection,
    recipients: List[str]
):
    """Background task to send alert."""
    alerter = AnomalyAlerter(db, alert_recipients=recipients)
    alerter.alert_anomaly(anomaly, recipients)


async def _build_baseline_task(
    db: Session,
    device_id: str,
    baseline_type: str,
    force_refresh: bool
):
    """Background task to build baseline."""
    profiler = BaselineProfiler(db)
    profiler.build_baseline(device_id, baseline_type, force_refresh)


async def _build_profile_task(db: Session, device_id: str):
    """Background task to build profile."""
    profiler = DeviceProfiler(db)
    profiler.build_profile(device_id, force_refresh=True)

