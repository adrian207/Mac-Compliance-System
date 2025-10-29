"""
Report Scheduler

Author: Adrian Johnson <adrian207@gmail.com>

Manages scheduled report generation and delivery.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
import time

from sqlalchemy.orm import Session

from reporting.models import ScheduledReport, Report, ReportFrequency
from reporting.generators import (
    ExecutiveDashboardGenerator,
    ComplianceReportGenerator,
    DeviceInventoryGenerator,
    SecurityPostureGenerator,
    RiskTrendGenerator
)
from reporting.exporters import PDFExporter, CSVExporter
from reporting.email_delivery import EmailDelivery


class ReportScheduler:
    """
    Manages scheduled report generation and delivery.
    
    Runs as a background service to generate and deliver reports on schedule.
    """
    
    def __init__(
        self,
        db: Session,
        email_config: Optional[dict] = None
    ):
        """
        Initialize the report scheduler.
        
        Args:
            db: Database session
            email_config: Email configuration dictionary
        """
        self.db = db
        self.email_delivery = EmailDelivery(**(email_config or {}))
        self.running = False
        
        # Initialize generators
        self.generators = {
            "executive_dashboard": ExecutiveDashboardGenerator(db),
            "compliance": ComplianceReportGenerator(db),
            "device_inventory": DeviceInventoryGenerator(db),
            "security_posture": SecurityPostureGenerator(db),
            "risk_trend": RiskTrendGenerator(db)
        }
        
        # Initialize exporters
        self.pdf_exporter = PDFExporter()
        self.csv_exporter = CSVExporter()
    
    def start(self):
        """Start the scheduler."""
        self.running = True
        print("[INFO] Report scheduler started")
        
        try:
            while self.running:
                self._check_and_run_scheduled_reports()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n[INFO] Stopping report scheduler...")
            self.running = False
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
    
    def _check_and_run_scheduled_reports(self):
        """Check for due scheduled reports and execute them."""
        now = datetime.now(UTC)
        
        # Get scheduled reports that are due
        due_reports = self.db.query(ScheduledReport).filter(
            ScheduledReport.enabled == True,
            ScheduledReport.next_run_at <= now
        ).all()
        
        for scheduled_report in due_reports:
            try:
                print(f"[INFO] Running scheduled report: {scheduled_report.name}")
                self._execute_scheduled_report(scheduled_report)
                
                # Update next run time
                scheduled_report.last_run_at = now
                scheduled_report.last_run_status = "success"
                scheduled_report.next_run_at = self._calculate_next_run(scheduled_report)
                scheduled_report.run_count += 1
                
                self.db.commit()
                
            except Exception as e:
                print(f"[ERROR] Failed to run scheduled report {scheduled_report.name}: {e}")
                scheduled_report.last_run_status = "failed"
                self.db.commit()
    
    def _execute_scheduled_report(self, scheduled_report: ScheduledReport):
        """
        Execute a scheduled report.
        
        Args:
            scheduled_report: Scheduled report configuration
        """
        # Get appropriate generator
        report_type_str = scheduled_report.report_type.value
        generator = self.generators.get(report_type_str)
        
        if not generator:
            raise ValueError(f"Unknown report type: {report_type_str}")
        
        # Generate report
        report_data = generator.generate(scheduled_report.parameters or {})
        
        # Export to file
        file_path = None
        if scheduled_report.report_format.value == "pdf":
            file_path = self.pdf_exporter.export(
                report_data,
                scheduled_report.name
            )
        elif scheduled_report.report_format.value == "csv":
            file_path = self.csv_exporter.export(
                report_data,
                scheduled_report.name
            )
        
        # Save report record
        report = generator.save_report(
            report_data,
            scheduled_report.parameters,
            file_path,
            "scheduler"
        )
        
        # Send email if recipients configured
        if scheduled_report.recipients:
            self._send_report_email(
                scheduled_report,
                report,
                file_path
            )
    
    def _send_report_email(
        self,
        scheduled_report: ScheduledReport,
        report: Report,
        file_path: Optional[str]
    ):
        """
        Send report via email.
        
        Args:
            scheduled_report: Scheduled report configuration
            report: Generated report record
            file_path: Path to exported report file
        """
        # Render email body
        subject = scheduled_report.subject_template or f"Scheduled Report: {scheduled_report.name}"
        
        # Get template variables from report data
        variables = {
            "report_name": scheduled_report.name,
            "generated_at": report.generated_at.isoformat(),
            "report_type": scheduled_report.report_type.value,
            "summary": str(report.data_snapshot)
        }
        
        body = scheduled_report.body_template or self.email_delivery.render_template(
            "scheduled_report",
            variables
        )
        
        # Send email
        attachments = [file_path] if file_path else []
        
        success = self.email_delivery.send_report(
            recipients=scheduled_report.recipients,
            subject=subject,
            body=body,
            attachments=attachments
        )
        
        if success:
            report.delivered = True
            report.delivered_at = datetime.now(UTC)
            report.delivery_recipients = scheduled_report.recipients
            self.db.commit()
            print(f"[INFO] Report emailed to {len(scheduled_report.recipients)} recipients")
        else:
            print(f"[ERROR] Failed to email report")
    
    def _calculate_next_run(self, scheduled_report: ScheduledReport) -> datetime:
        """
        Calculate next run time for scheduled report.
        
        Args:
            scheduled_report: Scheduled report configuration
        
        Returns:
            Next run datetime
        """
        now = datetime.now(UTC)
        
        if scheduled_report.frequency == ReportFrequency.DAILY:
            return now + timedelta(days=1)
        
        elif scheduled_report.frequency == ReportFrequency.WEEKLY:
            return now + timedelta(weeks=1)
        
        elif scheduled_report.frequency == ReportFrequency.MONTHLY:
            # Approximate: 30 days
            return now + timedelta(days=30)
        
        elif scheduled_report.frequency == ReportFrequency.QUARTERLY:
            # Approximate: 90 days
            return now + timedelta(days=90)
        
        else:  # ON_DEMAND
            return now + timedelta(days=365)  # Far future
    
    def create_scheduled_report(
        self,
        name: str,
        report_type: str,
        report_format: str,
        frequency: str,
        recipients: list,
        parameters: Optional[dict] = None,
        enabled: bool = True
    ) -> ScheduledReport:
        """
        Create a new scheduled report.
        
        Args:
            name: Report name
            report_type: Type of report
            report_format: Export format
            frequency: Scheduling frequency
            recipients: Email recipients
            parameters: Report parameters
            enabled: Whether enabled
        
        Returns:
            Created ScheduledReport
        """
        import uuid
        
        scheduled_report = ScheduledReport(
            schedule_id=f"SCH-{uuid.uuid4().hex[:12].upper()}",
            name=name,
            report_type=report_type,
            report_format=report_format,
            frequency=frequency,
            recipients=recipients,
            parameters=parameters or {},
            enabled=enabled,
            next_run_at=datetime.now(UTC),
            created_by="system"
        )
        
        self.db.add(scheduled_report)
        self.db.commit()
        
        return scheduled_report

