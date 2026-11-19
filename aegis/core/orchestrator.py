"""
Aegis Core Orchestrator.
Manages the cyclic state machine between Red Agent (Adaptive Planner),
Blue Agent (AST-Guided Patcher), and the Dual-Gate Evaluator until sound convergence.
"""

import sys
import importlib
from typing import Optional, List, Callable, Any
from fastapi.testclient import TestClient

from aegis.core.state import AegisState, RoundHistory, VulnerabilityProof
from aegis.core.config import DEFAULT_VECTORS, MAX_REPAIR_ATTEMPTS_PER_VECTOR
from aegis.red.agent import RedAgent
from aegis.blue.aci import AgentComputerInterface
from aegis.blue.agent import BlueAgent
from aegis.evaluator.dual_gate import DualGateEvaluator
import aegis.testbed.app as testbed_app


class AegisOrchestrator:
    """Coordinates iterative attack, remediation, and dual-gate evaluation."""

    def __init__(self, workspace_root: str, on_event: Optional[Callable[[str, Any], None]] = None):
        self.workspace_root = workspace_root
        self.on_event = on_event or (lambda event, data: None)
        self.base_url = "http://testserver"

        # Initialize agents
        self.aci = AgentComputerInterface(workspace_root)
        self.red_agent = RedAgent(self.base_url)
        self.blue_agent = BlueAgent(self.aci)
        self.evaluator = DualGateEvaluator(self.base_url)

        # Initialize State
        self.state = AegisState(
            target_repo_path=workspace_root,
            active_vector_ids=list(DEFAULT_VECTORS),
            pending_vectors=list(DEFAULT_VECTORS),
            remediated_vectors=[],
            unresolved_vectors=[],
            history=[],
        )

    def _get_client(self) -> TestClient:
        """Reloads the target app module to reflect code patches, returning a TestClient."""
        # Cleanly reload target module if it was patched on disk
        if "aegis.testbed.app" in sys.modules:
            importlib.reload(testbed_app)
        return TestClient(testbed_app.app, base_url=self.base_url)

    def run_all(self, max_rounds: int = 15) -> AegisState:
        """Executes the co-evolutionary loop across all attack vectors until convergence."""
        self.on_event("SESSION_START", {"vectors": list(self.state.pending_vectors)})

        round_num = 0
        while self.state.pending_vectors and round_num < max_rounds:
            round_num += 1
            self.state.total_rounds = round_num

            # --- 1. Adaptive Red Attack Planning ---
            vector_id = self.red_agent.plan_next_attack(self.state)
            if not vector_id:
                break
            self.state.pending_vectors.remove(vector_id)

            self.on_event("ROUND_START", {"round": round_num, "vector_id": vector_id})

            # --- 2. Red Agent Execution with Mutation Suite ---
            with self._get_client() as client:
                proof = self.red_agent.execute_vector(vector_id, client)

            if proof is None:
                # Target app was already resilient against this vector and its mutations
                self.on_event("VECTOR_SECURE", {"vector_id": vector_id})
                self.state.remediated_vectors.append(vector_id)
                self.state.history.append(
                    RoundHistory(
                        round_number=round_num,
                        vector_id=vector_id,
                        attack_succeeded=False,
                        remediation_attempted=False,
                        status="BLOCKED_ORIGINALLY",
                    )
                )
                continue

            # Exploit succeeded -> Vulnerability detected
            self.state.current_proof = proof
            self.on_event("VULNERABILITY_FOUND", {"proof": proof})

            # --- 3. Blue Agent AST Remediation Turn ---
            attempts = 0
            vector_resolved = False

            while attempts < MAX_REPAIR_ATTEMPTS_PER_VECTOR and not vector_resolved:
                attempts += 1
                self.on_event("REPAIR_ATTEMPT", {"round": round_num, "attempt": attempts, "vector_id": vector_id})

                patch = self.blue_agent.generate_and_apply_patch(proof)
                if not patch:
                    self.on_event("PATCH_GENERATION_FAILED", {"vector_id": vector_id})
                    break

                self.on_event("PATCH_APPLIED", {"patch": patch})

                # --- 4. Dual-Gate Adjudication (PoC+ Mutations + Golden Path) ---
                with self._get_client() as client:
                    gate_result = self.evaluator.evaluate(vector_id, client)

                self.on_event("DUAL_GATE_EVALUATED", {"result": gate_result})

                if gate_result.fully_passed:
                    vector_resolved = True
                    self.state.remediated_vectors.append(vector_id)
                    self.state.history.append(
                        RoundHistory(
                            round_number=round_num,
                            vector_id=vector_id,
                            attack_succeeded=True,
                            remediation_attempted=True,
                            patch_applied=patch,
                            gate_result=gate_result,
                            status="PATCHED_AND_VERIFIED",
                        )
                    )
                    self.on_event("VECTOR_RESOLVED", {"vector_id": vector_id, "patch": patch})
                else:
                    # Rollback candidate patch to preserve system stability
                    self.blue_agent.rollback_patch()
                    self.on_event("PATCH_REJECTED", {"vector_id": vector_id, "gate_result": gate_result})

            if not vector_resolved:
                # Record unresolved finding
                self.state.unresolved_vectors.append(vector_id)
                self.state.history.append(
                    RoundHistory(
                        round_number=round_num,
                        vector_id=vector_id,
                        attack_succeeded=True,
                        remediation_attempted=True,
                        status="MAX_ATTEMPTS_EXCEEDED",
                    )
                )
                self.on_event("VECTOR_UNRESOLVED", {"vector_id": vector_id})

        # Rigorous Convergence Condition:
        # Must have zero unresolved vectors AND all active vectors must be remediated
        self.state.is_converged = self.state.is_soundly_converged
        self.on_event("SESSION_COMPLETE", {"state": self.state})
        return self.state
