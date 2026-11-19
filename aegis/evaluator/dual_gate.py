"""
Aegis Dual-Gate Evaluator.
The core adjudication engine that evaluates candidate patches against
both security neutralization and functional preservation criteria.
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
        Runs both gates:
        Gate 1: Exploit Verification -> Exploit must be blocked.
        Gate 2: Functional Contract -> All Golden Path flows must pass.
        """
        # --- Gate 1: Security Exploit Verification ---
        re_exploit_proof = self.red_agent.execute_vector(vector_id, client)
        if re_exploit_proof is None:
            security_passed = True
            sec_output = f"Security Gate PASSED: Attack vector {vector_id} successfully neutralized and rejected."
        else:
            security_passed = False
            sec_output = f"Security Gate FAILED: Target remains vulnerable. Exploit still yielded: {re_exploit_proof.poc_summary}"

        # --- Gate 2: Functional Preservation (Golden Path) ---
        func_passed, func_output = GoldenPathSuite.run_all(client, self.base_url)

        return DualGateResult(
            security_check_passed=security_passed,
            golden_path_passed=func_passed,
            exploit_output=sec_output,
            golden_path_output=func_output,
        )
