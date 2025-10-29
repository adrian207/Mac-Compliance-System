"""
Real-Time Anomaly Detection Engine

Author: Adrian Johnson <adrian207@gmail.com>

Orchestrates anomaly detection across multiple detectors and processes telemetry in real-time.
"""

from datetime import datetime, UTC
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from analytics.models import AnomalyDetection
from analytics.detectors import StatisticalDetector, MLAnomalyDetector, RuleBasedDetector
from analytics.profilers import BaselineProfiler, DeviceProfiler
from telemetry.models import DeviceTelemetry


class DetectionEngine:
    """
    Real-time anomaly detection engine.
    
    Orchestrates multiple detection methods and provides unified anomaly detection.
    """
    
    def __init__(self, db: Session, enable_ml: bool = True):
        """
        Initialize detection engine.
        
        Args:
            db: Database session
            enable_ml: Enable ML-based detection (default: True)
        """
        self.db = db
        self.enable_ml = enable_ml
        
        # Initialize detectors
        self.statistical_detector = StatisticalDetector(db)
        self.rule_based_detector = RuleBasedDetector(db)
        
        if enable_ml:
            self.ml_detector = MLAnomalyDetector(db)
        else:
            self.ml_detector = None
        
        # Initialize profilers
        self.baseline_profiler = BaselineProfiler(db)
        self.device_profiler = DeviceProfiler(db)
        
        # Detection statistics
        self.stats = {
            "telemetry_processed": 0,
            "anomalies_detected": 0,
            "false_positives": 0,
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            },
            "by_detector": {
                "statistical": 0,
                "ml_model": 0,
                "rule_based": 0
            }
        }
    
    def process_telemetry(
        self,
        device_id: str,
        telemetry: DeviceTelemetry
    ) -> List[AnomalyDetection]:
        """
        Process telemetry and detect anomalies.
        
        Args:
            device_id: Device identifier
            telemetry: Telemetry data to analyze
        
        Returns:
            List of detected anomalies
        """
        all_anomalies = []
        
        try:
            # Ensure device has baseline and profile
            self._ensure_baseline(device_id)
            self._ensure_profile(device_id)
            
            # Run all detectors
            # 1. Rule-based detection (highest priority)
            rule_anomalies = self.rule_based_detector.detect_anomalies(device_id, telemetry)
            all_anomalies.extend(rule_anomalies)
            self.stats["by_detector"]["rule_based"] += len(rule_anomalies)
            
            # 2. Statistical detection
            stat_anomalies = self.statistical_detector.detect_anomalies(device_id, telemetry)
            all_anomalies.extend(stat_anomalies)
            self.stats["by_detector"]["statistical"] += len(stat_anomalies)
            
            # 3. ML-based detection (if enabled)
            if self.ml_detector:
                ml_anomalies = self.ml_detector.detect_anomalies(device_id, telemetry)
                all_anomalies.extend(ml_anomalies)
                self.stats["by_detector"]["ml_model"] += len(ml_anomalies)
            
            # Deduplicate and prioritize anomalies
            unique_anomalies = self._deduplicate_anomalies(all_anomalies)
            
            # Update statistics
            self.stats["telemetry_processed"] += 1
            self.stats["anomalies_detected"] += len(unique_anomalies)
            
            for anomaly in unique_anomalies:
                self.stats["by_severity"][anomaly.anomaly_severity] += 1
            
            return unique_anomalies
            
        except Exception as e:
            print(f"[ERROR] Detection engine failed for device {device_id}: {e}")
            return []
    
    def process_batch(
        self,
        telemetry_batch: List[tuple[str, DeviceTelemetry]]
    ) -> Dict[str, List[AnomalyDetection]]:
        """
        Process batch of telemetry data.
        
        Args:
            telemetry_batch: List of (device_id, telemetry) tuples
        
        Returns:
            Dictionary mapping device_id to anomalies
        """
        results = {}
        
        for device_id, telemetry in telemetry_batch:
            anomalies = self.process_telemetry(device_id, telemetry)
            if anomalies:
                results[device_id] = anomalies
        
        return results
    
    def _ensure_baseline(self, device_id: str):
        """
        Ensure device has baseline profiles.
        
        Args:
            device_id: Device identifier
        """
        # Check if baselines exist and are recent
        from analytics.models import BehaviorBaseline
        
        recent_baseline = self.db.query(BehaviorBaseline).filter(
            BehaviorBaseline.device_id == device_id,
            BehaviorBaseline.is_active == True
        ).first()
        
        if not recent_baseline:
            # Build initial baselines in background
            # [Inference] In production, this would be queued as a background task
            print(f"[INFO] Building initial baselines for device {device_id}")
            try:
                self.baseline_profiler.build_all_baselines(device_id)
            except Exception as e:
                print(f"[WARN] Failed to build baselines for {device_id}: {e}")
    
    def _ensure_profile(self, device_id: str):
        """
        Ensure device has behavior profile.
        
        Args:
            device_id: Device identifier
        """
        from analytics.models import BehaviorProfile
        
        profile = self.db.query(BehaviorProfile).filter(
            BehaviorProfile.device_id == device_id
        ).first()
        
        if not profile or not profile.is_complete:
            # Build profile in background
            print(f"[INFO] Building behavior profile for device {device_id}")
            try:
                self.device_profiler.build_profile(device_id)
            except Exception as e:
                print(f"[WARN] Failed to build profile for {device_id}: {e}")
    
    def _deduplicate_anomalies(
        self,
        anomalies: List[AnomalyDetection]
    ) -> List[AnomalyDetection]:
        """
        Deduplicate anomalies detected by multiple detectors.
        
        Keep the highest severity/confidence anomaly for each feature.
        
        Args:
            anomalies: List of anomalies
        
        Returns:
            Deduplicated list
        """
        if len(anomalies) <= 1:
            return anomalies
        
        # Group by feature/type
        feature_groups = {}
        
        for anomaly in anomalies:
            key = f"{anomaly.anomaly_type}_{anomaly.feature_name}"
            
            if key not in feature_groups:
                feature_groups[key] = []
            
            feature_groups[key].append(anomaly)
        
        # Keep best anomaly from each group
        unique_anomalies = []
        
        for group in feature_groups.values():
            if len(group) == 1:
                unique_anomalies.append(group[0])
            else:
                # Prioritize by severity, then confidence, then anomaly score
                best = max(
                    group,
                    key=lambda a: (
                        self._severity_rank(a.anomaly_severity),
                        a.confidence,
                        a.anomaly_score
                    )
                )
                unique_anomalies.append(best)
        
        return unique_anomalies
    
    def _severity_rank(self, severity: str) -> int:
        """Get numeric rank for severity."""
        ranks = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1
        }
        return ranks.get(severity, 0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detection engine statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            **self.stats,
            "detection_rate": (
                self.stats["anomalies_detected"] / self.stats["telemetry_processed"]
                if self.stats["telemetry_processed"] > 0 else 0
            ),
            "false_positive_rate": (
                self.stats["false_positives"] / self.stats["anomalies_detected"]
                if self.stats["anomalies_detected"] > 0 else 0
            )
        }
    
    def mark_false_positive(self, anomaly_id: str):
        """
        Mark an anomaly as false positive.
        
        Args:
            anomaly_id: Anomaly identifier
        """
        anomaly = self.db.query(AnomalyDetection).filter(
            AnomalyDetection.anomaly_id == anomaly_id
        ).first()
        
        if anomaly:
            anomaly.is_false_positive = True
            anomaly.updated_at = datetime.now(UTC)
            self.db.commit()
            
            self.stats["false_positives"] += 1
            print(f"[INFO] Marked anomaly {anomaly_id} as false positive")
    
    def confirm_anomaly(self, anomaly_id: str):
        """
        Confirm an anomaly as real threat.
        
        Args:
            anomaly_id: Anomaly identifier
        """
        anomaly = self.db.query(AnomalyDetection).filter(
            AnomalyDetection.anomaly_id == anomaly_id
        ).first()
        
        if anomaly:
            anomaly.is_confirmed = True
            anomaly.updated_at = datetime.now(UTC)
            self.db.commit()
            
            print(f"[INFO] Confirmed anomaly {anomaly_id}")
    
    def resolve_anomaly(
        self,
        anomaly_id: str,
        resolved_by: str,
        notes: str = None
    ):
        """
        Mark anomaly as resolved.
        
        Args:
            anomaly_id: Anomaly identifier
            resolved_by: Who resolved it
            notes: Optional resolution notes
        """
        anomaly = self.db.query(AnomalyDetection).filter(
            AnomalyDetection.anomaly_id == anomaly_id
        ).first()
        
        if anomaly:
            anomaly.is_resolved = True
            anomaly.resolved_at = datetime.now(UTC)
            anomaly.resolved_by = resolved_by
            
            if notes:
                anomaly.analyst_notes = notes
            
            anomaly.updated_at = datetime.now(UTC)
            self.db.commit()
            
            print(f"[INFO] Resolved anomaly {anomaly_id}")

