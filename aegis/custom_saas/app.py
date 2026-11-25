"""
Acme SaaS — bundled custom SaaS test environment.

A realistic third-party SaaS OAuth 2.0 authorization server intended to be
tested through the exact same Red/Blue/Dual-Gate flow as the bundled testbed.
It ships in its vulnerable baseline state and is ALWAYS executed through an
isolated sandbox copy (see aegis.runner), never patched in place.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import hashlib
import base64
import secrets
import urllib.parse

app = FastAPI(title="Acme SaaS OAuth Authorization Server", version="1.0.0")

REGISTERED_CLIENTS: Dict[str, Dict[str, Any]] = {
    "acme-saas-7f3a": {
        "client_secret": "acme-secret-b71c",
        "redirect_uris": ["https://acme-saas.example.com/oauth/redirect", "http://localhost:5000/oauth/return"],
        "allowed_scopes": ["read:workspace", "read:billing"],
    }
}

AUTH_CODES: Dict[str, Dict[str, Any]] = {}
ACCESS_TOKENS: Dict[str, Dict[str, Any]] = {}


def verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    """Verifies PKCE code_verifier against code_challenge per RFC 7636."""
    if method == "plain":
        return code_verifier == code_challenge
    elif method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return computed == code_challenge
    return False


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "acme-saas-oauth-server"}


@app.get("/authorize")
def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str = "read:workspace",
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256",
):
    # 1. Validate Client ID
    client = REGISTERED_CLIENTS.get(client_id)
    if not client:
        return JSONResponse(status_code=400, content={"error": "unauthorized_client", "error_description": "Unknown client_id"})

    # 2. Redirect URI Validation (VULNERABILITY: weak startswith allows path traversal / open redirects)
    valid_redirect = any(redirect_uri.startswith(reg_uri) for reg_uri in client["redirect_uris"])
    if not valid_redirect:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "Invalid redirect_uri"})

    # 3. State Parameter Check (VULNERABILITY: state omitted/not enforced, allowing login CSRF)
    # [UNENFORCED IN VULNERABLE BASELINE]

    # 4. Generate Authorization Code
    code = f"acm_{secrets.token_hex(16)}"
    AUTH_CODES[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "used": False,
    }

    params = {"code": code}
    if state is not None:
        params["state"] = state

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

    # VULNERABILITY: Code is not marked as used, allowing multi-redemption / replay
    # [UNENFORCED IN VULNERABLE BASELINE]

    if auth_data["client_id"] != req.client_id:
        return JSONResponse(status_code=400, content={"error": "invalid_client"})

    # VULNERABILITY: If code_verifier is omitted, continues without enforcing it
    if auth_data.get("code_challenge"):
        if req.code_verifier is None:
            pass  # Flaw: Silently continues without verifier!
        else:
            if not verify_pkce(req.code_verifier, auth_data["code_challenge"], auth_data["code_challenge_method"]):
                return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "PKCE verification failed"})

    # VULNERABILITY: Blindly grants unconsented scopes
    granted_scope = req.scope if req.scope else auth_data["scope"]

    access_token = f"at_{secrets.token_urlsafe(32)}"
    ACCESS_TOKENS[access_token] = {
        "client_id": req.client_id,
        "scope": granted_scope,
        "user_id": "acme_usr_4471",
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
        "name": "Acme Workspace User",
        "email": "user@acme-saas.example.com",
        "scope": token_data["scope"],
    }
