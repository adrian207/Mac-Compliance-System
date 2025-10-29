"""
Mock CrowdStrike Falcon API Server

Author: Adrian Johnson <adrian207@gmail.com>

Simulates CrowdStrike Falcon EDR API for testing.
"""

from datetime import datetime, UTC, timedelta
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import secrets


app = FastAPI(title="Mock CrowdStrike Falcon API")
security = HTTPBasic()

# Mock OAuth2 tokens
mock_tokens = {}

# Mock data
mock_devices = [
    {
        "device_id": "crowdstrike-dev-1",
        "hostname": "macbook-pro-123",
        "platform_name": "Mac",
        "os_version": "macOS 14.1.1",
        "agent_version": "7.10.17806",
        "status": "normal",
        "last_seen": datetime.now(UTC).isoformat(),
        "first_seen": "2024-01-15T10:00:00Z",
        "local_ip": "192.168.1.100",
        "external_ip": "203.0.113.100",
        "mac_address": "00:1A:2B:3C:4D:5E",
        "system_manufacturer": "Apple Inc.",
        "system_product_name": "MacBookPro18,3",
        "bios_version": "MBP183.88Z.F000.B00.2310122031",
        "agent_local_time": datetime.now(UTC).isoformat(),
        "reduced_functionality_mode": "no"
    },
    {
        "device_id": "crowdstrike-dev-2",
        "hostname": "macbook-air-456",
        "platform_name": "Mac",
        "os_version": "macOS 14.0",
        "agent_version": "7.10.17806",
        "status": "normal",
        "last_seen": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        "first_seen": "2024-02-20T14:00:00Z",
        "local_ip": "192.168.1.101",
        "external_ip": "203.0.113.101",
        "mac_address": "00:1A:2B:3C:4D:5F",
        "system_manufacturer": "Apple Inc.",
        "system_product_name": "MacBookAir10,1",
        "bios_version": "MBA101.88Z.F000.B00.2310122031",
        "agent_local_time": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        "reduced_functionality_mode": "no"
    }
]

mock_policies = [
    {
        "id": "policy-001",
        "name": "Corporate Mac Prevention Policy",
        "description": "Standard prevention policy for corporate Macs",
        "platform_name": "Mac",
        "enabled": True,
        "created_by": "admin@example.com",
        "created_timestamp": "2024-01-01T00:00:00Z"
    },
    {
        "id": "policy-002",
        "name": "High Security Mac Policy",
        "description": "High security settings for sensitive systems",
        "platform_name": "Mac",
        "enabled": True,
        "created_by": "admin@example.com",
        "created_timestamp": "2024-01-01T00:00:00Z"
    }
]

mock_detections = [
    {
        "detection_id": "ldt:abc123def456:1234567890",
        "device": {
            "device_id": "crowdstrike-dev-1",
            "hostname": "macbook-pro-123"
        },
        "severity": 4,
        "tactic": "Execution",
        "technique": "Command and Scripting Interpreter",
        "max_confidence": 80,
        "timestamp": (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    }
]


def create_access_token(client_id: str):
    """Create mock OAuth2 access token."""
    token = f"mock-token-{secrets.token_hex(16)}"
    mock_tokens[token] = {
        "client_id": client_id,
        "created_at": datetime.now(UTC),
        "expires_at": datetime.now(UTC).timestamp() + 3600
    }
    return token


def validate_bearer_token(authorization: str = Header(None)):
    """Validate bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.replace("Bearer ", "")
    if token not in mock_tokens:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check expiration
    token_data = mock_tokens[token]
    if datetime.now(UTC).timestamp() >= token_data["expires_at"]:
        del mock_tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    return token_data


@app.post("/oauth2/token")
async def get_token(credentials: HTTPBasicCredentials = Depends(security)):
    """OAuth2 token endpoint."""
    # In real CrowdStrike, client_id and secret are validated
    # For mock, we accept any credentials starting with "mock-"
    
    if not credentials.username.startswith("mock-"):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(credentials.username)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600
    }


@app.get("/sensors/queries/sensors/v1")
async def query_sensors(
    limit: int = 1,
    token_data: dict = Depends(validate_bearer_token)
):
    """Query sensors (health check)."""
    return {
        "resources": ["crowdstrike-dev-1"][:limit]
    }


@app.get("/devices/queries/devices/v1")
async def query_devices(
    limit: int = 5000,
    token_data: dict = Depends(validate_bearer_token)
):
    """Query devices."""
    device_ids = [d["device_id"] for d in mock_devices]
    
    return {
        "resources": device_ids[:limit]
    }


@app.post("/devices/entities/devices/v2")
async def get_device_details(
    payload: Dict[str, Any],
    token_data: dict = Depends(validate_bearer_token)
):
    """Get device details."""
    requested_ids = payload.get("ids", [])
    
    devices = [d for d in mock_devices if d["device_id"] in requested_ids]
    
    return {
        "resources": devices
    }


@app.get("/policy/combined/prevention/v1")
async def get_prevention_policies(token_data: dict = Depends(validate_bearer_token)):
    """Get prevention policies."""
    return {
        "resources": mock_policies
    }


@app.get("/detects/queries/detects/v1")
async def query_detections(
    filter: str = None,
    limit: int = 1000,
    token_data: dict = Depends(validate_bearer_token)
):
    """Query detections."""
    detection_ids = [d["detection_id"] for d in mock_detections]
    
    return {
        "resources": detection_ids[:limit]
    }


@app.post("/detects/entities/summaries/GET/v1")
async def get_detection_summaries(
    payload: Dict[str, Any],
    token_data: dict = Depends(validate_bearer_token)
):
    """Get detection summaries."""
    requested_ids = payload.get("ids", [])
    
    detections = [d for d in mock_detections if d["detection_id"] in requested_ids]
    
    return {
        "resources": detections
    }


@app.post("/devices/entities/devices-actions/v2")
async def device_action(
    action_name: str,
    payload: Dict[str, Any],
    token_data: dict = Depends(validate_bearer_token)
):
    """Perform device action (contain/lift_containment)."""
    device_ids = payload.get("ids", [])
    
    return {
        "resources": [
            {
                "id": device_id,
                "path": f"/devices/entities/devices-actions/v2?action_name={action_name}",
                "action": action_name
            }
            for device_id in device_ids
        ]
    }


if __name__ == "__main__":
    print("Starting Mock CrowdStrike Falcon API server on http://localhost:8005")
    uvicorn.run(app, host="0.0.0.0", port=8005)

