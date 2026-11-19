"""
Umbrella CLI Runner: Adversarial 2-Sided AI OAuth & 3rd-Party Testing & Repair Framework.
Demonstrates the iterative co-evolution loop:
Adaptive Red Team Attacks & Mutations -> AST Blue Team Repairs -> PoC+ Dual-Gate Adjudication.
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
  Adaptive Mutation Engine | AST Fault Localization | PoC+ Dual-Gate
================================================================================
    """
    print(banner)


def handle_event(event_type: str, data: dict):
    """Formats and prints real-time events during the adversarial cycle."""
    if event_type == "SESSION_START":
        print(f"\n[+] Starting Adaptive Adversarial Hardening Session.")
        print(f"[+] Loaded Threat Matrix ({len(data['vectors'])} vectors queued):")
        for v in data["vectors"]:
            info = OAUTH_THREAT_MATRIX.get(v, {})
            print(f"    - [{v}] {info.get('name', '')} (Severity: {info.get('severity', 'UNKNOWN')})")
        print("-" * 80)

    elif event_type == "ROUND_START":
        print(f"\n>>> ROUND {data['round']}: Adaptive Attack on [{data['vector_id']}]")
        info = OAUTH_THREAT_MATRIX.get(data['vector_id'], {})
        print(f"    Category: {info.get('category', '')} | Severity: {info.get('severity', '')}")
        print(f"    RFC Reference: {info.get('rfc_reference', '')}")

    elif event_type == "VECTOR_SECURE":
        print(f"    [*] Target app is already resilient against [{data['vector_id']}] and all mutation variants.")

    elif event_type == "VULNERABILITY_FOUND":
        proof = data["proof"]
        print(f"    [!] VULNERABILITY CONFIRMED via Property Mutation Fuzzing!")
        print(f"        Endpoint: {proof.target_endpoint}")
        print(f"        Mutation Variations Tested: {proof.mutations_tested} (Bypasses Found: {proof.mutations_succeeded})")
        print(f"        PoC Summary: {proof.poc_summary}")

    elif event_type == "REPAIR_ATTEMPT":
        print(f"    [*] Blue Agent (AST-Guided ACI) initiating repair attempt #{data['attempt']}...")

    elif event_type == "PATCH_APPLIED":
        patch = data["patch"]
        print(f"    [+] AST Patch Generated & Syntactically Validated:")
        print(f"        Target: {patch.target_file} | Lines Changed: {patch.lines_changed} | AST Validated: {patch.ast_validated}")
        print(f"        Rationale: {patch.explanation}")

    elif event_type == "DUAL_GATE_EVALUATED":
        res = data["result"]
        sec_status = "PASS" if res.security_check_passed else "FAIL"
        func_status = "PASS" if res.golden_path_passed else "FAIL"
        print(f"    [?] Dual-Gate Evaluation:")
        print(f"        1. Security Gate (PoC+ Mutations Blocked): [{sec_status}] {res.exploit_output}")
        print(f"           - Mutation Bypasses Neutralized: {res.mutations_blocked}/{res.mutations_tested}")
        print(f"        2. Functional Gate (Golden Path Contract): [{func_status}] {res.golden_path_output}")

    elif event_type == "VECTOR_RESOLVED":
        print(f"    [SUCCESS] Vector [{data['vector_id']}] successfully hardened and verified across all mutations!")

    elif event_type == "PATCH_REJECTED":
        print(f"    [REJECTED] Candidate patch failed Dual-Gate criteria. Rolled back.")

    elif event_type == "SESSION_COMPLETE":
        state = data["state"]
        print("\n" + "=" * 80)
        print("ADVERSARIAL HARDENING COMPLETE")
        print("=" * 80)
        print(f"Total Rounds Run:      {state.total_rounds}")
        print(f"Vectors Remediated:    {len(state.remediated_vectors)} / {len(state.active_vector_ids)}")
        print(f"Unresolved Vectors:    {len(state.unresolved_vectors)}")
        print(f"Sound Convergence:     {'YES (100% SECURE & FUNCTIONAL)' if state.is_soundly_converged else 'NO (INCOMPLETE)'}")
        print("\nSummary of Round Results:")
        for r in state.history:
            patch_info = f"(Changed {r.patch_applied.lines_changed} lines)" if r.patch_applied else ""
            print(f"  - [{r.vector_id}] -> Status: {r.status} {patch_info}")
        print("=" * 80 + "\n")


def main():
    print_banner()
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    orchestrator = AegisOrchestrator(workspace_root=workspace_dir, on_event=handle_event)
    orchestrator.run_all(max_rounds=15)


if __name__ == "__main__":
    main()
