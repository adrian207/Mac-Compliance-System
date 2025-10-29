"""
CSV Report Exporter

Author: Adrian Johnson <adrian207@gmail.com>

Exports reports to CSV format for data analysis and import.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class CSVExporter:
    """
    Exports reports to CSV format.
    
    Provides tabular data export for spreadsheet analysis.
    """
    
    def __init__(self, output_dir: str = "/tmp/reports"):
        """
        Initialize the CSV exporter.
        
        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        report_data: Dict[str, Any],
        report_title: str,
        filename: str = None
    ) -> str:
        """
        Export report data to CSV.
        
        Args:
            report_data: Report data dictionary
            report_title: Title for the CSV report
            filename: Optional custom filename
        
        Returns:
            Path to the generated CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_title.replace(' ', '_')}_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # Convert report data to tabular format
        rows = self._convert_to_rows(report_data)
        
        # Write CSV
        with open(output_path, 'w', newline='') as csvfile:
            if rows:
                writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        return str(output_path)
    
    def _convert_to_rows(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert report data to tabular rows.
        
        Args:
            report_data: Report data dictionary
        
        Returns:
            List of row dictionaries
        """
        # Check for common report structures
        if 'devices' in report_data:
            return self._convert_device_list(report_data['devices'])
        
        elif 'device_details' in report_data:
            return self._convert_device_list(report_data['device_details'])
        
        elif 'violations' in report_data:
            return report_data['violations']
        
        elif 'risk_score_history' in report_data:
            return report_data['risk_score_history']
        
        # Default: flatten top-level dictionary
        return [self._flatten_dict(report_data)]
    
    def _convert_device_list(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert device list to flat rows."""
        rows = []
        for device in devices:
            rows.append(self._flatten_dict(device))
        return rows
    
    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '_'
    ) -> Dict[str, Any]:
        """
        Flatten nested dictionary.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key prefix
            sep: Separator for nested keys
        
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to comma-separated strings
                items.append((new_key, ', '.join(str(x) for x in v)))
            else:
                items.append((new_key, v))
        
        return dict(items)

