"""
Aegis Red Team Agent (Adaptive Attack Planner).
Dynamically prioritizes attack vectors based on threat severity,
past attack outcomes, endpoint surface analysis, and response telemetry.
"""

from typing import Optional, Dict, Any, List
import httpx
from aegis.core.state import VulnerabilityProof, AegisState
from aegis.core.config import OAUTH_THREAT_MATRIX
from aegis.red.probes import OAuthAttackProbes, ProbeContext
from aegis.core.target import TargetProfile, LEGACY_CLIENT_ID, LEGACY_REDIRECT_URI, LEGACY_SCOPE, LEGACY_STATE


class RedAgent:
    """Autonomous Red Team Agent focusing on OAuth & 3rd-party integrations."""

    def __init__(self, base_url: str, profile: Optional[TargetProfile] = None):
        self.base_url = base_url
        self.profile = profile
        # Probe context: custom target identifiers, or legacy bundled-testbed constants.
        if profile is not None:
            self.ctx = ProbeContext(base_url, profile)
        else:
            self.ctx = ProbeContext.from_strings(base_url, LEGACY_CLIENT_ID, LEGACY_REDIRECT_URI, LEGACY_SCOPE, LEGACY_STATE)
        self.probes = OAuthAttackProbes()
        self.probe_dispatch = {
            "OAUTH-REDIRECT-TRAVERSAL": self.probes.test_redirect_traversal,
            "OAUTH-CODE-REPLAY": self.probes.test_code_replay,
            "OAUTH-PKCE-DOWNGRADE": self.probes.test_pkce_downgrade,
            "OAUTH-SCOPE-ESCALATION": self.probes.test_scope_escalation,
            "OAUTH-STATE-CSRF": self.probes.test_state_csrf,
        }
        # Severity weights for adaptive prioritization
        self.severity_weights = {
            "CRITICAL": 100,
            "HIGH": 75,
            "MEDIUM": 50,
            "LOW": 25,
        }
        self.attack_history: List[Dict[str, Any]] = []
        self.last_decision_telemetry: Optional[Dict[str, Any]] = None

    def plan_next_attack(self, state: AegisState) -> Optional[str]:
        """
        Adaptive Attack Planner:
        Instead of a naive FIFO queue, dynamically ranks candidates by:
        1. Threat severity (CRITICAL before HIGH).
        2. Endpoint correlation: if /token had a flaw, prioritize other /token vectors (+20 boost).
        3. Exclusion of already remediated vectors.
        Records structured decision telemetry for monitoring and auditability.
        """
        candidates = [v for v in state.pending_vectors if v not in state.remediated_vectors]
        if not candidates:
            self.last_decision_telemetry = None
            return None

        candidate_scores: Dict[str, Dict[str, Any]] = {}
        last_success = next((h for h in reversed(self.attack_history) if h.get("succeeded")), None)
        last_endpoint = last_success.get("target_endpoint") if last_success else None

        for v in candidates:
            meta = OAUTH_THREAT_MATRIX.get(v, {})
            base_score = self.severity_weights.get(meta.get("severity", "MEDIUM"), 50)
            boost = 0
            boost_reason = "Base severity score"

            if last_endpoint:
                if last_endpoint == "/token" and v in ["OAUTH-PKCE-DOWNGRADE", "OAUTH-CODE-REPLAY", "OAUTH-SCOPE-ESCALATION"]:
                    boost = 20
                    boost_reason = f"Endpoint correlation boost (+20) from preceding {last_endpoint} compromise"
                elif last_endpoint == "/authorize" and v in ["OAUTH-REDIRECT-TRAVERSAL", "OAUTH-STATE-CSRF"]:
                    boost = 20
                    boost_reason = f"Endpoint correlation boost (+20) from preceding {last_endpoint} compromise"

            candidate_scores[v] = {
                "base_score": base_score,
                "boost": boost,
                "total_score": base_score + boost,
                "boost_reason": boost_reason,
                "endpoint": meta.get("target_endpoint", "unknown"),
                "severity": meta.get("severity", "MEDIUM"),
            }

        # Sort candidates descending by total_score
        sorted_candidates = sorted(candidates, key=lambda v: candidate_scores[v]["total_score"], reverse=True)
        selected_vector = sorted_candidates[0]
        selected_info = candidate_scores[selected_vector]

        self.last_decision_telemetry = {
            "selected_vector": selected_vector,
            "total_score": selected_info["total_score"],
            "base_score": selected_info["base_score"],
            "boost": selected_info["boost"],
            "boost_reason": selected_info["boost_reason"],
            "candidate_ranking": [
                {
                    "vector_id": c,
                    "total_score": candidate_scores[c]["total_score"],
                    "base_score": candidate_scores[c]["base_score"],
                    "boost": candidate_scores[c]["boost"],
                    "reason": candidate_scores[c]["boost_reason"],
                }
                for c in sorted_candidates
            ],
            "last_endpoint_exploited": last_endpoint,
        }

        return selected_vector

    def execute_vector(self, vector_id: str, client: httpx.Client) -> Optional[VulnerabilityProof]:
        """Executes a specific attack probe against the target service and records telemetry."""
        probe_fn = self.probe_dispatch.get(vector_id)
        if not probe_fn:
            raise ValueError(f"Unknown attack vector: {vector_id}")

        proof = probe_fn(client, self.ctx)

        # Update telemetry history
        self.attack_history.append({
            "vector_id": vector_id,
            "succeeded": proof is not None,
            "target_endpoint": proof.target_endpoint if proof else None,
            "mutations_tested": proof.mutations_tested if proof else 1,
            "mutations_succeeded": proof.mutations_succeeded if proof else 0,
        })

        return proof
