"""
Mock Kandji API Server

Author: Adrian Johnson <adrian207@gmail.com>

Simulates Kandji API for testing without live credentials.
"""

from datetime import datetime, UTC
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Header
import uvicorn


app = FastAPI(title="Mock Kandji API")

# Mock data storage
mock_devices = [
    {
        "device_id": "mock-kandji-device-1",
        "device_name": "MacBook-Pro-123",
        "serial_number": "C02ABC123DEF",
        "model": "MacBook Pro (16-inch, 2023)",
        "os_version": "14.1.1",
        "platform": "macOS",
        "is_enrolled": True,
        "enrollment_date": "2024-01-15T10:00:00Z",
        "last_check_in": datetime.now(UTC).isoformat(),
        "user": {
            "name": "John Doe",
            "email": "john.doe@example.com"
        },
        "compliance_status": "compliant",
        "blueprint_id": "bp-001",
        "blueprint_name": "Corporate MacBook Policy",
        "model_identifier": "MacBookPro18,3",
        "total_ram": 32,
        "storage_capacity": 1000,
        "storage_available": 450,
        "filevault_enabled": True,
        "filevault_status": "on",
        "gatekeeper_enabled": True,
        "firewall_enabled": True,
        "sip_enabled": True,
        "ip_address": "192.168.1.100",
        "mac_address": "00:1A:2B:3C:4D:5E",
        "agent_version": "1.2.3"
    },
    {
        "device_id": "mock-kandji-device-2",
        "device_name": "MacBook-Air-456",
        "serial_number": "C02XYZ456GHI",
        "model": "MacBook Air (13-inch, 2023)",
        "os_version": "14.0",
        "platform": "macOS",
        "is_enrolled": True,
        "enrollment_date": "2024-02-20T14:30:00Z",
        "last_check_in": datetime.now(UTC).isoformat(),
        "user": {
            "name": "Jane Smith",
            "email": "jane.smith@example.com"
        },
        "compliance_status": "non_compliant",
        "blueprint_id": "bp-002",
        "blueprint_name": "Standard User Policy",
        "model_identifier": "MacBookAir10,1",
        "total_ram": 16,
        "storage_capacity": 512,
        "storage_available": 200,
        "filevault_enabled": False,
        "filevault_status": "off",
        "gatekeeper_enabled": True,
        "firewall_enabled": False,
        "sip_enabled": True,
        "ip_address": "192.168.1.101",
        "mac_address": "00:1A:2B:3C:4D:5F",
        "agent_version": "1.2.3"
    }
]

mock_users = [
    {
        "id": "user-001",
        "email": "john.doe@example.com",
        "name": "John Doe",
        "username": "jdoe",
        "device_count": 1
    },
    {
        "id": "user-002",
        "email": "jane.smith@example.com",
        "name": "Jane Smith",
        "username": "jsmith",
        "device_count": 1
    }
]

mock_blueprints = [
    {
        "id": "bp-001",
        "name": "Corporate MacBook Policy",
        "description": "Standard corporate security policy",
        "device_count": 1
    },
    {
        "id": "bp-002",
        "name": "Standard User Policy",
        "description": "Basic user security requirements",
        "device_count": 1
    }
]


@app.get("/api/v1/")
async def root(authorization: str = Header(None)):
    """API root endpoint."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return {
        "version": "v1",
        "status": "ok"
    }


@app.get("/api/v1/devices")
async def get_devices(
    page: int = 1,
    per_page: int = 100,
    authorization: str = Header(None)
):
    """Get devices."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Simple pagination
    start = (page - 1) * per_page
    end = start + per_page
    page_devices = mock_devices[start:end]
    
    return {
        "results": page_devices,
        "next": None if end >= len(mock_devices) else f"/api/v1/devices?page={page+1}"
    }


@app.get("/api/v1/devices/{device_id}")
async def get_device(device_id: str, authorization: str = Header(None)):
    """Get device details."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    for device in mock_devices:
        if device["device_id"] == device_id:
            return device
    
    raise HTTPException(status_code=404, detail="Device not found")


@app.get("/api/v1/devices/{device_id}/status")
async def get_device_compliance(device_id: str, authorization: str = Header(None)):
    """Get device compliance status."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    for device in mock_devices:
        if device["device_id"] == device_id:
            return {
                "compliance_status": device["compliance_status"],
                "parameters": [
                    {"name": "FileVault", "status": "pass" if device["filevault_enabled"] else "fail"},
                    {"name": "Firewall", "status": "pass" if device["firewall_enabled"] else "fail"},
                    {"name": "Gatekeeper", "status": "pass" if device["gatekeeper_enabled"] else "fail"}
                ],
                "issues": [] if device["compliance_status"] == "compliant" else [
                    "FileVault not enabled",
                    "Firewall not enabled"
                ]
            }
    
    raise HTTPException(status_code=404, detail="Device not found")


@app.get("/api/v1/users")
async def get_users(
    page: int = 1,
    per_page: int = 100,
    authorization: str = Header(None)
):
    """Get users."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    start = (page - 1) * per_page
    end = start + per_page
    page_users = mock_users[start:end]
    
    return {
        "results": page_users,
        "next": None if end >= len(mock_users) else f"/api/v1/users?page={page+1}"
    }


@app.get("/api/v1/blueprints")
async def get_blueprints(authorization: str = Header(None)):
    """Get blueprints."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return mock_blueprints


@app.post("/api/v1/devices/{device_id}/action")
async def send_device_action(
    device_id: str,
    payload: Dict[str, Any],
    authorization: str = Header(None)
):
    """Send remote command to device."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Find device
    device_found = False
    for device in mock_devices:
        if device["device_id"] == device_id:
            device_found = True
            break
    
    if not device_found:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "command_id": f"cmd-{device_id}-123",
        "status": "sent"
    }


if __name__ == "__main__":
    print("Starting Mock Kandji API server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)

