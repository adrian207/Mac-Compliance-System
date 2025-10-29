"""
Telemetry Collectors for Mac OS

Author: Adrian Johnson <adrian207@gmail.com>

Collection modules that gather various types of telemetry data from Mac OS endpoints.
"""

from agent.collectors.system_info import SystemInfoCollector
from agent.collectors.security_status import SecurityStatusCollector
from agent.collectors.network_info import NetworkInfoCollector
from agent.collectors.process_info import ProcessInfoCollector
from agent.collectors.software_inventory import SoftwareInventoryCollector

__all__ = [
    "SystemInfoCollector",
    "SecurityStatusCollector",
    "NetworkInfoCollector",
    "ProcessInfoCollector",
    "SoftwareInventoryCollector",
]

