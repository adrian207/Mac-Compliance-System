"""
Reporting Data Models

Author: Adrian Johnson <adrian207@gmail.com>

Database models for storing report metadata and scheduling.
"""

from datetime import datetime, UTC
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, Enum
import enum

from core.database import Base


class ReportType(enum.Enum):
    """Report type enumeration."""
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    COMPLIANCE = "compliance"
    DEVICE_INVENTORY = "device_inventory"
    SECURITY_POSTURE = "security_posture"
    RISK_TREND = "risk_trend"
    CUSTOM = "custom"


class ReportFormat(enum.Enum):
    """Report format enumeration."""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"


class ReportFrequency(enum.Enum):
    """Report scheduling frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ON_DEMAND = "on_demand"


class Report(Base):
    """
    Generated report record.
    
    Stores metadata about generated reports for tracking and retrieval.
    """
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(50), unique=True, nullable=False, index=True)
    report_type = Column(Enum(ReportType), nullable=False, index=True)
    report_format = Column(Enum(ReportFormat), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Generation info
    generated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    generated_by = Column(String(100))  # User or system
    generation_duration_ms = Column(Integer)  # Time to generate in milliseconds
    
    # Report parameters and filters
    parameters = Column(JSON)  # Filters, date ranges, etc.
    
    # Report data
    file_path = Column(String(500))  # Path to generated file
    file_size_bytes = Column(Integer)
    data_snapshot = Column(JSON)  # Key metrics snapshot
    
    # Delivery info
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime)
    delivery_recipients = Column(JSON)  # List of email addresses
    
    # Status
    status = Column(String(20), default="completed")  # completed, failed, generating
    error_message = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(UTC))


class ScheduledReport(Base):
    """
    Scheduled report configuration.
    
    Defines recurring report generation and delivery.
    """
    __tablename__ = "scheduled_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Report configuration
    report_type = Column(Enum(ReportType), nullable=False)
    report_format = Column(Enum(ReportFormat), nullable=False)
    parameters = Column(JSON)  # Default parameters
    
    # Scheduling
    frequency = Column(Enum(ReportFrequency), nullable=False)
    schedule_time = Column(String(10))  # HH:MM format
    schedule_day = Column(Integer)  # Day of week (0-6) or month (1-31)
    timezone = Column(String(50), default="UTC")
    
    # Delivery
    recipients = Column(JSON, nullable=False)  # Email addresses
    subject_template = Column(String(255))
    body_template = Column(Text)
    
    # Status
    enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    last_run_status = Column(String(20))
    next_run_at = Column(DateTime)
    run_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    created_by = Column(String(100))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(UTC))


class RiskScoreHistory(Base):
    """
    Historical risk scores for trend analysis.
    
    Tracks risk score changes over time for devices.
    """
    __tablename__ = "risk_score_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(100), nullable=False, index=True)
    
    # Risk scores
    total_risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)  # critical, high, medium, low
    
    # Score components
    security_posture_score = Column(Integer)
    compliance_score = Column(Integer)
    vulnerability_score = Column(Integer)
    behavior_score = Column(Integer)
    
    # Risk factors
    risk_factors = Column(JSON)  # List of contributing risk factors
    
    # Changes from previous
    score_delta = Column(Integer)  # Change from previous score
    risk_level_changed = Column(Boolean, default=False)
    
    # Metadata
    recorded_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    assessment_id = Column(String(50))  # Link to RiskAssessment if applicable


class ComplianceHistory(Base):
    """
    Historical compliance status for trend analysis.
    
    Tracks compliance status changes over time for devices.
    """
    __tablename__ = "compliance_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(100), nullable=False, index=True)
    
    # Compliance status
    is_compliant = Column(Boolean, nullable=False)
    compliance_score = Column(Integer)  # 0-100
    
    # Policy compliance
    policies_total = Column(Integer)
    policies_passed = Column(Integer)
    policies_failed = Column(Integer)
    policies_warning = Column(Integer)
    
    # Critical failures
    critical_failures = Column(JSON)  # List of critical compliance failures
    
    # Changes from previous
    status_changed = Column(Boolean, default=False)
    newly_failed_policies = Column(JSON)
    newly_passed_policies = Column(JSON)
    
    # Metadata
    recorded_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    check_id = Column(String(50))  # Link to ComplianceCheck if applicable

