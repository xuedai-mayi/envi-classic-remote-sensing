from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_plugin_manifest_and_mcp_config_are_connected() -> None:
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    mcp_config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "envi-classic-remote-sensing"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["skills"] == "./skills/"
    assert "envi-classic" in mcp_config["mcpServers"]


def test_release_contains_no_private_absolute_paths() -> None:
    private_path = r"C:" + r"[\\/]" + "Users" + r"[\\/]"
    student_id = "1624" + "0110"
    student_name = "\u675c" + "\u660a"
    local_folder = "\u65e5\u5e38" + "\u5b9e\u9a8c"
    forbidden = re.compile("|".join((private_path, student_id, student_name, local_folder)), re.IGNORECASE)
    excluded = {".git", ".venv", "__pycache__", ".pytest_cache"}
    inspected_suffixes = {".md", ".json", ".toml", ".py", ".ps1", ".yaml", ".yml"}

    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        if path.suffix.lower() not in inspected_suffixes:
            continue
        text = path.read_text(encoding="utf-8")
        if forbidden.search(text):
            findings.append(str(path.relative_to(ROOT)))

    assert not findings, f"Private paths or identifiers found in: {findings}"
