# Umbrella SaaS pitch + technical deep-dive deck builder (python-pptx, native shape diagrams)
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ---------- palette (security SaaS: navy ground, red=attacker, blue=repairer, green=verified) ----------
BG    = RGBColor(0x0E, 0x16, 0x2A)
PANEL = RGBColor(0x1D, 0x29, 0x41)
PANEL2= RGBColor(0x24, 0x32, 0x4E)
LINE  = RGBColor(0x3A, 0x4A, 0x6B)
WHITE = RGBColor(0xF5, 0xF8, 0xFC)
MUT   = RGBColor(0x9B, 0xAA, 0xC0)
DIM   = RGBColor(0x6B, 0x7A, 0x94)
RED   = RGBColor(0xF0, 0x52, 0x52)
RED_T = RGBColor(0x3A, 0x1E, 0x24)
BLUE  = RGBColor(0x4C, 0x96, 0xF5)
BLUE_T= RGBColor(0x16, 0x27, 0x42)
GREEN = RGBColor(0x34, 0xD3, 0x99)
GREEN_T=RGBColor(0x12, 0x32, 0x2A)
AMBER = RGBColor(0xF5, 0xB8, 0x4A)
AMBER_T=RGBColor(0x37, 0x2C, 0x14)
FONT  = "Arial"
MONO  = "Courier New"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

# ---------- helpers ----------
def slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    return s

def txt(s, x, y, w, h, text, size=14, color=WHITE, bold=False, align=PP_ALIGN.LEFT,
        font=FONT, anchor=MSO_ANCHOR.TOP, ls=1.0, space_after=0):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold; r.font.name = font; r.font.color.rgb = color
        p.alignment = align; p.line_spacing = ls
        if space_after: p.space_after = Pt(space_after)
    return tb

def bullets(s, x, y, w, h, items, size=14, gap=6):
    """items: list of (text, bold, color, optional_size)"""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, it in enumerate(items):
        t, b, c = it[0], it[1], it[2]
        sz = it[3] if len(it) > 3 else size
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "•  "
        r1.font.size = Pt(sz); r1.font.color.rgb = c; r1.font.bold = True; r1.font.name = FONT
        r2 = p.add_run(); r2.text = t
        r2.font.size = Pt(sz); r2.font.bold = b; r2.font.color.rgb = c; r2.font.name = FONT
        p.line_spacing = 1.05; p.space_after = Pt(gap)
    return tb

def box(s, x, y, w, h, fill, line=None, rounded=True, lw=1.25, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = s.shapes.add_shape(shape if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line: sp.line.color.rgb = line; sp.line.width = Pt(lw)
    else: sp.line.fill.background()
    sp.shadow.inherit = False
    return sp

def label(sp, title, sub=None, tcolor=WHITE, scolor=MUT, tsz=14, ssz=11, align=PP_ALIGN.CENTER, tfont=FONT, sfont=FONT):
    tf = sp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.09); tf.margin_top = tf.margin_bottom = Inches(0.05)
    p = tf.paragraphs[0]; r = p.add_run(); r.text = title
    r.font.size = Pt(tsz); r.font.bold = True; r.font.color.rgb = tcolor; r.font.name = tfont
    p.alignment = align
    if sub:
        for ln in sub.split("\n"):
            p2 = tf.add_paragraph(); r2 = p2.add_run(); r2.text = ln
            r2.font.size = Pt(ssz); r2.font.color.rgb = scolor; r2.font.name = sfont
            p2.alignment = align; p2.line_spacing = 1.0
    return sp

def arrow(s, x, y, w, h, color=MUT, direction="right", shape=None):
    m = {"right": MSO_SHAPE.RIGHT_ARROW, "left": MSO_SHAPE.LEFT_ARROW,
         "down": MSO_SHAPE.DOWN_ARROW, "up": MSO_SHAPE.UP_ARROW}
    sp = s.shapes.add_shape(shape or m[direction], Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = color; sp.line.fill.background(); sp.shadow.inherit = False
    return sp

def header(s, kicker, title, part):
    box(s, 0.6, 0.42, 0.09, 0.85, AMBER, rounded=False)
    txt(s, 0.85, 0.42, 9.5, 0.3, kicker.upper(), 11, AMBER, True, PP_ALIGN.LEFT)
    txt(s, 0.85, 0.72, 11.0, 0.6, title, 27, WHITE, True, PP_ALIGN.LEFT)
    txt(s, 11.2, 7.12, 1.6, 0.25, part, 9, DIM, False, PP_ALIGN.RIGHT)

PAGE = {"n": 0}
def footer(s, part):
    PAGE["n"] += 1
    txt(s, 0.6, 7.12, 6.0, 0.25, f"Umbrella · {part}", 9, DIM)
    txt(s, 12.4, 7.12, 0.35, 0.25, str(PAGE["n"]), 9, DIM, False, PP_ALIGN.RIGHT)

def panel(s, x, y, w, h, title=None, fill=PANEL, tcolor=WHITE, accent=None):
    p = box(s, x, y, w, h, fill, line=LINE)
    if accent:
        box(s, x, y, 0.07, h, accent, rounded=False)
    if title:
        txt(s, x + 0.22, y + 0.14, w - 0.4, 0.3, title, 13, tcolor, True)
    return p

def set_cell(cell, text, size=11, bold=False, color=WHITE, align=PP_ALIGN.LEFT, fill=None, font=FONT):
    tf = cell.text_frame; tf.word_wrap = True
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = cell.margin_right = Inches(0.07)
    cell.margin_top = cell.margin_bottom = Inches(0.04)
    p = tf.paragraphs[0]; p.text = ""
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = font
    p.alignment = align
    if fill is not None:
        cell.fill.solid(); cell.fill.fore_color.rgb = fill

def chip(s, x, y, w, h, text, fill, color=WHITE, size=10.5, bold=True):
    c = box(s, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    label(c, text, tsz=size, tcolor=color, align=PP_ALIGN.CENTER)
    return c

P1, P2 = "Part 1 · The Pitch", "Part 2 · Technical"

# =====================================================================
# S1 — TITLE
# =====================================================================
s = slide()
box(s, 0, 0, 13.333, 7.5, BG, rounded=False)
box(s, 0, 5.0, 13.333, 0.06, PANEL2, rounded=False)
txt(s, 0.9, 1.15, 11.5, 0.4, "CAPSTONE · ADVERSARIAL SECURITY PLATFORM", 12, AMBER, True)
txt(s, 0.9, 1.55, 11.5, 1.4, "Umbrella", 80, WHITE, True)
txt(s, 0.9, 2.95, 11.5, 0.5, "An AI red team and AI blue team that harden your OAuth stack — continuously.",
    20, MUT, False)
# mini loop: chevrons
cw, cy, ch = 3.1, 4.1, 0.95
for i, (t, sub, col) in enumerate([
    ("RED AGENT", "finds every way to break it", RED_T),
    ("BLUE AGENT", "surgically patches the code", BLUE_T),
    ("DUAL GATE", "proves fix AND no regression", GREEN_T),
]):
    cv = s.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(0.9 + i * 3.55), Inches(cy), Inches(cw), Inches(ch))
    cv.fill.solid(); cv.fill.fore_color.rgb = col
    cv.line.color.rgb = col if col != GREEN_T else GREEN; cv.line.width = Pt(1); cv.shadow.inherit = False
    label(cv, t, sub, tcolor=col if col in (RED, BLUE) else GREEN, scolor=MUT, tsz=15, ssz=10.5)
txt(s, 12.0, cy + 0.28, 0.6, 0.4, "↻", 24, AMBER, False, PP_ALIGN.CENTER)
txt(s, 0.9, 5.5, 11.5, 0.9,
    "Part 1 — the pitch, from first principles ·  Part 2 — the engineering, layer by layer\n"
    "github.com/CrispyDEV3loper/umbrella · branch: adaptive-update", 12, MUT)
footer(s, P1)

# =====================================================================
# S2 — THE PROBLEM
# =====================================================================
s = slide()
header(s, "The problem", "Your sign-in chain is the new attack surface", P1)
panel(s, 0.6, 1.75, 7.3, 4.9, "Why this matters now")
bullets(s, 0.95, 2.35, 6.7, 4.0, [
    ("Every SaaS product now authenticates through OAuth 2.0 / OIDC — Google, Microsoft, Okta, your own identity provider.", True, WHITE, 15),
    ("One broken redirect check or missing token guard, and an attacker can exchange a user's authorization code for their session.", False, WHITE, 14),
    ("Auth bugs are logic bugs: they live in the state machine across /authorize → /token → /userinfo, not in one line — scanners that read code statically miss most of them.", False, WHITE, 14),
    ("Security regressions arrive on every deploy. Nothing in your pipeline re-proves that the protocol still holds.", True, AMBER, 15),
], 14, 10)
panel(s, 8.15, 1.75, 4.58, 4.9, "The gap today", accent=RED)
bullets(s, 8.45, 2.35, 4.0, 4.0, [
    ("Manual pen tests: quarterly, point-in-time, and they test one sample payload per flaw.", False, WHITE, 13),
    ("Fixing a hole naively often breaks legitimate logins — so teams ship the vulnerability instead.", False, WHITE, 13),
    ("Nobody verifies that a security patch survived the next deploy.", True, AMBER, 13),
], 13, 9)
footer(s, P1)

# =====================================================================
# S3 — THE COST
# =====================================================================
s = slide()
header(s, "The problem", "What a broken auth chain costs", P1)
panel(s, 0.6, 1.75, 6.0, 4.9, "Downstream of one stolen token", accent=RED)
bullets(s, 0.95, 2.35, 5.3, 4.0, [
    ("Account takeover → data exfiltration → breach disclosure.", False, WHITE, 14),
    ("Compliance exposure: GDPR, SOC 2, HIPAA all sit on identity controls.", False, WHITE, 14),
    ("Trust damage: customers leave after a breach faster than they joined.", False, WHITE, 14),
], 14, 10)
panel(s, 6.85, 1.75, 5.88, 4.9, "Why 'just patch it' backfires")
bullets(s, 7.2, 2.35, 5.2, 4.0, [
    ("Security and functionality are in tension: block the attack and you may block your own users' logins.", True, WHITE, 14),
    ("Shallow fixes (string-blacklist the bad input) hold against one payload and fail against its encoded variants.", False, WHITE, 14),
    ("The patch must be verified against every variant AND every legitimate flow — which is exactly what Umbrella's dual gate does.", False, GREEN, 13),
], 14, 10)
footer(s, P1)

# =====================================================================
# S4 — OAUTH 101
# =====================================================================
s = slide()
header(s, "Foundation, from scratch", "OAuth in 60 seconds: the pass, the code, the token", P1)
txt(s, 0.85, 1.55, 11.5, 0.4,
    "OAuth 2.0 is the standard that lets app A use data from service B without sharing the user's password — by issuing short-lived passes.",
    13, MUT)
# flow
fy, fh = 2.25, 0.85
flow = [
    ("USER", "asks app A\nto use service B", PANEL),
    ("APP A", "redirects user to\nB's /authorize", PANEL),
    ("SERVICE B", "login + consent\nissues one-time CODE", PANEL2),
    ("APP A", "swaps code + proof\nat B's /token", PANEL),
    ("API", "returns short-lived\nACCESS TOKEN", GREEN_T),
    ("DATA", "/userinfo serves\nprofile with Bearer token", PANEL),
]
for i, (t, sub, f) in enumerate(flow):
    bx = box(s, 0.85 + i * 2.15, fy, 1.85, fh, f, line=LINE)
    label(bx, t, sub, tsz=13, ssz=9.5)
    if i < 5:
        arrow(s, 0.85 + i * 2.15 + 1.88, fy + 0.3, 0.24, 0.22, AMBER)
# endpoint cards
ey = 3.6
cards = [
    ("/authorize", "The front door. Checks who's asking and where the result may be sent (redirect_uri) plus an anti-forgery tag (state).", RED),
    ("/token", "The exchange desk. Trades the one-time code + a cryptographic proof (PKCE) for an access token. Must refuse reuse and scope creep.", AMBER),
    ("/userinfo", "The vault door. Returns user data only to a valid bearer token.", GREEN),
]
for i, (t, sub, col) in enumerate(cards):
    c = box(s, 0.85 + i * 4.05, ey, 3.75, 1.5, PANEL, line=LINE)
    box(s, 0.85 + i * 4.05, ey, 0.07, 1.5, col, rounded=False)
    txt(s, 1.1 + i * 4.05, ey + 0.15, 3.3, 0.35, t, 15, col, True, font=MONO)
    txt(s, 1.1 + i * 4.05, ey + 0.55, 3.35, 0.9, sub, 11, MUT, False, ls=1.15)
txt(s, 0.85, 5.55, 11.7, 0.9,
    "PKCE (RFC 7636): an extra one-way proof tied to the code, so a stolen code alone is useless — mandatory for mobile and web apps with no secret.\n"
    "Every flaw class below lives at one of these three doors.", 12.5, MUT, False, ls=1.2)
footer(s, P1)

# =====================================================================
# S5 — FIVE ATTACK CLASSES
# =====================================================================
s = slide()
header(s, "Foundation, from scratch", "Five ways this chain breaks — each attacked 3–5 different ways", P1)
rows = [
    ("Redirect leakage", "OAUTH-REDIRECT-TRAVERSAL", "Attacker forges the 'send result to…' address; a weak startswith check lets ../../ or subdomain tricks leak the code", "CRITICAL", RED, "/authorize"),
    ("Code replay", "OAUTH-CODE-REPLAY", "The one-time code gets redeemed twice → two valid tokens for one consent", "CRITICAL", RED, "/token"),
    ("PKCE downgrade", "OAUTH-PKCE-DOWNGRADE", "Skip or weaken the proof step (missing verifier, 'plain' method) so a stolen code can be cashed in", "HIGH", AMBER, "/token"),
    ("Scope creep", "OAUTH-SCOPE-ESCALATION", "At token time, request 'admin' / 'write:all' / '*' the user never consented to", "HIGH", AMBER, "/token"),
    ("Login forgery", "OAUTH-STATE-CSRF", "Missing or weak state tag lets a malicious site complete the user's login", "HIGH", AMBER, "/authorize"),
]
y0 = 1.7
for i, (lay, tech, desc, sev, scol, ep) in enumerate(rows):
    yy = y0 + i * 0.98
    p = box(s, 0.85, yy, 8.6, 0.85, PANEL, line=LINE)
    box(s, 0.85, yy, 0.07, 0.85, scol, rounded=False)
    txt(s, 1.1, yy + 0.09, 2.6, 0.3, lay, 14, WHITE, True)
    txt(s, 1.1, yy + 0.42, 2.7, 0.3, tech, 9.5, scol, False, font=MONO)
    txt(s, 4.0, yy + 0.1, 5.3, 0.7, desc, 11, MUT, False, ls=1.1)
    chip(s, 9.7, yy + 0.22, 1.15, 0.4, sev, scol if sev == "CRITICAL" else AMBER_T, WHITE, 11)
    txt(s, 10.95, yy + 0.26, 1.7, 0.3, ep, 11, DIM, False, font=MONO)
txt(s, 0.85, 6.75, 11.5, 0.3,
    "Each class is probed with multiple mutation variants — 17 in total — because real patches often block variant #1 and leak variants #2–5.", 12, MUT)
footer(s, P1)

# =====================================================================
# S6 — MEET UMBRELLA
# =====================================================================
s = slide()
header(s, "The product", "Meet Umbrella: an attacker, a repairer, and a referee — running on your CI clock", P1)
txt(s, 0.85, 1.6, 11.6, 0.45,
    "Umbrella runs a co-evolutionary game against your identity stack. No black-box 'AI scan': deterministic agents with verifiable, audited output.",
    14, MUT)
cards = [
    ("RED AGENT", "the attacker", RED, RED_T,
     ["Ranks which flaw class to hit next by severity and what just succeeded", "Hurls 17 mutation variants (encodings, downgrades, forgeries)", "Returns a proof: endpoint, payload, response — evidence, not vibes"]),
    ("BLUE AGENT", "the repairer", BLUE, BLUE_T,
     ["Finds the exact handler function via program-structure (AST) parsing", "Synthesizes an RFC-cited security block, applies it surgically", "Every write is syntax-gated; failed patches roll back atomically"]),
    ("DUAL-GATE REFEREE", "the verifier", GREEN, GREEN_T,
     ["Gate 1: re-run ALL variants of the attacked class — every one must fail", "Gate 2: run the legitimate login + data flow — every one must pass", "Only commit the patch when BOTH gates pass"]),
]
for i, (t, sub, col, cf, items) in enumerate(cards):
    x = 0.85 + i * 4.05
    p = box(s, x, 2.3, 3.75, 3.3, cf, line=LINE)
    box(s, x, 2.3, 3.75, 0.62, col, rounded=False)
    txt(s, x + 0.2, 2.42, 3.4, 0.4, f"{t} — {sub}", 13.5, WHITE if col != GREEN else BG, True)
    bullets(s, x + 0.22, 3.15, 3.35, 2.3, [(it, False, MUT, 11.5) for it in items], 11.5, 7)
footer(s, P1)

# =====================================================================
# S7 — HOW IT WORKS (Layman loop)
# =====================================================================
s = slide()
header(s, "The product", "One loop, three moves, repeat until provably secure", P1)
lw, ly, lh = 3.3, 2.6, 1.7
boxes = [
    ("1 · ATTACK", "Try every way to break it\nbase payload + every mutation variant", RED, RED_T),
    ("2 · PATCH", "Surgically fix the code\nfind the function, insert the RFC-cited guard", BLUE, BLUE_T),
    ("3 · VERIFY", "Prove the break is closed\nAND your users can still log in", GREEN, GREEN_T),
]
for i, (t, sub, col, cf) in enumerate(boxes):
    b = box(s, 0.95 + i * 4.25, ly, lw, lh, cf, line=LINE)
    label(b, t, sub, tsz=16, ssz=11.5, tcolor=col, scolor=MUT)
    if i < 2:
        arrow(s, 0.95 + i * 4.25 + lw + 0.18, ly + 0.62, 0.6, 0.42, AMBER)
# loopback
loop = arrow(s, 0.95 + 2 * 4.25 + lw + 0.25, ly + 0.62, 0.5, 0.42, AMBER, direction="right")
txt(s, 7.5, ly + 1.25, 5.0, 0.3, "next flaw class → until all 5 closed", 12, AMBER, False, PP_ALIGN.CENTER)
box(s, 0.95, 4.75, 11.4, 1.35, PANEL, line=LINE)
txt(s, 1.3, 4.95, 10.8, 0.4, "Every failed patch rolls back automatically (up to 3 attempts per flaw class).", 14, WHITE, True)
txt(s, 1.3, 5.45, 10.8, 0.5,
    "The loop only ends on 'sound convergence': zero unresolved flaw classes, every one verified by both gates.",
    12.5, MUT)
footer(s, P1)

# =====================================================================
# S8 — DUAL GATE PITCH
# =====================================================================
s = slide()
header(s, "The product", "The dual gate: a fix is only real if it holds AND the app still works", P1)
panel(s, 0.85, 1.85, 5.7, 3.0, "GATE 1 · SECURITY", accent=RED)
txt(s, 1.15, 2.5, 5.1, 2.2,
    "Re-exploit the flaw with every mutation variant.\nA shallow patch that blocks the demo payload but leaks the encoded versions fails this gate.\nAll variants must FAIL.",
    13.5, MUT, False, ls=1.3)
panel(s, 6.75, 1.85, 5.7, 3.0, "GATE 2 · FUNCTIONAL", accent=GREEN)
txt(s, 7.05, 2.5, 5.1, 2.2,
    "Run the legitimate flows: real PKCE login, code exchange, protected data access.\n'Fix' the app by breaking logins and this gate catches it.\nAll flows must PASS.",
    13.5, MUT, False, ls=1.3)
box(s, 0.85, 5.15, 11.6, 1.15, GREEN_T, line=GREEN, lw=1.5)
txt(s, 1.2, 5.32, 11.0, 0.35, "Why this matters to you: it makes auto-repair safe to run in CI.", 15, GREEN, True)
txt(s, 1.2, 5.75, 11.0, 0.5, "Without both gates you get either over-blocking (users locked out) or under-blocking (leaks remain). The gate pair is the product's core guarantee.", 12, MUT)
footer(s, P1)

# =====================================================================
# S9 — RESULTS
# =====================================================================
s = slide()
header(s, "Evidence", "Measured, not promised: four system configurations, one harness", P1)
data = [
    ["Configuration", "What's in the loop", "Mutation leaks", "Functional regressions", "Re-exploit", "Sound convergence"],
    ["A · Red only", "Discovery, no repair", "14/17 breached", "0% (nothing patched)", "100%", "No"],
    ["B · No dual gate", "Naive patches, no verification", "60% shallow bypass", "100% — logins broken", "60%", "No"],
    ["C · Static gate", "Single-payload check only", "60% (3/5 leak)", "0%", "60%", "Partial"],
    ["D · Full Umbrella", "Adaptive Red + AST Blue + Dual Gate", "0% (17/17 neutralized)", "0%", "0%", "Yes — 100%"],
]
gf = s.shapes.add_table(5, 6, Inches(0.85), Inches(1.8), Inches(11.6), Inches(2.9))
t = gf.table
for j, w in enumerate([2.5, 3.2, 1.9, 1.9, 1.15, 1.9]):
    t.columns[j].width = Inches(w)
for i in range(5):
    t.rows[i].height = Inches(0.58)
    for j in range(6):
        c = t.cell(i, j)
        if i == 0:
            set_cell(c, data[0][j], 11.5, True, AMBER, PP_ALIGN.LEFT if j > 0 else PP_ALIGN.LEFT, PANEL2)
        else:
            hl = (i == 4)
            fill = GREEN_T if hl else (PANEL if i % 2 else BG)
            colr = GREEN if hl and j in (3, 4, 5) else (WHITE if j == 0 else MUT)
            set_cell(c, data[i][j], 11.5, hl or j == 0, colr, PP_ALIGN.LEFT, fill)
panel(s, 0.85, 5.05, 11.6, 1.5, None, GREEN_T, accent=GREEN)
txt(s, 1.2, 5.3, 11.0, 0.4, "Full Umbrella: 17/17 bypasses neutralized · 0% functional regressions · 0% re-exploit · ~0.4s per full run",
    15, GREEN, True)
txt(s, 1.2, 5.85, 11.0, 0.6,
    "Ablation benchmark: each configuration runs against an isolated copy of the ground-truth target so trials can't contaminate each other. Configurations B and C are measured, not asserted — they show what happens when you remove the gate or use a shallow one.",
    11.5, MUT, False, ls=1.2)
footer(s, P1)

# =====================================================================
# S10 — OBSERVABILITY PITCH
# =====================================================================
s = slide()
header(s, "Trust & visibility", "You can see everything the system does — and it checks itself first", P1)
cards = [
    ("DOCTOR", "pre-flight check-up", GREEN,
     ["Runtime, permissions, syntax parseability of the target", "Finds the OAuth route handlers before starting", "Baseline health: does the legitimate flow even work today?"]),
    ("TRAJECTORY", "audit-grade memory", AMBER,
     ["Every decision, payload, patch, and gate result written to structured JSON", "Decision rationale included: which flaw was picked, why (score + boost)", "The evidence trail a security team can hand an auditor"]),
    ("DASHBOARD", "the control room", BLUE,
     ["5 tabs: adaptive decisions · patches & diffs · gate matrix · environment · audit trail", "One-click static HTML or a live server (python main.py --serve)", "No more 'the agent did what again?'"]),
]
for i, (t, sub, col, items) in enumerate(cards):
    x = 0.85 + i * 4.05
    p = box(s, x, 1.9, 3.75, 3.6, PANEL, line=LINE)
    box(s, x, 1.9, 3.75, 0.55, col, rounded=False)
    txt(s, x + 0.2, 2.0, 3.4, 0.35, f"{t} — {sub}", 13, BG, True)
    bullets(s, x + 0.22, 2.7, 3.35, 2.6, [(it, False, MUT, 11.5) for it in items], 11.5, 8)
txt(s, 0.85, 5.85, 11.5, 0.6,
    "Observability isn't a feature bolted on: the loop, the evidence, and the pre-flight are one system. If the doctor fails, Umbrella aborts instead of guessing.",
    13, AMBER, False)
footer(s, P1)

# =====================================================================
# S11 — WHO IT'S FOR
# =====================================================================
s = slide()
header(s, "The product", "Who runs this, and why they care", P1)
cards = [
    ("SaaS FOUNDERS & CTOs", "Identity is a launch-day feature, and every deploy can silently break it.\nUmbrella in CI turns 'is our OAuth still safe?' into a green/red CI gate.", GREEN),
    ("SECURITY TEAMS", "Stop explaining point-in-time pen-test PDFs.\nDeliver continuous, mutation-level evidence: which variants were tried, which leaked, which the patch closed.", AMBER),
    ("RESEARCHERS", "A clean, reproducible adversarial harness.\nGround-truth fixtures, isolated trials, ablation configurations — a Vul4Py-style methodology for protocol testing.", BLUE),
]
for i, (t, body, col) in enumerate(cards):
    x = 0.85 + i * 4.05
    p = box(s, x, 1.9, 3.75, 3.4, PANEL, line=LINE)
    box(s, x, 1.9, 0.07, 3.4, col, rounded=False)
    txt(s, x + 0.25, 2.1, 3.3, 0.4, t, 14, col, True)
    txt(s, x + 0.25, 2.65, 3.3, 2.4, body, 12, MUT, False, ls=1.25)
txt(s, 0.85, 5.7, 11.5, 0.5,
    "Today: FastAPI/Starlette OAuth authorization & resource servers, Python 3.10+. Design generalizes to Flask/ASGI-WSGI targets and adjacent protocols (OIDC, JWT).",
    12.5, WHITE, False)
footer(s, P1)

# =====================================================================
# S12 — HONEST SCOPE
# =====================================================================
s = slide()
header(s, "Trust & visibility", "Honest engineering: what it is, and what it isn't yet", P1)
panel(s, 0.85, 1.85, 5.6, 4.6, "Delivered today", accent=GREEN)
bullets(s, 1.15, 2.5, 5.0, 3.8, [
    ("Full closed loop: adaptive attack → surgical repair → dual-gate verification → convergence", False, WHITE, 12.5),
    ("17 mutation variants across 5 RFC-cited flaw classes", False, WHITE, 12.5),
    ("Safe writes: path containment, syntax gate, snapshot + rollback", False, WHITE, 12.5),
    ("Audit trail, pre-flight doctor, dashboard, ablation harness, 9-test suite", False, WHITE, 12.5),
], 12.5, 9)
panel(s, 6.75, 1.85, 5.75, 4.6, "Roadmap (stated plainly)", accent=AMBER)
bullets(s, 7.05, 2.5, 5.15, 3.8, [
    ("Target generalization: patch synthesis is anchored to the reference app; broader codebases need structure-based synthesis", False, MUT, 12.5),
    ("Deeper adaptivity: today's planner is severity + one endpoint-correlation boost; learned ranking is next", False, MUT, 12.5),
    ("More protocols: OIDC discovery, JWT claim checks, refresh-token rotation", False, MUT, 12.5),
    ("Live staging: run against ephemeral containers, not just the in-process testbed", False, MUT, 12.5),
], 12.5, 9)
footer(s, P1)

# =====================================================================
# S13 — PART 1 CLOSER
# =====================================================================
s = slide()
box(s, 0, 0, 13.333, 7.5, BG, rounded=False)
box(s, 0, 3.62, 13.333, 0.06, PANEL2, rounded=False)
txt(s, 0.9, 2.35, 11.5, 1.0, "That's the promise.", 40, WHITE, True)
txt(s, 0.9, 3.95, 11.5, 0.5, "Here's how it's actually built — the layers, the loop, the gates, the evidence.", 18, MUT)
txt(s, 0.9, 4.7, 11.5, 0.4, "PART 2 · TECHNICAL DEEP DIVE", 13, AMBER, True)
footer(s, P1)

# =====================================================================
# S14 — DIVIDER + TOC
# =====================================================================
s = slide()
header(s, "Part 2 · Technical", "Deep dive: what you're about to see", P2)
items = [
    ("15", "Seven-layer architecture", "foundation up: contracts, safe hands, attack, repair, adjudication, orchestration, observation, evidence"),
    ("16", "The closed-loop state machine", "every branch, every status, the retry budget"),
    ("17", "Red team internals", "mutation catalog + adaptive planner, no LLM involved"),
    ("18", "Vector × variant matrix", "all five classes, seventeen variants, RFC anchors"),
    ("19", "Blue team internals", "AST localization, surgical synthesis, Gate 0, containment"),
    ("20–21", "Adjudication", "dual-gate evaluator and the convergence invariant"),
    ("22–23", "Evidence & observation", "ablation methodology, tracer schema, dashboard, doctor"),
    ("24–25", "Reproduce it", "five commands; what to watch for"),
]
for i, (n, t, sub) in enumerate(items):
    yy = 1.85 + i * 0.62
    box(s, 0.85, yy, 0.85, 0.5, PANEL2, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.85, yy + 0.07, 0.85, 0.35, n, 13, AMBER, True, PP_ALIGN.CENTER, MONO)
    txt(s, 1.95, yy + 0.02, 4.2, 0.4, t, 14, WHITE, True)
    txt(s, 6.3, yy + 0.05, 6.2, 0.4, sub, 11, MUT)
footer(s, P2)

# =====================================================================
# S15 — 7-LAYER ARCHITECTURE
# =====================================================================
s = slide()
header(s, "Architecture", "Seven layers: base first, specialization on top", P2)
layers = [
    ("L7", "EVIDENCE", "ablation benchmark — isolated trials, 4 configurations", AMBER, "benchmark_runner.py"),
    ("L6", "OBSERVATION", "pre-flight doctor · trajectory tracer · 5-tab dashboard", AMBER, "aegis/monitor/ · core/doctor.py"),
    ("L5", "ORCHESTRATION", "closed-loop state machine to sound convergence", MUT, "aegis/core/orchestrator.py"),
    ("L4", "ADJUDICATION", "dual-gate referee: PoC+ mutation gate + golden-path gate", GREEN, "aegis/evaluator/"),
    ("L3", "REPAIR · BLUE", "AST localization + surgical RFC-cited patch synthesis", BLUE, "aegis/blue/agent.py"),
    ("L2", "ATTACK · RED", "mutation catalog → probes → adaptive planner + telemetry", RED, "aegis/red/"),
    ("L1", "SAFE HANDS", "path containment · AST syntax gate · snapshot/rollback", GREEN, "aegis/blue/aci.py"),
    ("L0", "FOUNDATION", "typed state contracts · threat matrix · target + ground-truth fixtures", MUT, "aegis/core/state.py · config.py · testbed/"),
]
ly, lh, lg = 1.78, 0.585, 0.095
for i, (n, name, desc, col, f) in enumerate(layers):
    yy = ly + i * (lh + lg)
    p = box(s, 0.85, yy, 11.6, lh, PANEL, line=LINE)
    box(s, 0.85, yy, 0.9, lh, PANEL2, rounded=False)
    txt(s, 0.85, yy + 0.11, 0.9, 0.35, n, 14, col, True, PP_ALIGN.CENTER, MONO)
    txt(s, 1.95, yy + 0.14, 2.6, 0.35, name, 13, WHITE, True)
    txt(s, 4.7, yy + 0.16, 4.7, 0.35, desc, 11, MUT)
    txt(s, 9.55, yy + 0.16, 2.8, 0.35, f, 10, DIM, False, PP_ALIGN.RIGHT, MONO)
txt(s, 0.85, 6.75, 11.6, 0.3, "Each layer speaks only to its neighbors via typed contracts (L0). Specialization (L2–L4) sits on a general base (L0–L1) and is observed from above (L5–L7).", 11, MUT)
footer(s, P2)

# =====================================================================
# S16 — STATE MACHINE
# =====================================================================
s = slide()
header(s, "Orchestration", "The closed loop: every branch is a recorded status", P2)
# row 1
by, bh = 1.9, 1.0
b1 = box(s, 0.85, by, 2.6, bh, RED_T, line=RED); label(b1, "PLAN", "rank vectors:\nseverity + endpoint boost", tcolor=RED, tsz=15, ssz=10.5)
arrow(s, 3.55, by + 0.4, 0.45, 0.28, AMBER)
b2 = box(s, 4.1, by, 3.0, bh, RED_T, line=RED); label(b2, "EXPLOIT", "base payload + all mutation\nvariants of that class", tcolor=RED, tsz=15, ssz=10.5)
arrow(s, 7.2, by + 0.4, 0.45, 0.28, AMBER)
d1 = box(s, 7.75, by - 0.12, 2.1, 1.25, PANEL2, line=AMBER, shape=MSO_SHAPE.DIAMOND); label(d1, "exploit?", tsz=13, tcolor=AMBER)
arrow(s, 9.95, by + 0.4, 0.45, 0.28, AMBER)
b3 = box(s, 10.5, by, 2.0, bh, BLUE_T, line=BLUE); label(b3, "PATCH", "Blue synthesizes +\nGate-0 applies (≤3)", tcolor=BLUE, tsz=15, ssz=10.5)
# NO branch
arrow(s, 8.55, by + 1.05, 0.26, 0.5, MUT, direction="down")
n1 = box(s, 7.35, 3.55, 2.55, 0.75, PANEL, line=LINE); label(n1, "NO → BLOCKED_ORIGINALLY", "already secure · record · next vector", tsz=11, ssz=9.5, tcolor=MUT, scolor=DIM)
# down to gate
arrow(s, 11.35, by + bh + 0.05, 0.26, 0.5, AMBER, direction="down")
g1 = box(s, 10.5, 3.55, 2.0, 0.85, GREEN_T, line=GREEN); label(g1, "DUAL GATE", "security + functional", tcolor=GREEN, tsz=13, ssz=9.5)
# row 2
d2 = box(s, 7.75, 4.7, 2.1, 1.1, PANEL2, line=GREEN, shape=MSO_SHAPE.DIAMOND); label(d2, "both pass?", tsz=12, tcolor=GREEN)
arrow(s, 8.7, 3.95, 0.26, 0.5, GREEN, direction="down")
c1 = box(s, 5.3, 5.6, 3.2, 0.7, GREEN_T, line=GREEN); label(c1, "YES → COMMIT", "PATCHED_AND_VERIFIED · next vector", tsz=11.5, tcolor=GREEN, ssz=9.5)
arrow(s, 7.75, 5.2, 0.3, 0.3, GREEN, direction="right")
# rotate: use left arrow from c1
# rollback
r1 = box(s, 1.0, 5.6, 3.2, 0.7, RED_T, line=RED); label(r1, "NO → ROLLBACK + RETRY", "snapshot restored · attempt ≤ 3", tsz=11.5, tcolor=RED, ssz=9.5)
arrow(s, 7.75, 5.2, 0.3, 0.3, RED, direction="left")
# end
e1 = box(s, 1.0, 4.7, 3.2, 0.8, PANEL, line=AMBER); label(e1, "SOUND CONVERGENCE", "0 unresolved ∧ all vectors remediated", tsz=11, tcolor=AMBER, ssz=9.5)
arrow(s, 4.25, 4.98, 0.5, 0.24, AMBER)
txt(s, 4.75, 5.95, 4.0, 0.35, "after all vectors:", 10.5, DIM, False, PP_ALIGN.CENTER)
footer(s, P2)

# =====================================================================
# S17 — RED INTERNALS
# =====================================================================
s = slide()
header(s, "Attack layer", "Red team internals: deterministic, fully audited", P2)
panel(s, 0.85, 1.8, 6.35, 4.75, "Mutation catalog — 17 variants", accent=RED)
rows = [
    ["Flaw class", "Variant", "What it tests"],
    ["Redirect", "5 — plain / %2e%2e / double-encoded / subdomain / param-pollution", "does the whitelist compare exactly?"],
    ["PKCE", "4 — omitted / empty / mismatch / plain downgrade", "is the proof step actually enforced?"],
    ["State", "3 — missing / low-entropy / whitespace", "is the anti-CSRF tag checked?"],
    ["Scope", "4 — space-delimited / write:all / wildcard / root", "can you widen consent after the fact?"],
    ["Replay", "1 — double redemption", "is the code truly one-time?"],
]
gf = s.shapes.add_table(6, 3, Inches(1.1), Inches(2.4), Inches(5.85), Inches(3.9))
t = gf.table
t.columns[0].width = Inches(1.15); t.columns[1].width = Inches(3.15); t.columns[2].width = Inches(1.55)
for i in range(6):
    t.rows[i].height = Inches(0.62 if i else 0.42)
    for j in range(3):
        c = t.cell(i, j)
        if i == 0:
            set_cell(c, rows[0][j], 10.5, True, AMBER, PP_ALIGN.LEFT, PANEL2)
        else:
            set_cell(c, rows[i][j], 10, i == 1 and j == 0, WHITE if j == 0 else MUT, PP_ALIGN.LEFT, PANEL if i % 2 else BG)
panel(s, 7.5, 1.8, 5.0, 4.75, "Adaptive planner (no LLM)", accent=AMBER)
bullets(s, 7.8, 2.45, 4.45, 3.9, [
    ("Severity weights: CRITICAL 100 · HIGH 75 · MEDIUM 50 · LOW 25", True, WHITE, 12.5),
    ("Endpoint correlation: a successful exploit on /token adds +20 to sibling /token classes — the attacker follows its own success", False, WHITE, 12),
    ("Remediated classes are excluded from the candidate set", False, WHITE, 12),
    ("Every ranking is recorded: base score, boost, reason, full candidate order — the dashboard's 'Adaptive Decision Graph' renders exactly this", False, GREEN, 12),
], 12, 8)
footer(s, P2)

# =====================================================================
# S18 — VECTOR MATRIX
# =====================================================================
s = slide()
header(s, "Attack layer", "The threat matrix: five classes, RFC-anchored", P2)
rows = [
    ["Vector", "Layman name", "Severity", "Endpoint", "RFC anchor", "Core claim"],
    ["OAUTH-REDIRECT-\nTRAVERSAL", "Redirect leakage", "CRITICAL", "/authorize", "RFC 6749 §3.1.2, RFC 6819", "redirect_uri must equal a registered value"],
    ["OAUTH-CODE-REPLAY", "Code replay", "CRITICAL", "/token", "RFC 6749 §4.1.2", "codes are one-time; redemption marks them used"],
    ["OAUTH-PKCE-\nDOWNGRADE", "PKCE downgrade", "HIGH", "/token", "RFC 7636 §4.2, §4.4.1", "verifier mandatory; S256 only"],
    ["OAUTH-SCOPE-\nESCALATION", "Scope creep", "HIGH", "/token", "RFC 6749 §3.3", "granted scope ⊆ consented scope"],
    ["OAUTH-STATE-CSRF", "Login forgery", "HIGH", "/authorize", "RFC 6749 §10.12", "state present + minimum entropy"],
]
gf = s.shapes.add_table(6, 6, Inches(0.85), Inches(1.9), Inches(11.6), Inches(3.6))
t = gf.table
for j, w in enumerate([2.6, 1.8, 1.2, 1.4, 2.2, 2.4]):
    t.columns[j].width = Inches(w)
for i in range(6):
    t.rows[i].height = Inches(0.62 if i else 0.45)
    for j in range(6):
        c = t.cell(i, j)
        if i == 0:
            set_cell(c, rows[0][j].replace("\n", " "), 11, True, AMBER, PP_ALIGN.LEFT, PANEL2)
        else:
            sev = rows[i][2]
            colr = RED if sev == "CRITICAL" else AMBER
            set_cell(c, rows[i][j], 10.5, j in (0, 1), WHITE if j in (0, 1) else (colr if j == 2 else MUT),
                     PP_ALIGN.LEFT, PANEL if i % 2 else BG, MONO if j in (0, 3, 4) else FONT)
txt(s, 0.85, 5.85, 11.5, 0.7,
    "The matrix is data, not code: adding a sixth class is a dict entry in config.py — probes, planner, gates, dashboard, and benchmark all pick it up from there.",
    13, MUT, False, ls=1.2)
footer(s, P2)

# =====================================================================
# S19 — BLUE INTERNALS / ACI
# =====================================================================
s = slide()
header(s, "Repair layer", "Blue team internals: safe hands before cleverness", P2)
steps = [
    ("1 · LOCATE", "AST scan of the target module:\nfind route handlers by decorator,\nline range, signature", BLUE, BLUE_T),
    ("2 · SYNTHESIZE", "regex-anchored context match →\ninsert RFC-cited guard block\ntailored to the handler", AMBER, AMBER_T),
    ("3 · GATE 0", "ast.parse() the whole file\nbefore any write;\nsyntax error ⇒ reject", RED, RED_T),
    ("4 · APPLY", "snapshot original, then\natomic single-block replace\n+ unified diff for review", GREEN, GREEN_T),
    ("5 · ROLLBACK", "dual-gate failure restores the\nsnapshot verbatim;\nattempt counter advances", MUT, PANEL),
]
for i, (t, sub, col, cf) in enumerate(steps):
    x = 0.85 + i * 2.42
    b = box(s, x, 2.0, 2.2, 1.9, cf, line=LINE)
    label(b, t, sub, tcolor=col, tsz=13, ssz=10, align=PP_ALIGN.LEFT)
    if i < 4:
        arrow(s, x + 2.24, 2.82, 0.16, 0.26, AMBER)
panel(s, 0.85, 4.35, 11.6, 1.75, "Containment: the hands can't leave the room", accent=GREEN)
bullets(s, 1.2, 4.6, 11.0, 1.4, [
    ("Every path is realpath-resolved and must stay under the workspace root (os.path.commonpath check) — symlink escapes and ../ climbs raise PermissionError. Unit-tested.", False, WHITE, 12),
    ("Gate 0 is a hard pre-write syntax check; failed candidate patches never touch the target's behavior. Rollback is a verbatim snapshot restore, not a reverse-diff.", False, MUT, 11.5),
], 12, 8)
footer(s, P2)

# =====================================================================
# S20 — DUAL GATE EVALUATOR
# =====================================================================
s = slide()
header(s, "Adjudication", "The dual gate: two oracles, one commit decision", P2)
panel(s, 0.85, 1.85, 5.6, 2.6, "GATE 1 · SECURITY (PoC+)", accent=RED)
bullets(s, 1.15, 2.5, 5.0, 1.8, [
    ("Re-run the entire mutation suite of the just-patched class", False, WHITE, 12.5),
    ("All 17-style variants must now FAIL — a patch that only kills the demo payload is rejected", False, MUT, 12),
    ("Counted: mutations_blocked / mutations_tested", False, MUT, 11.5),
], 12.5, 7)
panel(s, 6.75, 1.85, 5.75, 2.6, "GATE 2 · FUNCTIONAL (golden path)", accent=GREEN)
bullets(s, 7.05, 2.5, 5.15, 1.8, [
    ("Legit PKCE authorization-code login, end to end", False, WHITE, 12.5),
    ("Bearer-token access to protected /userinfo", False, MUT, 12),
    ("Any failure = the 'security' fix broke the product ⇒ reject + rollback", False, MUT, 11.5),
], 12.5, 7)
box(s, 0.85, 4.75, 11.6, 0.95, PANEL2, line=AMBER)
txt(s, 1.2, 4.95, 11.0, 0.35, "Commit ⇔ Gate 1 PASS ∧ Gate 2 PASS", 15, AMBER, True, PP_ALIGN.CENTER)
txt(s, 1.2, 5.35, 11.0, 0.3, "…or rollback and retry (max 3 attempts), else the class lands in unresolved_vectors.", 11.5, MUT, False, PP_ALIGN.CENTER)
txt(s, 0.85, 5.95, 11.6, 0.7,
    "Why both: Gate 1 alone rewards over-blocking ('just deny the endpoint'), Gate 2 alone rewards shallow fixes ('silence the test'). Their intersection is what makes the repair trustworthy — Config B in the benchmark is Gate 2's cost when Gate 1 is missing.",
    12, MUT, False, ls=1.2)
footer(s, P2)

# =====================================================================
# S21 — STATE CONTRACTS / CONVERGENCE
# =====================================================================
s = slide()
header(s, "Adjudication", "Typed contracts and the convergence invariant", P2)
panel(s, 0.85, 1.85, 5.9, 4.55, "The shared vocabulary (L0)", accent=MUT)
rows = [
    ["Contract", "Carries"],
    ["VulnerabilityProof", "payload, endpoint, status, base + mutation counts, PoC summary"],
    ["PatchResult", "unified diff, target file, lines changed, Gate-0 flag"],
    ["DualGateResult", "per-gate pass/fail, mutation block counts, combined verdict"],
    ["RoundHistory", "one loop iteration: decision, proof, patch, gate, status"],
    ["AegisState", "pending / remediated / unresolved vectors + history"],
]
gf = s.shapes.add_table(5, 2, Inches(1.15), Inches(2.45), Inches(5.3), Inches(3.6))
t = gf.table
t.columns[0].width = Inches(2.2); t.columns[1].width = Inches(3.1)
for i in range(5):
    t.rows[i].height = Inches(0.55 if i else 0.4)
    for j in range(2):
        c = t.cell(i, j)
        if i == 0:
            set_cell(c, rows[0][j], 10.5, True, AMBER, PP_ALIGN.LEFT, PANEL2)
        else:
            set_cell(c, rows[i][j], 10.5, j == 0, WHITE if j == 0 else MUT, PP_ALIGN.LEFT,
                     PANEL if i % 2 else BG, MONO if j == 0 else FONT)
panel(s, 7.0, 1.85, 5.5, 4.55, "Sound convergence (the exit condition)", accent=GREEN)
box(s, 7.3, 2.5, 4.9, 1.1, GREEN_T, line=GREEN)
txt(s, 7.55, 2.68, 4.5, 0.8, "converged ⇔ unresolved = ∅  ∧  remediated = all active vectors", 13.5, GREEN, True, PP_ALIGN.CENTER, MONO)
bullets(s, 7.3, 3.85, 4.9, 2.3, [
    ("Retry budget: 3 repair attempts per class, then it's recorded unresolved — the loop terminates", False, MUT, 11.5),
    ("Statuses: BLOCKED_ORIGINALLY · PATCHED_AND_VERIFIED · MAX_ATTEMPTS_EXCEEDED", False, WHITE, 11.5),
    ("'Already secure' is a first-class outcome, not a skip", False, MUT, 11.5),
], 11.5, 8)
footer(s, P2)

# =====================================================================
# S22 — ABLATION METHODOLOGY
# =====================================================================
s = slide()
header(s, "Evidence", "How the numbers are earned: ablation, not assertion", P2)
configs = [
    ("A · RED ONLY", "Isolates discovery", "no repair at all — measures what finding looks like without fixing", AMBER, AMBER_T),
    ("B · NO DUAL GATE", "Isolates verification", "naive 'silence the symptom' patch — measures real functional regression", RED, RED_T),
    ("C · STATIC GATE", "Isolates mutation depth", "single-payload check — measures real variant leakage", AMBER, AMBER_T),
    ("D · FULL SYSTEM", "The claim under test", "adaptive + AST + dual gate, end to end", GREEN, GREEN_T),
]
for i, (t, iso, sub, col, cf) in enumerate(configs):
    x = 0.85 + i * 3.0
    b = box(s, x, 1.9, 2.75, 1.9, cf, line=LINE)
    label(b, t, f"{iso}\n{sub}", tcolor=col, tsz=13, ssz=9.5)
    if i < 3:
        arrow(s, x + 2.79, 2.7, 0.18, 0.28, MUT)
panel(s, 0.85, 4.15, 11.6, 2.3, "Methodology details", accent=GREEN)
bullets(s, 1.2, 4.4, 11.0, 1.9, [
    ("Isolation: each trial copies the immutable ground-truth fixture into an ephemeral workspace — no cross-trial contamination (realpath + symlink containment enforced).", False, WHITE, 12),
    ("Metrics are computed from trial telemetry where it matters (Config D's convergence and mutation counts); regressions for B/C are measured by the golden-path suite, not asserted.", False, WHITE, 12),
    ("Known honesty limit, flagged in code review: B/C narrative strings (re-exploit rates, footer claims) are hardcoded rather than derived — tightening these is a roadmap item, and we say so instead of hiding it.", True, AMBER, 12),
], 12, 7)
footer(s, P2)

# =====================================================================
# S23 — OBSERVABILITY STACK
# =====================================================================
s = slide()
header(s, "Observation layer", "What the system writes for you to audit", P2)
panel(s, 0.85, 1.85, 4.5, 4.55, "Trajectory JSON (audit record)", accent=AMBER)
box(s, 1.1, 2.45, 4.0, 3.6, PANEL2, shape=MSO_SHAPE.RECTANGLE)
txt(s, 1.3, 2.6, 3.6, 3.3,
    "{\n  steps: [{step_id, event_type,\n    vector_id, data…}],\n  rounds: [{ adaptive_decision:\n      {total_score, base,\n       boost, reason, ranking[]},\n    patch, gate_result }],\n  summary: { soundly_converged,\n    totals… },\n  host_metadata: { os, python }\n}",
    10.5, MUT, False, PP_ALIGN.LEFT, MONO, ls=1.15)
panel(s, 5.55, 1.85, 3.6, 4.55, "Dashboard tabs", accent=BLUE)
bullets(s, 5.85, 2.5, 3.1, 3.8, [
    ("1 · Adaptive Decision Graph", True, BLUE, 12),
    ("   rankings + boosts + rationale", False, MUT, 10.5),
    ("2 · AST Patches & Diffs", True, BLUE, 12),
    ("   syntax-highlighted unified diffs", False, MUT, 10.5),
    ("3 · PoC+ & Gate Matrix", True, GREEN, 12),
    ("   17 variants × pass/fail, live", False, MUT, 10.5),
    ("4 · Environment & Pre-Flight", True, AMBER, 12),
    ("5 · Trajectory & Audit Trail", True, AMBER, 12),
], 12, 4)
panel(s, 9.35, 1.85, 3.1, 4.55, "Doctor checks", accent=GREEN)
bullets(s, 9.6, 2.5, 2.65, 3.8, [
    ("Python runtime ≥ 3.10", False, WHITE, 11.5),
    ("workspace read/write/delete", False, WHITE, 11.5),
    ("target AST parses clean", False, WHITE, 11.5),
    ("route handlers discovered", False, WHITE, 11.5),
    ("golden-path baseline green", False, WHITE, 11.5),
], 11.5, 9)
footer(s, P2)

# =====================================================================
# S24 — REPRODUCE
# =====================================================================
s = slide()
header(s, "Reproduce", "Five commands from a fresh clone", P2)
cmds = [
    ("pip install -r requirements.txt", "deps: fastapi, httpx, uvicorn, pydantic, pytest"),
    ("python main.py --doctor", "pre-flight: runtime, permissions, AST, routes, baseline"),
    ("python main.py", "the full loop → umbrella_trajectory.json + dashboard.html"),
    ("python main.py --serve --port 8080", "live dashboard + inspector"),
    ("python benchmark_runner.py", "4-configuration ablation harness"),
    ("pytest tests/ -v", "9 tests: ACI containment, syntax gate, mutations, convergence"),
]
box(s, 0.85, 1.85, 7.9, 4.6, PANEL2, shape=MSO_SHAPE.RECTANGLE)
yy = 2.1
for c, hint in cmds:
    txt(s, 1.15, yy, 5.5, 0.35, c, 14, GREEN, False, PP_ALIGN.LEFT, MONO)
    txt(s, 1.15, yy + 0.33, 7.3, 0.3, hint, 10.5, MUT)
    yy += 0.72
panel(s, 9.0, 1.85, 3.45, 4.6, "Read me before running", accent=AMBER)
bullets(s, 9.25, 2.5, 3.0, 3.8, [
    ("The committed testbed app ships already-hardened, so a fresh main.py run shows 5 × 'blocked originally' — that's correct behavior, not a bug.", False, MUT, 11),
    ("The benchmark resets the fixture to the vulnerable ground truth first, which is when the loop's repair is visible.", True, AMBER, 11),
    ("Run against isolates only — the repo's own hard rule: never point it at production.", True, RED, 11),
], 11, 8)
footer(s, P2)

# =====================================================================
# S25 — CLOSING
# =====================================================================
s = slide()
box(s, 0, 0, 13.333, 7.5, BG, rounded=False)
box(s, 0, 5.4, 13.333, 0.06, PANEL2, rounded=False)
txt(s, 0.9, 1.6, 11.5, 1.0, "Umbrella", 64, WHITE, True)
txt(s, 0.9, 2.85, 11.5, 0.5, "Continuous proof of identity security: attack, repair, verify — on every deploy.", 20, MUT)
txt(s, 0.9, 3.7, 11.5, 0.9,
    "The next hardening step is generalizing patch synthesis beyond the reference target;\nuntil then, the loop, gates, and evidence trail are complete and reproducible.",
    14, MUT, False, ls=1.3)
box(s, 0.9, 5.85, 6.4, 0.75, PANEL2, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
txt(s, 1.2, 6.03, 6.0, 0.4, "github.com/CrispyDEV3loper/umbrella", 14, AMBER, True, PP_ALIGN.LEFT, MONO)
txt(s, 0.9, 6.85, 11.5, 0.3, "Questions?", 13, MUT)
footer(s, P2)

OUT = "Umbrella_SaaS_Pitch.pptx"
prs.save(OUT)
print(f"saved {OUT} with {len(prs.slides.__iter__().__self__._sldIdLst)} slides" if False else f"saved {OUT} · slides={len(prs.slides._sldIdLst)}")
