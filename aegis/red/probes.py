"""
Aegis Red Team Protocol Probes.
Active testing engine for OAuth 2.0 and OpenID Connect security specifications
(RFC 8414, RFC 7636, RFC 6749, RFC 6819).
Integrates multi-variant parameter mutations to detect logic flaws and shallow patches.
"""

from typing import Dict, Any, Optional, Tuple, List
import httpx
import hashlib
import base64
import secrets
from aegis.core.state import VulnerabilityProof
from aegis.red.mutator import OAuthPayloadMutator


def generate_pkce_pair() -> Tuple[str, str]:
    """Generates an RFC 7636 compliant PKCE code_verifier and code_challenge."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


class OAuthAttackProbes:
    """Suite of adaptive OAuth 2.0 / OIDC attack probes with property-based mutation fuzzing."""

    @staticmethod
    def test_pkce_downgrade(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Executes PKCE Downgrade and Omission mutation suite.
        Tests missing verifier, empty verifiers, and method tampering.
        RFC 7636 mandates strict rejection of all invalid/missing verifiers.
        """
        verifier, challenge = generate_pkce_pair()
        mutations = OAuthPayloadMutator.mutate_pkce_downgrades(verifier)
        succeeded_mutations = []

        for mut in mutations:
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
                continue

            code = auth_resp.json().get("code")
            if not code:
                continue

            token_payload = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "https://my-saas-app.com/callback",
                "client_id": "client-app-123",
            }
            if mut["verifier"] is not None:
                token_payload["code_verifier"] = mut["verifier"]

            token_resp = client.post(f"{base_url}/token", json=token_payload)

            if token_resp.status_code == 200 and "access_token" in token_resp.json():
                succeeded_mutations.append({
                    "mutation_type": mut["type"],
                    "description": mut["description"],
                    "status": token_resp.status_code,
                    "body": token_resp.json(),
                })

        if succeeded_mutations:
            first_exploit = succeeded_mutations[0]
            return VulnerabilityProof(
                vector_id="OAUTH-PKCE-DOWNGRADE",
                category="PKCE",
                description="Token endpoint issued access token with missing or invalid PKCE verifier, violating RFC 7636.",
                exploit_payload=first_exploit,
                target_endpoint="/token",
                response_status=first_exploit["status"],
                response_body=first_exploit["body"],
                poc_summary=f"PKCE bypass succeeded on {len(succeeded_mutations)}/{len(mutations)} mutation variants. Primary: {first_exploit['description']}",
                mutations_tested=len(mutations),
                mutations_succeeded=len(succeeded_mutations),
            )
        return None

    @staticmethod
    def test_redirect_traversal(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Executes Redirect URI mutation suite: plain traversal, URL-encoded,
        double-encoded, subdomain spoofing, and parameter injection.
        RFC 6749 Section 3.1.2 mandates exact string comparison against registered URIs.
        """
        mutations = OAuthPayloadMutator.mutate_redirect_uri("https://my-saas-app.com/callback")
        succeeded_mutations = []

        for mut in mutations:
            auth_resp = client.get(
                f"{base_url}/authorize",
                params={
                    "response_type": "code",
                    "client_id": "client-app-123",
                    "redirect_uri": mut["uri"],
                    "scope": "read:profile",
                    "state": "state_123",
                },
            )

            if auth_resp.status_code == 200 and "code" in auth_resp.json():
                succeeded_mutations.append({
                    "mutation_type": mut["type"],
                    "description": mut["description"],
                    "uri": mut["uri"],
                    "status": auth_resp.status_code,
                    "body": auth_resp.json(),
                })

        if succeeded_mutations:
            first_exploit = succeeded_mutations[0]
            return VulnerabilityProof(
                vector_id="OAUTH-REDIRECT-TRAVERSAL",
                category="REDIRECT_URI",
                description="Authorization endpoint accepted path-traversal or manipulated redirect_uri bypassing whitelist.",
                exploit_payload=first_exploit,
                target_endpoint="/authorize",
                response_status=first_exploit["status"],
                response_body=first_exploit["body"],
                poc_summary=f"Redirect URI bypass succeeded on {len(succeeded_mutations)}/{len(mutations)} variants. Trigger: {first_exploit['description']} ({first_exploit['uri']})",
                mutations_tested=len(mutations),
                mutations_succeeded=len(succeeded_mutations),
            )
        return None

    @staticmethod
    def test_state_csrf(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Executes State CSRF mutation suite: omitted state, low-entropy static state,
        and whitespace injection. RFC 6749 Section 10.12 mandates strong CSRF binding.
        """
        mutations = OAuthPayloadMutator.mutate_state_parameters()
        succeeded_mutations = []

        for mut in mutations:
            params = {
                "response_type": "code",
                "client_id": "client-app-123",
                "redirect_uri": "https://my-saas-app.com/callback",
                "scope": "read:profile",
            }
            if mut["state"] is not None:
                params["state"] = mut["state"]

            auth_resp = client.get(f"{base_url}/authorize", params=params)

            if auth_resp.status_code == 200 and "code" in auth_resp.json():
                succeeded_mutations.append({
                    "mutation_type": mut["type"],
                    "description": mut["description"],
                    "status": auth_resp.status_code,
                    "body": auth_resp.json(),
                })

        if succeeded_mutations:
            first_exploit = succeeded_mutations[0]
            return VulnerabilityProof(
                vector_id="OAUTH-STATE-CSRF",
                category="CSRF",
                description="Authorization endpoint granted code without validating state parameter presence or entropy.",
                exploit_payload=first_exploit,
                target_endpoint="/authorize",
                response_status=first_exploit["status"],
                response_body=first_exploit["body"],
                poc_summary=f"State CSRF flaw succeeded on {len(succeeded_mutations)}/{len(mutations)} variants. Trigger: {first_exploit['description']}",
                mutations_tested=len(mutations),
                mutations_succeeded=len(succeeded_mutations),
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
                "state": "state_abc_123456",
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
                mutations_tested=1,
                mutations_succeeded=1,
            )
        return None

    @staticmethod
    def test_scope_escalation(client: httpx.Client, base_url: str) -> Optional[VulnerabilityProof]:
        """
        Executes Scope Escalation mutation suite: admin injection, write:all injection,
        wildcard escalation (*), and root override. RFC 6749 Section 3.3.
        """
        verifier, challenge = generate_pkce_pair()
        mutations = OAuthPayloadMutator.mutate_scope_escalations("read:profile")
        succeeded_mutations = []

        for mut in mutations:
            auth_resp = client.get(
                f"{base_url}/authorize",
                params={
                    "response_type": "code",
                    "client_id": "client-app-123",
                    "redirect_uri": "https://my-saas-app.com/callback",
                    "scope": "read:profile",  # User only consented to read:profile
                    "state": "state_scope_12345",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                },
            )
            if auth_resp.status_code != 200:
                continue

            code = auth_resp.json().get("code")
            token_resp = client.post(
                f"{base_url}/token",
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": "https://my-saas-app.com/callback",
                    "client_id": "client-app-123",
                    "code_verifier": verifier,
                    "scope": mut["scope"],  # Injected scope payload
                },
            )

            if token_resp.status_code == 200:
                body = token_resp.json()
                granted_scope = body.get("scope", "")
                # Check if elevated scope was granted
                if any(elevated in granted_scope for elevated in ["admin", "write:all", "*", "root"]):
                    succeeded_mutations.append({
                        "mutation_type": mut["type"],
                        "description": mut["description"],
                        "requested_scope": mut["scope"],
                        "granted_scope": granted_scope,
                        "status": token_resp.status_code,
                        "body": body,
                    })

        if succeeded_mutations:
            first_exploit = succeeded_mutations[0]
            return VulnerabilityProof(
                vector_id="OAUTH-SCOPE-ESCALATION",
                category="PRIVILEGE_ESCALATION",
                description="Token endpoint granted elevated unconsented scopes exceeding user consent.",
                exploit_payload=first_exploit,
                target_endpoint="/token",
                response_status=first_exploit["status"],
                response_body=first_exploit["body"],
                poc_summary=f"Scope escalation succeeded on {len(succeeded_mutations)}/{len(mutations)} variants. Granted: {first_exploit['granted_scope']}",
                mutations_tested=len(mutations),
                mutations_succeeded=len(succeeded_mutations),
            )
        return None
