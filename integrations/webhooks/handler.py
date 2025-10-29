"""
Webhook Handler

Author: Adrian Johnson <adrian207@gmail.com>

Processes webhooks from external security platforms.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional
import logging
from sqlalchemy.orm import Session

from integrations.models import Integration, IntegrationEvent, IntegrationType
from integrations.connectors import (
    KandjiConnector,
    ZscalerConnector,
    SeraphicConnector,
    OktaConnector,
    CrowdStrikeConnector
)


logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handles webhooks from external integrations.
    
    Routes webhook payloads to appropriate connectors and stores events.
    """
    
    def __init__(self, db: Session):
        """
        Initialize webhook handler.
        
        Args:
            db: Database session
        """
        self.db = db
        self._connectors = {}
    
    def _get_connector(self, integration: Integration):
        """
        Get or create connector for integration.
        
        Args:
            integration: Integration configuration
        
        Returns:
            Integration connector instance
        """
        if integration.integration_id in self._connectors:
            return self._connectors[integration.integration_id]
        
        # Create connector based on type
        connector_map = {
            IntegrationType.KANDJI: KandjiConnector,
            IntegrationType.ZSCALER: ZscalerConnector,
            IntegrationType.SERAPHIC: SeraphicConnector,
            IntegrationType.OKTA: OktaConnector,
            IntegrationType.CROWDSTRIKE: CrowdStrikeConnector
        }
        
        connector_class = connector_map.get(IntegrationType(integration.integration_type))
        if not connector_class:
            raise ValueError(f"Unknown integration type: {integration.integration_type}")
        
        connector = connector_class(integration)
        self._connectors[integration.integration_id] = connector
        
        return connector
    
    async def handle_webhook(
        self,
        integration_id: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        raw_payload: bytes
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook.
        
        Args:
            integration_id: Integration ID
            payload: Webhook payload (parsed JSON)
            headers: Request headers
            raw_payload: Raw request body
        
        Returns:
            Processing result
        """
        # Get integration
        integration = self.db.query(Integration).filter(
            Integration.integration_id == integration_id
        ).first()
        
        if not integration:
            logger.error(f"Integration not found: {integration_id}")
            return {
                "success": False,
                "error": "Integration not found"
            }
        
        if not integration.enabled:
            logger.warning(f"Integration disabled: {integration_id}")
            return {
                "success": False,
                "error": "Integration disabled"
            }
        
        if not integration.webhook_enabled:
            logger.warning(f"Webhooks not enabled for integration: {integration_id}")
            return {
                "success": False,
                "error": "Webhooks not enabled"
            }
        
        try:
            # Get connector
            connector = self._get_connector(integration)
            
            # Validate webhook signature if configured
            if integration.webhook_secret:
                signature = headers.get("X-Signature") or headers.get("X-Hub-Signature-256")
                
                if not signature:
                    logger.error("Webhook signature missing")
                    return {
                        "success": False,
                        "error": "Signature missing"
                    }
                
                if not connector.validate_webhook_signature(raw_payload, signature):
                    logger.error("Invalid webhook signature")
                    return {
                        "success": False,
                        "error": "Invalid signature"
                    }
            
            # Process webhook
            processed = connector.process_webhook(payload, headers)
            
            # Store event
            event = self._store_event(
                integration=integration,
                payload=payload,
                processed_data=processed
            )
            
            return {
                "success": True,
                "event_id": event.event_id,
                "processed": processed
            }
        
        except Exception as e:
            logger.error(f"Error handling webhook: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _store_event(
        self,
        integration: Integration,
        payload: Dict[str, Any],
        processed_data: Dict[str, Any]
    ) -> IntegrationEvent:
        """
        Store webhook event in database.
        
        Args:
            integration: Integration configuration
            payload: Raw payload
            processed_data: Processed event data
        
        Returns:
            Stored event
        """
        event = IntegrationEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:12].upper()}",
            integration_id=integration.integration_id,
            integration_type=integration.integration_type,
            external_event_id=payload.get("event_id") or payload.get("id"),
            event_type=processed_data.get("event_type", "unknown"),
            event_category=self._categorize_event(processed_data.get("event_type")),
            source=processed_data.get("device_id") or processed_data.get("user_id"),
            source_type=self._determine_source_type(processed_data),
            event_data=payload,
            severity=processed_data.get("severity", "info"),
            processed=processed_data.get("processed", False),
            processing_result=processed_data,
            delivery_method="webhook",
            event_timestamp=self._parse_timestamp(payload),
            received_at=datetime.now(UTC)
        )
        
        self.db.add(event)
        self.db.commit()
        
        return event
    
    def _categorize_event(self, event_type: Optional[str]) -> str:
        """
        Categorize event type.
        
        Args:
            event_type: Event type string
        
        Returns:
            Category string
        """
        if not event_type:
            return "other"
        
        event_type_lower = event_type.lower()
        
        if any(x in event_type_lower for x in ["threat", "detection", "malware", "ransomware"]):
            return "security"
        elif any(x in event_type_lower for x in ["auth", "login", "sso", "session"]):
            return "authentication"
        elif any(x in event_type_lower for x in ["device", "endpoint", "host"]):
            return "device"
        elif any(x in event_type_lower for x in ["compliance", "policy", "violation"]):
            return "compliance"
        elif any(x in event_type_lower for x in ["user", "identity"]):
            return "identity"
        else:
            return "other"
    
    def _determine_source_type(self, processed_data: Dict[str, Any]) -> str:
        """
        Determine source type from processed data.
        
        Args:
            processed_data: Processed event data
        
        Returns:
            Source type string
        """
        if processed_data.get("device_id"):
            return "device"
        elif processed_data.get("user_id") or processed_data.get("user_email"):
            return "user"
        elif processed_data.get("policy_id"):
            return "policy"
        else:
            return "unknown"
    
    def _parse_timestamp(self, payload: Dict[str, Any]) -> datetime:
        """
        Parse timestamp from payload.
        
        Args:
            payload: Webhook payload
        
        Returns:
            Parsed timestamp
        """
        timestamp_fields = ["timestamp", "event_timestamp", "created_at", "occurred_at"]
        
        for field in timestamp_fields:
            if field in payload:
                try:
                    from dateutil import parser
                    return parser.parse(payload[field])
                except:
                    pass
        
        return datetime.now(UTC)
    
    async def close_all(self):
        """Close all connector connections."""
        for connector in self._connectors.values():
            try:
                await connector.close()
            except Exception as e:
                logger.error(f"Error closing connector: {e}")

