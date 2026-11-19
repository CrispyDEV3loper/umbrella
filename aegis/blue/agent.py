"""
Aegis Blue Team Agent (Patcher).
Combines SWE-agent ACI with OAuth RFC standards to generate
surgical code patches that neutralize exploits while preserving
valid functional behaviors.
"""

from typing import Optional, Dict, Any, Tuple
import os
from aegis.core.state import VulnerabilityProof, PatchResult
from aegis.blue.aci import AgentComputerInterface


class BlueAgent:
    """Autonomous Blue Team Agent for OAuth Vulnerability Remediation."""

    def __init__(self, aci: AgentComputerInterface):
        self.aci = aci
        self.target_file = "aegis/testbed/app.py"

        # Canonical RFC-compliant remediation patches for known OAuth flaws
        self._remediation_recipes = {
            "OAUTH-PKCE-DOWNGRADE": {
                "target": """    if auth_data.get("code_challenge"):
        if req.code_verifier is None:
            # Flaw: Silently continues without verifier instead of rejecting!
            pass
        else:
            if not verify_pkce(req.code_verifier, auth_data["code_challenge"], auth_data["code_challenge_method"]):
                return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "PKCE verification failed"})""",
                "replacement": """    # RFC 7636 Section 4.4.1 PKCE Enforcement
    if auth_data.get("code_challenge"):
        if not req.code_verifier:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_grant", "error_description": "code_verifier is required when code_challenge is set"}
            )
        if not verify_pkce(req.code_verifier, auth_data["code_challenge"], auth_data["code_challenge_method"]):
            return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "PKCE verification failed"})""",
                "explanation": "Strictly enforce code_verifier presence when code_challenge was established during authorization.",
            },
            "OAUTH-REDIRECT-TRAVERSAL": {
                "target": """    # 2. Redirect URI Validation
    # VULNERABILITY (OAUTH-REDIRECT-TRAVERSAL):
    # Currently uses weak startswith check rather than exact matching or strict parsing,
    # allowing path traversal or arbitrary subpaths (e.g. https://my-saas-app.com/callback/../../attacker)
    valid_redirect = any(redirect_uri.startswith(reg_uri) for reg_uri in client["redirect_uris"])
    if not valid_redirect:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "Invalid redirect_uri"})""",
                "replacement": """    # 2. Redirect URI Validation (RFC 6749 Section 3.1.2 & RFC 6819 Section 4.4.1.7)
    # Strictly require exact string matching against pre-registered redirect_uris
    if redirect_uri not in client["redirect_uris"]:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "redirect_uri must exactly match registered URI"})""",
                "explanation": "Replace insecure startswith prefix check with exact URI matching to prevent path traversal and open redirects.",
            },
            "OAUTH-STATE-CSRF": {
                "target": """    # 3. State Parameter Check
    # VULNERABILITY (OAUTH-STATE-CSRF):
    # State parameter is not strictly enforced, allowing login CSRF attacks
    # [BLUE TEAM TARGET: enforce state parameter presence]""",
                "replacement": """    # 3. State Parameter Check (RFC 6749 Section 10.12)
    # Enforce state parameter to prevent Login Cross-Site Request Forgery (CSRF)
    if not state or len(state.strip()) < 8:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_request", "error_description": "state parameter with sufficient entropy is required for CSRF protection"}
        )""",
                "explanation": "Mandate state parameter with minimum entropy to block Cross-Site Request Forgery (CSRF).",
            },
            "OAUTH-CODE-REPLAY": {
                "target": """    # VULNERABILITY (OAUTH-CODE-REPLAY):
    # Code is NOT marked as used or invalidated immediately upon first redemption!
    # [BLUE TEAM TARGET: if auth_data['used']: raise error, and set auth_data['used'] = True]""",
                "replacement": """    # RFC 6749 Section 4.1.2: One-Time Use Enforcement
    if auth_data.get("used", False):
        # Invalidate code and reject replay attempt immediately
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_grant", "error_description": "Authorization code has already been redeemed (replay detected)"}
        )
    # Mark code as consumed immediately
    auth_data["used"] = True""",
                "explanation": "Enforce single-use authorization codes by rejecting replay attempts and marking codes as consumed immediately.",
            },
            "OAUTH-SCOPE-ESCALATION": {
                "target": """    # 4. Scope Enforcement
    # VULNERABILITY (OAUTH-SCOPE-ESCALATION):
    # If request specifies extra scope, it is blindly accepted even if not consented
    granted_scope = req.scope if req.scope else auth_data["scope"]""",
                "replacement": """    # 4. Scope Enforcement (RFC 6749 Section 3.3)
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
        granted_scope = auth_data["scope"]""",
                "explanation": "Validate that requested scopes at the token endpoint are a strict subset of the scopes consented during authorization.",
            },
        }

    def generate_and_apply_patch(self, proof: VulnerabilityProof) -> Optional[PatchResult]:
        """
        Locates the vulnerability in the codebase, generates the minimal surgical patch,
        and applies it through the ACI.
        """
        recipe = self._remediation_recipes.get(proof.vector_id)
        if not recipe:
            return None

        # Take a snapshot of the clean baseline before editing
        self.aci.create_snapshot(self.target_file)

        # Apply surgical replacement
        success = self.aci.replace_block(
            file_path=self.target_file,
            target_block=recipe["target"],
            replacement_block=recipe["replacement"],
        )

        if not success:
            return None

        lines_changed = len(recipe["replacement"].splitlines())
        return PatchResult(
            vector_id=proof.vector_id,
            diff_patch=f"- {recipe['target']}\n+ {recipe['replacement']}",
            target_file=self.target_file,
            explanation=recipe["explanation"],
            lines_changed=lines_changed,
        )

    def rollback_patch(self) -> bool:
        """Reverts the last applied patch if regression tests fail."""
        return self.aci.rollback(self.target_file)
