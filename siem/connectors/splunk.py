"""
Splunk HTTP Event Collector (HEC) Connector

Author: Adrian Johnson <adrian207@gmail.com>

Connector for sending events to Splunk via HTTP Event Collector.
"""

from datetime import datetime, UTC
from typing import List, Dict, Any
import json

import httpx

from siem.connectors.base import BaseSIEMConnector


class SplunkConnector(BaseSIEMConnector):
    """
    Splunk HTTP Event Collector connector.
    
    Sends events to Splunk using the HEC endpoint.
    Documentation: https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector
    """
    
    def __init__(self, db, connection):
        """Initialize Splunk connector."""
        super().__init__(db, connection)
        
        # Build HEC endpoint URL
        protocol = "https" if connection.use_ssl else "http"
        port = connection.port or 8088
        self.hec_url = f"{protocol}://{connection.endpoint}:{port}/services/collector/event"
        
        # Headers
        self.headers = {
            "Authorization": f"Splunk {connection.auth_token}",
            "Content-Type": "application/json"
        }
        
        # HTTP client
        self.client = httpx.Client(
            verify=connection.verify_ssl,
            timeout=30.0
        )
    
    def connect(self) -> bool:
        """
        Establish connection to Splunk HEC.
        
        Returns:
            True if connection successful
        """
        try:
            return self.test_connection()
        except Exception as e:
            print(f"[ERROR] Splunk connection failed: {e}")
            return False
    
    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send single event to Splunk HEC.
        
        Args:
            event: Event data dictionary
        
        Returns:
            True if sent successfully
        """
        try:
            # Format for Splunk HEC
            hec_event = self._format_for_hec(event)
            
            # Send to Splunk
            response = self.client.post(
                self.hec_url,
                headers=self.headers,
                json=hec_event
            )
            
            # Check response
            if response.status_code == 200:
                return True
            else:
                print(f"[ERROR] Splunk HEC returned {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Failed to send event to Splunk: {e}")
            return False
    
    def send_batch(self, events: List[Dict[str, Any]]) -> tuple[int, int]:
        """
        Send batch of events to Splunk HEC.
        
        Splunk HEC supports multiple events in a single request,
        separated by newlines.
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not events:
            return (0, 0)
        
        try:
            # Format all events for HEC
            hec_events = [self._format_for_hec(event) for event in events]
            
            # Splunk HEC batch format: newline-separated JSON objects
            batch_data = "\n".join(json.dumps(event) for event in hec_events)
            
            # Send batch
            response = self.client.post(
                self.hec_url,
                headers=self.headers,
                content=batch_data
            )
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                
                # Splunk returns {"text":"Success","code":0}
                if response_data.get("code") == 0:
                    return (len(events), 0)
                else:
                    print(f"[WARN] Splunk HEC batch partially failed: {response_data}")
                    return (0, len(events))
            else:
                print(f"[ERROR] Splunk HEC batch failed with {response.status_code}: {response.text}")
                return (0, len(events))
                
        except Exception as e:
            print(f"[ERROR] Failed to send batch to Splunk: {e}")
            return (0, len(events))
    
    def test_connection(self) -> bool:
        """
        Test Splunk HEC connection health.
        
        Sends a test event to verify connectivity and authentication.
        
        Returns:
            True if connection is healthy
        """
        try:
            # Send test event
            test_event = {
                "event": {
                    "message": "ZeroTrust platform health check",
                    "event_type": "health_check"
                },
                "sourcetype": "_json",
                "index": self.connection.index_name or "main"
            }
            
            response = self.client.post(
                self.hec_url,
                headers=self.headers,
                json=test_event
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"[ERROR] Splunk health check failed: {e}")
            return False
    
    def _format_for_hec(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format event for Splunk HEC.
        
        HEC format:
        {
            "time": <epoch time>,
            "host": <host name>,
            "source": <source>,
            "sourcetype": <sourcetype>,
            "index": <index>,
            "event": <event data>
        }
        
        Args:
            event: Event data dictionary
        
        Returns:
            HEC-formatted event
        """
        # Convert timestamp to epoch
        timestamp_str = event.get("timestamp", datetime.now(UTC).isoformat())
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            epoch_time = dt.timestamp()
        except:
            epoch_time = datetime.now(UTC).timestamp()
        
        # Build HEC event
        hec_event = {
            "time": epoch_time,
            "host": event.get("source", "zerotrust-platform"),
            "source": f"zerotrust:{event.get('event_type', 'unknown')}",
            "sourcetype": self.connection.source_type or "_json",
            "event": event
        }
        
        # Add index if configured
        if self.connection.index_name:
            hec_event["index"] = self.connection.index_name
        
        return hec_event
    
    def close(self):
        """Close HTTP client connection."""
        if self.client:
            self.client.close()

