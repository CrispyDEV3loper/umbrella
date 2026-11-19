"""
Realistic OAuth 2.0 / OIDC Authorization & Resource Server.
Contains intentional security flaws for the Red Agent to discover
and the Blue Agent to repair using surgical code patches.
"""

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import hashlib
import base64
import secrets
import urllib.parse

app = FastAPI(title="Target OAuth 2.0 Service", version="1.0.0")

# In-memory storage for clients, codes, and tokens
REGISTERED_CLIENTS: Dict[str, Dict[str, Any]] = {
    "client-app-123": {
        "client_secret": "secret-xyz-456",
        "redirect_uris": ["https://my-saas-app.com/callback", "http://localhost:3000/callback"],
        "allowed_scopes": ["read:profile", "read:email"],
    }
}

# Active authorization codes: code -> dict(client_id, redirect_uri, scope, code_challenge, code_challenge_method, used)
AUTH_CODES: Dict[str, Dict[str, Any]] = {}

# Active access tokens: token -> dict(client_id, scope, user_id)
ACCESS_TOKENS: Dict[str, Dict[str, Any]] = {}


def verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    """Verifies PKCE code_verifier against code_challenge using RFC 7636."""
    if method == "plain":
        return code_verifier == code_challenge
    elif method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return computed == code_challenge
    return False


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "target-oauth-server"}


# ==============================================================================
# AUTHORIZATION ENDPOINT
# ==============================================================================
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
    # 1. Validate Client ID
    client = REGISTERED_CLIENTS.get(client_id)
    if not client:
        return JSONResponse(status_code=400, content={"error": "unauthorized_client", "error_description": "Unknown client_id"})

    # 2. Redirect URI Validation (RFC 6749 Section 3.1.2 & RFC 6819 Section 4.4.1.7)
    # Strictly require exact string matching against pre-registered redirect_uris
    if redirect_uri not in client["redirect_uris"]:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "redirect_uri must exactly match registered URI"})

    # 3. State Parameter Check (RFC 6749 Section 10.12)
    # Enforce state parameter to prevent Login Cross-Site Request Forgery (CSRF)
    if not state or len(state.strip()) < 8:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_request", "error_description": "state parameter with sufficient entropy is required for CSRF protection"}
        )

    # 4. Generate Authorization Code
    code = f"authcode_{secrets.token_hex(16)}"
    AUTH_CODES[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "used": False,  # Flag for code replay
    }

    # Redirect user back with code
    params = {"code": code}
    if state is not None:
        params["state"] = state

    redirect_target = f"{redirect_uri}?{urllib.parse.urlencode(params)}"
    return JSONResponse(status_code=200, content={"redirect_to": redirect_target, "code": code, "state": state})


# ==============================================================================
# TOKEN ENDPOINT
# ==============================================================================
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

    # 1. Lookup Authorization Code
    auth_data = AUTH_CODES.get(req.code)
    if not auth_data:
        return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "Authorization code not found"})

    # RFC 6749 Section 4.1.2: One-Time Use Enforcement
    if auth_data.get("used", False):
        # Invalidate code and reject replay attempt immediately
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_grant", "error_description": "Authorization code has already been redeemed (replay detected)"}
        )
    # Mark code as consumed immediately
    auth_data["used"] = True

    # 2. Validate Client
    if auth_data["client_id"] != req.client_id:
        return JSONResponse(status_code=400, content={"error": "invalid_client"})

    # 3. PKCE Enforcement
    # VULNERABILITY (OAUTH-PKCE-DOWNGRADE):
    # If code_verifier is not provided by the client, the server does not enforce it
    # even when code_challenge was established in the /authorize step!
    # RFC 7636 Section 4.4.1 PKCE Enforcement
    if auth_data.get("code_challenge"):
        if not req.code_verifier:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_grant", "error_description": "code_verifier is required when code_challenge is set"}
            )
        if not verify_pkce(req.code_verifier, auth_data["code_challenge"], auth_data["code_challenge_method"]):
            return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "PKCE verification failed"})

    # 4. Scope Enforcement (RFC 6749 Section 3.3)
    # The granted scope must never exceed the scope authorized by the resource owner
    authorized_scopes = set(auth_data["scope"].split())
    if req.scope:
        requested_scopes = set(req.scope.split())
        # Check if client is requesting scopes beyond what was consented
        if not requested_scopes.issubset(authorized_scopes):
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_scope", "error_description": "Requested scopes exceed originally consented authorization"}
            )
        granted_scope = " ".join(sorted(requested_scopes))
    else:
        granted_scope = auth_data["scope"]

    # Issue Access Token
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


# ==============================================================================
# RESOURCE SERVER: USERINFO ENDPOINT
# ==============================================================================
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
