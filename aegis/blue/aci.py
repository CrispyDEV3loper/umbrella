"""
Aegis Blue Team Agent-Computer Interface (ACI).
Provides localized repository exploration, AST-level structure inspection,
syntax validation, surgical block replacement, and automated rollback capabilities.
"""

import os
import ast
from typing import List, Optional, Tuple, Dict, Any


class AgentComputerInterface:
    """Provides safe code inspection and modification tools for the Blue Agent."""

    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)
        self._backup_cache = {}

    def _resolve_path(self, relative_path: str) -> str:
        """Resolves path and enforces strict workspace containment to prevent directory traversal."""
        resolved = os.path.abspath(os.path.join(self.workspace_root, relative_path))
        # Use commonpath to prevent sibling directory prefix bypasses (e.g. /app vs /app-leak)
        if os.path.commonpath([resolved, self.workspace_root]) != self.workspace_root:
            raise PermissionError(f"Access denied outside workspace root: {relative_path}")
        return resolved

    def view_file(self, file_path: str, start_line: int = 1, end_line: int = -1) -> str:
        """Reads a range of lines with line numbering for exact reference."""
        full_path = self._resolve_path(file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if end_line == -1 or end_line > len(lines):
            end_line = len(lines)

        output = []
        for i in range(max(1, start_line), end_line + 1):
            output.append(f"{i:4d} | {lines[i - 1].rstrip()}")
        return "\n".join(output)

    def search_code(self, query: str, file_path: str) -> List[Tuple[int, str]]:
        """Finds matching lines for a query string in a target file."""
        full_path = self._resolve_path(file_path)
        matches = []
        with open(full_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if query in line:
                    matches.append((idx, line.strip()))
        return matches

    def parse_file_ast(self, file_path: str) -> ast.AST:
        """Parses a target Python source file into an Abstract Syntax Tree (AST)."""
        full_path = self._resolve_path(file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ast.parse(content, filename=file_path)

    def find_route_handlers(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Uses AST traversal to identify API route handlers (e.g. @app.get('/authorize')).
        Returns handler metadata: function name, path, method, line start, line end, and arguments.
        """
        tree = self.parse_file_ast(file_path)
        handlers = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    # Check for decorator like @app.get(...) or @app.post(...)
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        method = decorator.func.attr.lower()
                        route_path = None
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            route_path = decorator.args[0].value

                        args_list = [arg.arg for arg in node.args.args]
                        handlers.append({
                            "name": node.name,
                            "route_path": route_path,
                            "method": method,
                            "lineno": node.lineno,
                            "end_lineno": getattr(node, "end_lineno", node.lineno),
                            "arguments": args_list,
                        })
        return handlers

    def replace_block(self, file_path: str, target_block: str, replacement_block: str) -> bool:
        """
        Surgically replaces a block of code and validates that the resulting file
        is syntactically valid Python via ast.parse() before persisting to disk.
        """
        full_path = self._resolve_path(file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        if target_block not in content:
            return False

        new_content = content.replace(target_block, replacement_block, 1)

        # Gate 0: AST Syntax Validation
        try:
            ast.parse(new_content, filename=file_path)
        except SyntaxError:
            # Candidate patch introduced a syntax error -> Reject immediately
            return False

        # Backup current version before modification
        if full_path not in self._backup_cache:
            self._backup_cache[full_path] = content

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    def rollback(self, file_path: str) -> bool:
        """Restores a file to its backed-up state if a candidate patch fails tests."""
        full_path = self._resolve_path(file_path)
        if full_path in self._backup_cache:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(self._backup_cache[full_path])
            return True
        return False

    def create_snapshot(self, file_path: str) -> None:
        """Records a clean baseline snapshot of the file."""
        full_path = self._resolve_path(file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            self._backup_cache[full_path] = f.read()
