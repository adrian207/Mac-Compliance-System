"""
SIEM Integration Data Models

Author: Adrian Johnson <adrian207@gmail.com>

SQLAlchemy models for SIEM configuration and event tracking.
"""

from datetime import datetime, UTC
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text
from core.database import Base


class SIEMType(str, Enum):
    """Supported SIEM types."""
    SPLUNK = "splunk"
    ELASTIC = "elastic"
    QRADAR = "qradar"
    SYSLOG = "syslog"
    CEF = "cef"


class SIEMEventType(str, Enum):
    """Types of events exported to SIEM."""
    ANOMALY = "anomaly"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_CHECK = "compliance_check"
    TELEMETRY = "telemetry"
    WORKFLOW_EXECUTION = "workflow_execution"
    SECURITY_EVENT = "security_event"
    ALERT = "alert"


class SIEMConnection(Base):
    """
    SIEM connection configuration.
    
    Stores configuration for connecting to SIEM platforms.
    """
    __tablename__ = "siem_connections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    siem_type = Column(String(50), nullable=False)  # SIEMType enum value
    
    # Connection details
    endpoint = Column(String(500), nullable=False)
    port = Column(Integer, nullable=True)
    use_ssl = Column(Boolean, default=True)
    verify_ssl = Column(Boolean, default=True)
    
    # Authentication
    auth_type = Column(String(50), nullable=False)  # token, basic, apikey
    auth_token = Column(Text, nullable=True)  # Encrypted token/key
    username = Column(String(200), nullable=True)
    password = Column(Text, nullable=True)  # Encrypted password
    
    # Configuration
    index_name = Column(String(200), nullable=True)  # Splunk/Elastic index
    source_type = Column(String(100), nullable=True)  # Splunk sourcetype
    facility = Column(String(50), nullable=True)  # Syslog facility
    severity_mapping = Column(JSON, nullable=True)  # Custom severity mappings
    
    # Event filtering
    enabled_event_types = Column(JSON, nullable=False)  # List of SIEMEventType
    min_severity = Column(String(20), nullable=True)  # Minimum severity to export
    
    # Batching and performance
    batch_size = Column(Integer, default=100)
    batch_interval_seconds = Column(Integer, default=60)
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=30)
    
    # Status
    enabled = Column(Boolean, default=True)
    health_status = Column(String(50), default="unknown")  # healthy, degraded, failed
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    last_successful_export = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Statistics
    total_events_sent = Column(Integer, default=0)
    total_events_failed = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    created_by = Column(String(200), nullable=True)


class SIEMEvent(Base):
    """
    SIEM event export record.
    
    Tracks events exported to SIEM platforms for auditing and retry.
    """
    __tablename__ = "siem_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    connection_id = Column(String(50), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # SIEMEventType enum value
    event_source = Column(String(100), nullable=False)  # device_id, workflow_id, etc.
    event_data = Column(JSON, nullable=False)
    formatted_data = Column(JSON, nullable=True)  # SIEM-specific format
    
    # Export status
    export_status = Column(String(50), default="pending")  # pending, sent, failed
    export_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    exported_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_after = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        # Index for pending events retry
        # Index for status tracking
    )

