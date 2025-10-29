"""
Risk Trend Report Generator

Author: Adrian Johnson <adrian207@gmail.com>

Generates risk trend reports with historical analysis and forecasting.
"""

from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional, List
from sqlalchemy import func

from reporting.generators.base import BaseReportGenerator
from reporting.models import ReportType, ReportFormat, RiskScoreHistory
from risk_engine.models import RiskAssessment


class RiskTrendGenerator(BaseReportGenerator):
    """
    Generates risk trend reports with historical analysis.
    
    Tracks risk score changes, identifies trends, and provides forecasting.
    """
    
    def __init__(self, db):
        """Initialize the risk trend generator."""
        super().__init__(db)
        self.report_type = ReportType.RISK_TREND
        self.report_format = ReportFormat.JSON
    
    def get_title(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get report title."""
        return "Risk Trend Analysis Report"
    
    def get_description(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get report description."""
        return "Historical risk score trends and predictive analysis"
    
    def generate(self, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate risk trend report.
        
        Args:
            parameters: Report parameters
                - start_date: Start date for trend analysis
                - end_date: End date for trend analysis
                - device_id: Optional specific device to analyze
        
        Returns:
            Dict containing risk trend data
        """
        parameters = parameters or {}
        end_date = datetime.now(UTC)
        start_date = parameters.get('start_date', end_date - timedelta(days=90))
        device_id = parameters.get('device_id')
        
        report_data = {
            "report_metadata": {
                "generated_at": end_date.isoformat(),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "device_id": device_id
            },
            "trend_summary": self._generate_trend_summary(start_date, end_date, device_id),
            "risk_score_history": self._generate_risk_score_history(start_date, end_date, device_id),
            "risk_level_changes": self._generate_risk_level_changes(start_date, end_date, device_id),
            "risk_factor_trends": self._generate_risk_factor_trends(start_date, end_date, device_id),
            "device_risk_distribution": self._generate_device_risk_distribution(end_date)
        }
        
        return report_data
    
    def _generate_trend_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        device_id: Optional[str]
    ) -> Dict[str, Any]:
        """Generate trend summary statistics."""
        query = self.db.query(RiskScoreHistory).filter(
            RiskScoreHistory.recorded_at >= start_date,
            RiskScoreHistory.recorded_at <= end_date
        )
        
        if device_id:
            query = query.filter(RiskScoreHistory.device_id == device_id)
        
        risk_history = query.all()
        
        if not risk_history:
            return {
                "data_points": 0,
                "average_risk_score": 0,
                "trend_direction": "stable"
            }
        
        scores = [r.total_risk_score for r in risk_history]
        avg_score = sum(scores) / len(scores)
        
        # Calculate trend (compare first half vs second half)
        midpoint = len(scores) // 2
        first_half_avg = sum(scores[:midpoint]) / midpoint if midpoint > 0 else 0
        second_half_avg = sum(scores[midpoint:]) / (len(scores) - midpoint) if len(scores) > midpoint else 0
        
        trend_direction = self._get_trend_direction(second_half_avg, first_half_avg)
        trend_percentage = self._calculate_trend_percentage(second_half_avg, first_half_avg)
        
        return {
            "data_points": len(risk_history),
            "average_risk_score": round(avg_score, 2),
            "min_risk_score": min(scores),
            "max_risk_score": max(scores),
            "trend_direction": trend_direction,
            "trend_percentage": trend_percentage,
            "devices_analyzed": len(set(r.device_id for r in risk_history))
        }
    
    def _generate_risk_score_history(
        self,
        start_date: datetime,
        end_date: datetime,
        device_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate time-series risk score history."""
        query = self.db.query(
            func.date(RiskScoreHistory.recorded_at).label('date'),
            func.avg(RiskScoreHistory.total_risk_score).label('avg_score'),
            func.min(RiskScoreHistory.total_risk_score).label('min_score'),
            func.max(RiskScoreHistory.total_risk_score).label('max_score'),
            func.count(RiskScoreHistory.id).label('data_points')
        ).filter(
            RiskScoreHistory.recorded_at >= start_date,
            RiskScoreHistory.recorded_at <= end_date
        )
        
        if device_id:
            query = query.filter(RiskScoreHistory.device_id == device_id)
        
        query = query.group_by(func.date(RiskScoreHistory.recorded_at))
        
        history = query.all()
        
        return [
            {
                "date": date.isoformat(),
                "average_score": round(float(avg_score), 2),
                "min_score": int(min_score),
                "max_score": int(max_score),
                "data_points": data_points
            }
            for date, avg_score, min_score, max_score, data_points in history
        ]
    
    def _generate_risk_level_changes(
        self,
        start_date: datetime,
        end_date: datetime,
        device_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate risk level change events."""
        query = self.db.query(RiskScoreHistory).filter(
            RiskScoreHistory.recorded_at >= start_date,
            RiskScoreHistory.recorded_at <= end_date,
            RiskScoreHistory.risk_level_changed == True
        )
        
        if device_id:
            query = query.filter(RiskScoreHistory.device_id == device_id)
        
        changes = query.order_by(RiskScoreHistory.recorded_at.desc()).limit(50).all()
        
        return [
            {
                "device_id": change.device_id,
                "previous_risk_level": self._infer_previous_level(change.risk_level, change.score_delta),
                "new_risk_level": change.risk_level,
                "score_delta": change.score_delta,
                "risk_factors": change.risk_factors,
                "changed_at": change.recorded_at.isoformat()
            }
            for change in changes
        ]
    
    def _infer_previous_level(self, current_level: str, score_delta: int) -> str:
        """Infer previous risk level from current level and delta."""
        # Simplified inference
        levels = ["low", "medium", "high", "critical"]
        try:
            current_index = levels.index(current_level)
            if score_delta > 0:
                previous_index = max(0, current_index - 1)
            else:
                previous_index = min(len(levels) - 1, current_index + 1)
            return levels[previous_index]
        except ValueError:
            return "unknown"
    
    def _generate_risk_factor_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        device_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate risk factor occurrence trends."""
        query = self.db.query(RiskScoreHistory.risk_factors).filter(
            RiskScoreHistory.recorded_at >= start_date,
            RiskScoreHistory.recorded_at <= end_date
        )
        
        if device_id:
            query = query.filter(RiskScoreHistory.device_id == device_id)
        
        risk_factors_list = query.all()
        
        # Count occurrences
        factor_counts = {}
        for (factors,) in risk_factors_list:
            if factors:
                for factor in factors:
                    factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        # Sort by count
        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        
        total_factors = sum(factor_counts.values())
        
        return [
            {
                "risk_factor": factor,
                "occurrence_count": count,
                "percentage": self._calculate_percentage(count, total_factors)
            }
            for factor, count in sorted_factors[:20]
        ]
    
    def _generate_device_risk_distribution(self, end_date: datetime) -> Dict[str, Any]:
        """Generate current risk distribution across devices."""
        # Get latest risk assessments
        latest_assessments = self.db.query(
            RiskAssessment.risk_level,
            func.count(func.distinct(RiskAssessment.device_id)).label('count')
        ).filter(
            RiskAssessment.assessment_time >= end_date - timedelta(days=1)
        ).group_by(RiskAssessment.risk_level).all()
        
        total = sum(count for _, count in latest_assessments)
        
        distribution = {}
        for level, count in latest_assessments:
            distribution[level] = {
                "count": count,
                "percentage": self._calculate_percentage(count, total)
            }
        
        return {
            "total_devices": total,
            "distribution": distribution
        }
    
    def _extract_key_metrics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for quick reference."""
        summary = report_data.get("trend_summary", {})
        return {
            "average_risk_score": summary.get("average_risk_score"),
            "trend_direction": summary.get("trend_direction"),
            "trend_percentage": summary.get("trend_percentage"),
            "devices_analyzed": summary.get("devices_analyzed")
        }

