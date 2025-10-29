"""
SIEM Manager

Author: Adrian Johnson <adrian207@gmail.com>

Manages SIEM connections and coordinates event export.
"""

from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
import uuid

from sqlalchemy.orm import Session

from siem.models import SIEMConnection, SIEMEvent, SIEMType, SIEMEventType
from siem.connectors import SplunkConnector, ElasticConnector, SyslogConnector, BaseSIEMConnector


class SIEMManager:
    """
    Manages SIEM integrations and event export.
    
    Coordinates multiple SIEM connections and handles event queuing, batching,
    and retry logic.
    """
    
    def __init__(self, db: Session):
        """
        Initialize SIEM manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self.connectors: Dict[str, BaseSIEMConnector] = {}
        
        # Load active connections
        self._load_connections()
    
    def _load_connections(self):
        """Load active SIEM connections and initialize connectors."""
        connections = self.db.query(SIEMConnection).filter(
            SIEMConnection.enabled == True
        ).all()
        
        for connection in connections:
            try:
                connector = self._create_connector(connection)
                if connector:
                    self.connectors[connection.connection_id] = connector
                    print(f"[INFO] Loaded SIEM connector: {connection.name} ({connection.siem_type})")
            except Exception as e:
                print(f"[ERROR] Failed to load connector {connection.name}: {e}")
    
    def _create_connector(self, connection: SIEMConnection) -> Optional[BaseSIEMConnector]:
        """
        Create connector instance for SIEM connection.
        
        Args:
            connection: SIEM connection configuration
        
        Returns:
            Connector instance or None
        """
        connector_map = {
            SIEMType.SPLUNK: SplunkConnector,
            SIEMType.ELASTIC: ElasticConnector,
            SIEMType.SYSLOG: SyslogConnector,
            SIEMType.CEF: SyslogConnector  # CEF uses SyslogConnector
        }
        
        connector_class = connector_map.get(connection.siem_type)
        if not connector_class:
            print(f"[WARN] Unknown SIEM type: {connection.siem_type}")
            return None
        
        return connector_class(self.db, connection)
    
    def export_event(
        self,
        event_type: SIEMEventType,
        event_source: str,
        event_data: Dict[str, Any],
        connections: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Export event to SIEM platforms.
        
        Args:
            event_type: Type of event
            event_source: Source identifier (device_id, workflow_id, etc.)
            event_data: Event data dictionary
            connections: Optional list of connection_ids to export to (all if None)
        
        Returns:
            Dictionary of connection_id -> success status
        """
        # Queue event for export
        siem_events = self._queue_event(event_type, event_source, event_data, connections)
        
        # Export immediately (or could be done asynchronously)
        results = {}
        for siem_event in siem_events:
            connector = self.connectors.get(siem_event.connection_id)
            if connector:
                success = connector.send_event(siem_event.event_data)
                results[siem_event.connection_id] = success
                
                # Update status
                if success:
                    siem_event.export_status = "sent"
                    siem_event.exported_at = datetime.now(UTC)
                else:
                    siem_event.export_status = "failed"
                    siem_event.export_attempts += 1
                
                siem_event.last_attempt_at = datetime.now(UTC)
                self.db.commit()
        
        return results
    
    def _queue_event(
        self,
        event_type: SIEMEventType,
        event_source: str,
        event_data: Dict[str, Any],
        connections: Optional[List[str]] = None
    ) -> List[SIEMEvent]:
        """
        Queue event for export to SIEM platforms.
        
        Args:
            event_type: Type of event
            event_source: Source identifier
            event_data: Event data
            connections: Optional list of connection_ids
        
        Returns:
            List of created SIEMEvent objects
        """
        # Determine which connections to export to
        if connections:
            target_connections = [
                self.db.query(SIEMConnection).filter(
                    SIEMConnection.connection_id == conn_id,
                    SIEMConnection.enabled == True
                ).first()
                for conn_id in connections
            ]
            target_connections = [c for c in target_connections if c]
        else:
            # Export to all enabled connections that accept this event type
            target_connections = self.db.query(SIEMConnection).filter(
                SIEMConnection.enabled == True
            ).all()
        
        # Filter by event type
        target_connections = [
            c for c in target_connections
            if event_type.value in c.enabled_event_types
        ]
        
        # Create SIEM events
        siem_events = []
        for connection in target_connections:
            siem_event = SIEMEvent(
                event_id=f"SIEM-{uuid.uuid4().hex[:12].upper()}",
                connection_id=connection.connection_id,
                event_type=event_type.value,
                event_source=event_source,
                event_data=event_data,
                export_status="pending"
            )
            self.db.add(siem_event)
            siem_events.append(siem_event)
        
        self.db.commit()
        return siem_events
    
    def process_pending_events(self, limit: int = 1000) -> Dict[str, tuple[int, int]]:
        """
        Process pending events for export.
        
        Args:
            limit: Maximum number of events to process
        
        Returns:
            Dictionary of connection_id -> (successful, failed) counts
        """
        results = {}
        
        # Get pending events grouped by connection
        pending_events = self.db.query(SIEMEvent).filter(
            SIEMEvent.export_status == "pending"
        ).order_by(SIEMEvent.created_at).limit(limit).all()
        
        # Group by connection
        events_by_connection: Dict[str, List[SIEMEvent]] = {}
        for event in pending_events:
            if event.connection_id not in events_by_connection:
                events_by_connection[event.connection_id] = []
            events_by_connection[event.connection_id].append(event)
        
        # Export by connection
        for connection_id, events in events_by_connection.items():
            connector = self.connectors.get(connection_id)
            if connector:
                successful, failed = connector.export_events(events)
                results[connection_id] = (successful, failed)
                print(f"[INFO] Exported {successful} events to {connection_id}, {failed} failed")
        
        return results
    
    def retry_failed_events(self, max_age_hours: int = 24) -> Dict[str, tuple[int, int]]:
        """
        Retry failed events that are eligible for retry.
        
        Args:
            max_age_hours: Maximum age of events to retry (default: 24 hours)
        
        Returns:
            Dictionary of connection_id -> (successful, failed) counts
        """
        results = {}
        
        # Get failed events ready for retry
        cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
        
        failed_events = self.db.query(SIEMEvent).filter(
            SIEMEvent.export_status == "failed",
            SIEMEvent.created_at >= cutoff_time,
            SIEMEvent.export_attempts < 3  # Max retries from connection config
        ).all()
        
        # Filter by retry_after time
        retry_ready = [
            e for e in failed_events
            if not e.retry_after or datetime.now(UTC) >= e.retry_after
        ]
        
        # Group by connection
        events_by_connection: Dict[str, List[SIEMEvent]] = {}
        for event in retry_ready:
            if event.connection_id not in events_by_connection:
                events_by_connection[event.connection_id] = []
            events_by_connection[event.connection_id].append(event)
        
        # Retry by connection
        for connection_id, events in events_by_connection.items():
            connector = self.connectors.get(connection_id)
            if connector:
                # Reset status to pending for retry
                for event in events:
                    event.export_status = "pending"
                self.db.commit()
                
                # Export
                successful, failed = connector.export_events(events)
                results[connection_id] = (successful, failed)
                print(f"[INFO] Retried {len(events)} events to {connection_id}: {successful} succeeded, {failed} failed")
        
        return results
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all SIEM connections.
        
        Returns:
            Dictionary of connection_id -> health status
        """
        results = {}
        
        for connection_id, connector in self.connectors.items():
            health = connector.health_check()
            results[connection_id] = health
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get SIEM export statistics.
        
        Returns:
            Statistics dictionary
        """
        # Overall statistics
        total_events = self.db.query(SIEMEvent).count()
        sent_events = self.db.query(SIEMEvent).filter(
            SIEMEvent.export_status == "sent"
        ).count()
        failed_events = self.db.query(SIEMEvent).filter(
            SIEMEvent.export_status == "failed"
        ).count()
        pending_events = self.db.query(SIEMEvent).filter(
            SIEMEvent.export_status == "pending"
        ).count()
        
        # Per-connection statistics
        connection_stats = {}
        for connection_id, connector in self.connectors.items():
            connection_stats[connection_id] = connector.get_statistics()
        
        return {
            "total_events": total_events,
            "sent_events": sent_events,
            "failed_events": failed_events,
            "pending_events": pending_events,
            "success_rate": sent_events / total_events if total_events > 0 else 0,
            "active_connections": len(self.connectors),
            "connections": connection_stats
        }
    
    def add_connection(
        self,
        name: str,
        siem_type: SIEMType,
        endpoint: str,
        **kwargs
    ) -> SIEMConnection:
        """
        Add new SIEM connection.
        
        Args:
            name: Connection name
            siem_type: SIEM type
            endpoint: SIEM endpoint
            **kwargs: Additional configuration
        
        Returns:
            Created SIEMConnection
        """
        connection = SIEMConnection(
            connection_id=f"SIEM-CONN-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            siem_type=siem_type.value,
            endpoint=endpoint,
            **kwargs
        )
        
        self.db.add(connection)
        self.db.commit()
        
        # Initialize connector
        connector = self._create_connector(connection)
        if connector:
            self.connectors[connection.connection_id] = connector
        
        return connection
    
    def remove_connection(self, connection_id: str) -> bool:
        """
        Remove SIEM connection.
        
        Args:
            connection_id: Connection ID
        
        Returns:
            True if removed successfully
        """
        connection = self.db.query(SIEMConnection).filter(
            SIEMConnection.connection_id == connection_id
        ).first()
        
        if connection:
            # Close connector
            if connection_id in self.connectors:
                connector = self.connectors[connection_id]
                if hasattr(connector, 'close'):
                    connector.close()
                del self.connectors[connection_id]
            
            # Delete from database
            self.db.delete(connection)
            self.db.commit()
            return True
        
        return False

