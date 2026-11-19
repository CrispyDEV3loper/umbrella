# OAuth-Aegis: 2-Sided AI OAuth & 3rd-Party Integration Testing & Repair Framework

A co-evolutionary adversarial security system that combines **SWE-agent**, **OAuthVulnerabilityScanner**, and **LangGraph** concepts into an iterative attack, patch, and functional verification loop.

---

## The Concept

Standard penetration testing tools only find vulnerabilities; developers still have to manually patch them and hope they haven't broken existing user authentication. **OAuth-Aegis** bridges this gap:
1. **Red Side (Attacker):** Executes protocol-level OAuth 2.0 / OIDC attack probes (PKCE downgrades, redirect URI traversal, state CSRF omissions, authorization code replaying, scope escalations).
2. **Blue Side (Patcher):** Uses an Agent-Computer Interface (ACI modeled on SWE-agent) to inspect the codebase, locate the vulnerability, and generate minimal surgical patches.
3. **Dual-Gate Evaluator (Judge):** Rigorously checks that:
   - **Gate 1 (Security):** The exploit is completely blocked and rejected.
   - **Gate 2 (Functionality):** All standard "Golden Path" OAuth user journeys (PKCE exchange, token issuance, userinfo queries) pass 100% without regression.
4. **The Loop:** Repeats iteratively across all vectors in the threat matrix until the system reaches verified convergence.

---

## Architecture & Combined Components

```
                              ┌──────────────────────────────────────────────┐
                              │               LangGraph State                │
                              └──────────────────────┬───────────────────────┘
                                                     │
                                                     ▼
     ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
     │ 1. Red Agent (OAuthVulnerabilityScanner Probes)                                                  │
     │    - OAUTH-PKCE-DOWNGRADE       (RFC 7636 bypass)                                                │
     │    - OAUTH-REDIRECT-TRAVERSAL   (RFC 6749 Section 3.1.2 path traversal)                          │
     │    - OAUTH-STATE-CSRF           (RFC 6749 Section 10.12 omission)                                │
     │    - OAUTH-CODE-REPLAY          (RFC 6749 Section 4.1.2 multi-redemption)                        │
     │    - OAUTH-SCOPE-ESCALATION     (RFC 6749 Section 3.3 unauthorized scope injection)              │
     └───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                     │
                                                     ▼ (Exploit Confirmed)
     ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
     │ 2. Blue Agent (SWE-agent ACI & Program Repair)                                                   │
     │    - Localizes fault in target server routes                                                     │
     │    - Generates minimal surgical RFC-compliant code patch                                         │
     │    - Applies diff via Agent-Computer Interface (with automatic rollback support)                 │
     └───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                     │
                                                     ▼
     ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
     │ 3. Dual-Gate Evaluator                                                                           │
     │    ├─ Check 1: Re-run Exploit Trigger ──────────► Must be BLOCKED & REJECTED                     │
     │    └─ Check 2: Run Golden Path Contract Suite ─► Must PASS 100% (No regressions)                │
     └───────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                     │
                                                     ▼
                                      Both Passed? ──► Commit & Next Round
```

---

## Directory Structure

```text
aegis/
├── core/
│   ├── state.py              # Pydantic state schemas & vulnerability proofs
│   ├── config.py             # OAuth threat matrix & operational parameters
│   └── orchestrator.py       # Multi-round cyclic game loop controller
├── red/
│   ├── probes.py             # Active protocol probes from OAuthVulnerabilityScanner
│   └── agent.py              # Red Team strategy planner
├── blue/
│   ├── aci.py                # SWE-agent inspired Agent-Computer Interface
│   └── agent.py              # Blue Team patch generator and applicator
├── evaluator/
│   ├── golden_path.py        # Functional contract test suite (happy path)
│   └── dual_gate.py          # Dual-Gate adjudication engine
└── testbed/
    └── app.py                # Realistic FastAPI OAuth 2.0 Authorization Server
```

---

## Quickstart & Running the System

### 1. Run the Full Adversarial CLI
```bash
python main.py
```

### 2. Run the Automated Test Suite
```bash
pytest tests/test_aegis.py -v
```
