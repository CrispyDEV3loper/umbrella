"""
Script to generate the publication-grade 'Zero-to-Hero' Guide PDF for Project Umbrella.
Designed for readers with zero prior technical knowledge, enabling them to understand
and articulate the entire architecture, jargon, codebase, environment, and mathematical foundations.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))

        # Skip running header/footer on title cover page
        if self._pageNumber > 1:
            # Header
            self.drawString(44, 755, "PROJECT UMBRELLA: THE ZERO-TO-HERO GUIDE")
            self.drawRightString(letter[0] - 44, 755, "COMPLETE CONCEPTUAL & TECHNICAL MANUAL")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.75)
            self.line(44, 747, letter[0] - 44, 747)

            # Footer
            self.line(44, 42, letter[0] - 44, 42)
            self.drawString(44, 30, "Project Umbrella -- Autonomous Adversarial Hardening for Web Identity")
            self.drawRightString(letter[0] - 44, 30, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_pdf(filename="Project_Umbrella_Complete_Guide_Zero_to_Hero.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=44,
        rightMargin=44,
        topMargin=52,
        bottomMargin=52,
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    c_primary = colors.HexColor("#1A365D")   # Deep Navy
    c_secondary = colors.HexColor("#2B6CB0") # Slate Blue
    c_text = colors.HexColor("#2D3748")      # Charcoal Body
    c_light_bg = colors.HexColor("#F7FAFC")  # Light gray-blue
    c_accent = colors.HexColor("#C53030")    # Crimson Accent
    c_green = colors.HexColor("#22543D")     # Forest Green Accent

    # Custom Typography Styles
    styles.add(ParagraphStyle(
        name="DocTitle",
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=27,
        textColor=c_primary,
        alignment=0,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        fontName="Helvetica",
        fontSize=11.5,
        leading=16,
        textColor=c_secondary,
        alignment=0,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="MetaText",
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="ChapterHeader",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="SubChapterHeader",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14.5,
        textColor=c_secondary,
        spaceBefore=9,
        spaceAfter=4,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="GuideBody",
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=c_text,
        spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="GuideBullet",
        fontName="Helvetica",
        fontSize=8.8,
        leading=13,
        textColor=c_text,
        leftIndent=14,
        firstLineIndent=-9,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="CalloutText",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#2C5282"),
    ))
    styles.add(ParagraphStyle(
        name="TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=7.8,
        leading=10,
        textColor=c_text,
    ))
    styles.add(ParagraphStyle(
        name="TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=10,
        textColor=c_primary,
    ))

    story = []

    # =========================================================================
    # COVER / HEADER & ORIENTATION
    # =========================================================================
    story.append(Paragraph("PROJECT UMBRELLA: THE ZERO-TO-HERO GUIDE", styles["DocTitle"]))
    story.append(Paragraph(
        "A Complete Pedagogical Manual: How Autonomous Adversarial AI Discovers, Exploits, "
        "Repairs, and Functionally Verifies Web Identity Protocols in Modern SaaS Backends",
        styles["DocSubtitle"]
    ))
    story.append(Paragraph(
        "<b>Audience:</b> Engineering, Product, Security & Non-Technical Evaluators &nbsp;|&nbsp; "
        "<b>Prerequisites:</b> None &nbsp;|&nbsp; <b>Branch:</b> adaptive-update &nbsp;|&nbsp; <b>Edition:</b> November 2026",
        styles["MetaText"]
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=12))

    # Executive Orientation Box
    orientation_data = [[
        Paragraph(
            "<b>How to Read This Guide:</b> This document is intentionally written from first principles. "
            "Even if you have zero background in computer security, cryptography, or automated coding agents, "
            "this guide will build your understanding step-by-step. By the end of this manual, you will understand "
            "every term (AST, ACI, OAuth, PKCE, Dual-Gate, Fuzzing), know exactly what every file in the codebase does, "
            "understand the real-world SaaS environments it protects, and be able to explain the entire system as if you built it yourself.",
            styles["CalloutText"]
        )
    ]]
    orientation_table = Table(orientation_data, colWidths=[letter[0] - 88])
    orientation_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
        ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#BEE3F8")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(orientation_table)
    story.append(Spacer(1, 12))

    # =========================================================================
    # CHAPTER 1: THE FUNDAMENTAL PROBLEM (THE SAAS IDENTITY CRISIS)
    # =========================================================================
    story.append(Paragraph("Chapter 1: The Layman's Mental Model (Why Umbrella Exists)", styles["ChapterHeader"]))
    story.append(Paragraph(
        "Imagine you pull up to an upscale hotel and hand your car to the valet. You do not hand the valet your master house keys, "
        "your passport, or your bank cards. You hand them a specialized <b>valet key</b> that allows them to start the car and park it, "
        "but cannot open your locked glove compartment or the trunk. In the digital world, this valet key is called <b>OAuth 2.0</b>.",
        styles["GuideBody"]
    ))
    story.append(Paragraph(
        "Whenever you click a button that says <i>'Sign in with Google'</i>, <i>'Connect with Slack'</i>, or <i>'Link your GitHub repository'</i>, "
        "your application is using OAuth 2.0 and <b>OpenID Connect (OIDC)</b>. Instead of typing your password into every single website, you prove "
        "your identity to an Identity Provider (like Google or Okta), which hands a temporary digital ticket (an <i>Authorization Code</i> and <i>Access Token</i>) "
        "back to the application.",
        styles["GuideBody"]
    ))

    story.append(Paragraph("1.1 What Kinds of SaaS Platforms Depend on This?", styles["SubChapterHeader"]))
    story.append(Paragraph(
        "Umbrella is not designed for static personal websites. It is purpose-built to protect modern, complex, multi-tenant cloud software:",
        styles["GuideBody"]
    ))
    story.append(Paragraph(
        "&bull; <b>B2B Enterprise SaaS Applications:</b> Tools like Notion, Figma, Datadog, or Jira that connect to enterprise Single Sign-On (SSO) "
        "gateways (Okta, WorkOS, Ping Identity, Microsoft Entra ID). A flaw here allows an attacker to log in as an enterprise administrator.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>Multi-Tenant Integration Platforms:</b> Applications that integrate with third-party ecosystems (e.g., a Shopify analytics app "
        "accessing store sales, a Slack bot reading team channels, or a CRM syncing Salesforce records). A protocol flaw allows rogue apps to steal customer data.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>Cloud Microservice Mesh Architectures:</b> Modern software backends where dozens of internal microservices communicate by exchanging "
        "and validating digital tokens. If token validation is lax, one compromised internal container can impersonate any user across the whole company.",
        styles["GuideBullet"]
    ))

    story.append(Paragraph("1.2 The Two Fatal Traps in Modern Automated Security", styles["SubChapterHeader"]))
    story.append(Paragraph(
        "Why can't companies just use existing tools to keep these integrations safe? Because current technology falls into two disastrous traps:",
        styles["GuideBody"]
    ))
    story.append(Paragraph(
        "1. <b>The 'Bug Silencing' Trap:</b> When standard AI coding assistants (or automated program repair tools) try to fix a security flaw, "
        "they frequently take the easiest route: they throw a blanket error, delete the route, or disable the parameter. Technically, the attacker is blocked, "
        "but legitimate users can no longer log in! The security flaw was 'silenced' by destroying the software's functionality.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "2. <b>The 'Shallow Patch' Trap:</b> Human developers and naive tools usually write patches that block only the exact string the hacker used. "
        "If a hacker attacked using <code>/../../attacker</code>, the developer writes code that checks for <code>/../</code>. The hacker simply mutates "
        "their payload to URL-encoded characters (<code>%2e%2e/</code>) or parameter pollution, and the door swings wide open again.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "<b>Project Umbrella solves both traps simultaneously:</b> It pairs an offensive AI (Red Agent) that attacks with mutating payloads, "
        "a defensive AI (Blue Agent) that repairs the source code structurally, and a strict judge (Dual-Gate Evaluator) that verifies the flaw is gone "
        "<b>without breaking legitimate user logins</b>.",
        styles["GuideBody"]
    ))

    # =========================================================================
    # CHAPTER 2: PREREQUISITE DICTIONARY (JARGON DEMYSTIFIED)
    # =========================================================================
    story.append(Spacer(1, 14))
    story.append(Paragraph("Chapter 2: The Prerequisite Dictionary (Technical Jargon Demystified)", styles["ChapterHeader"]))
    story.append(Paragraph(
        "To discuss Project Umbrella with total mastery, you need to understand six fundamental concepts. Below is the plain-English translation of each:",
        styles["GuideBody"]
    ))

    jargon_table_data = [
        [
            Paragraph("Technical Term", styles["TableHeader"]),
            Paragraph("Plain-English Analogy & Real Meaning", styles["TableHeader"]),
            Paragraph("Why Project Umbrella Needs It", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>AST</b><br/>(Abstract Syntax Tree)", styles["TableCellBold"]),
            Paragraph("<b>The Sentence Diagram of Code:</b> When a computer reads code, it doesn't see raw text; it builds a grammatical tree of functions, parameters, and if-statements. Just like analyzing a sentence's subject, verb, and object.", styles["TableCell"]),
            Paragraph("Text search-and-replace is brittle and causes typos. Umbrella uses Python's native AST parser to locate the exact route handler function and inject precise security guards without breaking code syntax.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>ACI</b><br/>(Agent-Computer Interface)", styles["TableCellBold"]),
            Paragraph("<b>The Robotic Operating Theater:</b> A specialized, secure toolkit that allows an AI agent to inspect files, take snapshots, make surgical incisions, and stitch files back up with strict safety barriers.", styles["TableCell"]),
            Paragraph("Prevents the AI from accidentally escaping its sandbox or corrupting files. If a repair fails, the ACI instantly rolls back the file to its clean pre-attack state.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>PKCE</b><br/>(Proof Key for Code Exchange)", styles["TableCellBold"]),
            Paragraph("<b>The Secret Handshake:</b> Pronounced 'pixy'. A cryptographic secret code sent during login to prove that the mobile app or browser requesting the token is the exact same one that started the login.", styles["TableCell"]),
            Paragraph("Without PKCE, malicious apps sitting on the user's phone can intercept the authorization code and steal their account. Umbrella tests and enforces strict PKCE validation.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>PoC+ & Mutation Fuzzing</b>", styles["TableCellBold"]),
            Paragraph("<b>The Sneaky Lockpicker:</b> A standard Proof-of-Concept (PoC) tests one lockpick. PoC+ tests 17 different lockpicks (plain, URL-encoded, double-encoded, whitespace, and parameter pollution).", styles["TableCell"]),
            Paragraph("Prevents 'shallow patches'. Blue's patch is rejected unless it blocks 100% of all sneaky mutation variations, not just the single basic test string.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Dual-Gate Adjudication</b>", styles["TableCellBold"]),
            Paragraph("<b>The Two Bouncers at the Door:</b> A verification court with two opposing requirements. Gate 1 checks that all attacks fail. Gate 2 checks that legitimate users can still log in smoothly.", styles["TableCell"]),
            Paragraph("Guarantees that security patches never cause functional regressions. If a patch breaks login functionality, it is automatically thrown in the trash and rolled back.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Sound Convergence</b>", styles["TableCellBold"]),
            Paragraph("<b>The Mathematical Finish Line:</b> A rigorous state condition proving the audit is genuinely complete. It requires that every single known threat is remediated and zero vulnerabilities remain.", styles["TableCell"]),
            Paragraph("Prevents premature exit or false-positive reporting. Umbrella cannot claim success until 100% of the threat matrix is proven secure and functional.", styles["TableCell"]),
        ],
    ]
    jargon_table = Table(jargon_table_data, colWidths=[90, 215, 215])
    jargon_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(jargon_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # CHAPTER 3: THE 5 CATASTROPHIC ATTACK VECTORS
    # =========================================================================
    story.append(Paragraph("Chapter 3: The 5 Catastrophic OAuth Vulnerabilities Explained", styles["ChapterHeader"]))
    story.append(Paragraph(
        "Umbrella focuses on five distinct failure modes in Web Identity protocols. Here is what each attack looks like in plain terms:",
        styles["GuideBody"]
    ))

    story.append(Paragraph(
        "&bull; <b>1. Redirect URI Path Traversal (`OAUTH-REDIRECT-TRAVERSAL`):</b> When the user logs in, the identity provider sends them back "
        "to a pre-agreed URL (e.g., <code>https://my-saas-app.com/callback</code>). If the backend uses a sloppy check like <code>startswith('https://my-saas-app.com')</code>, "
        "an attacker sends <code>https://my-saas-app.com/callback/../../attacker_leak</code> or a fake subdomain <code>my-saas-app.com.evil.com</code>. "
        "The login code is routed straight to the attacker's server, handing over the user's account.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>2. Authorization Code Replay (`OAUTH-CODE-REPLAY`):</b> When you redeem a movie ticket at the box office, the attendant tears it in half "
        "so you cannot hand it to your friend to see a second movie for free. An Authorization Code is supposed to be a single-use ticket. If the server "
        "forgets to mark it as consumed, an attacker who eavesdropped on the code can redeem it again and generate a second active session.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>3. PKCE Method Downgrade & Omission (`OAUTH-PKCE-DOWNGRADE`):</b> PKCE requires mobile and browser clients to send a cryptographic hash (S256). "
        "In a downgrade attack, the attacker intercepts the request and strips out the secret code, or changes the method to 'plain' (unencrypted text). "
        "If the backend permits this downgrade, the attacker can hijack the authorization flow without knowing the secret key.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>4. Scope Escalation (`OAUTH-SCOPE-ESCALATION`):</b> You download a third-party calendar widget that asks for permission to <i>'read profile'</i>. "
        "When the widget connects to the token server, it secretly appends <code>scope='read:profile admin'</code>. If the server does not enforce that the granted scopes "
        "are a strict subset of what the user agreed to, the calendar widget suddenly gets full administrator access over the SaaS company.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>5. State Parameter Omission & CSRF (`OAUTH-STATE-CSRF`):</b> When you start a login handshake, your app creates a random cryptographic token (the <i>state</i>) "
        "and sends it along. When Google sends you back, it includes that exact token. If the backend doesn't check this token, an attacker can trick your browser "
        "into logging into the attacker's account, linking your credit card or private files to the attacker's profile.",
        styles["GuideBullet"]
    ))

    # =========================================================================
    # CHAPTER 4: OPERATIONAL ENVIRONMENT & SAAS LIFECYCLE
    # =========================================================================
    story.append(Spacer(1, 14))
    story.append(Paragraph("Chapter 4: Where Does Umbrella Run in the Real World?", styles["ChapterHeader"]))
    story.append(Paragraph(
        "A common point of confusion is whether Umbrella is a software library that lives inside your production database, an external cloud scanner, "
        "or an automated CI/CD pipeline robot. Here is the operational reality:",
        styles["GuideBody"]
    ))

    story.append(Paragraph("4.1 The Operational Lifecycle (Where Umbrella Sits)", styles["SubChapterHeader"]))
    story.append(Paragraph(
        "Umbrella is an <b>autonomous security-hardening harness</b> that runs during the software engineering and staging lifecycle. "
        "It acts like a crash-test dummy laboratory for code:",
        styles["GuideBody"]
    ))
    story.append(Paragraph(
        "&bull; <b>In CI/CD Pipelines (e.g. GitHub Actions, GitLab CI):</b> When a developer opens a pull request that touches authentication routes, "
        "Umbrella spins up in an isolated test runner, executes the adversarial co-evolution rounds, verifies the fix, and can automatically propose a verified PR patch.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>In Local Staging Sandboxes:</b> Security engineers run Umbrella on a dedicated staging clone or git worktree (`git worktree add ../staging-hardening`). "
        "It audits the application backend in complete isolation without risking live customer data or production uptime.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>What Systems Can It Harden?</b> Any Python web service implementing standard identity handshakes (FastAPI, Starlette, Flask, Django Ninja, LiteStar). "
        "It protects microservice backends, authorization servers, and multi-tenant SaaS integration endpoints.",
        styles["GuideBullet"]
    ))

    story.append(Paragraph("4.2 Pre-Flight Diagnostics: The 'Umbrella Doctor'", styles["SubChapterHeader"]))
    story.append(Paragraph(
        "Before launching an adversarial battle, you don't have to wonder if your environment is set up properly. Umbrella features an integrated "
        "diagnostic physician: <code>python main.py --doctor</code>. It automatically verifies five critical environment invariants:",
        styles["GuideBody"]
    ))
    story.append(Paragraph(
        "1. <b>Runtime Health:</b> Confirms Python 3.10+ is running with required standard library AST and networking packages.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "2. <b>Filesystem Containment:</b> Probes write permissions and verifies with <code>os.path.realpath()</code> that symbolic links cannot escape the repository boundary.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "3. <b>AST Parseability:</b> Compiles target backend source files into AST, validating line numbers, function bodies, and decorators without syntax errors.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "4. <b>Endpoint Discovery:</b> Automatically locates and registers where <code>/authorize</code>, <code>/token</code>, and <code>/userinfo</code> live.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "5. <b>Golden Path Baseline:</b> Confirms the target application actually works for legitimate users <i>before</i> any attacks are launched.",
        styles["GuideBullet"]
    ))

    # =========================================================================
    # CHAPTER 5: CODEBASE WALKTHROUGH SECTION-BY-SECTION
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("Chapter 5: Codebase Walkthrough (Section-by-Section)", styles["ChapterHeader"]))
    story.append(Paragraph(
        "The Umbrella codebase is located in the <code>aegis/</code> package, divided into six specialized subsystems. "
        "Here is what each section owns and why it exists:",
        styles["GuideBody"]
    ))

    codebase_table_data = [
        [
            Paragraph("Directory / Files", styles["TableHeader"]),
            Paragraph("Role & Everyday Analogy", styles["TableHeader"]),
            Paragraph("How It Operates Internally", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>aegis/core/</b><br/>`state.py`<br/>`config.py`<br/>`orchestrator.py`<br/>`doctor.py`", styles["TableCellBold"]),
            Paragraph("<b>The Brain & Referee:</b> Coordinates the turns between attacker and defender, keeping the official score.", styles["TableCell"]),
            Paragraph("Defines Pydantic schemas (VulnerabilityProof, DualGateResult). Orchestrator runs the while-loop, queries Red for attacks, invokes Blue for repairs, and checks the mathematical condition `is_soundly_converged`.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>aegis/red/</b><br/>`agent.py`<br/>`mutator.py`<br/>`probes.py`", styles["TableCellBold"]),
            Paragraph("<b>The Adaptive Attacker:</b> The elite ethical hacker probing for weaknesses with multi-variant tricks.", styles["TableCell"]),
            Paragraph("`mutator.py` crafts 17 mutation payloads. `probes.py` executes real HTTP handshakes. `agent.py` uses severity weights (100, 75) and response telemetry (+20 correlation boost for /token) to choose the next vector.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>aegis/blue/</b><br/>`aci.py`<br/>`agent.py`", styles["TableCellBold"]),
            Paragraph("<b>The Surgical Repair Team:</b> The master software engineer performing microscopic code operations.", styles["TableCell"]),
            Paragraph("`aci.py` provides the safe sandbox with AST parsing, pre-flight syntax checks, and atomic rollback. `agent.py` inspects route handlers and dynamically synthesizes RFC-compliant security guard blocks.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>aegis/evaluator/</b><br/>`dual_gate.py`<br/>`golden_path.py`", styles["TableCellBold"]),
            Paragraph("<b>The Supreme Court:</b> The incorruptible judge that enforces the Dual-Gate criteria.", styles["TableCell"]),
            Paragraph("`dual_gate.py` re-runs Red's full mutation suite (Gate 1). `golden_path.py` runs end-to-end legitimate user journeys (Gate 2). If either gate fails even 1% of the time, the candidate patch is rejected.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>aegis/monitor/</b><br/>`tracer.py`<br/>`dashboard.py`", styles["TableCellBold"]),
            Paragraph("<b>The Flight Data Recorder & Cockpit:</b> Complete visibility into every agent thought, score, and diff.", styles["TableCell"]),
            Paragraph("`tracer.py` writes structured JSON audit trails (`umbrella_trajectory.json`). `dashboard.py` exports an interactive visual HTML dashboard and live web server (`python main.py --serve`).", styles["TableCell"]),
        ],
        [
            Paragraph("<b>aegis/testbed/</b><br/>`app.py`<br/>`fixtures/`", styles["TableCellBold"]),
            Paragraph("<b>The Simulation Testing Ground:</b> The authentic web application target.", styles["TableCell"]),
            Paragraph("Contains realistic FastAPI OAuth 2.0 endpoints. Preserves pristine immutable vulnerable and hardened fixtures (`vulnerable_app_clean.py`) for reproducible benchmarking.", styles["TableCell"]),
        ],
    ]
    codebase_table = Table(codebase_table_data, colWidths=[100, 205, 215])
    codebase_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(codebase_table)

    # =========================================================================
    # CHAPTER 6: ANATOMY OF AN ADAPTIVE ATTACK & REPAIR ROUND
    # =========================================================================
    story.append(Spacer(1, 14))
    story.append(Paragraph("Chapter 6: The Anatomy of a Single Attack & Repair Round", styles["ChapterHeader"]))
    story.append(Paragraph(
        "To truly understand Project Umbrella as if you built it, follow the exact step-by-step journey of what happens during a single round "
        "(for example, Round 3 in our live run):",
        styles["GuideBody"]
    ))

    story.append(Paragraph("Step 1: Adaptive Decision & Endpoint Correlation", styles["SubChapterHeader"]))
    story.append(Paragraph(
        "In Round 2, the Red Agent successfully exploited an authorization code replay vulnerability on <code>/token</code>. "
        "When planning Round 3, the Red Agent inspects its attack history. Because <code>/token</code> proved to be vulnerable, it calculates:",
        styles["GuideBody"]
    ))
    story.append(Paragraph(
        "&bull; <code>OAUTH-STATE-CSRF</code> (hits <code>/authorize</code>): Base Score = 75, Boost = 0 -> <b>Total: 75</b><br/>"
        "&bull; <code>OAUTH-PKCE-DOWNGRADE</code> (hits <code>/token</code>): Base Score = 75, Boost = +20 -> <b>Total: 95</b><br/>"
        "Result: Red prioritizes <code>OAUTH-PKCE-DOWNGRADE</code> because compromising <code>/token</code> increases the likelihood of finding sister flaws on the same endpoint.",
        styles["CalloutText"]
    ))

    story.append(Paragraph("Step 2: Property Mutation Fuzzing (PoC+ Probing)", styles["SubChapterHeader"]))
    story.append(Paragraph(
        "Red does not simply send one invalid request. It dispatches 4 property mutations across the target: "
        "(1) complete omission of <code>code_verifier</code>, (2) empty string verifier, (3) mismatched random verifier, and (4) insecure 'plain' method downgrade. "
        "The vulnerable target allows access tokens to be issued on 2 of the 4 mutations! Red packages this telemetry into a <code>VulnerabilityProof</code>.",
        styles["GuideBody"]
    ))

    story.append(Paragraph("Step 3: AST Route Localization & Dynamic Guard Synthesis", styles["SubChapterHeader"]))
    story.append(Paragraph(
        "The Blue Agent receives the proof. It does not use brittle string replacement. It queries the ACI to parse <code>app.py</code> into an AST, "
        "locates the <code>token()</code> route handler function at line 105, and analyzes its statements. It dynamically synthesizes an RFC 7636 Section 4.2 "
        "compliant guard block enforcing mandatory S256 verification. Before saving, Gate 0 compiles the file with <code>ast.parse()</code> to confirm zero syntax errors.",
        styles["GuideBody"]
    ))

    story.append(Paragraph("Step 4: Dual-Gate Adjudication (The Moment of Truth)", styles["SubChapterHeader"]))
    story.append(Paragraph(
        "The candidate patch is written to disk, and the server module is reloaded cleanly via <code>importlib.reload()</code>. Now, the Dual-Gate evaluates:",
        styles["GuideBody"]
    ))
    story.append(Paragraph(
        "&bull; <b>Gate 1 (Security PoC+ Check):</b> Red re-executes all 4 PKCE mutations against the newly patched endpoint. "
        "<b>4 out of 4 mutations are blocked with HTTP 400 invalid_grant. Gate 1 passes (100% defense).</b>",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>Gate 2 (Functional Golden Path Check):</b> The Evaluator runs a complete, legitimate user authentication flow (PKCE S256 generation, "
        "authorization code issuance, valid token exchange, and user profile query). <b>The flow succeeds with HTTP 200. Gate 2 passes (0% regression).</b>",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "Because both gates passed simultaneously, the patch is committed permanently. The orchestrator records the vector as remediated and moves to the next turn.",
        styles["GuideBody"]
    ))

    # =========================================================================
    # CHAPTER 7: ACADEMIC INSPIRATIONS & GENEALOGY
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("Chapter 7: Academic Foundations (Standing on the Shoulders of Giants)", styles["ChapterHeader"]))
    story.append(Paragraph(
        "Project Umbrella did not invent every single concept from scratch; it unites the best ideas from breakthrough computer science research:",
        styles["GuideBody"]
    ))
    story.append(Paragraph(
        "&bull; <b>MoScan (ACM SIGSOFT ISSTA 2021):</b> Showed that Web Single Sign-On vulnerabilities must be modeled as Finite State Machines (FSMs) "
        "tested with systematic parameter mutation, inspiring Umbrella's <code>mutator.py</code>.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>SWE-agent (Princeton & Stanford University):</b> Pioneered the Agent-Computer Interface (ACI) paradigm, proving that language agents "
        "perform drastically better when given customized, safe code navigation and editing primitives.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>Vul4Py & PVBench (arXiv 2026):</b> Proved that automated program repair (APR) fails over 40% of the time unless evaluated against "
        "paired exploit and functional oracles, directly inspiring Umbrella's Dual-Gate architecture.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>Kumushi (arXiv 2026):</b> Demonstrated dynamic root-cause fault localization, preventing the 'bug silencing' problem where patches break application logic.",
        styles["GuideBullet"]
    ))
    story.append(Paragraph(
        "&bull; <b>LibCST (Meta / Instagram):</b> Inspired the pre-flight syntax validation and structural inspection of route handlers.",
        styles["GuideBullet"]
    ))

    # =========================================================================
    # CHAPTER 8: THE MASTER'S SPEECH (HOW TO EXPLAIN UMBRELLA TO ANYONE)
    # =========================================================================
    story.append(Spacer(1, 14))
    story.append(Paragraph("Chapter 8: The Master's Speech (How to Explain Umbrella to Anyone)", styles["ChapterHeader"]))
    story.append(Paragraph(
        "If you are asked in an interview, executive briefing, or engineering review to explain Project Umbrella, "
        "here are your concise scripts and answers to tough questions:",
        styles["GuideBody"]
    ))

    story.append(Paragraph("8.1 The 60-Second Elevator Pitch", styles["SubChapterHeader"]))
    pitch_box_data = [[
        Paragraph(
            "<i>\"Project Umbrella is an autonomous, co-evolutionary security framework that hardens Web Identity and OAuth integrations in modern SaaS backends. "
            "Instead of relying on scanners that only find bugs or generic AI tools that break user logins, Umbrella pairs two AI agents: an adaptive Red Agent that attacks "
            "with property-mutated payloads, and an AST-guided Blue Agent that writes surgical, RFC-compliant code repairs. "
            "Every repair is verified by a Dual-Gate system requiring 100% of attack mutations to fail and 100% of legitimate user logins to pass. "
            "The system runs in a closed loop until mathematically verified convergence, achieving complete vulnerability elimination with zero functional regressions.\"</i>",
            styles["CalloutText"]
        )
    ]]
    pitch_table = Table(pitch_box_data, colWidths=[letter[0] - 88])
    pitch_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FFF4")),
        ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#9AE6B4")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(pitch_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("8.2 How to Answer the 5 Toughest Technical Questions", styles["SubChapterHeader"]))

    qa_table_data = [
        [
            Paragraph("Tough Question", styles["TableHeader"]),
            Paragraph("Your Master-Level Technical Answer", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>Q1: Why not just use ChatGPT or Claude to write security patches?</b>", styles["TableCellBold"]),
            Paragraph("LLMs without verified feedback suffer from the 'bug silencing' trap: they write naive patches that disable endpoints or throw blanket HTTP 400 errors. Umbrella's Dual-Gate Evaluator executes real functional contracts, guaranteeing that client logins never break.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Q2: What happens if Blue writes code with a syntax error?</b>", styles["TableCellBold"]),
            Paragraph("The ACI implements Gate 0 AST Syntax Pre-Flight. Before any file write is saved to disk, it compiles the replacement through `ast.parse()`. If syntax is invalid, the patch is rejected immediately and the file is untouched.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Q3: What if Blue's patch passes the initial test but breaks under other payloads?</b>", styles["TableCellBold"]),
            Paragraph("This is the 'shallow patch' trap. Umbrella's mutator tests 17 property-based payload variations (URL encoding, parameter pollution, method downgrades). If even 1 of the 17 bypasses the patch, Gate 1 fails, triggering automatic rollback.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Q4: How do you know the system is actually finished and not just quitting?</b>", styles["TableCellBold"]),
            Paragraph("Umbrella evaluates the mathematical property `is_soundly_converged`: `len(unresolved_vectors) == 0` AND `len(remediated_vectors) == len(active_vector_ids)`. It is impossible for Umbrella to report convergence on an empty or unresolved queue.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Q5: How does the Red Agent choose attacks intelligently?</b>", styles["TableCellBold"]),
            Paragraph("Red uses an adaptive scoring formula combining base threat severity (CRITICAL=100, HIGH=75) with dynamic endpoint correlation. If an exploit breaches `/token`, all other `/token` vectors receive a +20 priority boost in the next round.", styles["TableCell"]),
        ],
    ]
    qa_table = Table(qa_table_data, colWidths=[180, 340])
    qa_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(qa_table)
    story.append(Spacer(1, 14))

    # Summary Callout at End
    final_note_data = [[
        Paragraph(
            "<b>Congratulations:</b> You now possess the complete conceptual mental model, architectural knowledge, "
            "jargon mastery, and technical deep-dive fluency required to understand, operate, and articulate Project Umbrella.",
            styles["CalloutText"]
        )
    ]]
    final_table = Table(final_note_data, colWidths=[letter[0] - 88])
    final_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
        ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#BEE3F8")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(final_table)

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Complete Zero-to-Hero Guide successfully generated: {filename}")


if __name__ == "__main__":
    build_pdf()
