"""
Aegis Golden Path Functional Contract Suite.
Executes standard, RFC-compliant OAuth 2.0 / OIDC user journeys.
Used by the Dual-Gate Evaluator to ensure that security patches
do not break legitimate client functionality or integration flows.
"""

from typing import Tuple, Dict, Any
import httpx
import secrets
import hashlib
import base64


def generate_pkce() -> Tuple[str, str]:
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


class GoldenPathSuite:
    """Verifies that legitimate OAuth flows continue to function without regression."""

    @staticmethod
    def run_all(client: httpx.Client, base_url: str) -> Tuple[bool, str]:
        """
        Runs the full functional regression suite.
        Returns: (all_passed: bool, message: str)
        """
        # Test 1: Standard Authorization Code Flow with PKCE & State
        flow_ok, msg = GoldenPathSuite.verify_standard_pkce_flow(client, base_url)
        if not flow_ok:
            return False, f"Regression in Standard PKCE Flow: {msg}"

        # Test 2: UserInfo Resource Access with Valid Token
        userinfo_ok, msg = GoldenPathSuite.verify_userinfo_access(client, base_url)
        if not userinfo_ok:
            return False, f"Regression in UserInfo Endpoint: {msg}"

        return True, "All Golden Path functional flows passed successfully (100% functional integrity)."

    @staticmethod
    def verify_standard_pkce_flow(client: httpx.Client, base_url: str) -> Tuple[bool, str]:
        """Legitimate end-to-end OAuth 2.0 code exchange with PKCE."""
        verifier, challenge = generate_pkce()
        state = f"valid_client_state_{secrets.token_hex(8)}"
        redirect_uri = "https://my-saas-app.com/callback"

        # 1. Authorize
        auth_resp = client.get(
            f"{base_url}/authorize",
            params={
                "response_type": "code",
                "client_id": "client-app-123",
                "redirect_uri": redirect_uri,
                "scope": "read:profile",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        if auth_resp.status_code != 200:
            return False, f"Authorization failed with status {auth_resp.status_code}: {auth_resp.text}"

        auth_data = auth_resp.json()
        code = auth_data.get("code")
        returned_state = auth_data.get("state")

        if not code:
            return False, "No authorization code returned"
        if returned_state != state:
            return False, "Returned state does not match original state"

        # 2. Token Exchange
        token_resp = client.post(
            f"{base_url}/token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": "client-app-123",
                "code_verifier": verifier,
            },
        )
        if token_resp.status_code != 200:
            return False, f"Token exchange failed with status {token_resp.status_code}: {token_resp.text}"

        token_data = token_resp.json()
        if "access_token" not in token_data:
            return False, "Response missing access_token"

        return True, "Standard PKCE flow succeeded"

    @staticmethod
    def verify_userinfo_access(client: httpx.Client, base_url: str) -> Tuple[bool, str]:
        """Verify that issued access token accesses protected user profile."""
        verifier, challenge = generate_pkce()
        auth_resp = client.get(
            f"{base_url}/authorize",
            params={
                "response_type": "code",
                "client_id": "client-app-123",
                "redirect_uri": "https://my-saas-app.com/callback",
                "scope": "read:profile",
                "state": "state_valid_userinfo_99",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        code = auth_resp.json().get("code")

        token_resp = client.post(
            f"{base_url}/token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "https://my-saas-app.com/callback",
                "client_id": "client-app-123",
                "code_verifier": verifier,
            },
        )
        token_str = token_resp.json().get("access_token")

        userinfo_resp = client.get(
            f"{base_url}/userinfo",
            headers={"Authorization": f"Bearer {token_str}"},
        )
        if userinfo_resp.status_code != 200:
            return False, f"Protected /userinfo returned {userinfo_resp.status_code}"

        user_data = userinfo_resp.json()
        if user_data.get("email") != "jane@example.com":
            return False, "UserInfo response corrupted or invalid"

        return True, "UserInfo verified"
