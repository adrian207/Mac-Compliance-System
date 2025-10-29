"""
Integration Data Models

Author: Adrian Johnson <adrian207@gmail.com>

SQLAlchemy models for security tool integrations.
"""

from datetime import datetime, UTC
from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, Float
from sqlalchemy.orm import relationship
from core.database import Base


class IntegrationType(str, Enum):
    """Integration type enumeration."""
    KANDJI = "kandji"
    ZSCALER = "zscaler"
    SERAPHIC = "seraphic"
    OKTA = "okta"
    CROWDSTRIKE = "crowdstrike"


class SyncStatus(str, Enum):
    """Sync status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Integration(Base):
    """
    Security tool integration configuration.
    
    Stores connection details and settings for external security tools.
    """
    __tablename__ = "integrations"
    
    # Primary key
    integration_id = Column(String(50), primary_key=True)
    
    # Integration details
    name = Column(String(200), nullable=False)
    integration_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    # Connection details
    endpoint = Column(String(500), nullable=False)
    api_version = Column(String(20), nullable=True)
    region = Column(String(50), nullable=True)
    
    # Authentication
    auth_type = Column(String(50), nullable=False)  # bearer, api_key, oauth2, basic
    api_key = Column(String(500), nullable=True)
    api_secret = Column(String(500), nullable=True)
    client_id = Column(String(200), nullable=True)
    client_secret = Column(String(500), nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Configuration
    sync_enabled = Column(Boolean, default=True)
    sync_interval_minutes = Column(Integer, default=15)
    webhook_enabled = Column(Boolean, default=False)
    webhook_secret = Column(String(200), nullable=True)
    
    # Features enabled
    features = Column(JSON, default=dict)  # Feature flags per integration
    
    # Sync settings
    sync_devices = Column(Boolean, default=True)
    sync_users = Column(Boolean, default=True)
    sync_policies = Column(Boolean, default=True)
    sync_events = Column(Boolean, default=True)
    
    # Bidirectional sync
    push_compliance = Column(Boolean, default=False)
    push_risk_scores = Column(Boolean, default=False)
    push_policies = Column(Boolean, default=False)
    
    # Rate limiting
    rate_limit_requests = Column(Integer, default=100)
    rate_limit_period_seconds = Column(Integer, default=60)
    
    # Status
    enabled = Column(Boolean, default=True)
    health_status = Column(String(20), default="unknown")
    last_health_check = Column(DateTime, nullable=True)
    
    # Statistics
    total_syncs = Column(Integer, default=0)
    successful_syncs = Column(Integer, default=0)
    failed_syncs = Column(Integer, default=0)
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(20), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    created_by = Column(String(100), default="system")
    
    def __repr__(self):
        return f"<Integration {self.name} ({self.integration_type})>"


class IntegrationSync(Base):
    """
    Integration sync history and status.
    
    Tracks sync operations with external systems.
    """
    __tablename__ = "integration_syncs"
    
    # Primary key
    sync_id = Column(String(50), primary_key=True)
    
    # Integration reference
    integration_id = Column(String(50), nullable=False)
    integration_type = Column(String(50), nullable=False)
    
    # Sync details
    sync_type = Column(String(50), nullable=False)  # full, incremental, devices, users, policies, events
    sync_direction = Column(String(20), nullable=False)  # pull, push, bidirectional
    
    # Status
    status = Column(String(20), nullable=False, default="pending")
    
    # Timing
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results
    items_processed = Column(Integer, default=0)
    items_created = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_deleted = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Data
    sync_data = Column(JSON, nullable=True)  # Summary of synced data
    
    # Metadata
    triggered_by = Column(String(100), default="system")
    
    def __repr__(self):
        return f"<IntegrationSync {self.sync_id} ({self.status})>"


class IntegrationEvent(Base):
    """
    Events received from integrations via webhooks or polling.
    
    Stores external events for processing.
    """
    __tablename__ = "integration_events"
    
    # Primary key
    event_id = Column(String(50), primary_key=True)
    
    # Integration reference
    integration_id = Column(String(50), nullable=False)
    integration_type = Column(String(50), nullable=False)
    
    # Event details
    external_event_id = Column(String(200), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(50), nullable=True)
    
    # Source
    source = Column(String(200), nullable=True)  # Device ID, user ID, etc.
    source_type = Column(String(50), nullable=True)  # device, user, policy, etc.
    
    # Event data
    event_data = Column(JSON, nullable=False)
    severity = Column(String(20), nullable=True)
    
    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    processing_result = Column(JSON, nullable=True)
    
    # Delivery method
    delivery_method = Column(String(20), nullable=False)  # webhook, poll, push
    
    # Timestamps
    event_timestamp = Column(DateTime, nullable=False)
    received_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    def __repr__(self):
        return f"<IntegrationEvent {self.event_id} ({self.event_type})>"


class IntegrationMapping(Base):
    """
    Maps platform entities to external system entities.
    
    Maintains relationships between internal and external IDs.
    """
    __tablename__ = "integration_mappings"
    
    # Primary key
    mapping_id = Column(String(50), primary_key=True)
    
    # Integration reference
    integration_id = Column(String(50), nullable=False)
    integration_type = Column(String(50), nullable=False)
    
    # Platform entity
    platform_entity_type = Column(String(50), nullable=False)  # device, user, policy
    platform_entity_id = Column(String(100), nullable=False)
    
    # External entity
    external_entity_type = Column(String(50), nullable=False)
    external_entity_id = Column(String(200), nullable=False)
    external_entity_name = Column(String(300), nullable=True)
    
    # Mapping metadata
    mapping_data = Column(JSON, nullable=True)  # Additional mapping context
    
    # Status
    active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    def __repr__(self):
        return f"<IntegrationMapping {self.platform_entity_id} -> {self.external_entity_id}>"

