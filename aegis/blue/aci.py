"""
Aegis Blue Team Agent-Computer Interface (ACI).
Modeled on SWE-agent's ACI primitives for localized repository
exploration, diff generation, block replacement, and rollback.
"""

import os
from typing import List, Optional, Tuple


class AgentComputerInterface:
    """Provides safe code inspection and modification tools for the Blue Agent."""

    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)
        self._backup_cache = {}

    def _resolve_path(self, relative_path: str) -> str:
        resolved = os.path.abspath(os.path.join(self.workspace_root, relative_path))
        if not resolved.startswith(self.workspace_root):
            raise PermissionError(f"Access denied outside workspace: {relative_path}")
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

    def replace_block(self, file_path: str, target_block: str, replacement_block: str) -> bool:
        """
        Surgically replaces an exact block of code with new logic.
        Backs up the file prior to modification to enable rollback.
        """
        full_path = self._resolve_path(file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        if target_block not in content:
            return False

        # Backup current version before modification
        if full_path not in self._backup_cache:
            self._backup_cache[full_path] = content

        new_content = content.replace(target_block, replacement_block, 1)
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
