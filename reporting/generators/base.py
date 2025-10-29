"""
Base Report Generator

Author: Adrian Johnson <adrian207@gmail.com>

Abstract base class for all report generators.
"""

from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import Any, Dict, Optional
import uuid

from sqlalchemy.orm import Session

from reporting.models import Report, ReportType, ReportFormat


class BaseReportGenerator(ABC):
    """
    Abstract base class for report generators.
    
    All report generators must implement the generate() method.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the report generator.
        
        Args:
            db: Database session
        """
        self.db = db
        self.report_type = ReportType.CUSTOM
        self.report_format = ReportFormat.JSON
    
    @abstractmethod
    def generate(self, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate the report.
        
        Args:
            parameters: Report parameters and filters
        
        Returns:
            Dict containing report data
        
        Raises:
            Exception: If report generation fails
        """
        pass
    
    @abstractmethod
    def get_title(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Get report title.
        
        Args:
            parameters: Report parameters
        
        Returns:
            Report title string
        """
        pass
    
    def save_report(
        self,
        report_data: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        generated_by: Optional[str] = None
    ) -> Report:
        """
        Save report metadata to database.
        
        Args:
            report_data: Generated report data
            parameters: Report parameters
            file_path: Path to exported file (if applicable)
            generated_by: User or system that generated the report
        
        Returns:
            Report database record
        """
        report_id = f"RPT-{uuid.uuid4().hex[:12].upper()}"
        
        report = Report(
            report_id=report_id,
            report_type=self.report_type,
            report_format=self.report_format,
            title=self.get_title(parameters),
            description=self.get_description(parameters),
            generated_at=datetime.now(UTC),
            generated_by=generated_by or "system",
            parameters=parameters or {},
            file_path=file_path,
            data_snapshot=self._extract_key_metrics(report_data),
            status="completed"
        )
        
        self.db.add(report)
        self.db.commit()
        
        return report
    
    def get_description(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Get report description.
        
        Args:
            parameters: Report parameters
        
        Returns:
            Report description string
        """
        return f"Generated {self.report_type.value} report"
    
    def _extract_key_metrics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key metrics from report data for quick reference.
        
        Args:
            report_data: Full report data
        
        Returns:
            Dict of key metrics
        """
        # Override in subclasses to extract relevant metrics
        return {}
    
    def _apply_date_filter(self, query, model, parameters: Optional[Dict[str, Any]] = None):
        """
        Apply date range filter to query.
        
        Args:
            query: SQLAlchemy query
            model: Model class with created_at or recorded_at field
            parameters: Report parameters with start_date/end_date
        
        Returns:
            Filtered query
        """
        if not parameters:
            return query
        
        # Determine date field
        date_field = getattr(model, 'recorded_at', None) or getattr(model, 'created_at', None)
        
        if not date_field:
            return query
        
        # Apply start date filter
        if 'start_date' in parameters:
            start_date = parameters['start_date']
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            query = query.filter(date_field >= start_date)
        
        # Apply end date filter
        if 'end_date' in parameters:
            end_date = parameters['end_date']
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            query = query.filter(date_field <= end_date)
        
        return query
    
    def _calculate_percentage(self, numerator: int, denominator: int) -> float:
        """
        Calculate percentage safely.
        
        Args:
            numerator: Numerator value
            denominator: Denominator value
        
        Returns:
            Percentage value (0-100)
        """
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)
    
    def _get_trend_direction(self, current: float, previous: float) -> str:
        """
        Get trend direction (up, down, stable).
        
        Args:
            current: Current value
            previous: Previous value
        
        Returns:
            Trend direction string
        """
        if current > previous:
            return "up"
        elif current < previous:
            return "down"
        else:
            return "stable"
    
    def _calculate_trend_percentage(self, current: float, previous: float) -> float:
        """
        Calculate trend percentage change.
        
        Args:
            current: Current value
            previous: Previous value
        
        Returns:
            Percentage change
        """
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        
        return round(((current - previous) / previous) * 100, 2)

