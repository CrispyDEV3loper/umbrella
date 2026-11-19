"""
Aegis Red Team Agent (Adaptive Attack Planner).
Dynamically prioritizes attack vectors based on threat severity,
past attack outcomes, endpoint surface analysis, and response telemetry.
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
            "OAUTH-REDIRECT-TRAVERSAL": OAuthAttackProbes.test_redirect_traversal,
            "OAUTH-CODE-REPLAY": OAuthAttackProbes.test_code_replay,
            "OAUTH-PKCE-DOWNGRADE": OAuthAttackProbes.test_pkce_downgrade,
            "OAUTH-SCOPE-ESCALATION": OAuthAttackProbes.test_scope_escalation,
            "OAUTH-STATE-CSRF": OAuthAttackProbes.test_state_csrf,
        }
        # Severity weights for adaptive prioritization
        self.severity_weights = {
            "CRITICAL": 100,
            "HIGH": 75,
            "MEDIUM": 50,
            "LOW": 25,
        }
        self.attack_history: List[Dict[str, Any]] = []

    def plan_next_attack(self, state: AegisState) -> Optional[str]:
        """
        Adaptive Attack Planner:
        Instead of a naive FIFO queue, dynamically ranks candidates by:
        1. Threat severity (CRITICAL before HIGH).
        2. Endpoint correlation: if /token had a flaw, prioritize other /token vectors.
        3. Exclusion of already remediated vectors.
        """
        candidates = [v for v in state.pending_vectors if v not in state.remediated_vectors]
        if not candidates:
            return None

        # Prioritize based on severity and recent findings
        def score_vector(vector_id: str) -> int:
            meta = OAUTH_THREAT_MATRIX.get(vector_id, {})
            score = self.severity_weights.get(meta.get("severity", "MEDIUM"), 50)

            # Boost score if target endpoint matches recent successful exploit
            if self.attack_history and self.attack_history[-1].get("succeeded"):
                last_endpoint = self.attack_history[-1].get("target_endpoint")
                if (last_endpoint == "/token" and vector_id in ["OAUTH-PKCE-DOWNGRADE", "OAUTH-CODE-REPLAY", "OAUTH-SCOPE-ESCALATION"]) or \
                   (last_endpoint == "/authorize" and vector_id in ["OAUTH-REDIRECT-TRAVERSAL", "OAUTH-STATE-CSRF"]):
                    score += 20
            return score

        candidates.sort(key=score_vector, reverse=True)
        return candidates[0]

    def execute_vector(self, vector_id: str, client: httpx.Client) -> Optional[VulnerabilityProof]:
        """Executes a specific attack probe against the target service and records telemetry."""
        probe_fn = self.probe_dispatch.get(vector_id)
        if not probe_fn:
            raise ValueError(f"Unknown attack vector: {vector_id}")

        proof = probe_fn(client, self.base_url)

        # Update telemetry history
        self.attack_history.append({
            "vector_id": vector_id,
            "succeeded": proof is not None,
            "target_endpoint": proof.target_endpoint if proof else None,
            "mutations_tested": proof.mutations_tested if proof else 1,
            "mutations_succeeded": proof.mutations_succeeded if proof else 0,
        })

        return proof
