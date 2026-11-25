"""
Aegis Core Orchestrator.
Manages the cyclic state machine between Red Agent (Adaptive Planner),
Blue Agent (AST-Guided Patcher), and the Dual-Gate Evaluator until sound convergence.
"""

import os
import importlib
from typing import Optional, Callable, Any
from fastapi.testclient import TestClient

from aegis.core.state import AegisState, RoundHistory, VulnerabilityProof
from aegis.core.config import DEFAULT_VECTORS, MAX_REPAIR_ATTEMPTS_PER_VECTOR
from aegis.red.agent import RedAgent
from aegis.blue.aci import AgentComputerInterface
from aegis.blue.agent import BlueAgent
from aegis.evaluator.dual_gate import DualGateEvaluator
from aegis.core.target import TargetProfile
import aegis.testbed.app as testbed_app


class AegisOrchestrator:
    """Coordinates iterative attack, remediation, and dual-gate evaluation.

    ``profile`` (a TargetProfile) points the whole loop at a custom bring-your-own-app
    target. When ``None`` the bundled testbed app is used (original behavior).
    """

    def __init__(self, workspace_root: str, on_event: Optional[Callable[[str, Any], None]] = None,
                 profile: Optional[TargetProfile] = None):
        self.workspace_root = workspace_root
        self.on_event = on_event or (lambda event, data: None)
        self.base_url = "http://testserver"
        self.profile = profile

        # Bind the target module, its FastAPI instance attribute, and the patchable file.
        if profile is not None:
            self.target_module = profile.app_module
            self.app_attr = profile.app_attr
            self.target_file = os.path.basename(profile.path)
            # The Blue agent's ACI must be rooted at the target's own directory so
            # containment still holds while patching the user's file in place.
            self.aci = AgentComputerInterface(os.path.dirname(os.path.abspath(profile.path)))
        else:
            self.target_module = testbed_app
            self.app_attr = "app"
            self.target_file = "aegis/testbed/app.py"
            self.aci = AgentComputerInterface(workspace_root)

        # Capture the target module's spec up front: importlib.reload() clobbers
        # module.__spec__ to None when the synthetic BYO name is unresolvable,
        # so a per-call read of __spec__ silently skips the re-exec fallback.
        self._target_spec = getattr(self.target_module, "__spec__", None)

        # Initialize agents
        self.red_agent = RedAgent(self.base_url, profile)
        self.blue_agent = BlueAgent(self.aci, target_file=self.target_file)
        self.evaluator = DualGateEvaluator(self.base_url, profile)

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
        """Reloads the target module from disk to reflect patches, returning a TestClient."""
        # Re-exec the target module so on-disk repairs are picked up, then serve it.
        spec = self._target_spec
        if spec is not None:
            try:
                importlib.reload(self.target_module)
            except ImportError:
                # Synthetic BYO module names aren't resolvable by import finders,
                # so fall back to re-exec'ing the on-disk source into the module
                # namespace to rebind its app instance and route handlers.
                with open(spec.origin, "r", encoding="utf-8") as f:
                    code = compile(f.read(), spec.origin, "exec")
                exec(code, self.target_module.__dict__)
        app = getattr(self.target_module, self.app_attr)
        return TestClient(app, base_url=self.base_url)

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
            decision_telemetry = self.red_agent.last_decision_telemetry
            self.state.pending_vectors.remove(vector_id)

            self.on_event("ROUND_START", {"round": round_num, "vector_id": vector_id, "decision": decision_telemetry})

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
                        adaptive_decision=decision_telemetry,
                        proof=None,
                        status="BLOCKED_ORIGINALLY",
                    )
                )
                continue

            # Exploit succeeded -> Vulnerability detected
            self.state.current_proof = proof
            self.on_event("VULNERABILITY_FOUND", {"proof": proof, "decision": decision_telemetry})

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
                            adaptive_decision=decision_telemetry,
                            proof=proof,
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
                        adaptive_decision=decision_telemetry,
                        proof=proof,
                        status="MAX_ATTEMPTS_EXCEEDED",
                    )
                )
                self.on_event("VECTOR_UNRESOLVED", {"vector_id": vector_id})

        # Rigorous Convergence Condition:
        # Must have zero unresolved vectors AND all active vectors must be remediated
        self.state.is_converged = self.state.is_soundly_converged
        self.on_event("SESSION_COMPLETE", {"state": self.state})
        return self.state
