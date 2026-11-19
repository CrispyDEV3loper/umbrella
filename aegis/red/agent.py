"""
Aegis Red Team Agent.
Intelligently sequences attack vectors, parameterizes payloads,
executes protocol probes against the target app, and generates
actionable vulnerability proofs for the Blue Agent.
"""

from typing import Optional, Dict, Any, List
import httpx
from aegis.core.state import VulnerabilityProof, AegisState
from aegis.core.config import OAUTH_THREAT_MATRIX
from aegis.red.probes import OAuthAttackProbes


class RedAgent:
    """Autonomous Red Team Agent focusing on OAuth & 3rd-party integrations."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.probe_dispatch = {
            "OAUTH-PKCE-DOWNGRADE": OAuthAttackProbes.test_pkce_downgrade,
            "OAUTH-REDIRECT-TRAVERSAL": OAuthAttackProbes.test_redirect_traversal,
            "OAUTH-STATE-CSRF": OAuthAttackProbes.test_state_csrf,
            "OAUTH-CODE-REPLAY": OAuthAttackProbes.test_code_replay,
            "OAUTH-SCOPE-ESCALATION": OAuthAttackProbes.test_scope_escalation,
        }

    def plan_next_attack(self, state: AegisState) -> Optional[str]:
        """Selects the next unverified or pending attack vector."""
        for vector_id in state.pending_vectors:
            if vector_id not in state.remediated_vectors:
                return vector_id
        return None

    def execute_vector(self, vector_id: str, client: httpx.Client) -> Optional[VulnerabilityProof]:
        """Executes a specific attack probe against the target service."""
        probe_fn = self.probe_dispatch.get(vector_id)
        if not probe_fn:
            raise ValueError(f"Unknown attack vector: {vector_id}")

        proof = probe_fn(client, self.base_url)
        return proof
