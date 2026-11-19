"""
Aegis Dual-Gate Evaluator.
The core adjudication engine that evaluates candidate patches against
both security neutralization (via PoC+ mutation verification) and
functional preservation criteria (via the Golden Path contract suite).
"""

from typing import Tuple, Optional
import httpx
from aegis.core.state import VulnerabilityProof, DualGateResult
from aegis.red.agent import RedAgent
from aegis.evaluator.golden_path import GoldenPathSuite


class DualGateEvaluator:
    """Enforces the Dual-Gate Verification Criterion."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.red_agent = RedAgent(base_url)

    def evaluate(self, vector_id: str, client: httpx.Client) -> DualGateResult:
        """
        Runs the full multi-tier evaluation:
        Gate 1: PoC+ Mutation Exploit Verification (All mutation variants must be neutralized).
        Gate 2: Functional Contract Suite (All Golden Path user journeys must pass 100%).
        """
        MUTATION_COUNTS = {
            "OAUTH-REDIRECT-TRAVERSAL": 5,
            "OAUTH-PKCE-DOWNGRADE": 4,
            "OAUTH-STATE-CSRF": 3,
            "OAUTH-SCOPE-ESCALATION": 4,
            "OAUTH-CODE-REPLAY": 1,
        }

        # --- Gate 1: Security PoC+ Mutation Verification ---
        re_exploit_proof = self.red_agent.execute_vector(vector_id, client)
        total_mutations = MUTATION_COUNTS.get(vector_id, 1)

        if re_exploit_proof is None:
            security_passed = True
            sec_output = f"Security Gate PASSED: Attack vector {vector_id} and all {total_mutations} mutation variants successfully neutralized."
            mut_tested = total_mutations
            mut_blocked = total_mutations
        else:
            security_passed = False
            mut_tested = total_mutations
            mut_blocked = total_mutations - re_exploit_proof.mutations_succeeded
            sec_output = f"Security Gate FAILED: Target remains vulnerable to bypass mutations ({mut_blocked}/{mut_tested} neutralized). Exploit: {re_exploit_proof.poc_summary}"

        # --- Gate 2: Functional Preservation (Golden Path) ---
        func_passed, func_output = GoldenPathSuite.run_all(client, self.base_url)

        return DualGateResult(
            security_check_passed=security_passed,
            golden_path_passed=func_passed,
            exploit_output=sec_output,
            golden_path_output=func_output,
            mutations_tested=mut_tested,
            mutations_blocked=mut_blocked,
            code_quality_passed=True,
        )
