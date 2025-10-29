"""
Elastic Stack (Elasticsearch) Connector

Author: Adrian Johnson <adrian207@gmail.com>

Connector for sending events to Elasticsearch.
"""

from datetime import datetime, UTC
from typing import List, Dict, Any
import json

import httpx

from siem.connectors.base import BaseSIEMConnector


class ElasticConnector(BaseSIEMConnector):
    """
    Elasticsearch connector.
    
    Sends events to Elasticsearch using the Bulk API.
    Documentation: https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html
    """
    
    def __init__(self, db, connection):
        """Initialize Elastic connector."""
        super().__init__(db, connection)
        
        # Build Elasticsearch URL
        protocol = "https" if connection.use_ssl else "http"
        port = connection.port or 9200
        self.base_url = f"{protocol}://{connection.endpoint}:{port}"
        self.bulk_url = f"{self.base_url}/_bulk"
        self.health_url = f"{self.base_url}/_cluster/health"
        
        # Index name
        self.index_name = connection.index_name or "zerotrust-events"
        
        # Headers
        self.headers = {
            "Content-Type": "application/x-ndjson"  # Bulk API requires ndjson
        }
        
        # Authentication
        auth = None
        if connection.auth_type == "basic" and connection.username and connection.password:
            auth = (connection.username, connection.password)
        elif connection.auth_type == "apikey" and connection.auth_token:
            self.headers["Authorization"] = f"ApiKey {connection.auth_token}"
        
        # HTTP client
        self.client = httpx.Client(
            auth=auth,
            verify=connection.verify_ssl,
            timeout=30.0
        )
    
    def connect(self) -> bool:
        """
        Establish connection to Elasticsearch.
        
        Returns:
            True if connection successful
        """
        try:
            return self.test_connection()
        except Exception as e:
            print(f"[ERROR] Elasticsearch connection failed: {e}")
            return False
    
    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send single event to Elasticsearch.
        
        Args:
            event: Event data dictionary
        
        Returns:
            True if sent successfully
        """
        try:
            # Use bulk API even for single event
            return self.send_batch([event])[0] == 1
                
        except Exception as e:
            print(f"[ERROR] Failed to send event to Elasticsearch: {e}")
            return False
    
    def send_batch(self, events: List[Dict[str, Any]]) -> tuple[int, int]:
        """
        Send batch of events to Elasticsearch using Bulk API.
        
        Bulk API format (ndjson):
        {"index": {"_index": "index-name", "_id": "optional-id"}}
        {"field1": "value1", "field2": "value2"}
        {"index": {"_index": "index-name"}}
        {"field1": "value1", "field2": "value2"}
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not events:
            return (0, 0)
        
        try:
            # Build bulk request body (ndjson format)
            bulk_body = []
            for event in events:
                # Index action
                action = {
                    "index": {
                        "_index": self._get_index_name(event),
                        "_id": event.get("event_id")
                    }
                }
                
                # Document
                doc = self._format_for_elastic(event)
                
                # Add to bulk body (ndjson: one action, one doc per line)
                bulk_body.append(json.dumps(action))
                bulk_body.append(json.dumps(doc))
            
            # Join with newlines and add trailing newline
            bulk_data = "\n".join(bulk_body) + "\n"
            
            # Send bulk request
            response = self.client.post(
                self.bulk_url,
                headers=self.headers,
                content=bulk_data
            )
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                
                # Count successes and failures
                successful = 0
                failed = 0
                
                if "items" in response_data:
                    for item in response_data["items"]:
                        index_result = item.get("index", {})
                        status = index_result.get("status", 500)
                        
                        # 200 or 201 = success
                        if status in [200, 201]:
                            successful += 1
                        else:
                            failed += 1
                            error = index_result.get("error", {})
                            print(f"[WARN] Elasticsearch indexing failed: {error}")
                else:
                    # No items in response, consider it a failure
                    failed = len(events)
                
                return (successful, failed)
            else:
                print(f"[ERROR] Elasticsearch bulk request failed with {response.status_code}: {response.text}")
                return (0, len(events))
                
        except Exception as e:
            print(f"[ERROR] Failed to send batch to Elasticsearch: {e}")
            return (0, len(events))
    
    def test_connection(self) -> bool:
        """
        Test Elasticsearch connection health.
        
        Returns:
            True if connection is healthy
        """
        try:
            # Check cluster health
            response = self.client.get(self.health_url)
            
            if response.status_code == 200:
                health = response.json()
                status = health.get("status", "red")
                
                # Green or yellow is acceptable
                return status in ["green", "yellow"]
            
            return False
            
        except Exception as e:
            print(f"[ERROR] Elasticsearch health check failed: {e}")
            return False
    
    def _get_index_name(self, event: Dict[str, Any]) -> str:
        """
        Get index name for event.
        
        Can use date-based indices for time-series data.
        
        Args:
            event: Event data
        
        Returns:
            Index name
        """
        # Option 1: Static index
        base_index = self.index_name
        
        # Option 2: Date-based index (e.g., zerotrust-events-2025-10-29)
        # timestamp_str = event.get("timestamp", datetime.now(UTC).isoformat())
        # try:
        #     dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        #     date_suffix = dt.strftime("%Y-%m-%d")
        #     return f"{base_index}-{date_suffix}"
        # except:
        #     return base_index
        
        return base_index
    
    def _format_for_elastic(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format event for Elasticsearch.
        
        Args:
            event: Event data dictionary
        
        Returns:
            Elasticsearch-formatted document
        """
        # Add @timestamp field (Elasticsearch standard)
        doc = {
            "@timestamp": event.get("timestamp", datetime.now(UTC).isoformat()),
            "event": {
                "kind": "event",
                "category": self._map_event_category(event.get("event_type")),
                "type": [event.get("event_type", "info")],
                "module": "zerotrust",
                "dataset": "zerotrust.events"
            },
            **event
        }
        
        return doc
    
    def _map_event_category(self, event_type: str) -> str:
        """
        Map event type to ECS (Elastic Common Schema) category.
        
        Args:
            event_type: Event type
        
        Returns:
            ECS category
        """
        category_mapping = {
            "anomaly": "threat",
            "risk_assessment": "host",
            "compliance_check": "configuration",
            "telemetry": "host",
            "workflow_execution": "process",
            "security_event": "authentication",
            "alert": "alert"
        }
        
        return category_mapping.get(event_type, "event")
    
    def create_index_template(self) -> bool:
        """
        Create index template for zerotrust events.
        
        [Inference] This would define mappings and settings for the index.
        
        Returns:
            True if template created successfully
        """
        # Index template would define field mappings, analyzers, etc.
        # For now, Elasticsearch will use dynamic mapping
        return True
    
    def close(self):
        """Close HTTP client connection."""
        if self.client:
            self.client.close()

