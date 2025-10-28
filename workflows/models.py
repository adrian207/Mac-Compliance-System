"""
Workflow Models

Author: Adrian Johnson <adrian207@gmail.com>

Database models for workflow execution tracking.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from core.database import BaseModel


class WorkflowExecution(BaseModel):
    """Workflow execution tracking."""
    
    __tablename__ = "workflow_executions"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    workflow_name = Column(String(255), nullable=False, index=True)
    trigger_type = Column(String(100), nullable=False)
    trigger_value = Column(String(255), nullable=True)
    
    # Execution status
    status = Column(String(50), nullable=False, index=True)  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Trigger context
    trigger_data = Column(JSON, nullable=True)
    
    # Execution results
    actions_total = Column(Integer, nullable=True)
    actions_successful = Column(Integer, nullable=True)
    actions_failed = Column(Integer, nullable=True)
    
    # Execution details
    execution_log = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    actions = relationship("WorkflowAction", back_populates="execution")


class WorkflowAction(BaseModel):
    """Individual workflow action execution."""
    
    __tablename__ = "workflow_actions"
    
    execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    action_name = Column(String(255), nullable=False)
    
    # Execution
    status = Column(String(50), nullable=False)  # pending, running, completed, failed, skipped
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Action details
    action_params = Column(JSON, nullable=True)
    action_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Dependencies
    depends_on = Column(JSON, nullable=True)
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="actions")


class WorkflowSchedule(BaseModel):
    """Scheduled workflow execution."""
    
    __tablename__ = "workflow_schedules"
    
    workflow_name = Column(String(255), nullable=False)
    schedule_type = Column(String(50), nullable=False)  # cron, interval, once
    schedule_expression = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    
    # Configuration
    workflow_params = Column(JSON, nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Execution tracking
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)


class IncidentTicket(BaseModel):
    """Security incident tickets."""
    
    __tablename__ = "incident_tickets"
    
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=True)
    
    # Ticket details
    ticket_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # Status
    status = Column(String(50), nullable=False, index=True)  # open, investigating, resolved, closed
    assigned_to = Column(String(255), nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # External tracking
    external_ticket_id = Column(String(255), nullable=True)
    external_system = Column(String(100), nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)
    related_events = Column(JSON, nullable=True)

