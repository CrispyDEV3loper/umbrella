"""
Aegis Core State Definitions & Data Models.
Tracks the iterative state between the Red Agent (Attacker),
Blue Agent (Patcher), and Dual-Gate Evaluator.
"""

from typing import TypedDict, List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VulnerabilityProof(BaseModel):
    """Represents a discovered and verified vulnerability."""
    vector_id: str
    category: str
    description: str
    exploit_payload: Dict[str, Any]
    target_endpoint: str
    response_status: int
    response_body: Dict[str, Any]
    poc_summary: str
    mutations_tested: int = 1
    mutations_succeeded: int = 1


class PatchResult(BaseModel):
    """Represents a code remediation proposed by the Blue Agent."""
    vector_id: str
    diff_patch: str
    target_file: str
    explanation: str
    lines_changed: int
    ast_validated: bool = True


class DualGateResult(BaseModel):
    """Result of the Dual-Gate verification."""
    security_check_passed: bool           # Exploit is now blocked (must be True)
    golden_path_passed: bool              # All standard functional flows pass (must be True)
    exploit_output: str
    golden_path_output: str
    mutations_tested: int = 0
    mutations_blocked: int = 0
    code_quality_passed: bool = True

    @property
    def fully_passed(self) -> bool:
        return self.security_check_passed and self.golden_path_passed and self.code_quality_passed


class RoundHistory(BaseModel):
    """Tracks a single round of the Red-Blue adversarial cycle."""
    round_number: int
    vector_id: str
    attack_succeeded: bool
    remediation_attempted: bool
    patch_applied: Optional[PatchResult] = None
    gate_result: Optional[DualGateResult] = None
    status: str  # "BLOCKED_ORIGINALLY", "PATCHED_AND_VERIFIED", "PATCH_FAILED_REGRESSION", "MAX_ATTEMPTS_EXCEEDED"


class AegisState(BaseModel):
    """Global system state passed across the orchestration loop."""
    target_repo_path: str
    active_vector_ids: List[str] = Field(default_factory=list)
    pending_vectors: List[str] = Field(default_factory=list)
    remediated_vectors: List[str] = Field(default_factory=list)
    unresolved_vectors: List[str] = Field(default_factory=list)
    
    current_proof: Optional[VulnerabilityProof] = None
    current_patch: Optional[PatchResult] = None
    current_gate_result: Optional[DualGateResult] = None
    
    history: List[RoundHistory] = Field(default_factory=list)
    is_converged: bool = False
    total_rounds: int = 0

    @property
    def is_soundly_converged(self) -> bool:
        """True only if every vector in active_vector_ids has been verified and remediated with 0 unresolved."""
        return (len(self.unresolved_vectors) == 0) and (len(self.remediated_vectors) == len(self.active_vector_ids))
