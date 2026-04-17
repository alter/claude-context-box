"""Tests for ccb.installer.merger."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccb.installer.merger import (
    CLAUDE_MD_BEGIN,
    CLAUDE_MD_END,
    GITIGNORE_BEGIN,
    GITIGNORE_END,
    GITIGNORE_PATTERNS,
    merge_claude_md,
    merge_gitignore,
    merge_settings_json,
    render_claude_md_block,
    render_gitignore_block,
    strip_claude_md,
    strip_gitignore,
)


# CLAUDE.md merging --------------------------------------------------------


def test_merge_claude_md_creates_when_absent(tmp_path: Path) -> None:
    target = tmp_path / "CLAUDE.md"
    block = render_claude_md_block("body", "0.3.0")
    assert merge_claude_md(target, block) == "created"
    content = target.read_text()
    assert content.startswith(CLAUDE_MD_BEGIN)
    assert "body" in content
    assert content.rstrip().endswith(CLAUDE_MD_END)


def test_merge_claude_md_appends_when_no_markers(tmp_path: Path) -> None:
    target = tmp_path / "CLAUDE.md"
    target.write_text("# user content\n\nrule 1\n")
    block = render_claude_md_block("body", "0.3.0")
    assert merge_claude_md(target, block) == "appended"
    content = target.read_text()
    assert content.startswith("# user content")
    assert CLAUDE_MD_BEGIN in content
    assert CLAUDE_MD_END in content


def test_merge_claude_md_replaces_existing_block(tmp_path: Path) -> None:
    target = tmp_path / "CLAUDE.md"
    target.write_text(
        "# user content\n\n"
        f"{CLAUDE_MD_BEGIN}\nold body\n{CLAUDE_MD_END}\n\n"
        "user appendix\n"
    )
    block = render_claude_md_block("new body", "0.3.0")
    assert merge_claude_md(target, block) == "replaced"
    content = target.read_text()
    assert "old body" not in content
    assert "new body" in content
    assert "user appendix" in content
    assert "# user content" in content


def test_merge_claude_md_preserves_user_content_outside_markers(tmp_path: Path) -> None:
    target = tmp_path / "CLAUDE.md"
    pre = "ABOVE the block — must survive\n\n"
    post = "\n\nBELOW the block — must survive too\n"
    target.write_text(pre + f"{CLAUDE_MD_BEGIN}\nold\n{CLAUDE_MD_END}" + post)
    merge_claude_md(target, render_claude_md_block("new", "0.3.0"))
    content = target.read_text()
    assert "ABOVE the block — must survive" in content
    assert "BELOW the block — must survive too" in content
    assert "new" in content
    assert "old" not in content


def test_merge_claude_md_only_replaces_first_block(tmp_path: Path) -> None:
    """Defensive: malformed file with two blocks — only first is replaced."""
    target = tmp_path / "CLAUDE.md"
    target.write_text(
        f"{CLAUDE_MD_BEGIN}\nfirst\n{CLAUDE_MD_END}\n"
        f"{CLAUDE_MD_BEGIN}\nsecond\n{CLAUDE_MD_END}\n"
    )
    merge_claude_md(target, render_claude_md_block("new", "0.3.0"))
    content = target.read_text()
    assert "first" not in content
    assert "second" in content
    assert "new" in content


def test_strip_claude_md_removes_block(tmp_path: Path) -> None:
    target = tmp_path / "CLAUDE.md"
    target.write_text(
        "user before\n\n"
        f"{CLAUDE_MD_BEGIN}\nccb\n{CLAUDE_MD_END}\n\n"
        "user after\n"
    )
    assert strip_claude_md(target) is True
    content = target.read_text()
    assert CLAUDE_MD_BEGIN not in content
    assert "user before" in content
    assert "user after" in content


def test_strip_claude_md_noop_when_no_block(tmp_path: Path) -> None:
    target = tmp_path / "CLAUDE.md"
    target.write_text("only user content\n")
    assert strip_claude_md(target) is False
    assert target.read_text() == "only user content\n"


def test_render_block_carries_version(tmp_path: Path) -> None:
    block = render_claude_md_block("body", "0.3.0-dev")
    assert "0.3.0-dev" in block
    assert block.startswith(CLAUDE_MD_BEGIN)
    assert block.endswith(CLAUDE_MD_END)


# settings.json merging ----------------------------------------------------


def test_merge_settings_creates_when_absent(tmp_path: Path) -> None:
    target = tmp_path / ".claude" / "settings.json"
    outcome = merge_settings_json(target, {"ccb": {"version": "0.3.0"}, "hooks": {}})
    assert outcome == "created"
    data = json.loads(target.read_text())
    assert data["ccb"]["version"] == "0.3.0"


def test_merge_settings_replaces_ccb_key(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    target.write_text(json.dumps({"ccb": {"version": "0.2.0"}, "userKey": "keep"}))
    merge_settings_json(target, {"ccb": {"version": "0.3.0"}})
    data = json.loads(target.read_text())
    assert data["ccb"]["version"] == "0.3.0"
    assert data["userKey"] == "keep"


def test_merge_settings_preserves_user_hooks(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    target.write_text(json.dumps({
        "hooks": {
            "SessionStart": [{"matcher": "", "command": "user-hook"}],
        },
    }))
    merge_settings_json(target, {
        "hooks": {
            "SessionStart": [{"_ccb": True, "matcher": "", "command": "ccb-hook"}],
        },
    })
    data = json.loads(target.read_text())
    cmds = [h["command"] for h in data["hooks"]["SessionStart"]]
    assert "user-hook" in cmds
    assert "ccb-hook" in cmds


def test_merge_settings_replaces_existing_ccb_hooks(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    target.write_text(json.dumps({
        "hooks": {
            "SessionStart": [
                {"matcher": "", "command": "user-hook"},
                {"_ccb": True, "matcher": "", "command": "old-ccb"},
            ],
        },
    }))
    merge_settings_json(target, {
        "hooks": {
            "SessionStart": [{"_ccb": True, "matcher": "", "command": "new-ccb"}],
        },
    })
    data = json.loads(target.read_text())
    cmds = [h["command"] for h in data["hooks"]["SessionStart"]]
    assert cmds == ["user-hook", "new-ccb"]


def test_merge_settings_rejects_invalid_json(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    target.write_text("{not valid json")
    with pytest.raises(SystemExit, match="not valid JSON"):
        merge_settings_json(target, {"ccb": {}})


# .gitignore merging -------------------------------------------------------


def test_merge_gitignore_creates_when_absent(tmp_path: Path) -> None:
    target = tmp_path / ".gitignore"
    block = render_gitignore_block("0.3.0")
    assert merge_gitignore(target, block) == "created"
    content = target.read_text()
    assert GITIGNORE_BEGIN in content
    assert GITIGNORE_END in content
    for pattern in GITIGNORE_PATTERNS:
        assert pattern in content


def test_merge_gitignore_appends_when_no_markers(tmp_path: Path) -> None:
    target = tmp_path / ".gitignore"
    target.write_text("# my project\n*.pyc\n.env\n")
    assert merge_gitignore(target, render_gitignore_block("0.3.0")) == "appended"
    content = target.read_text()
    assert content.startswith("# my project")
    assert "*.pyc" in content
    assert GITIGNORE_BEGIN in content


def test_merge_gitignore_replaces_existing_block(tmp_path: Path) -> None:
    target = tmp_path / ".gitignore"
    target.write_text(
        "*.pyc\n\n"
        f"{GITIGNORE_BEGIN}\nold-pattern\n{GITIGNORE_END}\n\n"
        ".env\n"
    )
    merge_gitignore(target, render_gitignore_block("0.3.0"))
    content = target.read_text()
    assert "old-pattern" not in content
    assert ".claude/ccb-venv/" in content
    assert "*.pyc" in content
    assert ".env" in content


def test_merge_gitignore_skips_when_patterns_already_listed(tmp_path: Path) -> None:
    """If user already explicitly added every ccb path, don't append a duplicate block."""
    target = tmp_path / ".gitignore"
    target.write_text(
        "*.pyc\n"
        ".claude/ccb-venv/\n"
        ".ccb/\n"
        "PROJECT.llm\n"
        "**/CONTEXT.llm\n"
    )
    outcome = merge_gitignore(target, render_gitignore_block("0.3.0"))
    assert outcome == "patterns-already-listed"
    assert GITIGNORE_BEGIN not in target.read_text()


def test_strip_gitignore_removes_block_only(tmp_path: Path) -> None:
    target = tmp_path / ".gitignore"
    target.write_text(
        "*.pyc\n\n"
        f"{GITIGNORE_BEGIN}\n.claude/ccb-venv/\n{GITIGNORE_END}\n\n"
        ".env\n"
    )
    assert strip_gitignore(target) is True
    content = target.read_text()
    assert GITIGNORE_BEGIN not in content
    assert "*.pyc" in content
    assert ".env" in content


def test_strip_gitignore_noop_when_no_block(tmp_path: Path) -> None:
    target = tmp_path / ".gitignore"
    target.write_text("*.pyc\n.env\n")
    assert strip_gitignore(target) is False
    assert target.read_text() == "*.pyc\n.env\n"


def test_strip_gitignore_noop_when_file_missing(tmp_path: Path) -> None:
    assert strip_gitignore(tmp_path / ".gitignore") is False
