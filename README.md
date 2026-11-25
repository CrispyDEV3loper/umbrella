# Umbrella: Adversarial 2-Sided AI OAuth & 3rd-Party Integration Testing & Repair Framework

An autonomous, co-evolutionary adversarial security system uniting adaptive protocol mutation fuzzing, AST-guided program repair, a multi-tier dual-gate adjudication loop, and publication-grade observability.

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
     │    - Records decision telemetry: candidate ranking, base scores, and endpoint affinity boosts   │
     └───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                     │
                                                     ▼ (Vulnerability Confirmed)
     ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
     │ 2. Blue Agent (AST-Guided Localization & Program Repair)                                        │
     │    - Parses target repository AST to dynamically locate endpoint route handlers                 │
     │    - Synthesizes surgical RFC-compliant remediation blocks tailored to function signatures      │
     │    - Gate 0: Enforces AST syntax validation prior to disk writes, with atomic rollback         │
     │    - Generates standard unified diffs for transparent code review                                │
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
│   ├── doctor.py             # Pre-flight environment diagnostics & AST route discovery
│   └── orchestrator.py       # Closed-loop cyclic state machine with sound convergence
├── red/
│   ├── mutator.py            # Property-based parameter mutation engine (encoding, pollution, edge cases)
│   ├── probes.py             # Active protocol security probes across mutation matrices
│   └── agent.py              # Adaptive attack planner with response telemetry scoring
├── blue/
│   ├── aci.py                # Agent-Computer Interface: path containment, AST inspection & syntax gates
│   └── agent.py              # AST-guided fault localization and dynamic patch generator
├── evaluator/
│   ├── golden_path.py        # Functional contract test suite (protects legitimate authentication)
│   └── dual_gate.py          # Dual-Gate adjudication engine (PoC+ mutations + Golden Path)
├── monitor/
│   ├── tracer.py             # SWE-agent style structured trajectory tracer & JSON logger
│   └── dashboard.py          # Interactive HTML visual dashboard & FastAPI monitoring server
└── testbed/
    ├── app.py                # Active target FastAPI OAuth 2.0 Authorization & Resource Server
    └── fixtures/             # Immutable ground-truth vulnerable and hardened fixtures
```

---

## 3. Threat Matrix & Mutation Vectors

| Vector ID | Attack Category | RFC Specification | Mutation Vectors Covered |
| :--- | :--- | :--- | :--- |
| `OAUTH-REDIRECT-TRAVERSAL` | Redirect Manipulation | RFC 6749 §3.1.2 & RFC 6819 | Plain `/../../`, URL-encoded `%2e%2e/`, double-encoded `%252e%252e/`, subdomain confusion, parameter pollution |
| `OAUTH-CODE-REPLAY` | Code Replay | RFC 6749 §4.1.2 | Sequential reuse, token multi-redemption |
| `OAUTH-PKCE-DOWNGRADE` | PKCE Downgrade | RFC 7636 §4.2 & §4.4.1 | Missing verifier, empty string verifier, plain method downgrade (RFC 7636 §4.2 enforcement) |
| `OAUTH-SCOPE-ESCALATION` | Privilege Escalation | RFC 6749 §3.3 | Space/comma delimiters, wildcard `*`, admin role injection |
| `OAUTH-STATE-CSRF` | Login CSRF | RFC 6749 §10.12 | Missing state, zero-entropy static state, whitespace tampering |

---

## 4. Environment Requirements & Diagnostics

### System & Target Requirements
* **Python Runtime:** Python 3.10+ (tested on Python 3.11 and 3.12).
* **Operating System:** Cross-platform (Linux, macOS, Windows).
* **Target Application Stack:** Python web backends (FastAPI, Starlette, Flask, ASGI/WSGI) implementing OAuth 2.0 / OpenID Connect authorization and token grant endpoints (`/authorize`, `/token`, `/userinfo`).
* **Hard Operational Rules:**
  1. **AST-Parseable Codebase:** The target source files must parse cleanly into Python AST without syntax errors.
  2. **Filesystem Permissions:** The user must execute Umbrella with read/write permissions on the workspace to allow the ACI to inspect, snapshot, patch, and rollback files.
  3. **Isolation Best Practice:** **Never execute Umbrella directly against production environments or live customer databases.** Run against an isolated git worktree, ephemeral staging container, or local testbed clone.

### Pre-Flight Diagnostic Check
Umbrella includes an automated **Environment Doctor** (`aegis.core.doctor`) inspired by developer diagnostic tools. It verifies Python runtime version, filesystem write permissions, realpath symlink containment, target code AST syntax, discovers all OAuth route handlers, and tests initial functional baseline health:

```bash
python main.py --doctor
```

---

## 5. User Monitoring & Observability

Umbrella provides comprehensive visibility into what the autonomous agents are doing to the environment:

### 1. Interactive Visual Dashboard (`umbrella_dashboard.html`)
After running Umbrella, open `umbrella_dashboard.html` in any browser or launch the live server:
```bash
python main.py --serve --port 8080
```
The dashboard features 5 interactive tabs:
* **Adaptive Decision Graph:** Visualizes how Red adapts its strategy, displaying candidate priority rankings, base severity scores, and dynamic endpoint correlation boosts (`+20` priority bonus when related endpoints are compromised).
* **AST Code Patches & Diffs:** Syntax-highlighted unified diffs showing exact code additions and deletions, target handler functions, and Gate 0 AST validation status.
* **PoC+ & Dual-Gate Matrix:** Live pass/fail indicators across all 17 mutation variants and Golden Path functional test suites.
* **Environment & Pre-Flight:** Host runtime specs, OS metadata, and discovered AST route handlers.
* **Trajectory JSON & Audit Trail:** Downloadable raw execution trace (`umbrella_trajectory.json`).

### 2. SWE-agent Style Trajectory Trace (`umbrella_trajectory.json`)
Every step, decision score, mutation fuzzer payload, code diff, and gate result is recorded in a machine-readable, audit-grade JSON trajectory log.

---

## 6. Quickstart Commands

```bash
# 1. Run Pre-Flight Environment Diagnostic
python main.py --doctor

# 2. Run the Full Adversarial Hardening Loop
python main.py

# 3. Launch the Interactive Monitoring Dashboard
python main.py --serve

# 4. Run the Empirical Ablation Benchmark (4 Baselines)
python benchmark_runner.py

# 5. Run the Automated Unit and Integration Test Suite (9 Tests)
pytest tests/ -v
```
