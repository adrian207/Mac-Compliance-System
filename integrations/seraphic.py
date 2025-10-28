"""
Seraphic Browser Security Integration

Author: Adrian Johnson <adrian207@gmail.com>

Integration with Seraphic for browser-based threat protection,
data loss prevention, and session isolation.
"""

from typing import Any, Dict, List, Optional

from integrations.base import BaseIntegration
from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)


class SeraphicIntegration(BaseIntegration):
    """
    Seraphic browser security integration.
    
    Provides functionality for:
    - Browser-based threat protection
    - Data loss prevention controls
    - Malicious site blocking
    - Session isolation and control
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize Seraphic integration.
        
        Args:
            config: Optional SeraphicConfig object. If None, loads from global config.
        """
        if config is None:
            global_config = get_config()
            config = global_config.seraphic
        
        if not config or not config.enabled:
            raise ValueError("Seraphic integration is not enabled")
        
        super().__init__(
            api_url=config.api_url,
            timeout=config.timeout_seconds,
            retry_attempts=config.retry_attempts
        )
        
        self.api_key = config.api_key
        self.organization_id = config.organization_id
        self.auto_apply_policies = config.auto_apply_policies
        self.isolation_on_high_risk = config.isolation_on_high_risk
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Seraphic API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Organization-ID": self.organization_id,
            "Content-Type": "application/json"
        }
    
    def test_connection(self) -> bool:
        """
        Test connection to Seraphic API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.get("/health")
            logger.info("seraphic_connection_successful")
            return True
        except Exception as e:
            logger.error("seraphic_connection_failed", error=str(e))
            return False
    
    def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get browser sessions for a user.
        
        Args:
            user_id: User identifier
            active_only: Only return active sessions
        
        Returns:
            List of browser sessions
        """
        try:
            params = {
                "userId": user_id,
                "activeOnly": active_only
            }
            
            response = self.get("/sessions", params=params)
            sessions = response.get("sessions", [])
            
            logger.info(
                "seraphic_sessions_retrieved",
                user_id=user_id,
                session_count=len(sessions)
            )
            
            return sessions
        
        except Exception as e:
            logger.error(
                "seraphic_sessions_retrieval_failed",
                user_id=user_id,
                error=str(e)
            )
            return []
    
    def isolate_session(
        self,
        session_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Isolate a browser session.
        
        Args:
            session_id: Session identifier
            reason: Optional reason for isolation
        
        Returns:
            True if isolation successful, False otherwise
        """
        try:
            data = {
                "sessionId": session_id,
                "action": "isolate"
            }
            
            if reason:
                data["reason"] = reason
            
            response = self.post("/sessions/actions", data=data)
            
            logger.info("seraphic_session_isolated", session_id=session_id)
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "seraphic_session_isolation_failed",
                session_id=session_id,
                error=str(e)
            )
            return False
    
    def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a browser session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if termination successful, False otherwise
        """
        try:
            response = self.post(
                "/sessions/actions",
                data={
                    "sessionId": session_id,
                    "action": "terminate"
                }
            )
            
            logger.info("seraphic_session_terminated", session_id=session_id)
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "seraphic_session_termination_failed",
                session_id=session_id,
                error=str(e)
            )
            return False
    
    def apply_policy(
        self,
        user_id: str,
        policy_id: str
    ) -> bool:
        """
        Apply a security policy to a user.
        
        Args:
            user_id: User identifier
            policy_id: Seraphic policy ID
        
        Returns:
            True if policy applied, False otherwise
        """
        try:
            response = self.post(
                f"/users/{user_id}/policies",
                data={"policyId": policy_id}
            )
            
            logger.info(
                "seraphic_policy_applied",
                user_id=user_id,
                policy_id=policy_id
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "seraphic_policy_application_failed",
                user_id=user_id,
                policy_id=policy_id,
                error=str(e)
            )
            return False
    
    def block_url(
        self,
        url: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Block access to a URL.
        
        Args:
            url: URL to block
            user_id: Optional user to apply block to (None for organization-wide)
            reason: Optional reason for blocking
        
        Returns:
            True if URL blocked, False otherwise
        """
        try:
            data = {
                "url": url
            }
            
            if user_id:
                data["userId"] = user_id
            
            if reason:
                data["reason"] = reason
            
            response = self.post("/security/blocklist", data=data)
            
            logger.info(
                "seraphic_url_blocked",
                url=url,
                user_id=user_id or "all"
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "seraphic_url_blocking_failed",
                url=url,
                error=str(e)
            )
            return False
    
    def get_security_events(
        self,
        user_id: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get browser security events.
        
        Args:
            user_id: Optional user identifier to filter events
            hours: Number of hours of history to retrieve
        
        Returns:
            List of security events
        """
        try:
            params = {
                "hours": hours
            }
            
            if user_id:
                params["userId"] = user_id
            
            response = self.get("/security/events", params=params)
            events = response.get("events", [])
            
            logger.info(
                "seraphic_security_events_retrieved",
                user_id=user_id,
                event_count=len(events)
            )
            
            return events
        
        except Exception as e:
            logger.error(
                "seraphic_security_events_retrieval_failed",
                user_id=user_id,
                error=str(e)
            )
            return []
    
    def enable_dlp_protection(
        self,
        user_id: str,
        protection_level: str = "high"
    ) -> bool:
        """
        Enable data loss prevention protection for a user.
        
        Args:
            user_id: User identifier
            protection_level: Protection level (low, medium, high)
        
        Returns:
            True if DLP enabled, False otherwise
        """
        try:
            response = self.post(
                f"/users/{user_id}/dlp",
                data={
                    "enabled": True,
                    "level": protection_level
                }
            )
            
            logger.info(
                "seraphic_dlp_enabled",
                user_id=user_id,
                level=protection_level
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "seraphic_dlp_enable_failed",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    def get_browsing_activity(
        self,
        user_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get browsing activity for a user.
        
        Args:
            user_id: User identifier
            hours: Number of hours of history to retrieve
        
        Returns:
            List of browsing activity records
        """
        try:
            params = {
                "hours": hours
            }
            
            response = self.get(
                f"/users/{user_id}/activity",
                params=params
            )
            
            activity = response.get("records", [])
            
            logger.info(
                "seraphic_activity_retrieved",
                user_id=user_id,
                record_count=len(activity)
            )
            
            return activity
        
        except Exception as e:
            logger.error(
                "seraphic_activity_retrieval_failed",
                user_id=user_id,
                error=str(e)
            )
            return []
    
    def get_threat_detections(
        self,
        user_id: Optional[str] = None,
        severity: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get threat detections.
        
        Args:
            user_id: Optional user identifier to filter detections
            severity: Optional severity filter (low, medium, high, critical)
            hours: Number of hours of history to retrieve
        
        Returns:
            List of threat detections
        """
        try:
            params = {
                "hours": hours
            }
            
            if user_id:
                params["userId"] = user_id
            
            if severity:
                params["severity"] = severity
            
            response = self.get("/security/threats", params=params)
            threats = response.get("threats", [])
            
            logger.info(
                "seraphic_threats_retrieved",
                user_id=user_id,
                threat_count=len(threats)
            )
            
            return threats
        
        except Exception as e:
            logger.error(
                "seraphic_threats_retrieval_failed",
                user_id=user_id,
                error=str(e)
            )
            return []
    
    def configure_risk_based_isolation(
        self,
        user_id: str,
        risk_threshold: str = "high"
    ) -> bool:
        """
        Configure automatic session isolation based on risk.
        
        Args:
            user_id: User identifier
            risk_threshold: Risk threshold for automatic isolation (medium, high, critical)
        
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            response = self.post(
                f"/users/{user_id}/settings/auto-isolation",
                data={
                    "enabled": True,
                    "threshold": risk_threshold
                }
            )
            
            logger.info(
                "seraphic_auto_isolation_configured",
                user_id=user_id,
                threshold=risk_threshold
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "seraphic_auto_isolation_config_failed",
                user_id=user_id,
                error=str(e)
            )
            return False


def get_seraphic_client() -> SeraphicIntegration:
    """
    Get configured Seraphic integration client.
    
    Returns:
        SeraphicIntegration instance
    """
    return SeraphicIntegration()

