"""
Baseline Behavior Profiler

Author: Adrian Johnson <adrian207@gmail.com>

Learns normal behavior patterns from historical telemetry data to establish baselines
for anomaly detection.
"""

from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Optional
import statistics
from collections import Counter
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from analytics.models import BehaviorBaseline
from telemetry.models import DeviceTelemetry


class BaselineProfiler:
    """
    Builds statistical baselines for device behavior.
    
    Analyzes historical telemetry to establish normal behavior patterns
    and statistical thresholds for anomaly detection.
    """
    
    def __init__(self, db: Session, learning_period_days: int = 30):
        """
        Initialize the baseline profiler.
        
        Args:
            db: Database session
            learning_period_days: Number of days to use for learning baseline
        """
        self.db = db
        self.learning_period_days = learning_period_days
        self.min_samples = 10  # Minimum samples needed for confident baseline
    
    def build_baseline(
        self,
        device_id: str,
        baseline_type: str,
        force_refresh: bool = False
    ) -> Optional[BehaviorBaseline]:
        """
        Build or update baseline for a device.
        
        Args:
            device_id: Device identifier
            baseline_type: Type of baseline (e.g., "authentication", "network")
            force_refresh: Force rebuild even if baseline exists
        
        Returns:
            BehaviorBaseline object or None if insufficient data
        """
        # Check if baseline already exists
        existing_baseline = self.db.query(BehaviorBaseline).filter(
            BehaviorBaseline.device_id == device_id,
            BehaviorBaseline.baseline_type == baseline_type,
            BehaviorBaseline.is_active == True
        ).first()
        
        if existing_baseline and not force_refresh and not existing_baseline.needs_refresh:
            return existing_baseline
        
        # Gather historical telemetry
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=self.learning_period_days)
        
        telemetry_data = self.db.query(DeviceTelemetry).filter(
            DeviceTelemetry.device_id == device_id,
            DeviceTelemetry.collection_time >= start_time,
            DeviceTelemetry.collection_time <= end_time
        ).order_by(DeviceTelemetry.collection_time).all()
        
        if len(telemetry_data) < self.min_samples:
            return None  # Insufficient data
        
        # Build baseline based on type
        baseline_data = self._compute_baseline(telemetry_data, baseline_type)
        
        if not baseline_data:
            return None
        
        # Create or update baseline
        if existing_baseline:
            baseline = existing_baseline
            baseline.last_updated = datetime.now(UTC)
            baseline.needs_refresh = False
        else:
            baseline = BehaviorBaseline(
                baseline_id=f"BL-{uuid.uuid4().hex[:12].upper()}",
                device_id=device_id,
                baseline_type=baseline_type
            )
            self.db.add(baseline)
        
        # Update baseline data
        baseline.learning_start = start_time
        baseline.learning_end = end_time
        baseline.sample_count = len(telemetry_data)
        baseline.confidence_score = self._calculate_confidence(len(telemetry_data))
        
        baseline.mean_values = baseline_data.get("mean_values")
        baseline.std_dev_values = baseline_data.get("std_dev_values")
        baseline.min_values = baseline_data.get("min_values")
        baseline.max_values = baseline_data.get("max_values")
        baseline.percentiles = baseline_data.get("percentiles")
        baseline.common_values = baseline_data.get("common_values")
        baseline.value_frequencies = baseline_data.get("value_frequencies")
        baseline.hourly_patterns = baseline_data.get("hourly_patterns")
        baseline.daily_patterns = baseline_data.get("daily_patterns")
        
        self.db.commit()
        
        return baseline
    
    def _compute_baseline(
        self,
        telemetry_data: List[DeviceTelemetry],
        baseline_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Compute statistical baseline from telemetry data.
        
        Args:
            telemetry_data: List of telemetry records
            baseline_type: Type of baseline to compute
        
        Returns:
            Dictionary containing baseline statistics
        """
        if baseline_type == "authentication":
            return self._compute_authentication_baseline(telemetry_data)
        elif baseline_type == "network":
            return self._compute_network_baseline(telemetry_data)
        elif baseline_type == "process":
            return self._compute_process_baseline(telemetry_data)
        elif baseline_type == "system":
            return self._compute_system_baseline(telemetry_data)
        else:
            return None
    
    def _compute_authentication_baseline(
        self,
        telemetry_data: List[DeviceTelemetry]
    ) -> Dict[str, Any]:
        """Compute authentication behavior baseline."""
        login_hours = []
        login_days = []
        failed_auth_counts = []
        
        for telemetry in telemetry_data:
            collection_time = telemetry.collection_time
            login_hours.append(collection_time.hour)
            login_days.append(collection_time.weekday())
            
            # Extract failed auth data if available
            if telemetry.security_data:
                failed_auths = telemetry.security_data.get("failed_authentication_attempts", 0)
                failed_auth_counts.append(failed_auths)
        
        return {
            "mean_values": {
                "failed_auth_count": statistics.mean(failed_auth_counts) if failed_auth_counts else 0
            },
            "std_dev_values": {
                "failed_auth_count": statistics.stdev(failed_auth_counts) if len(failed_auth_counts) > 1 else 0
            },
            "min_values": {
                "failed_auth_count": min(failed_auth_counts) if failed_auth_counts else 0
            },
            "max_values": {
                "failed_auth_count": max(failed_auth_counts) if failed_auth_counts else 0
            },
            "percentiles": {
                "failed_auth_count": self._calculate_percentiles(failed_auth_counts)
            },
            "hourly_patterns": self._compute_hourly_distribution(login_hours),
            "daily_patterns": self._compute_daily_distribution(login_days)
        }
    
    def _compute_network_baseline(
        self,
        telemetry_data: List[DeviceTelemetry]
    ) -> Dict[str, Any]:
        """Compute network behavior baseline."""
        networks = []
        vpn_usage = []
        connection_counts = []
        
        for telemetry in telemetry_data:
            if telemetry.network_data:
                net_data = telemetry.network_data
                
                # Collect network names
                if "ssid" in net_data:
                    networks.append(net_data["ssid"])
                
                # VPN usage
                vpn_usage.append(net_data.get("vpn_connected", False))
                
                # Connection count
                connections = net_data.get("active_connections", 0)
                connection_counts.append(connections)
        
        # Calculate network frequencies
        network_counter = Counter(networks)
        common_networks = dict(network_counter.most_common(10))
        
        return {
            "mean_values": {
                "connection_count": statistics.mean(connection_counts) if connection_counts else 0,
                "vpn_usage_rate": sum(vpn_usage) / len(vpn_usage) if vpn_usage else 0
            },
            "std_dev_values": {
                "connection_count": statistics.stdev(connection_counts) if len(connection_counts) > 1 else 0
            },
            "min_values": {
                "connection_count": min(connection_counts) if connection_counts else 0
            },
            "max_values": {
                "connection_count": max(connection_counts) if connection_counts else 0
            },
            "percentiles": {
                "connection_count": self._calculate_percentiles(connection_counts)
            },
            "common_values": {
                "networks": list(common_networks.keys())
            },
            "value_frequencies": {
                "networks": common_networks
            }
        }
    
    def _compute_process_baseline(
        self,
        telemetry_data: List[DeviceTelemetry]
    ) -> Dict[str, Any]:
        """Compute process behavior baseline."""
        process_counts = []
        process_names = []
        
        for telemetry in telemetry_data:
            if telemetry.process_data:
                proc_data = telemetry.process_data
                
                # Process count
                processes = proc_data.get("processes", [])
                process_counts.append(len(processes))
                
                # Collect process names
                for process in processes:
                    process_names.append(process.get("name", "unknown"))
        
        # Most common processes
        process_counter = Counter(process_names)
        common_processes = dict(process_counter.most_common(20))
        
        return {
            "mean_values": {
                "process_count": statistics.mean(process_counts) if process_counts else 0
            },
            "std_dev_values": {
                "process_count": statistics.stdev(process_counts) if len(process_counts) > 1 else 0
            },
            "min_values": {
                "process_count": min(process_counts) if process_counts else 0
            },
            "max_values": {
                "process_count": max(process_counts) if process_counts else 0
            },
            "percentiles": {
                "process_count": self._calculate_percentiles(process_counts)
            },
            "common_values": {
                "processes": list(common_processes.keys())
            },
            "value_frequencies": {
                "processes": common_processes
            }
        }
    
    def _compute_system_baseline(
        self,
        telemetry_data: List[DeviceTelemetry]
    ) -> Dict[str, Any]:
        """Compute system behavior baseline."""
        cpu_usages = []
        memory_usages = []
        disk_usages = []
        
        for telemetry in telemetry_data:
            if telemetry.system_data:
                sys_data = telemetry.system_data
                
                cpu_usages.append(sys_data.get("cpu_usage", 0))
                memory_usages.append(sys_data.get("memory_usage", 0))
                disk_usages.append(sys_data.get("disk_usage", 0))
        
        return {
            "mean_values": {
                "cpu_usage": statistics.mean(cpu_usages) if cpu_usages else 0,
                "memory_usage": statistics.mean(memory_usages) if memory_usages else 0,
                "disk_usage": statistics.mean(disk_usages) if disk_usages else 0
            },
            "std_dev_values": {
                "cpu_usage": statistics.stdev(cpu_usages) if len(cpu_usages) > 1 else 0,
                "memory_usage": statistics.stdev(memory_usages) if len(memory_usages) > 1 else 0,
                "disk_usage": statistics.stdev(disk_usages) if len(disk_usages) > 1 else 0
            },
            "min_values": {
                "cpu_usage": min(cpu_usages) if cpu_usages else 0,
                "memory_usage": min(memory_usages) if memory_usages else 0,
                "disk_usage": min(disk_usages) if disk_usages else 0
            },
            "max_values": {
                "cpu_usage": max(cpu_usages) if cpu_usages else 0,
                "memory_usage": max(memory_usages) if memory_usages else 0,
                "disk_usage": max(disk_usages) if disk_usages else 0
            },
            "percentiles": {
                "cpu_usage": self._calculate_percentiles(cpu_usages),
                "memory_usage": self._calculate_percentiles(memory_usages),
                "disk_usage": self._calculate_percentiles(disk_usages)
            }
        }
    
    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate percentiles for a list of values."""
        if not values or len(values) < 2:
            return {"p25": 0, "p50": 0, "p75": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            "p25": sorted_values[int(n * 0.25)],
            "p50": sorted_values[int(n * 0.50)],
            "p75": sorted_values[int(n * 0.75)],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)] if n > 1 else sorted_values[-1]
        }
    
    def _compute_hourly_distribution(self, hours: List[int]) -> Dict[int, float]:
        """Compute hourly activity distribution."""
        if not hours:
            return {}
        
        hour_counter = Counter(hours)
        total = len(hours)
        
        return {
            hour: count / total
            for hour, count in hour_counter.items()
        }
    
    def _compute_daily_distribution(self, days: List[int]) -> Dict[int, float]:
        """Compute daily activity distribution."""
        if not days:
            return {}
        
        day_counter = Counter(days)
        total = len(days)
        
        return {
            day: count / total
            for day, count in day_counter.items()
        }
    
    def _calculate_confidence(self, sample_count: int) -> float:
        """
        Calculate confidence score based on sample count.
        
        Args:
            sample_count: Number of samples used for baseline
        
        Returns:
            Confidence score (0-100)
        """
        if sample_count < self.min_samples:
            return 0.0
        elif sample_count < 50:
            return 50.0
        elif sample_count < 100:
            return 75.0
        else:
            return min(100.0, 75.0 + (sample_count - 100) / 10)
    
    def build_all_baselines(self, device_id: str) -> Dict[str, BehaviorBaseline]:
        """
        Build all baseline types for a device.
        
        Args:
            device_id: Device identifier
        
        Returns:
            Dictionary of baseline_type -> BehaviorBaseline
        """
        baseline_types = ["authentication", "network", "process", "system"]
        baselines = {}
        
        for baseline_type in baseline_types:
            baseline = self.build_baseline(device_id, baseline_type)
            if baseline:
                baselines[baseline_type] = baseline
        
        return baselines

