"""
Bring-Your-Own-App intake layer for Umbrella.

Lets a user point Umbrella at a custom FastAPI/Starlette OAuth 2.0 application
instead of the bundled testbed. Performs shape validation (routes, app object),
a baseline functional check, and patch-anchor pre-checks so runs fail clearly
and early instead of mid-loop.
"""

import ast
import importlib.util
import json
import os
import secrets
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from starlette.applications import Starlette

from aegis.blue.aci import AgentComputerInterface

# Legacy testbed constants (kept for the bundled-app path)
LEGACY_CLIENT_ID = "client-app-123"
LEGACY_REDIRECT_URI = "https://my-saas-app.com/callback"
LEGACY_SCOPE = "read:profile"
LEGACY_STATE = "state_123"

REQUIRED_ROUTES = ["/authorize", "/token"]
RECOMMENDED_ROUTES = ["/userinfo"]


class TargetIntakeError(Exception):
    """Raised when a bring-your-own-app target fails shape validation."""


@dataclass
class TargetProfile:
    """Everything the agents need to know about the target under test."""
    path: str                      # absolute path to the target module file
    app_module: Any = None         # loaded Python module
    app_attr: str = "app"          # name of the Starlette/FastAPI instance in the module
    client_id: str = LEGACY_CLIENT_ID
    redirect_uri: str = LEGACY_REDIRECT_URI
    scope: str = LEGACY_SCOPE
    state: str = LEGACY_STATE
    discovered_routes: List[Dict[str, Any]] = field(default_factory=list)
    patch_anchor_coverage: Dict[str, bool] = field(default_factory=dict)
    baseline_ok: bool = False

    @property
    def app(self) -> Any:
        """Current Starlette/FastAPI instance (re-read after module reloads)."""
        return getattr(self.app_module, self.app_attr, None)


def discover_route_handlers(file_path: str) -> List[Dict[str, Any]]:
    """AST-walks a target file for decorated route handlers (no containment restriction)."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)
    handlers = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    method = dec.func.attr.lower()
                    route_path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else None
                    handlers.append({
                        "name": node.name,
                        "route_path": route_path,
                        "method": method,
                        "lineno": node.lineno,
                        "arguments": [a.arg for a in node.args.args],
                    })
    return handlers


def load_target_module(file_path: str) -> Any:
    """Imports an arbitrary application module by file path."""
    abs_path = os.path.abspath(file_path)
    module_name = f"umbrella_byo_target_{abs(hash(abs_path)) % 100000}"
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module  # register so importlib.reload() works on later rounds
    spec.loader.exec_module(module)
    return module


def find_app_instance(module: Any) -> Tuple[str, Any]:
    """Finds the Starlette/FastAPI instance attribute in a target module."""
    for attr in ("app", "application"):
        inst = getattr(module, attr, None)
        if isinstance(inst, Starlette):
            return attr, inst
    for name in dir(module):
        if name.startswith("_"):
            continue
        inst = getattr(module, name, None)
        if isinstance(inst, Starlette):
            return name, inst
    raise TargetIntakeError(
        "No FastAPI/Starlette application instance found in the target module.\n"
        "The module must define a global app object, e.g.:\n"
        "    from fastapi import FastAPI\n    app = FastAPI()"
    )


def _baseline_check(app, profile: TargetProfile) -> Tuple[bool, str]:
    """Confirms a legitimate authorize -> token flow works with the profile's identifiers."""
    from fastapi.testclient import TestClient

    base_url = "http://testserver"
    with TestClient(app, base_url=base_url) as client:
        from aegis.red.probes import generate_pkce_pair
        verifier, challenge = generate_pkce_pair()
        resp = client.get(f"{base_url}/authorize", params={
            "response_type": "code",
            "client_id": profile.client_id,
            "redirect_uri": profile.redirect_uri,
            "scope": profile.scope,
            "state": profile.state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })
        if resp.status_code != 200:
            return False, (f"/authorize rejected the profile parameters with HTTP {resp.status_code}: {resp.text[:200]}\n"
                          "Check that --client-id and --redirect-uri match a registered client in your app.")
        code = resp.json().get("code")
        if not code:
            return False, "authorize returned 200 but no authorization code was present."
        token_resp = client.post(f"{base_url}/token", json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": profile.redirect_uri,
            "client_id": profile.client_id,
            "code_verifier": verifier,
            "scope": profile.scope,
        })
        if token_resp.status_code != 200 or "access_token" not in token_resp.json():
            return False, f"/token exchange failed with HTTP {token_resp.status_code}: {token_resp.text[:200]}"
    return True, "Baseline OAuth code-flow (authorize -> token) succeeded with the provided identifiers."


def load_target(
    path: str,
    client_id: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    scope: Optional[str] = None,
    state: Optional[str] = None,
    skip_baseline: bool = False,
) -> TargetProfile:
    """Loads, validates, and profiles a custom OAuth application for Umbrella."""
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        raise TargetIntakeError(f"Target file does not exist: {path}")
    if not abs_path.endswith(".py"):
        raise TargetIntakeError(f"Target must be a Python module: {path}")

    # 1. Syntax + load
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            ast.parse(f.read(), filename=abs_path)
    except SyntaxError as e:
        raise TargetIntakeError(f"Target file has a syntax error (line {e.lineno}): {e.msg}")

    try:
        module = load_target_module(abs_path)
    except Exception as e:
        raise TargetIntakeError(f"Could not import the target module: {e}\n"
                                "Ensure all of its imports (FastAPI, etc.) are installed in this environment.")

    # 2. App instance
    app_attr, app = find_app_instance(module)

    # 3. Route shape
    routes = discover_route_handlers(abs_path)
    paths = [h["route_path"] for h in routes]
    missing = [r for r in REQUIRED_ROUTES if r not in paths]
    if missing:
        raise TargetIntakeError(
            f"Target is missing required OAuth routes: {missing}\n"
            f"Discovered routes: {paths}\n"
            "Umbrella tests an authorization server with GET /authorize and POST /token."
        )

    # 4. Profile identifiers
    if not client_id or not redirect_uri:
        raise TargetIntakeError(
            "Custom targets require --client-id and --redirect-uri: the identifiers of a registered "
            "client in your application that the probes should use."
        )

    profile = TargetProfile(
        path=abs_path,
        app_module=module,
        app_attr=app_attr,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope or LEGACY_SCOPE,
        state=state or f"umb_{secrets.token_hex(8)}",
        discovered_routes=routes,
    )

    # 5. Baseline functional check (fail clearly, up front)
    if skip_baseline:
        profile.baseline_ok = True
    else:
        ok, msg = _baseline_check(app, profile)
        if not ok:
            raise TargetIntakeError(f"Baseline check failed:\n{msg}")
        profile.baseline_ok = True

    # 6. Patch-anchor pre-check (repair capability report, non-blocking)
    try:
        from aegis.blue.agent import BlueAgent
        aci = AgentComputerInterface(os.path.dirname(abs_path))
        blue = BlueAgent(aci, target_file=os.path.basename(abs_path))
        profile.patch_anchor_coverage = blue.anchor_coverage()
    except Exception:
        profile.patch_anchor_coverage = {}

    return profile


def intake_report(profile: TargetProfile) -> str:
    """Human-readable summary of a validated target for terminal output."""
    lines = [
        f"Target module:      {profile.path}",
        f"App instance:       {profile.app_attr} ({type(profile.app).__name__})",
        f"Client under test:  client_id={profile.client_id} redirect={profile.redirect_uri} scope={profile.scope}",
        f"Routes discovered:  {[r['route_path'] for r in profile.discovered_routes]}",
    ]
    if profile.patch_anchor_coverage:
        covered = [v for v, ok in profile.patch_anchor_coverage.items() if ok]
        uncovered = [v for v, ok in profile.patch_anchor_coverage.items() if not ok]
        lines.append(f"Patch anchors:      {len(covered)}/5 vulnerability classes have patch anchors in this code")
        if uncovered:
            lines.append(f"Unpatchable:        {uncovered} (will be detected but left unresolved unless anchors match)")
    return "\n".join(lines)
