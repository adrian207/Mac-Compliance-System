"""
Base SIEM Connector

Author: Adrian Johnson <adrian207@gmail.com>

Abstract base class for SIEM connectors.
"""

from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
import time

from sqlalchemy.orm import Session

from siem.models import SIEMConnection, SIEMEvent


class BaseSIEMConnector(ABC):
    """
    Abstract base class for SIEM connectors.
    
    Provides common functionality for connecting to and exporting events to SIEM platforms.
    """
    
    def __init__(self, db: Session, connection: SIEMConnection):
        """
        Initialize SIEM connector.
        
        Args:
            db: Database session
            connection: SIEM connection configuration
        """
        self.db = db
        self.connection = connection
        self.siem_type = connection.siem_type
        
        # Statistics
        self.stats = {
            "events_sent": 0,
            "events_failed": 0,
            "batches_sent": 0,
            "last_send_time": None
        }
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to SIEM platform.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send single event to SIEM.
        
        Args:
            event: Event data dictionary
        
        Returns:
            True if sent successfully
        """
        pass
    
    @abstractmethod
    def send_batch(self, events: List[Dict[str, Any]]) -> tuple[int, int]:
        """
        Send batch of events to SIEM.
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test SIEM connection health.
        
        Returns:
            True if connection is healthy
        """
        pass
    
    def export_events(
        self,
        events: List[SIEMEvent],
        update_status: bool = True
    ) -> tuple[int, int]:
        """
        Export events to SIEM with retry logic.
        
        Args:
            events: List of SIEMEvent objects
            update_status: Whether to update event status in database
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not events:
            return (0, 0)
        
        # Format events for SIEM
        formatted_events = [self._format_event(event) for event in events]
        
        # Send in batches
        batch_size = self.connection.batch_size
        successful = 0
        failed = 0
        
        for i in range(0, len(formatted_events), batch_size):
            batch = formatted_events[i:i + batch_size]
            siem_event_batch = events[i:i + batch_size]
            
            try:
                success_count, fail_count = self.send_batch(batch)
                successful += success_count
                failed += fail_count
                
                # Update event status
                if update_status:
                    self._update_event_status(
                        siem_event_batch[:success_count],
                        "sent"
                    )
                    if fail_count > 0:
                        self._update_event_status(
                            siem_event_batch[success_count:],
                            "failed"
                        )
                
                # Update statistics
                self.stats["events_sent"] += success_count
                self.stats["events_failed"] += fail_count
                self.stats["batches_sent"] += 1
                self.stats["last_send_time"] = datetime.now(UTC)
                
            except Exception as e:
                print(f"[ERROR] Batch export failed: {e}")
                failed += len(batch)
                
                if update_status:
                    self._update_event_status(siem_event_batch, "failed", str(e))
        
        # Update connection statistics
        self.connection.total_events_sent += successful
        self.connection.total_events_failed += failed
        self.connection.last_successful_export = datetime.now(UTC)
        self.db.commit()
        
        return (successful, failed)
    
    def _format_event(self, event: SIEMEvent) -> Dict[str, Any]:
        """
        Format event for SIEM platform.
        
        Args:
            event: SIEMEvent object
        
        Returns:
            Formatted event dictionary
        """
        # Base event structure
        formatted = {
            "timestamp": event.created_at.isoformat(),
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source": event.event_source,
            "platform": "zerotrust-mac-compliance",
            **event.event_data
        }
        
        return formatted
    
    def _update_event_status(
        self,
        events: List[SIEMEvent],
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Update event export status in database.
        
        Args:
            events: List of SIEMEvent objects
            status: New status (sent, failed, pending)
            error_message: Optional error message
        """
        now = datetime.now(UTC)
        
        for event in events:
            event.export_status = status
            event.export_attempts += 1
            event.last_attempt_at = now
            
            if status == "sent":
                event.exported_at = now
                event.error_message = None
            elif status == "failed":
                event.error_message = error_message
                # Schedule retry
                event.retry_after = now.timestamp() + self.connection.retry_delay_seconds
        
        self.db.commit()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on SIEM connection.
        
        Returns:
            Health status dictionary
        """
        try:
            is_healthy = self.test_connection()
            
            health_status = {
                "healthy": is_healthy,
                "status": "healthy" if is_healthy else "failed",
                "connection_id": self.connection.connection_id,
                "siem_type": self.siem_type,
                "last_check": datetime.now(UTC).isoformat(),
                "statistics": self.stats
            }
            
            # Update connection health
            self.connection.health_status = "healthy" if is_healthy else "failed"
            self.connection.last_health_check = datetime.now(UTC)
            self.db.commit()
            
            return health_status
            
        except Exception as e:
            self.connection.health_status = "failed"
            self.connection.last_error = str(e)
            self.connection.last_health_check = datetime.now(UTC)
            self.db.commit()
            
            return {
                "healthy": False,
                "status": "failed",
                "connection_id": self.connection.connection_id,
                "error": str(e),
                "last_check": datetime.now(UTC).isoformat()
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get connector statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "connection_id": self.connection.connection_id,
            "siem_type": self.siem_type,
            "total_events_sent": self.connection.total_events_sent,
            "total_events_failed": self.connection.total_events_failed,
            "success_rate": (
                self.connection.total_events_sent / 
                (self.connection.total_events_sent + self.connection.total_events_failed)
                if (self.connection.total_events_sent + self.connection.total_events_failed) > 0
                else 0
            ),
            "health_status": self.connection.health_status,
            "last_successful_export": (
                self.connection.last_successful_export.isoformat()
                if self.connection.last_successful_export else None
            ),
            "session_stats": self.stats
        }

