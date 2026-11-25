"""
Umbrella Environment Doctor & Pre-Flight Diagnostic Suite.
Validates host environment, Python runtime requirements, file permissions,
AST parseability of target codebase, route handler discovery, and baseline functional contracts.
Inspired by standard developer diagnostics (e.g., flutter doctor, brew doctor).
"""

import sys
import os
import platform
import ast

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from aegis.blue.aci import AgentComputerInterface
from aegis.core.target import discover_route_handlers
from aegis.evaluator.golden_path import GoldenPathSuite
from fastapi.testclient import TestClient
import aegis.testbed.app as testbed_app


class DiagnosticCheck(BaseModel):
    name: str
    status: str  # "PASS", "WARN", "FAIL"
    message: str
    details: Optional[Dict[str, Any]] = None


class DiagnosticReport(BaseModel):
    all_passed: bool
    checks: List[DiagnosticCheck] = Field(default_factory=list)
    host_info: Dict[str, Any] = Field(default_factory=dict)
    discovered_routes: List[Dict[str, Any]] = Field(default_factory=list)


class UmbrellaDoctor:
    """Pre-flight validation engine for Project Umbrella environments."""

    def __init__(self, workspace_root: Optional[str] = None, target_file: str = "aegis/testbed/app.py",
                 profile: Optional[Any] = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.target_file = target_file
        self.profile = profile  # bring-your-own-app target, when set

    def get_host_info(self) -> Dict[str, Any]:
        """Collects host runtime and OS characteristics."""
        return {
            "os_name": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "python_executable": sys.executable,
            "cwd": os.getcwd(),
            "workspace_root": self.workspace_root,
        }

    def check_python_runtime(self) -> DiagnosticCheck:
        """Verifies Python 3.10+ requirement for modern typing and AST parsing."""
        major, minor = sys.version_info.major, sys.version_info.minor
        if major < 3 or (major == 3 and minor < 10):
            return DiagnosticCheck(
                name="Python Runtime Version",
                status="FAIL",
                message=f"Python 3.10+ required. Detected Python {major}.{minor}.",
            )
        return DiagnosticCheck(
            name="Python Runtime Version",
            status="PASS",
            message=f"Compatible Python runtime detected: {major}.{minor}.{sys.version_info.micro}",
            details={"version": f"{major}.{minor}.{sys.version_info.micro}"},
        )

    def check_workspace_permissions(self) -> DiagnosticCheck:
        """Verifies filesystem read/write permissions and path resolution."""
        if not os.path.isdir(self.workspace_root):
            return DiagnosticCheck(
                name="Workspace Filesystem Permissions",
                status="FAIL",
                message=f"Workspace directory not found: {self.workspace_root}",
            )

        test_file = os.path.join(self.workspace_root, ".umbrella_write_test.tmp")
        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("umbrella_healthcheck")
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            os.remove(test_file)

            if content == "umbrella_healthcheck":
                return DiagnosticCheck(
                    name="Workspace Filesystem Permissions",
                    status="PASS",
                    message="Read, write, and delete permissions confirmed on workspace.",
                    details={"path": os.path.abspath(self.workspace_root)},
                )
            return DiagnosticCheck(
                name="Workspace Filesystem Permissions",
                status="FAIL",
                message="Data integrity failure on workspace write probe.",
            )
        except Exception as e:
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except Exception:
                    pass
            return DiagnosticCheck(
                name="Workspace Filesystem Permissions",
                status="FAIL",
                message=f"Filesystem permission error: {str(e)}",
            )

    def check_target_ast_parseable(self) -> DiagnosticCheck:
        """Checks if the target application source file compiles cleanly under Python AST."""
        if self.profile is not None:
            full_path = self.profile.path  # external BYO target: no workspace containment needed
        else:
            aci = AgentComputerInterface(self.workspace_root)
            try:
                full_path = aci._resolve_path(self.target_file)
            except Exception as e:
                return DiagnosticCheck(
                    name="Target AST Syntax Parseability",
                    status="FAIL",
                    message=f"Security/Path resolution error: {str(e)}",
                )

        if not os.path.isfile(full_path):
            return DiagnosticCheck(
                name="Target AST Syntax Parseability",
                status="FAIL",
                message=f"Target file does not exist: {self.target_file}",
            )

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=full_path)
            node_count = len(list(ast.walk(tree)))
            return DiagnosticCheck(
                name="Target AST Syntax Parseability",
                status="PASS",
                message=f"Source successfully parsed into valid AST ({node_count} nodes analyzed).",
                details={"file": self.target_file, "ast_nodes": node_count},
            )
        except SyntaxError as se:
            return DiagnosticCheck(
                name="Target AST Syntax Parseability",
                status="FAIL",
                message=f"Syntax error at line {se.lineno}, col {se.offset}: {se.msg}",
                details={"lineno": se.lineno, "offset": se.offset},
            )

    def check_route_discovery_and_coverage(self) -> (DiagnosticCheck, List[Dict[str, Any]]):
        """Discovers route handlers via AST and validates OAuth endpoint presence."""
        if self.profile is not None:
            handlers = self.profile.discovered_routes
        else:
            aci = AgentComputerInterface(self.workspace_root)
            try:
                handlers = aci.find_route_handlers(self.target_file)
            except Exception as e:
                return (
                    DiagnosticCheck(
                        name="AST Route Handler Discovery",
                        status="FAIL",
                        message=f"Failed to scan route handlers: {str(e)}",
                    ),
                    [],
                )

        discovered_paths = [h.get("route_path") for h in handlers]
        expected_endpoints = ["/authorize", "/token", "/userinfo"]
        missing = [ep for ep in expected_endpoints if ep not in discovered_paths]

        if not missing:
            return (
                DiagnosticCheck(
                    name="AST Route Handler Discovery",
                    status="PASS",
                    message=f"All {len(expected_endpoints)} core OAuth endpoints discovered ({', '.join(discovered_paths)}).",
                    details={"discovered": discovered_paths, "handler_count": len(handlers)},
                ),
                handlers,
            )
        else:
            return (
                DiagnosticCheck(
                    name="AST Route Handler Discovery",
                    status="WARN",
                    message=f"Missing recommended OAuth endpoints: {missing}. Discovered: {discovered_paths}",
                    details={"discovered": discovered_paths, "missing": missing},
                ),
                handlers,
            )

    def check_golden_path_contract(self) -> DiagnosticCheck:
        """Verifies that the target application passes the Golden Path legitimate flow prior to attack rounds."""
        try:
            if self.profile is not None:
                app = self.profile.app
                profile = self.profile
            else:
                app = testbed_app.app
                profile = None
            client = TestClient(app, base_url="http://testserver")
            passed, msg = GoldenPathSuite.run_all(client, "http://testserver", profile)
            if passed:
                return DiagnosticCheck(
                    name="Baseline Functional Contract (Golden Path)",
                    status="PASS",
                    message="Legitimate authentication and token flow verified operational.",
                    details={"message": msg},
                )
            else:
                return DiagnosticCheck(
                    name="Baseline Functional Contract (Golden Path)",
                    status="FAIL",
                    message=f"Target application fails legitimate authentication initially: {msg}",
                    details={"message": msg},
                )
        except Exception as e:
            return DiagnosticCheck(
                name="Baseline Functional Contract (Golden Path)",
                status="FAIL",
                message=f"Exception during baseline functional evaluation: {str(e)}",
            )

    def diagnose(self) -> DiagnosticReport:
        """Runs the complete pre-flight diagnostic suite."""
        host_info = self.get_host_info()
        checks: List[DiagnosticCheck] = []

        checks.append(self.check_python_runtime())
        checks.append(self.check_workspace_permissions())
        checks.append(self.check_target_ast_parseable())

        route_check, discovered_routes = self.check_route_discovery_and_coverage()
        checks.append(route_check)
        checks.append(self.check_golden_path_contract())

        all_passed = all(c.status in ["PASS", "WARN"] for c in checks) and any(c.status == "PASS" for c in checks)

        return DiagnosticReport(
            all_passed=all_passed,
            checks=checks,
            host_info=host_info,
            discovered_routes=discovered_routes,
        )

    def print_report(self, report: Optional[DiagnosticReport] = None):
        """Prints a clean, human-readable terminal report."""
        report = report or self.diagnose()
        print("\n" + "=" * 70)
        print("          PROJECT UMBRELLA: ENVIRONMENT DOCTOR & PRE-FLIGHT CHECK")
        print("=" * 70)
        print(f"Host OS:             {report.host_info.get('os_name')} ({report.host_info.get('architecture')})")
        print(f"Python Runtime:      {report.host_info.get('python_version')} ({report.host_info.get('python_executable')})")
        print(f"Workspace Root:      {report.host_info.get('workspace_root')}")
        target_file = self.profile.path if self.profile else self.target_file
        print(f"Target Source File:  {target_file}")
        print("-" * 70)
        print("DIAGNOSTIC CHECKS:")

        for c in report.checks:
            if c.status == "PASS":
                symbol = "[ OK ]"
            elif c.status == "WARN":
                symbol = "[WARN]"
            else:
                symbol = "[FAIL]"
            print(f"  {symbol} {c.name.ljust(40)} -> {c.message}")

        if report.discovered_routes:
            print("-" * 70)
            print("DISCOVERED ROUTE HANDLERS:")
            for r in report.discovered_routes:
                method = r.get("method", "GET").upper()
                print(f"  * {r.get('route_path', '').ljust(20)} [{method}] -> {r.get('name')} (line {r.get('lineno')})")

        print("=" * 70)
        if report.all_passed:
            print(">>> ENVIRONMENT IS READY FOR ADVERSARIAL HARDENING.")
        else:
            print(">>> CRITICAL ENVIRONMENT ISSUES DETECTED. RESOLVE BEFORE RUNNING UMBRELLA.")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    doctor = UmbrellaDoctor()
    doctor.print_report()
