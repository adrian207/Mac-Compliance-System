"""
Report Generators

Author: Adrian Johnson <adrian207@gmail.com>

Collection of report generator classes for different report types.
"""

from reporting.generators.base import BaseReportGenerator
from reporting.generators.executive_dashboard import ExecutiveDashboardGenerator
from reporting.generators.compliance_report import ComplianceReportGenerator
from reporting.generators.device_inventory import DeviceInventoryGenerator
from reporting.generators.security_posture import SecurityPostureGenerator
from reporting.generators.risk_trend import RiskTrendGenerator

__all__ = [
    "BaseReportGenerator",
    "ExecutiveDashboardGenerator",
    "ComplianceReportGenerator",
    "DeviceInventoryGenerator",
    "SecurityPostureGenerator",
    "RiskTrendGenerator",
]

