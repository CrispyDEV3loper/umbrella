"""
Automated Pytest Suite for Aegis.
Validates the Red Team probes, Blue Team ACI, Golden Path suite,
Dual-Gate evaluation, and full orchestrator convergence.
"""

import os
import sys
import shutil
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis.core.orchestrator import AegisOrchestrator
from aegis.blue.aci import AgentComputerInterface
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
    """Tests SWE-agent inspired ACI primitives for safe code editing and rollback."""
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


def test_full_orchestration_cycle(tmp_path):
    """Executes the full adversarial attack -> patch -> dual-gate loop end-to-end."""
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    orchestrator = AegisOrchestrator(workspace_root=workspace_dir)

    final_state = orchestrator.run_all(max_rounds=10)

    # Assert that all attack vectors converged to remediated status
    assert final_state.is_converged is True
    assert len(final_state.remediated_vectors) == len(final_state.active_vector_ids)

    # Assert that all round results achieved clean verification
    for round_res in final_state.history:
        assert round_res.status in ("PATCHED_AND_VERIFIED", "BLOCKED_ORIGINALLY")
        if round_res.gate_result is not None:
            assert round_res.gate_result.fully_passed is True
