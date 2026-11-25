"""
Umbrella CLI Runner: Adversarial 2-Sided AI OAuth & 3rd-Party Testing & Repair Framework.
Demonstrates the iterative co-evolution loop:
Adaptive Red Team Attacks & Mutations -> AST Blue Team Repairs -> PoC+ Dual-Gate Adjudication.
Equipped with Environment Doctor, SWE-agent Style Trajectory Tracer, and Interactive Web Dashboard.
"""

import os
import sys
import argparse

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aegis.core.orchestrator import AegisOrchestrator
from aegis.core.config import OAUTH_THREAT_MATRIX
from aegis.core.doctor import UmbrellaDoctor
from aegis.monitor.tracer import TrajectoryTracer
from aegis.monitor.dashboard import export_dashboard_file, serve_dashboard


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


def main():
    parser = argparse.ArgumentParser(
        description="Project Umbrella: Adversarial Co-Evolutionary Hardening for Web Identity Protocols"
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Execute pre-flight environment and AST diagnostics without running attack cycles.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Launch the interactive Web Monitoring Dashboard and Trajectory Inspector.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for the monitoring web server (default: 8080).",
    )
    parser.add_argument(
        "--trajectory",
        type=str,
        default="umbrella_trajectory.json",
        help="Destination path for the structured execution trajectory JSON.",
    )
    parser.add_argument(
        "--dashboard",
        type=str,
        default="umbrella_dashboard.html",
        help="Destination path for the standalone HTML monitoring dashboard.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=15,
        help="Maximum co-evolution rounds to execute.",
    )
    parser.add_argument(
        "--custom-saas",
        action="store_true",
        help="Run the bundled Acme SaaS target through the full Red/Blue/Dual-Gate flow (isolated sandbox).",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Bring-your-own-app: path to a FastAPI/Starlette OAuth module to test instead of the bundled testbed.",
    )
    parser.add_argument(
        "--client-id",
        type=str,
        default=None,
        help="Registered client_id of the BYO/custom target application.",
    )
    parser.add_argument(
        "--redirect-uri",
        type=str,
        default=None,
        help="Registered redirect_uri of the BYO/custom target application.",
    )
    parser.add_argument(
        "--scope",
        type=str,
        default=None,
        help="OAuth scope to exercise against the target (optional).",
    )

    args = parser.parse_args()
    workspace_dir = os.path.dirname(os.path.abspath(__file__))

    # Case 1: Environment Doctor Diagnostic Mode
    if args.doctor:
        print_banner()
        doctor = UmbrellaDoctor(workspace_root=workspace_dir)
        doctor.print_report()
        sys.exit(0)

    # Case 2: Web Dashboard Server Mode
    if args.serve:
        print_banner()
        traj_file = os.path.join(workspace_dir, args.trajectory)
        dash_file = os.path.join(workspace_dir, args.dashboard)
        doctor = UmbrellaDoctor(workspace_root=workspace_dir)
        doc_report = doctor.diagnose()
        if not os.path.exists(traj_file):
            print(f"[!] Trajectory file '{args.trajectory}' not found.")
            print("[*] Generating baseline trajectory from recent environment state...")
            export_dashboard_file(traj_file, dash_file)
        serve_dashboard(traj_file, port=args.port, doctor_data=doc_report.model_dump(), workspace_root=workspace_dir)
        sys.exit(0)

    # Case 2b: Custom SaaS flow (bundled Acme or BYO target)
    if args.custom_saas or args.target:
        from aegis.custom_saas.runner import run_target_flow
        from aegis.custom_saas import (
            CUSTOM_SAAS_TARGET, CUSTOM_SAAS_CLIENT_ID, CUSTOM_SAAS_REDIRECT_URI, CUSTOM_SAAS_SCOPE,
        )
        print_banner()
        if args.custom_saas:
            target_path = os.path.join(workspace_dir, CUSTOM_SAAS_TARGET)
            client_id, redirect_uri, scope = CUSTOM_SAAS_CLIENT_ID, CUSTOM_SAAS_REDIRECT_URI, CUSTOM_SAAS_SCOPE
            print("[*] Target: bundled Acme SaaS ->", target_path)
        else:
            target_path = os.path.abspath(args.target)
            client_id = args.client_id or CUSTOM_SAAS_CLIENT_ID
            redirect_uri = args.redirect_uri or CUSTOM_SAAS_REDIRECT_URI
            scope = args.scope or CUSTOM_SAAS_SCOPE
            print(f"[*] BYO target: {target_path}")

        print("[*] Running custom-SaaS Red/Blue/Dual-Gate flow in an isolated sandbox...\n")
        result = run_target_flow(
            workspace_root=workspace_dir,
            target_path=target_path,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            max_rounds=args.max_rounds,
            trajectory_path=os.path.join(workspace_dir, args.trajectory),
        )

        state = result["state"]
        print("=" * 80)
        print(f"Custom SaaS run complete (sandbox: {result['sandbox_dir']})")
        print(f"Total Rounds:      {state.total_rounds}")
        print(f"Vectors Remediated: {len(state.remediated_vectors)} / {len(state.active_vector_ids)}")
        print(f"Sound Convergence: {'YES (100% SECURE & FUNCTIONAL)' if state.is_soundly_converged else 'NO (INCOMPLETE)'}")
        print("=" * 80 + "\n")

        export_dashboard_file(
            trajectory_path=result["trajectory_path"],
            output_html_path=os.path.join(workspace_dir, args.dashboard),
            doctor_data=result["doctor_report"].model_dump(),
        )
        print(f"[+] Trajectory Audit Log:  {result['trajectory_path']}")
        print(f"[+] Visual Dashboard:      {os.path.join(workspace_dir, args.dashboard)}")
        print("[*] Live dashboard + SaaS intake: python main.py --serve")
        sys.exit(0)

    # Case 3: Full Co-Evolutionary Orchestration Run
    print_banner()

    # Pre-Flight Diagnostic Check
    print("[*] Executing Pre-Flight Environment & AST Diagnostics...")
    doctor = UmbrellaDoctor(workspace_root=workspace_dir)
    doc_report = doctor.diagnose()
    if not doc_report.all_passed:
        doctor.print_report(doc_report)
        print("[!] Pre-flight diagnostics failed. Aborting to protect environment.")
        sys.exit(1)
    print("    [+] Environment verified: Python runtime, AST parser, and OAuth routes operational.\n")

    # Initialize Trajectory Tracer
    traj_path = os.path.join(workspace_dir, args.trajectory)
    dash_path = os.path.join(workspace_dir, args.dashboard)
    tracer = TrajectoryTracer(workspace_root=workspace_dir, trajectory_path=traj_path)
    tracer.trajectory.host_metadata = doc_report.host_info

    def handle_event(event_type: str, data: dict):
        """Formats and prints real-time events while logging structured trajectory."""
        round_num = data.get("round", 0)
        vec_id = data.get("vector_id")

        # Record event in structured tracer
        tracer.log_event(event_type, data, round_number=round_num, vector_id=vec_id)

        if event_type == "SESSION_START":
            print(f"[+] Starting Adaptive Adversarial Hardening Session.")
            print(f"[+] Loaded Threat Matrix ({len(data['vectors'])} vectors queued):")
            for v in data["vectors"]:
                info = OAUTH_THREAT_MATRIX.get(v, {})
                print(f"    - [{v}] {info.get('name', '')} (Severity: {info.get('severity', 'UNKNOWN')})")
            print("-" * 80)

        elif event_type == "ROUND_START":
            dec = data.get("decision") or {}
            print(f"\n>>> ROUND {data['round']}: Adaptive Attack on [{data['vector_id']}]")
            info = OAUTH_THREAT_MATRIX.get(data['vector_id'], {})
            print(f"    Category: {info.get('category', '')} | Severity: {info.get('severity', '')}")
            if dec.get("total_score"):
                print(f"    Adaptive Priority Score: {dec.get('total_score')} (Base: {dec.get('base_score')}, Boost: +{dec.get('boost')})")
                print(f"    Selection Rationale: {dec.get('boost_reason')}")

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
            print("=" * 80)

    # Initialize Orchestrator and run co-evolution loop
    orchestrator = AegisOrchestrator(workspace_root=workspace_dir, on_event=handle_event)
    final_state = orchestrator.run_all(max_rounds=args.max_rounds)

    # Export interactive dashboard
    export_dashboard_file(
        trajectory_path=traj_path,
        output_html_path=dash_path,
        doctor_data=doc_report.model_dump(),
    )

    print(f"\n[+] Trajectory Audit Log saved to:  {traj_path}")
    print(f"[+] Interactive Visual Dashboard:   {dash_path}")
    print("[*] To open dashboard in browser, run: python main.py --serve")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
