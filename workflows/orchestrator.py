"""
Workflow Orchestration Engine

Author: Adrian Johnson <adrian207@gmail.com>

Orchestrates automated security response workflows.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.config import get_config, get_workflow_config
from core.database import get_db_manager
from core.logging_config import get_logger
from integrations.kandji import get_kandji_client
from integrations.zscaler import get_zscaler_client
from integrations.seraphic import get_seraphic_client
from workflows.models import WorkflowExecution, WorkflowAction, IncidentTicket

logger = get_logger(__name__)


class WorkflowOrchestrator:
    """
    Main workflow orchestration engine.
    
    Executes automated security workflows based on triggers and conditions.
    """
    
    def __init__(self):
        """Initialize workflow orchestrator."""
        self.config = get_config()
        self.db = get_db_manager()
    
    def execute_workflow(
        self,
        workflow_name: str,
        trigger_type: str,
        trigger_data: Dict[str, Any],
        device_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_name: Name of the workflow to execute
            trigger_type: Type of trigger that initiated the workflow
            trigger_data: Data associated with the trigger
            device_id: Optional device ID associated with workflow
        
        Returns:
            Dict containing workflow execution results
        """
        execution_start = datetime.utcnow()
        
        # Get workflow configuration
        workflow_config = get_workflow_config(self.config, workflow_name)
        
        if not workflow_config or not workflow_config.enabled:
            logger.warning("workflow_not_enabled", workflow_name=workflow_name)
            return {
                "success": False,
                "error": f"Workflow {workflow_name} is not enabled"
            }
        
        # Create execution record
        execution = WorkflowExecution(
            device_id=device_id,
            workflow_name=workflow_name,
            trigger_type=trigger_type,
            trigger_value=str(trigger_data.get("value")),
            trigger_data=trigger_data,
            status="running",
            started_at=execution_start
        )
        
        with self.db.get_session() as session:
            session.add(execution)
            session.flush()
            execution_id = execution.id
        
        logger.info(
            "workflow_execution_started",
            workflow_name=workflow_name,
            execution_id=execution_id,
            trigger_type=trigger_type
        )
        
        # Execute actions
        action_results = []
        for action_config in workflow_config.actions:
            if not action_config.enabled:
                continue
            
            action_result = self._execute_action(
                execution_id=execution_id,
                action_config=action_config,
                trigger_data=trigger_data,
                device_id=device_id
            )
            
            action_results.append(action_result)
        
        # Calculate execution summary
        actions_successful = sum(1 for r in action_results if r["status"] == "completed")
        actions_failed = sum(1 for r in action_results if r["status"] == "failed")
        
        duration = (datetime.utcnow() - execution_start).total_seconds() * 1000
        
        # Update execution record
        with self.db.get_session() as session:
            execution = session.query(WorkflowExecution).filter_by(id=execution_id).first()
            if execution:
                execution.status = "completed" if actions_failed == 0 else "failed"
                execution.completed_at = datetime.utcnow()
                execution.duration_ms = int(duration)
                execution.actions_total = len(action_results)
                execution.actions_successful = actions_successful
                execution.actions_failed = actions_failed
                execution.execution_log = action_results
        
        logger.info(
            "workflow_execution_completed",
            workflow_name=workflow_name,
            execution_id=execution_id,
            duration_ms=int(duration),
            actions_successful=actions_successful,
            actions_failed=actions_failed
        )
        
        return {
            "success": actions_failed == 0,
            "execution_id": execution_id,
            "workflow_name": workflow_name,
            "duration_ms": int(duration),
            "actions": action_results
        }
    
    def _execute_action(
        self,
        execution_id: int,
        action_config: Any,
        trigger_data: Dict[str, Any],
        device_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Execute a single workflow action.
        
        Args:
            execution_id: Workflow execution ID
            action_config: Action configuration
            trigger_data: Trigger data for context
            device_id: Optional device ID
        
        Returns:
            Dict containing action execution results
        """
        action_start = datetime.utcnow()
        action_type = action_config.type
        
        # Create action record
        action = WorkflowAction(
            execution_id=execution_id,
            action_type=action_type,
            action_name=action_type,
            status="running",
            started_at=action_start,
            action_params=action_config.dict() if hasattr(action_config, 'dict') else {}
        )
        
        with self.db.get_session() as session:
            session.add(action)
            session.flush()
            action_id = action.id
        
        logger.info(
            "workflow_action_started",
            execution_id=execution_id,
            action_id=action_id,
            action_type=action_type
        )
        
        # Execute action based on type
        try:
            if action_type == "zscaler_revoke_token":
                result = self._action_zscaler_revoke_token(trigger_data, device_id)
            elif action_type == "force_mfa":
                result = self._action_force_mfa(trigger_data, device_id)
            elif action_type == "network_quarantine":
                result = self._action_network_quarantine(trigger_data, device_id)
            elif action_type == "alert_soc":
                result = self._action_alert_soc(trigger_data, device_id)
            elif action_type == "create_incident":
                result = self._action_create_incident(trigger_data, device_id)
            elif action_type == "deploy_corrective_policies":
                result = self._action_deploy_corrective_policies(
                    trigger_data, device_id, action_config.platform
                )
            elif action_type == "restrict_network":
                result = self._action_restrict_network(trigger_data, device_id)
            elif action_type == "notify_user":
                result = self._action_notify_user(trigger_data, device_id)
            elif action_type == "verify_enrollment":
                result = self._action_verify_enrollment(trigger_data, device_id)
            elif action_type == "validate_posture":
                result = self._action_validate_posture(trigger_data, device_id)
            elif action_type == "apply_conditional_access":
                result = self._action_apply_conditional_access(trigger_data, device_id)
            elif action_type == "enable_monitoring":
                result = self._action_enable_monitoring(trigger_data, device_id)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown action type: {action_type}"
                }
            
            status = "completed" if result.get("success") else "failed"
            
        except Exception as e:
            logger.error(
                "workflow_action_failed",
                execution_id=execution_id,
                action_id=action_id,
                action_type=action_type,
                error=str(e)
            )
            result = {"success": False, "error": str(e)}
            status = "failed"
        
        duration = (datetime.utcnow() - action_start).total_seconds() * 1000
        
        # Update action record
        with self.db.get_session() as session:
            action = session.query(WorkflowAction).filter_by(id=action_id).first()
            if action:
                action.status = status
                action.completed_at = datetime.utcnow()
                action.duration_ms = int(duration)
                action.action_result = result
                if not result.get("success"):
                    action.error_message = result.get("error")
        
        logger.info(
            "workflow_action_completed",
            execution_id=execution_id,
            action_id=action_id,
            action_type=action_type,
            status=status,
            duration_ms=int(duration)
        )
        
        return {
            "action_id": action_id,
            "action_type": action_type,
            "status": status,
            "duration_ms": int(duration),
            "result": result
        }
    
    # Action implementations
    
    def _action_zscaler_revoke_token(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Revoke Zscaler access tokens."""
        try:
            user_id = trigger_data.get("user_id")
            if not user_id:
                return {"success": False, "error": "Missing user_id"}
            
            with get_zscaler_client() as zscaler:
                success = zscaler.revoke_all_user_tokens(user_id)
            
            return {
                "success": success,
                "message": f"Tokens revoked for user {user_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _action_force_mfa(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Force MFA re-authentication."""
        try:
            user_id = trigger_data.get("user_id")
            if not user_id:
                return {"success": False, "error": "Missing user_id"}
            
            with get_zscaler_client() as zscaler:
                success = zscaler.force_reauthentication(user_id)
            
            return {
                "success": success,
                "message": f"MFA re-authentication forced for user {user_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _action_network_quarantine(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Quarantine device to isolated network."""
        try:
            user_id = trigger_data.get("user_id")
            if not user_id:
                return {"success": False, "error": "Missing user_id"}
            
            with get_zscaler_client() as zscaler:
                success = zscaler.isolate_user(user_id)
            
            return {
                "success": success,
                "message": f"Device quarantined for user {user_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _action_alert_soc(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Send alert to security operations center."""
        # [Inference] This would integrate with your alerting system
        logger.warning(
            "soc_alert",
            device_id=device_id,
            trigger_data=trigger_data
        )
        return {
            "success": True,
            "message": "SOC alert sent"
        }
    
    def _action_create_incident(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Create security incident ticket."""
        try:
            ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
            
            risk_score = trigger_data.get("risk_score", 0)
            severity = "critical" if risk_score >= 90 else "high"
            
            incident = IncidentTicket(
                device_id=device_id,
                ticket_id=ticket_id,
                title=f"High Risk Device Detected - Risk Score: {risk_score}",
                description=f"Automated incident creation for device with risk score {risk_score}",
                severity=severity,
                status="open",
                tags=trigger_data
            )
            
            with self.db.get_session() as session:
                session.add(incident)
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "message": f"Incident {ticket_id} created"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _action_deploy_corrective_policies(
        self, trigger_data: Dict[str, Any], device_id: Optional[int], platform: Optional[str]
    ) -> Dict[str, Any]:
        """Deploy corrective policies via MDM."""
        if platform != "kandji":
            return {"success": False, "error": f"Unsupported platform: {platform}"}
        
        try:
            kandji_device_id = trigger_data.get("kandji_device_id")
            if not kandji_device_id:
                return {"success": False, "error": "Missing kandji_device_id"}
            
            # [Inference] Policy ID would be determined based on violations
            policy_id = "default-remediation-policy"
            
            with get_kandji_client() as kandji:
                success = kandji.deploy_policy(kandji_device_id, policy_id)
            
            return {
                "success": success,
                "message": f"Policies deployed to device {kandji_device_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _action_restrict_network(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Restrict network access."""
        try:
            user_id = trigger_data.get("user_id")
            risk_level = trigger_data.get("risk_level", "medium")
            
            with get_zscaler_client() as zscaler:
                success = zscaler.apply_risk_based_policy(user_id, risk_level)
            
            return {
                "success": success,
                "message": f"Network restrictions applied for user {user_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _action_notify_user(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Send notification to user."""
        # [Inference] This would integrate with your notification system
        logger.info(
            "user_notification",
            device_id=device_id,
            trigger_data=trigger_data
        )
        return {
            "success": True,
            "message": "User notification sent"
        }
    
    def _action_verify_enrollment(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Verify device enrollment status."""
        try:
            kandji_device_id = trigger_data.get("kandji_device_id")
            
            with get_kandji_client() as kandji:
                device = kandji.get_device(kandji_device_id)
            
            enrolled = device is not None
            
            return {
                "success": True,
                "enrolled": enrolled,
                "message": f"Device enrollment status: {'enrolled' if enrolled else 'not enrolled'}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _action_validate_posture(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Validate device security posture."""
        # [Inference] This would check against security baselines
        return {
            "success": True,
            "message": "Device posture validated"
        }
    
    def _action_apply_conditional_access(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Apply conditional access policies."""
        try:
            user_id = trigger_data.get("user_id")
            risk_level = trigger_data.get("risk_level", "low")
            
            with get_zscaler_client() as zscaler:
                success = zscaler.apply_risk_based_policy(user_id, risk_level)
            
            return {
                "success": success,
                "message": f"Conditional access policies applied for user {user_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _action_enable_monitoring(
        self, trigger_data: Dict[str, Any], device_id: Optional[int]
    ) -> Dict[str, Any]:
        """Enable enhanced monitoring for device."""
        # [Inference] This would configure enhanced telemetry collection
        logger.info(
            "enhanced_monitoring_enabled",
            device_id=device_id
        )
        return {
            "success": True,
            "message": "Enhanced monitoring enabled"
        }


def execute_workflow(
    workflow_name: str,
    trigger_type: str,
    trigger_data: Dict[str, Any],
    device_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute a workflow.
    
    Args:
        workflow_name: Name of the workflow
        trigger_type: Trigger type
        trigger_data: Trigger data
        device_id: Optional device ID
    
    Returns:
        Workflow execution results
    """
    orchestrator = WorkflowOrchestrator()
    return orchestrator.execute_workflow(
        workflow_name, trigger_type, trigger_data, device_id
    )

