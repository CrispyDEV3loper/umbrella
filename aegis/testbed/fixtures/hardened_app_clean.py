"""
Pristine, Fully-Hardened Reference Target Fixture.
Contains all five RFC-compliant security controls in their verified, secure state.
Used to measure false positive rates and test baseline security compliance.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import hashlib
import base64
import secrets
import urllib.parse

app = FastAPI(title="Pristine Hardened Target Service", version="1.0.0")

REGISTERED_CLIENTS: Dict[str, Dict[str, Any]] = {
    "client-app-123": {
        "client_secret": "secret-xyz-456",
        "redirect_uris": ["https://my-saas-app.com/callback", "http://localhost:3000/callback"],
        "allowed_scopes": ["read:profile", "read:email"],
    }
}

AUTH_CODES: Dict[str, Dict[str, Any]] = {}
ACCESS_TOKENS: Dict[str, Dict[str, Any]] = {}


def verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    if method == "plain":
        return code_verifier == code_challenge
    elif method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return computed == code_challenge
    return False


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "pristine-hardened-oauth-server"}


@app.get("/authorize")
def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str = "read:profile",
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256",
):
    client = REGISTERED_CLIENTS.get(client_id)
    if not client:
        return JSONResponse(status_code=400, content={"error": "unauthorized_client", "error_description": "Unknown client_id"})

    # 1. Exact Redirect URI Matching (RFC 6749 Section 3.1.2)
    if redirect_uri not in client["redirect_uris"]:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "redirect_uri must exactly match registered URI"})

    # 2. State Parameter Check (RFC 6749 Section 10.12)
    if not state or len(state.strip()) < 8:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "state parameter with sufficient entropy is required"})

    code = f"authcode_{secrets.token_hex(16)}"
    AUTH_CODES[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "used": False,
    }

    params = {"code": code, "state": state}
    redirect_target = f"{redirect_uri}?{urllib.parse.urlencode(params)}"
    return JSONResponse(status_code=200, content={"redirect_to": redirect_target, "code": code, "state": state})


class TokenRequest(BaseModel):
    grant_type: str
    code: str
    redirect_uri: str
    client_id: str
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    scope: Optional[str] = None


@app.post("/token")
def token(req: TokenRequest):
    if req.grant_type != "authorization_code":
        return JSONResponse(status_code=400, content={"error": "unsupported_grant_type"})

    auth_data = AUTH_CODES.get(req.code)
    if not auth_data:
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "Authorization code not found"})

    # Single-use enforcement (RFC 6749 Section 4.1.2)
    if auth_data.get("used", False):
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "Authorization code has already been redeemed"})
    auth_data["used"] = True

    if auth_data["client_id"] != req.client_id:
        return JSONResponse(status_code=400, content={"error": "invalid_client"})

    # PKCE Enforcement (RFC 7636 Section 4.4.1)
    if auth_data.get("code_challenge"):
        if not req.code_verifier:
            return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "code_verifier is required"})
        if not verify_pkce(req.code_verifier, auth_data["code_challenge"], auth_data["code_challenge_method"]):
            return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "PKCE verification failed"})

    # Scope Authorization (RFC 6749 Section 3.3)
    authorized_scopes = set(auth_data["scope"].split())
    if req.scope:
        requested_scopes = set(req.scope.split())
        if not requested_scopes.issubset(authorized_scopes):
            return JSONResponse(status_code=400, content={"error": "invalid_scope", "error_description": "Requested scopes exceed originally consented authorization"})
        granted_scope = " ".join(sorted(requested_scopes))
    else:
        granted_scope = auth_data["scope"]

    access_token = f"at_{secrets.token_urlsafe(32)}"
    ACCESS_TOKENS[access_token] = {
        "client_id": req.client_id,
        "scope": granted_scope,
        "user_id": "usr_998877",
    }

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": granted_scope,
    }


@app.get("/userinfo")
def userinfo(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    token_str = auth_header.split(" ")[1]
    token_data = ACCESS_TOKENS.get(token_str)
    if not token_data:
        return JSONResponse(status_code=401, content={"error": "invalid_token"})

    return {
        "sub": token_data["user_id"],
        "name": "Jane Developer",
        "email": "jane@example.com",
        "scope": token_data["scope"],
    }
