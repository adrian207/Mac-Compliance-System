"""
Telemetry Data Models

Author: Adrian Johnson <adrian207@gmail.com>

Database models for storing device telemetry and security events.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from core.database import BaseModel


class Device(BaseModel):
    """Device inventory and metadata."""
    
    __tablename__ = "devices"
    
    # Identifiers
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    hostname = Column(String(255), nullable=False)
    serial_number = Column(String(255), unique=True, nullable=True)
    uuid = Column(String(255), unique=True, nullable=True)
    
    # Device information
    model = Column(String(255), nullable=True)
    os_version = Column(String(100), nullable=True)
    os_build = Column(String(100), nullable=True)
    cpu_type = Column(String(100), nullable=True)
    total_memory_gb = Column(Float, nullable=True)
    total_disk_gb = Column(Float, nullable=True)
    
    # User information
    primary_user = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    
    # Enrollment and management
    enrollment_status = Column(String(50), nullable=True)
    mdm_enrolled = Column(Boolean, default=False)
    last_check_in = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    
    # Relationships
    telemetry_snapshots = relationship("TelemetrySnapshot", back_populates="device")
    risk_scores = relationship("RiskScore", back_populates="device")
    security_events = relationship("SecurityEvent", back_populates="device")
    compliance_results = relationship("ComplianceResult", back_populates="device")


class TelemetrySnapshot(BaseModel):
    """Point-in-time snapshot of device telemetry."""
    
    __tablename__ = "telemetry_snapshots"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # System information
    uptime_seconds = Column(Integer, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_percent = Column(Float, nullable=True)
    disk_usage_percent = Column(Float, nullable=True)
    
    # Security status
    filevault_enabled = Column(Boolean, nullable=True)
    firewall_enabled = Column(Boolean, nullable=True)
    gatekeeper_enabled = Column(Boolean, nullable=True)
    sip_enabled = Column(Boolean, nullable=True)
    xprotect_version = Column(String(100), nullable=True)
    
    # Network information
    ip_address = Column(String(45), nullable=True)
    mac_address = Column(String(17), nullable=True)
    wifi_ssid = Column(String(255), nullable=True)
    vpn_connected = Column(Boolean, nullable=True)
    
    # Authentication
    screen_lock_enabled = Column(Boolean, nullable=True)
    password_required = Column(Boolean, nullable=True)
    touch_id_enabled = Column(Boolean, nullable=True)
    
    # Software
    installed_software_count = Column(Integer, nullable=True)
    running_processes_count = Column(Integer, nullable=True)
    active_network_connections = Column(Integer, nullable=True)
    
    # Raw data (JSON)
    processes = Column(JSON, nullable=True)
    network_connections = Column(JSON, nullable=True)
    installed_applications = Column(JSON, nullable=True)
    system_extensions = Column(JSON, nullable=True)
    certificates = Column(JSON, nullable=True)
    
    # Metadata
    collection_duration_ms = Column(Integer, nullable=True)
    collection_errors = Column(JSON, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="telemetry_snapshots")


class SecurityEvent(BaseModel):
    """Security-related events detected on devices."""
    
    __tablename__ = "security_events"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    event_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Event classification
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    category = Column(String(100), nullable=True)
    
    # Event details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)
    
    # Detection information
    detection_method = Column(String(255), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Impact and risk
    risk_score_impact = Column(Integer, nullable=True)
    affected_resources = Column(JSON, nullable=True)
    
    # Response
    response_status = Column(String(50), nullable=True)  # detected, investigating, contained, resolved
    automated_actions = Column(JSON, nullable=True)
    
    # Raw event data
    raw_data = Column(JSON, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="security_events")


class ComplianceResult(BaseModel):
    """Device compliance check results."""
    
    __tablename__ = "compliance_results"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    check_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Overall status
    is_compliant = Column(Boolean, default=False, nullable=False, index=True)
    compliance_score = Column(Float, nullable=True)
    total_checks = Column(Integer, nullable=True)
    passed_checks = Column(Integer, nullable=True)
    failed_checks = Column(Integer, nullable=True)
    
    # Detailed results
    check_results = Column(JSON, nullable=True)
    violations = Column(JSON, nullable=True)
    
    # Policy information
    policy_version = Column(String(50), nullable=True)
    policy_name = Column(String(255), nullable=True)
    
    # Remediation
    remediation_required = Column(Boolean, default=False)
    remediation_actions = Column(JSON, nullable=True)
    remediation_status = Column(String(50), nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="compliance_results")


class NetworkConnection(BaseModel):
    """Tracked network connections from devices."""
    
    __tablename__ = "network_connections"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    connection_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Connection details
    process_name = Column(String(255), nullable=True)
    process_id = Column(Integer, nullable=True)
    local_address = Column(String(45), nullable=True)
    local_port = Column(Integer, nullable=True)
    remote_address = Column(String(45), nullable=True, index=True)
    remote_port = Column(Integer, nullable=True)
    protocol = Column(String(10), nullable=True)
    
    # Connection state
    state = Column(String(50), nullable=True)
    bytes_sent = Column(Integer, nullable=True)
    bytes_received = Column(Integer, nullable=True)
    
    # Risk assessment
    is_suspicious = Column(Boolean, default=False, index=True)
    risk_indicators = Column(JSON, nullable=True)
    threat_intel_match = Column(Boolean, default=False)
    
    # Metadata
    duration_seconds = Column(Integer, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)


class SoftwareInventory(BaseModel):
    """Installed software inventory."""
    
    __tablename__ = "software_inventory"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    scan_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Software details
    name = Column(String(255), nullable=False, index=True)
    version = Column(String(100), nullable=True)
    vendor = Column(String(255), nullable=True)
    install_date = Column(DateTime, nullable=True)
    install_path = Column(String(500), nullable=True)
    
    # Security information
    is_signed = Column(Boolean, nullable=True)
    is_notarized = Column(Boolean, nullable=True)
    signing_certificate = Column(String(255), nullable=True)
    
    # Risk assessment
    has_vulnerabilities = Column(Boolean, default=False, index=True)
    vulnerability_count = Column(Integer, default=0)
    vulnerability_details = Column(JSON, nullable=True)
    
    # Compliance
    is_approved = Column(Boolean, nullable=True)
    is_blocked = Column(Boolean, default=False)
    
    # Metadata
    size_bytes = Column(Integer, nullable=True)
    bundle_identifier = Column(String(255), nullable=True)

