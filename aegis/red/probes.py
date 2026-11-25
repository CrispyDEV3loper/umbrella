"""
Aegis Red Team Protocol Probes.
Active testing engine for OAuth 2.0 and OpenID Connect security specifications
(RFC 8414, RFC 7636, RFC 6749, RFC 6819).
Integrates multi-variant parameter mutations to detect logic flaws and shallow patches.

Probes operate against a ProbeContext (client identifiers, redirect URIs, scope, state),
so they can target either the bundled testbed or a bring-your-own-app custom target.
"""

from typing import Dict, Any, Optional, Tuple, List
import httpx
import hashlib
import base64
import secrets

from aegis.core.state import VulnerabilityProof
from aegis.red.mutator import OAuthPayloadMutator
from aegis.core.target import (
    TargetProfile,
    LEGACY_CLIENT_ID, LEGACY_REDIRECT_URI, LEGACY_SCOPE, LEGACY_STATE,
)


def generate_pkce_pair() -> Tuple[str, str]:
    """Generates an RFC 7636 compliant PKCE code_verifier and code_challenge."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


class ProbeContext:
    """Holds the identifiers a probe suite uses against a specific target.

    Built from a TargetProfile for custom apps, or the legacy bundled-testbed
    constants when profile is None (preserves original behavior exactly).
    """

    def __init__(self, base_url: str, profile: Optional[TargetProfile] = None):
        self.base_url = base_url
        self.client_id = profile.client_id if profile else LEGACY_CLIENT_ID
        self.redirect_uri = profile.redirect_uri if profile else LEGACY_REDIRECT_URI
        self.scope = profile.scope if profile else LEGACY_SCOPE
        self.state = profile.state if profile else LEGACY_STATE

    @staticmethod
    def for_legacy(base_url: str, client_id: str, redirect_uri: str,
                   scope: str, state: str) -> "ProbeContext":
        return ProbeContext(base_url, None)

    # convenience for legacy callers that pass raw strings
    @staticmethod
    def from_strings(base_url, client_id, redirect_uri, scope, state) -> "ProbeContext":
        p = ProbeContext(base_url, None)
        p.client_id, p.redirect_uri, p.scope, p.state = client_id, redirect_uri, scope, state
        return p


class OAuthAttackProbes:
    """Suite of adaptive OAuth 2.0 / OIDC attack probes with property-based mutation fuzzing."""

    # ---- instance probes (profile-aware) --------------------------------------

    def authorize_params(self, ctx: ProbeContext, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = {
            "response_type": "code",
            "client_id": ctx.client_id,
            "redirect_uri": ctx.redirect_uri,
            "scope": ctx.scope,
            "state": ctx.state,
        }
        if extra:
            params.update(extra)
        return params

    def test_pkce_downgrade(self, client: httpx.Client, ctx: ProbeContext) -> Optional[VulnerabilityProof]:
        """PKCE Downgrade & Omission mutation suite. RFC 7636 mandates strict verifier enforcement."""
        verifier, challenge = generate_pkce_pair()
        mutations = OAuthPayloadMutator.mutate_pkce_downgrades(verifier)
        succeeded = []

        for mut in mutations:
            req_challenge = mut.get("challenge", challenge)
            req_method = mut.get("method", "S256")
            auth_resp = client.get(
                f"{ctx.base_url}/authorize",
                params={**self.authorize_params(ctx), "code_challenge": req_challenge, "code_challenge_method": req_method},
            )
            if auth_resp.status_code != 200:
                continue
            code = auth_resp.json().get("code")
            if not code:
                continue
            token_payload = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": ctx.redirect_uri,
                "client_id": ctx.client_id,
            }
            if mut["verifier"] is not None:
                token_payload["code_verifier"] = mut["verifier"]
            token_resp = client.post(f"{ctx.base_url}/token", json=token_payload)
            if token_resp.status_code == 200 and "access_token" in token_resp.json():
                succeeded.append({
                    "mutation_type": mut["type"],
                    "description": mut["description"],
                    "status": token_resp.status_code,
                    "body": token_resp.json(),
                })
        if succeeded:
            first = succeeded[0]
            return VulnerabilityProof(
                vector_id="OAUTH-PKCE-DOWNGRADE",
                category="PKCE",
                description="Token endpoint issued access token with missing or invalid PKCE verifier, violating RFC 7636.",
                exploit_payload=first,
                target_endpoint="/token",
                response_status=first["status"],
                response_body=first["body"],
                poc_summary=f"PKCE bypass succeeded on {len(succeeded)}/{len(mutations)} mutation variants. Primary: {first['description']}",
                mutations_tested=len(mutations),
                mutations_succeeded=len(succeeded),
            )
        return None

    def test_redirect_traversal(self, client: httpx.Client, ctx: ProbeContext) -> Optional[VulnerabilityProof]:
        """Redirect URI mutation suite. RFC 6749 §3.1.2 mandates exact string comparison."""
        mutations = OAuthPayloadMutator.mutate_redirect_uri(ctx.redirect_uri)
        succeeded = []
        for mut in mutations:
            auth_resp = client.get(
                f"{ctx.base_url}/authorize",
                params={**self.authorize_params(ctx), "redirect_uri": mut["uri"]},
            )
            if auth_resp.status_code == 200 and "code" in auth_resp.json():
                succeeded.append({
                    "mutation_type": mut["type"],
                    "description": mut["description"],
                    "uri": mut["uri"],
                    "status": auth_resp.status_code,
                    "body": auth_resp.json(),
                })
        if succeeded:
            first = succeeded[0]
            return VulnerabilityProof(
                vector_id="OAUTH-REDIRECT-TRAVERSAL",
                category="REDIRECT_URI",
                description="Authorization endpoint accepted path-traversal or manipulated redirect_uri bypassing whitelist.",
                exploit_payload=first,
                target_endpoint="/authorize",
                response_status=first["status"],
                response_body=first["body"],
                poc_summary=f"Redirect URI bypass succeeded on {len(succeeded)}/{len(mutations)} variants. Trigger: {first['description']} ({first['uri']})",
                mutations_tested=len(mutations),
                mutations_succeeded=len(succeeded),
            )
        return None

    def test_state_csrf(self, client: httpx.Client, ctx: ProbeContext) -> Optional[VulnerabilityProof]:
        """State CSRF mutation suite. RFC 6749 §10.12 mandates strong CSRF binding."""
        mutations = OAuthPayloadMutator.mutate_state_parameters()
        succeeded = []
        for mut in mutations:
            params = {k: v for k, v in self.authorize_params(ctx).items() if k != "state"}
            if mut["state"] is not None:
                params["state"] = mut["state"]
            auth_resp = client.get(f"{ctx.base_url}/authorize", params=params)
            if auth_resp.status_code == 200 and "code" in auth_resp.json():
                succeeded.append({
                    "mutation_type": mut["type"],
                    "description": mut["description"],
                    "status": auth_resp.status_code,
                    "body": auth_resp.json(),
                })
        if succeeded:
            first = succeeded[0]
            return VulnerabilityProof(
                vector_id="OAUTH-STATE-CSRF",
                category="CSRF",
                description="Authorization endpoint granted code without validating state parameter presence or entropy.",
                exploit_payload=first,
                target_endpoint="/authorize",
                response_status=first["status"],
                response_body=first["body"],
                poc_summary=f"State CSRF flaw succeeded on {len(succeeded)}/{len(mutations)} variants. Trigger: {first['description']}",
                mutations_tested=len(mutations),
                mutations_succeeded=len(succeeded),
            )
        return None

    def test_code_replay(self, client: httpx.Client, ctx: ProbeContext) -> Optional[VulnerabilityProof]:
        """Authorization code replay. RFC 6749 §4.1.2 mandates single-use codes."""
        verifier, challenge = generate_pkce_pair()
        auth_resp = client.get(
            f"{ctx.base_url}/authorize",
            params={**self.authorize_params(ctx), "code_challenge": challenge, "code_challenge_method": "S256"},
        )
        if auth_resp.status_code != 200:
            return None
        code = auth_resp.json().get("code")
        if not code:
            return None
        token_payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": ctx.redirect_uri,
            "client_id": ctx.client_id,
            "code_verifier": verifier,
        }
        resp1 = client.post(f"{ctx.base_url}/token", json=token_payload)
        if resp1.status_code != 200:
            return None
        resp2 = client.post(f"{ctx.base_url}/token", json=token_payload)
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

    def test_scope_escalation(self, client: httpx.Client, ctx: ProbeContext) -> Optional[VulnerabilityProof]:
        """Scope escalation mutation suite. RFC 6749 §3.3."""
        verifier, challenge = generate_pkce_pair()
        mutations = OAuthPayloadMutator.mutate_scope_escalations(ctx.scope)
        succeeded = []
        for mut in mutations:
            auth_resp = client.get(
                f"{ctx.base_url}/authorize",
                params={**self.authorize_params(ctx), "code_challenge": challenge, "code_challenge_method": "S256"},
            )
            if auth_resp.status_code != 200:
                continue
            code = auth_resp.json().get("code")
            if not code:
                continue
            token_resp = client.post(
                f"{ctx.base_url}/token",
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": ctx.redirect_uri,
                    "client_id": ctx.client_id,
                    "code_verifier": verifier,
                    "scope": mut["scope"],
                },
            )
            if token_resp.status_code == 200:
                body = token_resp.json()
                granted_scope = body.get("scope", "")
                if any(e in granted_scope for e in ["admin", "write:all", "*", "root"]):
                    succeeded.append({
                        "mutation_type": mut["type"],
                        "description": mut["description"],
                        "requested_scope": mut["scope"],
                        "granted_scope": granted_scope,
                        "status": token_resp.status_code,
                        "body": body,
                    })
        if succeeded:
            first = succeeded[0]
            return VulnerabilityProof(
                vector_id="OAUTH-SCOPE-ESCALATION",
                category="PRIVILEGE_ESCALATION",
                description="Token endpoint granted elevated unconsented scopes exceeding user consent.",
                exploit_payload=first,
                target_endpoint="/token",
                response_status=first["status"],
                response_body=first["body"],
                poc_summary=f"Scope escalation succeeded on {len(succeeded)}/{len(mutations)} variants. Granted: {first['granted_scope']}",
                mutations_tested=len(mutations),
                mutations_succeeded=len(succeeded),
            )
        return None
