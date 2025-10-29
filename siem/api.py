"""
SIEM Integration API Endpoints

Author: Adrian Johnson <adrian207@gmail.com>

FastAPI endpoints for SIEM connection management and event export.
"""

from datetime import datetime, UTC
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from siem.models import SIEMConnection, SIEMEvent, SIEMType, SIEMEventType
from siem.manager import SIEMManager


# API Router
router = APIRouter(prefix="/api/v1/siem", tags=["siem"])


# Request/Response Models
class CreateSIEMConnectionRequest(BaseModel):
    """Request to create SIEM connection."""
    name: str
    siem_type: str
    endpoint: str
    port: Optional[int] = None
    use_ssl: bool = True
    verify_ssl: bool = True
    auth_type: str
    auth_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    index_name: Optional[str] = None
    source_type: Optional[str] = None
    facility: Optional[str] = None
    enabled_event_types: List[str]
    min_severity: Optional[str] = None
    batch_size: int = 100
    batch_interval_seconds: int = 60
    enabled: bool = True


class UpdateSIEMConnectionRequest(BaseModel):
    """Request to update SIEM connection."""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    enabled_event_types: Optional[List[str]] = None
    batch_size: Optional[int] = None


class SIEMConnectionResponse(BaseModel):
    """SIEM connection response."""
    connection_id: str
    name: str
    siem_type: str
    endpoint: str
    enabled: bool
    health_status: str
    total_events_sent: int
    total_events_failed: int
    last_successful_export: Optional[str] = None


class SIEMStatisticsResponse(BaseModel):
    """SIEM statistics response."""
    total_events: int
    sent_events: int
    failed_events: int
    pending_events: int
    success_rate: float
    active_connections: int


class ExportEventRequest(BaseModel):
    """Request to export event to SIEM."""
    event_type: str
    event_source: str
    event_data: dict
    connections: Optional[List[str]] = None


# Endpoints

@router.post("/connections", response_model=SIEMConnectionResponse)
async def create_siem_connection(
    request: CreateSIEMConnectionRequest,
    db: Session = Depends(get_db)
):
    """
    Create new SIEM connection.
    
    Args:
        request: Connection configuration
        db: Database session
    
    Returns:
        Created connection details
    """
    manager = SIEMManager(db)
    
    try:
        connection = manager.add_connection(
            name=request.name,
            siem_type=SIEMType(request.siem_type),
            endpoint=request.endpoint,
            port=request.port,
            use_ssl=request.use_ssl,
            verify_ssl=request.verify_ssl,
            auth_type=request.auth_type,
            auth_token=request.auth_token,
            username=request.username,
            password=request.password,
            index_name=request.index_name,
            source_type=request.source_type,
            facility=request.facility,
            enabled_event_types=request.enabled_event_types,
            min_severity=request.min_severity,
            batch_size=request.batch_size,
            batch_interval_seconds=request.batch_interval_seconds,
            enabled=request.enabled
        )
        
        return SIEMConnectionResponse(
            connection_id=connection.connection_id,
            name=connection.name,
            siem_type=connection.siem_type,
            endpoint=connection.endpoint,
            enabled=connection.enabled,
            health_status=connection.health_status,
            total_events_sent=connection.total_events_sent,
            total_events_failed=connection.total_events_failed,
            last_successful_export=(
                connection.last_successful_export.isoformat()
                if connection.last_successful_export else None
            )
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connections", response_model=List[SIEMConnectionResponse])
async def list_siem_connections(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List SIEM connections.
    
    Args:
        enabled_only: Only return enabled connections
        db: Database session
    
    Returns:
        List of connections
    """
    query = db.query(SIEMConnection)
    
    if enabled_only:
        query = query.filter(SIEMConnection.enabled == True)
    
    connections = query.all()
    
    return [
        SIEMConnectionResponse(
            connection_id=c.connection_id,
            name=c.name,
            siem_type=c.siem_type,
            endpoint=c.endpoint,
            enabled=c.enabled,
            health_status=c.health_status,
            total_events_sent=c.total_events_sent,
            total_events_failed=c.total_events_failed,
            last_successful_export=(
                c.last_successful_export.isoformat()
                if c.last_successful_export else None
            )
        )
        for c in connections
    ]


@router.get("/connections/{connection_id}", response_model=SIEMConnectionResponse)
async def get_siem_connection(
    connection_id: str,
    db: Session = Depends(get_db)
):
    """
    Get SIEM connection details.
    
    Args:
        connection_id: Connection ID
        db: Database session
    
    Returns:
        Connection details
    """
    connection = db.query(SIEMConnection).filter(
        SIEMConnection.connection_id == connection_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return SIEMConnectionResponse(
        connection_id=connection.connection_id,
        name=connection.name,
        siem_type=connection.siem_type,
        endpoint=connection.endpoint,
        enabled=connection.enabled,
        health_status=connection.health_status,
        total_events_sent=connection.total_events_sent,
        total_events_failed=connection.total_events_failed,
        last_successful_export=(
            connection.last_successful_export.isoformat()
            if connection.last_successful_export else None
        )
    )


@router.put("/connections/{connection_id}")
async def update_siem_connection(
    connection_id: str,
    request: UpdateSIEMConnectionRequest,
    db: Session = Depends(get_db)
):
    """
    Update SIEM connection.
    
    Args:
        connection_id: Connection ID
        request: Update request
        db: Database session
    
    Returns:
        Success message
    """
    connection = db.query(SIEMConnection).filter(
        SIEMConnection.connection_id == connection_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if request.name is not None:
        connection.name = request.name
    if request.enabled is not None:
        connection.enabled = request.enabled
    if request.enabled_event_types is not None:
        connection.enabled_event_types = request.enabled_event_types
    if request.batch_size is not None:
        connection.batch_size = request.batch_size
    
    connection.updated_at = datetime.now(UTC)
    db.commit()
    
    return {"message": "Connection updated successfully"}


@router.delete("/connections/{connection_id}")
async def delete_siem_connection(
    connection_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete SIEM connection.
    
    Args:
        connection_id: Connection ID
        db: Database session
    
    Returns:
        Success message
    """
    manager = SIEMManager(db)
    
    if manager.remove_connection(connection_id):
        return {"message": "Connection deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Connection not found")


@router.post("/connections/{connection_id}/test")
async def test_siem_connection(
    connection_id: str,
    db: Session = Depends(get_db)
):
    """
    Test SIEM connection health.
    
    Args:
        connection_id: Connection ID
        db: Database session
    
    Returns:
        Health check result
    """
    manager = SIEMManager(db)
    
    if connection_id not in manager.connectors:
        raise HTTPException(status_code=404, detail="Connection not found or not loaded")
    
    connector = manager.connectors[connection_id]
    health = connector.health_check()
    
    return health


@router.post("/export")
async def export_event(
    request: ExportEventRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Export event to SIEM platforms.
    
    Args:
        request: Export request
        background_tasks: FastAPI background tasks
        db: Database session
    
    Returns:
        Export status
    """
    manager = SIEMManager(db)
    
    try:
        event_type = SIEMEventType(request.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")
    
    # Queue events for export
    results = manager.export_event(
        event_type=event_type,
        event_source=request.event_source,
        event_data=request.event_data,
        connections=request.connections
    )
    
    return {
        "message": "Event export initiated",
        "results": results
    }


@router.post("/process-pending")
async def process_pending_events(
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """
    Process pending SIEM events.
    
    Args:
        limit: Maximum events to process
        db: Database session
    
    Returns:
        Processing results
    """
    manager = SIEMManager(db)
    results = manager.process_pending_events(limit=limit)
    
    return {
        "message": "Pending events processed",
        "results": results
    }


@router.post("/retry-failed")
async def retry_failed_events(
    max_age_hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Retry failed SIEM events.
    
    Args:
        max_age_hours: Maximum age of events to retry
        db: Database session
    
    Returns:
        Retry results
    """
    manager = SIEMManager(db)
    results = manager.retry_failed_events(max_age_hours=max_age_hours)
    
    return {
        "message": "Failed events retried",
        "results": results
    }


@router.get("/statistics", response_model=SIEMStatisticsResponse)
async def get_siem_statistics(db: Session = Depends(get_db)):
    """
    Get SIEM export statistics.
    
    Args:
        db: Database session
    
    Returns:
        Statistics
    """
    manager = SIEMManager(db)
    stats = manager.get_statistics()
    
    return SIEMStatisticsResponse(
        total_events=stats["total_events"],
        sent_events=stats["sent_events"],
        failed_events=stats["failed_events"],
        pending_events=stats["pending_events"],
        success_rate=stats["success_rate"],
        active_connections=stats["active_connections"]
    )


@router.get("/health")
async def health_check_all(db: Session = Depends(get_db)):
    """
    Health check all SIEM connections.
    
    Args:
        db: Database session
    
    Returns:
        Health status for all connections
    """
    manager = SIEMManager(db)
    health = manager.health_check_all()
    
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "connections": health
    }

