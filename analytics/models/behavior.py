"""
Behavioral Analytics Data Models

Author: Adrian Johnson <adrian207@gmail.com>

SQLAlchemy models for behavior tracking, baseline profiling, and anomaly detection.
"""

from datetime import datetime, UTC
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of anomalies detected."""
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    PROCESS = "process"
    FILE_SYSTEM = "file_system"
    SYSTEM_CONFIG = "system_config"
    SOFTWARE = "software"
    USER_BEHAVIOR = "user_behavior"
    SECURITY_EVENT = "security_event"


class BehaviorBaseline(Base):
    """
    Behavior baseline for devices.
    
    Stores statistical baselines for normal device behavior patterns.
    Used as reference for anomaly detection.
    """
    __tablename__ = "behavior_baselines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    baseline_id = Column(String(50), unique=True, nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    
    # Baseline metadata
    baseline_type = Column(String(50), nullable=False)  # e.g., "authentication", "network", "process"
    learning_start = Column(DateTime(timezone=True), nullable=False)
    learning_end = Column(DateTime(timezone=True), nullable=False)
    sample_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)  # 0-100
    
    # Statistical baselines
    mean_values = Column(JSON, nullable=True)  # Mean values for numeric features
    std_dev_values = Column(JSON, nullable=True)  # Standard deviation
    min_values = Column(JSON, nullable=True)  # Minimum observed values
    max_values = Column(JSON, nullable=True)  # Maximum observed values
    percentiles = Column(JSON, nullable=True)  # 25th, 50th, 75th, 95th percentiles
    
    # Categorical baselines
    common_values = Column(JSON, nullable=True)  # Most common categorical values
    value_frequencies = Column(JSON, nullable=True)  # Frequency distributions
    
    # Temporal patterns
    hourly_patterns = Column(JSON, nullable=True)  # Hour-of-day patterns
    daily_patterns = Column(JSON, nullable=True)  # Day-of-week patterns
    
    # Status
    is_active = Column(Boolean, default=True)
    needs_refresh = Column(Boolean, default=False)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    
    # Relationships
    anomalies = relationship("AnomalyDetection", back_populates="baseline")


class BehaviorProfile(Base):
    """
    Device behavior profile.
    
    High-level behavioral profile summarizing device characteristics
    and typical activity patterns.
    """
    __tablename__ = "behavior_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(50), unique=True, nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    
    # Profile metadata
    profile_version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    
    # Device characteristics
    device_type = Column(String(50))  # e.g., "laptop", "desktop", "server"
    user_role = Column(String(50))  # e.g., "executive", "developer", "operations"
    department = Column(String(100))
    
    # Activity patterns
    typical_login_hours = Column(JSON, nullable=True)  # List of typical hours
    typical_login_days = Column(JSON, nullable=True)  # List of typical days
    average_session_duration = Column(Integer)  # Minutes
    
    # Network patterns
    typical_networks = Column(JSON, nullable=True)  # List of common SSIDs/networks
    typical_vpn_usage = Column(Boolean, default=False)
    average_bandwidth_usage = Column(Float)  # MB/day
    
    # Application patterns
    common_applications = Column(JSON, nullable=True)  # Top applications used
    application_diversity = Column(Float)  # Entropy measure
    
    # Process patterns
    typical_process_count = Column(Integer)
    common_processes = Column(JSON, nullable=True)
    
    # Security patterns
    typical_failed_auth_count = Column(Integer, default=0)
    security_tool_usage = Column(JSON, nullable=True)
    
    # Behavior scores
    activity_regularity_score = Column(Float, default=0.0)  # How regular/predictable
    risk_appetite_score = Column(Float, default=0.0)  # Tendency for risky behavior
    
    # Peer group
    peer_group_id = Column(String(50), nullable=True)  # Similar devices for comparison
    
    # Status
    is_complete = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)


class BehaviorPattern(Base):
    """
    Detected behavior patterns.
    
    Stores identified patterns in device behavior for trend analysis
    and pattern matching.
    """
    __tablename__ = "behavior_patterns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(String(50), unique=True, nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    
    # Pattern details
    pattern_type = Column(String(50), nullable=False)  # Type of pattern
    pattern_name = Column(String(200))
    pattern_description = Column(Text)
    
    # Pattern data
    pattern_features = Column(JSON, nullable=False)  # Features defining the pattern
    frequency = Column(Integer, default=1)  # How often pattern occurs
    last_occurrence = Column(DateTime(timezone=True))
    first_occurrence = Column(DateTime(timezone=True))
    
    # Pattern metadata
    confidence = Column(Float, default=0.0)  # Confidence in pattern (0-1)
    is_anomalous = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)  # 0-100
    
    # Status
    is_active = Column(Boolean, default=True)
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class AnomalyDetection(Base):
    """
    Detected anomalies.
    
    Records behavioral anomalies detected through statistical analysis
    or machine learning models.
    """
    __tablename__ = "anomaly_detections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    anomaly_id = Column(String(50), unique=True, nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    
    # Anomaly classification
    anomaly_type = Column(String(50), nullable=False)  # AnomalyType enum value
    anomaly_severity = Column(String(20), nullable=False)  # AnomalySeverity enum value
    
    # Detection details
    detection_method = Column(String(50), nullable=False)  # e.g., "statistical", "ml_model", "rule_based"
    detector_name = Column(String(100))  # Name of detector that found it
    model_version = Column(String(20), nullable=True)  # Version of ML model if applicable
    
    # Anomaly data
    anomaly_score = Column(Float, nullable=False)  # Anomaly score (higher = more anomalous)
    confidence = Column(Float, default=0.0)  # Confidence in detection (0-1)
    
    # Context
    feature_name = Column(String(200))  # Which feature/metric is anomalous
    observed_value = Column(JSON)  # The anomalous value observed
    expected_value = Column(JSON, nullable=True)  # Expected value from baseline
    deviation = Column(Float, nullable=True)  # How far from expected (std devs)
    
    # Description
    title = Column(String(500))
    description = Column(Text)
    recommendations = Column(JSON, nullable=True)  # List of recommended actions
    
    # Related data
    baseline_id = Column(String(50), ForeignKey("behavior_baselines.baseline_id"), nullable=True)
    baseline = relationship("BehaviorBaseline", back_populates="anomalies")
    
    telemetry_snapshot = Column(JSON, nullable=True)  # Snapshot of telemetry at detection time
    
    # Status
    is_confirmed = Column(Boolean, default=False)  # Manually confirmed as real anomaly
    is_false_positive = Column(Boolean, default=False)  # Marked as false positive
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(200), nullable=True)
    
    # Alert status
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime(timezone=True), nullable=True)
    alert_recipients = Column(JSON, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    
    # Notes
    analyst_notes = Column(Text, nullable=True)

