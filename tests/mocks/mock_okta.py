"""
Mock Okta API Server

Author: Adrian Johnson <adrian207@gmail.com>

Simulates Okta SSO API for testing.
"""

from datetime import datetime, UTC, timedelta
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Header
import uvicorn


app = FastAPI(title="Mock Okta API")

# Mock data
mock_org = {
    "id": "00o1mock123",
    "companyName": "Mock Corp",
    "subdomain": "mock-corp",
    "website": "https://mock-corp.okta.com"
}

mock_devices = [
    {
        "id": "okta-device-1",
        "name": "MacBook-Pro-123",
        "platform": "macOS",
        "status": "ACTIVE",
        "userId": "user-001",
        "managed": True,
        "registered": True,
        "created": "2024-01-15T10:00:00Z",
        "lastUpdated": datetime.now(UTC).isoformat()
    },
    {
        "id": "okta-device-2",
        "name": "MacBook-Air-456",
        "platform": "macOS",
        "status": "ACTIVE",
        "userId": "user-002",
        "managed": False,
        "registered": True,
        "created": "2024-02-20T14:00:00Z",
        "lastUpdated": datetime.now(UTC).isoformat()
    }
]

mock_users = [
    {
        "id": "user-001",
        "status": "ACTIVE",
        "created": "2024-01-10T00:00:00Z",
        "lastLogin": datetime.now(UTC).isoformat(),
        "profile": {
            "email": "john.doe@example.com",
            "login": "john.doe@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "department": "Engineering",
            "title": "Senior Engineer"
        }
    },
    {
        "id": "user-002",
        "status": "ACTIVE",
        "created": "2024-02-15T00:00:00Z",
        "lastLogin": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        "profile": {
            "email": "jane.smith@example.com",
            "login": "jane.smith@example.com",
            "firstName": "Jane",
            "lastName": "Smith",
            "department": "Sales",
            "title": "Account Executive"
        }
    }
]

mock_policies = [
    {
        "id": "pol-001",
        "type": "OKTA_SIGN_ON",
        "name": "Corporate Sign-On Policy",
        "description": "Default sign-on policy for corporate users",
        "status": "ACTIVE",
        "priority": 1,
        "created": "2024-01-01T00:00:00Z"
    },
    {
        "id": "pol-002",
        "type": "OKTA_SIGN_ON",
        "name": "MFA Required Policy",
        "description": "Requires MFA for all users",
        "status": "ACTIVE",
        "priority": 2,
        "created": "2024-01-01T00:00:00Z"
    }
]

mock_groups = [
    {
        "id": "group-001",
        "name": "Everyone",
        "description": "All users"
    },
    {
        "id": "group-002",
        "name": "Engineering",
        "description": "Engineering team"
    }
]


def validate_ssws_token(authorization: str):
    """Validate SSWS token."""
    if not authorization or not authorization.startswith("SSWS "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.replace("SSWS ", "")
    if not token.startswith("mock-okta-"):
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/api/v1/org")
async def get_org(authorization: str = Header(None)):
    """Get organization details."""
    validate_ssws_token(authorization)
    
    return mock_org


@app.get("/api/v1/devices")
async def get_devices(
    limit: int = 200,
    authorization: str = Header(None)
):
    """Get devices."""
    validate_ssws_token(authorization)
    
    return mock_devices[:limit]


@app.get("/api/v1/users")
async def get_users(
    limit: int = 200,
    authorization: str = Header(None)
):
    """Get users with pagination support."""
    validate_ssws_token(authorization)
    
    users = mock_users[:limit]
    
    # Mock pagination with Link header (simplified)
    # In real Okta, this would be in response headers
    return users


@app.get("/api/v1/users/{user_id}/groups")
async def get_user_groups(
    user_id: str,
    authorization: str = Header(None)
):
    """Get groups for a user."""
    validate_ssws_token(authorization)
    
    # Return mock groups for any user
    return mock_groups


@app.get("/api/v1/users/{user_id}/sessions")
async def get_user_sessions(
    user_id: str,
    authorization: str = Header(None)
):
    """Get active sessions for a user."""
    validate_ssws_token(authorization)
    
    return [
        {
            "id": "session-001",
            "userId": user_id,
            "status": "ACTIVE",
            "createdAt": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
            "lastPasswordVerification": datetime.now(UTC).isoformat()
        }
    ]


@app.get("/api/v1/policies")
async def get_policies(
    type: str = "OKTA_SIGN_ON",
    authorization: str = Header(None)
):
    """Get policies."""
    validate_ssws_token(authorization)
    
    return [p for p in mock_policies if p["type"] == type]


@app.put("/api/v1/devices/{device_id}/trust")
async def update_device_trust(
    device_id: str,
    payload: Dict[str, Any],
    authorization: str = Header(None)
):
    """Update device trust level."""
    validate_ssws_token(authorization)
    
    return {
        "message": "Trust level updated",
        "deviceId": device_id,
        "trustLevel": payload.get("trustLevel")
    }


if __name__ == "__main__":
    print("Starting Mock Okta API server on http://localhost:8004")
    uvicorn.run(app, host="0.0.0.0", port=8004)

