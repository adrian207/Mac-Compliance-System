"""
Integration API Endpoints

Author: Adrian Johnson <adrian207@gmail.com>

FastAPI endpoints for integration management, sync, and webhooks.
"""

from datetime import datetime, UTC
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from integrations.models import (
    Integration,
    IntegrationSync,
    IntegrationEvent,
    IntegrationType
)
from integrations.sync import SyncManager
from integrations.webhooks import WebhookHandler


# API Router
router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


# Request/Response Models
class CreateIntegrationRequest(BaseModel):
    """Request to create integration."""
    name: str
    integration_type: str
    description: Optional[str] = None
    endpoint: str
    api_version: Optional[str] = None
    region: Optional[str] = None
    auth_type: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    sync_enabled: bool = True
    sync_interval_minutes: int = 15
    webhook_enabled: bool = False
    webhook_secret: Optional[str] = None
    sync_devices: bool = True
    sync_users: bool = True
    sync_policies: bool = True
    push_compliance: bool = False
    push_risk_scores: bool = False
    enabled: bool = True


class UpdateIntegrationRequest(BaseModel):
    """Request to update integration."""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None
    webhook_enabled: Optional[bool] = None
    sync_devices: Optional[bool] = None
    sync_users: Optional[bool] = None
    sync_policies: Optional[bool] = None
    push_compliance: Optional[bool] = None
    push_risk_scores: Optional[bool] = None


class IntegrationResponse(BaseModel):
    """Integration response."""
    integration_id: str
    name: str
    integration_type: str
    endpoint: str
    enabled: bool
    sync_enabled: bool
    webhook_enabled: bool
    health_status: str
    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    last_sync_at: Optional[str] = None


class SyncResponse(BaseModel):
    """Sync response."""
    sync_id: str
    integration_id: str
    sync_type: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    items_processed: int


# Endpoints

@router.post("/", response_model=IntegrationResponse)
async def create_integration(
    request: CreateIntegrationRequest,
    db: Session = Depends(get_db)
):
    """
    Create new integration.
    
    Args:
        request: Integration configuration
        db: Database session
    
    Returns:
        Created integration
    """
    import uuid
    
    integration = Integration(
        integration_id=f"INT-{uuid.uuid4().hex[:12].upper()}",
        name=request.name,
        integration_type=request.integration_type,
        description=request.description,
        endpoint=request.endpoint,
        api_version=request.api_version,
        region=request.region,
        auth_type=request.auth_type,
        api_key=request.api_key,
        api_secret=request.api_secret,
        client_id=request.client_id,
        client_secret=request.client_secret,
        sync_enabled=request.sync_enabled,
        sync_interval_minutes=request.sync_interval_minutes,
        webhook_enabled=request.webhook_enabled,
        webhook_secret=request.webhook_secret,
        sync_devices=request.sync_devices,
        sync_users=request.sync_users,
        sync_policies=request.sync_policies,
        push_compliance=request.push_compliance,
        push_risk_scores=request.push_risk_scores,
        enabled=request.enabled
    )
    
    db.add(integration)
    db.commit()
    db.refresh(integration)
    
    return IntegrationResponse(
        integration_id=integration.integration_id,
        name=integration.name,
        integration_type=integration.integration_type,
        endpoint=integration.endpoint,
        enabled=integration.enabled,
        sync_enabled=integration.sync_enabled,
        webhook_enabled=integration.webhook_enabled,
        health_status=integration.health_status,
        total_syncs=integration.total_syncs,
        successful_syncs=integration.successful_syncs,
        failed_syncs=integration.failed_syncs,
        last_sync_at=(
            integration.last_sync_at.isoformat()
            if integration.last_sync_at else None
        )
    )


@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List integrations.
    
    Args:
        enabled_only: Only return enabled integrations
        db: Database session
    
    Returns:
        List of integrations
    """
    query = db.query(Integration)
    
    if enabled_only:
        query = query.filter(Integration.enabled == True)
    
    integrations = query.all()
    
    return [
        IntegrationResponse(
            integration_id=i.integration_id,
            name=i.name,
            integration_type=i.integration_type,
            endpoint=i.endpoint,
            enabled=i.enabled,
            sync_enabled=i.sync_enabled,
            webhook_enabled=i.webhook_enabled,
            health_status=i.health_status,
            total_syncs=i.total_syncs,
            successful_syncs=i.successful_syncs,
            failed_syncs=i.failed_syncs,
            last_sync_at=i.last_sync_at.isoformat() if i.last_sync_at else None
        )
        for i in integrations
    ]


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    db: Session = Depends(get_db)
):
    """
    Get integration details.
    
    Args:
        integration_id: Integration ID
        db: Database session
    
    Returns:
        Integration details
    """
    integration = db.query(Integration).filter(
        Integration.integration_id == integration_id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return IntegrationResponse(
        integration_id=integration.integration_id,
        name=integration.name,
        integration_type=integration.integration_type,
        endpoint=integration.endpoint,
        enabled=integration.enabled,
        sync_enabled=integration.sync_enabled,
        webhook_enabled=integration.webhook_enabled,
        health_status=integration.health_status,
        total_syncs=integration.total_syncs,
        successful_syncs=integration.successful_syncs,
        failed_syncs=integration.failed_syncs,
        last_sync_at=(
            integration.last_sync_at.isoformat()
            if integration.last_sync_at else None
        )
    )


@router.put("/{integration_id}")
async def update_integration(
    integration_id: str,
    request: UpdateIntegrationRequest,
    db: Session = Depends(get_db)
):
    """
    Update integration.
    
    Args:
        integration_id: Integration ID
        request: Update request
        db: Database session
    
    Returns:
        Success message
    """
    integration = db.query(Integration).filter(
        Integration.integration_id == integration_id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if request.name is not None:
        integration.name = request.name
    if request.enabled is not None:
        integration.enabled = request.enabled
    if request.sync_enabled is not None:
        integration.sync_enabled = request.sync_enabled
    if request.sync_interval_minutes is not None:
        integration.sync_interval_minutes = request.sync_interval_minutes
    if request.webhook_enabled is not None:
        integration.webhook_enabled = request.webhook_enabled
    if request.sync_devices is not None:
        integration.sync_devices = request.sync_devices
    if request.sync_users is not None:
        integration.sync_users = request.sync_users
    if request.sync_policies is not None:
        integration.sync_policies = request.sync_policies
    if request.push_compliance is not None:
        integration.push_compliance = request.push_compliance
    if request.push_risk_scores is not None:
        integration.push_risk_scores = request.push_risk_scores
    
    integration.updated_at = datetime.now(UTC)
    db.commit()
    
    return {"message": "Integration updated successfully"}


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete integration.
    
    Args:
        integration_id: Integration ID
        db: Database session
    
    Returns:
        Success message
    """
    integration = db.query(Integration).filter(
        Integration.integration_id == integration_id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    db.delete(integration)
    db.commit()
    
    return {"message": "Integration deleted successfully"}


@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: str,
    db: Session = Depends(get_db)
):
    """
    Test integration connection.
    
    Args:
        integration_id: Integration ID
        db: Database session
    
    Returns:
        Test results
    """
    integration = db.query(Integration).filter(
        Integration.integration_id == integration_id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    manager = SyncManager(db)
    connector = manager._get_connector(integration)
    
    result = await connector.test_connection()
    
    # Update health status
    integration.health_status = "healthy" if result.get("success") else "unhealthy"
    integration.last_health_check = datetime.now(UTC)
    db.commit()
    
    return result


@router.post("/{integration_id}/sync")
async def sync_integration(
    integration_id: str,
    sync_type: str = "full",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Trigger sync for integration.
    
    Args:
        integration_id: Integration ID
        sync_type: Sync type (full, devices, users, policies)
        background_tasks: Background tasks
        db: Database session
    
    Returns:
        Sync initiated message
    """
    integration = db.query(Integration).filter(
        Integration.integration_id == integration_id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    manager = SyncManager(db)
    
    # Run sync in background
    background_tasks.add_task(manager.sync_integration, integration_id, sync_type)
    
    return {
        "message": "Sync initiated",
        "integration_id": integration_id,
        "sync_type": sync_type
    }


@router.post("/sync-all")
async def sync_all_integrations(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger sync for all integrations.
    
    Args:
        background_tasks: Background tasks
        db: Database session
    
    Returns:
        Sync initiated message
    """
    manager = SyncManager(db)
    
    # Run sync in background
    background_tasks.add_task(manager.sync_all_integrations)
    
    return {"message": "Sync initiated for all integrations"}


@router.get("/{integration_id}/syncs", response_model=List[SyncResponse])
async def get_sync_history(
    integration_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get sync history for integration.
    
    Args:
        integration_id: Integration ID
        limit: Maximum syncs to return
        db: Database session
    
    Returns:
        List of syncs
    """
    syncs = db.query(IntegrationSync).filter(
        IntegrationSync.integration_id == integration_id
    ).order_by(
        IntegrationSync.started_at.desc()
    ).limit(limit).all()
    
    return [
        SyncResponse(
            sync_id=s.sync_id,
            integration_id=s.integration_id,
            sync_type=s.sync_type,
            status=s.status,
            started_at=s.started_at.isoformat(),
            completed_at=s.completed_at.isoformat() if s.completed_at else None,
            items_processed=s.items_processed
        )
        for s in syncs
    ]


@router.post("/webhooks/{integration_id}")
async def receive_webhook(
    integration_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive webhook from external integration.
    
    Args:
        integration_id: Integration ID
        request: Request object
        db: Database session
    
    Returns:
        Processing result
    """
    # Get raw body
    body = await request.body()
    
    # Parse JSON
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Get headers
    headers = dict(request.headers)
    
    # Process webhook
    handler = WebhookHandler(db)
    result = await handler.handle_webhook(
        integration_id=integration_id,
        payload=payload,
        headers=headers,
        raw_payload=body
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/{integration_id}/events")
async def get_integration_events(
    integration_id: str,
    limit: int = 100,
    processed_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get events for integration.
    
    Args:
        integration_id: Integration ID
        limit: Maximum events to return
        processed_only: Only return processed events
        db: Database session
    
    Returns:
        List of events
    """
    query = db.query(IntegrationEvent).filter(
        IntegrationEvent.integration_id == integration_id
    )
    
    if processed_only:
        query = query.filter(IntegrationEvent.processed == True)
    
    events = query.order_by(
        IntegrationEvent.received_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "event_id": e.event_id,
            "event_type": e.event_type,
            "source": e.source,
            "severity": e.severity,
            "processed": e.processed,
            "received_at": e.received_at.isoformat()
        }
        for e in events
    ]


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get integration statistics.
    
    Args:
        db: Database session
    
    Returns:
        Statistics
    """
    total_integrations = db.query(Integration).count()
    enabled_integrations = db.query(Integration).filter(
        Integration.enabled == True
    ).count()
    
    total_syncs = db.query(IntegrationSync).count()
    successful_syncs = db.query(IntegrationSync).filter(
        IntegrationSync.status == "completed"
    ).count()
    
    total_events = db.query(IntegrationEvent).count()
    processed_events = db.query(IntegrationEvent).filter(
        IntegrationEvent.processed == True
    ).count()
    
    return {
        "total_integrations": total_integrations,
        "enabled_integrations": enabled_integrations,
        "total_syncs": total_syncs,
        "successful_syncs": successful_syncs,
        "sync_success_rate": (
            successful_syncs / total_syncs if total_syncs > 0 else 0
        ),
        "total_events": total_events,
        "processed_events": processed_events
    }

