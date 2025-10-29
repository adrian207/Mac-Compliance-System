"""
Base Collector Class

Author: Adrian Johnson <adrian207@gmail.com>

Abstract base class for all telemetry collectors.
"""

from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import Any, Dict


class BaseCollector(ABC):
    """
    Abstract base class for telemetry collectors.
    
    All collectors must implement the collect() method.
    """
    
    def __init__(self):
        """Initialize the collector."""
        self.name = self.__class__.__name__
        self.last_collection_time = None
        self.last_collection_duration = None
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Collect telemetry data.
        
        Returns:
            Dict containing collected telemetry data
        
        Raises:
            Exception: If collection fails
        """
        pass
    
    def _execute_command(self, command: list, timeout: int = 10) -> str:
        """
        Execute a shell command and return output.
        
        Args:
            command: Command and arguments as list
            timeout: Command timeout in seconds
        
        Returns:
            Command output as string
        
        Raises:
            Exception: If command fails
        """
        import subprocess
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception(f"Command timed out: {' '.join(command)}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Command failed: {' '.join(command)} - {e.stderr}")
    
    def _parse_system_profiler(self, data_type: str) -> Dict[str, Any]:
        """
        Parse output from system_profiler command.
        
        Args:
            data_type: Data type to profile (e.g., "SPHardwareDataType")
        
        Returns:
            Parsed data as dictionary
        """
        import plistlib
        
        output = self._execute_command([
            "system_profiler",
            data_type,
            "-xml"
        ])
        
        try:
            return plistlib.loads(output.encode())
        except Exception as e:
            raise Exception(f"Failed to parse system_profiler output: {e}")

