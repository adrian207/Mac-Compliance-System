"""
Zscaler Network Security Integration

Author: Adrian Johnson <adrian207@gmail.com>

Integration with Zscaler for Zero Trust Network Access (ZTNA),
access token management, and network policy enforcement.
"""

import base64
import time
from typing import Any, Dict, List, Optional

from integrations.base import BaseIntegration
from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)


class ZscalerIntegration(BaseIntegration):
    """
    Zscaler network security integration.
    
    Provides functionality for:
    - Zero Trust Network Access (ZTNA) enforcement
    - Access token management and revocation
    - Network policy application based on device risk
    - Traffic inspection and threat prevention
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize Zscaler integration.
        
        Args:
            config: Optional ZscalerConfig object. If None, loads from global config.
        """
        if config is None:
            global_config = get_config()
            config = global_config.zscaler
        
        if not config or not config.enabled:
            raise ValueError("Zscaler integration is not enabled")
        
        super().__init__(
            api_url=config.api_url,
            timeout=config.timeout_seconds,
            retry_attempts=config.retry_attempts
        )
        
        self.cloud = config.cloud
        self.username = config.username
        self.password = config.password
        self.api_key = config.api_key
        self.ztna_enabled = config.ztna_enabled
        self.auto_revoke_tokens = config.auto_revoke_tokens
        self.apply_policies_by_risk = config.apply_policies_by_risk
        
        # Policy IDs for different risk levels
        self.high_risk_policy_id = config.high_risk_policy_id
        self.medium_risk_policy_id = config.medium_risk_policy_id
        self.low_risk_policy_id = config.low_risk_policy_id
        
        # Authentication session
        self.session_token = None
        self.session_expires = 0
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Zscaler API."""
        # Ensure we have a valid session token
        if not self.session_token or time.time() >= self.session_expires:
            self._authenticate()
        
        return {
            "Authorization": f"Bearer {self.session_token}",
            "Content-Type": "application/json"
        }
    
    def _authenticate(self) -> None:
        """
        Authenticate with Zscaler API and obtain session token.
        
        [Inference] Authentication method may vary based on Zscaler deployment.
        This implementation uses obfuscated API key authentication.
        """
        try:
            # Generate obfuscated API key
            timestamp = str(int(time.time() * 1000))
            key_to_hash = self.api_key + timestamp
            obfuscated_key = self._obfuscate_api_key(key_to_hash)
            
            # Authentication request
            auth_data = {
                "username": self.username,
                "password": self.password,
                "apiKey": obfuscated_key,
                "timestamp": timestamp
            }
            
            response = self.client.post(
                f"{self.api_url}/authenticatedSession",
                json=auth_data
            )
            response.raise_for_status()
            
            result = response.json()
            self.session_token = result.get("sessionToken")
            
            # [Inference] Session typically expires in 30 minutes
            self.session_expires = time.time() + 1800  # 30 minutes
            
            logger.info("zscaler_authentication_successful")
        
        except Exception as e:
            logger.error("zscaler_authentication_failed", error=str(e))
            raise
    
    def _obfuscate_api_key(self, key: str) -> str:
        """
        Obfuscate API key for authentication.
        
        [Inference] This implements Zscaler's API key obfuscation algorithm.
        
        Args:
            key: Key to obfuscate
        
        Returns:
            Obfuscated key
        """
        # Simple obfuscation (actual Zscaler method may differ)
        return base64.b64encode(key.encode()).decode()
    
    def test_connection(self) -> bool:
        """
        Test connection to Zscaler API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._authenticate()
            # Try to get a simple resource
            self.get("/status")
            logger.info("zscaler_connection_successful")
            return True
        except Exception as e:
            logger.error("zscaler_connection_failed", error=str(e))
            return False
    
    def get_user_access_tokens(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get active access tokens for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of access tokens
        """
        try:
            response = self.get(f"/users/{user_id}/tokens")
            tokens = response.get("tokens", [])
            
            logger.info(
                "zscaler_tokens_retrieved",
                user_id=user_id,
                token_count=len(tokens)
            )
            
            return tokens
        
        except Exception as e:
            logger.error(
                "zscaler_tokens_retrieval_failed",
                user_id=user_id,
                error=str(e)
            )
            return []
    
    def revoke_access_token(
        self,
        user_id: str,
        token_id: str
    ) -> bool:
        """
        Revoke a specific access token.
        
        Args:
            user_id: User identifier
            token_id: Token identifier
        
        Returns:
            True if revocation successful, False otherwise
        """
        try:
            response = self.delete(f"/users/{user_id}/tokens/{token_id}")
            
            logger.info(
                "zscaler_token_revoked",
                user_id=user_id,
                token_id=token_id
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "zscaler_token_revocation_failed",
                user_id=user_id,
                token_id=token_id,
                error=str(e)
            )
            return False
    
    def revoke_all_user_tokens(self, user_id: str) -> bool:
        """
        Revoke all access tokens for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if all tokens revoked, False otherwise
        """
        tokens = self.get_user_access_tokens(user_id)
        
        if not tokens:
            logger.info("zscaler_no_tokens_to_revoke", user_id=user_id)
            return True
        
        success = True
        for token in tokens:
            token_id = token.get("id")
            if not self.revoke_access_token(user_id, token_id):
                success = False
        
        return success
    
    def force_reauthentication(self, user_id: str) -> bool:
        """
        Force user to re-authenticate.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if re-authentication forced, False otherwise
        """
        try:
            response = self.post(
                f"/users/{user_id}/actions/force_reauth",
                data={}
            )
            
            logger.info("zscaler_reauth_forced", user_id=user_id)
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "zscaler_reauth_failed",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    def apply_access_policy(
        self,
        user_id: str,
        policy_id: str
    ) -> bool:
        """
        Apply an access policy to a user.
        
        Args:
            user_id: User identifier
            policy_id: Zscaler policy ID
        
        Returns:
            True if policy applied, False otherwise
        """
        try:
            response = self.post(
                f"/users/{user_id}/policies",
                data={"policyId": policy_id}
            )
            
            logger.info(
                "zscaler_policy_applied",
                user_id=user_id,
                policy_id=policy_id
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "zscaler_policy_application_failed",
                user_id=user_id,
                policy_id=policy_id,
                error=str(e)
            )
            return False
    
    def apply_risk_based_policy(
        self,
        user_id: str,
        risk_level: str
    ) -> bool:
        """
        Apply access policy based on device risk level.
        
        Args:
            user_id: User identifier
            risk_level: Risk level (low, medium, high, critical)
        
        Returns:
            True if policy applied, False otherwise
        """
        if not self.apply_policies_by_risk:
            logger.info("zscaler_risk_based_policies_disabled")
            return False
        
        # Map risk level to policy ID
        policy_map = {
            "critical": self.high_risk_policy_id,
            "high": self.high_risk_policy_id,
            "medium": self.medium_risk_policy_id,
            "low": self.low_risk_policy_id,
        }
        
        policy_id = policy_map.get(risk_level)
        
        if not policy_id:
            logger.warning(
                "zscaler_no_policy_for_risk_level",
                risk_level=risk_level
            )
            return False
        
        return self.apply_access_policy(user_id, policy_id)
    
    def isolate_user(self, user_id: str) -> bool:
        """
        Isolate user to quarantine network segment.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if isolation successful, False otherwise
        """
        try:
            response = self.post(
                f"/users/{user_id}/actions/isolate",
                data={}
            )
            
            logger.warning("zscaler_user_isolated", user_id=user_id)
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "zscaler_user_isolation_failed",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    def remove_isolation(self, user_id: str) -> bool:
        """
        Remove user from network isolation.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if removal successful, False otherwise
        """
        try:
            response = self.post(
                f"/users/{user_id}/actions/remove_isolation",
                data={}
            )
            
            logger.info("zscaler_isolation_removed", user_id=user_id)
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "zscaler_isolation_removal_failed",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    def get_user_network_activity(
        self,
        user_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get network activity logs for a user.
        
        Args:
            user_id: User identifier
            hours: Number of hours of history to retrieve
        
        Returns:
            List of network activity records
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
                "zscaler_activity_retrieved",
                user_id=user_id,
                record_count=len(activity)
            )
            
            return activity
        
        except Exception as e:
            logger.error(
                "zscaler_activity_retrieval_failed",
                user_id=user_id,
                error=str(e)
            )
            return []
    
    def get_security_events(
        self,
        user_id: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get security events from Zscaler.
        
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
                "zscaler_security_events_retrieved",
                event_count=len(events)
            )
            
            return events
        
        except Exception as e:
            logger.error(
                "zscaler_security_events_retrieval_failed",
                error=str(e)
            )
            return []
    
    def block_url(self, url: str, reason: str) -> bool:
        """
        Add URL to block list.
        
        Args:
            url: URL to block
            reason: Reason for blocking
        
        Returns:
            True if URL blocked, False otherwise
        """
        try:
            response = self.post(
                "/security/blocklist",
                data={
                    "url": url,
                    "reason": reason
                }
            )
            
            logger.info("zscaler_url_blocked", url=url)
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "zscaler_url_blocking_failed",
                url=url,
                error=str(e)
            )
            return False


def get_zscaler_client() -> ZscalerIntegration:
    """
    Get configured Zscaler integration client.
    
    Returns:
        ZscalerIntegration instance
    """
    return ZscalerIntegration()

