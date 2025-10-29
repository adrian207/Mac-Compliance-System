"""
Compliance Report Generator

Author: Adrian Johnson <adrian207@gmail.com>

Generates detailed compliance reports with policy adherence, violations, and remediation tracking.
"""

from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional, List
from sqlalchemy import func

from reporting.generators.base import BaseReportGenerator
from reporting.models import ReportType, ReportFormat, ComplianceHistory
from hardening.compliance_checker import ComplianceChecker


class ComplianceReportGenerator(BaseReportGenerator):
    """
    Generates comprehensive compliance reports.
    
    Tracks policy adherence, violations, and compliance trends over time.
    """
    
    def __init__(self, db):
        """Initialize the compliance report generator."""
        super().__init__(db)
        self.report_type = ReportType.COMPLIANCE
        self.report_format = ReportFormat.PDF
        self.compliance_checker = ComplianceChecker(db)
    
    def get_title(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get report title."""
        if parameters and 'framework' in parameters:
            framework = parameters['framework'].upper()
            return f"Compliance Report - {framework}"
        return "Device Compliance Report"
    
    def get_description(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get report description."""
        return "Comprehensive compliance status and policy adherence report"
    
    def generate(self, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate compliance report.
        
        Args:
            parameters: Report parameters
                - framework: Compliance framework (e.g., "CIS", "NIST")
                - include_devices: bool - Include per-device details
                - start_date: Start date for historical data
                - end_date: End date for historical data
        
        Returns:
            Dict containing compliance report data
        """
        parameters = parameters or {}
        framework = parameters.get('framework', 'CIS')
        include_devices = parameters.get('include_devices', True)
        
        # Date range
        end_date = datetime.now(UTC)
        start_date = parameters.get('start_date', end_date - timedelta(days=30))
        
        report_data = {
            "report_metadata": {
                "generated_at": end_date.isoformat(),
                "framework": framework,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            },
            "executive_summary": self._generate_executive_summary(start_date, end_date),
            "compliance_overview": self._generate_compliance_overview(start_date, end_date),
            "policy_compliance": self._generate_policy_compliance(framework),
            "violations": self._generate_violations(start_date, end_date),
            "remediation_tracking": self._generate_remediation_tracking(start_date, end_date),
            "compliance_trends": self._generate_compliance_trends(start_date, end_date)
        }
        
        # Add per-device details if requested
        if include_devices:
            report_data["device_details"] = self._generate_device_details(start_date, end_date)
        
        return report_data
    
    def _generate_executive_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate executive summary of compliance status."""
        # Get latest compliance status for all devices
        latest_compliance = self.db.query(
            ComplianceHistory.device_id,
            ComplianceHistory.is_compliant,
            ComplianceHistory.compliance_score,
            ComplianceHistory.policies_passed,
            ComplianceHistory.policies_failed
        ).filter(
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date
        ).distinct(ComplianceHistory.device_id).all()
        
        total_devices = len(latest_compliance)
        compliant_devices = sum(1 for _, is_compliant, _, _, _ in latest_compliance if is_compliant)
        non_compliant_devices = total_devices - compliant_devices
        
        total_policies = sum(passed + failed for _, _, _, passed, failed in latest_compliance)
        total_passed = sum(passed for _, _, _, passed, _ in latest_compliance)
        total_failed = sum(failed for _, _, _, _, failed in latest_compliance)
        
        avg_compliance_score = (
            sum(score or 0 for _, _, score, _, _ in latest_compliance) / total_devices
            if total_devices > 0 else 0
        )
        
        return {
            "total_devices_assessed": total_devices,
            "compliant_devices": compliant_devices,
            "non_compliant_devices": non_compliant_devices,
            "compliance_rate": self._calculate_percentage(compliant_devices, total_devices),
            "average_compliance_score": round(avg_compliance_score, 2),
            "total_policies_evaluated": total_policies,
            "policies_passed": total_passed,
            "policies_failed": total_failed,
            "pass_rate": self._calculate_percentage(total_passed, total_policies)
        }
    
    def _generate_compliance_overview(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance overview by category."""
        # Compliance status distribution
        status_dist = self.db.query(
            ComplianceHistory.is_compliant,
            func.count(func.distinct(ComplianceHistory.device_id)).label('count')
        ).filter(
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date
        ).group_by(ComplianceHistory.is_compliant).all()
        
        total = sum(count for _, count in status_dist)
        
        return {
            "status_distribution": [
                {
                    "status": "compliant" if is_compliant else "non_compliant",
                    "count": count,
                    "percentage": self._calculate_percentage(count, total)
                }
                for is_compliant, count in status_dist
            ],
            "compliance_score_ranges": self._get_compliance_score_ranges(start_date, end_date)
        }
    
    def _get_compliance_score_ranges(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get distribution of compliance scores by range."""
        scores = self.db.query(
            ComplianceHistory.compliance_score
        ).filter(
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date,
            ComplianceHistory.compliance_score.isnot(None)
        ).distinct(ComplianceHistory.device_id).all()
        
        ranges = {
            "90-100": 0,
            "70-89": 0,
            "50-69": 0,
            "0-49": 0
        }
        
        for (score,) in scores:
            if score >= 90:
                ranges["90-100"] += 1
            elif score >= 70:
                ranges["70-89"] += 1
            elif score >= 50:
                ranges["50-69"] += 1
            else:
                ranges["0-49"] += 1
        
        total = len(scores)
        
        return [
            {
                "range": range_name,
                "count": count,
                "percentage": self._calculate_percentage(count, total)
            }
            for range_name, count in ranges.items()
        ]
    
    def _generate_policy_compliance(self, framework: str) -> List[Dict[str, Any]]:
        """Generate policy-level compliance details."""
        # Get policy templates for framework
        from hardening.policy_templates import POLICY_TEMPLATES
        
        policies = []
        
        # Get relevant policies based on framework
        for policy_name, policy_config in POLICY_TEMPLATES.items():
            if framework.upper() in policy_config.get('frameworks', []):
                policies.append({
                    "policy_name": policy_name,
                    "policy_id": policy_config.get('id'),
                    "category": policy_config.get('category', 'general'),
                    "severity": policy_config.get('severity', 'medium'),
                    "description": policy_config.get('description', ''),
                    "compliance_rate": 0,  # Would calculate from actual checks
                    "devices_passed": 0,
                    "devices_failed": 0
                })
        
        return policies
    
    def _generate_violations(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate list of compliance violations."""
        violations = []
        
        # Get devices with failures
        devices_with_failures = self.db.query(
            ComplianceHistory.device_id,
            ComplianceHistory.critical_failures,
            ComplianceHistory.recorded_at
        ).filter(
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date,
            ComplianceHistory.critical_failures.isnot(None)
        ).order_by(ComplianceHistory.recorded_at.desc()).all()
        
        for device_id, failures, recorded_at in devices_with_failures:
            if failures:
                for failure in failures:
                    violations.append({
                        "device_id": device_id,
                        "violation_type": failure.get('policy', 'unknown'),
                        "severity": failure.get('severity', 'medium'),
                        "description": failure.get('message', ''),
                        "detected_at": recorded_at.isoformat(),
                        "status": "open"
                    })
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        violations.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return violations[:50]  # Limit to top 50
    
    def _generate_remediation_tracking(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate remediation tracking metrics."""
        # Get devices that changed status
        status_changes = self.db.query(
            ComplianceHistory.device_id,
            ComplianceHistory.status_changed,
            ComplianceHistory.newly_passed_policies,
            ComplianceHistory.newly_failed_policies
        ).filter(
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date,
            ComplianceHistory.status_changed == True
        ).all()
        
        remediated_count = sum(
            len(passed or []) for _, _, passed, _ in status_changes
        )
        
        new_violations_count = sum(
            len(failed or []) for _, _, _, failed in status_changes
        )
        
        return {
            "total_remediations": remediated_count,
            "new_violations": new_violations_count,
            "net_improvement": remediated_count - new_violations_count,
            "devices_improved": sum(
                1 for _, _, passed, failed in status_changes
                if len(passed or []) > len(failed or [])
            ),
            "devices_declined": sum(
                1 for _, _, passed, failed in status_changes
                if len(failed or []) > len(passed or [])
            )
        }
    
    def _generate_compliance_trends(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate compliance trends over time."""
        # Get daily compliance snapshots
        trends = []
        
        # Group by day
        daily_compliance = self.db.query(
            func.date(ComplianceHistory.recorded_at).label('date'),
            func.avg(ComplianceHistory.compliance_score).label('avg_score'),
            func.count(func.distinct(ComplianceHistory.device_id)).label('device_count')
        ).filter(
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date
        ).group_by(func.date(ComplianceHistory.recorded_at)).all()
        
        for date, avg_score, device_count in daily_compliance:
            trends.append({
                "date": date.isoformat(),
                "average_compliance_score": round(float(avg_score or 0), 2),
                "devices_assessed": device_count
            })
        
        return trends
    
    def _generate_device_details(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate per-device compliance details."""
        device_details = []
        
        # Get latest compliance for each device
        latest_compliance = self.db.query(
            ComplianceHistory.device_id,
            ComplianceHistory.is_compliant,
            ComplianceHistory.compliance_score,
            ComplianceHistory.policies_total,
            ComplianceHistory.policies_passed,
            ComplianceHistory.policies_failed,
            ComplianceHistory.critical_failures,
            ComplianceHistory.recorded_at
        ).filter(
            ComplianceHistory.recorded_at >= start_date,
            ComplianceHistory.recorded_at <= end_date
        ).distinct(ComplianceHistory.device_id).all()
        
        for (device_id, is_compliant, score, total, passed, failed, 
             critical_failures, recorded_at) in latest_compliance:
            
            device_details.append({
                "device_id": device_id,
                "compliance_status": "compliant" if is_compliant else "non_compliant",
                "compliance_score": score,
                "policies_total": total,
                "policies_passed": passed,
                "policies_failed": failed,
                "critical_failures_count": len(critical_failures or []),
                "last_assessed": recorded_at.isoformat()
            })
        
        # Sort by compliance score (lowest first)
        device_details.sort(key=lambda x: x['compliance_score'] or 0)
        
        return device_details
    
    def _extract_key_metrics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for quick reference."""
        summary = report_data.get("executive_summary", {})
        return {
            "total_devices": summary.get("total_devices_assessed"),
            "compliance_rate": summary.get("compliance_rate"),
            "non_compliant_devices": summary.get("non_compliant_devices"),
            "critical_violations": len([
                v for v in report_data.get("violations", [])
                if v.get("severity") == "critical"
            ])
        }

