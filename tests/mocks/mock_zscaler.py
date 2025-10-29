"""
Mock Zscaler API Server

Author: Adrian Johnson <adrian207@gmail.com>

Simulates Zscaler ZIA/ZPA API for testing without live credentials.
"""

from datetime import datetime, UTC
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Cookie, Response
import uvicorn
import hashlib
import time


app = FastAPI(title="Mock Zscaler API")

# Mock session storage
mock_sessions = {}

# Mock data
mock_devices = [
    {
        "id": "zscaler-device-1",
        "name": "MacBook-Pro-Corporate",
        "owner": "john.doe@example.com",
        "deviceType": "MacBook",
        "osType": "macOS",
        "osVersion": "14.1.1",
        "deviceModel": "MacBookPro18,3",
        "hostname": "macbook-pro-123.local",
        "description": "Corporate MacBook Pro"
    },
    {
        "id": "zscaler-device-2",
        "name": "MacBook-Air-Remote",
        "owner": "jane.smith@example.com",
        "deviceType": "MacBook",
        "osType": "macOS",
        "osVersion": "14.0",
        "deviceModel": "MacBookAir10,1",
        "hostname": "macbook-air-456.local",
        "description": "Remote worker MacBook Air"
    }
]

mock_users = [
    {
        "id": 1001,
        "email": "john.doe@example.com",
        "name": "John Doe",
        "department": "Engineering",
        "groups": ["All Users", "Engineering", "Developers"]
    },
    {
        "id": 1002,
        "email": "jane.smith@example.com",
        "name": "Jane Smith",
        "department": "Sales",
        "groups": ["All Users", "Sales"]
    }
]

mock_policies = [
    {
        "id": 1,
        "name": "Corporate URL Filtering",
        "description": "Default URL filtering for corporate users",
        "action": "ALLOW",
        "state": "ENABLED",
        "order": 1,
        "enabled": True
    },
    {
        "id": 2,
        "name": "Block Social Media",
        "description": "Block social media sites",
        "action": "BLOCK",
        "state": "ENABLED",
        "order": 2,
        "enabled": True
    }
]


def create_session_token():
    """Create mock session token."""
    token = hashlib.md5(f"{time.time()}".encode()).hexdigest()
    mock_sessions[token] = {
        "created_at": datetime.now(UTC),
        "expires_at": datetime.now(UTC).timestamp() + 1800  # 30 minutes
    }
    return token


@app.post("/api/v1/authenticatedSession")
async def authenticate(payload: Dict[str, Any], response: Response):
    """Authenticate and create session."""
    # In real Zscaler, apiKey is obfuscated with timestamp
    # For mock, we just accept any credentials
    
    session_token = create_session_token()
    
    # Set session cookie
    response.set_cookie(
        key="JSESSIONID",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return {
        "message": "Authenticated successfully"
    }


@app.delete("/api/v1/authenticatedSession")
async def logout(jsessionid: str = Cookie(None)):
    """Logout and destroy session."""
    if jsessionid and jsessionid in mock_sessions:
        del mock_sessions[jsessionid]
    
    return {"message": "Logged out successfully"}


@app.get("/api/v1/status")
async def status(jsessionid: str = Cookie(None)):
    """Check API status."""
    if not jsessionid or jsessionid not in mock_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "status": "ok",
        "version": "v1"
    }


@app.get("/api/v1/devices")
async def get_devices(jsessionid: str = Cookie(None)):
    """Get enrolled devices."""
    if not jsessionid or jsessionid not in mock_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return mock_devices


@app.get("/api/v1/users")
async def get_users(
    pageSize: int = 1000,
    jsessionid: str = Cookie(None)
):
    """Get users."""
    if not jsessionid or jsessionid not in mock_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return mock_users[:pageSize]


@app.get("/api/v1/urlFilteringRules")
async def get_url_filtering_rules(jsessionid: str = Cookie(None)):
    """Get URL filtering policies."""
    if not jsessionid or jsessionid not in mock_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return mock_policies


@app.get("/api/v1/users/{user_email}/riskScore")
async def get_user_risk_score(
    user_email: str,
    jsessionid: str = Cookie(None)
):
    """Get user risk score."""
    if not jsessionid or jsessionid not in mock_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find user
    user = next((u for u in mock_users if u["email"] == user_email), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": user_email,
        "riskScore": 25,
        "riskLevel": "LOW",
        "factors": []
    }


@app.put("/api/v1/devices/{device_id}/trustLevel")
async def update_device_trust(
    device_id: str,
    payload: Dict[str, Any],
    jsessionid: str = Cookie(None)
):
    """Update device trust level."""
    if not jsessionid or jsessionid not in mock_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {"message": "Trust level updated", "deviceId": device_id}


@app.put("/api/v1/devices/{device_id}/posture")
async def update_device_posture(
    device_id: str,
    payload: Dict[str, Any],
    jsessionid: str = Cookie(None)
):
    """Update device posture."""
    if not jsessionid or jsessionid not in mock_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {"message": "Posture updated", "deviceId": device_id}


if __name__ == "__main__":
    print("Starting Mock Zscaler API server on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)

