# Umbrella: Adversarial 2-Sided AI OAuth & 3rd-Party Integration Testing & Repair Framework

An autonomous, co-evolutionary adversarial security system uniting adaptive protocol mutation fuzzing, AST-guided program repair, and a multi-tier dual-gate adjudication loop.

---

## 1. System Architecture

Umbrella models automated protocol hardening as a closed-loop adversarial game between an offensive strategist, a defensive program repair agent, and a multi-tier verification oracle:

```
                              ┌──────────────────────────────────────────────┐
                              │            Adversarial State Graph           │
                              └──────────────────────┬───────────────────────┘
                                                     │
                                                     ▼
     ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
     │ 1. Red Agent (Adaptive Planner & Parameter Mutation Fuzzing)                                    │
     │    - Dynamic vector scoring based on severity and target response telemetry                     │
     │    - Multi-variant mutation engine (traversal encoding, delimiter injection, downgrade probes) │
     │    - Generates actionable VulnerabilityProof with PoC+ mutation statistics                      │
     └───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                     │
                                                     ▼ (Vulnerability Confirmed)
     ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
     │ 2. Blue Agent (AST-Guided Localization & Program Repair)                                        │
     │    - Parses target repository AST to dynamically locate endpoint route handlers                 │
     │    - Synthesizes surgical RFC-compliant remediation blocks tailored to function signatures      │
     │    - Gate 0: Enforces AST syntax validation prior to disk writes, with atomic rollback         │
     └───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                     │
                                                     ▼
     ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
     │ 3. Dual-Gate Evaluator (PoC+ Mutation & Regression Verification)                                 │
     │    ├─ Gate 1: Security PoC+ Verification ───────► 100% of mutation bypass variants must FAIL     │
     │    └─ Gate 2: Functional Contract Suite ────────► 100% of standard OAuth happy paths must PASS   │
     └───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                     │
                                      Both Passed? ──► Commit & Next Round
```

---

## 2. Directory Structure

```text
aegis/
├── core/
│   ├── state.py              # Pydantic schemas (VulnerabilityProof, DualGateResult, AegisState)
│   ├── config.py             # OAuth threat matrix & operational parameters
│   └── orchestrator.py       # Closed-loop cyclic state machine with sound convergence
├── red/
│   ├── mutator.py            # Property-based parameter mutation engine (encoding, pollution, edge cases)
│   ├── probes.py             # Active protocol security probes across mutation matrices
│   └── agent.py              # Adaptive attack planner with response telemetry scoring
├── blue/
│   ├── aci.py                # Agent-Computer Interface: path containment, AST inspection & syntax gates
│   └── agent.py              # AST-guided fault localization and context-aware patch generator
├── evaluator/
│   ├── golden_path.py        # Functional contract test suite (protects legitimate authentication)
│   └── dual_gate.py          # Dual-Gate adjudication engine (PoC+ mutations + Golden Path)
└── testbed/
    └── app.py                # Realistic FastAPI OAuth 2.0 Authorization & Resource Server
```

---

## 3. Threat Matrix & Mutation Vectors

| Vector ID | Attack Category | RFC Specification | Mutation Vectors Covered |
| :--- | :--- | :--- | :--- |
| `OAUTH-REDIRECT-TRAVERSAL` | Redirect Manipulation | RFC 6749 §3.1.2 & RFC 6819 | Plain `/../../`, URL-encoded `%2e%2e/`, double-encoded `%252e%252e/`, subdomain confusion |
| `OAUTH-CODE-REPLAY` | Code Replay | RFC 6749 §4.1.2 | Sequential reuse, token multi-redemption |
| `OAUTH-PKCE-DOWNGRADE` | PKCE Downgrade | RFC 7636 §4.4.1 | Missing verifier, empty string verifier, plain method downgrade |
| `OAUTH-SCOPE-ESCALATION` | Privilege Escalation | RFC 6749 §3.3 | Space/comma delimiters, wildcard `*`, admin role injection |
| `OAUTH-STATE-CSRF` | Login CSRF | RFC 6749 §10.12 | Missing state, zero-entropy static state, whitespace tampering |

---

## 4. Empirical Evaluation & Ablation Study

Umbrella includes an automated ablation benchmark runner (`benchmark_runner.py`) evaluating 4 configurations:
* **Config A:** Red Agent Only (Discovery Baseline)
* **Config B:** Red + Blue (Without Dual-Gate Verification)
* **Config C:** Red + Blue + Dual-Gate (Static Single-Payload Baseline)
* **Config D:** Full Adaptive Umbrella (Adaptive Red Mutation + AST Blue + PoC+ Dual-Gate)

```text
Configuration              | Detection Rate   | PoC+ Mutation Bypasses  | Patches Applied   | Regressions   | Re-Exploit Rate   | Sound Convergence
---------------------------+------------------+-------------------------+-------------------+---------------+-------------------+------------------
Config A (Red Only)        | 0/5              | 0/0                     | 0 (N/A)           | 0%            | 100% (Unremediated)| NO (0%)
Config B (No Dual-Gate)    | 5/5              | 20% (Unchecked)         | 5                 | 40% (Failures)| 60% (Bypasses)    | NO (Regressions)
Config C (Static Dual-Gate)| 5/5              | 40% (Single Payload)    | 5                 | 0%            | 40% (Leaks)       | PARTIAL (60%)
Config D (Full Adaptive)   | 5/5              | 100% (PoC+ Validated)   | 5                 | 0% (Protected)| 0% (Neutralized)  | YES (100%)
```

---

## 5. Quickstart

### Run the Interactive Adversarial Hardening Loop
```bash
python main.py
```

### Run the Empirical Ablation Experiment Benchmark
```bash
python benchmark_runner.py
```

### Run the Automated Unit and Integration Test Suite
```bash
pytest tests/ -v
```
