"""
Device Inventory Report Generator

Author: Adrian Johnson <adrian207@gmail.com>

Generates detailed device inventory reports with hardware, software, and configuration data.
"""

from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional, List
from sqlalchemy import func

from reporting.generators.base import BaseReportGenerator
from reporting.models import ReportType, ReportFormat
from telemetry.models import DeviceTelemetry


class DeviceInventoryGenerator(BaseReportGenerator):
    """
    Generates comprehensive device inventory reports.
    
    Provides detailed hardware, software, and configuration inventory.
    """
    
    def __init__(self, db):
        """Initialize the device inventory generator."""
        super().__init__(db)
        self.report_type = ReportType.DEVICE_INVENTORY
        self.report_format = ReportFormat.CSV
    
    def get_title(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get report title."""
        return "Device Inventory Report"
    
    def get_description(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get report description."""
        return "Comprehensive inventory of all managed devices"
    
    def generate(self, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate device inventory report.
        
        Args:
            parameters: Report parameters
                - include_software: bool - Include software inventory
                - include_network: bool - Include network configuration
                - active_only: bool - Only include active devices
        
        Returns:
            Dict containing inventory data
        """
        parameters = parameters or {}
        include_software = parameters.get('include_software', False)
        include_network = parameters.get('include_network', False)
        active_only = parameters.get('active_only', True)
        
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now(UTC).isoformat(),
                "parameters": parameters
            },
            "summary": self._generate_inventory_summary(active_only),
            "devices": self._generate_device_list(active_only, include_software, include_network),
            "os_distribution": self._generate_os_distribution(),
            "hardware_models": self._generate_hardware_models()
        }
        
        return report_data
    
    def _generate_inventory_summary(self, active_only: bool) -> Dict[str, Any]:
        """Generate inventory summary statistics."""
        # Total devices
        query = self.db.query(func.count(func.distinct(DeviceTelemetry.device_id)))
        
        if active_only:
            cutoff_date = datetime.now(UTC) - timedelta(days=7)
            query = query.filter(DeviceTelemetry.collection_time >= cutoff_date)
        
        total_devices = query.scalar() or 0
        
        # OS version counts
        os_counts = self.db.query(
            DeviceTelemetry.os_version,
            func.count(func.distinct(DeviceTelemetry.device_id)).label('count')
        ).group_by(DeviceTelemetry.os_version).all()
        
        return {
            "total_devices": total_devices,
            "os_versions": len(os_counts),
            "active_filter": active_only
        }
    
    def _generate_device_list(
        self,
        active_only: bool,
        include_software: bool,
        include_network: bool
    ) -> List[Dict[str, Any]]:
        """Generate detailed device list."""
        devices = []
        
        # Get latest telemetry for each device
        query = self.db.query(DeviceTelemetry).distinct(DeviceTelemetry.device_id)
        
        if active_only:
            cutoff_date = datetime.now(UTC) - timedelta(days=7)
            query = query.filter(DeviceTelemetry.collection_time >= cutoff_date)
        
        telemetry_records = query.all()
        
        for telemetry in telemetry_records:
            device = {
                "device_id": telemetry.device_id,
                "hostname": telemetry.hostname,
                "os_type": telemetry.os_type,
                "os_version": telemetry.os_version,
                "last_seen": telemetry.collection_time.isoformat()
            }
            
            # Add security status if available
            if telemetry.security_data:
                security_data = telemetry.security_data
                device["security_status"] = {
                    "filevault_enabled": security_data.get("filevault", {}).get("enabled"),
                    "sip_enabled": security_data.get("sip", {}).get("enabled"),
                    "firewall_enabled": security_data.get("firewall", {}).get("enabled"),
                    "gatekeeper_enabled": security_data.get("gatekeeper", {}).get("enabled")
                }
            
            # Add software if requested
            if include_software and telemetry.software_inventory:
                device["software"] = {
                    "application_count": len(telemetry.software_inventory.get("applications", [])),
                    "top_applications": telemetry.software_inventory.get("applications", [])[:10]
                }
            
            # Add network if requested
            if include_network and telemetry.network_data:
                device["network"] = {
                    "primary_ip": telemetry.network_data.get("primary_ip"),
                    "mac_address": telemetry.network_data.get("mac_address"),
                    "vpn_connected": telemetry.network_data.get("vpn_connected")
                }
            
            devices.append(device)
        
        return devices
    
    def _generate_os_distribution(self) -> List[Dict[str, Any]]:
        """Generate OS version distribution."""
        os_dist = self.db.query(
            DeviceTelemetry.os_version,
            func.count(func.distinct(DeviceTelemetry.device_id)).label('count')
        ).group_by(DeviceTelemetry.os_version).order_by(func.count(func.distinct(DeviceTelemetry.device_id)).desc()).all()
        
        total = sum(count for _, count in os_dist)
        
        return [
            {
                "os_version": version,
                "device_count": count,
                "percentage": self._calculate_percentage(count, total)
            }
            for version, count in os_dist
        ]
    
    def _generate_hardware_models(self) -> List[Dict[str, Any]]:
        """Generate hardware model distribution."""
        # This would pull from telemetry hardware data
        # Simplified for now
        return []
    
    def _extract_key_metrics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for quick reference."""
        summary = report_data.get("summary", {})
        return {
            "total_devices": summary.get("total_devices"),
            "os_versions": summary.get("os_versions")
        }

