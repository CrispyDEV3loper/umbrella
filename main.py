"""
Aegis CLI Runner: 2-Sided AI OAuth & 3rd-Party Integration Testing & Repair System.
Demonstrates the iterative co-evolution loop:
Red Team Attacks -> Blue Team Repairs -> Dual-Gate Adjudicates -> Verifies Convergence.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aegis.core.orchestrator import AegisOrchestrator
from aegis.core.config import OAUTH_THREAT_MATRIX


def print_banner():
    banner = r"""
================================================================================
   ____   ___            _   _          _             _     
  / __ \ / _ \  __ _ _ _| |_| |_       /_\  ___  __ _(_)___ 
 / / _` | (_) |/ _` | ' \  _| ' \     / _ \/ -_)/ _` | (_-< 
 \ \__,_|\___/ \__,_|_||_\__|_||_|   /_/ \_\___|\__, |_/__/ 
  \____/                                         |___/      
  Adversarial 2-Sided AI OAuth & 3rd-Party Testing & Repair Framework
================================================================================
    """
    print(banner)


def handle_event(event_type: str, data: dict):
    """Formats and prints real-time events during the adversarial cycle."""
    if event_type == "SESSION_START":
        print(f"\n[+] Starting Adversarial Hardening Session.")
        print(f"[+] Loaded Threat Matrix ({len(data['vectors'])} vectors queued):")
        for v in data["vectors"]:
            info = OAUTH_THREAT_MATRIX.get(v, {})
            print(f"    - [{v}] {info.get('name', '')} (Severity: {info.get('severity', 'UNKNOWN')})")
        print("-" * 80)

    elif event_type == "ROUND_START":
        print(f"\n>>> ROUND {data['round']}: Testing Vector [{data['vector_id']}]")
        info = OAUTH_THREAT_MATRIX.get(data['vector_id'], {})
        print(f"    Description: {info.get('description', '')}")

    elif event_type == "VECTOR_SECURE":
        print(f"    [*] Target app is already resilient against [{data['vector_id']}]. No patch required.")

    elif event_type == "VULNERABILITY_FOUND":
        proof = data["proof"]
        print(f"    [!] VULNERABILITY CONFIRMED by Red Agent!")
        print(f"        Endpoint: {proof.target_endpoint}")
        print(f"        PoC Summary: {proof.poc_summary}")

    elif event_type == "REPAIR_ATTEMPT":
        print(f"    [*] Blue Agent (SWE-agent ACI) initiating repair attempt #{data['attempt']}...")

    elif event_type == "PATCH_APPLIED":
        patch = data["patch"]
        print(f"    [+] Patch Generated & Applied to {patch.target_file}:")
        print(f"        Rationale: {patch.explanation}")
        print(f"        Lines Changed: {patch.lines_changed}")

    elif event_type == "DUAL_GATE_EVALUATED":
        res = data["result"]
        sec_status = "PASS" if res.security_check_passed else "FAIL"
        func_status = "PASS" if res.golden_path_passed else "FAIL"
        print(f"    [?] Dual-Gate Evaluation:")
        print(f"        1. Security Check (Exploit Blocked): [{sec_status}] {res.exploit_output}")
        print(f"        2. Functional Check (Golden Path):   [{func_status}] {res.golden_path_output}")

    elif event_type == "VECTOR_RESOLVED":
        print(f"    [SUCCESS] Vector [{data['vector_id']}] successfully hardened and verified!")

    elif event_type == "PATCH_REJECTED":
        print(f"    [REJECTED] Patch caused regression or failed to stop exploit. Rolled back.")

    elif event_type == "SESSION_COMPLETE":
        state = data["state"]
        print("\n" + "=" * 80)
        print("ADVERSARIAL HARDENING COMPLETE")
        print("=" * 80)
        print(f"Total Rounds Run:      {state.total_rounds}")
        print(f"Vectors Remediated:    {len(state.remediated_vectors)} / {len(state.active_vector_ids)}")
        print(f"System State:          {'CONVERGED & SOLIDLY VERIFIED' if state.is_converged else 'INCOMPLETE'}")
        print("\nSummary of Round Results:")
        for r in state.history:
            patch_info = f"(Changed {r.patch_applied.lines_changed} lines)" if r.patch_applied else ""
            print(f"  - [{r.vector_id}] -> Status: {r.status} {patch_info}")
        print("=" * 80 + "\n")


def main():
    print_banner()
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    orchestrator = AegisOrchestrator(workspace_root=workspace_dir, on_event=handle_event)
    orchestrator.run_all(max_rounds=10)


if __name__ == "__main__":
    main()
