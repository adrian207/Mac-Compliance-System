"""
Device Behavior Profiler

Author: Adrian Johnson <adrian207@gmail.com>

Creates high-level behavioral profiles for devices based on historical activity patterns.
"""

from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Optional
import statistics
import uuid

from sqlalchemy.orm import Session

from analytics.models import BehaviorProfile
from telemetry.models import DeviceTelemetry


class DeviceProfiler:
    """
    Builds comprehensive behavioral profiles for devices.
    
    Analyzes historical patterns to create high-level profile summaries
    of device characteristics and typical behaviors.
    """
    
    def __init__(self, db: Session, profile_period_days: int = 90):
        """
        Initialize the device profiler.
        
        Args:
            db: Database session
            profile_period_days: Number of days to analyze for profiling
        """
        self.db = db
        self.profile_period_days = profile_period_days
        self.min_samples = 20  # Minimum data points for profile
    
    def build_profile(
        self,
        device_id: str,
        force_refresh: bool = False
    ) -> Optional[BehaviorProfile]:
        """
        Build or update device profile.
        
        Args:
            device_id: Device identifier
            force_refresh: Force rebuild even if profile exists
        
        Returns:
            BehaviorProfile object or None if insufficient data
        """
        # Check existing profile
        existing_profile = self.db.query(BehaviorProfile).filter(
            BehaviorProfile.device_id == device_id
        ).first()
        
        if existing_profile and not force_refresh:
            # Update if stale (>7 days old)
            if (datetime.now(UTC) - existing_profile.last_updated).days < 7:
                return existing_profile
        
        # Gather historical telemetry
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=self.profile_period_days)
        
        telemetry_data = self.db.query(DeviceTelemetry).filter(
            DeviceTelemetry.device_id == device_id,
            DeviceTelemetry.collection_time >= start_time,
            DeviceTelemetry.collection_time <= end_time
        ).order_by(DeviceTelemetry.collection_time).all()
        
        if len(telemetry_data) < self.min_samples:
            return None  # Insufficient data
        
        # Build profile components
        profile_data = self._analyze_device_behavior(telemetry_data)
        
        # Create or update profile
        if existing_profile:
            profile = existing_profile
            profile.profile_version += 1
            profile.last_updated = datetime.now(UTC)
        else:
            profile = BehaviorProfile(
                profile_id=f"PROF-{uuid.uuid4().hex[:12].upper()}",
                device_id=device_id,
                created_at=datetime.now(UTC)
            )
            self.db.add(profile)
        
        # Update profile data
        profile.typical_login_hours = profile_data.get("typical_login_hours")
        profile.typical_login_days = profile_data.get("typical_login_days")
        profile.average_session_duration = profile_data.get("average_session_duration")
        profile.typical_networks = profile_data.get("typical_networks")
        profile.typical_vpn_usage = profile_data.get("typical_vpn_usage")
        profile.average_bandwidth_usage = profile_data.get("average_bandwidth_usage")
        profile.common_applications = profile_data.get("common_applications")
        profile.application_diversity = profile_data.get("application_diversity")
        profile.typical_process_count = profile_data.get("typical_process_count")
        profile.common_processes = profile_data.get("common_processes")
        profile.typical_failed_auth_count = profile_data.get("typical_failed_auth_count")
        profile.activity_regularity_score = profile_data.get("activity_regularity_score")
        profile.risk_appetite_score = profile_data.get("risk_appetite_score")
        
        profile.is_complete = True
        profile.confidence_score = self._calculate_profile_confidence(len(telemetry_data))
        
        self.db.commit()
        
        return profile
    
    def _analyze_device_behavior(
        self,
        telemetry_data: List[DeviceTelemetry]
    ) -> Dict[str, Any]:
        """
        Analyze telemetry data to extract behavioral patterns.
        
        Args:
            telemetry_data: List of telemetry records
        
        Returns:
            Dictionary of profile characteristics
        """
        from collections import Counter
        
        # Temporal patterns
        login_hours = [t.collection_time.hour for t in telemetry_data]
        login_days = [t.collection_time.weekday() for t in telemetry_data]
        
        hour_counter = Counter(login_hours)
        day_counter = Counter(login_days)
        
        typical_login_hours = [h for h, count in hour_counter.most_common(8)]
        typical_login_days = [d for d, count in day_counter.most_common(5)]
        
        # Network patterns
        networks = []
        vpn_usages = []
        
        for t in telemetry_data:
            if t.network_data:
                if "ssid" in t.network_data:
                    networks.append(t.network_data["ssid"])
                vpn_usages.append(t.network_data.get("vpn_connected", False))
        
        network_counter = Counter(networks)
        typical_networks = [net for net, count in network_counter.most_common(5)]
        typical_vpn_usage = sum(vpn_usages) / len(vpn_usages) if vpn_usages else False
        
        # Application patterns
        applications = []
        for t in telemetry_data:
            if t.software_inventory:
                apps = t.software_inventory.get("applications", [])
                for app in apps:
                    if isinstance(app, dict):
                        applications.append(app.get("name", "unknown"))
        
        app_counter = Counter(applications)
        common_applications = [app for app, count in app_counter.most_common(15)]
        application_diversity = self._calculate_entropy(app_counter)
        
        # Process patterns
        process_counts = []
        processes = []
        
        for t in telemetry_data:
            if t.process_data:
                proc_list = t.process_data.get("processes", [])
                process_counts.append(len(proc_list))
                for proc in proc_list:
                    if isinstance(proc, dict):
                        processes.append(proc.get("name", "unknown"))
        
        typical_process_count = int(statistics.mean(process_counts)) if process_counts else 0
        
        proc_counter = Counter(processes)
        common_processes = [proc for proc, count in proc_counter.most_common(15)]
        
        # Security patterns
        failed_auth_counts = []
        for t in telemetry_data:
            if t.security_data:
                failed_auth_counts.append(
                    t.security_data.get("failed_authentication_attempts", 0)
                )
        
        typical_failed_auth_count = int(statistics.mean(failed_auth_counts)) if failed_auth_counts else 0
        
        # Activity regularity (how predictable the behavior is)
        activity_regularity_score = self._calculate_regularity(hour_counter, day_counter)
        
        # Risk appetite (based on security posture and behaviors)
        risk_appetite_score = self._calculate_risk_appetite(telemetry_data)
        
        return {
            "typical_login_hours": typical_login_hours,
            "typical_login_days": typical_login_days,
            "average_session_duration": 240,  # Placeholder
            "typical_networks": typical_networks,
            "typical_vpn_usage": typical_vpn_usage,
            "average_bandwidth_usage": 0.0,  # Placeholder
            "common_applications": common_applications,
            "application_diversity": application_diversity,
            "typical_process_count": typical_process_count,
            "common_processes": common_processes,
            "typical_failed_auth_count": typical_failed_auth_count,
            "activity_regularity_score": activity_regularity_score,
            "risk_appetite_score": risk_appetite_score
        }
    
    def _calculate_entropy(self, counter: Counter) -> float:
        """
        Calculate Shannon entropy for diversity measurement.
        
        Args:
            counter: Counter object with frequencies
        
        Returns:
            Entropy value (0-10 scale)
        """
        import math
        
        if not counter:
            return 0.0
        
        total = sum(counter.values())
        entropy = 0.0
        
        for count in counter.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        # Normalize to 0-10 scale
        return min(10.0, entropy)
    
    def _calculate_regularity(
        self,
        hour_counter: Counter,
        day_counter: Counter
    ) -> float:
        """
        Calculate activity regularity score.
        
        More concentrated patterns = higher regularity.
        
        Args:
            hour_counter: Counter of hours
            day_counter: Counter of days
        
        Returns:
            Regularity score (0-100)
        """
        if not hour_counter or not day_counter:
            return 0.0
        
        # Calculate concentration (inverse of entropy)
        hour_entropy = self._calculate_entropy(hour_counter)
        day_entropy = self._calculate_entropy(day_counter)
        
        # Higher entropy = lower regularity
        max_hour_entropy = 4.58  # log2(24)
        max_day_entropy = 2.81   # log2(7)
        
        hour_regularity = (1 - hour_entropy / max_hour_entropy) * 100
        day_regularity = (1 - day_entropy / max_day_entropy) * 100
        
        # Average regularity
        return (hour_regularity + day_regularity) / 2
    
    def _calculate_risk_appetite(
        self,
        telemetry_data: List[DeviceTelemetry]
    ) -> float:
        """
        Calculate risk appetite score based on security behaviors.
        
        Args:
            telemetry_data: List of telemetry records
        
        Returns:
            Risk appetite score (0-100, higher = more risk-taking)
        """
        risk_indicators = []
        
        for t in telemetry_data:
            score = 0
            
            if t.security_data:
                sec_data = t.security_data
                
                # Security controls disabled
                if not sec_data.get("filevault", {}).get("enabled"):
                    score += 20
                if not sec_data.get("sip", {}).get("enabled"):
                    score += 15
                if not sec_data.get("firewall", {}).get("enabled"):
                    score += 15
                if not sec_data.get("gatekeeper", {}).get("enabled"):
                    score += 10
                
                # Failed authentications
                failed_auths = sec_data.get("failed_authentication_attempts", 0)
                if failed_auths > 5:
                    score += 10
                elif failed_auths > 0:
                    score += 5
            
            risk_indicators.append(min(100, score))
        
        return statistics.mean(risk_indicators) if risk_indicators else 0.0
    
    def _calculate_profile_confidence(self, sample_count: int) -> float:
        """
        Calculate profile confidence score.
        
        Args:
            sample_count: Number of samples analyzed
        
        Returns:
            Confidence score (0-100)
        """
        if sample_count < self.min_samples:
            return 0.0
        elif sample_count < 100:
            return 60.0
        elif sample_count < 500:
            return 80.0
        else:
            return min(100.0, 80.0 + (sample_count - 500) / 50)

