"""
Risk Assessment Models

Author: Adrian Johnson <adrian207@gmail.com>

Database models for device risk scores and risk factors.
"""

from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship

from core.database import BaseModel


class RiskScore(BaseModel):
    """Device risk score calculation results."""
    
    __tablename__ = "risk_scores"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    assessment_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Overall risk score (0-100)
    total_risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    
    # Component scores (0-100)
    security_posture_score = Column(Float, nullable=True)
    compliance_score = Column(Float, nullable=True)
    behavioral_score = Column(Float, nullable=True)
    threat_indicator_score = Column(Float, nullable=True)
    
    # Weighted contributions
    security_posture_weight = Column(Float, nullable=True)
    compliance_weight = Column(Float, nullable=True)
    behavioral_weight = Column(Float, nullable=True)
    threat_indicator_weight = Column(Float, nullable=True)
    
    # Risk factors
    risk_factors = Column(JSON, nullable=True)
    high_risk_factors = Column(JSON, nullable=True)
    
    # Mitigation recommendations
    recommendations = Column(JSON, nullable=True)
    
    # Previous score comparison
    previous_score = Column(Float, nullable=True)
    score_change = Column(Float, nullable=True)
    score_trend = Column(String(20), nullable=True)  # improving, degrading, stable
    
    # Metadata
    assessment_version = Column(String(50), nullable=True)
    calculation_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="risk_scores")


class RiskFactor(BaseModel):
    """Individual risk factors contributing to overall risk."""
    
    __tablename__ = "risk_factors"
    
    risk_score_id = Column(Integer, ForeignKey("risk_scores.id"), nullable=False, index=True)
    
    # Factor identification
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    factor_name = Column(String(255), nullable=False)
    
    # Impact
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    impact_score = Column(Float, nullable=False)
    weight = Column(Float, nullable=True)
    
    # Details
    description = Column(Text, nullable=True)
    current_value = Column(String(255), nullable=True)
    expected_value = Column(String(255), nullable=True)
    
    # Remediation
    remediation_available = Column(String(50), nullable=True)
    remediation_priority = Column(String(20), nullable=True)
    remediation_effort = Column(String(20), nullable=True)
    
    # Metadata
    detection_time = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)


class RiskTrend(BaseModel):
    """Historical risk trends and analytics."""
    
    __tablename__ = "risk_trends"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    trend_date = Column(DateTime, nullable=False, index=True)
    
    # Daily statistics
    min_risk_score = Column(Float, nullable=True)
    max_risk_score = Column(Float, nullable=True)
    avg_risk_score = Column(Float, nullable=True)
    median_risk_score = Column(Float, nullable=True)
    
    # Risk level distribution
    time_in_low_risk = Column(Integer, nullable=True)  # minutes
    time_in_medium_risk = Column(Integer, nullable=True)
    time_in_high_risk = Column(Integer, nullable=True)
    time_in_critical_risk = Column(Integer, nullable=True)
    
    # Events
    risk_level_changes = Column(Integer, nullable=True)
    high_risk_incidents = Column(Integer, nullable=True)
    
    # Factors
    top_risk_factors = Column(JSON, nullable=True)
    resolved_factors = Column(JSON, nullable=True)
    new_factors = Column(JSON, nullable=True)

