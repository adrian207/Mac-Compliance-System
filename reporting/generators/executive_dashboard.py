"""
Executive Dashboard Report Generator

Author: Adrian Johnson <adrian207@gmail.com>

Generates executive-level dashboards with KPIs, trends, and summary metrics.
"""

from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional
from sqlalchemy import func

from reporting.generators.base import BaseReportGenerator
from reporting.models import ReportType, ReportFormat, RiskScoreHistory, ComplianceHistory
from telemetry.models import DeviceTelemetry
from risk_engine.models import RiskAssessment
from hardening.compliance_checker import ComplianceChecker


class ExecutiveDashboardGenerator(BaseReportGenerator):
    """
    Generates executive dashboard reports with high-level KPIs and trends.
    
    Provides actionable insights for leadership and stakeholders.
    """
    
    def __init__(self, db):
        """Initialize the executive dashboard generator."""
        super().__init__(db)
        self.report_type = ReportType.EXECUTIVE_DASHBOARD
        self.report_format = ReportFormat.JSON
    
    def get_title(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get report title."""
        if parameters and 'period' in parameters:
            return f"Executive Dashboard - {parameters['period'].title()}"
        return "Executive Dashboard"
    
    def get_description(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get report description."""
        return "High-level security metrics and KPIs for executive review"
    
    def generate(self, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate executive dashboard report.
        
        Args:
            parameters: Report parameters
                - period: "daily", "weekly", "monthly", "quarterly"
                - compare_previous: bool - Include comparison with previous period
        
        Returns:
            Dict containing dashboard data
        """
        parameters = parameters or {}
        period = parameters.get('period', 'monthly')
        compare_previous = parameters.get('compare_previous', True)
        
        # Calculate date ranges
        end_date = datetime.now(UTC)
        start_date = self._get_period_start_date(end_date, period)
        
        dashboard_data = {
            "report_metadata": {
                "generated_at": end_date.isoformat(),
                "period": period,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            },
            "summary": self._generate_summary(start_date, end_date),
            "device_metrics": self._generate_device_metrics(start_date, end_date),
            "risk_metrics": self._generate_risk_metrics(start_date, end_date),
            "compliance_metrics": self._generate_compliance_metrics(start_date, end_date),
            "security_incidents": self._generate_security_incidents(start_date, end_date),
            "top_risks": self._generate_top_risks(start_date, end_date),
            "recommendations": self._generate_recommendations()
        }
        
        # Add trend comparison if requested
        if compare_previous:
            previous_end = start_date
            previous_start = self._get_period_start_date(previous_end, period)
            dashboard_data["trend_comparison"] = self._generate_trend_comparison(
                start_date, end_date, previous_start, previous_end
            )
        
        return dashboard_data
    
    def _get_period_start_date(self, end_date: datetime, period: str) -> datetime:
        """Calculate start date based on period."""
        if period == "daily":
            return end_date - timedelta(days=1)
        elif period == "weekly":
            return end_date - timedelta(weeks=1)
        elif period == "monthly":
            return end_date - timedelta(days=30)
        elif period == "quarterly":
            return end_date - timedelta(days=90)
        else:
            return end_date - timedelta(days=30)
    
    def _generate_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate high-level summary metrics."""
        # Total devices
        total_devices = self.db.query(func.count(func.distinct(DeviceTelemetry.device_id))).scalar() or 0
        
        # Active devices (reported in period)
        active_devices = self.db.query(
            func.count(func.distinct(DeviceTelemetry.device_id))
        ).filter(
            DeviceTelemetry.collection_time >= start_date,
            DeviceTelemetry.collection_time <= end_date
        ).scalar() or 0
        
        # Critical risk devices
        critical_risk_devices = self.db.query(
            func.count(func.distinct(RiskAssessment.device_id))
        ).filter(
            RiskAssessment.risk_level == "critical",
            RiskAssessment.assessment_time >= start_date,
            RiskAssessment.assessment_time <= end_date
        ).scalar() or 0
        
        # Non-compliant devices
        non_compliant_devices = self.db.query(
            func.count(func.distinct(ComplianceHistory.device_id))
        ).filter(
            ComplianceHistory.is_compliant == False,
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date
        ).scalar() or 0
        
        # Average risk score
        avg_risk_score = self.db.query(
            func.avg(RiskScoreHistory.total_risk_score)
        ).filter(
            RiskScoreHistory.recorded_at >= start_date,
            RiskScoreHistory.recorded_at <= end_date
        ).scalar() or 0
        
        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "inactive_devices": total_devices - active_devices,
            "critical_risk_devices": critical_risk_devices,
            "non_compliant_devices": non_compliant_devices,
            "average_risk_score": round(float(avg_risk_score), 2),
            "health_score": self._calculate_health_score(
                total_devices, critical_risk_devices, non_compliant_devices
            )
        }
    
    def _calculate_health_score(
        self,
        total_devices: int,
        critical_risk: int,
        non_compliant: int
    ) -> float:
        """Calculate overall security health score (0-100)."""
        if total_devices == 0:
            return 100.0
        
        # Penalties
        critical_penalty = (critical_risk / total_devices) * 40  # Up to 40 points
        compliance_penalty = (non_compliant / total_devices) * 30  # Up to 30 points
        
        health_score = 100 - critical_penalty - compliance_penalty
        return max(0.0, round(health_score, 2))
    
    def _generate_device_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate device fleet metrics."""
        # OS version distribution
        os_versions = self.db.query(
            DeviceTelemetry.os_version,
            func.count(func.distinct(DeviceTelemetry.device_id)).label('count')
        ).filter(
            DeviceTelemetry.collection_time >= start_date,
            DeviceTelemetry.collection_time <= end_date
        ).group_by(DeviceTelemetry.os_version).all()
        
        return {
            "os_distribution": [
                {"version": ver, "count": count}
                for ver, count in os_versions
            ],
            "total_unique_devices": sum(count for _, count in os_versions)
        }
    
    def _generate_risk_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate risk-related metrics."""
        # Risk level distribution
        risk_distribution = self.db.query(
            RiskAssessment.risk_level,
            func.count(func.distinct(RiskAssessment.device_id)).label('count')
        ).filter(
            RiskAssessment.assessment_time >= start_date,
            RiskAssessment.assessment_time <= end_date
        ).group_by(RiskAssessment.risk_level).all()
        
        total_assessed = sum(count for _, count in risk_distribution)
        
        risk_dist_dict = dict(risk_distribution)
        
        return {
            "risk_distribution": [
                {"level": level, "count": count, "percentage": self._calculate_percentage(count, total_assessed)}
                for level, count in risk_distribution
            ],
            "total_assessed": total_assessed,
            "critical_count": risk_dist_dict.get("critical", 0),
            "high_count": risk_dist_dict.get("high", 0),
            "medium_count": risk_dist_dict.get("medium", 0),
            "low_count": risk_dist_dict.get("low", 0)
        }
    
    def _generate_compliance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance metrics."""
        # Latest compliance status per device
        latest_compliance = self.db.query(
            ComplianceHistory.device_id,
            ComplianceHistory.is_compliant,
            ComplianceHistory.compliance_score
        ).filter(
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date
        ).distinct(ComplianceHistory.device_id).all()
        
        compliant_count = sum(1 for _, is_compliant, _ in latest_compliance if is_compliant)
        total_count = len(latest_compliance)
        
        avg_compliance_score = sum(score or 0 for _, _, score in latest_compliance) / total_count if total_count > 0 else 0
        
        return {
            "total_devices_checked": total_count,
            "compliant_count": compliant_count,
            "non_compliant_count": total_count - compliant_count,
            "compliance_rate": self._calculate_percentage(compliant_count, total_count),
            "average_compliance_score": round(avg_compliance_score, 2)
        }
    
    def _generate_security_incidents(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate security incident summary."""
        # Devices with security issues
        security_issues = self.db.query(
            func.count(func.distinct(RiskAssessment.device_id))
        ).filter(
            RiskAssessment.assessment_time >= start_date,
            RiskAssessment.assessment_time <= end_date,
            RiskAssessment.risk_level.in_(["critical", "high"])
        ).scalar() or 0
        
        return {
            "devices_with_issues": security_issues,
            "incident_count": security_issues,  # Simplified - could track actual incidents
            "resolved_count": 0,  # Would require incident tracking
            "open_count": security_issues
        }
    
    def _generate_top_risks(self, start_date: datetime, end_date: datetime) -> list:
        """Generate top risk factors."""
        # Get most common risk factors
        risk_factors_query = self.db.query(
            RiskScoreHistory.risk_factors
        ).filter(
            RiskScoreHistory.recorded_at >= start_date,
            RiskScoreHistory.recorded_at <= end_date
        ).all()
        
        # Count risk factors
        risk_factor_counts = {}
        for (factors,) in risk_factors_query:
            if factors:
                for factor in factors:
                    risk_factor_counts[factor] = risk_factor_counts.get(factor, 0) + 1
        
        # Sort and return top 10
        top_risks = sorted(risk_factor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [
            {"risk_factor": factor, "occurrences": count}
            for factor, count in top_risks
        ]
    
    def _generate_recommendations(self) -> list:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Get current metrics for recommendations
        summary = self._generate_summary(
            datetime.now(UTC) - timedelta(days=7),
            datetime.now(UTC)
        )
        
        if summary["critical_risk_devices"] > 0:
            recommendations.append({
                "priority": "critical",
                "title": "Address Critical Risk Devices",
                "description": f"{summary['critical_risk_devices']} devices have critical risk levels requiring immediate attention",
                "action": "Review and remediate critical risk devices"
            })
        
        if summary["non_compliant_devices"] > summary["total_devices"] * 0.2:
            recommendations.append({
                "priority": "high",
                "title": "Improve Compliance Rate",
                "description": f"{summary['non_compliant_devices']} devices are non-compliant (>{20}%)",
                "action": "Deploy automated compliance remediation workflows"
            })
        
        if summary["inactive_devices"] > summary["total_devices"] * 0.1:
            recommendations.append({
                "priority": "medium",
                "title": "Investigate Inactive Devices",
                "description": f"{summary['inactive_devices']} devices haven't reported recently",
                "action": "Verify agent status and connectivity"
            })
        
        if summary["health_score"] < 70:
            recommendations.append({
                "priority": "high",
                "title": "Overall Security Health Below Target",
                "description": f"Current health score is {summary['health_score']}/100",
                "action": "Implement comprehensive security improvement plan"
            })
        
        return recommendations
    
    def _generate_trend_comparison(
        self,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime
    ) -> Dict[str, Any]:
        """Generate trend comparison between periods."""
        current_summary = self._generate_summary(current_start, current_end)
        previous_summary = self._generate_summary(previous_start, previous_end)
        
        return {
            "total_devices": {
                "current": current_summary["total_devices"],
                "previous": previous_summary["total_devices"],
                "change": current_summary["total_devices"] - previous_summary["total_devices"],
                "trend": self._get_trend_direction(
                    current_summary["total_devices"],
                    previous_summary["total_devices"]
                )
            },
            "critical_risk_devices": {
                "current": current_summary["critical_risk_devices"],
                "previous": previous_summary["critical_risk_devices"],
                "change": current_summary["critical_risk_devices"] - previous_summary["critical_risk_devices"],
                "trend": self._get_trend_direction(
                    current_summary["critical_risk_devices"],
                    previous_summary["critical_risk_devices"]
                )
            },
            "health_score": {
                "current": current_summary["health_score"],
                "previous": previous_summary["health_score"],
                "change": round(current_summary["health_score"] - previous_summary["health_score"], 2),
                "trend": self._get_trend_direction(
                    current_summary["health_score"],
                    previous_summary["health_score"]
                )
            }
        }
    
    def _extract_key_metrics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for quick reference."""
        summary = report_data.get("summary", {})
        return {
            "total_devices": summary.get("total_devices"),
            "critical_risk_devices": summary.get("critical_risk_devices"),
            "health_score": summary.get("health_score"),
            "compliance_rate": report_data.get("compliance_metrics", {}).get("compliance_rate")
        }

