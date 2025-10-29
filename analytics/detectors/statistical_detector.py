"""
Statistical Anomaly Detector

Author: Adrian Johnson <adrian207@gmail.com>

Detects anomalies using statistical methods and baseline comparisons.
"""

from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
import uuid

from sqlalchemy.orm import Session

from analytics.models import AnomalyDetection, BehaviorBaseline, AnomalySeverity, AnomalyType
from telemetry.models import DeviceTelemetry


class StatisticalDetector:
    """
    Statistical anomaly detection using baseline comparisons.
    
    Detects anomalies by comparing current behavior against established
    statistical baselines using z-scores and threshold checks.
    """
    
    def __init__(
        self,
        db: Session,
        z_score_threshold: float = 3.0,
        percentile_threshold: float = 0.95
    ):
        """
        Initialize statistical detector.
        
        Args:
            db: Database session
            z_score_threshold: Z-score threshold for anomaly (default: 3 std devs)
            percentile_threshold: Percentile threshold (default: 95th percentile)
        """
        self.db = db
        self.z_score_threshold = z_score_threshold
        self.percentile_threshold = percentile_threshold
    
    def detect_anomalies(
        self,
        device_id: str,
        telemetry: DeviceTelemetry
    ) -> List[AnomalyDetection]:
        """
        Detect anomalies in telemetry data.
        
        Args:
            device_id: Device identifier
            telemetry: Current telemetry data
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Get active baselines for device
        baselines = self.db.query(BehaviorBaseline).filter(
            BehaviorBaseline.device_id == device_id,
            BehaviorBaseline.is_active == True
        ).all()
        
        if not baselines:
            return anomalies  # No baselines to compare against
        
        # Check each baseline type
        for baseline in baselines:
            detected = self._check_baseline(device_id, telemetry, baseline)
            anomalies.extend(detected)
        
        return anomalies
    
    def _check_baseline(
        self,
        device_id: str,
        telemetry: DeviceTelemetry,
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """
        Check telemetry against a specific baseline.
        
        Args:
            device_id: Device identifier
            telemetry: Current telemetry
            baseline: Baseline to check against
        
        Returns:
            List of detected anomalies
        """
        if baseline.baseline_type == "authentication":
            return self._check_authentication_baseline(device_id, telemetry, baseline)
        elif baseline.baseline_type == "network":
            return self._check_network_baseline(device_id, telemetry, baseline)
        elif baseline.baseline_type == "process":
            return self._check_process_baseline(device_id, telemetry, baseline)
        elif baseline.baseline_type == "system":
            return self._check_system_baseline(device_id, telemetry, baseline)
        else:
            return []
    
    def _check_authentication_baseline(
        self,
        device_id: str,
        telemetry: DeviceTelemetry,
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Check authentication anomalies."""
        anomalies = []
        
        if not telemetry.security_data:
            return anomalies
        
        sec_data = telemetry.security_data
        failed_auths = sec_data.get("failed_authentication_attempts", 0)
        
        # Check failed authentication count
        mean_failed = baseline.mean_values.get("failed_auth_count", 0)
        std_failed = baseline.std_dev_values.get("failed_auth_count", 0)
        
        if std_failed > 0:
            z_score = (failed_auths - mean_failed) / std_failed
            
            if z_score > self.z_score_threshold:
                anomaly = self._create_anomaly(
                    device_id=device_id,
                    anomaly_type=AnomalyType.AUTHENTICATION,
                    feature_name="failed_authentication_attempts",
                    observed_value=failed_auths,
                    expected_value=mean_failed,
                    deviation=z_score,
                    baseline=baseline,
                    title=f"Unusual failed authentication attempts",
                    description=f"Device has {failed_auths} failed authentication attempts, "
                               f"which is {z_score:.1f} standard deviations above normal ({mean_failed:.1f}).",
                    severity=self._determine_severity(z_score),
                    anomaly_score=min(100.0, z_score * 20)
                )
                anomalies.append(anomaly)
        
        # Check login time anomaly
        login_hour = telemetry.collection_time.hour
        hourly_patterns = baseline.hourly_patterns or {}
        
        expected_probability = hourly_patterns.get(str(login_hour), 0)
        
        if expected_probability < 0.01:  # Less than 1% of normal activity
            anomaly = self._create_anomaly(
                device_id=device_id,
                anomaly_type=AnomalyType.AUTHENTICATION,
                feature_name="login_time",
                observed_value=login_hour,
                expected_value=list(hourly_patterns.keys()),
                baseline=baseline,
                title=f"Unusual login time detected",
                description=f"Login at hour {login_hour} is unusual for this device "
                           f"(occurs in only {expected_probability*100:.1f}% of normal activity).",
                severity=AnomalySeverity.LOW,
                anomaly_score=50.0
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _check_network_baseline(
        self,
        device_id: str,
        telemetry: DeviceTelemetry,
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Check network anomalies."""
        anomalies = []
        
        if not telemetry.network_data:
            return anomalies
        
        net_data = telemetry.network_data
        
        # Check connection count
        connections = net_data.get("active_connections", 0)
        mean_connections = baseline.mean_values.get("connection_count", 0)
        std_connections = baseline.std_dev_values.get("connection_count", 0)
        
        if std_connections > 0:
            z_score = (connections - mean_connections) / std_connections
            
            if abs(z_score) > self.z_score_threshold:
                anomaly = self._create_anomaly(
                    device_id=device_id,
                    anomaly_type=AnomalyType.NETWORK,
                    feature_name="active_connections",
                    observed_value=connections,
                    expected_value=mean_connections,
                    deviation=z_score,
                    baseline=baseline,
                    title=f"Unusual network connection count",
                    description=f"Device has {connections} active connections, "
                               f"which is {abs(z_score):.1f} standard deviations from normal ({mean_connections:.1f}).",
                    severity=self._determine_severity(abs(z_score)),
                    anomaly_score=min(100.0, abs(z_score) * 20)
                )
                anomalies.append(anomaly)
        
        # Check for unknown network
        current_network = net_data.get("ssid")
        if current_network:
            known_networks = baseline.common_values.get("networks", [])
            
            if current_network not in known_networks and len(known_networks) > 0:
                anomaly = self._create_anomaly(
                    device_id=device_id,
                    anomaly_type=AnomalyType.NETWORK,
                    feature_name="network_ssid",
                    observed_value=current_network,
                    expected_value=known_networks,
                    baseline=baseline,
                    title=f"Connection to unknown network",
                    description=f"Device connected to network '{current_network}' "
                               f"which has not been seen before.",
                    severity=AnomalySeverity.MEDIUM,
                    anomaly_score=60.0
                )
                anomalies.append(anomaly)
        
        # Check VPN status change
        vpn_connected = net_data.get("vpn_connected", False)
        typical_vpn = baseline.mean_values.get("vpn_usage_rate", 0)
        
        # Significant deviation from typical VPN usage
        if (vpn_connected and typical_vpn < 0.2) or (not vpn_connected and typical_vpn > 0.8):
            anomaly = self._create_anomaly(
                device_id=device_id,
                anomaly_type=AnomalyType.NETWORK,
                feature_name="vpn_status",
                observed_value=vpn_connected,
                expected_value=typical_vpn > 0.5,
                baseline=baseline,
                title=f"Unusual VPN usage pattern",
                description=f"VPN status ({vpn_connected}) differs from typical usage pattern "
                           f"({typical_vpn*100:.0f}% VPN usage).",
                severity=AnomalySeverity.LOW,
                anomaly_score=40.0
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _check_process_baseline(
        self,
        device_id: str,
        telemetry: DeviceTelemetry,
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Check process anomalies."""
        anomalies = []
        
        if not telemetry.process_data:
            return anomalies
        
        proc_data = telemetry.process_data
        processes = proc_data.get("processes", [])
        process_count = len(processes)
        
        # Check process count
        mean_count = baseline.mean_values.get("process_count", 0)
        std_count = baseline.std_dev_values.get("process_count", 0)
        
        if std_count > 0:
            z_score = (process_count - mean_count) / std_count
            
            if abs(z_score) > self.z_score_threshold:
                anomaly = self._create_anomaly(
                    device_id=device_id,
                    anomaly_type=AnomalyType.PROCESS,
                    feature_name="process_count",
                    observed_value=process_count,
                    expected_value=mean_count,
                    deviation=z_score,
                    baseline=baseline,
                    title=f"Unusual process count",
                    description=f"Device has {process_count} running processes, "
                               f"which is {abs(z_score):.1f} standard deviations from normal ({mean_count:.0f}).",
                    severity=self._determine_severity(abs(z_score)),
                    anomaly_score=min(100.0, abs(z_score) * 20)
                )
                anomalies.append(anomaly)
        
        # Check for unknown processes
        known_processes = set(baseline.common_values.get("processes", []))
        current_processes = set(p.get("name", "unknown") for p in processes if isinstance(p, dict))
        
        unknown_processes = current_processes - known_processes
        
        if unknown_processes and len(known_processes) > 5:
            # Only flag if there are multiple unknown processes
            if len(unknown_processes) > 3:
                anomaly = self._create_anomaly(
                    device_id=device_id,
                    anomaly_type=AnomalyType.PROCESS,
                    feature_name="unknown_processes",
                    observed_value=list(unknown_processes)[:10],  # Limit to 10
                    expected_value=list(known_processes)[:10],
                    baseline=baseline,
                    title=f"Multiple unknown processes detected",
                    description=f"Device is running {len(unknown_processes)} processes "
                               f"that have not been seen before.",
                    severity=AnomalySeverity.MEDIUM,
                    anomaly_score=55.0
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _check_system_baseline(
        self,
        device_id: str,
        telemetry: DeviceTelemetry,
        baseline: BehaviorBaseline
    ) -> List[AnomalyDetection]:
        """Check system resource anomalies."""
        anomalies = []
        
        if not telemetry.system_data:
            return anomalies
        
        sys_data = telemetry.system_data
        
        # Check CPU usage
        cpu_usage = sys_data.get("cpu_usage", 0)
        mean_cpu = baseline.mean_values.get("cpu_usage", 0)
        std_cpu = baseline.std_dev_values.get("cpu_usage", 0)
        
        if std_cpu > 0:
            z_score = (cpu_usage - mean_cpu) / std_cpu
            
            if z_score > self.z_score_threshold:
                anomaly = self._create_anomaly(
                    device_id=device_id,
                    anomaly_type=AnomalyType.SYSTEM_CONFIG,
                    feature_name="cpu_usage",
                    observed_value=cpu_usage,
                    expected_value=mean_cpu,
                    deviation=z_score,
                    baseline=baseline,
                    title=f"Unusual CPU usage",
                    description=f"CPU usage is {cpu_usage}%, which is {z_score:.1f} "
                               f"standard deviations above normal ({mean_cpu:.1f}%).",
                    severity=self._determine_severity(z_score),
                    anomaly_score=min(100.0, z_score * 20)
                )
                anomalies.append(anomaly)
        
        # Check memory usage
        memory_usage = sys_data.get("memory_usage", 0)
        mean_memory = baseline.mean_values.get("memory_usage", 0)
        std_memory = baseline.std_dev_values.get("memory_usage", 0)
        
        if std_memory > 0:
            z_score = (memory_usage - mean_memory) / std_memory
            
            if z_score > self.z_score_threshold:
                anomaly = self._create_anomaly(
                    device_id=device_id,
                    anomaly_type=AnomalyType.SYSTEM_CONFIG,
                    feature_name="memory_usage",
                    observed_value=memory_usage,
                    expected_value=mean_memory,
                    deviation=z_score,
                    baseline=baseline,
                    title=f"Unusual memory usage",
                    description=f"Memory usage is {memory_usage}%, which is {z_score:.1f} "
                               f"standard deviations above normal ({mean_memory:.1f}%).",
                    severity=self._determine_severity(z_score),
                    anomaly_score=min(100.0, z_score * 20)
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _create_anomaly(
        self,
        device_id: str,
        anomaly_type: AnomalyType,
        feature_name: str,
        observed_value: Any,
        expected_value: Any,
        title: str,
        description: str,
        severity: AnomalySeverity,
        anomaly_score: float,
        deviation: Optional[float] = None,
        baseline: Optional[BehaviorBaseline] = None
    ) -> AnomalyDetection:
        """
        Create anomaly detection record.
        
        Args:
            device_id: Device identifier
            anomaly_type: Type of anomaly
            feature_name: Feature that's anomalous
            observed_value: Observed value
            expected_value: Expected value
            title: Anomaly title
            description: Detailed description
            severity: Severity level
            anomaly_score: Anomaly score
            deviation: Z-score deviation (optional)
            baseline: Related baseline (optional)
        
        Returns:
            AnomalyDetection object
        """
        anomaly = AnomalyDetection(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:12].upper()}",
            device_id=device_id,
            anomaly_type=anomaly_type.value,
            anomaly_severity=severity.value,
            detection_method="statistical",
            detector_name="StatisticalDetector",
            anomaly_score=anomaly_score,
            confidence=0.85,  # Statistical methods have high confidence
            feature_name=feature_name,
            observed_value=observed_value,
            expected_value=expected_value,
            deviation=deviation,
            title=title,
            description=description,
            recommendations=self._get_recommendations(anomaly_type, severity),
            baseline_id=baseline.baseline_id if baseline else None,
            detected_at=datetime.now(UTC)
        )
        
        self.db.add(anomaly)
        self.db.commit()
        
        return anomaly
    
    def _determine_severity(self, z_score: float) -> AnomalySeverity:
        """
        Determine severity based on z-score.
        
        Args:
            z_score: Z-score deviation
        
        Returns:
            AnomalySeverity enum value
        """
        abs_z = abs(z_score)
        
        if abs_z >= 6.0:
            return AnomalySeverity.CRITICAL
        elif abs_z >= 4.5:
            return AnomalySeverity.HIGH
        elif abs_z >= 3.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _get_recommendations(
        self,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity
    ) -> List[str]:
        """
        Get recommendations based on anomaly type and severity.
        
        Args:
            anomaly_type: Type of anomaly
            severity: Severity level
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]:
            recommendations.append("Investigate immediately")
            recommendations.append("Review security logs for this device")
        
        if anomaly_type == AnomalyType.AUTHENTICATION:
            recommendations.extend([
                "Check for unauthorized access attempts",
                "Verify user identity",
                "Consider requiring password reset"
            ])
        elif anomaly_type == AnomalyType.NETWORK:
            recommendations.extend([
                "Verify network connection is legitimate",
                "Check for data exfiltration",
                "Review firewall logs"
            ])
        elif anomaly_type == AnomalyType.PROCESS:
            recommendations.extend([
                "Identify unknown processes",
                "Check for malware or unwanted software",
                "Review process execution history"
            ])
        elif anomaly_type == AnomalyType.SYSTEM_CONFIG:
            recommendations.extend([
                "Investigate cause of resource spike",
                "Check for resource-intensive applications",
                "Consider performance optimization"
            ])
        
        return recommendations

