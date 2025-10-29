"""
Reporting API Endpoints

Author: Adrian Johnson <adrian207@gmail.com>

FastAPI endpoints for report generation, retrieval, and management.
"""

from datetime import datetime, UTC
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from reporting.models import Report, ScheduledReport, ReportType, ReportFormat, ReportFrequency
from reporting.generators import (
    ExecutiveDashboardGenerator,
    ComplianceReportGenerator,
    DeviceInventoryGenerator,
    SecurityPostureGenerator,
    RiskTrendGenerator
)
from reporting.exporters import PDFExporter, CSVExporter
from reporting.scheduler import ReportScheduler


# API Router
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


# Request/Response Models
class GenerateReportRequest(BaseModel):
    """Request to generate a report."""
    report_type: str
    report_format: str = "json"
    parameters: Optional[dict] = None
    email_recipients: Optional[list] = None


class ScheduleReportRequest(BaseModel):
    """Request to schedule a report."""
    name: str
    report_type: str
    report_format: str
    frequency: str
    recipients: list
    parameters: Optional[dict] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    enabled: bool = True


class ReportResponse(BaseModel):
    """Report response model."""
    report_id: str
    report_type: str
    report_format: str
    title: str
    status: str
    generated_at: str
    file_path: Optional[str] = None
    data_snapshot: Optional[dict] = None


class ScheduledReportResponse(BaseModel):
    """Scheduled report response model."""
    schedule_id: str
    name: str
    report_type: str
    frequency: str
    enabled: bool
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int


# Endpoints

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate a report on-demand.
    
    Args:
        request: Report generation request
        background_tasks: FastAPI background tasks
        db: Database session
    
    Returns:
        Generated report metadata
    """
    # Select appropriate generator
    generators = {
        "executive_dashboard": ExecutiveDashboardGenerator,
        "compliance": ComplianceReportGenerator,
        "device_inventory": DeviceInventoryGenerator,
        "security_posture": SecurityPostureGenerator,
        "risk_trend": RiskTrendGenerator
    }
    
    generator_class = generators.get(request.report_type)
    if not generator_class:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {request.report_type}")
    
    # Generate report
    generator = generator_class(db)
    report_data = generator.generate(request.parameters)
    
    # Export if format specified
    file_path = None
    if request.report_format == "pdf":
        exporter = PDFExporter()
        file_path = exporter.export(report_data, generator.get_title(request.parameters))
    elif request.report_format == "csv":
        exporter = CSVExporter()
        file_path = exporter.export(report_data, generator.get_title(request.parameters))
    
    # Save report
    report = generator.save_report(
        report_data,
        request.parameters,
        file_path,
        "api"
    )
    
    # Schedule email delivery if recipients provided
    if request.email_recipients:
        background_tasks.add_task(
            _send_report_email,
            db,
            report,
            file_path,
            request.email_recipients
        )
    
    return ReportResponse(
        report_id=report.report_id,
        report_type=report.report_type.value,
        report_format=report.report_format.value,
        title=report.title,
        status=report.status,
        generated_at=report.generated_at.isoformat(),
        file_path=report.file_path,
        data_snapshot=report.data_snapshot
    )


@router.get("/list", response_model=list[ReportResponse])
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List generated reports.
    
    Args:
        report_type: Optional filter by report type
        limit: Maximum number of reports to return
        db: Database session
    
    Returns:
        List of reports
    """
    query = db.query(Report).order_by(Report.generated_at.desc())
    
    if report_type:
        query = query.filter(Report.report_type == report_type)
    
    reports = query.limit(limit).all()
    
    return [
        ReportResponse(
            report_id=r.report_id,
            report_type=r.report_type.value,
            report_format=r.report_format.value,
            title=r.title,
            status=r.status,
            generated_at=r.generated_at.isoformat(),
            file_path=r.file_path,
            data_snapshot=r.data_snapshot
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Get report details.
    
    Args:
        report_id: Report ID
        db: Database session
    
    Returns:
        Report details
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportResponse(
        report_id=report.report_id,
        report_type=report.report_type.value,
        report_format=report.report_format.value,
        title=report.title,
        status=report.status,
        generated_at=report.generated_at.isoformat(),
        file_path=report.file_path,
        data_snapshot=report.data_snapshot
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a report.
    
    Args:
        report_id: Report ID
        db: Database session
    
    Returns:
        Success message
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    db.delete(report)
    db.commit()
    
    return {"message": "Report deleted successfully"}


@router.post("/schedule", response_model=ScheduledReportResponse)
async def schedule_report(
    request: ScheduleReportRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule a recurring report.
    
    Args:
        request: Schedule request
        db: Database session
    
    Returns:
        Scheduled report details
    """
    scheduler = ReportScheduler(db)
    
    scheduled_report = scheduler.create_scheduled_report(
        name=request.name,
        report_type=request.report_type,
        report_format=request.report_format,
        frequency=request.frequency,
        recipients=request.recipients,
        parameters=request.parameters,
        enabled=request.enabled
    )
    
    # Update templates if provided
    if request.subject_template:
        scheduled_report.subject_template = request.subject_template
    if request.body_template:
        scheduled_report.body_template = request.body_template
    
    db.commit()
    
    return ScheduledReportResponse(
        schedule_id=scheduled_report.schedule_id,
        name=scheduled_report.name,
        report_type=scheduled_report.report_type.value,
        frequency=scheduled_report.frequency.value,
        enabled=scheduled_report.enabled,
        last_run_at=scheduled_report.last_run_at.isoformat() if scheduled_report.last_run_at else None,
        next_run_at=scheduled_report.next_run_at.isoformat() if scheduled_report.next_run_at else None,
        run_count=scheduled_report.run_count
    )


@router.get("/schedule/list", response_model=list[ScheduledReportResponse])
async def list_scheduled_reports(
    db: Session = Depends(get_db)
):
    """
    List scheduled reports.
    
    Args:
        db: Database session
    
    Returns:
        List of scheduled reports
    """
    scheduled_reports = db.query(ScheduledReport).all()
    
    return [
        ScheduledReportResponse(
            schedule_id=sr.schedule_id,
            name=sr.name,
            report_type=sr.report_type.value,
            frequency=sr.frequency.value,
            enabled=sr.enabled,
            last_run_at=sr.last_run_at.isoformat() if sr.last_run_at else None,
            next_run_at=sr.next_run_at.isoformat() if sr.next_run_at else None,
            run_count=sr.run_count
        )
        for sr in scheduled_reports
    ]


@router.put("/schedule/{schedule_id}")
async def update_scheduled_report(
    schedule_id: str,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Update scheduled report settings.
    
    Args:
        schedule_id: Schedule ID
        enabled: Enable/disable status
        db: Database session
    
    Returns:
        Updated schedule details
    """
    scheduled_report = db.query(ScheduledReport).filter(
        ScheduledReport.schedule_id == schedule_id
    ).first()
    
    if not scheduled_report:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    
    if enabled is not None:
        scheduled_report.enabled = enabled
    
    db.commit()
    
    return {"message": "Scheduled report updated successfully"}


@router.delete("/schedule/{schedule_id}")
async def delete_scheduled_report(
    schedule_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a scheduled report.
    
    Args:
        schedule_id: Schedule ID
        db: Database session
    
    Returns:
        Success message
    """
    scheduled_report = db.query(ScheduledReport).filter(
        ScheduledReport.schedule_id == schedule_id
    ).first()
    
    if not scheduled_report:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    
    db.delete(scheduled_report)
    db.commit()
    
    return {"message": "Scheduled report deleted successfully"}


# Helper Functions

async def _send_report_email(
    db: Session,
    report: Report,
    file_path: Optional[str],
    recipients: list
):
    """Background task to send report email."""
    from reporting.email_delivery import EmailDelivery
    
    email_delivery = EmailDelivery()
    
    subject = f"Report: {report.title}"
    body = f"""
Your requested report is ready.

Report Type: {report.report_type.value}
Generated: {report.generated_at.isoformat()}

Best regards,
ZeroTrust Platform
    """
    
    attachments = [file_path] if file_path else []
    
    success = email_delivery.send_report(
        recipients=recipients,
        subject=subject,
        body=body,
        attachments=attachments
    )
    
    if success:
        report.delivered = True
        report.delivered_at = datetime.now(UTC)
        report.delivery_recipients = recipients
        db.commit()

