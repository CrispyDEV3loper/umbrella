"""
Runs a target OAuth SaaS application through the full Red/Blue/Dual-Gate
co-evolutionary flow in an isolated sandbox.

The Blue Agent patches the target file in place, so a pristine source is never
modified: the target is cloned into a temporary workspace (or a caller-supplied
sandbox) and ``load_target`` is pointed at that copy. This mirrors how the
ablation benchmark isolates its fixtures.
"""

import os
import sys
import shutil
import tempfile
from typing import Optional, Callable, Any, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aegis.custom_saas import (
    CUSTOM_SAAS_TARGET, CUSTOM_SAAS_CLIENT_ID, CUSTOM_SAAS_REDIRECT_URI, CUSTOM_SAAS_SCOPE,
)
from aegis.core.target import load_target
from aegis.core.doctor import UmbrellaDoctor
from aegis.core.orchestrator import AegisOrchestrator
from aegis.monitor.tracer import TrajectoryTracer


def run_target_flow(
    workspace_root: str,
    target_path: str,
    client_id: str,
    redirect_uri: str,
    scope: Optional[str] = None,
    max_rounds: int = 15,
    on_event: Optional[Callable[[str, Any], None]] = None,
    trajectory_path: Optional[str] = None,
    sandbox_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs the generic adversarial flow against an arbitrary target SaaS module.

    ``target_path`` may be the pristine source; it is always copied into
    ``sandbox_dir`` (or a fresh temp dir) and the flow runs against that copy.
    Returns a dict with the final state, profile, sandbox path, trajectory path,
    and doctor report.
    """
    if sandbox_dir is None:
        sandbox_dir = tempfile.mkdtemp(prefix="umbrella_target_")
    else:
        os.makedirs(sandbox_dir, exist_ok=True)
    target_copy = os.path.join(sandbox_dir, "target_app_under_test.py")
    shutil.copyfile(target_path, target_copy)

    # Intake the sandbox copy: validates routes, baseline flow, patch anchors.
    profile = load_target(
        target_copy,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
    )

    # Pre-flight doctor scoped to the target profile.
    doctor = UmbrellaDoctor(workspace_root=workspace_root, profile=profile)
    doc_report = doctor.diagnose()

    # Trajectory tracer (writes to caller-specified path or the sandbox).
    if trajectory_path is None:
        trajectory_path = os.path.join(sandbox_dir, "target_trajectory.json")
    tracer = TrajectoryTracer(workspace_root=workspace_root, trajectory_path=trajectory_path)
    tracer.trajectory.host_metadata = doc_report.model_dump()

    def _handler(event_type: str, data: Any) -> None:
        payload = data if isinstance(data, dict) else {}
        tracer.log_event(event_type, payload, round_number=payload.get("round", 0), vector_id=payload.get("vector_id"))
        if on_event:
            on_event(event_type, data)

    orchestrator = AegisOrchestrator(workspace_root=workspace_root, on_event=_handler, profile=profile)
    final_state = orchestrator.run_all(max_rounds=max_rounds)

    return {
        "state": final_state,
        "profile": profile,
        "sandbox_dir": sandbox_dir,
        "target_copy": target_copy,
        "trajectory_path": trajectory_path,
        "doctor_report": doc_report,
    }


def run_custom_saas(
    workspace_root: str,
    max_rounds: int = 15,
    on_event: Optional[Callable[[str, Any], None]] = None,
    trajectory_path: Optional[str] = None,
    sandbox_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs the bundled Acme SaaS target through the full flow."""
    return run_target_flow(
        workspace_root=workspace_root,
        target_path=os.path.join(workspace_root, CUSTOM_SAAS_TARGET),
        client_id=CUSTOM_SAAS_CLIENT_ID,
        redirect_uri=CUSTOM_SAAS_REDIRECT_URI,
        scope=CUSTOM_SAAS_SCOPE,
        max_rounds=max_rounds,
        on_event=on_event,
        trajectory_path=trajectory_path,
        sandbox_dir=sandbox_dir,
    )
