"""
Aegis Red Team Parameter Mutation Engine.
Generates multi-variant adversarial payloads to test whether
defensive patches are resilient against encoding, traversal,
delimiter, and state-machine bypass variations.
"""

from typing import List, Dict, Any, Tuple
import urllib.parse


class OAuthPayloadMutator:
    """Generates property-based adversarial mutations across OAuth parameter spaces."""

    @staticmethod
    def mutate_redirect_uri(base_valid_uri: str, attacker_target: str = "attacker_leak") -> List[Dict[str, str]]:
        """
        Generates mutation variants for redirect_uri bypass testing.
        Tests whether the server enforces exact matching or falls prey to
        URL encoding, directory traversal, prefix matching, or sub-domain tricks.
        """
        mutations = [
            {
                "type": "PLAIN_TRAVERSAL",
                "uri": f"{base_valid_uri}/../../{attacker_target}",
                "description": "Standard directory traversal via /../../",
            },
            {
                "type": "URL_ENCODED_TRAVERSAL",
                "uri": f"{base_valid_uri}/%2e%2e/%2e%2e/{attacker_target}",
                "description": "Single URL-encoded dot-dot-slash (%2e%2e/)",
            },
            {
                "type": "DOUBLE_ENCODED_TRAVERSAL",
                "uri": f"{base_valid_uri}/%252e%252e/%252e%252e/{attacker_target}",
                "description": "Double URL-encoded dot-dot-slash (%252e%252e/)",
            },
            {
                "type": "SUBDOMAIN_CONFUSION",
                "uri": "https://my-saas-app.com.evil-domain.com/callback",
                "description": "Subdomain suffix spoofing against weak regex / prefix match",
            },
            {
                "type": "PARAMETER_POLLUTION_INJECTION",
                "uri": f"{base_valid_uri}?target=https://attacker.com/{attacker_target}",
                "description": "Open redirect parameter chaining",
            },
        ]
        return mutations

    @staticmethod
    def mutate_pkce_downgrades(valid_verifier: str) -> List[Dict[str, Any]]:
        """
        Generates mutation variants for PKCE enforcement.
        """
        return [
            {
                "type": "OMISSION",
                "verifier": None,
                "description": "Complete omission of code_verifier field",
            },
            {
                "type": "EMPTY_STRING",
                "verifier": "",
                "description": "Empty string as code_verifier",
            },
            {
                "type": "ARBITRARY_MISMATCH",
                "verifier": "invalid_random_verifier_string_000000000000",
                "description": "Mismatched code_verifier string",
            },
            {
                "type": "METHOD_TAMPERING",
                "verifier": "plain_challenge_tamper_attempt",
                "description": "Attempting to force plain method downgrade verification",
            },
        ]

    @staticmethod
    def mutate_state_parameters() -> List[Dict[str, Any]]:
        """
        Generates mutation variants for CSRF state parameter checking.
        """
        return [
            {
                "type": "OMITTED",
                "state": None,
                "description": "Omission of state parameter entirely",
            },
            {
                "type": "LOW_ENTROPY",
                "state": "1",
                "description": "Single-digit static low-entropy state",
            },
            {
                "type": "WHITESPACE_ONLY",
                "state": "   ",
                "description": "Whitespace-only state string",
            },
        ]

    @staticmethod
    def mutate_scope_escalations(consented_scope: str) -> List[Dict[str, str]]:
        """
        Generates mutation variants for scope injection and vertical privilege escalation.
        """
        return [
            {
                "type": "ADMIN_SPACE_DELIMITED",
                "scope": f"{consented_scope} admin",
                "description": "Appending 'admin' role via standard space delimiter",
            },
            {
                "type": "WRITE_ALL_DELIMITED",
                "scope": f"{consented_scope} write:all",
                "description": "Appending 'write:all' administrative permission",
            },
            {
                "type": "WILDCARD_INJECTION",
                "scope": f"{consented_scope} *",
                "description": "Attempting wildcard root scope escalation (*)",
            },
            {
                "type": "ROOT_OVERRIDE",
                "scope": "root system_admin",
                "description": "Completely replacing consented scope with root access",
            },
        ]
