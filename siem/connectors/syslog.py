"""
Syslog and CEF (Common Event Format) Connector

Author: Adrian Johnson <adrian207@gmail.com>

Connector for sending events via Syslog protocol with optional CEF formatting.
"""

from datetime import datetime, UTC
from typing import List, Dict, Any
import socket
import ssl

from siem.connectors.base import BaseSIEMConnector


class SyslogConnector(BaseSIEMConnector):
    """
    Syslog connector with CEF format support.
    
    Sends events via Syslog protocol (UDP/TCP/TLS) with optional CEF formatting.
    RFC 5424: https://tools.ietf.org/html/rfc5424
    CEF: https://www.microfocus.com/documentation/arcsight/arcsight-smartconnectors-8.3/cef-implementation-standard/
    """
    
    def __init__(self, db, connection):
        """Initialize Syslog connector."""
        super().__init__(db, connection)
        
        # Syslog configuration
        self.host = connection.endpoint
        self.port = connection.port or 514
        self.protocol = connection.auth_type or "udp"  # udp, tcp, tls
        self.facility = self._parse_facility(connection.facility or "local0")
        
        # CEF configuration
        self.use_cef = connection.siem_type == "cef"
        self.cef_vendor = "ZeroTrust"
        self.cef_product = "Mac-Compliance-System"
        self.cef_version = "1.0"
        
        # Socket
        self.socket = None
        self._connect_socket()
    
    def _connect_socket(self):
        """Establish socket connection."""
        try:
            if self.protocol == "udp":
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            elif self.protocol in ["tcp", "tls"]:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                if self.protocol == "tls":
                    context = ssl.create_default_context()
                    if not self.connection.verify_ssl:
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                    self.socket = context.wrap_socket(
                        self.socket,
                        server_hostname=self.host
                    )
                
                self.socket.connect((self.host, self.port))
        except Exception as e:
            print(f"[ERROR] Failed to connect syslog socket: {e}")
            self.socket = None
    
    def connect(self) -> bool:
        """
        Establish connection to Syslog server.
        
        Returns:
            True if connection successful
        """
        try:
            if not self.socket:
                self._connect_socket()
            return self.socket is not None
        except Exception as e:
            print(f"[ERROR] Syslog connection failed: {e}")
            return False
    
    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send single event via Syslog.
        
        Args:
            event: Event data dictionary
        
        Returns:
            True if sent successfully
        """
        try:
            # Format event
            if self.use_cef:
                message = self._format_cef(event)
            else:
                message = self._format_syslog(event)
            
            # Send via socket
            if self.protocol == "udp":
                self.socket.sendto(message.encode('utf-8'), (self.host, self.port))
            else:  # tcp or tls
                self.socket.sendall(message.encode('utf-8') + b'\n')
            
            return True
                
        except Exception as e:
            print(f"[ERROR] Failed to send event via Syslog: {e}")
            # Try to reconnect
            self._connect_socket()
            return False
    
    def send_batch(self, events: List[Dict[str, Any]]) -> tuple[int, int]:
        """
        Send batch of events via Syslog.
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not events:
            return (0, 0)
        
        successful = 0
        failed = 0
        
        for event in events:
            if self.send_event(event):
                successful += 1
            else:
                failed += 1
        
        return (successful, failed)
    
    def test_connection(self) -> bool:
        """
        Test Syslog connection health.
        
        Returns:
            True if connection is healthy
        """
        try:
            # For UDP, we can't really test - just check socket exists
            if self.protocol == "udp":
                return self.socket is not None
            
            # For TCP/TLS, socket being connected means it's healthy
            return self.socket is not None and self.socket.fileno() != -1
            
        except Exception as e:
            print(f"[ERROR] Syslog health check failed: {e}")
            return False
    
    def _format_syslog(self, event: Dict[str, Any]) -> str:
        """
        Format event as RFC 5424 Syslog message.
        
        Format: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
        
        Args:
            event: Event data dictionary
        
        Returns:
            Syslog-formatted message
        """
        # Calculate priority (facility * 8 + severity)
        severity = self._map_severity(event.get("severity", "info"))
        priority = (self.facility * 8) + severity
        
        # Timestamp (ISO 8601)
        timestamp = event.get("timestamp", datetime.now(UTC).isoformat())
        
        # Hostname
        hostname = event.get("source", "zerotrust-platform")
        
        # App name
        app_name = "zerotrust"
        
        # Process ID
        procid = "-"
        
        # Message ID
        msgid = event.get("event_type", "-")
        
        # Structured data (optional)
        structured_data = "-"
        
        # Message
        msg = self._format_message(event)
        
        # Build syslog message
        syslog_msg = f"<{priority}>1 {timestamp} {hostname} {app_name} {procid} {msgid} {structured_data} {msg}"
        
        return syslog_msg
    
    def _format_cef(self, event: Dict[str, Any]) -> str:
        """
        Format event as CEF (Common Event Format).
        
        Format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        
        Args:
            event: Event data dictionary
        
        Returns:
            CEF-formatted message
        """
        # CEF header
        signature_id = event.get("event_type", "unknown")
        name = event.get("title", event.get("event_type", "Unknown Event"))
        severity = self._map_cef_severity(event.get("severity", "info"))
        
        cef_header = f"CEF:0|{self.cef_vendor}|{self.cef_product}|{self.cef_version}|{signature_id}|{name}|{severity}"
        
        # CEF extension (key=value pairs)
        extensions = []
        
        # Standard CEF fields
        if "event_id" in event:
            extensions.append(f"externalId={event['event_id']}")
        
        if "source" in event:
            extensions.append(f"dvc={event['source']}")
        
        if "timestamp" in event:
            # CEF uses milliseconds since epoch
            try:
                dt = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                ms = int(dt.timestamp() * 1000)
                extensions.append(f"rt={ms}")
            except:
                pass
        
        # Add custom fields
        if "device_id" in event:
            extensions.append(f"deviceExternalId={event['device_id']}")
        
        if "risk_score" in event:
            extensions.append(f"cn1={event['risk_score']} cn1Label=RiskScore")
        
        if "anomaly_score" in event:
            extensions.append(f"cn2={event['anomaly_score']} cn2Label=AnomalyScore")
        
        if "description" in event:
            # Escape special characters in CEF
            desc = event['description'].replace('\\', '\\\\').replace('=', '\\=').replace('\n', '\\n')
            extensions.append(f"msg={desc}")
        
        # Build CEF message
        extension_str = " ".join(extensions)
        cef_msg = f"{cef_header}|{extension_str}"
        
        # Wrap in syslog format
        severity_num = self._map_severity(event.get("severity", "info"))
        priority = (self.facility * 8) + severity_num
        timestamp = event.get("timestamp", datetime.now(UTC).isoformat())
        hostname = event.get("source", "zerotrust-platform")
        
        syslog_cef = f"<{priority}>{timestamp} {hostname} {cef_msg}"
        
        return syslog_cef
    
    def _format_message(self, event: Dict[str, Any]) -> str:
        """
        Format event as message text.
        
        Args:
            event: Event data dictionary
        
        Returns:
            Message string
        """
        # Build readable message
        msg_parts = []
        
        if "event_type" in event:
            msg_parts.append(f"type={event['event_type']}")
        
        if "device_id" in event:
            msg_parts.append(f"device={event['device_id']}")
        
        if "title" in event:
            msg_parts.append(f"title=\"{event['title']}\"")
        
        if "description" in event:
            msg_parts.append(f"desc=\"{event['description']}\"")
        
        return " ".join(msg_parts) if msg_parts else "ZeroTrust event"
    
    def _parse_facility(self, facility_str: str) -> int:
        """
        Parse syslog facility name to number.
        
        Args:
            facility_str: Facility name (e.g., "local0")
        
        Returns:
            Facility number (0-23)
        """
        facilities = {
            "kern": 0, "user": 1, "mail": 2, "daemon": 3,
            "auth": 4, "syslog": 5, "lpr": 6, "news": 7,
            "uucp": 8, "cron": 9, "authpriv": 10, "ftp": 11,
            "local0": 16, "local1": 17, "local2": 18, "local3": 19,
            "local4": 20, "local5": 21, "local6": 22, "local7": 23
        }
        
        return facilities.get(facility_str.lower(), 16)  # Default to local0
    
    def _map_severity(self, severity_str: str) -> int:
        """
        Map severity string to syslog severity number.
        
        Args:
            severity_str: Severity string
        
        Returns:
            Syslog severity (0-7)
        """
        severity_map = {
            "emergency": 0, "alert": 1, "critical": 2, "error": 3,
            "warning": 4, "notice": 5, "info": 6, "debug": 7
        }
        
        # Map our severity levels to syslog
        our_severity_map = {
            "critical": 2,
            "high": 3,
            "medium": 4,
            "low": 5,
            "info": 6
        }
        
        return our_severity_map.get(severity_str.lower(), 6)
    
    def _map_cef_severity(self, severity_str: str) -> int:
        """
        Map severity string to CEF severity (0-10).
        
        Args:
            severity_str: Severity string
        
        Returns:
            CEF severity (0-10)
        """
        cef_severity_map = {
            "critical": 10,
            "high": 7,
            "medium": 5,
            "low": 3,
            "info": 1
        }
        
        return cef_severity_map.get(severity_str.lower(), 1)
    
    def close(self):
        """Close socket connection."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

