"""
Sync Manager

Author: Adrian Johnson <adrian207@gmail.com>

Orchestrates bidirectional synchronization with external security platforms.
"""

import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List, Optional
import logging
import asyncio
from sqlalchemy.orm import Session

from integrations.models import (
    Integration,
    IntegrationSync,
    IntegrationMapping,
    IntegrationType,
    SyncStatus
)
from integrations.connectors import (
    KandjiConnector,
    ZscalerConnector,
    SeraphicConnector,
    OktaConnector,
    CrowdStrikeConnector
)


logger = logging.getLogger(__name__)


class SyncManager:
    """
    Manages synchronization between platform and external integrations.
    
    Handles both pull (from external systems) and push (to external systems)
    synchronization operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize sync manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self._connectors = {}
    
    def _get_connector(self, integration: Integration):
        """Get or create connector for integration."""
        if integration.integration_id in self._connectors:
            return self._connectors[integration.integration_id]
        
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
    
    async def sync_integration(
        self,
        integration_id: str,
        sync_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Perform synchronization for an integration.
        
        Args:
            integration_id: Integration ID
            sync_type: Type of sync (full, incremental, devices, users, policies)
        
        Returns:
            Sync results
        """
        integration = self.db.query(Integration).filter(
            Integration.integration_id == integration_id
        ).first()
        
        if not integration:
            return {
                "success": False,
                "error": "Integration not found"
            }
        
        if not integration.enabled or not integration.sync_enabled:
            return {
                "success": False,
                "error": "Sync disabled"
            }
        
        # Create sync record
        sync_record = IntegrationSync(
            sync_id=f"SYNC-{uuid.uuid4().hex[:12].upper()}",
            integration_id=integration.integration_id,
            integration_type=integration.integration_type,
            sync_type=sync_type,
            sync_direction="pull",
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.now(UTC)
        )
        
        self.db.add(sync_record)
        self.db.commit()
        
        try:
            # Get connector
            connector = self._get_connector(integration)
            
            # Perform sync based on type
            results = {}
            
            if sync_type == "full":
                results = await connector.full_sync()
            elif sync_type == "devices":
                results["devices"] = await connector.sync_devices()
            elif sync_type == "users":
                results["users"] = await connector.sync_users()
            elif sync_type == "policies":
                results["policies"] = await connector.sync_policies()
            
            # Update sync record
            sync_record.status = SyncStatus.COMPLETED if results.get("success", True) else SyncStatus.FAILED
            sync_record.completed_at = datetime.now(UTC)
            sync_record.duration_seconds = (sync_record.completed_at - sync_record.started_at).total_seconds()
            sync_record.sync_data = results
            
            # Count items
            total_items = 0
            if results.get("devices"):
                total_items += results["devices"].get("devices_synced", 0)
            if results.get("users"):
                total_items += results["users"].get("users_synced", 0)
            if results.get("policies"):
                total_items += results["policies"].get("policies_synced", 0)
            
            sync_record.items_processed = total_items
            sync_record.items_created = total_items  # Simplified
            
            # Update integration stats
            integration.total_syncs += 1
            if sync_record.status == SyncStatus.COMPLETED:
                integration.successful_syncs += 1
            else:
                integration.failed_syncs += 1
            integration.last_sync_at = datetime.now(UTC)
            integration.last_sync_status = sync_record.status
            
            self.db.commit()
            
            return {
                "success": True,
                "sync_id": sync_record.sync_id,
                "results": results
            }
        
        except Exception as e:
            logger.error(f"Sync failed for {integration_id}: {e}", exc_info=True)
            
            # Update sync record
            sync_record.status = SyncStatus.FAILED
            sync_record.completed_at = datetime.now(UTC)
            sync_record.duration_seconds = (sync_record.completed_at - sync_record.started_at).total_seconds()
            sync_record.error_message = str(e)
            
            # Update integration stats
            integration.total_syncs += 1
            integration.failed_syncs += 1
            integration.last_sync_at = datetime.now(UTC)
            integration.last_sync_status = sync_record.status
            
            self.db.commit()
            
            return {
                "success": False,
                "error": str(e),
                "sync_id": sync_record.sync_id
            }
    
    async def sync_all_integrations(self) -> Dict[str, Any]:
        """
        Sync all enabled integrations.
        
        Returns:
            Combined sync results
        """
        integrations = self.db.query(Integration).filter(
            Integration.enabled == True,
            Integration.sync_enabled == True
        ).all()
        
        results = {}
        
        for integration in integrations:
            try:
                result = await self.sync_integration(integration.integration_id)
                results[integration.integration_id] = result
            except Exception as e:
                logger.error(f"Error syncing {integration.integration_id}: {e}")
                results[integration.integration_id] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "total_integrations": len(integrations),
            "results": results
        }
    
    async def push_compliance_status(
        self,
        device_id: str,
        compliance_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Push compliance status to all relevant integrations.
        
        Args:
            device_id: Internal device ID
            compliance_status: Compliance status data
        
        Returns:
            Push results
        """
        # Get integrations with push enabled
        integrations = self.db.query(Integration).filter(
            Integration.enabled == True,
            Integration.push_compliance == True
        ).all()
        
        results = {}
        
        for integration in integrations:
            try:
                # Get device mapping
                mapping = self.db.query(IntegrationMapping).filter(
                    IntegrationMapping.integration_id == integration.integration_id,
                    IntegrationMapping.platform_entity_id == device_id,
                    IntegrationMapping.platform_entity_type == "device"
                ).first()
                
                if not mapping:
                    logger.warning(f"No mapping found for device {device_id} in {integration.integration_id}")
                    continue
                
                # Get connector
                connector = self._get_connector(integration)
                
                # Push compliance
                success = await connector.push_compliance_status(
                    mapping.external_entity_id,
                    compliance_status
                )
                
                results[integration.integration_id] = {
                    "success": success,
                    "external_device_id": mapping.external_entity_id
                }
            
            except Exception as e:
                logger.error(f"Error pushing compliance to {integration.integration_id}: {e}")
                results[integration.integration_id] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def push_risk_score(
        self,
        device_id: str,
        risk_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Push risk score to all relevant integrations.
        
        Args:
            device_id: Internal device ID
            risk_score: Risk score data
        
        Returns:
            Push results
        """
        # Get integrations with push enabled
        integrations = self.db.query(Integration).filter(
            Integration.enabled == True,
            Integration.push_risk_scores == True
        ).all()
        
        results = {}
        
        for integration in integrations:
            try:
                # Get device mapping
                mapping = self.db.query(IntegrationMapping).filter(
                    IntegrationMapping.integration_id == integration.integration_id,
                    IntegrationMapping.platform_entity_id == device_id,
                    IntegrationMapping.platform_entity_type == "device"
                ).first()
                
                if not mapping:
                    continue
                
                # Get connector
                connector = self._get_connector(integration)
                
                # Push risk score
                success = await connector.push_risk_score(
                    mapping.external_entity_id,
                    risk_score
                )
                
                results[integration.integration_id] = {
                    "success": success,
                    "external_device_id": mapping.external_entity_id
                }
            
            except Exception as e:
                logger.error(f"Error pushing risk score to {integration.integration_id}: {e}")
                results[integration.integration_id] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def create_mapping(
        self,
        integration_id: str,
        platform_entity_type: str,
        platform_entity_id: str,
        external_entity_type: str,
        external_entity_id: str,
        external_entity_name: Optional[str] = None
    ) -> IntegrationMapping:
        """
        Create entity mapping between platform and external system.
        
        Args:
            integration_id: Integration ID
            platform_entity_type: Platform entity type
            platform_entity_id: Platform entity ID
            external_entity_type: External entity type
            external_entity_id: External entity ID
            external_entity_name: External entity name
        
        Returns:
            Created mapping
        """
        mapping = IntegrationMapping(
            mapping_id=f"MAP-{uuid.uuid4().hex[:12].upper()}",
            integration_id=integration_id,
            integration_type=self.db.query(Integration).filter(
                Integration.integration_id == integration_id
            ).first().integration_type,
            platform_entity_type=platform_entity_type,
            platform_entity_id=platform_entity_id,
            external_entity_type=external_entity_type,
            external_entity_id=external_entity_id,
            external_entity_name=external_entity_name
        )
        
        self.db.add(mapping)
        self.db.commit()
        
        return mapping
    
    async def scheduled_sync(self):
        """
        Perform scheduled sync for all integrations.
        
        Runs sync for integrations where sync interval has elapsed.
        """
        integrations = self.db.query(Integration).filter(
            Integration.enabled == True,
            Integration.sync_enabled == True
        ).all()
        
        for integration in integrations:
            try:
                # Check if sync is due
                if integration.last_sync_at:
                    next_sync = integration.last_sync_at + timedelta(
                        minutes=integration.sync_interval_minutes
                    )
                    
                    if datetime.now(UTC) < next_sync:
                        continue
                
                # Perform sync
                logger.info(f"Running scheduled sync for {integration.name}")
                await self.sync_integration(integration.integration_id, "full")
            
            except Exception as e:
                logger.error(f"Error in scheduled sync for {integration.integration_id}: {e}")
    
    async def close_all(self):
        """Close all connector connections."""
        for connector in self._connectors.values():
            try:
                await connector.close()
            except Exception as e:
                logger.error(f"Error closing connector: {e}")

