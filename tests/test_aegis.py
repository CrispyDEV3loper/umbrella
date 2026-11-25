"""
Automated Pytest Suite for Umbrella.
Validates the Adaptive Red Team mutation probes, Blue Team AST-guided ACI,
path traversal prevention, Golden Path contract suite, and sound convergence.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis.core.orchestrator import AegisOrchestrator
from aegis.blue.aci import AgentComputerInterface
from aegis.red.mutator import OAuthPayloadMutator
from aegis.evaluator.golden_path import GoldenPathSuite
import aegis.testbed.app as testbed_app


@pytest.fixture
def test_client():
    """Provides a TestClient for the target app."""
    return TestClient(testbed_app.app, base_url="http://testserver")


def test_initial_golden_path(test_client):
    """Verifies that the target app initially passes all functional happy-path flows."""
    all_ok, msg = GoldenPathSuite.run_all(test_client, "http://testserver")
    assert all_ok is True, f"Initial Golden Path failed: {msg}"


def test_aci_view_and_replace(tmp_path):
    """Tests ACI primitives for safe code editing and rollback."""
    test_file = tmp_path / "sample.py"
    test_file.write_text("def hello():\n    return 'vulnerable'\n")

    aci = AgentComputerInterface(str(tmp_path))
    content = aci.view_file("sample.py", 1, 2)
    assert "vulnerable" in content

    # Test surgical replacement
    replaced = aci.replace_block("sample.py", "return 'vulnerable'", "return 'hardened'")
    assert replaced is True
    assert "hardened" in test_file.read_text()

    # Test rollback
    rolled_back = aci.rollback("sample.py")
    assert rolled_back is True
    assert "vulnerable" in test_file.read_text()


def test_aci_path_traversal_protection(tmp_path):
    """Verifies that ACI rejects sibling directory path traversal attempts."""
    aci = AgentComputerInterface(str(tmp_path))
    with pytest.raises(PermissionError):
        aci._resolve_path("../outside_workspace_leak.py")


def test_aci_ast_syntax_validation(tmp_path):
    """Verifies that ACI rejects candidate patches with invalid Python syntax."""
    test_file = tmp_path / "syntax_check.py"
    test_file.write_text("def valid_func():\n    return 42\n")

    aci = AgentComputerInterface(str(tmp_path))
    # Candidate replacement has broken syntax
    invalid_patch = "def valid_func(broken syntax here"
    result = aci.replace_block("syntax_check.py", "def valid_func():\n    return 42\n", invalid_patch)
    assert result is False, "ACI should reject invalid Python syntax"
    # Ensure file content was not corrupted
    assert "return 42" in test_file.read_text()


def test_mutation_engine():
    """Verifies that the property-based mutation engine generates multi-variant payloads."""
    # Test Redirect URI mutations
    redirect_mutations = OAuthPayloadMutator.mutate_redirect_uri("https://valid.com/cb")
    assert len(redirect_mutations) >= 4
    types = [m["type"] for m in redirect_mutations]
    assert "PLAIN_TRAVERSAL" in types
    assert "URL_ENCODED_TRAVERSAL" in types
    assert "DOUBLE_ENCODED_TRAVERSAL" in types

    # Test PKCE mutations
    pkce_mutations = OAuthPayloadMutator.mutate_pkce_downgrades("test_verifier_123")
    assert len(pkce_mutations) >= 3

    # Test Scope mutations
    scope_mutations = OAuthPayloadMutator.mutate_scope_escalations("read:profile")
    assert len(scope_mutations) >= 3


def test_full_orchestration_cycle():
    """Executes the full adversarial attack -> patch -> dual-gate loop end-to-end."""
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    orchestrator = AegisOrchestrator(workspace_root=workspace_dir)

    final_state = orchestrator.run_all(max_rounds=15)

    # Assert that all attack vectors converged to remediated status
    assert final_state.is_converged is True
    assert final_state.is_soundly_converged is True
    assert len(final_state.unresolved_vectors) == 0
    assert len(final_state.remediated_vectors) == len(final_state.active_vector_ids)

    # Assert that all round results achieved clean verification
    for round_res in final_state.history:
        assert round_res.status in ("PATCHED_AND_VERIFIED", "BLOCKED_ORIGINALLY")
        if round_res.gate_result is not None:
            assert round_res.gate_result.fully_passed is True


def test_umbrella_doctor():
    """Verifies that the Environment Doctor performs pre-flight checks and route discovery."""
    from aegis.core.doctor import UmbrellaDoctor
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    doctor = UmbrellaDoctor(workspace_root=workspace_dir)
    report = doctor.diagnose()
    assert report.all_passed is True
    assert len(report.discovered_routes) >= 3
    route_paths = [r["route_path"] for r in report.discovered_routes]
    assert "/authorize" in route_paths
    assert "/token" in route_paths


def test_trajectory_tracer(tmp_path):
    """Verifies that the Trajectory Tracer writes structured audit JSON with adaptive decisions."""
    from aegis.monitor.tracer import TrajectoryTracer
    traj_file = tmp_path / "test_traj.json"
    tracer = TrajectoryTracer(workspace_root=str(tmp_path), trajectory_path=str(traj_file))
    
    tracer.log_event("SESSION_START", {"vectors": ["OAUTH-PKCE-DOWNGRADE"]})
    tracer.log_event("ROUND_START", {
        "round": 1,
        "vector_id": "OAUTH-PKCE-DOWNGRADE",
        "decision": {
            "total_score": 95,
            "base_score": 75,
            "boost": 20,
            "boost_reason": "Endpoint correlation boost (+20) from preceding /token compromise",
        }
    })
    tracer.log_event("VECTOR_RESOLVED", {"vector_id": "OAUTH-PKCE-DOWNGRADE"})
    tracer.log_event("SESSION_COMPLETE", {})
    
    assert traj_file.exists()
    import json
    with open(traj_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["steps"]) >= 4
    assert len(data["rounds"]) == 1
    assert data["rounds"][0]["adaptive_decision"]["total_score"] == 95


def test_dashboard_export(tmp_path):
    """Verifies that the standalone HTML dashboard is generated cleanly with all tabs."""
    from aegis.monitor.dashboard import export_dashboard_file
    traj_file = tmp_path / "test_traj.json"
    out_html = tmp_path / "test_dashboard.html"
    traj_file.write_text('{"summary": {"soundly_converged": true}, "rounds": []}')
    
    export_dashboard_file(str(traj_file), str(out_html))
    assert out_html.exists()
    html_text = out_html.read_text(encoding="utf-8")
    assert "Project Umbrella -- Monitoring & Trajectory Inspector" in html_text
    assert "Adaptive Decision Graph" in html_text
    assert "AST Code Patches & Diffs" in html_text
