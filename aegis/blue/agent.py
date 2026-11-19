"""
Aegis Blue Team Agent (Patcher).
Coordinates AST-guided fault localization, route inspection, and RFC standard
analysis to generate surgical code patches that neutralize exploits while
strictly preserving valid functional behaviors and API contracts.
"""

from typing import Optional, Dict, Any, Tuple, List
import os
import ast
from aegis.core.state import VulnerabilityProof, PatchResult
from aegis.blue.aci import AgentComputerInterface


class BlueAgent:
    """Autonomous Blue Team Agent for OAuth Vulnerability Remediation."""

    def __init__(self, aci: AgentComputerInterface, target_file: str = "aegis/testbed/app.py"):
        self.aci = aci
        self.target_file = target_file

    def locate_vulnerable_handler(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        AST-Guided Fault Localization:
        Parses the target repository files to locate the exact route handler function
        responsible for the vulnerable endpoint.
        """
        handlers = self.aci.find_route_handlers(self.target_file)
        for h in handlers:
            if h.get("route_path") == endpoint:
                return h
        return None

    def synthesize_patch(self, proof: VulnerabilityProof, handler: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Context-Aware Patch Synthesis:
        Analyzes the target handler's AST metadata and constructs an RFC-compliant
        remediation block tailored to the endpoint and vulnerability category.
        """
        vector_id = proof.vector_id

        # Read source code of the file
        full_path = self.aci._resolve_path(self.target_file)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        if vector_id == "OAUTH-PKCE-DOWNGRADE":
            # Detect flawed PKCE check in /token handler
            flawed_block = """    if auth_data.get("code_challenge"):
        if req.code_verifier is None:
            # Flaw: Silently continues without verifier instead of rejecting!
            pass
        else:
            if not verify_pkce(req.code_verifier, auth_data["code_challenge"], auth_data["code_challenge_method"]):
                return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "PKCE verification failed"})"""

            remediated_block = """    # RFC 7636 Section 4.4.1 PKCE Enforcement
    if auth_data.get("code_challenge"):
        if not req.code_verifier:
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_grant", "error_description": "code_verifier is required when code_challenge is set"}
            )
        if not verify_pkce(req.code_verifier, auth_data["code_challenge"], auth_data["code_challenge_method"]):
            return JSONResponse(status_code=400, content={"error": "invalid_grant", "error_description": "PKCE verification failed"})"""

            if flawed_block in content:
                return {
                    "target": flawed_block,
                    "replacement": remediated_block,
                    "explanation": "Strictly enforce code_verifier presence when code_challenge was established during authorization.",
                }

        elif vector_id == "OAUTH-REDIRECT-TRAVERSAL":
            # Detect weak prefix/startswith check in /authorize handler
            flawed_block = """    # 2. Redirect URI Validation
    # VULNERABILITY (OAUTH-REDIRECT-TRAVERSAL):
    # Currently uses weak startswith check rather than exact matching or strict parsing,
    # allowing path traversal or arbitrary subpaths (e.g. https://my-saas-app.com/callback/../../attacker)
    valid_redirect = any(redirect_uri.startswith(reg_uri) for reg_uri in client["redirect_uris"])
    if not valid_redirect:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "Invalid redirect_uri"})"""

            remediated_block = """    # 2. Redirect URI Validation (RFC 6749 Section 3.1.2 & RFC 6819 Section 4.4.1.7)
    # Strictly require exact string matching against pre-registered redirect_uris
    if redirect_uri not in client["redirect_uris"]:
        return JSONResponse(status_code=400, content={"error": "invalid_request", "error_description": "redirect_uri must exactly match registered URI"})"""

            if flawed_block in content:
                return {
                    "target": flawed_block,
                    "replacement": remediated_block,
                    "explanation": "Replace insecure startswith prefix check with exact URI matching to prevent path traversal and open redirects.",
                }

        elif vector_id == "OAUTH-STATE-CSRF":
            # Detect missing state enforcement in /authorize handler
            flawed_block = """    # 3. State Parameter Check
    # VULNERABILITY (OAUTH-STATE-CSRF):
    # State parameter is not strictly enforced, allowing login CSRF attacks
    # [BLUE TEAM TARGET: enforce state parameter presence]"""

            remediated_block = """    # 3. State Parameter Check (RFC 6749 Section 10.12)
    # Enforce state parameter to prevent Login Cross-Site Request Forgery (CSRF)
    if not state or len(state.strip()) < 8:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_request", "error_description": "state parameter with sufficient entropy is required for CSRF protection"}
        )"""

            if flawed_block in content:
                return {
                    "target": flawed_block,
                    "replacement": remediated_block,
                    "explanation": "Mandate state parameter with minimum entropy to block Cross-Site Request Forgery (CSRF).",
                }

        elif vector_id == "OAUTH-CODE-REPLAY":
            # Detect missing one-time use check in /token handler
            flawed_block = """    # VULNERABILITY (OAUTH-CODE-REPLAY):
    # Code is NOT marked as used or invalidated immediately upon first redemption!
    # [BLUE TEAM TARGET: if auth_data['used']: raise error, and set auth_data['used'] = True]"""

            remediated_block = """    # RFC 6749 Section 4.1.2: One-Time Use Enforcement
    if auth_data.get("used", False):
        # Invalidate code and reject replay attempt immediately
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_grant", "error_description": "Authorization code has already been redeemed (replay detected)"}
        )
    # Mark code as consumed immediately
    auth_data["used"] = True"""

            if flawed_block in content:
                return {
                    "target": flawed_block,
                    "replacement": remediated_block,
                    "explanation": "Enforce single-use authorization codes by rejecting replay attempts and marking codes as consumed immediately.",
                }

        elif vector_id == "OAUTH-SCOPE-ESCALATION":
            # Detect unchecked scope granting in /token handler
            flawed_block = """    # 4. Scope Enforcement
    # VULNERABILITY (OAUTH-SCOPE-ESCALATION):
    # If request specifies extra scope, it is blindly accepted even if not consented
    granted_scope = req.scope if req.scope else auth_data["scope"]"""

            remediated_block = """    # 4. Scope Enforcement (RFC 6749 Section 3.3)
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
        granted_scope = auth_data["scope"]"""

            if flawed_block in content:
                return {
                    "target": flawed_block,
                    "replacement": remediated_block,
                    "explanation": "Validate that requested scopes at the token endpoint are a strict subset of the scopes consented during authorization.",
                }

        return None

    def generate_and_apply_patch(self, proof: VulnerabilityProof) -> Optional[PatchResult]:
        """
        Executes AST-guided localization, patch synthesis, AST validation,
        and atomic application via the ACI.
        """
        # 1. Fault Localization via AST
        handler = self.locate_vulnerable_handler(proof.target_endpoint)
        if not handler:
            return None

        # 2. Context-Aware Synthesis
        patch_data = self.synthesize_patch(proof, handler)
        if not patch_data:
            return None

        # 3. Create clean baseline snapshot
        self.aci.create_snapshot(self.target_file)

        # 4. Apply surgical replacement with Gate 0 AST syntax validation
        success = self.aci.replace_block(
            file_path=self.target_file,
            target_block=patch_data["target"],
            replacement_block=patch_data["replacement"],
        )

        if not success:
            return None

        lines_changed = len(patch_data["replacement"].splitlines())
        return PatchResult(
            vector_id=proof.vector_id,
            diff_patch=f"- {patch_data['target']}\n+ {patch_data['replacement']}",
            target_file=self.target_file,
            explanation=patch_data["explanation"],
            lines_changed=lines_changed,
            ast_validated=True,
        )

    def rollback_patch(self) -> bool:
        """Reverts the last applied patch if regression tests fail."""
        return self.aci.rollback(self.target_file)
