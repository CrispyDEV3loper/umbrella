"""
Umbrella Trajectory Tracer & Audit Logger.
Captures fine-grained, structured telemetry of every agent thought, decision score,
AST mutation fuzzer payload, code patch diff, and Dual-Gate verification outcome.
Inspired by SWE-agent .traj traces, PentestGPT session logs, and Vul4Py oracle telemetry.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from aegis.core.state import AegisState, RoundHistory, VulnerabilityProof, PatchResult, DualGateResult
from aegis.core.config import OAUTH_THREAT_MATRIX


class TrajectoryStep(BaseModel):
    step_id: int
    round_number: int
    timestamp: str
    event_type: str
    vector_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class SessionTrajectory(BaseModel):
    session_id: str
    started_at: str
    completed_at: Optional[str] = None
    workspace_root: str
    host_metadata: Dict[str, Any] = Field(default_factory=dict)
    initial_vectors: List[str] = Field(default_factory=list)
    steps: List[TrajectoryStep] = Field(default_factory=list)
    rounds: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class TrajectoryTracer:
    """Records real-time execution steps and writes an audit-grade trajectory JSON."""

    def __init__(self, workspace_root: str, trajectory_path: Optional[str] = None):
        self.workspace_root = workspace_root
        self.trajectory_path = trajectory_path or os.path.join(workspace_root, "umbrella_trajectory.json")
        self.session_id = f"umbrella-{int(time.time())}"
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.step_counter = 0

        self.trajectory = SessionTrajectory(
            session_id=self.session_id,
            started_at=self.started_at,
            workspace_root=self.workspace_root,
            host_metadata={},
            initial_vectors=[],
            steps=[],
            rounds=[],
            summary={},
        )
        self._current_round_data: Dict[str, Any] = {}

    def log_event(self, event_type: str, data: Dict[str, Any], round_number: int = 0, vector_id: Optional[str] = None):
        """Logs an event step into the sequential trajectory."""
        self.step_counter += 1
        now_str = datetime.now(timezone.utc).isoformat()

        # Clean non-serializable objects
        clean_data = self._clean_data(data)

        step = TrajectoryStep(
            step_id=self.step_counter,
            round_number=round_number,
            timestamp=now_str,
            event_type=event_type,
            vector_id=vector_id,
            data=clean_data,
        )
        self.trajectory.steps.append(step)

        # Process round aggregations
        if event_type == "SESSION_START":
            self.trajectory.initial_vectors = data.get("vectors", [])

        elif event_type == "ROUND_START":
            self._current_round_data = {
                "round_number": data.get("round", round_number),
                "vector_id": data.get("vector_id", vector_id),
                "timestamp": now_str,
                "threat_info": OAUTH_THREAT_MATRIX.get(data.get("vector_id", vector_id), {}),
                "adaptive_decision": self._clean_data(data.get("decision", {})),
                "vulnerability": None,
                "patch": None,
                "gate_result": None,
                "status": "IN_PROGRESS",
            }

        elif event_type == "VULNERABILITY_FOUND":
            proof = data.get("proof")
            if proof and hasattr(proof, "model_dump"):
                proof_dict = proof.model_dump()
            elif isinstance(proof, dict):
                proof_dict = proof
            else:
                proof_dict = str(proof)
            self._current_round_data["vulnerability"] = proof_dict

        elif event_type == "PATCH_APPLIED":
            patch = data.get("patch")
            if patch and hasattr(patch, "model_dump"):
                patch_dict = patch.model_dump()
            elif isinstance(patch, dict):
                patch_dict = patch
            else:
                patch_dict = str(patch)
            self._current_round_data["patch"] = patch_dict

        elif event_type == "DUAL_GATE_EVALUATED":
            res = data.get("result")
            if res and hasattr(res, "model_dump"):
                gate_dict = res.model_dump()
            elif isinstance(res, dict):
                gate_dict = res
            else:
                gate_dict = str(res)
            self._current_round_data["gate_result"] = gate_dict

        elif event_type == "VECTOR_RESOLVED":
            self._current_round_data["status"] = "PATCHED_AND_VERIFIED"
            self.trajectory.rounds.append(dict(self._current_round_data))
            self._current_round_data = {}

        elif event_type == "VECTOR_SECURE":
            self._current_round_data["status"] = "BLOCKED_ORIGINALLY"
            self.trajectory.rounds.append(dict(self._current_round_data))
            self._current_round_data = {}

        elif event_type == "VECTOR_UNRESOLVED":
            self._current_round_data["status"] = "MAX_ATTEMPTS_EXCEEDED"
            self.trajectory.rounds.append(dict(self._current_round_data))
            self._current_round_data = {}

        elif event_type == "SESSION_COMPLETE":
            state: Optional[AegisState] = data.get("state")
            self.trajectory.completed_at = now_str
            self._compute_summary(state)
            self.save()

    def _compute_summary(self, state: Optional[AegisState]):
        """Calculates final aggregate metrics."""
        total_rounds = len(self.trajectory.rounds)
        total_mutations_tested = 0
        total_mutations_blocked = 0
        patches_applied = 0

        for r in self.trajectory.rounds:
            if r.get("patch"):
                patches_applied += 1
            gate = r.get("gate_result")
            if isinstance(gate, dict):
                total_mutations_tested += gate.get("mutations_tested", 0)
                total_mutations_blocked += gate.get("mutations_blocked", 0)

        remediated_count = len(state.remediated_vectors) if state else 0
        active_count = len(state.active_vector_ids) if state else len(self.trajectory.initial_vectors)
        converged = state.is_soundly_converged if state else False

        self.trajectory.summary = {
            "total_rounds": total_rounds,
            "active_vectors_count": active_count,
            "remediated_vectors_count": remediated_count,
            "unresolved_vectors_count": len(state.unresolved_vectors) if state else 0,
            "patches_applied": patches_applied,
            "total_mutations_tested": total_mutations_tested,
            "total_mutations_blocked": total_mutations_blocked,
            "soundly_converged": converged,
            "functional_regressions": 0 if converged else 1,
        }

    def _clean_data(self, obj: Any) -> Any:
        """Recursively converts objects to JSON-serializable primitives."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return {k: self._clean_data(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
        if isinstance(obj, dict):
            return {str(k): self._clean_data(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._clean_data(item) for item in obj]
        if isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        return str(obj)

    def save(self, filepath: Optional[str] = None):
        """Writes the trajectory to JSON."""
        target_path = filepath or self.trajectory_path
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.trajectory.model_dump(), f, indent=2)
        return target_path
