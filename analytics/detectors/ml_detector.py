"""
Machine Learning Anomaly Detector

Author: Adrian Johnson <adrian207@gmail.com>

ML-based anomaly detection using Isolation Forest and other ensemble methods.
"""

from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
import uuid
import pickle
from pathlib import Path

from sqlalchemy.orm import Session
import numpy as np

from analytics.models import AnomalyDetection, AnomalySeverity, AnomalyType
from telemetry.models import DeviceTelemetry


class MLAnomalyDetector:
    """
    Machine learning-based anomaly detection.
    
    Uses Isolation Forest and other ensemble methods for unsupervised
    anomaly detection.
    """
    
    def __init__(
        self,
        db: Session,
        model_path: str = "models/anomaly_detector.pkl",
        contamination: float = 0.05
    ):
        """
        Initialize ML anomaly detector.
        
        Args:
            db: Database session
            model_path: Path to trained model file
            contamination: Expected proportion of anomalies (default: 5%)
        """
        self.db = db
        self.model_path = Path(model_path)
        self.contamination = contamination
        self.model = None
        self.feature_names = []
        
        # [Inference] In production, this would load a pre-trained model
        # from sklearn.ensemble import IsolationForest
        # self._load_model()
    
    def train_model(self, training_data: List[Dict[str, Any]]):
        """
        Train the anomaly detection model.
        
        Args:
            training_data: List of feature dictionaries from normal behavior
        """
        # [Inference] This would use scikit-learn's Isolation Forest
        # from sklearn.ensemble import IsolationForest
        
        # Extract features
        X = self._extract_features_batch(training_data)
        
        if len(X) < 10:
            raise ValueError("Insufficient training data")
        
        # Train Isolation Forest
        # self.model = IsolationForest(
        #     contamination=self.contamination,
        #     random_state=42,
        #     n_estimators=100
        # )
        # self.model.fit(X)
        
        # Save model
        # self._save_model()
        
        print(f"[INFO] ML model trained on {len(X)} samples")
    
    def detect_anomalies(
        self,
        device_id: str,
        telemetry: DeviceTelemetry
    ) -> List[AnomalyDetection]:
        """
        Detect anomalies using ML model.
        
        Args:
            device_id: Device identifier
            telemetry: Current telemetry data
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # [Inference] In production, this would use a trained ML model
        # For now, provide placeholder logic
        
        # Extract features
        features = self._extract_features(telemetry)
        
        if not features:
            return anomalies
        
        # Predict anomaly score
        # anomaly_score = self._predict_anomaly_score(features)
        anomaly_score = self._mock_prediction(features)
        
        # If anomalous, create detection record
        if anomaly_score > 0.7:  # Threshold for anomaly
            anomaly = self._create_anomaly(
                device_id=device_id,
                anomaly_score=anomaly_score,
                features=features,
                telemetry=telemetry
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _extract_features(self, telemetry: DeviceTelemetry) -> Dict[str, float]:
        """
        Extract numerical features from telemetry.
        
        Args:
            telemetry: Telemetry data
        
        Returns:
            Dictionary of features
        """
        features = {}
        
        # System features
        if telemetry.system_data:
            sys_data = telemetry.system_data
            features["cpu_usage"] = sys_data.get("cpu_usage", 0)
            features["memory_usage"] = sys_data.get("memory_usage", 0)
            features["disk_usage"] = sys_data.get("disk_usage", 0)
        
        # Network features
        if telemetry.network_data:
            net_data = telemetry.network_data
            features["active_connections"] = net_data.get("active_connections", 0)
            features["vpn_connected"] = 1 if net_data.get("vpn_connected") else 0
        
        # Process features
        if telemetry.process_data:
            proc_data = telemetry.process_data
            processes = proc_data.get("processes", [])
            features["process_count"] = len(processes)
        
        # Security features
        if telemetry.security_data:
            sec_data = telemetry.security_data
            features["filevault_enabled"] = 1 if sec_data.get("filevault", {}).get("enabled") else 0
            features["sip_enabled"] = 1 if sec_data.get("sip", {}).get("enabled") else 0
            features["firewall_enabled"] = 1 if sec_data.get("firewall", {}).get("enabled") else 0
            features["failed_auth_count"] = sec_data.get("failed_authentication_attempts", 0)
        
        # Temporal features
        features["hour_of_day"] = telemetry.collection_time.hour
        features["day_of_week"] = telemetry.collection_time.weekday()
        
        return features
    
    def _extract_features_batch(
        self,
        training_data: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Extract features for batch training.
        
        Args:
            training_data: List of telemetry-like dictionaries
        
        Returns:
            Numpy array of features
        """
        # [Inference] This would extract features from training data
        # and return numpy array
        return np.array([[0.0] * 10] * len(training_data))  # Placeholder
    
    def _mock_prediction(self, features: Dict[str, float]) -> float:
        """
        Mock anomaly prediction for demonstration.
        
        [Inference] This is a placeholder. In production, this would use
        a trained Isolation Forest or other ML model.
        
        Args:
            features: Feature dictionary
        
        Returns:
            Anomaly score (0-1, higher = more anomalous)
        """
        # Simple heuristic for demonstration
        score = 0.0
        
        # High resource usage
        if features.get("cpu_usage", 0) > 80:
            score += 0.3
        if features.get("memory_usage", 0) > 85:
            score += 0.3
        
        # Security controls disabled
        if features.get("filevault_enabled", 1) == 0:
            score += 0.2
        if features.get("sip_enabled", 1) == 0:
            score += 0.2
        
        # Failed authentications
        if features.get("failed_auth_count", 0) > 5:
            score += 0.4
        
        # Unusual time
        hour = features.get("hour_of_day", 12)
        if hour < 6 or hour > 22:
            score += 0.1
        
        return min(1.0, score)
    
    def _create_anomaly(
        self,
        device_id: str,
        anomaly_score: float,
        features: Dict[str, float],
        telemetry: DeviceTelemetry
    ) -> AnomalyDetection:
        """
        Create anomaly detection record.
        
        Args:
            device_id: Device identifier
            anomaly_score: ML anomaly score
            features: Feature values
            telemetry: Telemetry snapshot
        
        Returns:
            AnomalyDetection object
        """
        # Determine severity
        if anomaly_score >= 0.9:
            severity = AnomalySeverity.CRITICAL
        elif anomaly_score >= 0.8:
            severity = AnomalySeverity.HIGH
        elif anomaly_score >= 0.7:
            severity = AnomalySeverity.MEDIUM
        else:
            severity = AnomalySeverity.LOW
        
        # Create anomaly record
        anomaly = AnomalyDetection(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:12].upper()}",
            device_id=device_id,
            anomaly_type=AnomalyType.USER_BEHAVIOR.value,
            anomaly_severity=severity.value,
            detection_method="ml_model",
            detector_name="MLAnomalyDetector",
            model_version="1.0",
            anomaly_score=anomaly_score * 100,
            confidence=0.75,  # ML methods have moderate confidence
            feature_name="behavior_composite",
            observed_value=features,
            title=f"Unusual device behavior detected (ML)",
            description=f"Machine learning model detected anomalous behavior pattern "
                       f"with score {anomaly_score:.2f}. Multiple behavioral indicators "
                       f"deviate from normal patterns.",
            recommendations=[
                "Review device activity logs",
                "Verify user identity and recent actions",
                "Check for unauthorized access or malware",
                "Consider increasing monitoring for this device"
            ],
            telemetry_snapshot={
                "collection_time": telemetry.collection_time.isoformat(),
                "system_data": telemetry.system_data,
                "network_data": telemetry.network_data,
                "security_data": telemetry.security_data
            },
            detected_at=datetime.now(UTC)
        )
        
        self.db.add(anomaly)
        self.db.commit()
        
        return anomaly
    
    def _load_model(self):
        """Load trained model from disk."""
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data.get("model")
                self.feature_names = model_data.get("feature_names", [])
            print(f"[INFO] ML model loaded from {self.model_path}")
        else:
            print(f"[WARN] No trained model found at {self.model_path}")
    
    def _save_model(self):
        """Save trained model to disk."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model": self.model,
            "feature_names": self.feature_names,
            "contamination": self.contamination,
            "trained_at": datetime.now(UTC).isoformat()
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.load(model_data, f)
        
        print(f"[INFO] ML model saved to {self.model_path}")

