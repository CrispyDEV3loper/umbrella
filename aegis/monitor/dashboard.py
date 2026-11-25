"""
Umbrella Interactive Visual Dashboard & Inspector.
Generates a standalone, dependency-free interactive HTML/JS application (umbrella_dashboard.html)
and provides an optional live FastAPI web server for real-time monitoring and trajectory inspection.
The live server also exposes a "Run Custom SaaS" intake endpoint so a user can point the
same Red/Blue/Dual-Gate flow at their own (or the bundled Acme) SaaS application and watch
the result render in the same dashboard.
Inspired by SWE-agent Inspector and PentestGPT task visualizers.
"""

import os
import json
import shutil
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from aegis.core.config import OAUTH_THREAT_MATRIX


def generate_dashboard_html(trajectory_data: Dict[str, Any], doctor_data: Optional[Dict[str, Any]] = None) -> str:
    """Generates an all-in-one standalone HTML5/CSS3/JS dashboard string."""
    traj_json_str = json.dumps(trajectory_data, indent=2)
    doc_json_str = json.dumps(doctor_data or {}, indent=2)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Project Umbrella -- Adversarial Monitoring & Trajectory Inspector</title>
  <style>
    :root {{
      --primary: #1a365d;
      --secondary: #2b6cb0;
      --accent-red: #e53e3e;
      --accent-green: #38a169;
      --accent-blue: #3182ce;
      --bg: #f7fafc;
      --card-bg: #ffffff;
      --text: #2d3748;
      --text-muted: #718096;
      --border: #e2e8f0;
      --font-mono: "Fira Code", Consolas, Monaco, "Courier New", monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header {{
      background: var(--primary);
      color: #fff;
      padding: 1.25rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    header h1 {{ font-size: 1.35rem; font-weight: 700; letter-spacing: -0.5px; }}
    header .badge {{
      background: var(--accent-green);
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
    }}
    .container {{
      max-width: 1280px;
      margin: 1.5rem auto;
      padding: 0 1rem;
    }}
    /* Metric Cards */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .card .title {{ font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600; }}
    .card .value {{ font-size: 1.75rem; font-weight: 700; color: var(--primary); margin-top: 0.25rem; }}
    .card .desc {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; }}
    
    /* Navigation Tabs */
    .tabs {{
      display: flex;
      border-bottom: 2px solid var(--border);
      margin-bottom: 1.5rem;
      background: var(--card-bg);
      border-radius: 8px 8px 0 0;
      overflow-x: auto;
    }}
    .tab-btn {{
      padding: 0.85rem 1.5rem;
      border: none;
      background: none;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      border-bottom: 3px solid transparent;
      transition: all 0.2s;
      white-space: nowrap;
    }}
    .tab-btn:hover {{ color: var(--primary); }}
    .tab-btn.active {{
      color: var(--secondary);
      border-bottom-color: var(--secondary);
      background: #ebf8ff;
    }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
      margin-top: 0.5rem;
    }}
    th, td {{
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{ background: #f8fafc; font-weight: 600; color: var(--primary); }}
    tr:hover {{ background: #f1f5f9; }}
    
    /* Status Badges */
    .tag {{
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .tag-green {{ background: #c6f6d5; color: #22543d; }}
    .tag-red {{ background: #fed7d7; color: #742a2a; }}
    .tag-blue {{ background: #bee3f8; color: #2a4365; }}
    .tag-yellow {{ background: #feebc8; color: #7b341e; }}

    /* Diff Viewer */
    .diff-box {{
      background: #1e1e1e;
      color: #d4d4d4;
      font-family: var(--font-mono);
      font-size: 0.82rem;
      padding: 1rem;
      border-radius: 6px;
      overflow-x: auto;
      white-space: pre-wrap;
      max-height: 400px;
    }}
    .diff-add {{ color: #4ade80; background: rgba(74, 222, 128, 0.1); display: block; }}
    .diff-del {{ color: #f87171; background: rgba(248, 113, 113, 0.1); display: block; }}
    .diff-hdr {{ color: #60a5fa; font-weight: bold; display: block; }}

    /* Round Cards */
    .round-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      margin-bottom: 1.25rem;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .round-header {{
      background: #f8fafc;
      padding: 0.85rem 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
    }}
    .round-body {{ padding: 1.25rem; }}
    .section-title {{ font-size: 0.95rem; font-weight: 700; color: var(--primary); margin-bottom: 0.5rem; }}

    .btn {{
      display: inline-block;
      padding: 0.4rem 0.85rem;
      background: var(--secondary);
      color: #fff;
      border: none;
      border-radius: 4px;
      font-size: 0.85rem;
      cursor: pointer;
      text-decoration: none;
    }}
    .btn:hover {{ background: var(--primary); }}
  </style>
</head>
<body>

  <header>
    <div>
      <h1>Project Umbrella -- Monitoring & Trajectory Inspector</h1>
      <small style="opacity: 0.8;">Autonomous Adversarial Hardening for Web Identity Protocols</small>
    </div>
    <div style="display:flex; gap:0.75rem; align-items:center;">
      <button class="btn" style="background:#fff; color:var(--primary); font-weight:700;" onclick="switchTab('tab-intake')">+ Run a SaaS Target</button>
      <div id="convergence-badge" class="badge">Checking Status...</div>
    </div>
  </header>

  <div class="container">
    <!-- Top Summary KPI Cards -->
    <div class="metrics-grid">
      <div class="card">
        <div class="title">Sound Convergence</div>
        <div class="value" id="kpi-convergence">--</div>
        <div class="desc" id="kpi-convergence-sub">Verification State</div>
      </div>
      <div class="card">
        <div class="title">Vulnerabilities Remediated</div>
        <div class="value" id="kpi-remediated">-- / --</div>
        <div class="desc">100% Threat Elimination</div>
      </div>
      <div class="card">
        <div class="title">PoC+ Mutation Defense</div>
        <div class="value" id="kpi-mutations">-- / --</div>
        <div class="desc">Bypasses Neutralized</div>
      </div>
      <div class="card">
        <div class="title">Functional Regressions</div>
        <div class="value" id="kpi-regressions">0%</div>
        <div class="desc">Golden Path Intact</div>
      </div>
    </div>

    <!-- Secondary Metrics Grid -->
    <div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));">
      <div class="card">
        <div class="title">Total Co-Evolution Rounds</div>
        <div class="value" id="kpi-rounds">--</div>
        <div class="desc">Attack/Repair Cycles Executed</div>
      </div>
      <div class="card">
        <div class="title">AST Patches Synthesized</div>
        <div class="value" id="kpi-patches">--</div>
        <div class="desc">Blue Agent Repairs Written</div>
      </div>
      <div class="card">
        <div class="title">Mutation Bypass Rate</div>
        <div class="value" id="kpi-bypass-rate">--</div>
        <div class="desc">Property Attacks That Slipped Through</div>
      </div>
      <div class="card">
        <div class="title">Unresolved Threat Vectors</div>
        <div class="value" id="kpi-unresolved">--</div>
        <div class="desc">Max Repair Attempts Exhausted</div>
      </div>
      <div class="card">
        <div class="title">Patch Acceptance Rate</div>
        <div class="value" id="kpi-acceptance">--</div>
        <div class="desc">Dual-Gate Approvals / Attempts</div>
      </div>
      <div class="card">
        <div class="title">Session Duration</div>
        <div class="value" id="kpi-duration">--</div>
        <div class="desc">Start to Final Verdict</div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs">
      <button class="tab-btn" onclick="switchTab('tab-intake')">0. SaaS Target Intake</button>
      <button class="tab-btn active" onclick="switchTab('tab-adaptive')">1. Adaptive Decision Graph</button>
      <button class="tab-btn" onclick="switchTab('tab-patches')">2. AST Code Patches & Diffs</button>
      <button class="tab-btn" onclick="switchTab('tab-dualgate')">3. PoC+ & Dual-Gate Matrix</button>
      <button class="tab-btn" onclick="switchTab('tab-doctor')">4. Environment & Pre-Flight</button>
      <button class="tab-btn" onclick="switchTab('tab-raw')">5. Trajectory JSON & Audit Trail</button>
    </div>

    <!-- TAB 0: CUSTOM SAAS INTAKE -->
    <div id="tab-intake" class="tab-content">
      <div class="card">
        <h3 class="section-title">Test Your Custom SaaS Through the Full Red/Blue/Dual-Gate Flow</h3>
        <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem;">
          Point Umbrella at any FastAPI/Starlette OAuth 2.0 authorization server. The target file is cloned into an
          isolated sandbox (the pristine source is never modified), validated by the Environment Doctor, then driven
          through the identical adaptive attack & AST repair pipeline.
        </p>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:1rem; margin-bottom:1rem;">
          <div>
            <label style="font-size:0.8rem; font-weight:600; color:var(--text-muted);">Target Python Module (absolute path to your OAuth app)</label>
            <input id="saas-target-path" type="text" placeholder="/path/to/your_saas_app.py"
                   style="width:100%; padding:0.5rem; border:1px solid var(--border); border-radius:4px; margin-top:0.25rem; font-size:0.9rem;">
          </div>
          <div>
            <label style="font-size:0.8rem; font-weight:600; color:var(--text-muted);">Registered Client ID</label>
            <input id="saas-client-id" type="text" placeholder="e.g. acme-saas-7f3a"
                   style="width:100%; padding:0.5rem; border:1px solid var(--border); border-radius:4px; margin-top:0.25rem; font-size:0.9rem;">
          </div>
          <div>
            <label style="font-size:0.8rem; font-weight:600; color:var(--text-muted);">Registered Redirect URI</label>
            <input id="saas-redirect-uri" type="text" placeholder="https://your-saas.example.com/oauth/redirect"
                   style="width:100%; padding:0.5rem; border:1px solid var(--border); border-radius:4px; margin-top:0.25rem; font-size:0.9rem;">
          </div>
          <div>
            <label style="font-size:0.8rem; font-weight:600; color:var(--text-muted);">Scope (optional)</label>
            <input id="saas-scope" type="text" placeholder="read:profile"
                   style="width:100%; padding:0.5rem; border:1px solid var(--border); border-radius:4px; margin-top:0.25rem; font-size:0.9rem;">
          </div>
          <div>
            <label style="font-size:0.8rem; font-weight:600; color:var(--text-muted);">Max Rounds (default 15)</label>
            <input id="saas-max-rounds" type="number" min="1" max="60" placeholder="15"
                   style="width:100%; padding:0.5rem; border:1px solid var(--border); border-radius:4px; margin-top:0.25rem; font-size:0.9rem;">
          </div>
        </div>
        <div style="display:flex; gap:0.75rem; align-items:center;">
          <button class="btn" id="btn-run-saas" onclick="runSaaS()">Run Custom SaaS Test</button>
          <button class="btn" style="background:var(--accent-green);" onclick="runBundledSaaS()">Test Bundled Acme SaaS</button>
          <span id="saas-status" style="font-size:0.85rem; color:var(--text-muted);"></span>
        </div>
        <pre id="saas-result-box" class="diff-box" style="margin-top:1rem; display:none;"></pre>
      </div>
    </div>

    <!-- TAB 1: ADAPTIVE DECISION GRAPH -->
    <div id="tab-adaptive" class="tab-content active">
      <div class="card" style="margin-bottom: 1.5rem;">
        <h3 class="section-title">How Red Adapted Its Attack Trajectory</h3>
        <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem;">
          Umbrella dynamically ranks attack candidates using threat severity ratings and <b>response-driven endpoint correlation</b>. 
          When an exploit breaches an endpoint (e.g. <code>/token</code>), the planner assigns a <b>+20 priority boost</b> to remaining <code>/token</code> vectors.
        </p>
        <div id="rounds-accordion"></div>
      </div>
    </div>

    <!-- TAB 2: CODE PATCHES & DIFFS -->
    <div id="tab-patches" class="tab-content">
      <div class="card">
        <h3 class="section-title">Surgical AST Program Repairs</h3>
        <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem;">
          Below are the exact unified code diffs synthesized by the Blue Agent, validated for Python syntax under <code>ast.parse()</code> prior to file write.
        </p>
        <div id="diffs-container"></div>
      </div>
    </div>

    <!-- TAB 3: DUAL-GATE & MUTATION MATRIX -->
    <div id="tab-dualgate" class="tab-content">
      <div class="card">
        <h3 class="section-title">Dual-Gate Adjudication & Property Mutation Matrix</h3>
        <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem;">
          Demonstrating that candidate patches pass both Gate 1 (100% of property mutations blocked) and Gate 2 (100% of legitimate OAuth flows operational).
        </p>
        <table>
          <thead>
            <tr>
              <th>Round / Vector</th>
              <th>Target Endpoint</th>
              <th>Gate 1: PoC+ Mutations</th>
              <th>Gate 2: Golden Path</th>
              <th>Dual-Gate Verdict</th>
            </tr>
          </thead>
          <tbody id="dualgate-table-body"></tbody>
        </table>
      </div>
    </div>

    <!-- TAB 4: ENVIRONMENT & DOCTOR -->
    <div id="tab-doctor" class="tab-content">
      <div class="card">
        <h3 class="section-title">Host Runtime Diagnostics & AST Route Discovery</h3>
        <div id="doctor-content"></div>
      </div>
    </div>

    <!-- TAB 5: RAW TRAJECTORY JSON -->
    <div id="tab-raw" class="tab-content">
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <h3 class="section-title" style="margin: 0;">Full Execution Trajectory Trace</h3>
          <button class="btn" onclick="downloadJSON()">Download trajectory.json</button>
        </div>
        <pre id="raw-json-box" class="diff-box" style="max-height: 500px;"></pre>
      </div>
    </div>
  </div>

  <script>
    const TRAJECTORY = {traj_json_str};
    const DOCTOR = {doc_json_str};

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      event.target.classList.add('active');
    }}

    function renderMetrics() {{
      const summary = TRAJECTORY.summary || {{}};
      const isConverged = summary.soundly_converged;
      
      const convBadge = document.getElementById('convergence-badge');
      if (isConverged) {{
        convBadge.innerText = 'SOUNDLY CONVERGED (100%)';
        convBadge.style.background = 'var(--accent-green)';
        document.getElementById('kpi-convergence').innerText = '100%';
        document.getElementById('kpi-convergence').style.color = 'var(--accent-green)';
        document.getElementById('kpi-convergence-sub').innerText = 'Mathematically Verified';
      }} else {{
        convBadge.innerText = 'IN PROGRESS / PARTIAL';
        convBadge.style.background = 'var(--accent-red)';
        document.getElementById('kpi-convergence').innerText = 'PENDING';
        document.getElementById('kpi-convergence').style.color = 'var(--accent-red)';
      }}

      document.getElementById('kpi-remediated').innerText = 
        `${{summary.remediated_vectors_count || 0}} / ${{summary.active_vectors_count || 5}}`;
      
      document.getElementById('kpi-mutations').innerText = 
        `${{summary.total_mutations_blocked || 0}} / ${{summary.total_mutations_tested || 0}}`;
      
      document.getElementById('kpi-regressions').innerText =
        `${{summary.functional_regressions || 0}}%`;

      // --- Secondary metrics grid ---
      const rounds = TRAJECTORY.rounds || [];
      const gateRounds = rounds.filter(r => r.gate_result && typeof r.gate_result === 'object');
      const accepted = gateRounds.filter(r => r.status === 'PATCHED_AND_VERIFIED').length;
      const tested = summary.total_mutations_tested || 0;
      const blocked = summary.total_mutations_blocked || 0;
      const bypassRate = tested > 0 ? Math.round(((tested - blocked) / tested) * 100) : 0;

      document.getElementById('kpi-rounds').innerText = summary.total_rounds ?? rounds.length;
      document.getElementById('kpi-patches').innerText = summary.patches_applied ?? rounds.filter(r => r.patch).length;
      document.getElementById('kpi-bypass-rate').innerText = bypassRate + '%';
      document.getElementById('kpi-bypass-rate').style.color = bypassRate === 0 ? 'var(--accent-green)' : 'var(--accent-red)';
      document.getElementById('kpi-unresolved').innerText = summary.unresolved_vectors_count ?? 0;
      const acceptance = gateRounds.length > 0 ? Math.round((accepted / gateRounds.length) * 100) : 0;
      document.getElementById('kpi-acceptance').innerText = `${{accepted}} / ${{gateRounds.length}} (${{acceptance}}%)`;

      let dur = '--';
      if (TRAJECTORY.started_at && TRAJECTORY.completed_at) {{
        const ms = new Date(TRAJECTORY.completed_at) - new Date(TRAJECTORY.started_at);
        const s = Math.floor(ms / 1000);
        dur = s >= 60 ? Math.floor(s / 60) + 'm ' + (s % 60) + 's' : s + 's';
      }}
      document.getElementById('kpi-duration').innerText = dur;
    }}

    // --- SaaS intake (live server mode only) ---
    const LIVE_MODE = location.protocol.startsWith('http');

    async function runSaaS() {{
      const body = {{
        target_path: document.getElementById('saas-target-path').value.trim(),
        client_id: document.getElementById('saas-client-id').value.trim(),
        redirect_uri: document.getElementById('saas-redirect-uri').value.trim(),
        scope: document.getElementById('saas-scope').value.trim() || null,
        max_rounds: parseInt(document.getElementById('saas-max-rounds').value || '15', 10),
      }};
      await postSaaS(body);
    }}

    async function runBundledSaaS() {{
      await postSaaS({{ bundled: true, max_rounds: parseInt(document.getElementById('saas-max-rounds').value || '15', 10) }});
    }}

    async function postSaaS(body) {{
      const status = document.getElementById('saas-status');
      const box = document.getElementById('saas-result-box');
      if (!LIVE_MODE) {{
        box.style.display = 'block';
        box.innerText = 'This dashboard was exported as a static file (file://).\\nSaaS runs require the live monitor server: run  python main.py --serve  and open http://127.0.0.1:<port>/';
        return;
      }}
      status.innerText = 'Running Red/Blue/Dual-Gate flow on target...';
      box.style.display = 'none';
      try {{
        const res = await fetch('/api/run-saas', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(body),
        }});
        const out = await res.json();
        if (!res.ok || !out.ok) {{
          throw new Error(out.error || ('server returned HTTP ' + res.status));
        }}
        // Reload the freshly computed trajectory into this dashboard
        TRAJECTORY = out.trajectory;
        DOCTOR = out.doctor;
        renderMetrics();
        renderAdaptiveDecisions();
        renderDiffs();
        renderDualGateTable();
        renderDoctor();
        renderRawJSON();
        status.innerText = '';
        box.style.display = 'block';
        box.innerText = 'SaaS run complete -> trajectory ' + out.trajectory_path + '\\nsandbox: ' + out.sandbox_dir + '\\n' + JSON.stringify(out.summary || {{}}, null, 2);
        switchTab('tab-adaptive');
      }} catch (err) {{
        status.innerText = '';
        box.style.display = 'block';
        box.innerText = 'Run failed: ' + err.message;
      }}
    }}

    function renderAdaptiveDecisions() {{
      const container = document.getElementById('rounds-accordion');
      const rounds = TRAJECTORY.rounds || [];
      if (!rounds.length) {{
        container.innerHTML = '<p style="color:var(--text-muted);">No rounds recorded yet.</p>';
        return;
      }}

      container.innerHTML = rounds.map(r => {{
        const dec = r.adaptive_decision || {{}};
        const ranking = dec.candidate_ranking || [];
        const proof = r.vulnerability || {{}};
        const patch = r.patch || {{}};
        
        return `
          <div class="round-card">
            <div class="round-header">
              <div>
                <strong>Round ${{r.round_number}}: [${{r.vector_id}}]</strong>
                <span style="margin-left: 10px; color: var(--text-muted); font-size: 0.85rem;">${{r.threat_info?.name || ''}}</span>
              </div>
              <div>
                <span class="tag tag-blue">${{r.threat_info?.severity || 'MEDIUM'}}</span>
                <span class="tag tag-green">${{r.status}}</span>
              </div>
            </div>
            <div class="round-body">
              <div style="margin-bottom: 0.75rem;">
                <strong>Adaptive Selection Rationale:</strong>
                <div style="background:#edf2f7; padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.85rem; margin-top: 0.25rem;">
                  Total Score: <b>${{dec.total_score || 0}}</b> (Base: ${{dec.base_score || 0}} + Boost: ${{dec.boost || 0}})
                  <br/><i>${{dec.boost_reason || 'Standard priority'}}</i>
                </div>
              </div>

              ${{ranking.length ? `
                <div style="margin-bottom: 0.75rem;">
                  <strong style="font-size: 0.85rem;">Candidate Queue Ranking at this Turn:</strong>
                  <table style="margin-top: 0.25rem;">
                    <thead>
                      <tr><th>Vector ID</th><th>Total Score</th><th>Base Severity</th><th>Correlation Boost</th><th>Rationale</th></tr>
                    </thead>
                    <tbody>
                      ${{ranking.map(c => `
                        <tr style="${{c.vector_id === r.vector_id ? 'font-weight:bold; background:#e6fffa;' : ''}}">
                          <td>${{c.vector_id}} ${{c.vector_id === r.vector_id ? '<b>(SELECTED)</b>' : ''}}</td>
                          <td>${{c.total_score}}</td>
                          <td>${{c.base_score}}</td>
                          <td>+${{c.boost}}</td>
                          <td><small>${{c.reason}}</small></td>
                        </tr>
                      `).join('')}}
                    </tbody>
                  </table>
                </div>
              ` : ''}}

              ${{proof.poc_summary ? `
                <div style="margin-top: 0.5rem;">
                  <strong>Vulnerability Proof (PoC):</strong>
                  <p style="font-size: 0.85rem; color: var(--accent-red); margin-top: 0.2rem;">${{proof.poc_summary}}</p>
                </div>
              ` : ''}}
            </div>
          </div>
        `;
      }}).join('');
    }}

    function renderDiffs() {{
      const container = document.getElementById('diffs-container');
      const rounds = (TRAJECTORY.rounds || []).filter(r => r.patch);
      
      if (!rounds.length) {{
        container.innerHTML = '<p style="color:var(--text-muted);">No patches recorded.</p>';
        return;
      }}

      container.innerHTML = rounds.map(r => {{
        const patch = r.patch;
        const diffText = formatDiff(patch.diff_patch || '');
        return `
          <div class="round-card">
            <div class="round-header">
              <div>
                <strong>[${{r.vector_id}}] Patch for ${{patch.target_file}}</strong>
                <span class="tag tag-green" style="margin-left: 10px;">AST Validated</span>
              </div>
              <small style="color:var(--text-muted);">${{patch.lines_changed}} lines modified</small>
            </div>
            <div class="round-body">
              <p style="font-size: 0.85rem; margin-bottom: 0.75rem;"><b>Remediation Rationale:</b> ${{patch.explanation}}</p>
              <div class="diff-box">${{diffText}}</div>
            </div>
          </div>
        `;
      }}).join('');
    }}

    function formatDiff(rawDiff) {{
      const lines = rawDiff.split('\\n');
      return lines.map(line => {{
        if (line.startsWith('+')) return `<span class="diff-add">${{escapeHtml(line)}}</span>`;
        if (line.startsWith('-')) return `<span class="diff-del">${{escapeHtml(line)}}</span>`;
        if (line.startsWith('@')) return `<span class="diff-hdr">${{escapeHtml(line)}}</span>`;
        return escapeHtml(line);
      }}).join('\\n');
    }}

    function escapeHtml(text) {{
      return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }}

    function renderDualGateTable() {{
      const tbody = document.getElementById('dualgate-table-body');
      const rounds = TRAJECTORY.rounds || [];
      tbody.innerHTML = rounds.map(r => {{
        const gate = r.gate_result || {{}};
        const secPass = gate.security_check_passed;
        const funcPass = gate.golden_path_passed;
        return `
          <tr>
            <td><strong>Round ${{r.round_number}}:</strong> ${{r.vector_id}}</td>
            <td><code>${{r.threat_info?.target_endpoint || '/authorize'}}</code></td>
            <td>
              <span class="tag ${{secPass ? 'tag-green' : 'tag-red'}}">
                ${{secPass ? 'PASS' : 'FAIL'}} (${{gate.mutations_blocked || 0}}/${{gate.mutations_tested || 0}} Neutralized)
              </span>
            </td>
            <td>
              <span class="tag ${{funcPass ? 'tag-green' : 'tag-red'}}">
                ${{funcPass ? 'PASS (100% Contract)' : 'REGRESSION'}}
              </span>
            </td>
            <td>
              <span class="tag ${{r.status === 'PATCHED_AND_VERIFIED' ? 'tag-green' : 'tag-yellow'}}">
                ${{r.status}}
              </span>
            </td>
          </tr>
        `;
      }}).join('');
    }}

    function renderDoctor() {{
      const container = document.getElementById('doctor-content');
      if (!DOCTOR.host_info) {{
        container.innerHTML = '<p style="color:var(--text-muted);">Run <code>python main.py --doctor</code> to inspect environment.</p>';
        return;
      }}
      
      const host = DOCTOR.host_info;
      const checks = DOCTOR.checks || [];
      const routes = DOCTOR.discovered_routes || [];

      container.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
          <div style="background:#f8fafc; padding: 1rem; border-radius: 6px; border: 1px solid var(--border);">
            <div style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">HOST SYSTEM</div>
            <div style="font-weight:bold; margin-top:0.25rem;">${{host.os_name}} (${{host.architecture}})</div>
            <div style="font-size:0.85rem; color:var(--text-muted);">Python ${{host.python_version}}</div>
          </div>
          <div style="background:#f8fafc; padding: 1rem; border-radius: 6px; border: 1px solid var(--border);">
            <div style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">TARGET WORKSPACE</div>
            <div style="font-weight:bold; font-size:0.85rem; word-break:break-all; margin-top:0.25rem;">${{host.workspace_root}}</div>
          </div>
        </div>

        <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem;">Pre-Flight System Diagnostics:</h4>
        <table style="margin-bottom: 1.5rem;">
          <thead><tr><th>Check Name</th><th>Status</th><th>Diagnostic Output</th></tr></thead>
          <tbody>
            ${{checks.map(c => `
              <tr>
                <td><b>${{c.name}}</b></td>
                <td><span class="tag ${{c.status === 'PASS' ? 'tag-green' : (c.status === 'WARN' ? 'tag-yellow' : 'tag-red')}}">${{c.status}}</span></td>
                <td>${{c.message}}</td>
              </tr>
            `).join('')}}
          </tbody>
        </table>

        ${{routes.length ? `
          <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem;">Discovered AST Route Handlers:</h4>
          <table>
            <thead><tr><th>Route Path</th><th>Method</th><th>Handler Function</th><th>AST Line Number</th></tr></thead>
            <tbody>
              ${{routes.map(rt => `
                <tr>
                  <td><code>${{rt.route_path}}</code></td>
                  <td><span class="tag tag-blue">${{rt.method?.toUpperCase() || 'GET'}}</span></td>
                  <td><code>${{rt.name}}</code></td>
                  <td>line ${{rt.lineno}}</td>
                </tr>
              `).join('')}}
            </tbody>
          </table>
        ` : ''}}
      `;
    }}

    function renderRawJSON() {{
      document.getElementById('raw-json-box').innerText = JSON.stringify(TRAJECTORY, null, 2);
    }}

    function downloadJSON() {{
      const blob = new Blob([JSON.stringify(TRAJECTORY, null, 2)], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `umbrella_trajectory_${{TRAJECTORY.session_id || 'session'}}.json`;
      a.click();
    }}

    // Initial render
    renderMetrics();
    renderAdaptiveDecisions();
    renderDiffs();
    renderDualGateTable();
    renderDoctor();
    renderRawJSON();
  </script>
</body>
</html>
"""
    return html_template


def export_dashboard_file(trajectory_path: str, output_html_path: str, doctor_data: Optional[Dict[str, Any]] = None) -> str:
    """Exports a self-contained HTML file from trajectory JSON."""
    if os.path.exists(trajectory_path):
        with open(trajectory_path, "r", encoding="utf-8") as f:
            trajectory_data = json.load(f)
    else:
        trajectory_data = {"summary": {"soundly_converged": False}, "rounds": []}

    html = generate_dashboard_html(trajectory_data, doctor_data)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_html_path


def create_monitor_app(trajectory_path: str, doctor_data: Optional[Dict[str, Any]] = None,
                       workspace_root: Optional[str] = None) -> FastAPI:
    """Builds a lightweight FastAPI monitoring web server with a live SaaS intake endpoint."""
    app = FastAPI(title="Umbrella Monitor")
    if workspace_root is None:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @app.get("/", response_class=HTMLResponse)
    def index():
        if os.path.exists(trajectory_path):
            with open(trajectory_path, "r", encoding="utf-8") as f:
                trajectory_data = json.load(f)
        else:
            trajectory_data = {"summary": {"soundly_converged": False}, "rounds": []}
        return generate_dashboard_html(trajectory_data, doctor_data)

    @app.get("/api/trajectory", response_class=JSONResponse)
    def get_trajectory():
        if os.path.exists(trajectory_path):
            with open(trajectory_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"error": "No trajectory found."}

    @app.get("/api/bundled-saas", response_class=JSONResponse)
    def bundled_saas_info():
        from aegis.custom_saas import (
            CUSTOM_SAAS_LABEL, CUSTOM_SAAS_TARGET, CUSTOM_SAAS_CLIENT_ID,
            CUSTOM_SAAS_REDIRECT_URI, CUSTOM_SAAS_SCOPE,
        )
        return {
            "label": CUSTOM_SAAS_LABEL,
            "target_path": os.path.join(workspace_root, CUSTOM_SAAS_TARGET),
            "client_id": CUSTOM_SAAS_CLIENT_ID,
            "redirect_uri": CUSTOM_SAAS_REDIRECT_URI,
            "scope": CUSTOM_SAAS_SCOPE,
        }

    @app.post("/api/run-saas", response_class=JSONResponse)
    def run_saas(payload: Dict[str, Any]):
        """Runs the full Red/Blue/Dual-Gate flow against a BYO (or bundled) SaaS module.

        The target is executed from an isolated sandbox copy; the pristine source is
        never patched. The fresh trajectory is also written to the monitor's main
        trajectory file so the dashboard reflects it on reload.
        """
        import tempfile
        from aegis.custom_saas.runner import run_target_flow
        from aegis.custom_saas import (
            CUSTOM_SAAS_TARGET, CUSTOM_SAAS_CLIENT_ID,
            CUSTOM_SAAS_REDIRECT_URI, CUSTOM_SAAS_SCOPE,
        )

        if payload.get("bundled"):
            target_path = os.path.join(workspace_root, CUSTOM_SAAS_TARGET)
            client_id, redirect_uri, scope = CUSTOM_SAAS_CLIENT_ID, CUSTOM_SAAS_REDIRECT_URI, CUSTOM_SAAS_SCOPE
        else:
            target_path = (payload.get("target_path") or "").strip()
            client_id = (payload.get("client_id") or "").strip()
            redirect_uri = (payload.get("redirect_uri") or "").strip()
            scope = (payload.get("scope") or "").strip() or None
            if not target_path:
                return JSONResponse(status_code=400, content={"ok": False, "error": "target_path is required (or set bundled: true)."})
            if not (client_id and redirect_uri):
                return JSONResponse(status_code=400, content={"ok": False, "error": "client_id and redirect_uri are required for a custom target."})

        try:
            max_rounds = max(1, min(60, int(payload.get("max_rounds") or 15)))
        except (TypeError, ValueError):
            max_rounds = 15

        try:
            result = run_target_flow(
                workspace_root=workspace_root,
                target_path=target_path,
                client_id=client_id,
                redirect_uri=redirect_uri,
                scope=scope,
                max_rounds=max_rounds,
                trajectory_path=trajectory_path,
                sandbox_dir=tempfile.mkdtemp(prefix="umbrella_saas_"),
            )
        except Exception as e:
            return JSONResponse(status_code=400, content={"ok": False, "error": f"{type(e).__name__}: {e}"})

        with open(trajectory_path, "r", encoding="utf-8") as f:
            traj = json.load(f)
        return {
            "ok": True,
            "trajectory": traj,
            "doctor": result["doctor_report"].model_dump(),
            "summary": traj.get("summary", {}),
            "trajectory_path": trajectory_path,
            "sandbox_dir": result["sandbox_dir"],
            "target_copy": result["target_copy"],
        }

    return app


def serve_dashboard(trajectory_path: str, host: str = "127.0.0.1", port: int = 8080,
                    doctor_data: Optional[Dict[str, Any]] = None,
                    workspace_root: Optional[str] = None):
    """Launches the interactive monitoring server (with live SaaS intake endpoint)."""
    app = create_monitor_app(trajectory_path, doctor_data=doctor_data, workspace_root=workspace_root)
    print(f"\n[+] Project Umbrella Monitoring Dashboard live at: http://{host}:{port}")
    print(f"[+] Use the 'Run a SaaS Target' button on the dashboard to test your own OAuth app.")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    traj_path = os.path.join(workspace, "umbrella_trajectory.json")
    out_path = os.path.join(workspace, "umbrella_dashboard.html")
    export_dashboard_file(traj_path, out_path)
    print(f"Exported interactive dashboard to: {out_path}")
