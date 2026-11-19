"""
Aegis Core Configuration and Threat Matrix.
Defines the standard OAuth 2.0 / OIDC attack vectors derived from
RFC 6749, RFC 7636, RFC 6819, RFC 9207, and OAuth Security Best Current Practices.
"""

from typing import Dict, Any, List


# Standard threat matrix of OAuth 2.0 vulnerabilities
OAUTH_THREAT_MATRIX: Dict[str, Dict[str, Any]] = {
    "OAUTH-PKCE-DOWNGRADE": {
        "name": "PKCE Downgrade / Omission Attack",
        "description": "Tests if authorization code exchange succeeds without code_verifier when code_challenge was provided or omitted, violating RFC 7636.",
        "category": "PKCE",
        "rfc_reference": "RFC 7636",
        "severity": "HIGH",
    },
    "OAUTH-REDIRECT-TRAVERSAL": {
        "name": "Redirect URI Path Traversal / Wildcard Bypass",
        "description": "Tests whether authorization endpoint allows redirect_uri manipulation (e.g. directory traversal / path tampering) to leak auth codes.",
        "category": "REDIRECT_URI",
        "rfc_reference": "RFC 6749 Section 3.1.2 & RFC 6819 Section 4.4.1.7",
        "severity": "CRITICAL",
    },
    "OAUTH-STATE-CSRF": {
        "name": "State Parameter Omission / Login CSRF",
        "description": "Tests if client or authorization server completes the flow when state parameter is omitted, allowing cross-site request forgery.",
        "category": "CSRF",
        "rfc_reference": "RFC 6749 Section 10.12",
        "severity": "HIGH",
    },
    "OAUTH-CODE-REPLAY": {
        "name": "Authorization Code Replay / Multi-Redemption",
        "description": "Tests if authorization codes can be redeemed multiple times to issue multiple access tokens, violating one-time use requirement.",
        "category": "REPLAY",
        "rfc_reference": "RFC 6749 Section 4.1.2",
        "severity": "CRITICAL",
    },
    "OAUTH-SCOPE-ESCALATION": {
        "name": "Unauthorized Scope Injection / Privilege Escalation",
        "description": "Tests if token endpoint grants elevated scopes (e.g., admin, write:all) that were never consented to in the authorization step.",
        "category": "PRIVILEGE_ESCALATION",
        "rfc_reference": "RFC 6749 Section 3.3",
        "severity": "HIGH",
    },
}


DEFAULT_VECTORS: List[str] = list(OAUTH_THREAT_MATRIX.keys())

MAX_REPAIR_ATTEMPTS_PER_VECTOR = 3
DEFAULT_TARGET_PORT = 8089
DEFAULT_HOST = "127.0.0.1"
