"""
Mock Seraphic API Server

Author: Adrian Johnson <adrian207@gmail.com>

Simulates Seraphic browser security API for testing.
"""

from datetime import datetime, UTC, timedelta
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Header
import uvicorn


app = FastAPI(title="Mock Seraphic API")

# Mock data
mock_endpoints = [
    {
        "endpointId": "seraphic-ep-1",
        "hostname": "macbook-pro-123.local",
        "userEmail": "john.doe@example.com",
        "platform": "macOS",
        "osVersion": "14.1.1",
        "agentVersion": "3.2.1",
        "agentStatus": "active",
        "lastSeen": datetime.now(UTC).isoformat(),
        "protectionEnabled": True,
        "isolationEnabled": True,
        "dlpEnabled": True,
        "policyId": "pol-001",
        "policyName": "Corporate Browser Security"
    },
    {
        "endpointId": "seraphic-ep-2",
        "hostname": "macbook-air-456.local",
        "userEmail": "jane.smith@example.com",
        "platform": "macOS",
        "osVersion": "14.0",
        "agentVersion": "3.2.0",
        "agentStatus": "active",
        "lastSeen": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
        "protectionEnabled": True,
        "isolationEnabled": False,
        "dlpEnabled": True,
        "policyId": "pol-002",
        "policyName": "Standard User Policy"
    }
]

mock_users = [
    {
        "userId": "user-001",
        "email": "john.doe@example.com",
        "name": "John Doe",
        "department": "Engineering",
        "endpointCount": 1
    },
    {
        "userId": "user-002",
        "email": "jane.smith@example.com",
        "name": "Jane Smith",
        "department": "Sales",
        "endpointCount": 1
    }
]

mock_policies = [
    {
        "policyId": "pol-001",
        "name": "Corporate Browser Security",
        "description": "High security for corporate users",
        "enabled": True,
        "endpointCount": 1,
        "settings": {
            "isolation": "high",
            "dlp": "enabled",
            "threatProtection": "enabled"
        }
    },
    {
        "policyId": "pol-002",
        "name": "Standard User Policy",
        "description": "Basic security for standard users",
        "enabled": True,
        "endpointCount": 1,
        "settings": {
            "isolation": "medium",
            "dlp": "enabled",
            "threatProtection": "enabled"
        }
    }
]

mock_threats = [
    {
        "threatId": "threat-001",
        "endpointId": "seraphic-ep-1",
        "userEmail": "john.doe@example.com",
        "threatType": "phishing",
        "threatName": "Phishing Website",
        "severity": "high",
        "url": "https://evil-phishing-site.com",
        "actionTaken": "blocked",
        "timestamp": (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    }
]


def validate_api_key(api_key: str):
    """Validate API key."""
    if not api_key or not api_key.startswith("mock-seraphic-"):
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/api/v1/health")
async def health(x_seraphic_api_key: str = Header(None)):
    """Health check endpoint."""
    validate_api_key(x_seraphic_api_key)
    
    return {
        "status": "ok",
        "version": "v1",
        "tenantId": "tenant-mock-123"
    }


@app.get("/api/v1/endpoints")
async def get_endpoints(
    page: int = 1,
    limit: int = 100,
    x_seraphic_api_key: str = Header(None)
):
    """Get endpoints."""
    validate_api_key(x_seraphic_api_key)
    
    start = (page - 1) * limit
    end = start + limit
    page_endpoints = mock_endpoints[start:end]
    
    return {
        "endpoints": page_endpoints,
        "hasMore": end < len(mock_endpoints)
    }


@app.get("/api/v1/users")
async def get_users(
    limit: int = 1000,
    x_seraphic_api_key: str = Header(None)
):
    """Get users."""
    validate_api_key(x_seraphic_api_key)
    
    return {
        "users": mock_users[:limit]
    }


@app.get("/api/v1/policies")
async def get_policies(x_seraphic_api_key: str = Header(None)):
    """Get policies."""
    validate_api_key(x_seraphic_api_key)
    
    return {
        "policies": mock_policies
    }


@app.get("/api/v1/threats")
async def get_threats(
    endpointId: str = None,
    hours: int = 24,
    x_seraphic_api_key: str = Header(None)
):
    """Get threat detections."""
    validate_api_key(x_seraphic_api_key)
    
    threats = mock_threats
    if endpointId:
        threats = [t for t in threats if t["endpointId"] == endpointId]
    
    return {
        "threats": threats
    }


@app.post("/api/v1/endpoints/{endpoint_id}/compliance")
async def update_compliance(
    endpoint_id: str,
    payload: Dict[str, Any],
    x_seraphic_api_key: str = Header(None)
):
    """Update endpoint compliance status."""
    validate_api_key(x_seraphic_api_key)
    
    return {
        "message": "Compliance updated",
        "endpointId": endpoint_id
    }


@app.post("/api/v1/endpoints/{endpoint_id}/risk")
async def update_risk(
    endpoint_id: str,
    payload: Dict[str, Any],
    x_seraphic_api_key: str = Header(None)
):
    """Update endpoint risk score."""
    validate_api_key(x_seraphic_api_key)
    
    return {
        "message": "Risk score updated",
        "endpointId": endpoint_id
    }


@app.post("/api/v1/endpoints/{endpoint_id}/policy")
async def update_policy(
    endpoint_id: str,
    payload: Dict[str, Any],
    x_seraphic_api_key: str = Header(None)
):
    """Update endpoint policy."""
    validate_api_key(x_seraphic_api_key)
    
    return {
        "message": "Policy updated",
        "endpointId": endpoint_id,
        "action": payload.get("action")
    }


if __name__ == "__main__":
    print("Starting Mock Seraphic API server on http://localhost:8003")
    uvicorn.run(app, host="0.0.0.0", port=8003)

